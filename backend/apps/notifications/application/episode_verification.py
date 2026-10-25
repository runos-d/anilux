import logging

from django.core.cache import cache
from django.utils import timezone

from apps.anime.models import Anime
from apps.anime.application.cache_utils import safe_cache_get, safe_cache_set

logger = logging.getLogger(__name__)
VERIFICATION_TTL = 120


def verified_recently(shikimori_id, after=None):
    stamp = safe_cache_get(f'episodes:verified:{shikimori_id}')
    return stamp is not None and timezone.now().timestamp() - stamp <= VERIFICATION_TTL and (
        after is None or stamp >= after.timestamp())


def mark_verified(shikimori_ids):
    stamp = timezone.now().timestamp()
    for sid in shikimori_ids:
        safe_cache_set(f'episodes:verified:{sid}', stamp, VERIFICATION_TTL)


def queue_due_verifications(user=None):
    from apps.notifications.models import Reminder
    from .celery_tasks import verify_calendar_episode
    due = Reminder.objects.filter(is_active=True, user__is_active=True, calendar_release__isnull=False,
        reminder_time__lte=timezone.now(), available_notified_at__isnull=True)
    if user is not None:
        due = due.filter(user=user)
    dates = {}
    for sid, date in due.order_by('reminder_time').values_list('calendar_release__shikimori_id', 'reminder_time'):
        dates[sid] = date
    queued = 0
    for sid, date in dates.items():
        if verified_recently(sid, after=date):
            continue
        try:
            if cache.add(f'episodes:verify-queued:{sid}', 1, 60):
                verify_calendar_episode.delay(sid)
                queued += 1
                if queued >= 10:
                    break
        except Exception:
            logger.warning('Kodik episode verification deferred for title %s', sid)


def verify_title(shikimori_id):
    from apps.anime.infrastructure.api.kodik import kodik_api
    from apps.anime.application.episode_availability import provider_episodes, apply_availability
    from .episode_events import process_subscriptions, process_reminders
    try:
        response = kodik_api._get('/search', {'shikimori_id': str(shikimori_id), 'types': 'anime,anime-serial',
            'limit': 100, 'with_material_data': True, 'with_seasons': True, 'with_episodes': True}, retries=1)
        records = response.get('results') if isinstance(response, dict) else None
        if not isinstance(records, list) or response.get('error'):
            return False
        matching = [record for record in records if str(record.get('shikimori_id')) == str(shikimori_id)]
        if len(matching) != len(records):
            return False
        observations = [provider_episodes(record) for record in matching]
        complete = not response.get('next_page') and all(value is not None for value in observations)
        if response.get('total') is not None and int(response['total']) > len(records):
            complete = False
        anime = Anime.objects.filter(shikimori_id=shikimori_id).first()
        if anime and not anime.is_available:
            return False
        if not anime and matching:
            from apps.anime.application.anime_service import anime_service
            anime, _ = anime_service.import_anime(matching[0], update_existing=False,
                skip_shikimori=True, skip_video_sync=True, download_posters=False, track_availability=False)
        known = [value for value in observations if value is not None]
        if anime and (known or complete):
            apply_availability({anime.pk: set().union(*known)}, replace=complete)
        if complete:
            mark_verified([shikimori_id])
        process_subscriptions()
        process_reminders(verified_shikimori_ids={shikimori_id} if complete else set())
        return complete
    except Exception:
        logger.warning('Kodik availability check failed for title %s; delivery deferred', shikimori_id)
        return False
