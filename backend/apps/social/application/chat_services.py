import json
import hashlib
import re
import uuid
from datetime import timedelta, datetime
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from pathlib import Path

from django.utils import timezone
def _post_commit(func, *args, **kwargs):
    transaction.on_commit(lambda: func(*args, **kwargs))

from django.db import transaction, connection, IntegrityError, models
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncDate, ExtractHour
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

import redis

from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from ..models import GroupChat, PrivateChat, Message, ChatMember
    from ..models import ChatRestriction, ChatBan, AntiSpamRule, ChatBackup
    from django.contrib.auth.models import User

User = get_user_model()



@dataclass
class PermissionResult:
    allowed: bool
    reason: str = ""
    missing_permissions: List[str] = field(default_factory=list)


def rate_limit(max_calls=10, period=60):
    from django.core.cache import cache
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"ratelimit:{func.__name__}:{args[0].user.id if args and hasattr(args[0],'user') else 'anon'}"
            count = cache.get(key, 0)
            if count >= max_calls:
                raise Exception('Rate limit exceeded')
            cache.set(key, count + 1, period)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def effective_member_permissions(member):
    if member.is_owner or member.user.is_staff and member.chat.discussion_type in ('anime', 'franchise'):
        return {p: True for p in PermissionChecker.ALL_PERMISSIONS}
    defaults = PermissionChecker.DEFAULT_ROLE_PERMISSIONS['admin' if member.is_admin else 'member']
    permissions = {p: p in defaults for p in PermissionChecker.ALL_PERMISSIONS}
    if member.role:
        permissions.update({f.name: getattr(member.role, f.name) for f in member.role._meta.fields if f.name.startswith('can_')})
    for f in member._meta.fields:
        if f.name.startswith('can_'):
            permissions[f.name] = permissions.get(f.name, False) or getattr(member, f.name)
    permissions['can_post_messages'] = permissions.get('can_post_messages', True) and member.can_send_messages
    for permission in ('can_invite_users', 'can_pin_messages'):
        permissions[permission] = permissions.get(permission, False) and (member.is_admin or
            bool(member.role and member.role.level >= 2) or getattr(member.chat, permission, False))
    return permissions


class PermissionChecker:
    ALL_PERMISSIONS = {
        'can_delete_messages',
        'can_ban_users',
        'can_restrict_members',
        'can_pin_messages',
        
        'can_manage_chat',
        'can_change_chat_info',
        'can_invite_users',
        'can_add_new_admins',
        'can_promote_members',
        
        'can_post_messages',
        'can_edit_messages',
        'can_manage_video_chats',
        
        'can_remain_anonymous',
        'can_delete_chat',
    }
    
    DEFAULT_ROLE_PERMISSIONS = {
        'owner': ALL_PERMISSIONS,  
        'admin': {
            'can_manage_chat', 'can_change_chat_info', 'can_delete_messages',
            'can_ban_users', 'can_restrict_members', 'can_invite_users', 'can_pin_messages',
            'can_promote_members', 'can_manage_video_chats', 'can_post_messages',
            'can_edit_messages',
        },
        'moderator': {
            'can_delete_messages', 'can_restrict_members', 'can_pin_messages',
            'can_invite_users', 'can_post_messages',
        },
        'member': {
            'can_post_messages',
        },
    }
    
    def __init__(self, user, chat):
        self.user = user
        self.chat = chat
        self._membership = None
        self._restrictions = None
        self._ban = None
    
    @property
    def membership(self):
        if self._membership is None and hasattr(self.chat, 'members'):
            from ..models import ChatMember
            try:
                self._membership = self.chat.members.get(user=self.user)
            except ChatMember.DoesNotExist:
                self._membership = False
        return self._membership if self._membership else None
    
    @property
    def restrictions(self):
        if self._restrictions is None and hasattr(self.chat, 'restrictions'):
            from ..models import ChatRestriction
            self._restrictions = ChatRestriction.objects.filter(
                chat=self.chat,
                user=self.user
            ).filter(
                Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
            )
        return self._restrictions or []
    
    @property
    def is_banned(self) -> bool:
        if self._ban is None and hasattr(self.chat, 'bans'):
            from ..models import ChatBan
            self._ban = ChatBan.objects.filter(
                chat=self.chat,
                user=self.user
            ).filter(
                Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
            ).exists()
        return self._ban or False
    
    def has_permission(self, permission_name: str) -> PermissionResult:
        if not self.user or not self.user.is_authenticated or not self.user.is_active:
            return PermissionResult(False, 'Требуется активный аккаунт')
        if permission_name not in self.ALL_PERMISSIONS:
            return PermissionResult(
                allowed=False,
                reason=f"Неизвестное право: {permission_name}"
            )
        
        if not hasattr(self.chat, 'members'):
            return self._check_private_chat_permission(permission_name)
        
        if self.is_banned or self.membership and self.membership.is_banned:
            return PermissionResult(
                allowed=False,
                reason="Пользователь заблокирован в этом чате"
            )
        
        if not self.membership:
            return PermissionResult(
                allowed=False,
                reason="Пользователь не является участником чата"
            )
        
        if self._is_owner():
            return PermissionResult(allowed=True)
        
        effective_permissions = self._get_effective_permissions()
        
        restricted_perms = self._get_restricted_permissions()
        
        if permission_name in restricted_perms:
            return PermissionResult(
                allowed=False,
                reason=f"Право '{permission_name}' ограничено",
                missing_permissions=[permission_name]
            )
        
        has_perm = effective_permissions.get(permission_name, False)
        if permission_name == 'can_post_messages':
            member = self.membership
            has_perm = has_perm and member.can_send_messages and not (member.is_muted and (not member.muted_until or member.muted_until > timezone.now()))
        
        return PermissionResult(
            allowed=has_perm,
            reason="" if has_perm else f"Нет права '{permission_name}'",
            missing_permissions=[] if has_perm else [permission_name]
        )
    
    def has_any_permission(self, permission_names: List[str]) -> PermissionResult:
        for perm in permission_names:
            result = self.has_permission(perm)
            if result.allowed:
                return result
        
        return PermissionResult(
            allowed=False,
            reason=f"Нет ни одного из прав: {', '.join(permission_names)}",
            missing_permissions=permission_names
        )
    
    def has_all_permissions(self, permission_names: List[str]) -> PermissionResult:
        missing = []
        for perm in permission_names:
            result = self.has_permission(perm)
            if not result.allowed:
                missing.append(perm)
        
        if missing:
            return PermissionResult(
                allowed=False,
                reason=f"Отсутствуют права: {', '.join(missing)}",
                missing_permissions=missing
            )
        
        return PermissionResult(allowed=True)
    
    def can_perform_action(self, action: str, target_user=None) -> PermissionResult:
        action_permissions = {
            'ban': 'can_ban_users', 'restrict': 'can_restrict_members',
            'promote': 'can_promote_members', 'demote': 'can_promote_members',
            'remove': 'can_manage_chat', 'edit_info': 'can_change_chat_info',
            'pin': 'can_pin_messages', 'delete_message': 'can_delete_messages',
            'invite': 'can_invite_users',
        }
        result = self.has_permission(action_permissions.get(action, ''))
        if not result.allowed or target_user is None:
            return result
        if action in ('ban', 'restrict', 'promote', 'demote', 'remove'):
            discussion = self.chat.discussion_type in ('anime', 'franchise')
            if target_user.pk == self.user.pk or (target_user.is_staff if discussion else target_user.pk == self.chat.created_by_id):
                return PermissionResult(False, 'Нельзя изменить владельца или собственные права этим действием')
            target = self.chat.members.select_related('role', 'chat').filter(user=target_user).first()
            if target and not self._is_owner() and self._get_role_level_for_member(target) >= self._get_role_level():
                return PermissionResult(False, 'Нельзя управлять участником с равной или более высокой ролью')
        return PermissionResult(True)

    def _is_owner(self) -> bool:
        return bool(self.membership and (self.membership.is_owner or
            self.user.is_staff and self.chat.discussion_type in ('anime', 'franchise')))

    def _get_role_level(self) -> int:
        return self._get_role_level_for_member(self.membership) if self.membership else 0

    def _get_role_level_for_member(self, membership) -> int:
        if membership.is_owner or membership.user.is_staff and self.chat.discussion_type in ('anime', 'franchise'):
            return 3
        return max(2 if membership.is_admin else 0, min(membership.role.level, 2) if membership.role else 0)

    def _get_effective_permissions(self) -> Dict[str, bool]:
        return effective_member_permissions(self.membership) if self.membership else {}

    def _get_restricted_permissions(self) -> Set[str]:
        restricted = set()
        
        for restriction in self.restrictions:
            restriction_type = restriction.restriction_type
            
            if restriction_type == 'read_only':
                restricted.add('can_post_messages')
            elif restriction_type == 'no_media':
                restricted.update(['can_send_media'])
            elif restriction_type == 'no_stickers':
                restricted.update(['can_send_stickers'])
            elif restriction_type == 'no_links':
                restricted.update(['can_send_links'])
            elif restriction_type == 'no_voice':
                restricted.update(['can_send_voice'])
        
        return restricted
    
    def _check_private_chat_permission(self, permission_name: str) -> PermissionResult:
        from ..models import PrivateChat
        
        if not isinstance(self.chat, PrivateChat):
            return PermissionResult(allowed=False, reason="Не личный чат")
        
        if self.user not in [self.chat.user1, self.chat.user2]:
            return PermissionResult(allowed=False, reason="Не участник чата")
        
        if self.user == self.chat.user1 and self.chat.user2_blocked:
            return PermissionResult(allowed=False, reason="Вы заблокированы")
        if self.user == self.chat.user2 and self.chat.user1_blocked:
            return PermissionResult(allowed=False, reason="Вы заблокированы")
        
        basic_permissions = {
            'can_post_messages', 'can_send_media', 'can_send_stickers',
            'can_send_links', 'can_send_voice'
        }
        
        if permission_name in basic_permissions:
            return PermissionResult(allowed=True)
        
        return PermissionResult(allowed=False, reason="Недоступно в личном чате")



class SettingsCache:
    CACHE_PREFIX = 'chat_settings'
    CACHE_TIMEOUT = 3600  
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    
    def get_cache_key(self, user_id: int, chat_type: str, chat_id: int) -> str:
        return f"{self.CACHE_PREFIX}:{user_id}:{chat_type}:{chat_id}"
    
    def get_chat_settings(self, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        cache_key = self.get_cache_key(user_id, chat_type, chat_id)
        
        cached = self.redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass
        
        settings_data = self._load_settings_from_db(user_id, chat_type, chat_id)
        
        if settings_data:
            self.redis_client.setex(
                cache_key,
                self.CACHE_TIMEOUT,
                json.dumps(settings_data, default=str)
            )
        
        return settings_data
    
    def invalidate(self, user_id: int, chat_type: str, chat_id: int):
        cache_key = self.get_cache_key(user_id, chat_type, chat_id)
        self.redis_client.delete(cache_key)
    
    def invalidate_all_for_chat(self, chat_type: str, chat_id: int):
        pattern = f"{self.CACHE_PREFIX}:*:{chat_type}:{chat_id}"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    def invalidate_all_for_user(self, user_id: int):
        pattern = f"{self.CACHE_PREFIX}:{user_id}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    def _load_settings_from_db(self, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        try:
            user = User.objects.get(id=user_id)
            
            if chat_type == 'private':
                from ..models import PrivateChat
                from ..models import PrivateChatSettings
                
                chat = PrivateChat.objects.get(id=chat_id)
                if user not in [chat.user1, chat.user2]:
                    return None
                
                settings_obj, _ = PrivateChatSettings.objects.get_or_create(
                    chat=chat, user=user
                )
                
                return {
                    'custom_name': settings_obj.custom_name,
                    'notifications_enabled': settings_obj.notifications_enabled,
                    'sound_enabled': settings_obj.sound_enabled,
                    'muted_until': settings_obj.muted_until.isoformat() if settings_obj.muted_until else None,
                    'is_archived': settings_obj.is_archived,
                    'is_pinned': settings_obj.is_pinned,
                    'is_blocked': settings_obj.is_blocked,
                    'auto_delete_after': settings_obj.auto_delete_after,
                }
            
            elif chat_type == 'group':
                from ..models import GroupChat
                from ..models import ChatSettings
                
                chat = GroupChat.objects.get(id=chat_id)
                if not chat.members.filter(user=user).exists():
                    return None
                
                settings_obj, _ = ChatSettings.objects.get_or_create(
                    user=user, chat=chat
                )
                
                return {
                    'notifications_enabled': settings_obj.notifications_enabled,
                    'sound_enabled': settings_obj.sound_enabled,
                    'is_blocked': settings_obj.is_blocked,
                }
            
        except Exception as e:
            logger.info(f"Error loading settings from DB: {e}")
            return None
        
        return None



class AntiSpamService:
    def __init__(self, chat):
        self.chat = chat
        self._rules = None
    
    @property
    def rules(self):
        if self._rules is None and hasattr(self.chat, 'anti_spam_rules'):
            from ..models import AntiSpamRule
            self._rules = list(self.chat.anti_spam_rules.filter(enabled=True))
        return self._rules or []
    
    def check_message(self, message) -> Dict[str, Any]:
        result = {
            'is_spam': False,
            'violated_rules': [],
            'action': None,
            'action_duration': None
        }
        
        if not self.rules:
            return result
        
        for rule in self.rules:
            violation = self._check_rule(rule, message)
            if violation:
                result['is_spam'] = True
                result['violated_rules'].append(rule.rule_type)
                
                if not result['action'] or self._action_severity(rule.action) > self._action_severity(result['action']):
                    result['action'] = rule.action
                    result['action_duration'] = rule.action_duration
        
        return result
    
    def _check_rule(self, rule, message) -> bool:
        rule_type = rule.rule_type
        
        if rule_type == 'flood':
            return self._check_flood(rule, message)
        elif rule_type == 'links':
            return self._check_links(rule, message)
        elif rule_type == 'spam_keywords':
            return self._check_keywords(rule, message)
        elif rule_type == 'caps_lock':
            return self._check_caps_lock(rule, message)
        elif rule_type == 'new_members':
            return self._check_new_member(rule, message)
        elif rule_type == 'media_flood':
            return self._check_media_flood(rule, message)
        
        return False
    
    def _check_flood(self, rule, message) -> bool:
        from ..models import Message
        
        time_window = timezone.now() - timedelta(seconds=rule.time_window)
        recent_count = Message.objects.filter(
            chat=self.chat,
            sender=message.sender,
            created_at__gte=time_window
        ).count()
        
        return recent_count > rule.threshold
    
    def _check_links(self, rule, message) -> bool:
        if not message.text:
            return False
        
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message.text)
        
        return len(urls) > 0
    
    def _check_keywords(self, rule, message) -> bool:
        if not message.text:
            return False
        
        keywords = rule.keywords or []
        text_lower = message.text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _check_caps_lock(self, rule, message) -> bool:
        if not message.text:
            return False
        
        text = message.text
        if len(text) < 5:
            return False
        
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return False
        
        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        return caps_ratio > 0.7
    
    def _check_new_member(self, rule, message) -> bool:
        from ..models import ChatMember
        
        try:
            member = ChatMember.objects.get(chat=self.chat, user=message.sender)
            join_time = member.joined_at
            hours_since_join = (timezone.now() - join_time).total_seconds() / 3600
            return hours_since_join < 24  
        except ChatMember.DoesNotExist:
            return True
    
    def _check_media_flood(self, rule, message) -> bool:
        from ..models import Message
        
        if not message.media:
            return False
        
        time_window = timezone.now() - timedelta(seconds=rule.time_window)
        recent_media_count = Message.objects.filter(
            chat=self.chat,
            sender=message.sender,
            media__isnull=False,
            created_at__gte=time_window
        ).count()
        
        return recent_media_count > rule.threshold
    
    def _action_severity(self, action: str) -> int:
        severity = {
            'warn': 1,
            'delete': 2,
            'mute': 3,
            'ban': 4,
        }
        return severity.get(action, 0)
    
    def apply_action(self, message, action: str, duration: int = None):
        from ..models import ChatRestriction, ChatBan
        
        if action == 'delete':
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.save(update_fields=['is_deleted', 'deleted_at'])
        
        elif action == 'mute':
            until = timezone.now() + timedelta(minutes=duration or 60)
            ChatRestriction.objects.create(
                chat=self.chat,
                user=message.sender,
                restriction_type='read_only',
                reason='Автоматическое ограничение за спам',
                until_date=until,
                restricted_by=None  
            )
        
        elif action == 'ban':
            until = timezone.now() + timedelta(hours=duration or 24) if duration else None
            ChatBan.objects.create(
                chat=self.chat,
                user=message.sender,
                reason='Автоматическая блокировка за спам',
                until_date=until,
                banned_by=None
            )









class ChatAnalytics:
    def __init__(self, chat, user=None):
        self.chat = chat
        self.user = user

    def messages(self, days):
        from .conversations import visible_messages
        from ..models import Message
        qs = visible_messages(self.chat, self.user) if self.user else Message.objects.filter(chat=self.chat, is_deleted=False)
        return qs.filter(created_at__gte=timezone.now()-timedelta(days=days))
    
    def get_activity_stats(self, days: int = 7) -> Dict:
        from ..models import Message
        
        start_date = timezone.now() - timedelta(days=days)
        
        messages = self.messages(days)
        
        messages_count = messages.count()
        
        active_users = messages.values('sender').distinct().count()
        
        avg_per_day = messages_count / days if days > 0 else 0
        
        by_day = list(messages.annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day'))

        by_hour = list(messages.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour'))
        
        peak_hour = max(by_hour, key=lambda x: x['count'])['hour'] if by_hour else 0
        
        return {
            'messages_count': messages_count,
            'active_users': active_users,
            'avg_messages_per_day': round(avg_per_day, 2),
            'peak_hour': peak_hour,
            'by_day': by_day,
            'by_hour': by_hour,
            'total': messages_count,
            'messages_per_day': [{'date': item['day'], 'count': item['count']} for item in by_day],
        }
    
    def get_member_stats(self) -> Dict:
        from ..models import ChatMember, ChatAdminLog
        
        total = self.chat.members.count()
        
        online = 0
        try:
            from core.online_status import online_status
            member_ids = list(self.chat.members.values_list('user_id', flat=True))
            online = len(online_status.get_users_data(member_ids))
        except Exception:
            online = 0
        
        admins = self.chat.members.filter(
            Q(is_admin=True) | Q(role__level__gte=2) | Q(user_id=self.chat.created_by_id)
        ).count()
        
        today = timezone.now().replace(hour=0, minute=0, second=0)
        new_today = ChatAdminLog.objects.filter(
            chat=self.chat,
            action='member_joined',
            created_at__gte=today
        ).count()
        
        left_today = ChatAdminLog.objects.filter(
            chat=self.chat,
            action='member_left',
            created_at__gte=today
        ).count()
        
        by_role = list(self.chat.members.values(
            'role__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count'))
        
        return {
            'total': total,
            'online': online,
            'admins': admins,
            'new_today': new_today,
            'left_today': left_today,
            'by_role': by_role,
        }
    
    def get_content_stats(self, days: int = 7) -> Dict:
        from ..models import Message
        from ..models import MessageReaction
        
        start_date = timezone.now() - timedelta(days=days)
        
        messages = self.messages(days)
        media = messages.filter(Q(media__gt='') | Q(attachments__isnull=False) | Q(content_attachments__isnull=False) |
            Q(shared_post__isnull=False) | Q(shared_anime__isnull=False) | Q(shared_playlist__isnull=False) | Q(shared_shorts__isnull=False)).distinct()
        media_messages = media.count()
        total = messages.count()
        text_messages = total-media_messages
        
        reactions_count = MessageReaction.objects.filter(
            message_id__in=messages.values('pk'),
            created_at__gte=start_date
        ).count()
        
        pinned_messages = messages.filter(is_pinned=True).count()
        
        by_media_type = []
        for kind in ('image', 'video', 'audio', 'file', 'anime', 'playlist', 'post', 'shorts'):
            condition = Q(media_type=kind, media__gt='') | Q(attachments__type=kind) | Q(content_attachments__content_type=kind)
            if kind in ('anime', 'playlist', 'post', 'shorts'):
                condition |= Q(**{f'shared_{kind}__isnull': False})
            count = messages.filter(condition).distinct().count()
            if count:
                by_media_type.append({'media_type': kind, 'count': count})
        
        return {
            'media_messages': media_messages,
            'text_messages': text_messages,
            'reactions_count': reactions_count,
            'pinned_messages': pinned_messages,
            'by_media_type': by_media_type,
            'total': total, 'with_media': media_messages, 'text_only': text_messages,
        }
    
    def get_engagement_score(self, *, activity=None, members=None, content=None) -> float:
        activity = activity or self.get_activity_stats(days=7)
        members = members or self.get_member_stats()
        
        if members['total'] == 0:
            return 0
        
        active_ratio = activity['active_users'] / members['total'] if members['total'] > 0 else 0
        messages_per_active = activity['messages_count'] / activity['active_users'] if activity['active_users'] > 0 else 0
        content = content or self.get_content_stats(days=7)
        reaction_ratio = content['reactions_count'] / activity['messages_count'] if activity['messages_count'] > 0 else 0
        
        score = (active_ratio * 0.4 + 
                min(messages_per_active / 10, 1) * 0.4 + 
                min(reaction_ratio, 1) * 0.2) * 100
        
        return round(score, 2)



class ChatBackupService:
    def create_backup(self, chat, user):
        from apps.social.infrastructure.models.social_chat import ChatBackup
        from .chat_backups import require_backup_access, build_backup
        require_backup_access(chat, user)
        backup = build_backup(ChatBackup.objects.create(chat=chat, created_by=user).pk)
        return {'success': True, 'backup_id': backup.pk, 'messages_count': backup.messages_count,
                'members_count': backup.members_count, 'file_size': backup.file_size}

    def restore_backup(self, backup_id, user):
        from .chat_backups import restore_backup
        return restore_backup(backup_id, user)


class NotificationService:
    def __init__(self):
        try:
            from channels.layers import get_channel_layer
            self.channel_layer = get_channel_layer()
        except ImportError:
            self.channel_layer = None
    
    async def send_to_chat(self, chat, event_type: str, data: Dict, exclude_users: List[int] = None):
        if not self.channel_layer:
            return
        
        chat_id = chat.id if hasattr(chat, 'id') else chat
        
        await self.channel_layer.group_send(
            f'chat_{chat_id}',
            {
                'type': 'chat_message',
                'event_type': event_type,
                'data': data,
                'exclude_users': exclude_users or [],
            }
        )
    
    async def send_to_user(self, user_id: int, event_type: str, data: Dict):
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'user_{user_id}',
            {
                'type': 'notification_event',
                'event_type': event_type,
                'data': data,
            }
        )
    
    async def broadcast_to_chat_members(self, chat, event_type: str, data: Dict):
        if not self.channel_layer or not hasattr(chat, 'members'):
            return
        
        member_ids = list(chat.members.values_list('user_id', flat=True))
        for user_id in member_ids:
            await self.send_to_user(user_id, event_type, data)



def can_delete_message(user, message) -> bool:
    from ..models import GroupChat

    if message.sender_id == user.id:
        return True
    if message.private_chat_id:
        return False
    if not message.chat_id:
        return False
    chat = GroupChat.objects.filter(id=message.chat_id).first()
    if chat is None:
        return False
    return PermissionChecker(user, chat).has_permission('can_delete_messages').allowed









settings_cache = SettingsCache()
