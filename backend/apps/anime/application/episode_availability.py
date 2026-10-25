from django.db import transaction
from django.utils import timezone

from apps.anime.models import Anime, CalendarRelease, KodikAvailability


def initial_baseline(anime, episodes, added_at):
    newer = set(CalendarRelease.objects.filter(shikimori_id=anime.shikimori_id,
        episode__in=episodes, aired_at__gt=added_at).values_list('episode', flat=True)) if anime.shikimori_id else set()
    return sorted(set(episodes) - newer)


def provider_episodes(record):
    if not isinstance(record, dict) or not record.get('link'):
        return None
    if record.get('type') == 'anime':
        return {1}
    if record.get('type') != 'anime-serial':
        return None
    seasons = record.get('seasons') or {}
    explicit = set()
    detailed = False
    for season in seasons.values() if isinstance(seasons, dict) else []:
        if isinstance(season, dict) and isinstance(season.get('episodes'), dict):
            detailed = True
            for number, link in season['episodes'].items():
                if str(number).isdigit() and link and 0 < int(number) <= 10000:
                    explicit.add(int(number))
    if detailed:
        return explicit
    try:
        last = int(record['last_episode'])
    except (KeyError, ValueError, TypeError):
        return None
    if not 0 <= last <= 10000:
        return None
    return set(range(1, last + 1))


def apply_availability(observed, replace=False):
    from apps.users.models import UserLibrary
    from apps.notifications.models import EpisodeSubscription
    if not observed:
        return 0
    changed = []
    newly_available = {}
    with transaction.atomic():
        KodikAvailability.objects.bulk_create(
            [KodikAvailability(anime_id=pk) for pk in sorted(observed)], ignore_conflicts=True)
        rows = list(KodikAvailability.objects.select_for_update().filter(anime_id__in=observed).order_by('anime_id'))
        unknown_library = set(UserLibrary.objects.filter(anime_id__in=observed,
            episode_baseline__isnull=True).values_list('anime_id', flat=True))
        unknown_subscriptions = set(EpisodeSubscription.objects.filter(anime_id__in=observed,
            baseline_initialized=False).values_list('anime_id', flat=True))
        updates = []
        for row in rows:
            before = set(row.episodes)
            after = set(observed[row.anime_id]) if replace else before | set(observed[row.anime_id])
            row.episodes = sorted(after)
            row.last_episode = max(after, default=0)
            row.updated_at = timezone.now()
            if row.anime_id in unknown_library:
                unknown = UserLibrary.objects.filter(anime_id=row.anime_id, episode_baseline__isnull=True)
                for item in unknown.select_related('anime'):
                    baseline = initial_baseline(item.anime, row.episodes, item.added_at)
                    fields = {'episode_baseline': baseline}
                    UserLibrary.objects.filter(pk=item.pk).update(**fields)
            if row.anime_id in unknown_subscriptions:
                for sub in EpisodeSubscription.objects.filter(anime_id=row.anime_id,
                        baseline_initialized=False).select_related('anime'):
                    membership = UserLibrary.objects.filter(user_id=sub.user_id, anime_id=sub.anime_id).first()
                    baseline = initial_baseline(sub.anime, row.episodes,
                        membership.added_at if membership else sub.created_at)
                    EpisodeSubscription.objects.filter(pk=sub.pk).update(
                        last_notified_episode=max(baseline, default=0), notified_episodes=baseline, baseline_initialized=True)
            if after != before:
                changed.append(row.anime_id)
                updates.append(row)
                if after - before:
                    newly_available[row.anime_id] = after - before
        KodikAvailability.objects.bulk_update(updates, ['episodes', 'last_episode', 'updated_at'])
        from apps.users.application.library_episodes import unseen_episodes
        for item in UserLibrary.objects.select_for_update().filter(
                anime_id__in=newly_available, status='completed', user_set_status=False
                ).select_related('anime', 'anime__kodik_availability'):
            if set(unseen_episodes(item)) & newly_available[item.anime_id]:
                item.status = 'started'
                item.user_set_status = False
                item.save(update_fields=['status', 'user_set_status', 'updated_at'])
        from apps.notifications.application.celery_tasks import process_episode_events
        transaction.on_commit(lambda: process_episode_events.delay(), robust=True)
    return len(changed)


def record_availability(anime, record):
    episodes = provider_episodes(record)
    if episodes is not None:
        return apply_availability({anime.pk: episodes})
    return 0
