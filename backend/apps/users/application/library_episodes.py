import random

from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from apps.anime.models import CalendarRelease, KodikAvailability
from apps.anime.infrastructure.models.anime import UserEpisodeProgress
from apps.users.models import UserLibrary, UserLibraryArchive

PROGRESS_FIELDS = ('current_episode', 'episodes_watched', 'real_episodes_watched',
                   'rewatch_count', 'watched_through', 'episode_baseline',
                   'current_season')

MANUAL_STATUSES = ('dropped', 'on_hold', 'hidden', 'favorite')


def status_for_progress(watched, total, in_progress=False):
    if total and watched >= total:
        return 'completed'
    if watched > 0 or in_progress:
        return 'started'
    return 'planned'


def latest_active_progress(rows):
    active = [
        (season_number or 1, episode_number)
        for season_number, episode_number, status in rows
        if status in ('watched', 'skipped', 'in_progress')
    ]
    return max(active, default=None)


def sync_library_from_episode_rows(user, anime):
    rows = list(UserEpisodeProgress.objects.filter(user=user, anime=anime)
                .values_list('season_number', 'episode_number', 'status'))
    archive = UserLibraryArchive.objects.filter(user=user, anime=anime).first()
    library = UserLibrary.objects.filter(user=user, anime=anime).first()
    latest = latest_active_progress(rows)

    if library is None and archive is not None:
        retained = UserLibrary(user=user, anime=anime, **archive.progress)
        watched = len(seen_progress_keys(retained, rows))
        archive.progress.update(
            current_season=latest[0] if latest else (retained.current_season or 1),
            current_episode=latest[1] if latest else 0,
            episodes_watched=watched,
            real_episodes_watched=watched,
            watched_through=retained.watched_through,
        )
        archive.save(update_fields=['progress'])
        return None

    if library is None:
        library = UserLibrary.objects.create(user=user, anime=anime)

    seen = seen_progress_keys(library, rows)
    watched = len(seen)
    in_progress = any(status == 'in_progress' for _, _, status in rows)
    total = anime.progress_total or anime.episodes or 0
    new_status = status_for_progress(watched, total, in_progress)
    manual_status = (
        library.user_set_status and library.status in MANUAL_STATUSES
    )
    if not manual_status:
        library.status = new_status
    library.current_season = latest[0] if latest else (library.current_season or 1)
    library.current_episode = latest[1] if latest else 0
    library.episodes_watched = watched
    library.real_episodes_watched = watched
    library.user_set_status = manual_status
    if (watched > 0 or in_progress) and not library.started_at:
        library.started_at = timezone.now()
    if library.status == 'completed' and not library.completed_at:
        library.completed_at = timezone.now()
    library.save(update_fields=[
        'status', 'current_season', 'current_episode', 'episodes_watched',
        'real_episodes_watched', 'user_set_status', 'started_at',
        'completed_at', 'updated_at',
    ])
    return library


def _apply_watched_count(user, anime, season, watched, now):
    total = anime.progress_total or anime.episodes or 0
    watched = max(0, int(watched or 0))
    if total:
        watched = min(watched, total)

    progress = UserEpisodeProgress.objects.filter(
        user=user, anime=anime, season_number=season
    )
    existing = set(
        progress.filter(episode_number__lte=watched)
        .values_list('episode_number', flat=True)
    )
    progress.filter(episode_number__lte=watched).update(
        status='watched', is_manually_marked=True, watched_at=now)
    progress.filter(episode_number__gt=watched).update(
        status='not_started', is_manually_marked=False,
        watched_at=None, last_position=0)
    UserEpisodeProgress.objects.bulk_create([
        UserEpisodeProgress(
            user=user,
            anime=anime,
            season_number=season,
            episode_number=number,
            status='watched',
            is_manually_marked=True,
            watched_at=now,
        )
        for number in range(1, watched + 1)
        if number not in existing
    ])
    return watched


def _clear_watched_through(user, anime):
    UserLibrary.objects.filter(user=user, anime=anime).update(watched_through=0)
    archive = UserLibraryArchive.objects.filter(user=user, anime=anime).first()
    if archive is not None:
        archive.progress['watched_through'] = 0
        archive.save(update_fields=['progress'])


@transaction.atomic
def set_watched_progress(user, anime, watched, season=1):
    season = max(0, int(season or 1))
    watched = _apply_watched_count(user, anime, season, watched, timezone.now())
    _clear_watched_through(user, anime)
    sync_library_from_episode_rows(user, anime)
    return watched


@transaction.atomic
def set_watched_progress_by_seasons(user, anime, seasons):
    now = timezone.now()
    counts = {}
    for item in seasons or []:
        if isinstance(item, dict):
            season = int(item.get('season_number', 1) or 1)
            watched = int(item.get('watched_up_to', 0) or 0)
        else:
            season, watched = item
            season = int(season or 1)
            watched = int(watched or 0)
        counts[season] = _apply_watched_count(
            user, anime, max(0, season), watched, now
        )

    _clear_watched_through(user, anime)
    sync_library_from_episode_rows(user, anime)
    return counts


@transaction.atomic
def reset_watched_progress(user, anime):
    UserEpisodeProgress.objects.filter(user=user, anime=anime).update(
        status='not_started',
        is_manually_marked=False,
        watched_at=None,
        last_position=0,
    )
    _clear_watched_through(user, anime)
    sync_library_from_episode_rows(user, anime)


def prepare_library_progress(item):
    old = UserLibrary.objects.filter(pk=item.pk).values('status', 'current_episode',
        'episodes_watched', 'real_episodes_watched').first() if item.pk else None
    availability = KodikAvailability.objects.filter(anime_id=item.anime_id).first()
    if item.episode_baseline is None and availability:
        item.episode_baseline = availability.episodes
    elif item.episode_baseline is None and item.anime.status == 'announced':
        item.episode_baseline = []
    if not UserEpisodeProgress.objects.filter(user_id=item.user_id, anime_id=item.anime_id).exists():
        if old is None or any(old[field] != getattr(item, field) for field in PROGRESS_FIELDS[:3]):
            item.watched_through = max(item.current_episode or 0, item.episodes_watched or 0, item.real_episodes_watched or 0)


def seen_progress_keys(item, progress=None):
    season = item.current_season or 1
    seen = {(season, number) for number in range(1, item.watched_through + 1)}
    rows = progress if progress is not None else UserEpisodeProgress.objects.filter(
        user_id=item.user_id, anime_id=item.anime_id
    ).values_list('season_number', 'episode_number', 'status')
    for season_number, episode_number, status in rows:
        key = (season_number or 1, episode_number)
        if status in ('watched', 'skipped'):
            seen.add(key)
        else:
            seen.discard(key)
    return seen


def seen_episodes(item, progress=None):
    seen = set(range(1, item.watched_through + 1))
    rows = progress if progress is not None else UserEpisodeProgress.objects.filter(
        user_id=item.user_id, anime_id=item.anime_id).values_list('episode_number', 'status')
    for number, status in rows:
        if status in ('watched', 'skipped'):
            seen.add(number)
        else:
            seen.discard(number)
    return seen


def unseen_episodes(item, progress=None):
    try:
        available = set(item.anime.kodik_availability.episodes)
    except KodikAvailability.DoesNotExist:
        return []
    return sorted(available - seen_episodes(item, progress))


@receiver(post_save, sender=UserLibrary)
def collection_added(sender, instance, created, raw=False, **kwargs):
    if not created or raw:
        return
    archive = UserLibraryArchive.objects.filter(user_id=instance.user_id, anime_id=instance.anime_id).first()
    if archive:
        for field in PROGRESS_FIELDS:
            if field in archive.progress:
                setattr(instance, field, archive.progress[field])
        UserLibrary.objects.filter(pk=instance.pk).update(**{field: getattr(instance, field) for field in PROGRESS_FIELDS})
    from apps.notifications.models import EpisodeSubscription
    available = KodikAvailability.objects.filter(anime_id=instance.anime_id).first()
    sub, _ = EpisodeSubscription.objects.get_or_create(user_id=instance.user_id, anime_id=instance.anime_id)
    sub.is_active = True
    sub.manually_disabled = False
    sub.baseline_initialized = available is not None or instance.anime.status == 'announced'
    sub.notified_episodes = available.episodes if available else []
    sub.last_notified_episode = available.last_episode if available else 0
    sub.save()


@receiver(pre_delete, sender=UserLibrary)
def collection_removed(sender, instance, origin=None, **kwargs):
    from apps.users.models import User
    from apps.anime.models import Anime
    if isinstance(origin, (User, Anime)) or getattr(origin, 'model', None) in (User, Anime):
        return
    UserLibraryArchive.objects.update_or_create(user_id=instance.user_id, anime_id=instance.anime_id,
        defaults={'progress': {field: getattr(instance, field) for field in PROGRESS_FIELDS}})
    from apps.notifications.models import EpisodeSubscription
    EpisodeSubscription.objects.filter(user_id=instance.user_id, anime_id=instance.anime_id).update(is_active=False)


def new_episodes_for_user(user):
    from collections import defaultdict
    items = list(UserLibrary.objects.filter(user=user, anime__is_available=True,
        anime__kodik_availability__last_episode__gt=0).exclude(status__in=('hidden', 'dropped'))
        .select_related('anime', 'anime__kodik_availability'))
    progress = defaultdict(list)
    for anime_id, number, status in UserEpisodeProgress.objects.filter(user=user,
            anime_id__in=[item.anime_id for item in items]).values_list('anime_id', 'episode_number', 'status'):
        progress[anime_id].append((number, status))
    now = timezone.now()
    releases = defaultdict(dict)
    for sid, episode, aired_at in CalendarRelease.objects.filter(
            shikimori_id__in={item.anime.shikimori_id for item in items if item.anime.shikimori_id},
            aired_at__gt=min((item.added_at for item in items), default=now),
            aired_at__lte=now).values_list('shikimori_id', 'episode', 'aired_at'):
        releases[sid][episode] = aired_at
    result = []
    for item in items:
        anime = item.anime
        dates = releases[anime.shikimori_id]
        unseen = [episode for episode in unseen_episodes(item, progress[item.anime_id])
                  if episode in dates and dates[episode] > item.added_at]
        if not unseen:
            continue
        result.append({'anime_id': anime.pk, 'id': anime.pk, 'slug': anime.slug,
            'title': anime.title_ru or anime.title_en, 'poster': anime.poster.url if anime.poster else anime.poster_url,
            'title_en': anime.title_en or '', 'rating_count': 0, 'status': anime.status,
            'year': anime.year, 'kind': anime.kind, 'genres': anime.genres or [], 'rating': anime.score,
            'episodes': anime.episodes, 'latest_episode': unseen[-1], 'unwatched_count': len(unseen),
            'next_episode': unseen[0]})
    random.shuffle(result)
    return result[:24]
