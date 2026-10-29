import logging
from collections import Counter
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.anime.application.cache_utils import safe_cache_get, safe_cache_set
from apps.anime.infrastructure.models.anime import Anime
from apps.anime.infrastructure.models.read_models import RecommendationSnapshot

logger = logging.getLogger(__name__)
ALGORITHM_VERSION = 2
SECTIONS = ('based_on_watched', 'similar_style', 'top_rated_in_genres', 'new_in_genres',
            'classics', 'top_anime', 'new_releases', 'short', 'movies', 'top_rated', 'new_season')


def candidate_pool():
    from .catalog_visibility import hidden_anime
    key = f"recommendations:candidates:v2:{safe_cache_get('catalog:revision', 0)}"
    cached = safe_cache_get(key)
    if cached is not None:
        return cached
    fields = ('id', 'slug', 'title_ru', 'title_en', 'poster', 'poster_url', 'genres', 'score',
              'kind', 'episodes', 'year', 'status', 'franchise_id', 'franchise_order')
    rows = list(Anime.objects.filter(has_cyrillic=True, is_available=True, score__gte=6)
                .exclude(status='announced').exclude(pk__in=hidden_anime().values('pk'))
                .order_by('-score', 'id').values(*fields)[:1000])
    franchises = {r['franchise_id'] for r in rows if r['franchise_id']}
    totals = {r['franchise_id']: r for r in Anime.objects.filter(franchise_id__in=franchises)
              .values('franchise_id').annotate(parts=Count('id'), episodes_total=Sum('episodes'))}
    for row in rows:
        row['title'] = row.pop('title_ru') or row['title_en']
        row['anime_id'] = row['id']
        row['rating'] = row['score']
        row['poster'] = '/media/' + row['poster'] if row['poster'] else row['poster_url']
        row['genres'] = row['genres'] if isinstance(row['genres'], list) else []
        row['franchise_parts_count'] = totals.get(row['franchise_id'], {}).get('parts', 1)
        row['franchise_episodes'] = totals.get(row['franchise_id'], {}).get('episodes_total')
    safe_cache_set(key, rows, 900)
    return rows


def pick(rows, code, text, limit=24):
    seen, result = set(), []
    for row in rows:
        group = ('franchise', row['franchise_id']) if row['franchise_id'] else ('anime', row['id'])
        if group in seen:
            continue
        seen.add(group)
        reason, details = text(row) if callable(text) else (text, {})
        result.append({**row, 'reason': reason, 'reason_details': {'code': code, **details}})
        if len(result) == limit:
            break
    return result


def count_label(count, one, few, many):
    if count % 10 == 1 and count % 100 != 11:
        word = one
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        word = few
    else:
        word = many
    return f'{count} {word}'


def short_reason(row):
    episodes = row['franchise_episodes'] or row['episodes']
    parts = row['franchise_parts_count']
    return (f"«{row['title']}» можно посмотреть за {count_label(episodes, 'серию', 'серии', 'серий')}. "
            f"У этого аниме {count_label(parts, 'часть', 'части', 'частей')}; "
            'всего допускается до двух частей и 24 серий.',
            {'episodes': episodes, 'parts': parts})


def build(user=None):
    from apps.users.infrastructure.models.users import UserLibrary
    pool = candidate_pool()
    library = list(UserLibrary.objects.filter(user=user).select_related('anime').only(
        'anime_id', 'status', 'rating', 'is_favorite', 'anime__title_ru', 'anime__title_en',
        'anime__genres', 'anime__kind')) if user else []
    profiles = [item for item in library if item.status in ('started', 'completed')]
    excluded = {item.anime_id for item in library if item.status in ('started', 'completed', 'hidden', 'dropped')}
    eligible = [row for row in pool if row['id'] not in excluded and (row['franchise_order'] or 1) <= 1]
    genres = Counter()
    for item in profiles:
        for genre in item.anime.genres or []:
            genres[genre] += (item.rating or 5) / 10 + (2 if item.is_favorite else 0)
    current_year = timezone.now().year
    result = {'user_genres': [g for g, _ in genres.most_common(15)], 'has_personalization': bool(profiles)}
    result['top_rated'] = pick([r for r in eligible if r['score'] >= 8.5], 'rating',
                              lambda r: (f"У «{r['title']}» высокий рейтинг -{r['score']:.1f}.", {'rating': r['score']}))
    recent = [r for r in eligible if (r['year'] or 0) >= current_year - 1 and r['score'] >= 7]
    recent_reason = lambda r: (
        f"«{r['title']}» -аниме {r['year']} года с рейтингом {r['score']:.1f}.",
        {'year': r['year'], 'rating': r['score']})
    result['new_season'] = pick(recent, 'recent', recent_reason)
    result['top_anime'] = result['new_season']
    result['classics'] = pick([r for r in eligible if r['year'] and r['year'] <= 2010 and r['score'] >= 7],
                              'classic', lambda r: (
                                  f"«{r['title']}» -аниме {r['year']} года с рейтингом {r['score']:.1f}; подборка включает тайтлы до 2010 года включительно.",
                                  {'year': r['year'], 'rating': r['score']}))
    result['movies'] = pick([r for r in eligible if r['kind'] == 'movie' and r['episodes'] == 1 and r['score'] >= 7],
                            'movie', lambda r: (
                                f"«{r['title']}» -фильм из одной серии с рейтингом {r['score']:.1f}.",
                                {'episodes': 1, 'rating': r['score']}))
    result['short'] = pick([r for r in eligible if r['episodes'] and
                           (r['franchise_episodes'] or r['episodes']) <= 24 and r['franchise_parts_count'] <= 2],
                           'short', short_reason)
    scored = []
    for row in eligible:
        matched = set(row['genres']) & set(genres)
        if not matched or not profiles:
            continue
        source = max(profiles, key=lambda item: len(set(item.anime.genres or []) & set(row['genres'])))
        overlap = sorted(set(source.anime.genres or []) & set(row['genres']))
        score = sum(genres[g] for g in matched) + row['score'] * .05 + (.1 if source.anime.kind == row['kind'] else 0)
        title = source.anime.title_ru or source.anime.title_en
        reason = f'В «{row["title"]}» есть общие жанры с «{title}» из вашей коллекции: {", ".join(overlap)}. Рейтинг -{row["score"]:.1f}.'
        scored.append((score, {**row, '_reason': reason, '_source': source.anime_id, '_genres': overlap}))
    ranked = [row for _, row in sorted(scored, key=lambda item: (-item[0], item[1]['id']))]
    result['based_on_watched'] = pick(ranked, 'similar_to_watched', lambda r: (
        r['_reason'], {'source_anime_id': r['_source'], 'genres': r['_genres']}))
    for items in result.values():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for key in ('_reason', '_source', '_genres'):
                        item.pop(key, None)
    result['similar_style'] = result['based_on_watched']
    result['top_rated_in_genres'] = pick(ranked, 'preferred_genres', lambda r: (
        f"Рейтинг «{r['title']}» -{r['score']:.1f}. Жанры из просмотренных вами аниме: " + ', '.join(sorted(set(r['genres']) & set(genres))[:3]) + '.',
        {'genres': sorted(set(r['genres']) & set(genres))[:3], 'rating': r['score']}))
    result['new_in_genres'] = pick([r for r in ranked if r['status'] == 'ongoing'], 'ongoing_genres',
                                 lambda r: (
                                     f"«{r['title']}» сейчас выходит. Общие жанры с просмотренными вами аниме: " + ', '.join(sorted(set(r['genres']) & set(genres))[:3]) + '.',
                                     {'genres': sorted(set(r['genres']) & set(genres))[:3]}))
    result['new_releases'] = pick(recent, 'recent', recent_reason)
    return result


@shared_task(name='anime.refresh_recommendations')
def refresh_recommendations(key='public'):
    from apps.users.infrastructure.models.users import User
    user = User.objects.filter(pk=key.removeprefix('user:'), is_active=True).first() if key.startswith('user:') else None
    if key.startswith('user:') and not user:
        return
    snapshot, _ = RecommendationSnapshot.objects.get_or_create(key=key, defaults={'user': user})
    revision = snapshot.revision
    catalog_revision = safe_cache_get('catalog:revision', 0)
    data = build(user)
    with transaction.atomic():
        snapshot = RecommendationSnapshot.objects.select_for_update().get(pk=snapshot.pk)
        if snapshot.revision != revision:
            return
        snapshot.data, snapshot.dirty = data, False
        snapshot.generated_at = timezone.now()
        snapshot.catalog_revision = catalog_revision
        snapshot.algorithm_version = ALGORITHM_VERSION
        snapshot.save()
    safe_cache_set(f'recommendations:snapshot:v{ALGORITHM_VERSION}:{key}:{revision}:{catalog_revision}', data, 60)
    return key


def queue_refresh(key):
    from django.core.cache import cache
    try:
        if cache.add('recommendations:queued:' + key, 1, 10):
            refresh_recommendations.delay(key)
    except Exception:
        logger.warning('Recommendation refresh deferred', exc_info=True)


def read(user, sections=None):
    from apps.users.infrastructure.models.users import UserLibrary
    wanted = [s.strip() for s in sections.split(',') if s.strip()] if sections else list(SECTIONS)
    if set(wanted) - set(SECTIONS):
        raise ValidationError({'sections': 'Неизвестный раздел рекомендаций'})
    key = f'user:{user.pk}' if user and user.is_authenticated else 'public'
    snapshot, _ = RecommendationSnapshot.objects.get_or_create(key=key, defaults={'user': user if key != 'public' else None})
    data = safe_cache_get(f'recommendations:snapshot:v{ALGORITHM_VERSION}:{key}:{snapshot.revision}:{snapshot.catalog_revision}')
    if data is None:
        data = snapshot.data
    if snapshot.algorithm_version != ALGORITHM_VERSION or (key != 'public' and snapshot.dirty):
        data = None
    if snapshot.algorithm_version != ALGORITHM_VERSION or snapshot.dirty or snapshot.catalog_revision != safe_cache_get('catalog:revision', 0) or not snapshot.generated_at or snapshot.generated_at < timezone.now() - timedelta(minutes=15):
        queue_refresh(key)
    if not data:
        public = RecommendationSnapshot.objects.filter(key='public').first()
        # A cold personal read must never materialize the user's entire library.
        # Shared fallback has no personal reasons; the worker builds those later.
        data = public.data if public and public.algorithm_version == ALGORITHM_VERSION and public.data else build(None)
    candidates = {row['id'] for section in wanted for row in data.get(section, [])[:24]}
    excluded = set(UserLibrary.objects.filter(user=user, anime_id__in=candidates,
                   status__in=('hidden', 'started', 'completed', 'dropped'))
                   .values_list('anime_id', flat=True)) if key != 'public' else set()
    from .catalog_visibility import hidden_anime
    excluded.update(hidden_anime().filter(pk__in=candidates).values_list('pk', flat=True))
    # Decisions about current catalog visibility cannot rely on a stale snapshot.
    available = set(Anime.objects.filter(pk__in=candidates, is_available=True, has_cyrillic=True)
                    .values_list('pk', flat=True))
    excluded.update(candidates - available)
    movie_ids = {row['id'] for row in data.get('movies', [])} if 'movies' in wanted else set()
    valid_movies = set(Anime.objects.filter(pk__in=movie_ids, kind='movie', episodes=1).values_list('pk', flat=True))
    return {**{section: [row for row in data.get(section, [])[:24] if row['id'] not in excluded
                         and (section != 'movies' or row['id'] in valid_movies)] for section in wanted},
            'user_genres': data.get('user_genres', []), 'has_personalization': data.get('has_personalization', False)}


def invalidate_user(user_id):
    from django.core.cache import cache
    key = f'user:{user_id}'
    snapshot, _ = RecommendationSnapshot.objects.get_or_create(key=key, defaults={'user_id': user_id})
    RecommendationSnapshot.objects.filter(pk=snapshot.pk).update(dirty=True, revision=F('revision')+1)
    try:
        cache.delete('recommendations:snapshot:' + key)
        cache.delete('recommendations:queued:' + key)
    except Exception:
        pass
    transaction.on_commit(lambda: queue_refresh(key), robust=True)


def invalidate_catalog():
    from apps.seo.signals import schedule_hubs
    schedule_hubs()
    from django.core.cache import cache
    # A running worker may have read the previous catalog. Increment the same
    # revision it checks under lock so that it cannot overwrite invalidation.
    RecommendationSnapshot.objects.all().update(dirty=True, revision=F('revision')+1)
    try:
        cache.delete('recommendations:candidates:v1')
        cache.delete('recommendations:snapshot:public')
        cache.set('catalog:revision', timezone.now().timestamp(), None)
    except Exception:
        pass
    transaction.on_commit(lambda: queue_refresh('public'), robust=True)


@shared_task(name='anime.refresh_dirty_recommendations')
def refresh_dirty_recommendations():
    for key in RecommendationSnapshot.objects.filter(dirty=True).values_list('key', flat=True)[:50]:
        refresh_recommendations(key)
