import json
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from functools import partial
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import (
    PrivateChat,
    GroupChat,
    ChatMember,
    Message,
)
from apps.social.application.unread_count_service import unread_service
from core.online_status import online_status, typing_status
from core.socket_limits import SocketFrameBudget
from core.socket_credentials import socket_token, accepted_protocol
from django.conf import settings
import logging
from autobahn.exception import Disconnected


logger = logging.getLogger(__name__)


def _get_token_from_scope(scope):
    return socket_token(scope)

@database_sync_to_async
def resolve_chat_db_id(chat_id):
    try:
        chat_id_int = int(chat_id)
    except (TypeError, ValueError):
        return chat_id
    if PrivateChat.objects.filter(id=chat_id_int).exists() or GroupChat.objects.filter(id=chat_id_int).exists():
        return chat_id_int
    pc = PrivateChat.objects.filter(public_id=chat_id_int).first()
    if pc is not None:
        return pc.id
    gc = GroupChat.objects.filter(public_id=chat_id_int).first()
    if gc is not None:
        return gc.id
    return chat_id_int

EVENT_ACTION_ALIASES = {
    "message_sent": "new_message",
}

FLAT_EVENT_KEYS = (
    "chat_id",
    "chat_type",
    "message_id",
    "message_ids",
    "user_id",
    "username",
    "avatar",
    "is_typing",
    "is_online",
    "unread_count",
    "read_at",
    "chat",
    "message",
    "notification",
    "from_user_id",
    "from_username",
    "target_user_id",
    "post_id",
    "comment_id",
    "action",
)

class GlobalEventsConsumer(AsyncWebsocketConsumer):
    MAX_CONNECTIONS_PER_USER = 10
    PING_INTERVAL = 25
    CONNECTION_TIMEOUT = 60
    PRESENCE_OPERATION_TIMEOUT = 3

    _active_connections = defaultdict(set)
    _connection_lock = asyncio.Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frames = SocketFrameBudget()
        self.user = None
        self.token_expires = None
        self.user_id = None
        self.last_ping_time = None
        self.ping_check_task = None
        self.connected_at = None
        self._callback_registered = False
        self._presence_registered = False
        self.chat_groups = set()
        self.presence_groups = set()


    async def connect(self):
        token = _get_token_from_scope(self.scope)

        if token:
            self.user = await self.get_user_from_token(token)

        if not token and not self.user:
            if self.scope.get("user") and self.scope["user"].is_authenticated:
                self.user = self.scope["user"]

        if not self.user or not self.user.is_active:
            await self.close(code=4001)
            return
        
        self.user_id = self.user.id
        self.connected_at = timezone.now()
        
        async with self._connection_lock:
            user_connections = self._active_connections.get(self.user_id, set())
            user_connections = {conn for conn in user_connections if conn != self.channel_name}
            self._active_connections[self.user_id] = user_connections
            
            if len(user_connections) >= self.MAX_CONNECTIONS_PER_USER:
                logger.warning(f"User {self.user_id} exceeded max connections ({self.MAX_CONNECTIONS_PER_USER})")
                await self.close(code=4003)
                return
            
            self._active_connections[self.user_id].add(self.channel_name)
        
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)
        await self.accept(subprotocol=accepted_protocol(self.scope))

        self.last_ping_time = timezone.now()
        self.ping_check_task = asyncio.create_task(self._check_ping_timeout())

        from core.redis_client import redis_pubsub_manager
        if not getattr(redis_pubsub_manager, "_listener_started", False):
            redis_pubsub_manager.start()
            redis_pubsub_manager._listener_started = True
        redis_pubsub_manager.register_callback(
            "realtime_updates",
            self._send_event_to_client,
            asyncio.get_running_loop(),
        )
        self._callback_registered = True

        await database_sync_to_async(online_status.touch_connection, thread_sensitive=False)(
            self.user_id,
            self.user.username,
            self.channel_name,
        )
        self._presence_registered = True

        logger.info(f"WebSocket connected: user {self.user_id}")

    async def disconnect(self, close_code):
        if self._callback_registered:
            from core.redis_client import redis_pubsub_manager
            try:
                redis_pubsub_manager.unregister_callback("realtime_updates", self._send_event_to_client)
            except Exception as e:
                logger.warning(f"Не удалось отписать callback global WS: {e}")
            self._callback_registered = False

        if self.ping_check_task:
            self.ping_check_task.cancel()
            try:
                await self.ping_check_task
            except asyncio.CancelledError:
                pass

        for group in self.chat_groups | self.presence_groups:
            await self.channel_layer.group_discard(group, self.channel_name)
        self.chat_groups.clear()
        self.presence_groups.clear()

        if self.user_id:
            await self.channel_layer.group_discard(
                f"user_{self.user_id}", self.channel_name
            )
            async with self._connection_lock:
                conns = self._active_connections.get(self.user_id)
                if conns is not None:
                    conns.discard(self.channel_name)
                    if not conns:
                        del self._active_connections[self.user_id]

        if self._presence_registered:
            self._presence_registered = False
            try:
                await asyncio.wait_for(
                    database_sync_to_async(online_status.remove_connection, thread_sensitive=False)(
                        self.user_id,
                        self.user.username,
                        self.channel_name,
                    ),
                    timeout=self.PRESENCE_OPERATION_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Timed out while removing presence for user %s",
                    self.user_id,
                )

    async def _check_ping_timeout(self):
        try:
            while True:
                await asyncio.sleep(30)
                if not await self.authorized():
                    await self.close(code=4001)
                    return
                if self.last_ping_time:
                    elapsed = (timezone.now() - self.last_ping_time).total_seconds()
                    if elapsed > 60:
                        logger.info(f"Closing inactive connection for user {self.user_id}")
                        await self.close(code=4002)
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping check error: {e}")

    async def _send_event_to_client(self, event):
        try:
            target_users = event.get('target_users')
            if target_users is not None and self.user_id not in target_users:
                return
            if not await self.authorized():
                await self.close(code=4001)
                return
            event_type = event.get("event_type") or event.get("type")
            data = event.get("data", {})
            if not event_type:
                return

            target_users = event.get("target_users")
            if target_users is not None and self.user_id not in target_users:
                return

            if not isinstance(data, dict):
                data = {"value": data}

            action = EVENT_ACTION_ALIASES.get(event_type, event_type)

            data = await self.legacy_data_for_user(action, data)
            if data is None:
                return
            envelope = {"action": action, "data": data}
            if event.get('event_id'):
                envelope['event_id'] = str(event['event_id'])
            for key in FLAT_EVENT_KEYS:
                if key in data and key not in envelope:
                    envelope[key] = data[key]

            await asyncio.wait_for(self.send(text_data=json.dumps(envelope, default=str)), timeout=5)
        except asyncio.TimeoutError:
            await self.close(code=4008)
        except Exception as e:
            logger.info(f"Error sending event to client: {e}")

    async def legacy_event(self, event):
        await self._send_event_to_client(event['event'])

    async def user_online(self, event):
        await self._send_event_to_client(event['event'])

    async def receive(self, text_data=None, bytes_data=None):
        code = self.frames.reject_code(text_data)
        if code:
            await self.close(code=code)
            return
        try:
            if not await self.authorized():
                await self.close(code=4001)
                return
            data = json.loads(text_data)
            if not isinstance(data, dict):
                return
            action = data.get("action")

            if action == 'subscribe_presence':
                ids = data.get('user_ids', [])
                if not isinstance(ids, list) or len(ids) > 200 or any(type(pk) is not int or pk <= 0 for pk in ids):
                    return
                groups = {f'user_online_{pk}' for pk in ids}
                for group in self.presence_groups - groups:
                    await self.channel_layer.group_discard(group, self.channel_name)
                for group in groups - self.presence_groups:
                    await self.channel_layer.group_add(group, self.channel_name)
                self.presence_groups = groups
                return

            if action in ('ping', 'pong', 'presence'):
                is_active = data.get('is_active', True)
                if type(is_active) is not bool:
                    return
                self.last_ping_time = timezone.now()
                await database_sync_to_async(online_status.touch_connection, thread_sensitive=False)(
                    self.user_id, self.user.username, self.channel_name, is_active=is_active,
                )
                from core.group_events import renew_socket_groups
                if not await renew_socket_groups(self, {f'user_{self.user_id}'} | self.chat_groups | self.presence_groups):
                    return
                if action == 'ping':
                    await self.send(text_data=json.dumps({'action': 'pong'}))
            elif action in ("subscribe_chat", "unsubscribe_chat"):
                group = await self.resolve_subscription(data.get("chat_id"))
                if group:
                    if action == "subscribe_chat":
                        await self.channel_layer.group_add(group, self.channel_name)
                        self.chat_groups.add(group)
                    else:
                        await self.channel_layer.group_discard(group, self.channel_name)
                        self.chat_groups.discard(group)
        except json.JSONDecodeError:
            pass

    async def conversation_event(self, event):
        if self.user_id not in event.get('recipients', []):
            return
        if self.token_expires and self.token_expires <= timezone.now().timestamp():
            await self.close(code=4001)
            return
        if not await self.authorized():
            await self.close(code=4001)
            return
        from apps.social.application.live_projection import live_event
        payload = await live_event(event['payload'], self.user)
        if payload:
            await self.send(text_data=json.dumps(payload, default=str))

    async def notification_event(self, event):
        data = event.get("data", {"notification": event.get("notification", {})})
        await self._send_event_to_client({"event_type": event.get("event_type", event.get("action", "notification")),
                                          "data": data, "target_users": [self.user_id]})

    async def chat_message(self, event):
        if self.user_id in event.get("exclude_users", []):
            return
        data = event.get("data", {"message": event.get("message", {})})
        await self._send_event_to_client({"event_type": event.get("event_type", event.get("event", "new_message")),
                                          "data": data, "target_users": [self.user_id]})

    @partial(database_sync_to_async, thread_sensitive=False)
    def resolve_subscription(self, identifier):
        from apps.social.application.conversations import resolve_chat, check_access
        from rest_framework.exceptions import APIException
        try:
            chat = resolve_chat(identifier, self.user, 'group')
            check_access(chat, self.user)
            if ChatMember.objects.filter(chat=chat, user=self.user, is_banned=False).exists():
                return f'chat_{chat.pk}'
        except APIException:
            return None

    @partial(database_sync_to_async, thread_sensitive=False)
    def legacy_data_for_user(self, action, data):
        from apps.social.application.conversations import resolve_chat, visible_messages, serialize_message, get_conversation, chat_kind
        from rest_framework.exceptions import APIException
        message = data.get('message')
        if action in ('new_message', 'message_edited'):
            identifier = message.get('id') if isinstance(message, dict) else data.get('message_id')
            current = Message.objects.select_related('chat', 'private_chat').filter(pk=identifier).first()
            if current is None:
                return None
            try:
                if not visible_messages(current.parent_chat, self.user).filter(pk=current.pk).exists():
                    return None
            except APIException:
                return None
            chat = current.parent_chat
            return dict(data, message=serialize_message(current, self.user), chat_id=chat.public_id,
                        chat_type=chat_kind(chat), conversation_id=get_conversation(chat).pk)
        if data.get('chat_id') is not None:
            try:
                chat = resolve_chat(data['chat_id'], self.user, data.get('chat_type'))
            except APIException:
                return None
            data = dict(data, chat_id=chat.public_id, chat_type=chat_kind(chat))
        return data

    async def authorized(self):
        if self.token_expires and self.token_expires <= timezone.now().timestamp():
            return False
        from core.socket_auth import socket_user
        user = await socket_user(self.user_id, getattr(self, 'token_claims', None), self.scope)
        if user is not None:
            self.user = user
        return user is not None

    async def get_user_from_token(self, token):
        try:
            if len(token) > 4096:
                return None
            access_token = AccessToken(token)
            self.token_claims = access_token
            self.token_expires = access_token['exp']
            from core.socket_auth import socket_user
            return await socket_user(access_token['user_id'], access_token, self.scope)
        except (TokenError, AuthenticationFailed, KeyError):
            return None


class ChatConsumer(AsyncWebsocketConsumer):
    MAX_CONNECTIONS_PER_USER = 10
    PING_INTERVAL = 25
    CONNECTION_TIMEOUT = 60

    _active_connections: dict[int, set["ChatConsumer"]] = {}
    _connection_lock = asyncio.Lock()
    _cleanup_task = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = None
        self.chat_type = None
        self.user = None
        self.user_id = None
        self.group_name = None
        self.typing_task = None
        self.topic_id = None
        self.last_ping_time = None
        self.ping_check_task = None
        self.connected_at = None
        self._closed = False
        self.should_listen = True

    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        resolved = await resolve_chat_db_id(self.chat_id)
        if resolved is not None:
            self.chat_id = resolved
        self.group_name = f"chat_{self.chat_id}"

        token = _get_token_from_scope(self.scope)
        if token:
            self.user = await self.get_user_from_token(token)
        if not self.user:
            if self.scope.get("user") and self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
        if not self.user:
            await self.close(code=4001)
            return

        self.user_id = self.user.id

        self.chat_type = await self.get_chat_type()
        if not self.chat_type:
            logger.warning(
                f"WS connect denied: chat {self.chat_id} not found (user {self.user_id})"
            )
            await self.close(code=4004)
            return
        if not await self.check_chat_membership():
            logger.warning(
                f"WS connect denied: user {self.user_id} is not a member of "
                f"{self.chat_type} chat {self.chat_id}"
            )
            await self.close(code=4004)
            return

        self.connected_at = timezone.now()

        async with self._connection_lock:
            user_connections = self._active_connections.get(self.user_id, set())
            user_connections = {conn for conn in user_connections if not conn._closed}
            self._active_connections[self.user_id] = user_connections

            if len(user_connections) >= self.MAX_CONNECTIONS_PER_USER:
                logger.warning(f"Closing oldest connection for user {self.user_id} (limit {self.MAX_CONNECTIONS_PER_USER})")
                oldest_conn = next(iter(user_connections))
                user_connections.discard(oldest_conn)
                asyncio.get_running_loop().call_soon(
                    lambda: asyncio.create_task(oldest_conn.close(code=4003))
                )

            user_connections.add(self)
            self._active_connections[self.user_id] = user_connections

        await self.channel_layer.group_add(f"chat_{self.chat_id}", self.channel_name)
        self.user_personal_group = f"chat_user_{self.user_id}"
        await self.channel_layer.group_add(self.user_personal_group, self.channel_name)

        await self.accept()

        self.last_ping_time = timezone.now()
        self.ping_check_task = asyncio.create_task(self._check_ping_timeout())

        try:
            await self.send_initial_data()
        except Disconnected:
            pass
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")

        logger.info(f"WebSocket connected: user {self.user_id} to chat {self.chat_id}")

    async def disconnect(self, close_code):
        self._closed = True
        self.should_listen = False

        async with self._connection_lock:
            user_connections = self._active_connections.get(self.user_id, set())
            user_connections.discard(self)
            if not user_connections:
                self._active_connections.pop(self.user_id, None)
            else:
                self._active_connections[self.user_id] = user_connections

        if self.group_name:
            await self.channel_layer.group_discard(f"chat_{self.chat_id}", self.channel_name)
        if getattr(self, "user_personal_group", None):
            await self.channel_layer.group_discard(self.user_personal_group, self.channel_name)

        if self.ping_check_task:
            self.ping_check_task.cancel()
            try:
                await self.ping_check_task
            except asyncio.CancelledError:
                pass

        typing_status.stop_typing(self.chat_id, self.user_id)

        async with self._connection_lock:
            user_connections = self._active_connections.get(self.user_id, set())
            is_online = any(not conn._closed for conn in user_connections)

        if not is_online:
            online_status.set_offline(self.user_id)

        logger.info(f"WebSocket disconnected: user {self.user_id} from chat {self.chat_id}")

    async def _check_ping_timeout(self):
        try:
            while self.should_listen:
                await asyncio.sleep(30)
                if not self.should_listen:
                    break
                if not self.last_ping_time:
                    continue
                elapsed = (timezone.now() - self.last_ping_time).total_seconds()
                if elapsed > 60:
                    logger.info(f"Closing inactive connection for user {self.user_id} in chat {self.chat_id}")
                    await self.close(code=4002)
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping check error: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "ping":
                self.last_ping_time = timezone.now()
                await self.send(text_data=json.dumps({"action": "pong"}))
                return
            elif action == "send_message":
                await self.handle_send_message(data)
            elif action == "typing_start":
                await self.handle_typing_start()
            elif action == "typing_stop":
                await self.handle_typing_stop()
            elif action == "mark_read":
                await self.handle_mark_read(data)
            elif action == "get_messages":
                await self.send_initial_data()
            elif action == "set_topic":
                self.topic_id = data.get("topic_id")
                await self.send_initial_data()
            elif action == "subscribe_user_online":
                other_user_id = data.get("user_id")
                if other_user_id:
                    await self.handle_subscribe_user_online(other_user_id)
            elif action in ("block", "unblock"):
                await self._handle_block_action(data)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")

    async def handle_subscribe_user_online(self, other_user_id):
        try:
            other_user_id = int(other_user_id)
        except (TypeError, ValueError):
            return

        if not await self.is_related_user(other_user_id):
            logger.warning(
                f"subscribe_user_online denied: user {self.user_id} -> {other_user_id}"
            )
            return

        self.other_user_online_group = f"user_online_{other_user_id}"
        await self.channel_layer.group_add(
            self.other_user_online_group, self.channel_name
        )
        is_online = online_status.is_online(other_user_id)
        await self.send(
            text_data=json.dumps({
                "action": "user_online",
                "user_id": other_user_id,
                "is_online": is_online,
            })
        )

    @database_sync_to_async
    def is_related_user(self, other_user_id: int) -> bool:
        if other_user_id == self.user_id:
            return True
        if PrivateChat.objects.filter(
            Q(user1_id=self.user_id, user2_id=other_user_id)
            | Q(user1_id=other_user_id, user2_id=self.user_id)
        ).exists():
            return True
        my_chats = ChatMember.objects.filter(user_id=self.user_id).values_list(
            "chat_id", flat=True
        )
        return ChatMember.objects.filter(
            chat_id__in=list(my_chats), user_id=other_user_id
        ).exists()

    async def chat_message(self, event):
        if self.user_id == event.get("sender_id"):
            return
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "new_message",
                    "message": event.get("message", {}),
                })
            )
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")

    async def typing_status(self, event):
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "user_typing",
                    "chat_id": int(self.chat_id) if self.chat_id else None,
                    "chat_type": self.chat_type,
                    "user_id": event.get("user_id"),
                    "username": event.get("username"),
                    "is_typing": event.get("is_typing", False),
                    "startTime": event.get("startTime", timezone.now().isoformat()),
                })
            )
        except Exception as e:
            logger.error(f"Error sending typing status: {e}")

    async def user_online(self, event):
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "user_online",
                    "user_id": event.get("user_id"),
                    "is_online": event.get("is_online", True),
                    "username": event.get("username"),
                })
            )
        except Exception as e:
            logger.error(f"Error sending user online: {e}")

    async def messages_read_event(self, event):
        if self.user_id == event.get("user_id"):
            return
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "messages_read",
                    "user_id": event.get("user_id"),
                    "message_ids": event.get("message_ids", []),
                    "read_at": event.get("read_at"),
                })
            )
        except Exception as e:
            logger.error(f"Error sending messages read: {e}")

    async def chat_cleared(self, event):
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "chat_cleared",
                    "chat_id": event.get("chat_id"),
                    "cleared_at": timezone.now().isoformat(),
                })
            )
        except Exception as e:
            logger.error(f"Error sending chat cleared: {e}")

    async def member_left(self, event):
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "member_left",
                    "user_id": event.get("user_id"),
                    "username": event.get("username"),
                    "chat_id": event.get("chat_id"),
                })
            )
        except Exception as e:
            logger.error(f"Error sending member_left: {e}")

    async def message_deleted(self, event):
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "message_deleted",
                    "message_id": event.get("message_id"),
                    "chat_id": event.get("chat_id"),
                })
            )
        except Exception as e:
            logger.error(f"Error sending message deleted: {e}")

    async def message_edited(self, event):
        try:
            await self.send(
                text_data=json.dumps({
                    "action": "message_edited",
                    "message": event.get("message", {}),
                }, default=str)
            )
        except Exception as e:
            logger.error(f"Error sending message edited: {e}")

    async def block_event(self, event):
        await self._handle_block_unblock_event(event, 'block')

    async def unblock_event(self, event):
        await self._handle_block_unblock_event(event, 'unblock')

    async def _handle_block_unblock_event(self, event, action):
        try:
            chat_id = event.get('chat_id')
            user_id = event.get('user_id')
            target_user_id = event.get('target_user_id')
            username = event.get('username', 'Пользователь')
            created_at = event.get('created_at', timezone.now().isoformat())
            
            from apps.social.infrastructure.models.social import Message, PrivateChat
            from apps.users.infrastructure.models.users import User
            
            chat = await database_sync_to_async(PrivateChat.objects.get)(id=chat_id)
            sender = await database_sync_to_async(User.objects.get)(id=user_id)
            
            existing = await database_sync_to_async(
                lambda: Message.objects.filter(
                    private_chat=chat,
                    system_action=action,
                    created_at__gte=timezone.now() - timedelta(seconds=2)
                ).exists()
            )()
            
            if existing:
                return
            
            msg = await database_sync_to_async(Message.objects.create)(
                private_chat=chat,
                sender=sender,
                text="",
                message_type="system",
                system_action=action,
            )
            
            from apps.social.presentation.serializers.social_serializers import MessageSerializer
            from django.http import HttpRequest
            
            mock_request = HttpRequest()
            mock_request.user = sender
            serializer = MessageSerializer(msg, context={"request": mock_request})
            message_data = serializer.data
            
            await self.channel_layer.group_send(
                f"chat_{chat_id}",
                {
                    "type": "chat_message",
                    "message": message_data,
                    "sender_id": user_id,
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling {action} event: {e}")

    async def _handle_block_action(self, data):
        chat_id = data.get("chat_id")
        target_user_id = data.get("target_user_id")
        action = data.get("action")
        sender_id = data.get("sender_id")
        
        from apps.social.infrastructure.models.social import Message
        from apps.social.infrastructure.models.social import PrivateChat
        from apps.users.infrastructure.models.users import User
        
        try:
            chat = await database_sync_to_async(PrivateChat.objects.get)(id=chat_id)
            sender = await database_sync_to_async(User.objects.get)(id=sender_id)
            
            msg = await database_sync_to_async(Message.objects.create)(
                private_chat=chat,
                sender=sender,
                text="",
                message_type="system",
                system_action=action,
            )
            
            from apps.social.presentation.serializers.social_serializers import MessageSerializer
            from django.http import HttpRequest
            
            mock_request = HttpRequest()
            mock_request.user = sender
            serializer = MessageSerializer(msg, context={"request": mock_request})
            message_data = serializer.data
            
            await self.channel_layer.group_send(
                f"chat_{chat_id}",
                {
                    "type": "chat_message",
                    "message": message_data,
                    "sender_id": sender_id,
                }
            )
        except Exception as e:
            logger.error(f"Error handling block action: {e}")

    async def handle_typing_start(self):
        if not self.user or not self.chat_id:
            return
        typing_status.set_typing(self.chat_id, self.user_id, self.user.username)
        await self._broadcast_typing(True)
        if self.typing_task:
            self.typing_task.cancel()
        self.typing_task = asyncio.create_task(self._auto_stop_typing())

    async def handle_typing_stop(self):
        if not self.user or not self.chat_id:
            return
        typing_status.stop_typing(self.chat_id, self.user_id)
        await self._broadcast_typing(False)

    async def _broadcast_typing(self, is_typing: bool):
        payload = {
            "chat_id": int(self.chat_id),
            "chat_type": self.chat_type,
            "user_id": self.user_id,
            "username": self.user.username,
            "is_typing": is_typing,
        }
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_status",
                "user_id": self.user_id,
                "username": self.user.username,
                "is_typing": is_typing,
                "startTime": timezone.now().isoformat(),
            },
        )
        await self.publish_to_global("user_typing", payload)

    async def _auto_stop_typing(self):
        await asyncio.sleep(5)
        await self.handle_typing_stop()

    async def handle_mark_read(self, data):
        message_ids = data.get("message_ids", [])
        if not message_ids or not self.user_id:
            return

        updated = await self.mark_messages_read(message_ids, self.user_id)
        unread_service.decrement(self.chat_id, self.user_id)

        from apps.social.application.tasks import create_message_read_status
        for message_id in message_ids:
            create_message_read_status.delay(message_id, self.user_id)

        read_payload = {
            "chat_id": int(self.chat_id),
            "chat_type": self.chat_type,
            "user_id": self.user_id,
            "message_ids": message_ids,
            "read_at": timezone.now().isoformat(),
        }

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "messages_read_event",
                "user_id": self.user_id,
                "message_ids": message_ids,
                "read_at": read_payload["read_at"],
            },
        )
        await self.publish_to_global("messages_read", read_payload)

        try:
            participant_ids = await self.get_participant_ids()
        except Exception:
            participant_ids = []
        for uid in participant_ids:
            if uid == self.user_id:
                continue
            await self.publish_to_global(
                "unread_updated",
                {
                    "user_id": uid,
                    "chat_id": int(self.chat_id),
                    "unread_count": unread_service.get_for_chat(uid, self.chat_id),
                },
            )
        return updated

    async def handle_send_message(self, data):
        text = data.get("text", "").strip()
        reply_to_id = data.get("reply_to_id")
        if not text:
            return

        message = await self.create_message(text, self.topic_id, reply_to_id)
        if not message:
            return

        message_data = await self.serialize_message(message)
        message_data.pop("is_mine", None)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message_data,
                "sender_id": self.user_id,
            },
        )

        from apps.social.application.tasks import process_message_post_save

        process_message_post_save.delay(message.id)

        await self.publish_to_global(
            "new_message",
            {
                "message": message_data,
                "chat_id": int(self.chat_id),
                "chat_type": self.chat_type,
            },
        )

    @database_sync_to_async
    def get_participant_ids(self):
        if self.chat_type == "private":
            return list(
                PrivateChat.objects.filter(id=self.chat_id).values_list(
                    "user1_id", "user2_id"
                )
            )[0]
        return list(
            ChatMember.objects.filter(chat_id=self.chat_id).values_list(
                "user_id", flat=True
            )
        )

    async def publish_to_global(self, event_type, data):
        try:
            participant_ids = await self.get_participant_ids()
        except Exception as e:
            logger.warning(f"publish_to_global: не удалось получить участников: {e}")
            return
        from core.redis_events import event_publisher

        event_publisher.publish_event(
            event_type, data, target_users=list(participant_ids)
        )

    async def send_initial_data(self):
        try:
            messages = await self.get_recent_messages()
            online_users = await self.get_online_users()
            other_user_data = None
            if self.chat_type == "private" and self.user:
                other_user_data = await self.get_other_user_data()

            await self.send(
                text_data=json.dumps({
                    "action": "init",
                    "messages": messages,
                    "online_users": online_users,
                    "other_user": other_user_data,
                }, default=str)
            )
        except Exception as e:
            logger.error(f"Error in send_initial_data: {e}")

    @database_sync_to_async
    def get_other_user_data(self):
        try:
            private_chat = PrivateChat.objects.get(id=self.chat_id)
            other_user = private_chat.other_user(self.user)
            if other_user:
                is_online = online_status.is_online(other_user.id)
                return {
                    "id": other_user.id,
                    "username": other_user.username,
                    "display_name": other_user.display_name,
                    "avatar": other_user.avatar.url if other_user.avatar else None,
                    "is_online": is_online,
                }
        except Exception as e:
            logger.error(f"Error getting other user data: {e}")
        return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def get_chat_type(self):
        if PrivateChat.objects.filter(id=self.chat_id).exists():
            return "private"
        elif GroupChat.objects.filter(id=self.chat_id).exists():
            return "group"
        return None

    @database_sync_to_async
    def check_chat_membership(self):
        if self.chat_type == "private":
            return PrivateChat.objects.filter(id=self.chat_id).filter(
                Q(user1_id=self.user_id) | Q(user2_id=self.user_id)
            ).exists()
        if self.chat_type == "group":
            chat = GroupChat.objects.filter(id=self.chat_id).first()
            if chat and chat.folder_type == 'discussions' and chat.is_public:
                return True
            return ChatMember.objects.filter(
                chat_id=self.chat_id, user_id=self.user_id
            ).exists()
        return False

    @database_sync_to_async
    def get_recent_messages(self):
        from apps.social.presentation.serializers.social_serializers import MessageSerializer
        messages = []
        msg_qs = None

        if self.chat_type == "private":
            msg_qs = (
                Message.objects.filter(private_chat_id=self.chat_id)
                .select_related("sender", "reply_to__sender")
                .prefetch_related("read_statuses")
                .order_by("-created_at")[:50]
            )
        elif self.chat_type == "group":
            if self.topic_id is not None and self.topic_id != 0:
                msg_qs = (
                    Message.objects.filter(chat_id=self.chat_id, topic_id=self.topic_id)
                    .select_related("sender", "reply_to__sender")
                    .prefetch_related("read_statuses")
                    .order_by("-created_at")[:50]
                )
            else:
                msg_qs = (
                    Message.objects.filter(chat_id=self.chat_id)
                    .select_related("sender", "reply_to__sender")
                    .prefetch_related("read_statuses")
                    .order_by("-created_at")[:50]
                )

        if msg_qs:
            messages_qs = msg_qs[:30]
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                @property
                def is_authenticated(self):
                    return True
                def build_absolute_uri(self, location=None):
                    if location:
                        if location.startswith('http://') or location.startswith('http://'):
                            return location
                        return location
                    return ""

            mock_request = MockRequest(self.user) if self.user else None
            for m in messages_qs:
                try:
                    serializer = MessageSerializer(m, context={"request": mock_request})
                    messages.append(serializer.data)
                except Exception as e:
                    logger.error(f"Error serializing message {m.id}: {e}")

        return list(reversed(messages))

    @database_sync_to_async
    def create_message(self, text, topic_id=None, reply_to_id=None):
        try:
            if self.chat_type not in ("private", "group"):
                logger.error(
                    f"create_message: unknown chat type for chat {self.chat_id}"
                )
                return None
            msg_data = {"text": text, "sender_id": self.user_id}
            if self.chat_type == "private":
                msg_data["private_chat_id"] = self.chat_id
            else:
                msg_data["chat_id"] = self.chat_id
            if topic_id:
                msg_data["topic_id"] = topic_id
            if reply_to_id:
                try:
                    reply_to_message = Message.objects.filter(
                        id=reply_to_id
                    ).filter(self._chat_scope_q()).first()
                    if reply_to_message:
                        msg_data["reply_to"] = reply_to_message
                except (Message.DoesNotExist, ValueError):
                    pass
            msg = Message.objects.create(**msg_data)
            return msg
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    def _chat_scope_q(self):
        if self.chat_type == "private":
            return Q(private_chat_id=self.chat_id)
        return Q(chat_id=self.chat_id)

    @database_sync_to_async
    def serialize_message(self, message):
        from apps.social.presentation.serializers.social_serializers import MessageSerializer
        from django.http import HttpRequest

        message = Message.objects.select_related("sender", "reply_to__sender").get(id=message.id)
        try:
            mock_request = HttpRequest()
            mock_request.user = self.user
            serializer = MessageSerializer(message, context={"request": mock_request})
            return serializer.data
        except Exception as e:
            logger.error(f"Error serializing message: {e}")
            return {"id": message.id, "text": message.text, "sender_id": message.sender_id}

    @database_sync_to_async
    def mark_messages_read(self, message_ids, user_id):
        if not isinstance(message_ids, (list, tuple, set)):
            return 0
        safe_ids = [mid for mid in message_ids if isinstance(mid, int)]
        if not safe_ids:
            return 0
        if self.chat_type == "private":
            scope = Q(private_chat_id=self.chat_id)
        elif self.chat_type == "group":
            scope = Q(chat_id=self.chat_id)
        else:
            return 0
        return Message.objects.filter(id__in=safe_ids).filter(scope).update(
            read_at=timezone.now()
        )

    @database_sync_to_async
    def get_online_users(self):
        return [uid for uid in online_status.get_online_users()]


class TypingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = None
        self.group_name = None

    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        resolved = await resolve_chat_db_id(self.chat_id)
        if resolved is not None:
            self.chat_id = resolved
        self.group_name = f"typing_{self.chat_id}"

        token = _get_token_from_scope(self.scope)
        if token:
            self.user = await self.get_user_from_token(token)
        if not self.user:
            if self.scope.get("user") and self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
        if not self.user:
            await self.close(code=4001)
            return

        self.user_id = self.user.id

        if not await self.check_chat_membership():
            logger.warning(
                f"Typing WS denied: user {self.user_id} is not a member of chat {self.chat_id}"
            )
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def check_chat_membership(self):
        if PrivateChat.objects.filter(id=self.chat_id).filter(
            Q(user1_id=self.user_id) | Q(user2_id=self.user_id)
        ).exists():
            return True
        chat = GroupChat.objects.filter(id=self.chat_id).first()
        if chat and chat.folder_type == 'discussions' and chat.is_public:
            return True
        return ChatMember.objects.filter(
            chat_id=self.chat_id, user_id=self.user_id
        ).exists()

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "typing_start":
                await self.handle_typing_start(data)
            elif action == "typing_stop":
                await self.handle_typing_stop(data)
            elif action == "ping":
                await self.send(text_data=json.dumps({"action": "pong"}))
        except json.JSONDecodeError:
            pass

    async def handle_typing_start(self, data):
        user_id = self.user_id
        username = getattr(self.user, "username", None) or data.get("username", "Unknown")

        typing_status.set_typing(self.chat_id, user_id, username)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_indicator",
                "action": "typing_start",
                "chat_id": self.chat_id,
                "user_id": user_id,
                "username": username,
                "startTime": timezone.now().isoformat(),
            },
        )

    async def typing_indicator(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "action": "user_typing",
                    "chat_id": event.get("chat_id") or self.chat_id,
                    "user_id": event.get("user_id"),
                    "username": event.get("username"),
                    "is_typing": event.get("action") == "typing_start",
                    "startTime": event.get("startTime", timezone.now().isoformat()),
                }
            )
        )

    async def handle_typing_stop(self, data):
        user_id = self.user_id

        typing_status.stop_typing(self.chat_id, user_id)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_indicator",
                "action": "typing_stop",
                "chat_id": self.chat_id,
                "user_id": user_id,
                "startTime": timezone.now().isoformat(),
            },
        )
