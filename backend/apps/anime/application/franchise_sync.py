from collections import Counter
from datetime import timedelta
import re
import time
import uuid
import math
from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from apps.anime.models import Anime, Franchise
from apps.anime.infrastructure.api.shikimori import shikimori_api


REBUILD_STATUS_TTL = 24 * 60 * 60
ACTIVE_REBUILD_KEY = 'anime:franchise-rebuild:active'
ACTIVE_REBUILD_TTL = 10 * 60


def rebuild_status_key(rebuild_id):
    return f'anime:franchise-rebuild:{rebuild_id}'


def set_rebuild_status(status_id, **values):
    if not status_id:
        return
    key = rebuild_status_key(status_id)
    status = cache.get(key, {})
    status.update(values)
    cache.set(key, status, REBUILD_STATUS_TTL)


def graph_nodes(graph, anchor):
    nodes = graph.get('nodes') if isinstance(graph, dict) else None
    if not isinstance(nodes, list):
        return None
    result = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_url = str(node.get('url') or '')
        if node_url and '/animes/' not in node_url:
            continue
        try:
            sid = int(node['id'])
        except (KeyError, TypeError, ValueError):
            continue
        if sid > 0:
            result[sid] = node
    if nodes and anchor not in result:
        return None
    return result


def node_order(node):
    try:
        date = float(node.get('date') or float('inf'))
        if date <= 0 or not math.isfinite(date):
            date = float('inf')
    except (TypeError, ValueError):
        date = float('inf')
    return date


def franchise_name(nodes):
    main = [node for node in nodes if node.get('name')]
    if not main:
        return ''
    top = max(node.get('weight') or 0 for node in main)
    names = [str(node['name']).split() for node in main if (node.get('weight') or 0) == top]
    prefix = []
    for words in zip(*names):
        if len(set(words)) != 1: break
        prefix.append(words[0])
    return re.sub(r'[\s:.,\--]+$', '', ' '.join(prefix)) or str(main[0]['name'])


def detach_incomplete_franchise(shikimori_ids, now):
    rows = list(Anime.objects.select_for_update().filter(
        shikimori_id__in=shikimori_ids,
        franchise_manual=False,
    ))
    old_ids = {row.franchise_id for row in rows if row.franchise_id}
    changed = any(row.franchise_id for row in rows)
    for row in rows:
        row.franchise_id = None
        row.franchise_order = 0
        row.franchise_checked_at = now
    if rows:
        Anime.objects.bulk_update(
            rows,
            ['franchise', 'franchise_order', 'franchise_checked_at'],
            batch_size=200,
        )
    for old in Franchise.objects.filter(pk__in=old_ids):
        old.update_aggregated_data()
    return changed


def sync_franchise(shikimori_id, refresh_provider=False):
    sid = int(shikimori_id)
    if refresh_provider:
        cache.delete(f'shikimori:franchise:{sid}')
    graph = shikimori_api.get_franchise(sid)
    nodes = graph_nodes(graph, sid)
    if nodes is None:
        return {'success': False, 'shikimori_id': sid}
    now = timezone.now()
    if len(nodes) < 2:
        with transaction.atomic():
            changed = detach_incomplete_franchise([sid], now)
        return {'success': True, 'linked': 0, 'changed': changed}
    ordered = sorted(nodes, key=lambda key: (node_order(nodes[key]), key))
    with transaction.atomic():
        rows = list(Anime.objects.select_for_update().filter(shikimori_id__in=ordered, franchise_manual=False).order_by('pk'))
        if len(rows) < 2:
            changed = detach_incomplete_franchise(ordered, now)
            return {'success': True, 'linked': 0, 'changed': changed}
        existing = Counter(row.franchise_id for row in rows if row.franchise_id)
        franchise = Franchise.objects.filter(slug=f'shikimori-{min(nodes)}').order_by('pk').first()
        if franchise is None and existing:
            franchise = Franchise.objects.get(pk=sorted(existing, key=lambda key: (-existing[key], key))[0])
        if franchise is None:
            franchise = Franchise.objects.create(slug=f'shikimori-{min(nodes)}', name=franchise_name([nodes[key] for key in ordered])[:255])
        old_ids = set(existing)-{franchise.pk}
        positions = {key: index for index, key in enumerate(ordered)}
        for row in rows:
            row.franchise_id, row.franchise_order, row.franchise_checked_at = franchise.pk, positions[row.shikimori_id], now
        Anime.objects.bulk_update(rows, ['franchise', 'franchise_order', 'franchise_checked_at'], batch_size=200)
        franchise.update_aggregated_data()
        for old in Franchise.objects.filter(pk__in=old_ids):
            old.update_aggregated_data()
            if not old.entries.exists():
                from apps.social.infrastructure.models.social import GroupChat
                GroupChat.objects.filter(franchise_id=old.pk).update(franchise_id=franchise.pk)
    return {'success': True, 'linked': len(rows), 'franchise_id': franchise.pk, 'changed': True}


@shared_task(name='anime.sync_franchises', time_limit=280, soft_time_limit=250)
def sync_franchises(
    limit=40,
    continue_until_done=False,
    refresh_provider=False,
    rebuild_id=None,
    total=None,
    refresh_before=None,
    provider_failures=0,
):
    owner = rebuild_id or uuid.uuid4().hex
    key = 'anime:franchise-sync:lock'
    if not cache.add(key, owner, 300):
        if continue_until_done:
            active_id = cache.get(ACTIVE_REBUILD_KEY)
            active_status = cache.get(rebuild_status_key(active_id)) if active_id else None
            if rebuild_id and active_id != rebuild_id and active_status and active_status.get('state') in ('queued', 'running'):
                set_rebuild_status(
                    rebuild_id,
                    **active_status,
                    rebuild_id=active_id,
                    message='Отслеживается уже запущенная пересборка',
                )
                return {'skipped': 'duplicate', 'rebuild_id': active_id}
            set_rebuild_status(rebuild_id, state='queued', message='Ожидание текущей синхронизации')
            sync_franchises.apply_async(
                kwargs={
                    'limit': limit,
                    'continue_until_done': True,
                    'refresh_provider': refresh_provider,
                    'rebuild_id': rebuild_id,
                    'total': total,
                    'refresh_before': refresh_before,
                    'provider_failures': provider_failures,
                },
                countdown=10,
            )
        return {'skipped': 'busy', 'retry_queued': bool(continue_until_done)}
    completed, requests, linked, changed, provider_failed = set(), 0, 0, False, False
    started = time.monotonic()
    try:
        if rebuild_id:
            cache.set(ACTIVE_REBUILD_KEY, rebuild_id, ACTIVE_REBUILD_TTL)
        cutoff = refresh_before or timezone.now() - timedelta(days=30)
        due = Anime.objects.filter(shikimori_id__isnull=False, franchise_manual=False).filter(
            Q(franchise_checked_at__isnull=True) | Q(franchise_checked_at__lt=cutoff))
        if total is None:
            total = due.count()
        set_rebuild_status(rebuild_id, state='running', total=total, message='Получение графов Shikimori')
        candidates = list(due.order_by('franchise_checked_at', '-year', '-pk').values_list('shikimori_id', flat=True)[:1000])
        for sid in candidates:
            if sid in completed: continue
            if requests >= max(1, min(int(limit), 100)) or time.monotonic()-started > 210: break
            result = sync_franchise(sid, refresh_provider=refresh_provider)
            requests += 1
            if not result['success']:
                provider_failed = True
                break
            linked += result['linked']
            changed = changed or result.get('changed', False)
            if result.get('franchise_id'):
                completed.update(Anime.objects.filter(franchise_id=result['franchise_id']).values_list('shikimori_id', flat=True))
            time.sleep(1.1)
        if changed:
            from .recommendations import invalidate_catalog
            invalidate_catalog()
        remaining = due.count()
        has_more = remaining > 0
        processed = max(0, total - remaining)
        retry_provider = bool(
            provider_failed and continue_until_done and provider_failures < 5
        )
        set_rebuild_status(
            rebuild_id,
            state=('queued' if retry_provider else 'failed') if provider_failed else ('running' if has_more else 'completed'),
            total=total,
            processed=processed,
            remaining=remaining,
            linked=linked,
            message=(
                f'Shikimori временно не ответил. Повтор {provider_failures + 1} из 5 поставлен в очередь.'
                if retry_provider else
                ('Shikimori временно не ответил. Существующие связи сохранены.' if provider_failed else
                ('Пересборка продолжается' if has_more else 'Франшизы пересобраны')
                )
            ),
        )
        if rebuild_id:
            if (provider_failed and not retry_provider) or not has_more:
                if cache.get(ACTIVE_REBUILD_KEY) == rebuild_id:
                    cache.delete(ACTIVE_REBUILD_KEY)
            else:
                cache.set(ACTIVE_REBUILD_KEY, rebuild_id, ACTIVE_REBUILD_TTL)
        if retry_provider or (continue_until_done and has_more and not provider_failed):
            sync_franchises.apply_async(
                kwargs={
                    'limit': limit,
                    'continue_until_done': True,
                    'refresh_provider': refresh_provider,
                    'rebuild_id': rebuild_id,
                    'total': total,
                    'refresh_before': refresh_before,
                    'provider_failures': provider_failures + 1 if retry_provider else 0,
                },
                countdown=min(300, 30 * (2 ** provider_failures)) if retry_provider else 5,
            )
        return {
            'requests': requests,
            'linked': linked,
            'has_more': has_more,
            'processed': processed,
            'provider_failed': provider_failed,
        }
    finally:
        if cache.get(key) == owner: cache.delete(key)
