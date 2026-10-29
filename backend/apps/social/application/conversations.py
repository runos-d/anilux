from apps.social.infrastructure.models.social import Post
import hashlib
import json
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.social.infrastructure.models.social import (
    PrivateChat, GroupChat, ChatMember, Message, MessageReadStatus,
)
from apps.social.infrastructure.models.conversation import Conversation, ChatEvent, ConversationUserState

logger = logging.getLogger(__name__)


def chat_kind(chat):
    return 'private' if isinstance(chat, PrivateChat) else 'group'


def resolve_chat(identifier, user, kind=None, *, write=False):
    try:
        identifier = int(identifier)
    except (TypeError, ValueError):
        raise ValidationError({'chat_id': 'Некорректный идентификатор чата'})
    if identifier < 1 or identifier > 2**53 - 1:
        raise ValidationError({'chat_id': 'Некорректный идентификатор чата'})
    if kind not in (None, '', 'private', 'group'):
        raise ValidationError({'chat_type': 'Неизвестный тип чата'})
    models = [PrivateChat, GroupChat] if not kind else [PrivateChat if kind == 'private' else GroupChat]
    candidates = [c for model in models for c in model.objects.filter(public_id=identifier)]
    if not candidates:
        candidates = [c for model in models for c in model.objects.filter(Q(pk=identifier) | Q(code=str(identifier)))]
    if len(candidates) != 1:
        if candidates:
            raise ValidationError({'chat_type': 'Укажите тип чата: идентификатор неоднозначен'})
        raise NotFound('Чат не найден')
    chat = candidates[0]
    check_access(chat, user, write=write)
    return chat


def check_access(chat, user, *, write=False, media=False, text='', rate_limit=False):
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Требуется авторизация')
    if isinstance(chat, PrivateChat):
        if user.pk not in (chat.user1_id, chat.user2_id):
            raise NotFound('Чат не найден')
        if write:
            from apps.social.infrastructure.models.social_chat import PrivateChatSettings
            if (chat.user1_blocked or chat.user2_blocked or
                    PrivateChatSettings.objects.filter(chat=chat, is_blocked=True).exists()):
                raise PermissionDenied('Чат заблокирован')
        return
    from apps.social.infrastructure.models.social_chat import ChatBan, ChatRestriction
    active = Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
    member = ChatMember.objects.select_related('role').filter(chat=chat, user=user).first()
    if (member and member.is_banned) or ChatBan.objects.filter(chat=chat, user=user).filter(active).exists():
        raise PermissionDenied('Вы заблокированы в этом чате')
    if not member and (write or not chat.is_public):
        raise PermissionDenied('Сначала вступите в чат')
    if not write:
        return
    from .chat_services import PermissionChecker
    checker = PermissionChecker(user, chat)
    checker._membership, checker._ban = member, False
    if not checker.has_permission('can_post_messages').allowed:
        raise PermissionDenied('Отправка сообщений ограничена')
    restrictions = set(ChatRestriction.objects.filter(chat=chat, user=user).filter(active)
                       .values_list('restriction_type', flat=True))
    if not checker._is_owner() and ('read_only' in restrictions or (media and ('no_media' in restrictions or not member.can_send_media or not chat.can_send_media))):
        raise PermissionDenied('Отправка ограничена настройками чата')
    if not checker._is_owner() and 'no_links' in restrictions and ('http://' in text or 'https://' in text):
        raise PermissionDenied('Отправка ссылок ограничена')
    if rate_limit:
        from apps.social.infrastructure.models.social_chat import ChatSlowMode
        settings = ChatSlowMode.objects.filter(chat=chat).first()
        delay = chat.slow_mode_delay if not member.is_admin and not member.is_owner else 0
        if settings:
            exempt = (checker._is_owner() or
                      settings.exempt_admins and (member.is_admin or member.role and member.role.level >= 2) or
                      settings.exempt_moderators and member.role and member.role.level == 1)
            delay = settings.custom_delays.get(str(user.pk), settings.delay) if settings.enabled and not exempt else 0
        individual_delays = ChatRestriction.objects.filter(chat=chat, user=user, restriction_type='slow_mode').filter(active).values_list('slow_mode_delay', flat=True)
        delay = max([int(delay or 0)] + [d for d in individual_delays if d is not None and d > 0])
        if delay:
            last = Message.objects.filter(chat=chat, sender=user).order_by('-created_at').first()
            if last and last.created_at > timezone.now() - timedelta(seconds=int(delay)):
                raise ValidationError({'text': 'Дождитесь окончания медленного режима'})


def get_conversation(chat, *, lock=False):
    key = 'private_chat' if isinstance(chat, PrivateChat) else 'group_chat'
    conversation, _ = Conversation.objects.get_or_create(**{key: chat})
    if lock:
        conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    return conversation


def message_scope(chat):
    return Q(private_chat_id=chat.pk) if isinstance(chat, PrivateChat) else Q(chat_id=chat.pk)


def visible_messages(chat, user):
    check_access(chat, user)
    qs = Message.objects.filter(message_scope(chat), is_deleted=False)
    state = ConversationUserState.objects.filter(conversation=get_conversation(chat), user=user).first()
    if state:
        qs = qs.filter(seq__gt=state.cleared_through_seq)
    if isinstance(chat, GroupChat) and not chat.history_visible:
        member = ChatMember.objects.filter(chat=chat, user=user).first()
        if member:
            qs = qs.filter(created_at__gte=member.joined_at)
        else:
            return qs.none()
    return qs


def unread_count(chat, user):
    return visible_messages(chat, user).exclude(sender=user).exclude(read_statuses__user=user).count()


def participant_ids(chat):
    if isinstance(chat, PrivateChat):
        return [chat.user1_id, chat.user2_id]
    from apps.social.infrastructure.models.social_chat import ChatBan
    banned = ChatBan.objects.filter(chat=chat).filter(Q(until_date__isnull=True) | Q(until_date__gt=timezone.now()))
    return list(ChatMember.objects.filter(chat=chat, is_banned=False).exclude(user_id__in=banned.values('user_id')).values_list('user_id', flat=True))


def room(chat):
    return f'conversation_{get_conversation(chat).pk}'


def serialize_message(message, user=None):
    if message.is_deleted:
        return {'id': message.pk, 'seq': message.seq, 'version': message.version,
                'is_deleted': True, 'created_at': message.created_at.isoformat()}
    from apps.social.presentation.serializers.social_serializers import MessageSerializer
    from types import SimpleNamespace
    return dict(MessageSerializer(message, context={'request': SimpleNamespace(user=user, build_absolute_uri=lambda url: url)} if user else {}).data)


def serialize_messages(messages, user=None):
    """Share DRF fields and viewer context across a history page."""
    from apps.social.presentation.serializers.social_serializers import MessageSerializer
    from types import SimpleNamespace
    context = {'request': SimpleNamespace(user=user, build_absolute_uri=lambda url: url)} if user else {}
    return list(MessageSerializer(messages, many=True, context=context).data)


@transaction.atomic
def record_event(chat, kind, payload, recipients=None):
    conversation = get_conversation(chat, lock=True)
    conversation.event_seq += 1
    conversation.save(update_fields=['event_seq'])
    payload = json.loads(json.dumps(payload, default=str))
    payload.update(chat_id=chat.public_id, chat_type=chat_kind(chat), conversation_id=conversation.pk)
    event = ChatEvent.objects.create(conversation=conversation, sequence=conversation.event_seq,
                                    kind=kind, payload=payload,
                                    recipients=participant_ids(chat) if recipients is None else recipients)
    transaction.on_commit(lambda: enqueue_event(event.pk), robust=True)
    return event


def enqueue_event(event_id):
    from apps.social.application.tasks_chat import deliver_chat_event
    try:
        deliver_chat_event.delay(event_id)
    except Exception:
        logger.warning('Chat outbox delivery deferred: event=%s', event_id)


def event_envelope(event):
    return dict(event.payload, action=event.kind, event_id=event.pk,
                sequence=event.sequence, protocol_version=2)


def event_for_user(event, user):
    if user.pk not in event.recipients:
        return None
    payload = event_envelope(event)
    if event.kind in ('chat_deleted', 'access_revoked'):
        return payload
    if event.conversation_id is None:
        return None
    chat = event.conversation.chat
    try:
        check_access(chat, user)
    except (PermissionDenied, NotFound):
        return None
    if event.kind in ('unread_updated', 'message_deleted'):
        payload['unread_count'] = unread_count(chat, user)
    if event.kind == 'chat_cleared' and not payload.get('for_user'):
        if ChatEvent.objects.filter(conversation_id=event.conversation_id, kind='chat_restored', sequence__gt=event.sequence).exists():
            return None
    if event.kind == 'message_deleted':
        current = Message.objects.filter(pk=payload.get('message_id')).first()
        if current and not current.is_deleted:
            return None
    message = payload.get('message')
    if message and event.kind != 'message_deleted':
        current = visible_messages(chat, user).filter(pk=message['id']).first()
        if current is None:
            return None
        payload['message'] = serialize_message(current, user)
        if event.kind == 'new_message':
            payload['unread_count'] = unread_count(chat, user)
    return payload


def user_can_receive(payload, user_id, *, user=None):
    if payload.get('action') in ('chat_deleted', 'access_revoked'):
        return True
    conv = Conversation.objects.select_related('private_chat', 'group_chat').filter(pk=payload.get('conversation_id')).first()
    if conv is None:
        return False
    from apps.users.infrastructure.models.users import User
    user = user if user is not None else User.objects.filter(pk=user_id, is_active=True).first()
    if user is None or user.pk != user_id or not user.is_active:
        return False
    try:
        check_access(conv.chat, user)
        if payload.get('action') in ('new_message', 'message_edited'):
            message_id = (payload.get('message') or {}).get('id')
            return visible_messages(conv.chat, user).filter(pk=message_id).exists()
        return True
    except (PermissionDenied, NotFound):
        return False


def live_event_for_user(payload, user_id, *, user=None):
    from apps.users.infrastructure.models.users import User
    # Consumers may pass the fresh account returned by their current auth batch.
    user = user if user is not None else User.objects.filter(pk=user_id, is_active=True).first()
    if user is None or user.pk != user_id or not user.is_active:
        return None
    if payload.get('event_id'):
        event = ChatEvent.objects.select_related('conversation__private_chat', 'conversation__group_chat').filter(pk=payload['event_id']).first()
        return event_for_user(event, user) if event else None
    return payload if user_can_receive(payload, user_id, user=user) else None


def validate_topic(chat, topic_id):
    if topic_id in (None, '', 'main', '0', 0):
        return None
    from apps.social.infrastructure.models.social_chat import ChatTopic
    try:
        topic_id = int(topic_id)
    except (TypeError, ValueError):
        raise ValidationError({'topic_id': 'Некорректный идентификатор темы'})
    if isinstance(chat, PrivateChat) or not ChatTopic.objects.filter(chat=chat, pk=topic_id).exists():
        raise ValidationError({'topic_id': 'Тема не принадлежит этому чату'})
    return int(topic_id)


@transaction.atomic
def send_message(chat, user, values, *, attachments=None, fingerprint=None):
    chat = type(chat).objects.select_for_update().get(pk=chat.pk)
    conversation = get_conversation(chat, lock=True)
    values = dict(values)
    key = values.get('client_message_id') or None
    if key and (not isinstance(key, str) or len(key) > 36):
        raise ValidationError({'client_message_id': 'Максимум 36 символов'})
    topic = validate_topic(chat, values.pop('topic_id', None))
    raw_text = values.get('text') or ''
    if not isinstance(raw_text, str):
        raise ValidationError({'text': 'Ожидается строка'})
    text = raw_text.strip()
    if len(text) > 20000:
        raise ValidationError({'text': 'Максимум 20000 символов'})
    if not text and not attachments and not any(values.get(k) for k in ('media', 'shared_post', 'shared_anime', 'shared_playlist', 'shared_shorts')):
        raise ValidationError({'text': 'Добавьте текст или вложение'})
    if fingerprint is None:
        fingerprint = hashlib.sha256(json.dumps({'text': text, 'topic': topic,
            'reply': getattr(values.get('reply_to'), 'pk', None), 'files': [], 'cards': [],
            'shared': {k: getattr(values.get(k), 'pk', None) for k in ('shared_post', 'shared_anime', 'shared_playlist', 'shared_shorts')}}, sort_keys=True).encode()).hexdigest()
    existing = Message.objects.filter(conversation=conversation, sender=user, client_message_id=key).first() if key else None
    if existing:
        check_access(chat, user)
        if existing.command_fingerprint != fingerprint:
            raise ValidationError({'client_message_id': 'Ключ отправки уже использован для другого сообщения'})
        return existing, False
    check_access(chat, user, write=True, media=bool(attachments or values.get('media')), text=text, rate_limit=True)
    for k in ('shared_post', 'shared_anime', 'shared_playlist', 'shared_shorts'):
        if values.get(k):
            check_shareable(values[k], user)
    reply = values.get('reply_to')
    if reply and not visible_messages(chat, user).filter(pk=reply.pk).exists():
        raise ValidationError({'reply_to': 'Сообщение недоступно в этом чате'})
    allowed = {'text', 'media', 'media_type', 'reply_to', 'shared_post', 'shared_anime',
               'shared_playlist', 'shared_shorts', 'location_latitude', 'location_longitude', 'location_name', 'forwarded_from'}
    data = {k: v for k, v in values.items() if k in allowed}
    data.update(text=text, sender=user, topic_id=topic, client_message_id=key,
                command_fingerprint=fingerprint, conversation=conversation)
    data['private_chat' if isinstance(chat, PrivateChat) else 'chat'] = chat
    message = Message.objects.create(**data)
    if attachments:
        attachments(message)
    type(chat).objects.filter(pk=chat.pk).update(last_message_at=message.created_at)
    ConversationUserState.objects.filter(conversation=conversation, hidden=True).update(hidden=False)
    if isinstance(chat, PrivateChat):
        chat.settings.filter(is_hidden=True).update(is_hidden=False)
    record_event(chat, 'new_message', {'message': serialize_message(message)})
    return message, True


def check_shareable(obj, user):
    from apps.anime.models import Excerpt
    if isinstance(obj, Excerpt):
        if not obj.shared or not obj.anime.is_available:
            raise PermissionDenied('Отрывок недоступен для пересылки')
        return
    if isinstance(obj, Post):
        from apps.social.application.post_access import readable_posts
        if not readable_posts(Post.objects.filter(pk=obj.pk), user).exists():
            raise PermissionDenied('Пост недоступен для пересылки')
        return
    if getattr(obj, 'is_deleted', False):
        raise PermissionDenied('Вложение удалено')
    owner = getattr(obj, 'user_id', getattr(obj, 'author_id', getattr(obj, 'owner_id', None)))
    if user and owner == user.pk:
        return
    if (hasattr(obj, 'is_public') and not obj.is_public) or getattr(obj, 'visibility', 'public') != 'public':
        raise PermissionDenied('Вложение недоступно для пересылки')


@transaction.atomic
def mark_read(chat, user, message_ids=None):
    chat = type(chat).objects.select_for_update().get(pk=chat.pk)
    qs = visible_messages(chat, user).exclude(sender=user)
    if message_ids is not None:
        if not isinstance(message_ids, list) or len(message_ids) > 1000 or any(type(i) is not int or i < 1 for i in message_ids):
            raise ValidationError({'message_ids': 'Ожидается список до 1000 ID сообщений'})
        qs = qs.filter(pk__in=message_ids)
    ids = list(qs.exclude(read_statuses__user=user).values_list('pk', flat=True))
    MessageReadStatus.objects.bulk_create([MessageReadStatus(message_id=i, user=user) for i in ids], ignore_conflicts=True)
    if ids:
        record_event(chat, 'messages_read', {'user_id': user.pk, 'message_ids': ids, 'read_at': timezone.now().isoformat()})
    count = unread_count(chat, user)
    record_event(chat, 'unread_updated', {'user_id': user.pk, 'unread_count': count}, recipients=[user.pk])
    return {'success': True, 'message_ids': ids, 'unread_count': count}


@transaction.atomic
def change_message(message_id, user, *, text=None, delete=False, version=None):
    original = Message.objects.select_related('chat', 'private_chat').filter(pk=message_id).first()
    if original is None:
        raise NotFound('Сообщение не найдено')
    chat = original.parent_chat
    chat = type(chat).objects.select_for_update().get(pk=chat.pk)
    check_access(chat, user)
    message = Message.objects.select_for_update().get(pk=message_id)
    from apps.social.application.chat_services import can_delete_message
    if delete:
        if not can_delete_message(user, message):
            raise PermissionDenied('Недостаточно прав для удаления')
        if message.is_deleted:
            return message
        message.is_deleted, message.deleted_at, message.deleted_by = True, timezone.now(), user
        message.is_pinned = False
        from apps.social.infrastructure.models.social_chat import MessagePin
        MessagePin.objects.filter(message=message).delete()
    else:
        if not message.can_edit(user):
            raise PermissionDenied('Сообщение нельзя редактировать')
        try:
            version = int(version) if version is not None else None
        except (TypeError, ValueError):
            raise ValidationError({'version': 'Некорректная версия сообщения'})
        if version is not None and version != message.version:
            from rest_framework.exceptions import APIException
            exc = APIException('Сообщение уже изменено. Обновите его и повторите правку.')
            exc.status_code = 409
            raise exc
        if not isinstance(text, str):
            raise ValidationError({'text': 'Ожидается строка'})
        text = text.strip()
        if not text or len(text) > 20000:
            raise ValidationError({'text': 'Укажите текст длиной от 1 до 20000 символов'})
        message.text, message.is_edited, message.edited_at = text, True, timezone.now()
    message.version += 1
    message.save()
    last = Message.objects.filter(message_scope(chat), is_deleted=False).order_by('-seq').first()
    type(chat).objects.filter(pk=chat.pk).update(last_message_at=last.created_at if last else None)
    record_event(chat, 'message_deleted' if delete else 'message_edited',
                 {'message_id': message.pk, 'version': message.version, 'message': serialize_message(message)})
    return message


def accessible_message(message_id, user):
    message = Message.objects.select_related('chat', 'private_chat', 'sender').filter(pk=message_id).first()
    if not message or not visible_messages(message.parent_chat, user).filter(pk=message_id).exists():
        raise NotFound('Сообщение не найдено')
    return message


@transaction.atomic
def react(message_id, user, emoji, active=None):
    if not isinstance(emoji, str) or not emoji.strip() or len(emoji) > 50:
        raise ValidationError({'emoji': 'Укажите реакцию длиной до 50 символов'})
    original = accessible_message(message_id, user)
    chat = type(original.parent_chat).objects.select_for_update().get(pk=original.parent_chat.pk)
    check_access(chat, user)
    if isinstance(chat, GroupChat):
        member = ChatMember.objects.filter(chat=chat, user=user).first()
        if not member or not member.can_add_reactions:
            raise PermissionDenied('Добавление реакций ограничено')
    message = Message.objects.select_for_update().get(pk=message_id)
    from apps.social.infrastructure.models.social_chat import MessageReaction
    if active is not None and type(active) is not bool:
        raise ValidationError({'active': 'Ожидается логическое значение'})
    user_reactions = MessageReaction.objects.select_for_update().filter(message=message, user=user).order_by('created_at', 'pk')
    current = user_reactions.first()
    if active is False:
        user_reactions.filter(emoji=emoji).delete()
        status = 'removed'
    elif current and current.emoji == emoji:
        user_reactions.exclude(pk=current.pk).delete()
        status = 'unchanged'
    elif current:
        user_reactions.exclude(pk=current.pk).delete()
        current.emoji = emoji
        current.save(update_fields=['emoji'])
        status = 'replaced'
    else:
        MessageReaction.objects.create(message=message, user=user, emoji=emoji)
        status = 'added'
    reactions = {}
    for symbol, uid in MessageReaction.objects.filter(message=message).values_list('emoji', 'user_id'):
        reactions.setdefault(symbol, []).append(uid)
    message.reactions = reactions
    message.version += 1
    message.save(update_fields=['reactions', 'version'])
    record_event(chat, 'message_edited', {'message': serialize_message(message)})
    return {'status': status, 'emoji': emoji, 'reactions': reactions}


@transaction.atomic
def pin(message_id, user, enabled):
    original = accessible_message(message_id, user)
    chat = type(original.parent_chat).objects.select_for_update().get(pk=original.parent_chat.pk)
    check_access(chat, user)
    if isinstance(chat, GroupChat):
        from apps.social.application.chat_services import PermissionChecker
        if not PermissionChecker(user, chat).has_permission('can_pin_messages').allowed:
            raise PermissionDenied('Недостаточно прав для закрепления')
    message = Message.objects.select_for_update().get(pk=message_id)
    from apps.social.infrastructure.models.social_chat import MessagePin
    if enabled:
        MessagePin.objects.get_or_create(message=message, defaults={'chat': message.chat,
            'private_chat': message.private_chat, 'pinned_by': user})
    else:
        MessagePin.objects.filter(message=message).delete()
    message.is_pinned = enabled
    message.pinned_by = user if enabled else None
    message.pinned_at = timezone.now() if enabled else None
    message.version += 1
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at', 'version'])
    record_event(chat, 'message_edited', {'message': serialize_message(message)})
    return message


@transaction.atomic
def clear_history(chat, user, *, for_all=False, hide=False):
    chat = type(chat).objects.select_for_update().get(pk=chat.pk)
    check_access(chat, user)
    conversation = get_conversation(chat, lock=True)
    if for_all:
        if isinstance(chat, GroupChat) and chat.created_by_id != user.pk and not user.is_staff:
            raise PermissionDenied('Очистить историю группы может только владелец')
        count = Message.objects.filter(message_scope(chat), is_deleted=False).count()
        Message.objects.filter(message_scope(chat), is_deleted=False).update(is_deleted=True,
            deleted_at=timezone.now(), deleted_by=user, is_pinned=False, version=F('version') + 1)
        from apps.social.infrastructure.models.social_chat import MessagePin
        MessagePin.objects.filter(message__conversation=conversation).delete()
        type(chat).objects.filter(pk=chat.pk).update(last_message_at=None)
        record_event(chat, 'chat_cleared', {'cleared_through_seq': conversation.next_message_seq})
    else:
        count = visible_messages(chat, user).count()
        if isinstance(chat, PrivateChat) and hide:
            participant_ids = [chat.user1_id, chat.user2_id]
            for participant_id in participant_ids:
                state, _ = ConversationUserState.objects.get_or_create(
                    conversation=conversation, user_id=participant_id)
                state.cleared_through_seq = conversation.next_message_seq
                state.hidden = True
                state.save(update_fields=['cleared_through_seq', 'hidden'])
            chat.settings.filter(user_id__in=participant_ids).update(is_hidden=True)
            record_event(chat, 'chat_deleted', {
                'cleared_through_seq': conversation.next_message_seq,
                'deleted_by': user.pk,
            }, recipients=participant_ids)
        else:
            state, _ = ConversationUserState.objects.get_or_create(conversation=conversation, user=user)
            state.cleared_through_seq = conversation.next_message_seq
            state.hidden = hide
            if isinstance(chat, PrivateChat):
                chat.settings.filter(user=user).update(is_hidden=hide)
            state.save(update_fields=['cleared_through_seq', 'hidden'])
            record_event(chat, 'chat_deleted' if hide else 'chat_cleared',
                         {'cleared_through_seq': state.cleared_through_seq, 'for_user': user.pk}, recipients=[user.pk])
    return count


@transaction.atomic
def delete_group(chat, user):
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    check_access(chat, user)
    if chat.discussion_type in ('anime', 'franchise') and not user.is_staff:
        raise PermissionDenied('Обсуждение может удалить только администратор сайта')
    if chat.created_by_id != user.pk and not user.is_staff:
        raise PermissionDenied('Удалить группу может только владелец')
    event = record_event(chat, 'chat_deleted', {})
    ChatEvent.objects.filter(conversation=event.conversation).exclude(pk=event.pk).delete()
    chat.delete()


@transaction.atomic
def leave_group(chat, user):
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    member = ChatMember.objects.filter(chat=chat, user=user).first()
    if member is None:
        return
    if member.is_owner:
        raise PermissionDenied('Сначала передайте владение группой')
    member.delete()
    record_event(chat, 'access_revoked', {'user_id': user.pk}, recipients=[user.pk])
    record_event(chat, 'member_updated', {'user_id': user.pk})


@transaction.atomic
def join_invite(token, user):
    from apps.social.infrastructure.models.social_chat import ChatInviteLink, ChatJoinRequest
    invite = ChatInviteLink.objects.filter(invite_link=token).first()
    if invite is None:
        raise NotFound('Ссылка не найдена')
    chat = GroupChat.objects.select_for_update().get(pk=invite.chat_id)
    invite = ChatInviteLink.objects.select_for_update().get(pk=invite.pk)
    check_access_for_join(chat, user)
    if invite.target_user_id and invite.target_user_id != user.pk:
        raise PermissionDenied('Приглашение предназначено другому пользователю')
    if ChatMember.objects.filter(chat=chat, user=user).exists():
        return {'status': 'joined', 'chat_id': chat.public_id, 'chat_name': chat.name}
    if not invite.is_valid:
        raise ValidationError('Ссылка недействительна')
    if chat.members.count() >= chat.max_members:
        raise ValidationError('Чат переполнен')
    role = invite.auto_assign_role
    if role and (role.chat_id != chat.pk or role.level >= 3):
        raise ValidationError('Некорректная роль приглашения')
    ChatMember.objects.create(chat=chat, user=user, role=role)
    ChatJoinRequest.objects.filter(chat=chat, user=user, status='pending').update(
        status='approved', reviewed_at=timezone.now())
    invite.usage_count += 1
    invite.save(update_fields=['usage_count'])
    record_event(chat, 'chat_created', {}, recipients=[user.pk])
    return {'status': 'joined', 'chat_id': chat.public_id, 'chat_name': chat.name}


def check_access_for_join(chat, user):
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Требуется активный аккаунт')
    from apps.social.infrastructure.models.social_chat import ChatBan
    if ChatMember.objects.filter(chat=chat, user=user, is_banned=True).exists() or ChatBan.objects.filter(
        chat=chat, user=user).filter(Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())).exists():
        raise PermissionDenied('Вы заблокированы в этом чате')


@transaction.atomic
def join_group(chat, user):
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    check_access_for_join(chat, user)
    existing = ChatMember.objects.filter(chat=chat, user=user).first()
    if existing:
        return existing, False
    if not chat.is_public:
        raise PermissionDenied('Для закрытого чата нужна ссылка приглашения')
    if chat.members.count() >= chat.max_members:
        raise ValidationError('Чат переполнен')
    member = ChatMember.objects.create(chat=chat, user=user)
    record_event(chat, 'chat_created', {}, recipients=[user.pk])
    return member, True


@transaction.atomic
def review_join(request_id, user, *, approve):
    from apps.social.infrastructure.models.social_chat import ChatJoinRequest, ChatInviteLink
    original = ChatJoinRequest.objects.get(pk=request_id)
    chat = GroupChat.objects.select_for_update().get(pk=original.chat_id)
    check_access(chat, user)
    from apps.social.application.chat_services import PermissionChecker
    if not PermissionChecker(user, chat).has_permission('can_invite_users').allowed:
        raise PermissionDenied('Недостаточно прав для рассмотрения заявки')
    jr = ChatJoinRequest.objects.select_for_update().get(pk=request_id)
    target_status = 'approved' if approve else 'rejected'
    if jr.status == target_status:
        return jr
    if jr.status != 'pending':
        raise ValidationError('Заявка уже рассмотрена')
    if approve:
        check_access_for_join(chat, jr.user)
        if not ChatMember.objects.filter(chat=chat, user=jr.user).exists():
            if chat.members.count() >= chat.max_members:
                raise ValidationError('Чат переполнен')
            invite = ChatInviteLink.objects.select_for_update().get(pk=jr.invite_id) if jr.invite_id else None
            if invite and (not invite.is_valid or (invite.target_user_id and invite.target_user_id != jr.user_id)):
                raise ValidationError('Приглашение больше недействительно')
            role = invite.auto_assign_role if invite else None
            if role and (role.chat_id != chat.pk or role.level >= 3):
                raise ValidationError('Некорректная роль приглашения')
            ChatMember.objects.create(chat=chat, user=jr.user, role=role)
            if invite:
                invite.usage_count += 1
                invite.save(update_fields=['usage_count'])
            record_event(chat, 'chat_created', {}, recipients=[jr.user_id])
    jr.status, jr.reviewed_by, jr.reviewed_at = target_status, user, timezone.now()
    jr.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
    return jr



MAX_MESSAGE_FILE_BYTES = 250 * 1024 * 1024


def validate_message_file_size(files, existing_bytes=0):
    if existing_bytes + sum(file.size for file in files) > MAX_MESSAGE_FILE_BYTES:
        raise ValidationError({'files': 'Общий размер файлов в сообщении не должен превышать 250 МБ'})


def validate_upload(file):
    if file is None:
        raise ValidationError({'file': 'Добавьте файл'})
    validate_message_file_size([file])
    mime = file.content_type or 'application/octet-stream'
    if mime.startswith('image/'):
        from PIL import Image
        try:
            Image.open(file).verify()
            file.seek(0)
        except Exception:
            raise ValidationError({'file': 'Повреждённое изображение'})
    return 'image' if mime.startswith('image/') else 'video' if mime.startswith('video/') else 'audio' if mime.startswith('audio/') else 'file'


@transaction.atomic
def add_attachment(message_id, user, file):
    original = accessible_message(message_id, user)
    chat = type(original.parent_chat).objects.select_for_update().get(pk=original.parent_chat.pk)
    check_access(chat, user, write=True, media=True)
    message = Message.objects.select_for_update().get(pk=message_id)
    if not message.can_edit(user):
        raise PermissionDenied('Вложения может менять только автор доступного для редактирования сообщения')
    from apps.social.infrastructure.models.social import Attachment
    existing_bytes = sum(attachment.file_size or (attachment.file.size if attachment.file else 0)
                         for attachment in message.attachments.all() if attachment.file)
    if message.media:
        existing_bytes += message.media.size
    validate_message_file_size([file], existing_bytes)
    kind = validate_upload(file)
    attachment = Attachment(message=message, type=kind, file=file,
                            file_name=file.name, file_size=file.size, mime_type=file.content_type or 'application/octet-stream')
    try:
        attachment.save()
        message.version += 1
        message.save(update_fields=['version'])
        record_event(chat, 'message_edited', {'message': serialize_message(message)})
    except Exception:
        if attachment.file and attachment.file._committed:
            attachment.file.delete(save=False)
        raise
    return attachment


def require_permission(chat, user, permission, *, target=None, action=None):
    from .chat_services import PermissionChecker
    check_access(chat, user)
    checker = PermissionChecker(user, chat)
    result = checker.can_perform_action(action, target) if action else checker.has_permission(permission)
    if not result.allowed:
        raise PermissionDenied(result.reason)
    return checker


def validate_role_grant(chat, user, role):
    from .chat_services import PermissionChecker
    if role is None:
        return
    if role.chat_id != chat.pk or role.level >= 3:
        raise ValidationError({'role_id': 'Роль должна принадлежать этому чату; владение передаётся отдельно'})
    checker = PermissionChecker(user, chat)
    if checker._is_owner():
        return
    require_permission(chat, user, 'can_promote_members')
    if role.level >= checker._get_role_level():
        raise PermissionDenied('Нельзя назначить равную или более высокую роль')
    for field in role._meta.fields:
        if field.name.startswith('can_') and getattr(role, field.name) and not checker.has_permission(field.name).allowed:
            raise PermissionDenied('Нельзя передать право, которым вы не обладаете')


def member_ids(value):
    if not isinstance(value, list) or len(value) > 500 or any(type(i) is not int or i < 1 for i in value):
        raise ValidationError({'user_ids': 'Ожидается список до 500 ID пользователей'})
    return sorted(set(value))


@transaction.atomic
def request_join(chat, user, values):
    from apps.social.infrastructure.models.social_chat import ChatJoinRequest
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    check_access_for_join(chat, user)
    if not chat.is_public:
        raise PermissionDenied('Для закрытого чата нужна ссылка приглашения')
    if ChatMember.objects.filter(chat=chat, user=user).exists():
        raise ValidationError('Вы уже участник')
    if chat.members.count() >= chat.max_members:
        raise ValidationError('Чат переполнен')
    jr, created = ChatJoinRequest.objects.get_or_create(chat=chat, user=user, defaults=values)
    if not created and jr.status != 'pending':
        jr.message, jr.answers = values.get('message', ''), values.get('answers', {})
        jr.status, jr.reviewed_by, jr.reviewed_at, jr.invite = 'pending', None, None, None
        jr.save()
    return jr
