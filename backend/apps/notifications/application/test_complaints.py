from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.notifications.infrastructure.models.notifications import Complaint, Notification
from apps.social.infrastructure.models.social import Post, Report


User = get_user_model()


class ComplaintWorkflowTests(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(
            username="reporter", email="reporter@example.com", password="pass"
        )
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        self.post = Post.objects.create(author=self.author, title="Reported title", text="Full reported text")
        self.client = APIClient()

    def submit(self):
        self.client.force_authenticate(self.reporter)
        response = self.client.post(
            "/api/social/reports/",
            {"content_type": "post", "content_id": self.post.pk, "reason": "spam", "comment": "Details"},
            format="json",
        )
        self.assertEqual(201, response.status_code, response.data)
        return Complaint.objects.get(source_report_id=response.data["id"])

    def test_report_creates_admin_case_with_snapshot_and_notifications(self):
        complaint = self.submit()
        self.assertEqual("reactor_post", complaint.complaint_type)
        self.assertEqual("Full reported text", complaint.target_snapshot["text"])
        self.assertEqual(f"/post/{self.post.public_id}", complaint.target_snapshot["url"])
        self.assertTrue(Notification.objects.filter(user=self.admin, link="/admin/complaints").exists())

    def test_legacy_admin_feed_receives_reporter_and_full_post_content(self):
        self.submit()
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/social/moderation/reports/")
        self.assertEqual(200, response.status_code, response.data)
        row = response.data["results"][0]
        self.assertEqual("reporter", row["reporter"]["username"])
        self.assertEqual("author", row["content_preview"]["author"]["username"])
        self.assertEqual("Reported title", row["content_preview"]["title"])
        self.assertEqual("Full reported text", row["content_preview"]["text"])
        self.assertEqual(f"/post/{self.post.public_id}", row["content_preview"]["url"])

    def test_warning_resolves_both_records_and_notifies_users(self):
        complaint = self.submit()
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/users/admin/complaints/{complaint.pk}/",
            {"status": "resolved", "action": "warn_user", "resolution": "Материал нарушает правила."},
            format="json",
        )
        self.assertEqual(200, response.status_code, response.data)
        complaint.refresh_from_db()
        report = Report.objects.get(pk=complaint.source_report_id)
        self.assertEqual("resolved", report.status)
        self.assertEqual("warn_user", report.action_taken)
        self.assertTrue(Notification.objects.filter(user=self.reporter, title__contains="рассмотрена").exists())
        self.assertTrue(Notification.objects.filter(user=self.author, type="warning").exists())

    def test_deleted_content_keeps_snapshot_in_admin_list(self):
        complaint = self.submit()
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/users/admin/complaints/{complaint.pk}/",
            {"status": "resolved", "action": "delete_content", "resolution": "Публикация удалена."},
            format="json",
        )
        self.assertEqual(200, response.status_code, response.data)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)
        listing = self.client.get("/api/users/admin/complaints/?status=resolved")
        self.assertEqual(200, listing.status_code, listing.data)
        row = listing.data["results"][0]
        self.assertEqual("Full reported text", row["target_preview"])
        self.assertIsNone(row["target_url"])
        self.assertFalse(row["target_available"])

    def test_legacy_feed_moderation_uses_same_action_workflow(self):
        complaint = self.submit()
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            f"/api/social/moderation/reports/{complaint.source_report_id}/resolve/",
            {"status": "resolved", "action": "warn_user", "moderator_comment": "Официальное предупреждение."},
            format="json",
        )
        self.assertEqual(200, response.status_code, response.data)
        complaint.refresh_from_db()
        self.assertEqual("resolved", complaint.status)
        self.assertEqual("warn_user", complaint.action_taken)
        self.assertTrue(Notification.objects.filter(user=self.author, type="warning").exists())
