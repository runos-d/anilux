import json
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.notifications.infrastructure.models.notifications import PushSubscription
from apps.users.application.data_management import (
    build_user_export, delete_user_account, expire_exports,
)
from apps.users.infrastructure.models.users import DataExport, PrivacySettings, User


class PrivacySettingsContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="privacy-a", email="a@example.test", password="strong-password")
        self.other = User.objects.create_user(username="privacy-b", email="b@example.test", password="strong-password")

    def test_me_read_patch_and_user_isolation(self):
        self.client.force_authenticate(self.user)
        url = reverse("privacy-settings-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["who_can_see_email"], "contacts")

        response = self.client.patch(url, {"who_can_see_email": "nobody"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["who_can_see_email"], "nobody")
        self.assertEqual(PrivacySettings.objects.get(user=self.other).who_can_see_email, "contacts")

    def test_consent_requires_current_policy_version(self):
        self.client.force_authenticate(self.user)
        url = reverse("privacy-settings-me")
        invalid = self.client.patch(url, {
            "analytics_consent_state": "granted",
            "analytics_consent_version": "old-policy",
            "analytics_consent_source": "settings",
        }, format="json")
        self.assertEqual(invalid.status_code, 400)

        valid = self.client.patch(url, {
            "analytics_consent_state": "denied",
            "analytics_consent_version": "2026-10-27.1",
            "analytics_consent_source": "settings",
        }, format="json")
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.data["analytics_consent_state"], "denied")
        self.assertIsNotNone(valid.data["analytics_consent_updated_at"])

    def test_every_visible_privacy_control_is_persisted(self):
        self.client.force_authenticate(self.user)
        payload = {
            "who_can_see_phone": "nobody",
            "who_can_see_email": "everyone",
            "who_can_see_last_seen": "contacts",
            "who_can_see_profile_photo": "nobody",
            "who_can_call": "contacts",
            "who_can_add_to_groups": "nobody",
            "allow_message_forwarding": False,
        }
        response = self.client.patch(reverse("privacy-settings-me"), payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.privacy_settings.refresh_from_db()
        for field, value in payload.items():
            self.assertEqual(getattr(self.user.privacy_settings, field), value)


class UserDataLifecycleTests(TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.override = override_settings(DATA_EXPORT_ROOT=Path(self.tempdir.name), DATA_EXPORT_TTL_HOURS=168)
        self.override.enable()
        self.client = APIClient()
        self.user = User.objects.create_user(username="export-owner", email="owner@example.test", password="strong-password")
        self.other = User.objects.create_user(username="export-other", email="other@example.test", password="strong-password")

    def tearDown(self):
        self.override.disable()
        self.tempdir.cleanup()

    def _record(self, **kwargs):
        defaults = {
            "user": self.user,
            "items": ["profile"],
            "format": "json",
            "expires_at": timezone.now() + timedelta(days=7),
        }
        defaults.update(kwargs)
        return DataExport.objects.create(**defaults)

    def test_export_contains_only_subject_data_and_owner_downloads(self):
        record = self._record()
        build_user_export(record.pk)
        record.refresh_from_db()
        self.assertEqual(record.status, "ready")
        path = Path(record.file_path)
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as archive:
            payload = json.loads(archive.read("profile.json"))
        self.assertEqual(payload[0]["email"], self.user.email)
        self.assertNotIn(self.other.email, json.dumps(payload))

        self.client.force_authenticate(self.other)
        denied = self.client.get(reverse("export_data_download", kwargs={"export_id": record.pk}))
        self.assertEqual(denied.status_code, 404)
        self.client.force_authenticate(self.user)
        allowed = self.client.get(reverse("export_data_download", kwargs={"export_id": record.pk}))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed["Cache-Control"], "private, no-store")
        allowed.close()

    def test_expiry_deletes_physical_archive(self):
        record = self._record(expires_at=timezone.now() - timedelta(seconds=1))
        root = Path(self.tempdir.name) / str(self.user.pk)
        root.mkdir(parents=True)
        path = root / f"export-{record.pk}.zip"
        path.write_bytes(b"archive")
        record.status = "ready"
        record.file_path = str(path)
        record.save(update_fields=["status", "file_path"])
        self.assertEqual(expire_exports(), 1)
        record.refresh_from_db()
        self.assertEqual(record.status, "expired")
        self.assertFalse(path.exists())

    @patch("apps.users.application.user_data_tasks.build_data_export_task.delay")
    def test_export_api_validates_and_isolates_owners(self, enqueue):
        self.client.force_authenticate(self.user)
        invalid = self.client.post(reverse("export_data"), {"items": ["profile", "profile"]}, format="json")
        self.assertEqual(invalid.status_code, 400)

        created = self.client.post(reverse("export_data"), {"items": ["profile"], "format": "json"}, format="json")
        self.assertEqual(created.status_code, 202)
        self.assertEqual(created.data["status"], "queued")
        enqueue.assert_called_once_with(created.data["id"])

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse("export_data")).data["exports"], [])
        self.assertEqual(
            self.client.get(reverse("export_data_detail", kwargs={"export_id": created.data["id"]})).status_code,
            404,
        )

    def test_account_deletion_removes_files_tokens_sessions_push_and_is_idempotent(self):
        user_id = self.user.pk
        self.user.avatar.save("avatar.txt", ContentFile(b"avatar"), save=True)
        avatar_path = Path(self.user.avatar.path)
        export = self._record(status="ready")
        root = Path(self.tempdir.name) / str(user_id)
        root.mkdir(parents=True)
        export_path = root / "export.zip"
        export_path.write_bytes(b"private")
        export.file_path = str(export_path)
        export.save(update_fields=["file_path"])
        PushSubscription.objects.create(user=self.user, endpoint="https://push.example.test/one")
        token = RefreshToken.for_user(self.user)
        session = SessionStore()
        session["_auth_user_id"] = str(user_id)
        session.save()

        self.assertTrue(delete_user_account(user_id))
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertFalse(PushSubscription.objects.filter(user_id=user_id).exists())
        self.assertFalse(Session.objects.filter(session_key=session.session_key).exists())
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=token["jti"]).exists())
        self.assertFalse(avatar_path.exists())
        self.assertFalse(export_path.exists())
        self.assertFalse(delete_user_account(user_id))
