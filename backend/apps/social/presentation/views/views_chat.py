from apps.social.application.conversations import resolve_chat, require_permission, validate_role_grant, member_ids
import logging

logger = logging.getLogger(__name__)

from core.redis_events import event_publisher
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from apps.social.application.settings_transfer import SettingsImportParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Exists, OuterRef
from django.db import transaction
from django.core.cache import cache

from apps.social.infrastructure.models.social import (
    GroupChat, PrivateChat, ChatMember, ChatRole, Message,
    ChatAdminLog, MessageReadStatus, ChatFolder, ChatFolderChat
)
from apps.social.infrastructure.models.social_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage,
    SecurityLog, GroupChatSettings, PrivateChatSettings, MessagePin,
    GroupMemberSettings, ChatTopic, UserGlobalChatStyle,
)
from apps.social.application.chat_settings_service import (
    ChatSettingsService, PermissionChecker, SettingsCache,
    NotificationService, RateLimiter, AntiSpamService,
    SettingsExport, SettingsVersioning, PermissionResult,
)
from apps.users.infrastructure.models.users import User



class TransactionalChatViewSet(viewsets.ModelViewSet):
    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code >= 400:
            transaction.set_rollback(True)
        return response


def managed_chat_ids(request, permission):
    if permission not in PermissionChecker.ALL_PERMISSIONS:
        return ChatMember.objects.none().values_list("chat_id", flat=True)

    active_bans = ChatBan.objects.filter(
        chat_id=OuterRef("chat_id"),
        user=request.user,
    ).filter(Q(until_date__isnull=True) | Q(until_date__gt=timezone.now()))
    permission_filter = (
        (Q(chat__created_by=request.user) & ~Q(chat__discussion_type__in=("anime", "franchise")))
        | Q(role__isnull=True, is_admin=True)
        | Q(**{f"role__{permission}": True})
    )
    if request.user.is_staff:
        permission_filter |= Q(chat__discussion_type__in=("anime", "franchise"))

    return (
        ChatMember.objects.filter(user=request.user, is_banned=False)
        .annotate(_has_active_ban=Exists(active_bans))
        .filter(_has_active_ban=False)
        .filter(permission_filter)
        .values_list("chat_id", flat=True)
    )


class ChatCustomizationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _check_chat_access(self, request, chat_type: str, chat_id: int):
        return resolve_chat(chat_id, request.user, chat_type)


    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper')
    def get_wallpaper(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        data = ChatSettingsService.get_wallpaper_for_chat(request.user, chat_type, chat.id)
        if not data:
            return Response({'wallpaper': None})
        return Response({'wallpaper': data})

    @action(detail=False, methods=['put', 'post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper/set')
    def set_wallpaper(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        from apps.social.presentation.serializers.social_chat_serializers import ChatWallpaperSerializer
        serializer = ChatWallpaperSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'wallpaper_image' in request.FILES:
            file = request.FILES['wallpaper_image']
            if file.size > 5 * 1024 * 1024:
                return Response({'error': 'Файл слишком большой (максимум 5MB)'}, status=400)

            from apps.social.infrastructure.models.social_chat import ChatWallpaper as WP
            defaults = {
                'wallpaper_type': 'image',
                'wallpaper_image': file,
                'wallpaper_blur': serializer.validated_data.get('wallpaper_blur', 0),
                'wallpaper_intensity': serializer.validated_data.get('wallpaper_intensity', 100),
                'wallpaper_color': '#000000',
            }
            if chat_type == 'group':
                wp, _ = WP.objects.update_or_create(user=request.user, chat_id=chat.id, defaults=defaults)
            else:
                wp, _ = WP.objects.update_or_create(user=request.user, private_chat_id=chat.id, defaults=defaults)

            SettingsCache.invalidate(request.user.id, chat_type, chat.id)
            return Response({
                'wallpaper': ChatSettingsService._wallpaper_to_dict(wp),
                'message': 'Обои установлены'
            })

        data = ChatSettingsService.set_wallpaper_for_chat(request.user, chat_type, chat.id, serializer.validated_data)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'wallpaper': data, 'message': 'Обои установлены'})

    @action(detail=False, methods=['delete'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper/reset')
    def reset_wallpaper(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        ChatSettingsService.reset_wallpaper(request.user, chat_type, chat.id)
        return Response({'message': 'Обои сброшены'})

    @action(detail=False, methods=['post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper/preset')
    def apply_wallpaper_preset(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        preset_id = request.data.get('preset_id')
        if not preset_id:
            return Response({'error': 'preset_id required'}, status=400)
        data = ChatSettingsService.apply_preset_wallpaper(request.user, chat_type, chat.id, preset_id)
        if not data:
            return Response({'error': 'Пресет не найден'}, status=404)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'wallpaper': data, 'message': 'Обои применены'})

    @action(detail=False, methods=['get'], url_path='wallpapers/presets')
    def wallpaper_presets(self, request):
        presets = ChatSettingsService.PRESET_WALLPAPERS
        categories = {}
        for p in presets:
            cat = p.get('preset_category') or p.get('category', 'other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(p)
        return Response({'presets': presets, 'categories': categories})


    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme')
    def get_theme(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        data = ChatSettingsService.get_theme_for_chat(request.user, chat_type, chat.id)
        return Response({'theme': data or ChatSettingsService._default_theme()})

    @action(detail=False, methods=['put', 'post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme/set')
    def set_theme(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        from apps.social.presentation.serializers.social_chat_serializers import ChatThemeSerializer
        serializer = ChatThemeSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = ChatSettingsService.set_theme_for_chat(request.user, chat_type, chat.id, serializer.validated_data)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'theme': data, 'message': 'Тема применена'})

    @action(detail=False, methods=['post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme/preset')
    def apply_theme_preset(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        preset_id = request.data.get('preset_id')
        if not preset_id:
            return Response({'error': 'preset_id required'}, status=400)
        data = ChatSettingsService.apply_preset_theme(request.user, chat_type, chat.id, preset_id)
        if not data:
            return Response({'error': 'Тема не найдена'}, status=404)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'theme': data, 'message': 'Тема применена'})

    @action(detail=False, methods=['get'], url_path='themes/presets')
    def theme_presets(self, request):
        return Response({'presets': ChatSettingsService.PRESET_THEMES})

    @action(detail=False, methods=['delete'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme/reset')
    def reset_theme(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        from apps.social.infrastructure.models.social_chat import ChatTheme as CT
        if chat_type == 'group':
            CT.objects.filter(user=request.user, chat_id=chat.id).delete()
        else:
            CT.objects.filter(user=request.user, private_chat_id=chat.id).delete()
        SettingsCache.invalidate(request.user.id, chat_type, chat.id)
        return Response({'message': 'Тема сброшена', 'theme': ChatSettingsService._default_theme()})


    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/all')
    def get_all_settings(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        data = ChatSettingsService.get_all_settings_for_chat(request.user, chat_type, chat.id)
        return Response(data)

    @action(detail=False, methods=['post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/bulk-update')
    def bulk_update_settings(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)

        result = {}

        if 'wallpaper' in request.data:
            wp_data = request.data['wallpaper']
            if wp_data:
                result['wallpaper'] = ChatSettingsService.set_wallpaper_for_chat(
                    request.user, chat_type, chat.id, wp_data
                )

        if 'theme' in request.data:
            theme_data = request.data['theme']
            if theme_data:
                result['theme'] = ChatSettingsService.set_theme_for_chat(
                    request.user, chat_type, chat.id, theme_data
                )

        SettingsVersioning.increment_version(request.user.id)
        SettingsCache.invalidate(request.user.id, chat_type, chat.id)
        result['css_vars'] = ChatSettingsService._build_css_vars(
            result.get('wallpaper'),
            result.get('theme')
        )
        return Response({'settings': result, 'message': 'Настройки сохранены'})


    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/css-vars')
    def get_css_vars(self, request, chat_type=None, chat_id=None):
        chat = self._check_chat_access(request, chat_type, chat_id)
        wallpaper = ChatSettingsService.get_wallpaper_for_chat(request.user, chat_type, chat.id)
        theme = ChatSettingsService.get_theme_for_chat(request.user, chat_type, chat.id)
        css_vars = ChatSettingsService._build_css_vars(wallpaper, theme)

        css_string = ':root {\n' + '\n'.join(f'  {k}: {v};' for k, v in css_vars.items()) + '\n}'
        return Response({'css_vars': css_vars, 'css_string': css_string})



def private_settings(chat, user):
    chat = PrivateChat.objects.select_for_update().get(pk=chat.pk)
    prefix = 'user1' if chat.user1_id == user.pk else 'user2'
    defaults = {field: getattr(chat, f'{prefix}_{legacy}') for field, legacy in
                [('notifications_enabled', 'notifications'), ('muted_until', 'muted_until'),
                 ('is_archived', 'archived'), ('is_pinned', 'pinned'), ('is_blocked', 'blocked')]}
    old = chat.user_settings.filter(user=user).first()
    if old:
        defaults.update(custom_name=old.custom_name, custom_avatar=old.custom_avatar)
    return PrivateChatSettings.objects.get_or_create(chat=chat, user=user, defaults=defaults)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def private_chat_user_settings(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'private')

    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, created = private_settings(chat, request.user)

    if request.method == 'GET':
        return Response(_serialize_private_settings(settings_obj, request))

    from apps.social.presentation.serializers.social_serializers import PrivateChatSettingsSerializer

    data = request.data.copy()
    for legacy, canonical in [('notifications', 'notifications_enabled'), ('archived', 'is_archived'), ('pinned', 'is_pinned'), ('blocked', 'is_blocked')]:
        if legacy in data and canonical not in data:
            data[canonical] = data[legacy]
    serializer = PrivateChatSettingsSerializer(settings_obj, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    for field, value in validated.items():
        setattr(settings_obj, field, value)

    if 'is_blocked' in validated:
        settings_obj.blocked_at = timezone.now() if validated['is_blocked'] else None

    settings_obj.save()
    if 'is_hidden' in validated:
        from apps.social.application.conversations import get_conversation
        from apps.social.infrastructure.models.conversation import ConversationUserState
        state, _ = ConversationUserState.objects.get_or_create(conversation=get_conversation(chat), user=request.user)
        state.hidden = validated['is_hidden']
        state.save(update_fields=['hidden'])
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    SettingsVersioning.increment_version(request.user.id)

    return Response(_serialize_private_settings(settings_obj, request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def mute_private_chat(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'private')
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    duration = request.data.get('duration')  
    settings_obj, _ = private_settings(chat, request.user)

    if duration is None:
        settings_obj.muted_until = None  
        settings_obj.notifications_enabled = False
    else:
        settings_obj.muted_until = timezone.now() + timezone.timedelta(minutes=int(duration))

    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)

    return Response({'message': 'Чат заглушен', 'muted_until': settings_obj.muted_until})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def unmute_private_chat(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'private')
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = private_settings(chat, request.user)
    settings_obj.muted_until = None
    settings_obj.notifications_enabled = True
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({'message': 'Уведомления включены'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def block_user_in_private_chat(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'private')
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = private_settings(chat, request.user)
    if settings_obj.is_blocked:
        return Response({'message': 'Пользователь уже заблокирован'})
    settings_obj.is_blocked = True
    settings_obj.blocked_at = timezone.now()
    settings_obj.save()
    
    other_user = chat.user1 if chat.user2 == request.user else chat.user2
    
    msg = Message.objects.create(
        private_chat=chat,
        sender=request.user,
        text=f'{request.user.username} заблокировал(а) {other_user.username}',
        message_type="system",
        system_action="block",
        system_target_user=other_user,
    )
    
    from apps.social.presentation.views.views_chat import _send_system_message_to_chat
    _send_system_message_to_chat(chat, msg, request.user, other_user)
    
    from core.redis_events import event_publisher
    event_publisher.publish_event(
        "block",
        {
            "chat_id": chat.id,
            "user_id": request.user.id,
            "sender_id": request.user.id,
            "target_user_id": other_user.id,
        },
        target_users=[request.user.id, other_user.id]
    )
    
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({'message': 'Пользователь заблокирован'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def unblock_user_in_private_chat(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'private')
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = private_settings(chat, request.user)
    if not settings_obj.is_blocked:
        return Response({'message': 'Пользователь уже разблокирован'})
    settings_obj.is_blocked = False
    settings_obj.blocked_at = None
    settings_obj.save()
    
    other_user = chat.user1 if chat.user2 == request.user else chat.user2
    
    msg = Message.objects.create(
        private_chat=chat,
        sender=request.user,
        text=f'{request.user.username} разблокировал(а) {other_user.username}',
        message_type="system",
        system_action="unblock",
        system_target_user=other_user,
    )
    
    from apps.social.presentation.views.views_chat import _send_system_message_to_chat
    _send_system_message_to_chat(chat, msg, request.user, other_user)
    
    from core.redis_events import event_publisher
    event_publisher.publish_event(
        "unblock",
        {
            "chat_id": chat.id,
            "user_id": request.user.id,
            "sender_id": request.user.id,
            "target_user_id": other_user.id,
        },
        target_users=[request.user.id, other_user.id]
    )
    
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({'message': 'Пользователь разблокирован'})

def _send_system_message_to_chat(chat, msg, sender, target_user):
    from apps.social.application.conversations import record_event, serialize_message
    type(chat).objects.filter(pk=chat.pk).update(last_message_at=msg.created_at)
    record_event(chat, 'new_message', {'message': serialize_message(msg)})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def delete_private_chat(request, chat_id):
    from apps.social.application.conversations import clear_history
    chat = resolve_chat(chat_id, request.user, 'private')
    clear_history(chat, request.user, hide=True)
    return Response({'message': 'Чат удалён у обоих собеседников', 'chat_id': chat.public_id, 'action': 'deleted_for_both'})


def _serialize_private_settings(settings_obj, request) -> dict:
    return {
        'id': settings_obj.id,
        'chat_id': settings_obj.chat.public_id,
        'chat_type': 'private',
        'custom_name': settings_obj.custom_name,
        'custom_avatar_url': request.build_absolute_uri(settings_obj.custom_avatar.url) if settings_obj.custom_avatar else None,
        'notifications_enabled': settings_obj.notifications_enabled,
        'mentions_only': settings_obj.mentions_only,
        'sound_enabled': settings_obj.sound_enabled,
        'notification_sound': settings_obj.notification_sound,
        'vibration_enabled': settings_obj.vibration_enabled,
        'show_preview': settings_obj.show_preview,
        'show_popup': settings_obj.show_popup,
        'muted_until': settings_obj.muted_until,
        'is_muted': settings_obj.is_muted,
        'is_archived': settings_obj.is_archived,
        'is_pinned': settings_obj.is_pinned,
        'is_hidden': settings_obj.is_hidden,
        'is_blocked': settings_obj.is_blocked,
        'blocked_at': settings_obj.blocked_at,
        'auto_delete_enabled': settings_obj.auto_delete_enabled,
        'auto_delete_after': settings_obj.auto_delete_after,
        'folder_id': settings_obj.folder_id,
        'tags': settings_obj.tags,
        'updated_at': settings_obj.updated_at,
    }



@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def group_member_settings(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'group')
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)

    if request.method == 'GET':
        return Response({
            'notifications_enabled': settings_obj.notifications_enabled,
            'mentions_only': settings_obj.mentions_only,
            'sound_enabled': settings_obj.sound_enabled,
            'notification_sound': settings_obj.notification_sound,
            'vibration_enabled': settings_obj.vibration_enabled,
            'vibration_type': settings_obj.vibration_type,
            'show_preview': settings_obj.show_preview,
            'show_popup': settings_obj.show_popup,
            'muted_until': settings_obj.muted_until,
            'is_muted': settings_obj.is_muted,
            'is_pinned': settings_obj.is_pinned,
            'is_archived': settings_obj.is_archived,
            'tags': settings_obj.tags,
        })

    from apps.social.presentation.serializers.social_serializers import GroupMemberSettingsSerializer

    serializer = GroupMemberSettingsSerializer(settings_obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    for field, value in validated.items():
        setattr(settings_obj, field, value)
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'group', chat_id)

    return Response({'message': 'Настройки сохранены'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def mute_group_chat(request, chat_id):
    from apps.social.presentation.serializers.social_serializers import MuteGroupChatSerializer

    chat = resolve_chat(chat_id, request.user, 'group')
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    serializer = MuteGroupChatSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)
    duration = validated.get('duration')

    if duration is None:
        settings_obj.notifications_enabled = False
        settings_obj.muted_until = None
    else:
        settings_obj.muted_until = timezone.now() + timezone.timedelta(minutes=int(duration))
        settings_obj.notifications_enabled = False

    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'group', chat_id)
    return Response({
        'message': 'Группа заглушена',
        'notifications_enabled': False,
        'muted_until': settings_obj.muted_until,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def unmute_group_chat(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'group')
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)
    settings_obj.notifications_enabled = True
    settings_obj.muted_until = None
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'group', chat_id)
    return Response({
        'message': 'Уведомления включены',
        'notifications_enabled': True,
        'muted_until': None,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def archive_group_chat(request, chat_id):
    from apps.social.presentation.serializers.social_serializers import ArchiveChatSerializer

    chat = resolve_chat(chat_id, request.user, 'group')
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)
    serializer = ArchiveChatSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    is_archived = validated.get('is_archived', not settings_obj.is_archived)
    settings_obj.is_archived = is_archived
    settings_obj.save(update_fields=['is_archived'])
    SettingsCache.invalidate(request.user.id, 'group', chat_id)
    return Response({
        'message': 'Чат архивирован' if is_archived else 'Чат разархивирован',
        'is_archived': is_archived,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def archive_private_chat(request, chat_id):
    from apps.social.presentation.serializers.social_serializers import ArchiveChatSerializer

    chat = resolve_chat(chat_id, request.user, 'private')
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = private_settings(chat, request.user)
    serializer = ArchiveChatSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    is_archived = validated.get('is_archived', not settings_obj.is_archived)
    settings_obj.is_archived = is_archived
    settings_obj.save(update_fields=['is_archived'])
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({
        'message': 'Чат архивирован' if is_archived else 'Чат разархивирован',
        'is_archived': is_archived,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_group_notification_settings(request, chat_id):
    chat = resolve_chat(chat_id, request.user, 'group')
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)
    return Response({
        'notifications_enabled': settings_obj.notifications_enabled,
        'mentions_only': settings_obj.mentions_only,
        'sound_enabled': settings_obj.sound_enabled,
        'muted_until': settings_obj.muted_until,
        'is_muted': settings_obj.is_muted,
        'is_archived': settings_obj.is_archived,
        'is_pinned': settings_obj.is_pinned,
    })



class ChatInviteLinkViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.social.application.conversations import check_access
        from rest_framework.exceptions import APIException
        candidates = GroupChat.objects.filter(members__user=self.request.user).distinct()
        identifier = self.request.query_params.get('chat') or self.kwargs.get('chat_id')
        if identifier:
            candidates = candidates.filter(pk=resolve_chat(identifier, self.request.user, 'group').pk)
        allowed = []
        for chat in candidates:
            try:
                check_access(chat, self.request.user)
                if PermissionChecker(self.request.user, chat).has_permission('can_invite_users').allowed:
                    allowed.append(chat.pk)
            except APIException:
                continue
        return ChatInviteLink.objects.filter(chat_id__in=allowed).select_related('chat', 'creator')

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatInviteLinkSerializer, ChatInviteLinkCreateSerializer
        return ChatInviteLinkCreateSerializer if self.action in ['create', 'update', 'partial_update'] else ChatInviteLinkSerializer

    def require_manage(self, chat):
        from apps.social.application.conversations import check_access
        chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
        check_access(chat, self.request.user)
        require_permission(chat, self.request.user, 'can_invite_users')
        return chat

    def get_object(self):
        invite = super().get_object()
        self.require_manage(invite.chat)
        return ChatInviteLink.objects.select_for_update().get(pk=invite.pk)

    def perform_create(self, serializer):
        self.require_manage(serializer.validated_data['chat'])
        serializer.save(creator=self.request.user, expires_at=timezone.now() + timezone.timedelta(hours=24))

    def perform_update(self, serializer):
        if serializer.validated_data.get('chat', serializer.instance.chat).pk != serializer.instance.chat_id:
            raise ValidationError({'chat': 'Нельзя переносить приглашение в другой чат'})
        self.require_manage(serializer.instance.chat)
        serializer.save(expires_at=serializer.instance.effective_expires_at)

    def create(self, request, *args, **kwargs):
        from apps.social.presentation.serializers.social_chat_serializers import ChatInviteLinkSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(ChatInviteLinkSerializer(serializer.instance, context=self.get_serializer_context()).data, status=201)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        invite = self.get_object()
        invite.is_revoked = True
        invite.save(update_fields=['is_revoked'])
        ChatAdminLog.objects.create(chat=invite.chat, user=request.user,
            action='invite_link_revoked', details={'invite_link': invite.invite_link})
        return Response({'status': 'revoked'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def join_chat_by_invite(request, token):
    from apps.social.application.conversations import join_invite
    return Response(join_invite(token, request.user))


def _user_is_banned(chat, user) -> bool:
    from apps.social.infrastructure.models.social_chat import ChatBan

    return ChatBan.objects.filter(chat=chat, user=user).filter(
        Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
    ).exists()



class ModerationViewSet(TransactionalChatViewSet):
    moderation_permission = 'can_ban_users'

    def require_moderation(self, chat, target=None):
        from apps.social.application.conversations import check_access
        chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
        check_access(chat, self.request.user)
        action = 'ban' if self.moderation_permission == 'can_ban_users' else 'restrict'
        require_permission(chat, self.request.user, self.moderation_permission, target=target, action=action if target else None)
        return chat

    def get_object(self):
        obj = super().get_object()
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            self.require_moderation(obj.chat, obj.user)
            obj = type(obj).objects.select_for_update().get(pk=obj.pk)
        return obj

    def perform_update(self, serializer):
        instance = serializer.instance
        if serializer.validated_data.get('chat', instance.chat).pk != instance.chat_id:
            raise ValidationError({'chat': 'Нельзя переносить ограничения в другой чат'})
        self.require_moderation(instance.chat, serializer.validated_data.get('user', instance.user))
        serializer.save()


class ChatBanViewSet(ModerationViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ChatBan.objects.filter(Q(user=self.request.user) | Q(chat_id__in=managed_chat_ids(self.request, self.moderation_permission)))
        identifier = self.kwargs.get('chat_id') or self.request.query_params.get('chat')
        if identifier:
            qs = qs.filter(chat=resolve_chat(identifier, self.request.user, 'group'))
        return qs.select_related('chat', 'user', 'banned_by').distinct()

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatBanSerializer, ChatBanCreateSerializer
        return ChatBanCreateSerializer if self.action == 'create' else ChatBanSerializer

    def _require_permission(self, chat, permission: str):
        result = PermissionChecker(self.request.user, chat).has_permission(permission)
        if not result.allowed:
            raise PermissionDenied(
                result.reason or 'Недостаточно прав для этого действия'
            )

    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        if chat is None:
            raise ValidationError({'chat': 'Чат обязателен'})
        self.require_moderation(chat, serializer.validated_data.get('user'))
        serializer.save(banned_by=self.request.user)

    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        ban = self.get_object()
        member = ChatMember.objects.filter(chat=ban.chat, user=request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Нет прав на разблокировку')
        ban.delete()
        ChatAdminLog.objects.create(
            chat=ban.chat, user=request.user,
            action='member_unbanned', target_user=ban.user,
            details={'reason': 'Manual unban'}
        )
        return Response({'status': 'unbanned'})


class ChatRestrictionViewSet(ModerationViewSet):
    moderation_permission = 'can_restrict_members'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ChatRestriction.objects.filter(Q(user=self.request.user) | Q(chat_id__in=managed_chat_ids(self.request, self.moderation_permission)))
        identifier = self.kwargs.get('chat_id') or self.request.query_params.get('chat')
        if identifier:
            qs = qs.filter(chat=resolve_chat(identifier, self.request.user, 'group'))
        return qs.select_related('chat', 'user', 'restricted_by').distinct()

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatRestrictionSerializer, ChatRestrictionCreateSerializer
        return ChatRestrictionCreateSerializer if self.action == 'create' else ChatRestrictionSerializer

    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        if chat is None:
            raise ValidationError({'chat': 'Чат обязателен'})
        self.require_moderation(chat, serializer.validated_data.get('user'))
        serializer.save(restricted_by=self.request.user)

    @action(detail=True, methods=['post'])
    def lift(self, request, pk=None):
        restriction = self.get_object()
        member = ChatMember.objects.filter(chat=restriction.chat, user=request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Нет прав на снятие ограничений')
        restriction.delete()
        return Response({'status': 'lifted'})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def set_member_role(request, chat_id, user_id):
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    target = get_object_or_404(ChatMember.objects.select_related('role', 'user'), chat=chat, user_id=user_id)
    require_permission(chat, request.user, 'can_promote_members', target=target.user, action='promote')
    update_fields = []
    if 'role_id' in request.data:
        identifier = request.data['role_id']
        if identifier is not None and (type(identifier) is not int or identifier < 1):
            raise ValidationError({'role_id': 'Некорректный ID роли'})
        role = get_object_or_404(ChatRole, pk=identifier, chat=chat) if identifier is not None else None
        validate_role_grant(chat, request.user, role)
        target.role = role
        update_fields.append('role')
    if 'is_admin' in request.data:
        is_admin = request.data['is_admin']
        if type(is_admin) is not bool:
            raise ValidationError({'is_admin': 'Ожидается boolean'})
        if is_admin:
            require_permission(chat, request.user, 'can_add_new_admins')
        target.is_admin = is_admin
        update_fields.append('is_admin')
    if update_fields:
        target.save(update_fields=update_fields)
        ChatAdminLog.objects.create(chat=chat, user=request.user, action='member_promoted', target_user=target.user,
                                   details={'new_role_id': target.role_id, 'is_admin': target.is_admin})
    return Response({'status': 'role_updated'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def transfer_ownership(request, chat_id):
    from apps.social.application.conversations import check_access_for_join
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    current = get_object_or_404(ChatMember, chat=chat, user=request.user)
    if chat.discussion_type in ('anime', 'franchise'):
        raise ValidationError('Обсуждением управляют администраторы сайта; владение не передаётся')
    if not current.is_owner:
        raise PermissionDenied('Только владелец может передать владение')
    new = get_object_or_404(ChatMember.objects.select_related('user', 'role'), chat=chat, user_id=request.data.get('user_id'))
    check_access_for_join(chat, new.user)
    if not new.user.is_active:
        raise ValidationError({'user_id': 'Аккаунт отключён'})
    if current.pk == new.pk:
        return Response({'status': 'ownership_transferred'})
    chat.created_by = new.user
    chat.save(update_fields=['created_by'])
    current.is_admin = new.is_admin = True
    for member in (current, new):
        if member.role and member.role.level >= 3:
            member.role = None
        member.save(update_fields=['is_admin', 'role'])
    ChatAdminLog.objects.create(chat=chat, user=request.user, action='chat_updated', target_user=new.user,
                               details={'action': 'ownership_transferred'})
    return Response({'status': 'ownership_transferred'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def remove_member(request, chat_id):
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    target = get_object_or_404(ChatMember.objects.select_related('user', 'role'), chat=chat, user_id=request.data.get('user_id'))
    require_permission(chat, request.user, 'can_manage_chat', target=target.user, action='remove')
    target.delete()
    ChatAdminLog.objects.create(chat=chat, user=request.user, action='member_left', target_user=target.user,
                               details={'action': 'removed_by_admin'})
    return Response({'status': 'removed'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def ban_user(request, chat_id):
    from rest_framework import serializers
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    target = get_object_or_404(User, pk=request.data.get('user_id'))
    require_permission(chat, request.user, 'can_ban_users', target=target, action='ban')
    until_date = serializers.DateTimeField(allow_null=True).run_validation(request.data.get('until_date'))
    reason = serializers.CharField(max_length=2000, allow_blank=True).run_validation(request.data.get('reason', ''))
    ChatBan.objects.update_or_create(chat=chat, user=target,
        defaults={'banned_by': request.user, 'reason': reason, 'until_date': until_date})
    ChatAdminLog.objects.create(chat=chat, user=request.user, action='member_banned', target_user=target, details={'reason': reason})
    return Response({'status': 'banned'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def unban_user(request, chat_id):
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    ban = get_object_or_404(ChatBan.objects.select_related('user'), chat=chat, user_id=request.data.get('user_id'))
    require_permission(chat, request.user, 'can_ban_users', target=ban.user, action='ban')
    ChatMember.objects.filter(chat=chat, user=ban.user, is_banned=True).update(is_banned=False, banned_by=None, banned_at=None, ban_reason='')
    ban.delete()
    ChatAdminLog.objects.create(chat=chat, user=request.user, action='member_unbanned', target_user=ban.user)
    return Response({'status': 'unbanned'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_banned_users(request, chat_id):
    try:
        chat = resolve_chat(chat_id, request.user, 'group')
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if not member.is_owner and not member.is_admin:
        return Response({'error': 'Нет доступа'}, status=403)

    from apps.social.presentation.serializers.social_chat_serializers import ChatBanSerializer
    bans = ChatBan.objects.filter(chat=chat).select_related('user', 'banned_by')
    return Response(ChatBanSerializer(bans, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_restricted_users(request, chat_id):
    try:
        chat = resolve_chat(chat_id, request.user, 'group')
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if not member.is_owner and not member.is_admin:
        return Response({'error': 'Нет доступа'}, status=403)

    from apps.social.presentation.serializers.social_chat_serializers import ChatRestrictionSerializer
    restrictions = ChatRestriction.objects.filter(chat=chat).filter(
        Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
    ).select_related('user', 'restricted_by')
    return Response(ChatRestrictionSerializer(restrictions, many=True).data)



def _reactions_payload(message):
    reactions = getattr(message, 'reactions', None)
    return reactions if isinstance(reactions, dict) else {}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def toggle_reaction(request, message_id):
    emoji = request.data.get('emoji')
    if not emoji:
        return Response({'error': 'emoji required'}, status=400)

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)

    if message.chat:
        if not ChatMember.objects.filter(chat=message.chat, user=request.user).exists():
            return Response({'error': 'Нет доступа'}, status=403)
    elif message.private_chat:
        if request.user not in [message.private_chat.user1, message.private_chat.user2]:
            return Response({'error': 'Нет доступа'}, status=403)
    else:
        return Response({'error': 'Сообщение не привязано к чату'}, status=400)

    reaction, created = MessageReaction.objects.get_or_create(
        message=message, user=request.user, emoji=emoji
    )
    if not created:
        reaction.delete()
        return Response({
            'status': 'removed',
            'emoji': emoji,
            'reactions': _reactions_payload(message),
        })

    if message.sender_id != request.user.id:
        try:
            from apps.notifications.application.services import NotificationService
            NotificationService.create_notification(
                user=message.sender,
                notification_type='reaction',
                title=f'{request.user.username} отреагировал на ваше сообщение',
                content=f'{emoji}',
                link=f"/chats/{message.chat_id or message.private_chat_id}",
                icon='❤️',
                content_object=message,
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление о реакции: {e}")

    return Response({
        'status': 'added',
        'emoji': emoji,
        'reactions': _reactions_payload(message),
    })



class ChatFolderViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ChatFolder.objects.filter(user=self.request.user).prefetch_related('chats')

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatFolderSerializer
        return ChatFolderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post', 'patch'])
    @transaction.atomic
    def reorder(self, request):
        from rest_framework.exceptions import ValidationError
        ids = request.data.get('folder_ids', [])
        folders = list(self.get_queryset().select_for_update())
        if not isinstance(ids, list) or len(ids) != len(set(ids)) or set(ids) != {f.pk for f in folders}:
            raise ValidationError({'folder_ids': 'Укажите все свои папки по одному разу'})
        for index, pk in enumerate(ids):
            ChatFolder.objects.filter(pk=pk).update(position=index)
        return Response({'status': 'reordered'})

    @action(detail=True, methods=['post'])
    def add_chat(self, request, pk=None):
        from apps.social.application.conversations import get_conversation
        folder = self.get_object()
        kind = request.data.get('chat_type')
        chat = resolve_chat(request.data.get('chat_id'), request.user, kind)
        if isinstance(chat, GroupChat) and not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            raise PermissionDenied('Сначала вступите в чат')
        ChatFolderChat.objects.get_or_create(folder=folder, chat_type=kind, chat_id=chat.public_id,
            defaults={'conversation': get_conversation(chat)})
        return Response({'status': 'added'})

    @action(detail=True, methods=['post'])
    def remove_chat(self, request, pk=None):
        folder = self.get_object()
        ChatFolderChat.objects.filter(folder=folder, chat_type=request.data.get('chat_type'),
            chat_id=request.data.get('chat_id')).delete()
        return Response({'status': 'removed'})

    @action(detail=True, methods=['get'])
    def chats(self, request, pk=None):
        return Response(folder_chats(self.get_object(), request))

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        chats = folder_chats(self.get_object(), request)
        return Response({'folder_id': int(pk), 'chat_count': len(chats),
            'unread_count': sum(c['unread_count'] for c in chats), 'chats': chats[:10]})


def folder_chats(folder, request):
    from apps.social.application import conversations as service
    from apps.social.presentation.views.conversation_views import detail
    from rest_framework.exceptions import APIException
    from apps.social.infrastructure.models.conversation import ConversationUserState
    selected = {item.conversation_id for item in folder.chats.all()}
    candidates = []
    rules = folder.rules or {}
    include_private = rules.get('include_private', folder.include_private)
    include_groups = rules.get('include_groups', folder.include_groups)
    if include_private or selected:
        candidates.extend(PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).select_related('user1', 'user2'))
    if include_groups or rules.get('include_anime_discussions') or folder.include_channels or selected:
        candidates.extend(GroupChat.objects.filter(members__user=request.user).distinct())
    result = []
    for chat in candidates:
        try:
            service.check_access(chat, request.user)
            conv = service.get_conversation(chat)
            if ConversationUserState.objects.filter(conversation=conv, user=request.user, hidden=True).exists():
                continue
            kind = service.chat_kind(chat)
            row = detail(chat, request)
            settings = row.get('user_settings') or row.get('user_member_settings') or {}
            archived = settings.get('is_archived', False)
            muted = settings.get('is_muted', False)
            pinned = settings.get('is_pinned', False)
            filters = []
            if include_private or include_groups or rules.get('include_anime_discussions'):
                discussion = kind == 'group' and chat.folder_type == 'discussions'
                filters.append((kind == 'private' and include_private) or (kind == 'group' and include_groups and not discussion)
                    or (discussion and rules.get('include_anime_discussions', False)))
            if folder.include_pinned:
                filters.append(pinned)
            included = conv.pk in selected or (bool(filters) and (all(filters) if folder.match_all else any(filters)))
            if kind == 'private' and chat.other_user(request.user).pk in rules.get('exclude_user_ids', []):
                continue
            name = (row.get('name') or row.get('other_user', {}).get('username') or '').lower()
            if any(word.lower() in name for word in rules.get('exclude_keywords', []) if word):
                continue
            if rules.get('include_keywords') and not any(word.lower() in name for word in rules['include_keywords'] if word):
                continue
            if rules.get('only_unread') and not row['unread_count']:
                continue
            if rules.get('only_pinned') and not pinned:
                continue
            if included and (folder.include_archived or not archived) and (folder.include_muted or not muted):
                result.append(row)
        except APIException:
            continue
    return result


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_folder_chats(request, folder_id):
    return Response(folder_chats(get_object_or_404(ChatFolder, pk=folder_id, user=request.user), request))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_chat_analytics(request, chat_id):
    from apps.social.application import conversations as service
    chat = resolve_chat(chat_id, request.user, 'group')
    service.require_permission(chat, request.user, 'can_manage_chat')

    try:
        days = int(request.query_params.get('days', 7))
    except (TypeError, ValueError):
        raise ValidationError({'days': 'Ожидается число дней'})
    days = max(1, min(days, 90))

    cache_key = f'chat_analytics:v2:{chat.pk}:{request.user.pk}:{service.get_conversation(chat).event_seq}:{days}'
    if request.query_params.get('refresh') not in ('1', 'true'):
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

    from apps.social.application.chat_settings_service import ChatAnalytics as CA
    ca = CA(chat, request.user)
    activity, members, content = ca.get_activity_stats(days), ca.get_member_stats(), ca.get_content_stats(days)
    payload = {
        'activity': activity, 'members': members, 'content': content,
        'engagement_score': ca.get_engagement_score(activity=activity if days == 7 else None,
            members=members, content=content if days == 7 else None),
    }
    cache.set(cache_key, payload, 60)
    return Response(payload)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def export_settings(request):
    exporter = SettingsExport()
    return Response(exporter.export_user_settings(request.user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([SettingsImportParser])
@transaction.atomic
def import_settings(request):
    importer = SettingsExport()
    return Response(importer.import_user_settings(request.user, request.data))



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def bulk_delete_messages(request, chat_id):
    try:
        chat = resolve_chat(chat_id, request.user, 'group')
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    checker = PermissionChecker(request.user, chat)
    r = checker.has_permission('can_delete_messages')
    if not r.allowed:
        return Response({'error': r.reason}, status=403)

    ids = request.data.get('message_ids', [])
    count = Message.objects.filter(id__in=ids, chat=chat).update(
        is_deleted=True, deleted_at=timezone.now(), deleted_by=request.user
    )
    return Response({'deleted_count': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def bulk_add_members(request, chat_id):
    from apps.social.application.conversations import check_access_for_join
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    require_permission(chat, request.user, 'can_invite_users')
    ids = member_ids(request.data.get('user_ids', []))
    users = list(User.objects.filter(pk__in=ids, is_active=True))
    if len(users) != len(ids):
        raise ValidationError({'user_ids': 'Пользователь не найден или отключён'})
    for user in users:
        check_access_for_join(chat, user)
    existing = set(chat.members.values_list('user_id', flat=True))
    added = [user for user in users if user.pk not in existing]
    if len(existing) + len(added) > chat.max_members:
        raise ValidationError({'user_ids': 'Чат переполнен'})
    for user in added:
        ChatMember.objects.create(chat=chat, user=user)
    return Response({'added_count': len(added)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def bulk_remove_members(request, chat_id):
    chat = GroupChat.objects.select_for_update().get(pk=resolve_chat(chat_id, request.user, 'group').pk)
    require_permission(chat, request.user, 'can_manage_chat')
    ids = member_ids(request.data.get('user_ids', []))
    targets = list(ChatMember.objects.filter(chat=chat, user_id__in=ids).select_related('user', 'role'))
    for target in targets:
        require_permission(chat, request.user, 'can_manage_chat', target=target.user, action='remove')
    for target in targets:
        target.delete()
    return Response({'removed_count': len(targets)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pin_message_new(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)

    if message.chat:
        checker = PermissionChecker(request.user, message.chat)
        r = checker.has_permission('can_pin_messages')
        if not r.allowed:
            return Response({'error': r.reason}, status=403)

    MessagePin.objects.get_or_create(
        chat=message.chat,
        private_chat=message.private_chat,
        message=message,
        defaults={'pinned_by': request.user}
    )
    message.is_pinned = True
    message.pinned_by = request.user
    message.pinned_at = timezone.now()
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at'])

    if message.chat:
        ChatAdminLog.objects.create(
            chat=message.chat, user=request.user,
            action='message_pinned', message=message
        )
    return Response({'status': 'pinned'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def unpin_message_new(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)

    if message.chat:
        checker = PermissionChecker(request.user, message.chat)
        r = checker.has_permission('can_pin_messages')
        if not r.allowed:
            return Response({'error': r.reason}, status=403)

    MessagePin.objects.filter(message=message).delete()
    message.is_pinned = False
    message.pinned_by = None
    message.pinned_at = None
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at'])
    return Response({'status': 'unpinned'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_pinned_messages_new(request, chat_id):
    chat_type = request.query_params.get('type', 'group')
    if chat_type == 'group':
        chat = resolve_chat(chat_id, request.user, 'group')
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({'error': 'Нет доступа'}, status=403)
        pins = MessagePin.objects.filter(chat=chat).select_related('message', 'pinned_by')
    else:
        chat = resolve_chat(chat_id, request.user, 'private')
        if request.user not in [chat.user1, chat.user2]:
            return Response({'error': 'Нет доступа'}, status=403)
        pins = MessagePin.objects.filter(private_chat=chat).select_related('message', 'pinned_by')

    data = [{'id': p.id, 'message_id': p.message_id, 'pinned_by': p.pinned_by.username, 'created_at': p.created_at} for p in pins]
    return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def clear_chat_history(request, chat_id):
    chat_type = request.query_params.get('type', 'private')
    
    if chat_type == 'private':
        chat = resolve_chat(chat_id, request.user, 'private')
        if request.user not in [chat.user1, chat.user2]:
            return Response({'error': 'Нет доступа'}, status=403)
        
        deleted_count = Message.objects.filter(
            private_chat=chat,
            is_deleted=False
        ).update(
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=request.user
        )
        
        MessageReadStatus.objects.filter(message__private_chat=chat).delete()
        
        from core.redis_events import event_publisher
        event_publisher.publish_event(
            "chat_cleared",
            {"chat_id": chat_id},
            target_users=[chat.user1.id, chat.user2.id]
        )
        
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_cleared",
                "chat_id": chat_id,
                "cleared_by": request.user.id,
                "cleared_at": timezone.now().isoformat(),
            }
        )
        
        return Response({'status': 'cleared', 'deleted_count': deleted_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def init_franchise_discussion(request):
    from apps.anime.infrastructure.models.anime import Franchise, Anime as AnimeModel
    from apps.social.application import conversations as service
    from rest_framework.exceptions import ValidationError
    franchise = get_object_or_404(Franchise.objects.select_for_update(), pk=request.data.get('franchise_id'))
    ids = request.data.get('anime_ids', [])
    if not isinstance(ids, list) or len(ids) > 500 or any(type(pk) is not int for pk in ids):
        raise ValidationError({'anime_ids': 'Ожидается список до 500 частей франшизы'})
    parts = list(AnimeModel.objects.filter(franchise=franchise, pk__in=ids).order_by('franchise_order', 'year', 'pk'))
    if len(parts) != len(set(ids)):
        raise ValidationError({'anime_ids': 'Все части должны принадлежать выбранной франшизе'})
    from apps.social.application._discussion_views_patch import ensure_franchise_group
    chat, franchise, parts = ensure_franchise_group(franchise.pk, request.user)
    service.join_group(chat, request.user)
    def poster(obj):
        if obj and getattr(obj, 'poster', None):
            return request.build_absolute_uri(obj.poster.url)
        return getattr(obj, 'poster_url', None) if obj else None
    first = parts[0] if parts else AnimeModel.objects.filter(franchise=franchise).first()
    cover = poster(franchise) or poster(first)
    topics = [{'id': t.pk, 'chat_id': chat.public_id, 'title': t.title, 'order': t.order,
        'anime_id': t.anime_id, 'anime_title': (t.anime.title_ru or t.anime.title_en) if t.anime else None,
        'poster_url': poster(t.anime) if t.anime else cover, 'slug': t.slug}
        for t in ChatTopic.objects.filter(chat=chat).select_related('anime').order_by('order', 'pk')]
    return Response({'group_id': chat.public_id, 'group_map': {str(t['anime_id']) if t['anime_id'] else 'general': chat.public_id for t in topics},
        'franchise_name': franchise.name, 'franchise_poster': cover, 'topics': topics})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def global_chat_style(request):
    from apps.social.infrastructure.models.social_chat import UserGlobalChatStyle
    obj, _ = UserGlobalChatStyle.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response({
            'wallpaper_type':    obj.wallpaper_type,
            'wallpaper_color':   obj.wallpaper_color,
            'wallpaper_color2':  obj.wallpaper_color2,
            'bubble_style':      obj.bubble_style,
            'accent_color':      obj.accent_color,
            'font_size':         obj.font_size,
            'message_animation': obj.message_animation,
            'emoji_set':         obj.emoji_set,
            'time_format':       obj.time_format,
        })

    fields = [
        'wallpaper_type', 'wallpaper_color', 'wallpaper_color2',
        'bubble_style', 'accent_color', 'font_size',
        'message_animation', 'emoji_set', 'time_format',
    ]
    from apps.social.presentation.serializers.social_serializers import GlobalChatStyleSerializer

    serializer = GlobalChatStyleSerializer(obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    for f, value in validated.items():
        setattr(obj, f, value)
    obj.save()
    return Response({'status': 'saved'})



class SecurityLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SecurityLog.objects.filter(user=self.request.user)
        action = self.request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import SecurityLogSerializer
        return SecurityLogSerializer



class ChatJoinRequestViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.social.application.conversations import check_access
        from rest_framework.exceptions import APIException
        managed = []
        for chat in GroupChat.objects.filter(members__user=self.request.user).distinct():
            try:
                check_access(chat, self.request.user)
                if PermissionChecker(self.request.user, chat).has_permission('can_invite_users').allowed:
                    managed.append(chat.pk)
            except APIException:
                continue
        qs = ChatJoinRequest.objects.filter(Q(user=self.request.user) | Q(chat_id__in=managed)).select_related('chat', 'user', 'reviewed_by')
        identifier = self.kwargs.get('chat_id') or self.request.query_params.get('chat')
        if identifier:
            qs = qs.filter(chat=resolve_chat(identifier, self.request.user, 'group'))
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatJoinRequestSerializer, ChatJoinRequestCreateSerializer
        return ChatJoinRequestCreateSerializer if self.action == 'create' else ChatJoinRequestSerializer

    def create(self, request, *args, **kwargs):
        from apps.social.application.conversations import request_join
        from apps.social.presentation.serializers.social_chat_serializers import ChatJoinRequestSerializer
        values = request.data.copy()
        if self.kwargs.get('chat_id'):
            values['chat'] = self.kwargs['chat_id']
        serializer = self.get_serializer(data=values)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        jr = request_join(values.pop('chat'), request.user, values)
        return Response(ChatJoinRequestSerializer(jr, context=self.get_serializer_context()).data, status=201)

    def require_editable(self, obj):
        GroupChat.objects.select_for_update().get(pk=obj.chat_id)
        obj.refresh_from_db()
        if obj.user_id != self.request.user.pk or obj.status != 'pending':
            raise PermissionDenied('Можно менять только свою ожидающую заявку')
        return obj

    def perform_update(self, serializer):
        obj = self.require_editable(serializer.instance)
        if serializer.validated_data.get('chat', obj.chat).pk != obj.chat_id:
            raise ValidationError({'chat': 'Нельзя перенести заявку в другой чат'})
        serializer.save()

    def perform_destroy(self, instance):
        self.require_editable(instance).delete()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        from apps.social.application.conversations import review_join
        review_join(self.get_object().pk, request.user, approve=True)
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        from apps.social.application.conversations import review_join
        review_join(self.get_object().pk, request.user, approve=False)
        return Response({'status': 'rejected'})


class ChatTagViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatTag.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatTagSerializer
        return ChatTagSerializer

    def save_tag(self, serializer):
        User.objects.select_for_update().get(pk=self.request.user.pk)
        if serializer.instance:
            serializer.instance.refresh_from_db()
        name = serializer.validated_data.get('name', getattr(serializer.instance, 'name', ''))
        duplicates = self.get_queryset().filter(name=name)
        if serializer.instance:
            duplicates = duplicates.exclude(pk=serializer.instance.pk)
        if duplicates.exists():
            raise ValidationError({'name': 'Тег с таким именем уже существует'})
        serializer.save(user=self.request.user)

    def perform_create(self, serializer):
        self.save_tag(serializer)

    def perform_update(self, serializer):
        self.save_tag(serializer)


class ChatTagAssignmentViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return ChatTagAssignment.objects.filter(tag__user=self.request.user).select_related('tag', 'group_chat', 'private_chat')

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatTagAssignmentSerializer
        return ChatTagAssignmentSerializer

    def perform_create(self, serializer):
        from apps.social.application.conversations import check_access
        chat = serializer.validated_data.get('group_chat') or serializer.validated_data.get('private_chat')
        chat = type(chat).objects.select_for_update().get(pk=chat.pk)
        check_access(chat, self.request.user)
        if isinstance(chat, GroupChat) and not ChatMember.objects.filter(chat=chat, user=self.request.user).exists():
            raise PermissionDenied('Сначала вступите в чат')
        tag = get_object_or_404(ChatTag.objects.select_for_update(), pk=serializer.validated_data['tag'].pk, user=self.request.user)
        obj, _ = ChatTagAssignment.objects.get_or_create(tag=tag,
            group_chat=serializer.validated_data.get('group_chat'), private_chat=serializer.validated_data.get('private_chat'))
        serializer.instance = obj



class AntiSpamRuleViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = AntiSpamRule.objects.filter(chat_id__in=managed_chat_ids(self.request, 'can_manage_chat'))
        identifier = self.kwargs.get('chat_id') or self.request.query_params.get('chat')
        return qs.filter(chat=resolve_chat(identifier, self.request.user, 'group')) if identifier else qs

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import AntiSpamRuleSerializer
        return AntiSpamRuleSerializer

    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        if chat is None:
            raise ValidationError({'chat': 'Чат обязателен'})
        chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
        require_permission(chat, self.request.user, 'can_manage_chat')
        serializer.save()

    def perform_update(self, serializer):
        chat = serializer.instance.chat
        chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
        require_permission(chat, self.request.user, 'can_manage_chat')
        serializer.instance.refresh_from_db()
        new_chat = serializer.validated_data.get('chat')
        if new_chat is not None and new_chat.pk != chat.pk:
            raise ValidationError({'chat': 'Нельзя перенести правило в другой чат'})
        serializer.save()

    def perform_destroy(self, instance):
        chat = GroupChat.objects.select_for_update().get(pk=instance.chat_id)
        require_permission(chat, self.request.user, 'can_manage_chat')
        instance.delete()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def check_message_spam(request, chat_id):
    try:
        chat = resolve_chat(chat_id, request.user, 'group')
    except GroupChat.DoesNotExist:
        return Response({'error': 'Чат не найден'}, status=404)

    text = request.data.get('text', '')
    temp = Message(chat=chat, sender=request.user, text=text)
    service = AntiSpamService(chat)
    return Response(service.check_message(temp))



class ScheduledMessageViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ScheduledMessage.objects.filter(sender=self.request.user).select_related('chat', 'private_chat', 'sender')
        return qs.select_for_update() if self.request.method not in ('GET', 'HEAD', 'OPTIONS') else qs

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ScheduledMessageSerializer, ScheduledMessageCreateSerializer
        return ScheduledMessageCreateSerializer if self.action in ['create', 'update', 'partial_update'] else ScheduledMessageSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from apps.social.presentation.serializers.social_chat_serializers import ScheduledMessageSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(sender=request.user)
        return Response(ScheduledMessageSerializer(job, context={'request': request}).data, status=201)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        msg = self.get_object()
        if msg.status != 'scheduled':
            return Response({'error': 'Можно отменить только запланированные'}, status=400)
        msg.status = 'cancelled'
        msg.save(update_fields=['status'])
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        msg = self.get_object()
        if msg.status != 'scheduled':
            return Response(
                {'error': 'Отправить можно только запланированное'}, status=400
            )
        if not (msg.chat_id or msg.private_chat_id):
            return Response({'error': 'Сообщение не привязано к чату'}, status=400)

        msg.scheduled_at = timezone.now()
        msg.save(update_fields=['scheduled_at'])

        try:
            from apps.social.application.tasks_chat import send_scheduled_messages
            send_scheduled_messages.delay()
        except Exception as e:
            logger.warning(f"send_now: не удалось поставить задачу в очередь: {e}")

        msg.refresh_from_db()
        serializer = self.get_serializer(msg)
        return Response(serializer.data)



class ChatBackupViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = ChatBackup.objects.filter(chat_id__in=managed_chat_ids(self.request, 'can_manage_chat')).select_related('chat', 'created_by')
        identifier = self.kwargs.get('chat_id') or self.request.query_params.get('chat')
        return qs.filter(chat=resolve_chat(identifier, self.request.user, 'group')) if identifier else qs

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatBackupSerializer
        return ChatBackupSerializer

    def get_serializer(self, *args, **kwargs):
        identifier = self.kwargs.get('chat_id')
        if self.action == 'create' and identifier and 'data' in kwargs:
            chat = resolve_chat(identifier, self.request.user, 'group')
            data = kwargs['data'].copy()
            if data.get('chat') and resolve_chat(data['chat'], self.request.user, 'group').pk != chat.pk:
                raise ValidationError({'chat': 'Чат не совпадает с адресом запроса'})
            data['chat'] = chat.public_id
            kwargs['data'] = data
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        from apps.social.application.chat_backups import require_backup_access
        from apps.social.application.tasks import backup_chat_task
        chat = GroupChat.objects.select_for_update().get(pk=serializer.validated_data['chat'].pk)
        require_backup_access(chat, self.request.user)
        backup = serializer.save(created_by=self.request.user, status='creating')
        transaction.on_commit(lambda: backup_chat_task.delay(backup.pk), robust=True)

    def perform_destroy(self, instance):
        from apps.social.application.chat_backups import require_backup_access
        chat = GroupChat.objects.select_for_update().get(pk=instance.chat_id)
        require_backup_access(chat, self.request.user)
        file = instance.backup_file
        instance.delete()
        if file:
            transaction.on_commit(lambda: file.delete(save=False), robust=True)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        from django.http import FileResponse
        from apps.social.application.chat_backups import require_backup_access
        backup = self.get_object()
        require_backup_access(backup.chat, request.user)
        if backup.status != 'completed' or not backup.backup_file:
            raise ValidationError('Резервная копия ещё не готова')
        response = FileResponse(backup.backup_file.open('rb'), as_attachment=True, filename=f'chat-{backup.chat.public_id}-{backup.pk}.zip')
        response['Cache-Control'] = 'private, no-store'
        return response

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        from apps.social.application.chat_backups import restore_backup
        dry_run = request.data.get('dry_run', False)
        if type(dry_run) is not bool:
            raise ValidationError({'dry_run': 'Ожидается boolean'})
        return Response(restore_backup(self.get_object().pk, request.user, dry_run=dry_run))

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        from apps.social.application.tasks import backup_chat_task
        backup = self.get_object()
        if backup.status != 'failed':
            raise ValidationError('Повтор доступен для неудачной копии')
        backup.status = 'creating'
        backup.save(update_fields=['status'])
        transaction.on_commit(lambda: backup_chat_task.delay(backup.pk), robust=True)
        return Response(self.get_serializer(backup).data)


class ChatSlowModeViewSet(TransactionalChatViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.social.application.conversations import check_access
        from rest_framework.exceptions import APIException
        allowed = []
        for chat in GroupChat.objects.filter(members__user=self.request.user).distinct():
            try:
                check_access(chat, self.request.user)
                allowed.append(chat.pk)
            except APIException:
                continue
        qs = ChatSlowMode.objects.filter(chat_id__in=allowed).select_related('chat')
        identifier = self.request.query_params.get('chat')
        return qs.filter(chat=resolve_chat(identifier, self.request.user, 'group')) if identifier else qs

    def get_serializer_class(self):
        from apps.social.presentation.serializers.social_chat_serializers import ChatSlowModeSerializer
        return ChatSlowModeSerializer

    def save_mode(self, serializer):
        from apps.social.application.conversations import record_event
        chat = serializer.instance.chat if serializer.instance else serializer.validated_data['chat']
        chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
        require_permission(chat, self.request.user, 'can_manage_chat')
        if serializer.validated_data.get('chat', chat).pk != chat.pk:
            raise ValidationError({'chat': 'Нельзя перенести настройки в другой чат'})
        if serializer.instance:
            serializer.instance.refresh_from_db()
        if serializer.instance is None and ChatSlowMode.objects.filter(chat=chat).exists():
            raise ValidationError({'chat': 'Настройки уже существуют'})
        obj = serializer.save()
        GroupChat.objects.filter(pk=chat.pk).update(slow_mode_delay=obj.delay if obj.enabled else 0)
        record_event(chat, 'chat_updated', {})

    def perform_create(self, serializer):
        self.save_mode(serializer)

    def perform_update(self, serializer):
        self.save_mode(serializer)

    def perform_destroy(self, instance):
        from apps.social.application.conversations import record_event
        chat = GroupChat.objects.select_for_update().get(pk=instance.chat_id)
        require_permission(chat, self.request.user, 'can_manage_chat')
        instance.delete()
        GroupChat.objects.filter(pk=chat.pk).update(slow_mode_delay=0)
        record_event(chat, 'chat_updated', {})
