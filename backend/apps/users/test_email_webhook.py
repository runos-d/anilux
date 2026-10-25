from django.test import TestCase, override_settings

from apps.users.infrastructure.models.users import SuppressedEmail, TransactionalEmailEvent


@override_settings(BREVO_WEBHOOK_BEARER_TOKEN="test-webhook-token", ENVIRONMENT="development")
class BrevoTransactionalWebhookTests(TestCase):
    url = "/api/integrations/brevo/transactional-events/"

    def test_requires_integration_bearer_token(self):
        response = self.client.post(
            self.url,
            {"event": "delivered", "email": "person@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(TransactionalEmailEvent.objects.count(), 0)

    def test_hard_bounce_is_idempotent_and_suppresses_normalized_recipient(self):
        payload = {
            "event": "hardBounce",
            "email": "Person@Example.com",
            "messageId": "provider-message-1",
            "ts": 1_700_000_000,
            "reason": "mailbox unavailable",
        }
        headers = {"HTTP_AUTHORIZATION": "Bearer test-webhook-token"}
        first = self.client.post(self.url, payload, content_type="application/json", **headers)
        second = self.client.post(self.url, payload, content_type="application/json", **headers)

        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.json()["duplicate"])
        self.assertTrue(second.json()["duplicate"])
        self.assertEqual(TransactionalEmailEvent.objects.count(), 1)
        self.assertTrue(SuppressedEmail.objects.filter(email="person@example.com").exists())
