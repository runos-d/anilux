import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=8)
def deliver_chat_event(event_id):
    from django.db import transaction
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from apps.social.infrastructure.models.conversation import ChatEvent
    from apps.social.application.conversations import event_envelope
    with transaction.atomic():
        event = ChatEvent.objects.select_for_update().filter(pk=event_id, delivered_at__isnull=True).first()
        if event is None:
            return
        envelope = event_envelope(event)
        frame = {'type': 'conversation_event', 'payload': envelope, 'recipients': event.recipients}
        layer = get_channel_layer()
        conversation_id = event.conversation_id or envelope.get('conversation_id')
        async_to_sync(layer.group_send)(f'conversation_{conversation_id}', frame)
        for user_id in event.recipients:
            async_to_sync(layer.group_send)(f'user_{user_id}', frame)
        event.delivered_at = timezone.now()
        event.save(update_fields=['delivered_at'])
        logger.info('chat.event.delivered event=%s conversation=%s recipients=%s age_seconds=%.3f',
                    event.pk, conversation_id, len(event.recipients), (event.delivered_at-event.created_at).total_seconds())


@shared_task
def retry_chat_outbox():
    from apps.social.infrastructure.models.conversation import ChatEvent
    for event_id in ChatEvent.objects.filter(delivered_at__isnull=True).order_by('id').values_list('id', flat=True)[:500]:
        deliver_chat_event.delay(event_id)


@shared_task(name='social.cleanup_expired_bans', max_retries=3, default_retry_delay=300, countdown=60)
def cleanup_expired_bans():
    from apps.social.infrastructure.models.social_chat import ChatBan
    count = ChatBan.objects.filter(
        until_date__lt=timezone.now(),
        until_date__isnull=False
    ).delete()[0]
    logger.info(f"cleanup_expired_bans: удалено {count} блокировок")
    return count


@shared_task(name='social.cleanup_expired_restrictions', max_retries=3, default_retry_delay=300, countdown=60)
def cleanup_expired_restrictions():
    from apps.social.infrastructure.models.social_chat import ChatRestriction
    count = ChatRestriction.objects.filter(
        until_date__lt=timezone.now(),
        until_date__isnull=False
    ).delete()[0]
    logger.info(f"cleanup_expired_restrictions: удалено {count} ограничений")
    return count


@shared_task(name='social.cleanup_expired_invite_links', max_retries=3, default_retry_delay=300, countdown=60)
def cleanup_expired_invite_links():
    from apps.social.infrastructure.models.social_chat import ChatInviteLink
    count = ChatInviteLink.objects.filter(
        expires_at__lt=timezone.now(),
        is_revoked=False
    ).update(is_revoked=True)
    logger.info(f"cleanup_expired_invite_links: отозвано {count} ссылок")
    return count


@shared_task(name='social.update_group_stats_cache', max_retries=3, default_retry_delay=300, countdown=60)
def update_group_stats_cache(chat_id: int):
    from apps.social.infrastructure.models.social_chat import GroupChatSettings
    from apps.social.infrastructure.models.social import Message as Msg
    try:
        gs, _ = GroupChatSettings.objects.get_or_create(chat_id=chat_id)
        gs.refresh_cache()
        logger.info(f"update_group_stats_cache: обновлён кэш для группы {chat_id}")
    except Exception as e:
        logger.error(f"update_group_stats_cache error: {e}")


@shared_task(name='social.send_scheduled_messages', max_retries=3, default_retry_delay=300, countdown=60)
def send_scheduled_messages():
    from django.db import transaction
    from rest_framework.exceptions import APIException
    from apps.social.infrastructure.models.social_chat import ScheduledMessage
    from apps.social.application.conversations import send_message
    ids = list(ScheduledMessage.objects.filter(status='scheduled', scheduled_at__lte=timezone.now())
               .order_by('scheduled_at').values_list('pk', flat=True)[:100])
    sent = 0
    for pk in ids:
        try:
            with transaction.atomic():
                job = ScheduledMessage.objects.select_for_update().get(pk=pk)
                if job.status != 'scheduled' or job.scheduled_at > timezone.now():
                    continue
                chat = job.chat or job.private_chat
                send_message(chat, job.sender, {'text': job.text, 'media': job.media, 'media_type': job.media_type,
                    'client_message_id': f'scheduled-{job.pk}-{int(job.scheduled_at.timestamp())}'[:36]})
                job.sent_at = timezone.now()
                if job.is_recurring and job.recurring_interval and job.recurring_interval > 0:
                    job.scheduled_at = max(job.scheduled_at, timezone.now()) + timedelta(seconds=job.recurring_interval)
                else:
                    job.status = 'sent'
                job.save(update_fields=['sent_at', 'status', 'scheduled_at'])
                sent += 1
        except APIException as exc:
            ScheduledMessage.objects.filter(pk=pk, status='scheduled').update(status='failed', error_message=str(exc.detail))
        except Exception:
            logger.exception('Scheduled message deferred: %s', pk)
    return sent


@shared_task(name='social.cleanup_old_messages')
def cleanup_old_messages(days: int = 365):
    from django.db import transaction
    from apps.social.infrastructure.models.social import Message, PrivateChat, GroupChat
    from apps.social.infrastructure.models.social_chat import MessagePin
    from apps.social.application import conversations as service
    if type(days) is not int or days < 1:
        raise ValueError('days must be a positive integer')
    cutoff = timezone.now() - timedelta(days=days)
    scope = Message.objects.filter(created_at__lt=cutoff, is_pinned=False, is_deleted=False)
    chats = list(scope.order_by().values_list('private_chat_id', 'chat_id').distinct())
    count = 0
    for private_id, group_id in chats:
        model, pk = (PrivateChat, private_id) if private_id else (GroupChat, group_id)
        while True:
            with transaction.atomic():
                chat = model.objects.select_for_update().filter(pk=pk).first()
                if chat is None:
                    break
                messages = list(scope.filter(service.message_scope(chat)).select_for_update().order_by('seq')[:200])
                if not messages:
                    break
                MessagePin.objects.filter(message_id__in=[m.pk for m in messages]).delete()
                for message in messages:
                    message.is_deleted, message.deleted_at = True, timezone.now()
                    message.version += 1
                    message.save(update_fields=['is_deleted', 'deleted_at', 'version'])
                    service.record_event(chat, 'message_deleted', {'message_id': message.pk,
                        'version': message.version, 'message': service.serialize_message(message)})
                last = Message.objects.filter(service.message_scope(chat), is_deleted=False).order_by('-seq').first()
                model.objects.filter(pk=pk).update(last_message_at=last.created_at if last else None)
                count += len(messages)
    logger.info('cleanup_old_messages: expired %s messages', count)
    return count
