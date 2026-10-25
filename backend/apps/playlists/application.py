from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from apps.anime.models import Anime
from apps.playlists.models import FavoriteAnime, PlaylistItem


def synchronize_anime_items(playlist, entries):
    ids = [entry['anime_id'] for entry in entries]
    if len(ids) != len(set(ids)):
        raise serializers.ValidationError({'items': 'Аниме не должно повторяться в подборке'})
    found = set(Anime.objects.filter(pk__in=ids).values_list('pk', flat=True))
    if found != set(ids):
        raise serializers.ValidationError({'items': 'Некоторые аниме больше недоступны. Обновите подборку.'})
    current = list(playlist.items.order_by('position', 'pk'))
    old_anime = {item.anime_id: item for item in current if item.anime_id}
    slots = [item.position for item in current if item.anime_id]
    last = max((item.position for item in current), default=0)
    updates, additions = [], []
    for index, entry in enumerate(entries):
        position = slots[index] if index < len(slots) else last + index - len(slots) + 1
        item = old_anime.get(entry['anime_id'])
        if item:
            item.position, item.notes = position, entry.get('notes', '')
            updates.append(item)
        else:
            additions.append(PlaylistItem(playlist=playlist, anime_id=entry['anime_id'], position=position, notes=entry.get('notes', '')))
    playlist.items.filter(anime_id__isnull=False).exclude(anime_id__in=ids).delete()
    if updates:
        PlaylistItem.objects.bulk_update(updates, ['position', 'notes'], batch_size=500)
    if additions:
        PlaylistItem.objects.bulk_create(additions, batch_size=500)
    playlist.recalculate_total_duration()
    playlist._prefetched_objects_cache = {}


def append_anime_items(playlist, anime_ids, notes=''):
    known = set(playlist.items.filter(anime_id__isnull=False).values_list('anime_id', flat=True))
    requested = list(dict.fromkeys(anime_ids))
    found = set(Anime.objects.filter(pk__in=requested).values_list('pk', flat=True))
    position = max(playlist.items.values_list('position', flat=True), default=0)
    additions, skipped = [], []
    for anime_id in requested:
        if anime_id not in found:
            skipped.append({'anime_id': anime_id, 'reason': 'Аниме не найдено'})
        elif anime_id in known:
            skipped.append({'anime_id': anime_id, 'reason': 'Уже в плейлисте'})
        else:
            position += 1
            additions.append(PlaylistItem(playlist=playlist, anime_id=anime_id, position=position, notes=notes))
    if additions:
        PlaylistItem.objects.bulk_create(additions, batch_size=500)
        playlist.recalculate_total_duration()
    playlist._prefetched_objects_cache = {}
    return list(PlaylistItem.objects.filter(playlist=playlist, anime_id__in=[item.anime_id for item in additions]).select_related('anime')), skipped


@transaction.atomic
def set_anime_favorites(user, anime_ids, is_favorite):
    from apps.users.models import UserLibrary

    requested_ids = list(dict.fromkeys(int(anime_id) for anime_id in anime_ids))
    existing_ids = set(
        Anime.objects.filter(pk__in=requested_ids).values_list('pk', flat=True)
    )
    anime_ids = [anime_id for anime_id in requested_ids if anime_id in existing_ids]
    if not anime_ids:
        return []

    if is_favorite:
        FavoriteAnime.objects.bulk_create(
            [FavoriteAnime(user=user, anime_id=anime_id) for anime_id in anime_ids],
            ignore_conflicts=True,
            batch_size=500,
        )
        UserLibrary.objects.bulk_create(
            [
                UserLibrary(
                    user=user,
                    anime_id=anime_id,
                    status='planned',
                    is_favorite=True,
                )
                for anime_id in anime_ids
            ],
            ignore_conflicts=True,
            batch_size=500,
        )
        UserLibrary.objects.filter(user=user, anime_id__in=anime_ids).update(
            is_favorite=True,
            updated_at=timezone.now(),
        )
    else:
        FavoriteAnime.objects.filter(user=user, anime_id__in=anime_ids).delete()
        UserLibrary.objects.filter(user=user, anime_id__in=anime_ids).update(
            is_favorite=False,
            updated_at=timezone.now(),
        )

    return anime_ids
