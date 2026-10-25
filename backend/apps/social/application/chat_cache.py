import json
from typing import List, Dict, Optional, Any
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class ChatCacheService:
    TTL_LAST_MESSAGES = 86400  
    TTL_CHAT_INFO = 3600  
    TTL_USER_INFO = 3600  
    TTL_TYPING = 5  

    @staticmethod
    def _get_chat_last_messages_key(chat_id: int) -> str:
        return f"chat:{chat_id}:last_messages"

    @staticmethod
    def _get_chat_last_message_key(chat_id: int) -> str:
        return f"chat:{chat_id}:last_message"

    @staticmethod
    def _get_chat_info_key(chat_id: int) -> str:
        return f"chat:{chat_id}:info"

    @staticmethod
    def _get_user_info_key(user_id: int) -> str:
        return f"user:{user_id}:info"

    @staticmethod
    def _get_user_unread_chat_key(user_id: int, chat_id: int) -> str:
        return f"user:{user_id}:unread:{chat_id}"

    @staticmethod
    def _get_user_unread_total_key(user_id: int) -> str:
        return f"user:{user_id}:unread:total"

    @staticmethod
    def _get_user_unread_chats_key(user_id: int) -> str:
        return f"user:{user_id}:unread_chats"

    @staticmethod
    def _get_typing_key(chat_id: int, user_id: int) -> str:
        return f"typing:{chat_id}:{user_id}"

    @staticmethod
    def _serialize_message(message: Any) -> Dict:
        return {
            'id': message.id,
            'sender_id': message.sender_id,
            'text': message.text,
            'media_type': message.media_type,
            'media_url': message.media.url if message.media else None,
            'created_at': message.created_at.isoformat(),
            'is_edited': message.is_edited,
            'is_deleted': message.is_deleted,
            'is_pinned': message.is_pinned,
            'reply_to_id': message.reply_to_id,
            'forwarded_from_id': message.forwarded_from_id,
            'reactions': message.reactions,
        }

    @staticmethod
    def get_last_messages(chat_id: int, limit: int = 50) -> List[Dict]:
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        cached = cache.get(key)

        if cached:
            return cached[:limit]

        return []

    @staticmethod
    def add_message_to_cache(chat_id: int, message: Any, max_cached: int = 50) -> None:
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        messages = ChatCacheService.get_last_messages(chat_id, max_cached)

        serialized = ChatCacheService._serialize_message(message)
        messages.append(serialized)

        if len(messages) > max_cached:
            messages = messages[-max_cached:]

        cache.set(key, messages, ChatCacheService.TTL_LAST_MESSAGES)

        ChatCacheService.set_last_message(chat_id, serialized)

    @staticmethod
    def update_message_in_cache(chat_id: int, message_id: int, updates: Dict) -> None:
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        messages = ChatCacheService.get_last_messages(chat_id)

        for msg in messages:
            if msg['id'] == message_id:
                msg.update(updates)
                break

        cache.set(key, messages, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def remove_message_from_cache(chat_id: int, message_id: int) -> None:
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        messages = ChatCacheService.get_last_messages(chat_id)

        messages = [msg for msg in messages if msg['id'] != message_id]
        cache.set(key, messages, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def set_last_message(chat_id: int, message: Dict) -> None:
        key = ChatCacheService._get_chat_last_message_key(chat_id)
        cache.set(key, message, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def get_last_message(chat_id: int) -> Optional[Dict]:
        key = ChatCacheService._get_chat_last_message_key(chat_id)
        return cache.get(key)

    @staticmethod
    def set_chat_info(chat_id: int, info: Dict) -> None:
        key = ChatCacheService._get_chat_info_key(chat_id)
        cache.set(key, info, ChatCacheService.TTL_CHAT_INFO)

    @staticmethod
    def get_chat_info(chat_id: int) -> Optional[Dict]:
        key = ChatCacheService._get_chat_info_key(chat_id)
        return cache.get(key)

    @staticmethod
    def invalidate_chat_info(chat_id: int) -> None:
        key = ChatCacheService._get_chat_info_key(chat_id)
        cache.delete(key)

    @staticmethod
    def set_user_info(user_id: int, info: Dict) -> None:
        key = ChatCacheService._get_user_info_key(user_id)
        cache.set(key, info, ChatCacheService.TTL_USER_INFO)

    @staticmethod
    def get_user_info(user_id: int) -> Optional[Dict]:
        key = ChatCacheService._get_user_info_key(user_id)
        return cache.get(key)

    @staticmethod
    def invalidate_user_info(user_id: int) -> None:
        key = ChatCacheService._get_user_info_key(user_id)
        cache.delete(key)

    @staticmethod
    def increment_unread(user_id: int, chat_id: int, count: int = 1) -> int:
        chat_key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        unread_count = cache.get(chat_key, 0) + count
        cache.set(chat_key, unread_count, ChatCacheService.TTL_LAST_MESSAGES)

        total_key = ChatCacheService._get_user_unread_total_key(user_id)
        total_unread = cache.get(total_key, 0) + count
        cache.set(total_key, total_unread, ChatCacheService.TTL_LAST_MESSAGES)

        chats_key = ChatCacheService._get_user_unread_chats_key(user_id)
        unread_chats = cache.get(chats_key, set())
        unread_chats.add(chat_id)
        cache.set(chats_key, unread_chats, ChatCacheService.TTL_LAST_MESSAGES)

        return unread_count

    @staticmethod
    def decrement_unread(user_id: int, chat_id: int, count: int = 1) -> int:
        chat_key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        unread_count = max(0, cache.get(chat_key, 0) - count)
        cache.set(chat_key, unread_count, ChatCacheService.TTL_LAST_MESSAGES)

        total_key = ChatCacheService._get_user_unread_total_key(user_id)
        total_unread = max(0, cache.get(total_key, 0) - count)
        cache.set(total_key, total_unread, ChatCacheService.TTL_LAST_MESSAGES)

        if unread_count == 0:
            chats_key = ChatCacheService._get_user_unread_chats_key(user_id)
            unread_chats = cache.get(chats_key, set())
            unread_chats.discard(chat_id)
            cache.set(chats_key, unread_chats, ChatCacheService.TTL_LAST_MESSAGES)

        return unread_count

    @staticmethod
    def get_unread_count(user_id: int, chat_id: Optional[int] = None) -> int:
        if chat_id:
            key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        else:
            key = ChatCacheService._get_user_unread_total_key(user_id)

        return cache.get(key, 0)

    @staticmethod
    def get_unread_chats(user_id: int) -> List[int]:
        key = ChatCacheService._get_user_unread_chats_key(user_id)
        return list(cache.get(key, set()))

    @staticmethod
    def mark_chat_read(user_id: int, chat_id: int) -> None:
        chat_key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        unread_count = cache.get(chat_key, 0)

        if unread_count > 0:
            total_key = ChatCacheService._get_user_unread_total_key(user_id)
            total_unread = max(0, cache.get(total_key, 0) - unread_count)
            cache.set(total_key, total_unread, ChatCacheService.TTL_LAST_MESSAGES)

            cache.set(chat_key, 0, ChatCacheService.TTL_LAST_MESSAGES)

            chats_key = ChatCacheService._get_user_unread_chats_key(user_id)
            unread_chats = cache.get(chats_key, set())
            unread_chats.discard(chat_id)
            cache.set(chats_key, unread_chats, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def set_typing(chat_id: int, user_id: int) -> None:
        key = ChatCacheService._get_typing_key(chat_id, user_id)
        cache.set(key, timezone.now().isoformat(), ChatCacheService.TTL_TYPING)

    @staticmethod
    def remove_typing(chat_id: int, user_id: int) -> None:
        key = ChatCacheService._get_typing_key(chat_id, user_id)
        cache.delete(key)

    @staticmethod
    def get_typing_users(chat_id: int, user_ids: List[int]) -> List[int]:
        typing_users = []
        for user_id in user_ids:
            key = ChatCacheService._get_typing_key(chat_id, user_id)
            if cache.get(key):
                typing_users.append(user_id)
        return typing_users

    @staticmethod
    def clear_chat_cache(chat_id: int) -> None:
        keys = [
            ChatCacheService._get_chat_last_messages_key(chat_id),
            ChatCacheService._get_chat_last_message_key(chat_id),
            ChatCacheService._get_chat_info_key(chat_id),
        ]
        cache.delete_many(keys)

    @staticmethod
    def clear_user_cache(user_id: int) -> None:
        keys = [
            ChatCacheService._get_user_info_key(user_id),
            ChatCacheService._get_user_unread_total_key(user_id),
            ChatCacheService._get_user_unread_chats_key(user_id),
        ]
        cache.delete_many(keys)
