"""Optional screenshots are never fetched in the card's HTTP request."""
from celery import shared_task
from django.core.cache import cache
from apps.anime.models import Anime
from .anime_service import anime_service


@shared_task(name='anime.refresh_missing_screenshots', time_limit=75, soft_time_limit=65)
def refresh_missing_screenshots():
    if not cache.add('screenshots:batch-running', True, 90):
        return
    try:
        cursor = cache.get('screenshots:cursor', 0)
        rows = list(Anime.objects.filter(pk__gt=cursor, screenshots=[], shikimori_id__isnull=False)
                    .order_by('pk').values('pk', 'shikimori_id')[:3])
        if not rows:
            cache.set('screenshots:cursor', 0, 86400)
        for row in rows:
            cache.set('screenshots:cursor', row['pk'], 86400)
            key = f"screenshots:attempt:{row['pk']}"
            if not cache.add(key, True, 1800):
                continue
            try:
                result = anime_service.search_by_shikimori_id(row['shikimori_id'], limit=1)
                screenshots = (result or {}).get('screenshots') or []
                if screenshots:
                    Anime.objects.filter(pk=row['pk']).update(screenshots=screenshots)
            except Exception:
                # Both a missing result and a provider failure have a retry budget.
                continue
    finally:
        cache.delete('screenshots:batch-running')


@shared_task(name='anime.prune_presence_index', time_limit=10)
def prune_presence_index():
    from core.online_status import online_status, PRESENCE_INDEX
    from django.utils import timezone
    client = online_status._get_client()
    if client:
        client.zremrangebyscore(PRESENCE_INDEX, '-inf', timezone.now().timestamp())
