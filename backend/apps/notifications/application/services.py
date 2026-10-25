from django.db import transaction
from django.utils import timezone
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notifications.infrastructure.models.notifications import Notification
from apps.users.infrastructure.models.users import User

logger = logging.getLogger(__name__)



TYPE_ICONS = {
    'like':             '❤️',
    'dislike':          '👎',
    'heart':            '💖',
    'comment':          '💬',
    'reply':            '↩️',
    'mention':          '@',
    'follow':           '👥',
    'repost':           '🔁',
    'group_invite':     '📨',
    'achievement':      '🏆',
    'contest':          '🏅',
    'contest_vote':     '🗳️',
    'contest_results':  '📊',
    'contest_win':      '👑',
    'reminder_episode': '⏰',
    'reminder_event':   '📅',
    'reminder_contest': '⏳',
    'system':           '⚙️',
    'warning':          '⚠️',
    'security':         '🔒',
}


class NotificationService:
    @staticmethod
    def should_send_notification(user: User, notification_type: str) -> bool:
        try:
            settings = getattr(user, 'notif_settings', None)
            if not settings:
                return True
            type_cfg = settings.type_settings.get(notification_type, {})
            return type_cfg.get('enabled', True)
        except Exception:
            return True


    @staticmethod
    def create_notification(
        user: User,
        notification_type: str,
        title: str,
        content: str,
        link: str = '',
        icon: str = '',
        content_object=None,
        send_ws: bool = True,
        dedupe_key: str = '',
        enable_push: bool = True,
        enable_sound: bool = True,
    ) -> 'Notification | None':
        if not NotificationService.should_send_notification(user, notification_type):
            return None

        icon = icon or TYPE_ICONS.get(notification_type, '🔔')

        kwargs = dict(
            user=user,
            type=notification_type,
            title=title,
            content=content,
            icon=icon,
            link=link,
            dedupe_key=dedupe_key,
            enable_push=enable_push,
            enable_sound=enable_sound,
        )
        if content_object is not None:
            from django.contrib.contenttypes.models import ContentType
            kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
            kwargs['object_id'] = content_object.pk

        if kwargs.get('dedupe_key'):
            existing = Notification.objects.filter(
                user=user, dedupe_key=kwargs['dedupe_key'], is_deleted=False
            ).first()
            if existing:
                return existing

        notification = Notification.objects.create(**kwargs)

        def _send():
            if send_ws:
                NotificationService._send_ws(notification)
            try:
                from apps.notifications.application.celery_tasks import send_push_for_notification
                if notification.enable_push:
                    send_push_for_notification.delay(notification.id)
            except Exception as exc:
                logger.warning('Push celery enqueue failed: %s', exc)

        transaction.on_commit(_send)
        return notification


    @staticmethod
    def _send_ws(notification: 'Notification'):
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            payload = {
                'type': 'notification_event',
                'action': 'notification',
                'notification': {
                    'id': notification.id,
                    'type': notification.type,
                    'title': notification.title,
                    'content': notification.content,
                    'icon': notification.icon,
                    'link': notification.link,
                    'is_read': notification.is_read,
                    'is_important': notification.is_important,
                    'created_at': notification.created_at.isoformat(),
                    'enable_push': notification.enable_push,
                    'enable_sound': notification.enable_sound,
                },
            }
            async_to_sync(channel_layer.group_send)(
                f'user_{notification.user_id}',
                payload,
            )
        except Exception as exc:
            logger.warning('WS notification send failed: %s', exc)


notification_service = NotificationService()
