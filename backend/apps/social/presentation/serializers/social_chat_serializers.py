from rest_framework import serializers
from .chat_fields import ChatModelSerializer
from django.utils import timezone
from django.db.models import Q

from apps.social.infrastructure.models.social_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme,
    MessageReaction, ChatBan, ChatRestriction, ChatSlowMode,
    ChatJoinRequest, ChatTag, ChatTagAssignment, AntiSpamRule,
    ChatBackup, ScheduledMessage, SecurityLog, GroupChatSettings,
    PrivateChatSettings, MessagePin, GroupMemberSettings,
)
from apps.social.infrastructure.models.social import GroupChat, PrivateChat, Message, ChatRole, ChatMember, ChatFolder, ChatFolderChat
from apps.users.infrastructure.models.users import User
from apps.social.presentation.serializers.social_serializers import PrivateChatSerializer



class UserMiniSerializer(ChatModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar_url', 'is_online']

    def get_avatar_url(self, obj):
        if obj.avatar:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.avatar.url) if req else obj.avatar.url
        return None

    def get_is_online(self, obj):
        try:
            from core.online_status import online_status
            return online_status.is_online(obj.id)
        except Exception:
            return False



class ChatWallpaperSerializer(ChatModelSerializer):
    wallpaper_image_url = serializers.SerializerMethodField()
    css = serializers.SerializerMethodField()

    class Meta:
        model = ChatWallpaper
        fields = [
            'id', 'wallpaper_type',
            'wallpaper_color', 'wallpaper_color2',
            'wallpaper_intensity', 'wallpaper_blur', 'wallpaper_motion',
            'gradient_angle',
            'pattern_type', 'pattern_color', 'pattern_opacity',
            'wallpaper_image', 'wallpaper_image_url',
            'is_preset', 'preset_name', 'preset_category',
            'css', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_wallpaper_image_url(self, obj):
        if obj.wallpaper_image:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.wallpaper_image.url) if req else obj.wallpaper_image.url
        return None

    def get_css(self, obj):
        return obj.to_css()



class ChatThemeSerializer(ChatModelSerializer):
    css_vars = serializers.SerializerMethodField()

    class Meta:
        model = ChatTheme
        fields = [
            'id', 'theme',
            'message_color_mine', 'message_color_other',
            'message_text_color_mine', 'message_text_color_other',
            'bubble_style', 'bubble_border_radius', 'bubble_shadow',
            'anime_card_border_radius', 'playlist_card_border_radius',
            'font_family', 'font_size', 'font_size_px', 'font_weight', 'line_height',
            'time_format', 'time_color',
            'background_color', 'header_color', 'input_color',
            'input_text_color', 'accent_color', 'link_color',
            'message_animation', 'reaction_animation', 'typing_animation',
            'emoji_set', 'emoji_size',
            'show_avatars', 'show_usernames', 'compact_mode',
            'show_read_status', 'show_typing_indicator', 'message_grouping',
            'custom_css', 'css_vars', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_css_vars(self, obj):
        return obj.to_css_vars()



class PrivateChatSettingsSerializer(ChatModelSerializer):
    is_muted = serializers.ReadOnlyField()
    custom_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChatSettings
        fields = [
            'id', 'chat', 'user',
            'custom_name', 'custom_avatar', 'custom_avatar_url',
            'notifications_enabled', 'sound_enabled', 'notification_sound',
            'vibration_enabled', 'show_preview', 'show_popup',
            'muted_until', 'is_muted',
            'is_archived', 'is_pinned', 'is_hidden', 'is_blocked', 'blocked_at',
            'auto_delete_enabled', 'auto_delete_after',
            'folder_id', 'tags',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'is_system', 'created_at', 'updated_at']

    def get_custom_avatar_url(self, obj):
        if obj.custom_avatar:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.custom_avatar.url) if req else obj.custom_avatar.url
        return None



class GroupMemberSettingsSerializer(ChatModelSerializer):
    is_muted = serializers.ReadOnlyField()

    class Meta:
        model = GroupMemberSettings
        fields = [
            'id', 'notifications_enabled', 'mentions_only',
            'sound_enabled', 'notification_sound', 'vibration_enabled',
            'vibration_type', 'show_preview', 'show_popup',
            'muted_until', 'is_muted',
            'is_pinned', 'is_archived', 'tags',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class ChatInviteLinkSerializer(ChatModelSerializer):
    expires_at = serializers.DateTimeField(source='effective_expires_at', read_only=True)
    creator = UserMiniSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = ChatInviteLink
        fields = [
            'id', 'chat', 'creator', 'name', 'invite_link', 'link_type',
            'expires_at', 'usage_limit', 'usage_count', 'remaining_uses',
            'is_revoked', 'is_primary', 'auto_assign_role',
            'is_valid', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'invite_link', 'usage_count', 'creator', 'created_at', 'updated_at']

    def get_remaining_uses(self, obj):
        if obj.usage_limit is None:
            return None
        return max(0, obj.usage_limit - obj.usage_count)


class ChatInviteLinkCreateSerializer(ChatModelSerializer):
    class Meta:
        model = ChatInviteLink
        fields = ['chat', 'name', 'link_type', 'expires_at', 'usage_limit', 'is_primary', 'auto_assign_role']

    def validate(self, data):
        req = self.context.get('request')
        if req:
            chat = data.get('chat', getattr(self.instance, 'chat', None))
            try:
                member = ChatMember.objects.get(chat=chat, user=req.user)
                if not member.is_owner and not member.is_admin:
                    if not member.effective_permissions.get('can_invite_users', False):
                        raise serializers.ValidationError('Нет прав на создание приглашений')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник этого чата')
        chat = data.get('chat', getattr(self.instance, 'chat', None))
        role = data.get('auto_assign_role', getattr(self.instance, 'auto_assign_role', None))
        if role and role.chat_id != chat.pk:
            raise serializers.ValidationError({'auto_assign_role': 'Роль должна принадлежать этому чату'})
        if role:
            from apps.social.application.conversations import validate_role_grant
            validate_role_grant(chat, req.user, role)
        if data.get('usage_limit') is not None and data['usage_limit'] < 1:
            raise serializers.ValidationError({'usage_limit': 'Лимит должен быть положительным'})
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['creator'] = req.user
        return super().create(validated_data)



class ChatBanSerializer(ChatModelSerializer):
    user = UserMiniSerializer(read_only=True)
    banned_by = UserMiniSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = ChatBan
        fields = [
            'id', 'chat', 'user', 'banned_by', 'reason',
            'until_date', 'delete_messages', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'banned_by', 'created_at']


class ChatBanCreateSerializer(ChatModelSerializer):
    class Meta:
        model = ChatBan
        fields = ['chat', 'user', 'reason', 'until_date', 'delete_messages']

    def validate(self, data):
        chat = data.get('chat')
        user = data.get('user')
        if chat.created_by == user:
            raise serializers.ValidationError('Нельзя заблокировать владельца')
        req = self.context.get('request')
        if req:
            try:
                m = ChatMember.objects.get(chat=chat, user=req.user)
                if not m.is_owner and not m.is_admin and not m.effective_permissions.get('can_ban_users', False):
                    raise serializers.ValidationError('Нет прав на блокировку')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник')
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['banned_by'] = req.user
        if validated_data.get('delete_messages'):
            from apps.social.application.conversations import change_message
            for message_id in Message.objects.filter(chat=validated_data['chat'], sender=validated_data['user'], is_deleted=False).values_list('pk', flat=True):
                change_message(message_id, req.user, delete=True)
        ChatMember.objects.filter(chat=validated_data['chat'], user=validated_data['user']).delete()
        return super().create(validated_data)



class ChatRestrictionSerializer(ChatModelSerializer):
    user = UserMiniSerializer(read_only=True)
    restricted_by = UserMiniSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    restriction_type_display = serializers.CharField(source='get_restriction_type_display', read_only=True)

    class Meta:
        model = ChatRestriction
        fields = [
            'id', 'chat', 'user', 'restricted_by',
            'restriction_type', 'restriction_type_display',
            'reason', 'until_date', 'slow_mode_delay',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'restricted_by', 'created_at']


class ChatRestrictionCreateSerializer(ChatModelSerializer):
    class Meta:
        model = ChatRestriction
        fields = ['chat', 'user', 'restriction_type', 'reason', 'until_date', 'slow_mode_delay']

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['restricted_by'] = req.user
        return super().create(validated_data)



class ChatSlowModeSerializer(ChatModelSerializer):
    delay = serializers.IntegerField(min_value=0, max_value=3600, required=False)

    def validate_custom_delays(self, value):
        if not isinstance(value, dict) or len(value) > 500 or any(not isinstance(k, str) or not k.isdecimal() or int(k) < 1 or type(v) is not int or not 0 <= v <= 3600 for k, v in value.items()):
            raise serializers.ValidationError('Ожидается объект user_id → секунды от 0 до 3600')
        return value

    class Meta:
        model = ChatSlowMode
        fields = ['id', 'chat', 'enabled', 'delay', 'exempt_admins', 'exempt_moderators', 'custom_delays', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        validators = []



class ChatJoinRequestSerializer(ChatModelSerializer):
    user = UserMiniSerializer(read_only=True)
    reviewed_by = UserMiniSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChatJoinRequest
        fields = [
            'id', 'chat', 'user', 'message', 'answers',
            'status', 'status_display', 'reviewed_by', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at']


class ChatJoinRequestCreateSerializer(ChatModelSerializer):
    class Meta:
        model = ChatJoinRequest
        fields = ['chat', 'message', 'answers']
        validators = []

    def validate(self, data):
        if not data['chat'].is_public:
            raise serializers.ValidationError({'chat': 'Для закрытого чата нужна действующая ссылка приглашения'})
        if not isinstance(data.get('answers', {}), dict):
            raise serializers.ValidationError({'answers': 'Ожидается объект'})
        return data



class ChatTagSerializer(ChatModelSerializer):
    class Meta:
        model = ChatTag
        fields = ['id', 'user', 'name', 'color', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatTagAssignmentSerializer(ChatModelSerializer):
    tag = serializers.PrimaryKeyRelatedField(queryset=ChatTag.objects.none())

    class Meta:
        model = ChatTagAssignment
        fields = ['id', 'tag', 'group_chat', 'private_chat', 'created_at']
        read_only_fields = ['id', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tag'].queryset = ChatTag.objects.filter(user=self.context['request'].user)

    def validate(self, data):
        if bool(data.get('group_chat')) == bool(data.get('private_chat')):
            raise serializers.ValidationError('Укажите ровно один чат')
        group = data.get('group_chat')
        if group and not ChatMember.objects.filter(chat=group, user=self.context['request'].user, is_banned=False).exists():
            raise serializers.ValidationError('Сначала вступите в чат')
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['tag'] = ChatTagSerializer(instance.tag, context=self.context).data
        return data



class AntiSpamRuleSerializer(ChatModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AntiSpamRule
        fields = [
            'id', 'chat', 'rule_type', 'rule_type_display',
            'threshold', 'time_window', 'keywords',
            'action', 'action_display', 'action_duration',
            'enabled', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class ChatBackupSerializer(ChatModelSerializer):
    backup_file = serializers.SerializerMethodField()
    created_by = UserMiniSerializer(read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChatBackup
        fields = [
            'id', 'chat', 'created_by',
            'backup_file', 'messages_count', 'members_count',
            'file_size', 'file_size_mb', 'status', 'status_display', 'created_at', 'restored_at', 'error_message',
        ]
        read_only_fields = ['id', 'created_by', 'backup_file', 'messages_count', 'members_count', 'file_size', 'status', 'created_at', 'restored_at', 'error_message']

    def get_backup_file(self, obj):
        return f'/api/social/chat-backups/{obj.pk}/download/' if obj.status == 'completed' and obj.backup_file else None

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2) if obj.file_size else 0



class ScheduledMessageSerializer(ChatModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    media = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_media(self, obj):
        from apps.social.infrastructure.chat_storage import private_file_url
        return private_file_url(obj.media, self.context.get('request'))

    class Meta:
        model = ScheduledMessage
        fields = [
            'id', 'sender', 'chat', 'private_chat',
            'text', 'media', 'media_type',
            'scheduled_at', 'is_recurring', 'recurring_interval',
            'status', 'status_display', 'sent_at', 'error_message',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'sender', 'status', 'sent_at', 'error_message', 'created_at', 'updated_at']


class ScheduledMessageCreateSerializer(ChatModelSerializer):
    class Meta:
        model = ScheduledMessage
        fields = ['chat', 'private_chat', 'text', 'media', 'media_type', 'scheduled_at', 'is_recurring', 'recurring_interval']

    def validate(self, data):
        from apps.social.application.conversations import check_access
        chat = data.get('chat', getattr(self.instance, 'chat', None))
        private = data.get('private_chat', getattr(self.instance, 'private_chat', None))
        if bool(chat) == bool(private):
            raise serializers.ValidationError('Укажите ровно один чат')
        if self.instance and self.instance.status != 'scheduled':
            raise serializers.ValidationError('Сообщение уже обработано')
        check_access(chat or private, self.context['request'].user, write=True, media=bool(data.get('media')))
        if data.get('scheduled_at') and data['scheduled_at'] <= timezone.now():
            raise serializers.ValidationError('Время в прошлом')
        if data.get('is_recurring') and (data.get('recurring_interval') or 0) < 60:
            raise serializers.ValidationError('Интервал повторения должен быть не меньше 60 секунд')
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['sender'] = req.user
        return super().create(validated_data)



class SecurityLogSerializer(ChatModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = SecurityLog
        fields = [
            'id', 'user', 'action', 'action_display',
            'ip_address', 'user_agent', 'device_info', 'location',
            'details', 'is_suspicious', 'was_notified', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']



class GroupChatSettingsSerializer(ChatModelSerializer):
    class Meta:
        model = GroupChatSettings
        fields = [
            'id', 'chat', 'members_count', 'online_count', 'messages_count',
            'last_activity_at', 'last_message_at',
            'daily_messages', 'weekly_active', 'cache_updated_at',
        ]
        read_only_fields = ['id', 'cache_updated_at']



class MessagePinSerializer(ChatModelSerializer):
    pinned_by_username = serializers.CharField(source='pinned_by.username', read_only=True)

    class Meta:
        model = MessagePin
        fields = ['id', 'message', 'pinned_by', 'pinned_by_username', 'created_at']
        read_only_fields = ['id', 'created_at']



class ChatFolderSerializer(ChatModelSerializer):
    order = serializers.IntegerField(source='position', required=False, min_value=0)
    chats_count = serializers.SerializerMethodField()

    class Meta:
        from apps.social.infrastructure.models.social import ChatFolder
        model = ChatFolder
        fields = [
            'id', 'name', 'icon', 'color', 'order',
            'include_private', 'include_groups', 'include_channels',
            'include_archived', 'include_muted', 'match_all',
            'position', 'is_system', 'rules', 'created_at', 'updated_at', 'chats_count',
        ]
        read_only_fields = ['id', 'user', 'is_system', 'created_at', 'updated_at']

    def get_chats_count(self, obj):
        return obj.chats.count()

    def validate_rules(self, rules):
        if not isinstance(rules, dict):
            raise serializers.ValidationError('Ожидается объект правил')
        booleans = {'include_private', 'include_groups', 'include_bots', 'only_unread', 'only_pinned', 'include_anime_discussions'}
        keywords = {'exclude_keywords', 'include_keywords'}
        for key, value in rules.items():
            if key in booleans and type(value) is bool:
                continue
            if key in keywords and isinstance(value, list) and len(value) <= 32 and all(isinstance(w, str) and len(w) <= 100 for w in value):
                continue
            if key == 'exclude_user_ids' and isinstance(value, list) and len(value) <= 200 and all(type(i) is int for i in value):
                continue
            raise serializers.ValidationError(f'Некорректное правило: {key}')
        return rules


class ChatFolderCreateSerializer(ChatFolderSerializer):
    class Meta:
        from apps.social.infrastructure.models.social import ChatFolder
        model = ChatFolder
        fields = ['name', 'icon', 'color', 'order', 'include_private', 'include_groups',
                  'include_channels', 'include_archived', 'include_muted', 'match_all']
