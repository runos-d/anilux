import json
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

ONLINE_KEY_PREFIX = 'user_online:'
ONLINE_TTL = 120
AWAY_TTL = 60
PRESENCE_SESSIONS_PREFIX = 'user_presence_sessions:'

TOUCH_CONNECTION = """
local was_online = redis.call('EXISTS', KEYS[1])
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', ARGV[1])
redis.call('ZADD', KEYS[2], ARGV[2], ARGV[3])
redis.call('EXPIRE', KEYS[2], ARGV[4])
redis.call('SETEX', KEYS[1], ARGV[4], ARGV[5])
return 1 - was_online
"""
REMOVE_CONNECTION = """
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', ARGV[1])
redis.call('ZREM', KEYS[2], ARGV[2])
if redis.call('ZCARD', KEYS[2]) == 0 then
    redis.call('DEL', KEYS[2])
    return redis.call('DEL', KEYS[1])
end
return 0
"""
REFRESH_PRESENCE = """
if ARGV[3] == '1' then
    redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', ARGV[4])
    if redis.call('ZCARD', KEYS[2]) == 0 then return 0 end
end
local was_online = redis.call('EXISTS', KEYS[1])
local ttl = math.max(tonumber(ARGV[1]), redis.call('TTL', KEYS[1]))
redis.call('SETEX', KEYS[1], ttl, ARGV[2])
return 1 - was_online
"""


class RedisOnlineStatus:
    def __init__(self):
        self._connection_error_logged = False

    def _get_client(self):
        from core.redis_client import redis_pubsub_manager
        try:
            return redis_pubsub_manager._get_redis_client()
        except Exception as e:
            if not self._connection_error_logged:
                logger.warning(f"Redis не доступен для статуса онлайн: {e}")
                self._connection_error_logged = True
            return None

    def set_online(self, user_id: int, username: str, extra_data: Optional[Dict[str, Any]] = None, is_active: bool = True, require_connection: bool = False) -> None:
        client = self._get_client()
        if client is None:
            return

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            now = timezone.now()
            ttl = ONLINE_TTL if is_active else AWAY_TTL
            data = {
                'user_id': user_id,
                'username': username,
                'last_seen': now.isoformat(),
                'last_seen_ts': now.timestamp(),
                'is_active': is_active,
                **(extra_data or {})
            }
            if client.eval(REFRESH_PRESENCE, 2, key, f'{PRESENCE_SESSIONS_PREFIX}{user_id}',
                           ttl, json.dumps(data), int(require_connection), now.timestamp()) == 1:
                self._send_online_event(user_id, username, True)
        except Exception as e:
            logger.debug(f"Redis set_online error (ignored): {e}")

    def touch_connection(self, user_id, username, connection_id):
        client = self._get_client()
        if client is None:
            return
        try:
            now = timezone.now()
            data = json.dumps({'user_id': user_id, 'username': username,
                               'last_seen': now.isoformat(), 'last_seen_ts': now.timestamp(),
                               'is_active': True})
            changed = client.eval(TOUCH_CONNECTION, 2, f'{ONLINE_KEY_PREFIX}{user_id}',
                                  f'{PRESENCE_SESSIONS_PREFIX}{user_id}', now.timestamp(),
                                  now.timestamp() + ONLINE_TTL, connection_id, ONLINE_TTL, data)
            if changed == 1:
                self._send_online_event(user_id, username, True)
        except Exception as exc:
            logger.debug('Redis connection presence error: %s', exc)

    def remove_connection(self, user_id, username, connection_id):
        client = self._get_client()
        if client is None:
            return
        try:
            changed = client.eval(REMOVE_CONNECTION, 2, f'{ONLINE_KEY_PREFIX}{user_id}',
                                  f'{PRESENCE_SESSIONS_PREFIX}{user_id}',
                                  timezone.now().timestamp(), connection_id)
            if changed == 1:
                self._send_online_event(user_id, username, False)
        except Exception as exc:
            logger.debug('Redis connection removal error: %s', exc)

    def _send_online_event(self, user_id: int, username: str, is_online: bool) -> None:
        if is_online:
            publish_user_online_event(user_id, username)
        else:
            publish_user_offline_event(user_id, username)
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f"user_online_{user_id}"
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "user_online",
                        "user_id": user_id,
                        "username": username,
                        "is_online": is_online,
                    }
                )
        except Exception as e:
            logger.debug(f"Channel layer send error: {e}")

    def set_offline(self, user_id: int) -> None:
        client = self._get_client()
        if client is None:
            return

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            changed = client.delete(key, f'{PRESENCE_SESSIONS_PREFIX}{user_id}')
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            username = User.objects.filter(id=user_id).values_list('username', flat=True).first() or 'Unknown'
            if changed:
                self._send_online_event(user_id, username, False)
        except Exception as e:
            logger.debug(f"Redis set_offline error (ignored): {e}")

    def is_online(self, user_id: int) -> bool:
        client = self._get_client()
        if client is None:
            return False

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            return client.exists(key) > 0
        except Exception as e:
            logger.debug(f"Redis is_online error (ignored): {e}")
            return False

    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        client = self._get_client()
        if client is None:
            return None

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            data = client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Redis get_user_data error (ignored): {e}")
            return None

    def get_users_data(self, user_ids):
        ids = list(set(user_ids))
        client = self._get_client()
        if client is None or not ids:
            return {}
        try:
            rows = client.mget([f'{ONLINE_KEY_PREFIX}{pk}' for pk in ids])
            result = {}
            for pk, raw in zip(ids, rows):
                if raw:
                    try:
                        data = json.loads(raw)
                        if isinstance(data, dict):
                            result[pk] = data
                    except (ValueError, TypeError):
                        continue
            return result
        except Exception as exc:
            logger.debug('Redis batch online status error: %s', exc)
            return {}

    def get_online_users(self) -> list:
        client = self._get_client()
        if client is None:
            return []

        try:
            pattern = f"{ONLINE_KEY_PREFIX}*"
            keys = client.keys(pattern)
            users = []
            for key in keys:
                data = client.get(key)
                if data:
                    try:
                        users.append(json.loads(data))
                    except json.JSONDecodeError:
                        continue
            return users
        except Exception as e:
            logger.debug(f"Redis get_online_users error (ignored): {e}")
            return []

    def refresh_online(self, user_id: int, username: str) -> None:
        self.set_online(user_id, username)


TYPING_KEY_PREFIX = 'typing:'
TYPING_TTL = 5


class RedisTypingStatus:
    def __init__(self):
        self._connection_error_logged = False

    def _get_client(self):
        from core.redis_client import redis_pubsub_manager
        try:
            return redis_pubsub_manager._get_redis_client()
        except Exception as e:
            if not self._connection_error_logged:
                logger.warning(f"Redis не доступен для статуса печатания: {e}")
                self._connection_error_logged = True
            return None

    def set_typing(self, chat_id: int, user_id: int, username: str) -> None:
        client = self._get_client()
        if client is None:
            return

        try:
            key = f"{TYPING_KEY_PREFIX}{chat_id}:{user_id}"
            data = json.dumps({
                'user_id': user_id,
                'username': username,
                'timestamp': timezone.now().isoformat()
            })
            client.setex(key, TYPING_TTL, data)
        except Exception as e:
            logger.debug(f"Redis set_typing error (ignored): {e}")

    def stop_typing(self, chat_id: int, user_id: int) -> None:
        client = self._get_client()
        if client is None:
            return

        try:
            key = f"{TYPING_KEY_PREFIX}{chat_id}:{user_id}"
            client.delete(key)
        except Exception as e:
            logger.debug(f"Redis stop_typing error (ignored): {e}")

    def is_typing(self, chat_id: int, user_id: int) -> bool:
        client = self._get_client()
        if client is None:
            return False

        try:
            key = f"{TYPING_KEY_PREFIX}{chat_id}:{user_id}"
            return client.exists(key) > 0
        except Exception as e:
            logger.debug(f"Redis is_typing error (ignored): {e}")
            return False

    def get_typing_users(self, chat_id: int) -> list:
        client = self._get_client()
        if client is None:
            return []

        try:
            pattern = f"{TYPING_KEY_PREFIX}{chat_id}:*"
            keys = client.keys(pattern)
            typing_users = []
            for key in keys:
                data = client.get(key)
                if data:
                    try:
                        typing_users.append(json.loads(data))
                    except json.JSONDecodeError:
                        continue
            return typing_users
        except Exception as e:
            logger.debug(f"Redis get_typing_users error (ignored): {e}")
            return []

    def stop_all_typing(self, chat_id: int) -> None:
        client = self._get_client()
        if client is None:
            return

        try:
            pattern = f"{TYPING_KEY_PREFIX}{chat_id}:*"
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
        except Exception as e:
            logger.debug(f"Redis stop_all_typing error (ignored): {e}")


online_status = RedisOnlineStatus()
typing_status = RedisTypingStatus()


def publish_user_online_event(user_id: int, username: str) -> None:
    from core.redis_events import publish_user_online as redis_publish
    try:
        redis_publish(user_id, username)
    except Exception:
        pass 

def publish_user_offline_event(user_id: int, username: str) -> None:
    from core.redis_events import publish_user_offline as redis_publish
    try:
        redis_publish(user_id, username)
    except Exception:
        pass
