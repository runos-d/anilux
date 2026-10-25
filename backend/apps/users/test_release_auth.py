from django.core import mail, signing
from unittest.mock import Mock, patch

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.users.application.email_service import consume_one_time_token, issue_one_time_token, send_confirmation
from apps.users.infrastructure.models.users import User
from apps.users.presentation.serializers.users_serializers import LoginSerializer, RegisterSerializer


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class EmailOnlyAuthTests(TestCase):
    def test_registration_requires_email_and_rejects_case_insensitive_duplicate(self):
        User.objects.create_user(username="first", email="person@example.com", password="Safe-pass-1842")
        missing = RegisterSerializer(data={"username": "missing", "password": "Safe-pass-1842", "password_confirm": "Safe-pass-1842"})
        duplicate = RegisterSerializer(data={"username": "second", "email": "PERSON@example.com", "password": "Safe-pass-1842", "password_confirm": "Safe-pass-1842"})
        self.assertFalse(missing.is_valid())
        self.assertFalse(duplicate.is_valid())

    def test_login_uses_email_not_username(self):
        User.objects.create_user(username="internal-name", email="person@example.com", password="Safe-pass-1842")
        serializer = LoginSerializer(data={"email": "PERSON@example.com", "password": "Safe-pass-1842"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_confirmation_token_is_signed_expiring_and_one_time(self):
        user = User.objects.create_user(username="confirm", email="confirm@example.com", password="Safe-pass-1842")
        token = issue_one_time_token(user, "confirm")
        self.assertEqual(consume_one_time_token(token, "confirm"), user)
        with self.assertRaises(signing.BadSignature):
            consume_one_time_token(token, "confirm")

    def test_email_uses_configured_brand_and_frontend_url(self):
        user = User.objects.create_user(username="mail", email="mail@example.com", password="Safe-pass-1842")
        send_confirmation(user)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(settings.PROJECT_BRAND_NAME, mail.outbox[0].subject)
        self.assertIn("http://localhost:5173/confirm-email", mail.outbox[0].body)

    @patch("apps.users.presentation.views.users_views.requests.get")
    @patch("apps.users.presentation.views.users_views.requests.post")
    def test_google_callback_keeps_untrusted_profile_out_of_redirect_and_exchange_is_one_time(self, post, get):
        state = "safe-state"
        cache.set(f"google_oauth_state:{state}", state, 60)
        post.return_value = Mock(
            json=lambda: {"access_token": "provider-token"},
            raise_for_status=lambda: None,
        )
        malicious = "</script><img src=x onerror=alert(1)>"
        get.return_value = Mock(
            json=lambda: {
                "id": "google-safe-id",
                "email": "oauth@example.com",
                "verified_email": True,
                "name": malicious,
                "given_name": malicious,
                "family_name": "User",
            },
            raise_for_status=lambda: None,
        )

        callback = self.client.get(
            "/api/users/google/callback/",
            {"code": "provider-code", "state": state},
        )
        self.assertEqual(callback.status_code, 302)
        self.assertNotIn("script", callback["Location"])
        exchange_code = callback["Location"].split("code=", 1)[1]

        first = self.client.post(
            "/api/users/google/exchange/",
            {"code": exchange_code},
            content_type="application/json",
        )
        second = self.client.post(
            "/api/users/google/exchange/",
            {"code": exchange_code},
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["user"]["display_name"], malicious)
        self.assertEqual(second.status_code, 400)
