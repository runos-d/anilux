from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


def publish_change(chat, kind='chat_updated', user_id=None):
    from apps.social.application.conversations import record_event
    record_event(chat, kind, {}, recipients=[user_id] if user_id else None)


@receiver(post_save, sender='social.ChatMember')
def on_member_saved(sender, instance, created, **kwargs):
    try:
        cache_pattern_key = f"chat_settings:*:group:{instance.chat_id}"
        cache.delete(f"chat_settings:{instance.user_id}:group:{instance.chat_id}")

        from apps.social.infrastructure.models.social_chat import GroupChatSettings
        gs, _ = GroupChatSettings.objects.get_or_create(chat_id=instance.chat_id)
        gs.members_count = instance.chat.members.count()
        gs.save(update_fields=['members_count', 'cache_updated_at'])
    except Exception:
        pass
    publish_change(instance.chat, 'member_updated')
    if instance.is_banned:
        publish_change(instance.chat, 'access_revoked', instance.user_id)


@receiver(post_delete, sender='social.ChatMember')
def on_member_deleted(sender, instance, **kwargs):
    try:
        cache.delete(f"chat_settings:{instance.user_id}:group:{instance.chat_id}")
        from apps.social.infrastructure.models.social_chat import GroupChatSettings
        try:
            gs = GroupChatSettings.objects.get(chat_id=instance.chat_id)
            gs.members_count = max(0, gs.members_count - 1)
            gs.save(update_fields=['members_count', 'cache_updated_at'])
        except GroupChatSettings.DoesNotExist:
            pass
    except Exception:
        pass
    origin = kwargs.get('origin')
    if isinstance(origin, sender) or getattr(origin, 'model', None) is sender:
        publish_change(instance.chat, 'member_updated')
        publish_change(instance.chat, 'access_revoked', instance.user_id)


@receiver(post_save, sender='social.Message')
def on_message_saved(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        if instance.chat_id:
            from apps.social.infrastructure.models.social_chat import GroupChatSettings
            gs, _ = GroupChatSettings.objects.get_or_create(chat_id=instance.chat_id)
            from django.db.models import F
            GroupChatSettings.objects.filter(pk=gs.pk).update(
                messages_count=F('messages_count') + 1,
                last_message_at=instance.created_at,
            )
    except Exception:
        pass


@receiver(post_save, sender='social.ChatWallpaper')
def on_wallpaper_saved(sender, instance, **kwargs):
    try:
        if instance.user_id:
            chat_type = 'group' if instance.chat_id else 'private'
            chat_id = instance.chat_id or instance.private_chat_id
            if chat_id:
                cache.delete(f"chat_wallpaper:{instance.user_id}:{chat_type}:{chat_id}")
                cache.delete(f"chat_settings:{instance.user_id}:{chat_type}:{chat_id}")
    except Exception:
        pass


@receiver(post_save, sender='social.ChatTheme')
def on_theme_saved(sender, instance, **kwargs):
    try:
        if instance.user_id:
            chat_type = 'group' if instance.chat_id else 'private'
            chat_id = instance.chat_id or instance.private_chat_id
            if chat_id:
                cache.delete(f"chat_theme:{instance.user_id}:{chat_type}:{chat_id}")
                cache.delete(f"chat_settings:{instance.user_id}:{chat_type}:{chat_id}")
    except Exception:
        pass


@receiver(post_save, sender='social.PrivateChatSettings')
def on_private_chat_settings_saved(sender, instance, **kwargs):
    try:
        cache.delete(f"chat_settings:{instance.user_id}:private:{instance.chat_id}")
    except Exception:
        pass
    from apps.social.infrastructure.models.social import PrivateChat
    prefix = 'user1' if instance.chat.user1_id == instance.user_id else 'user2'
    PrivateChat.objects.filter(pk=instance.chat_id).update(**{
        f'{prefix}_notifications': instance.notifications_enabled,
        f'{prefix}_muted_until': instance.muted_until, f'{prefix}_archived': instance.is_archived,
        f'{prefix}_pinned': instance.is_pinned, f'{prefix}_blocked': instance.is_blocked,
    })
    publish_change(instance.chat)


@receiver(post_save, sender='social.GroupChat')
@receiver(post_save, sender='social.PrivateChat')
def on_chat_saved(sender, instance, created, update_fields=None, **kwargs):
    if not created and (update_fields is None or set(update_fields) - {'members_count', 'last_message_at'}):
        publish_change(instance)


@receiver(post_save, sender='social.ChatBan')
def on_chat_ban_saved(sender, instance, **kwargs):
    if instance.is_active:
        publish_change(instance.chat, 'access_revoked', instance.user_id)


@receiver(post_save, sender='social.ChatRestriction')
@receiver(post_save, sender='social.GroupMemberSettings')
def on_member_settings_saved(sender, instance, **kwargs):
    if hasattr(instance, 'membership'):
        publish_change(instance.membership.chat, user_id=instance.membership.user_id)
    else:
        publish_change(instance.chat, user_id=instance.user_id)
