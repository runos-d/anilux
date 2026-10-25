import time
import uuid
from unittest.mock import patch

import redis
from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpResponse
from django.test import SimpleTestCase, TransactionTestCase, RequestFactory

from core.online_status import RedisOnlineStatus, online_status, ONLINE_KEY_PREFIX, PRESENCE_SESSIONS_PREFIX


def presence_client():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)


class PresenceRegistryTests(SimpleTestCase):
    def setUp(self):
        self.client = presence_client()
        self.user_id = 2_000_000_000 + uuid.uuid4().int % 100_000_000
        self.keys = [f'{ONLINE_KEY_PREFIX}{self.user_id}', f'{PRESENCE_SESSIONS_PREFIX}{self.user_id}']
        self.status = RedisOnlineStatus()
        self.status._get_client = lambda: self.client
        self.events = patch.object(self.status, '_send_online_event').start()
        self.addCleanup(patch.stopall)
        self.addCleanup(self.client.delete, *self.keys)

    def test_last_socket_goes_offline_but_closing_one_of_two_does_not(self):
        self.status.touch_connection(self.user_id, 'peer', 'tab-a')
        self.status.touch_connection(self.user_id, 'peer', 'tab-b')
        self.assertTrue(self.status.is_online(self.user_id))
        self.status.remove_connection(self.user_id, 'peer', 'tab-a')
        self.assertTrue(self.status.is_online(self.user_id))
        self.events.assert_called_once_with(self.user_id, 'peer', True)
        self.status.remove_connection(self.user_id, 'peer', 'tab-b')
        self.assertFalse(self.status.is_online(self.user_id))
        self.events.assert_called_with(self.user_id, 'peer', False)
        self.assertEqual(self.events.call_count, 2)

    def test_expired_socket_leases_cannot_keep_the_last_live_socket_online(self):
        self.status.touch_connection(self.user_id, 'peer', 'crashed-tab')
        self.client.zadd(self.keys[1], {'crashed-tab': time.time() - 1})
        self.status.touch_connection(self.user_id, 'peer', 'live-tab')
        self.assertEqual(self.client.zcard(self.keys[1]), 1)
        self.status.remove_connection(self.user_id, 'peer', 'live-tab')
        self.assertFalse(self.status.is_online(self.user_id))

    def test_heartbeat_refresh_does_not_republish_online_or_shorten_other_socket_lease(self):
        self.status.touch_connection(self.user_id, 'peer', 'tab')
        self.status.set_online(self.user_id, 'peer', is_active=False)
        self.assertGreater(self.client.ttl(self.keys[0]), 60)
        self.events.assert_called_once_with(self.user_id, 'peer', True)
        self.status.remove_connection(self.user_id, 'peer', 'tab')
        self.assertFalse(self.status.is_online(self.user_id))

    def test_passive_http_request_does_not_mark_a_user_online(self):
        from config.middleware import OnlineStatusMiddleware
        request = RequestFactory().get('/api/social/chats/')
        request.user = type('AuthenticatedUser', (), {'is_authenticated': True, 'id': self.user_id})()
        with patch.object(online_status, 'set_online') as update:
            response = OnlineStatusMiddleware(lambda request: HttpResponse('[]'))(request)
        update.assert_not_called()
        self.assertIn('no-store', response['Cache-Control'])

    def test_delayed_heartbeat_after_last_disconnect_cannot_restore_online(self):
        self.status.set_online(self.user_id, 'peer', require_connection=True)
        self.assertFalse(self.status.is_online(self.user_id))
        self.status.touch_connection(self.user_id, 'peer', 'tab')
        self.status.set_online(self.user_id, 'peer', require_connection=True)
        self.assertTrue(self.status.is_online(self.user_id))
        self.status.remove_connection(self.user_id, 'peer', 'tab')
        for is_active in [False, True]:
            self.status.set_online(self.user_id, 'peer', is_active=is_active, require_connection=True)
            self.assertFalse(self.status.is_online(self.user_id))
        self.assertEqual(self.events.call_count, 2)


class GlobalSocketPresenceTests(TransactionTestCase):
    def setUp(self):
        from apps.users.infrastructure.models.users import User
        self.user = User.objects.create_user(username='socket_presence', email='socket_presence@test.local')
        self.redis = presence_client()
        self.keys = [f'{ONLINE_KEY_PREFIX}{self.user.pk}', f'{PRESENCE_SESSIONS_PREFIX}{self.user.pk}']
        self.redis.delete(*self.keys)
        self.addCleanup(self.redis.delete, *self.keys)
        manager = patch('core.redis_client.redis_pubsub_manager').start()
        self.manager = manager
        manager._get_redis_client.return_value = self.redis
        self.events = patch.object(online_status, '_send_online_event').start()
        patch('apps.social.application.conversations.enqueue_event').start()
        self.addCleanup(patch.stopall)

    def test_two_global_connections_refresh_presence_and_last_disconnect_clears_it(self):
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.social.application.routing import websocket_urlpatterns
        url = f'/ws/global/?token={AccessToken.for_user(self.user)}'

        async def scenario():
            a = WebsocketCommunicator(URLRouter(websocket_urlpatterns), url)
            b = WebsocketCommunicator(URLRouter(websocket_urlpatterns), url)
            try:
                for socket in [a, b]:
                    self.assertTrue((await socket.connect())[0])
                    await socket.send_json_to({'action': 'ping'})
                    self.assertEqual((await socket.receive_json_from())['action'], 'pong')
                self.assertEqual(self.redis.zcard(self.keys[1]), 2)
                callback = self.manager.register_callback.call_args_list[0].args[1]
                await callback({'type': 'user_offline', 'data': {'user_id': 123, 'username': 'peer'}})
                self.assertEqual(await a.receive_json_from(), {'action': 'user_offline',
                    'data': {'user_id': 123, 'username': 'peer'}, 'user_id': 123, 'username': 'peer'})
                await a.disconnect()
                self.assertTrue(self.redis.exists(self.keys[0]))
                await b.disconnect()
                self.assertFalse(self.redis.exists(self.keys[0]))
                self.events.assert_called_with(self.user.pk, self.user.username, False)
            finally:
                await a.disconnect()
                await b.disconnect()
        async_to_sync(scenario)()
