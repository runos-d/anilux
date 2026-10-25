from celery import shared_task
import logging
from apps.notifications.infrastructure.models.notifications import Notification
from django.conf import settings
from django.utils import timezone
import json
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


@shared_task(name='notifications.process_episode_events')
def process_episode_events():
    from .episode_events import process_subscriptions, process_reminders
    from .episode_verification import queue_due_verifications
    queue_due_verifications()
    return {'subscriptions': process_subscriptions(), 'reminders': len(process_reminders())}


@shared_task(name='notifications.verify_calendar_episode', time_limit=45, soft_time_limit=40)
def verify_calendar_episode(shikimori_id):
    from .episode_verification import verify_title
    return verify_title(shikimori_id)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_push_for_notification(self, notification_id):
    from pywebpush import webpush, WebPushException
    from apps.notifications.infrastructure.models.notifications import PushSubscription
    from apps.notifications.presentation.views.push_views import valid_endpoint
    n = Notification.objects.select_related('user').filter(id=notification_id, is_deleted=False, is_read=False).first()
    if not n:
        return {'skipped': 'missing_or_read'}
    prefs = getattr(n.user, 'notif_settings', None)
    type_cfg = prefs.type_settings.get(n.type, {}) if prefs else {}
    if not n.enable_push or (prefs and not prefs.push_enabled) or type_cfg.get('push', True) is False or type_cfg.get('enabled', True) is False:
        return {'skipped': 'disabled'}
    if prefs and prefs.dnd_enabled and prefs.dnd_start and prefs.dnd_end:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            profile = getattr(n.user, 'profile_settings', None)
            local_zone = ZoneInfo(getattr(profile, 'timezone', settings.TIME_ZONE))
        except (ZoneInfoNotFoundError, ValueError):
            local_zone = timezone.get_default_timezone()
        now = timezone.localtime(timezone.now(), local_zone).time()
        start, end = prefs.dnd_start, prefs.dnd_end
        if (start <= end and start <= now <= end) or (start > end and (now >= start or now <= end)):
            return {'skipped': 'dnd'}
    if not (settings.WEB_PUSH_PUBLIC_KEY and settings.WEB_PUSH_PRIVATE_KEY and settings.WEB_PUSH_SUBJECT):
        return {'skipped': 'not_configured'}
    payload = json.dumps({'title': n.title[:150], 'content': n.content[:1000],
                          'link': n.link, 'tag': f'notification:{n.pk}'}, ensure_ascii=False)
    sent, transient = 0, False
    for subscription in PushSubscription.objects.filter(user=n.user, is_active=True):
        if not valid_endpoint(subscription.endpoint):
            subscription.is_active = False
            subscription.save(update_fields=['is_active'])
            continue
        try:
            headers = {'X-WNS-Type': 'wns/raw', 'Content-Type': 'application/octet-stream'} if (
                urlsplit(subscription.endpoint).hostname or '').endswith('.notify.windows.com') else {}
            webpush(subscription_info={'endpoint': subscription.endpoint,
                    'keys': {'p256dh': subscription.p256dh, 'auth': subscription.auth}},
                    data=payload, vapid_private_key=settings.WEB_PUSH_PRIVATE_KEY,
                    vapid_claims={'sub': settings.WEB_PUSH_SUBJECT}, headers=headers, ttl=3600, timeout=10)
            sent += 1
        except WebPushException as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (404, 410):
                subscription.is_active = False
                subscription.save(update_fields=['is_active'])
            elif status is None or status == 429 or status >= 500:
                transient = True
            else:
                logger.warning('Push rejected: notification=%s subscription=%s status=%s', n.pk, subscription.pk, status)
        except Exception:
            transient = True
    if transient:
        raise self.retry(exc=RuntimeError('Temporary Web Push delivery failure'))
    return {'sent': sent}
