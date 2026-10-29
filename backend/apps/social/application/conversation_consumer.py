import asyncio
import json
import time
from functools import partial
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.exceptions import APIException
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.utils.encoders import JSONEncoder
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from core.socket_limits import SocketFrameBudget
from core.socket_credentials import socket_token, accepted_protocol

from apps.social.application import conversations as service
from apps.social.infrastructure.models.social import Message
from apps.users.infrastructure.models.users import User


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    @classmethod
    async def encode_json(cls, content):
        from core.telemetry import ws_phase
        with ws_phase('room', 'serialize'):
            return json.dumps(content, cls=JSONEncoder)

    async def connect(self):
        self.frames = SocketFrameBudget()
        self.room_name = None
        self.watchdog = None
        self.topic_id = None
        self.last_ping = time.monotonic()
        self.last_typing = 0
        self.params = parse_qs(self.scope.get('query_string', b'').decode())
        try:
            self.user, self.chat, self.room_name = await self.authorize()
        except (TokenError, User.DoesNotExist, AuthenticationFailed):
            await self.close(code=4001)
            return
        except APIException:
            await self.close(code=4004)
            return
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept(subprotocol=accepted_protocol(self.scope))
        self.watchdog = asyncio.create_task(self.check_timeout())
        await self.send_snapshot()

    async def authorize(self):
        raw = socket_token(self.scope)
        if raw and len(raw) > 4096:
            raise AuthenticationFailed('Invalid token')
        token = AccessToken(raw) if raw else None
        self.token_claims = token
        self.token_expires = token['exp'] if token else None
        from core.socket_auth import socket_user
        scope_user = self.scope.get('user')
        user_id = token['user_id'] if token else getattr(scope_user, 'pk', None)
        user = await socket_user(user_id, token, self.scope)
        if user is None:
            raise AuthenticationFailed('Требуется авторизация')
        return await self.authorize_chat(user)

    # Each operation opens and closes its own thread-local DB connection. These
    # independent conversations must not share Channels' single-thread executor.
    @partial(database_sync_to_async, thread_sensitive=False)
    def authorize_chat(self, user):
        chat = service.resolve_chat(self.scope['url_route']['kwargs']['chat_id'], user, self.params.get('type', [None])[0])
        self.topic_id = service.validate_topic(chat, self.params.get('topic_id', [None])[0])
        return user, chat, service.room(chat)

    async def disconnect(self, code):
        if self.watchdog:
            self.watchdog.cancel()
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    def token_expired(self):
        return bool(self.token_expires and self.token_expires <= timezone.now().timestamp())

    async def check_timeout(self):
        try:
            while True:
                await asyncio.sleep(25)
                if self.token_expired() or not await self.active_account():
                    await self.close(code=4001)
                    return
                if time.monotonic() - self.last_ping > 75:
                    await self.close(code=4002)
                    return
        except asyncio.CancelledError:
            return

    @partial(database_sync_to_async, thread_sensitive=False)
    def snapshot(self):
        from apps.social.presentation.views.conversation_views import history, detail_state
        chat = type(self.chat).objects.get(pk=self.chat.pk)
        service.check_access(chat, self.user)
        cursor = service.get_conversation(chat).event_seq
        messages, more = history(chat, self.user, topic=self.topic_id)
        return {'action': 'init', 'messages': service.serialize_messages(messages, self.user),
                'event_cursor': cursor, 'has_more': more, 'cleared_through_seq': detail_state(chat, self.user),
                'topic_id': self.topic_id,
                'next_cursor': messages[0].seq if more else None,
                'conversation_id': service.get_conversation(chat).pk, 'chat_id': chat.public_id, 'chat_type': service.chat_kind(chat)}

    async def send_snapshot(self):
        try:
            await self.send_json(await self.snapshot())
        except (APIException, type(self.chat).DoesNotExist):
            await self.close(code=4004)

    @partial(database_sync_to_async, thread_sensitive=False)
    def execute(self, data):
        self.user = User.objects.get(pk=self.user.pk, is_active=True)
        if self.token_expires and self.token_expires <= timezone.now().timestamp():
            raise AuthenticationFailed('Обновите авторизацию')
        chat = type(self.chat).objects.get(pk=self.chat.pk)
        service.check_access(chat, self.user)
        if data.get('action') == 'send_message':
            values = {k: data[k] for k in ('text', 'client_message_id') if k in data}
            values['topic_id'] = self.topic_id
            reply_id = data.get('reply_to_id') or data.get('reply_to')
            if reply_id:
                values['reply_to'] = service.accessible_message(reply_id, self.user)
            message, _ = service.send_message(chat, self.user, values)
            return {'action': 'message_ack', 'message': service.serialize_message(message, self.user)}
        if data.get('action') == 'mark_read':
            return dict(service.mark_read(chat, self.user, data.get('message_ids')), action='read_ack')
        if data.get('action') in ('typing_start', 'typing_stop'):
            service.check_access(chat, self.user, write=True)
        if data.get('action') == 'set_topic':
            self.topic_id = service.validate_topic(chat, data.get('topic_id'))
        return None

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        code = self.frames.reject_code(text_data)
        if code:
            await self.close(code=code)
            return
        try:
            await super().receive(text_data=text_data, bytes_data=bytes_data, **kwargs)
        except (json.JSONDecodeError, UnicodeDecodeError):
            await self.close(code=1007)

    async def receive_json(self, data, **kwargs):
        if not isinstance(data, dict):
            return
        action = data.get('action')
        if self.token_expired() or not await self.active_account():
            await self.close(code=4001)
            return
        if action == 'ping':
            self.last_ping = time.monotonic()
            from core.group_events import renew_socket_groups
            if not await renew_socket_groups(self, [self.room_name]):
                return
            await self.send_json({'action': 'pong'})
            return
        try:
            result = await self.execute(data)
            if result:
                await self.send_json(result)
            elif action in ('get_messages', 'set_topic'):
                await self.send_snapshot()
            elif action in ('typing_start', 'typing_stop') and time.monotonic() - self.last_typing > 1:
                self.last_typing = time.monotonic()
                await self.channel_layer.group_send(self.room_name, {'type': 'conversation_event', 'payload': {
                    'action': 'user_typing', 'user_id': self.user.pk, 'is_typing': action == 'typing_start',
                    'topic_id': self.topic_id,
                    'chat_id': self.chat.public_id, 'chat_type': service.chat_kind(self.chat),
                    'conversation_id': int(self.room_name.rsplit('_', 1)[1])}})
        except APIException as exc:
            await self.send_json({'action': 'error', 'error': str(exc.detail), 'status': exc.status_code,
                                  'client_message_id': data.get('client_message_id')})
            if exc.status_code in (403, 404):
                await self.close(code=4004)
            elif exc.status_code == 401:
                await self.close(code=4001)
        except User.DoesNotExist:
            await self.close(code=4001)
        except (type(self.chat).DoesNotExist, Message.DoesNotExist):
            await self.close(code=4004)

    async def active_account(self):
        if self.token_expired():
            return False
        from core.socket_auth import socket_user
        user = await socket_user(self.user.pk, getattr(self, 'token_claims', None), self.scope)
        if user is not None:
            self.user = user
        return user is not None

    async def can_receive(self):
        if not await self.active_account():
            return False
        from apps.social.application.live_projection import can_read_chat
        return await can_read_chat(self.chat, self.user)

    async def conversation_event(self, event):
        from core.telemetry import observe_publication, ws_phase
        observe_publication(event, 'room')
        recipients = event.get('recipients')
        if recipients is not None and self.user.pk not in recipients:
            return
        if self.token_expired():
            await self.close(code=4001)
            return
        allowed = await self.can_receive()
        if not allowed:
            await self.close(code=1013 if allowed is None else 4004)
            return
        from apps.social.application.live_projection import live_event
        payload = await live_event(event['payload'], self.user)
        if payload:
            with ws_phase('room', 'send'):
                await self.send_json(payload)
