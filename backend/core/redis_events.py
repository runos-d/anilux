from django.utils import timezone
import json
from django.conf import settings
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class RedisEventPublisher:
    def __init__(self):
        self._connection_error_logged = False

    def _get_client(self):
        from core.redis_client import redis_pubsub_manager
        try:
            return redis_pubsub_manager._get_redis_client()
        except Exception as e:
            if not self._connection_error_logged:
                logger.warning(f"Redis не доступен: {e}. Функционал реального времени отключен.")
                self._connection_error_logged = True
            return None

    def publish_event(self, event_type: str, data: Dict[str, Any], target_users: Optional[list] = None) -> None:
        client = self._get_client()
        if client is None:
            return

        try:
            event = {
                'type': event_type,
                'data': data,
                'timestamp': self._get_timestamp(),
                'target_users': target_users
            }

            channel = 'realtime_updates'
            client.publish(channel, json.dumps(event))

            queue_key = 'realtime_queue'
            client.lpush(queue_key, json.dumps(event))

            client.ltrim(queue_key, 0, 99)
        except Exception as e:
            logger.debug(f"Redis error: {e}")

    def get_recent_events(self, limit: int = 50) -> list:
        client = self._get_client()
        if client is None:
            return []

        try:
            queue_key = 'realtime_queue'
            events_data = client.lrange(queue_key, 0, limit - 1)
            events = []
            for event_data in events_data:
                try:
                    events.append(json.loads(event_data))
                except json.JSONDecodeError:
                    continue
            return events
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return []

    def _get_timestamp(self) -> str:
        from django.utils import timezone
        return timezone.now().isoformat()


event_publisher = RedisEventPublisher()


def publish_post_created(post_data: Dict[str, Any]) -> None:
    event_publisher.publish_event('post_created', post_data)


def publish_post_updated(post_data: Dict[str, Any]) -> None:
    event_publisher.publish_event('post_updated', post_data)


def publish_post_deleted(post_id: int) -> None:
    event_publisher.publish_event('post_deleted', {'post_id': post_id})


def publish_user_online(user_id: int, username: str) -> None:
    event_publisher.publish_event('user_online', {
        'user_id': user_id,
        'username': username
    })


def publish_user_offline(user_id: int, username: str) -> None:
    event_publisher.publish_event('user_offline', {
        'user_id': user_id,
        'username': username
    })


def publish_chat_created(chat_data: Dict[str, Any]) -> None:
    event_publisher.publish_event('chat_created', chat_data)


def publish_chat_deleted(chat_id: int, chat_type: str, user_ids: list) -> None:
    event_publisher.publish_event('chat_deleted', {
        'chat_id': chat_id,
        'chat_type': chat_type,
        'affected_users': user_ids
    })


def publish_user_typing(chat_id: int, user_id: int, username: str, is_typing: bool) -> None:
    event_publisher.publish_event('user_typing', {
        'chat_id': chat_id,
        'user_id': user_id,
        'username': username,
        'is_typing': is_typing
    })


def publish_message_sent(message_data: Dict[str, Any]) -> None:
    event_publisher.publish_event('message_sent', message_data)


def publish_new_message(message_data: Dict[str, Any], chat_id: int, chat_type: str, participant_ids: list) -> None:
    event_publisher.publish_event('new_message', {
        'message': message_data,
        'chat_id': chat_id,
        'chat_type': chat_type
    }, target_users=participant_ids)


def publish_messages_read(chat_id: int, chat_type: str, user_id: int, message_ids: List[int], read_at: str, target_users: Optional[list] = None) -> None:
    event_publisher.publish_event('messages_read', {
        'chat_id': chat_id,
        'chat_type': chat_type,
        'user_id': user_id,
        'message_ids': message_ids,
        'read_at': read_at
    }, target_users=target_users)


def publish_unread_updated(user_id: int, chat_id: int, unread_count: int) -> None:
    event_publisher.publish_event('unread_updated', {
        'user_id': user_id,
        'chat_id': chat_id,
        'unread_count': unread_count
    }, target_users=[user_id])


def publish_anime_updated(anime_data: Dict[str, Any]) -> None:
    event_publisher.publish_event('anime_updated', anime_data)


def publish_settings_update(user_id: int, updated_fields: list) -> None:
    event_publisher.publish_event('settings_updated', {
        'user_id': user_id,
        'updated_fields': updated_fields
    })


def publish_avatar_update(user_id: int, avatar_url: Optional[str]) -> None:
    event_publisher.publish_event('avatar_updated', {
        'user_id': user_id,
        'avatar_url': avatar_url
    })


def publish_profile_update(user_id: int, profile_data: Dict[str, Any]) -> None:
    event_publisher.publish_event('profile_updated', {
        'user_id': user_id,
        'profile_data': profile_data
    })


def publish_password_changed(user_id: int) -> None:
    event_publisher.publish_event('password_changed', {
        'user_id': user_id,
        'timestamp': timezone.now().isoformat()
    })


def publish_follow_event(follower_id: int, follower_username: str, target_user_id: int, action: str) -> None:
    event_publisher.publish_event(action, {
        'from_user_id': follower_id,
        'from_username': follower_username,
        'target_user_id': target_user_id,
        'timestamp': timezone.now().isoformat()
    }, target_users=[target_user_id])