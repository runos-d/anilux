"""Current authorization through real Redis multicast and both WS consumers."""
import asyncio
import os
import uuid
from datetime import timedelta
from unittest import skipUnless
from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.test import TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.social.application import conversations as service
from apps.social.application.routing import websocket_urlpatterns
from apps.social.application.tasks_chat import deliver_chat_event
from apps.social.infrastructure.models.conversation import ChatEvent
from apps.social.infrastructure.models.social import ChatMember, GroupChat
from apps.users.infrastructure.models.users import ActiveSession, User


@skipUnless(os.environ.get('SCALABILITY_REDIS_TESTS') == 'true', 'Requires isolated lab Redis')
class MulticastSecurityTests(TransactionTestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='multicast-a', email='ma@example.test')
        self.b = User.objects.create_user(username='multicast-b', email='mb@example.test')
        self.chat = GroupChat.objects.create(name='Multicast security', created_by=self.a)
        ChatMember.objects.bulk_create([ChatMember(chat=self.chat, user=user) for user in (self.a, self.b)])
        session = SessionStore()
        session['_auth_user_id'] = str(self.b.pk)
        session['_auth_user_hash'] = self.b.get_session_auth_hash()
        session.create()
        self.session_key = session.session_key
        active = ActiveSession.objects.get_or_create(user=self.b, session_key=self.session_key,
            defaults={'ip_address': '127.0.0.1', 'user_agent': 'test'})[0]
        token = AccessToken.for_user(self.b)
        token.set_exp(lifetime=timedelta(hours=1))
        token['sid'] = str(active.pk)
        self.token = str(token)

    def scenario(self, revoke, rich=False):
        async def run():
            sockets = [WebsocketCommunicator(URLRouter(websocket_urlpatterns), path,
                subprotocols=['animecore.v2', 'auth.'+self.token]) for path in
                ('/ws/global/', f'/ws/chat/{self.chat.public_id}/?type=group')]
            layer = get_channel_layer()
            try:
                for socket in sockets:
                    self.assertTrue((await socket.connect())[0])
                self.assertEqual((await sockets[1].receive_json_from())['action'], 'init')
                def publish():
                    values = {'text': 'current access'}
                    if rich:
                        original, _ = service.send_message(self.chat, self.a, {'text': 'original reply'})
                        # This first event is not the one published by this probe.
                        values['reply_to'] = original
                    message, _ = service.send_message(self.chat, self.a, values)
                    event = ChatEvent.objects.get(kind='new_message', payload__message__id=message.pk)
                    deliver_chat_event.run(event.pk)
                    return event
                event = await database_sync_to_async(publish)()
                for socket in sockets:
                    self.assertEqual((await socket.receive_json_from(timeout=3))['action'], 'new_message')
                await database_sync_to_async(revoke)()
                # Replay the *old* addressed event through the new real transport.
                # Old recipients/group membership must never grant current access.
                frame = {'type': 'conversation_event', 'payload': service.event_envelope(event), 'recipients': event.recipients}
                await layer.group_send(f'conversation_{event.conversation_id}', frame)
                await layer.user_groups_send([f'user_{self.b.pk}'], frame)
                if revoke.__name__ == 'session':
                    for socket in sockets:
                        self.assertEqual((await socket.receive_output(timeout=3))['type'], 'websocket.close')
                else:
                    self.assertEqual((await sockets[1].receive_output(timeout=3))['type'], 'websocket.close')
                    self.assertTrue(await sockets[0].receive_nothing(timeout=.2))
            finally:
                for socket in sockets:
                    await socket.disconnect()
                await layer.close_pools()
        configuration = {'default': {'BACKEND': 'core.channel_layer.BoundedRedisChannelLayer',
            'CONFIG': {'hosts': [('lab-realtime', 6379)], 'prefix': 'security-test-'+uuid.uuid4().hex}}}
        with override_settings(CHANNEL_LAYERS=configuration), patch('apps.social.application.conversations.enqueue_event'), \
                patch('core.redis_client.redis_pubsub_manager'):
            async_to_sync(run)()

    def test_session_revocation_is_observed_after_successful_multicast(self):
        def session():
            Session.objects.filter(session_key=self.session_key).delete()
        self.scenario(session)

    def test_membership_revocation_blocks_old_multicast_and_room_replay(self):
        def membership():
            ChatMember.objects.filter(chat=self.chat, user=self.b).delete()
        self.scenario(membership)

    def test_ban_blocks_rich_projection_and_old_multicast_replay(self):
        from apps.social.infrastructure.models.social_chat import ChatBan
        def ban():
            ChatBan.objects.create(chat=self.chat, user=self.b, banned_by=self.a)
        self.scenario(ban, rich=True)
