from celery import shared_task
import hashlib
import json
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import SeoHub, SeoCollection
from .service import visible_anime, Franchise, SEASONS, KINDS, STATUSES, resolve, franchise_path, genre_catalog


@shared_task(name='seo.refresh_hubs')
def refresh_hubs():
    qs = visible_anime()
    years = list(qs.exclude(year=None).order_by('year').values_list('year', flat=True).distinct())
    paths = {'/', '/anime', '/anime/browse', '/anime/franchises'}
    paths.update(f'/anime/year/{y}' for y in years)
    paths.update(f'/anime/season/{y}/{s}' for y in years for s in SEASONS)
    paths.update(f"/anime/genre/{row['slug']}" for row in genre_catalog(qs))
    paths.update(f'/anime/type/{kind}' for kind in KINDS)
    paths.update(f'/anime/status/{status}' for status in STATUSES if status != 'released')
    paths.update(franchise_path(f) for f in Franchise.objects.filter(entries__in=qs).distinct())
    paths.update(f'/anime/collection/{slug}' for slug in SeoCollection.objects.filter(enabled=True).values_list('slug', flat=True))
    fallback_mod = qs.aggregate(value=Max('updated_at'))['value']
    rows = []
    previous = {row.path: row for row in SeoHub.objects.all()}
    for path in sorted(paths):
        page = resolve(path)
        if page.indexable and page.status == 200 and not page.redirect:
            signature = hashlib.sha256(json.dumps([page.name, page.text, page.count, page.items, page.modified], default=str, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            old = previous.get(path)
            modified = page.modified or fallback_mod
            if old:
                modified = old.lastmod if old.fingerprint == signature else timezone.now()
            rows.append(SeoHub(path=path, lastmod=modified, fingerprint=signature))
    with transaction.atomic():
        SeoHub.objects.all().delete()
        SeoHub.objects.bulk_create(rows, batch_size=500)
    return len(rows)
