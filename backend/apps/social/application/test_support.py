from django.test import TestCase
from rest_framework.test import APIClient

from apps.social.models import SupportMessage, SupportTicket
from apps.users.models import User


class SupportConversationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='support-user', password='test-pass')
        self.admin = User.objects.create_user(username='support-admin', password='test-pass', is_staff=True)
        self.ticket = SupportTicket.objects.create(user=self.user, subject='Проверка', status='answered')
        self.message = SupportMessage.objects.create(ticket=self.ticket, sender=self.admin, text='Ответ поддержки')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_user_can_read_conversation_and_admin_reply_is_marked_read(self):
        response = self.client.get(f'/api/social/support/{self.ticket.pk}/messages/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('Ответ поддержки', response.data[0]['text'])
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)
        self.assertIsNotNone(self.message.read_at)
