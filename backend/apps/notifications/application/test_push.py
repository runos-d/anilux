import base64
from datetime import time
from unittest.mock import patch
from types import SimpleNamespace
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from pywebpush import WebPushException
from apps.notifications.infrastructure.models.notifications import Notification, NotificationSetting, PushSubscription
from .celery_tasks import send_push_for_notification

def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')

@override_settings(WEB_PUSH_PUBLIC_KEY='public-test', WEB_PUSH_PRIVATE_KEY='private-test', WEB_PUSH_SUBJECT='mailto:test@example.test')
class PushTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='push-user', email='push@example.test')
        self.other = get_user_model().objects.create_user(username='push-other', email='other@example.test')
        self.client = APIClient(); self.client.force_authenticate(self.user)
        self.data = {'endpoint': 'https://fcm.googleapis.com/fcm/send/fixture', 'keys': {
            'p256dh': b64(ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)),
            'auth': b64(b'0123456789abcdef')}}
        self.n = Notification.objects.create(user=self.user, type='system', title='Тест', content='Проверка', link='/notifications')

    def subscribe(self):
        response = self.client.post('/api/notifications/push/subscription/', self.data, format='json')
        self.assertEqual(200, response.status_code, response.data)
        return PushSubscription.objects.get(user=self.user)

    def test_subscription_validation_idempotency_and_account_isolation(self):
        self.subscribe(); self.subscribe(); self.assertEqual(1, PushSubscription.objects.count())
        for endpoint in ('http://fcm.googleapis.com/1', 'https://127.0.0.1/1', 'https://fcm.googleapis.com.evil.test/1', 'https://fcm.googleapis.com:8443/1'):
            self.assertEqual(400, self.client.post('/api/notifications/push/subscription/', {**self.data, 'endpoint': endpoint}, format='json').status_code)
        self.client.force_authenticate(self.other)
        self.assertEqual(204, self.client.delete('/api/notifications/push/subscription/', {'endpoint': self.data['endpoint']}, format='json').status_code)
        self.assertEqual(1, PushSubscription.objects.count())
        self.client.force_authenticate(None)
        self.assertIn(self.client.post('/api/notifications/push/subscription/', self.data, format='json').status_code, (401, 403))

    @patch('pywebpush.webpush')
    def test_sends_payload_to_subscribed_user_only(self, send):
        self.subscribe()
        result = send_push_for_notification.run(self.n.pk)
        self.assertEqual({'sent': 1}, result)
        self.assertIn('Проверка', send.call_args.kwargs['data'])
        self.assertEqual('private-test', send.call_args.kwargs['vapid_private_key'])
        send.reset_mock()
        self.n.user = self.other; self.n.save()
        self.assertEqual({'sent': 0}, send_push_for_notification.run(self.n.pk)); send.assert_not_called()

    @patch('pywebpush.webpush')
    def test_expired_endpoint_disabled_and_transient_failure_retried(self, send):
        subscription = self.subscribe()
        send.side_effect = WebPushException('expired', response=SimpleNamespace(status_code=410))
        self.assertEqual({'sent': 0}, send_push_for_notification.run(self.n.pk))
        subscription.refresh_from_db(); self.assertFalse(subscription.is_active)
        subscription.is_active = True; subscription.save()
        send.side_effect = WebPushException('retry', response=SimpleNamespace(status_code=503))
        with patch.object(send_push_for_notification, 'retry', side_effect=RuntimeError('retried')) as retry:
            with self.assertRaisesRegex(RuntimeError, 'retried'):
                send_push_for_notification.run(self.n.pk)
            retry.assert_called_once()

    @patch('pywebpush.webpush')
    def test_global_type_dnd_read_and_notification_switches(self, send):
        self.subscribe()
        prefs = NotificationSetting.objects.create(user=self.user, push_enabled=False)
        self.assertEqual('disabled', send_push_for_notification.run(self.n.pk)['skipped'])
        prefs.push_enabled = True; prefs.type_settings = {'system': {'enabled': False}}; prefs.save()
        self.assertEqual('disabled', send_push_for_notification.run(self.n.pk)['skipped'])
        prefs.type_settings = {}; prefs.dnd_enabled = True; prefs.dnd_start = time(0); prefs.dnd_end = time(23,59,59); prefs.save()
        self.assertEqual('dnd', send_push_for_notification.run(self.n.pk)['skipped'])
        prefs.dnd_enabled = False; prefs.save()
        self.n.is_read = True; self.n.save()
        self.assertEqual('missing_or_read', send_push_for_notification.run(self.n.pk)['skipped'])
        send.assert_not_called()

    @override_settings(WEB_PUSH_PRIVATE_KEY='')
    def test_unconfigured_server_reports_truthful_capability(self):
        response = self.client.get('/api/notifications/push/config/')
        self.assertEqual({'enabled': False, 'public_key': ''}, response.data)
        self.assertEqual('not_configured', send_push_for_notification.run(self.n.pk)['skipped'])

    @patch('pywebpush.webpush')
    def test_windows_push_headers_only_for_trusted_wns_endpoints(self, send):
        self.data['endpoint'] = 'https://wns2-ln2p.notify.windows.com/w/?token=fixture'
        self.subscribe()
        self.assertEqual({'sent': 1}, send_push_for_notification.run(self.n.pk))
        self.assertEqual({'X-WNS-Type': 'wns/raw', 'Content-Type': 'application/octet-stream'}, send.call_args.kwargs['headers'])
        self.data['endpoint'] = 'https://wns2-ln2p.notify.windows.com.evil.test/w/'
        self.assertEqual(400, self.client.post('/api/notifications/push/subscription/', self.data, format='json').status_code)
