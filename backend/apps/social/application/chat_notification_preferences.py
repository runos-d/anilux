from django.utils import timezone
from apps.social.infrastructure.models.social import PrivateChat
from apps.social.infrastructure.models.social_chat import PrivateChatSettings, GroupMemberSettings


def notification_preferences(chats, user):
    private_ids = [chat.pk for chat in chats if isinstance(chat, PrivateChat)]
    group_ids = [chat.pk for chat in chats if not isinstance(chat, PrivateChat)]
    private = {row['chat_id']: row for row in PrivateChatSettings.objects.filter(chat_id__in=private_ids, user=user)
               .values('chat_id', 'notifications_enabled', 'muted_until')}
    group = {row['membership__chat_id']: row for row in GroupMemberSettings.objects.filter(
        membership__chat_id__in=group_ids, membership__user=user)
        .values('membership__chat_id', 'notifications_enabled', 'muted_until')}
    result = {}
    now = timezone.now()
    for chat in chats:
        is_private = isinstance(chat, PrivateChat)
        settings = (private if is_private else group).get(chat.pk)
        if settings:
            enabled, until = settings['notifications_enabled'], settings['muted_until']
        elif is_private:
            prefix = 'user1' if chat.user1_id == user.pk else 'user2'
            enabled, until = getattr(chat, prefix + '_notifications'), getattr(chat, prefix + '_muted_until')
        else:
            enabled, until = True, None
        result[('private' if is_private else 'group', chat.pk)] = bool(enabled and (not until or until <= now))
    return result
