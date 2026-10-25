from datetime import timedelta

from django.db.models import Count, Exists, OuterRef, Prefetch, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.playlists.models import FavoritePlaylist, Playlist, PlaylistItem, PlaylistLike


def count_for(model, **filters):
    rows = model.objects.filter(playlist_id=OuterRef('pk'), **filters).order_by()
    return Coalesce(Subquery(rows.values('playlist_id').annotate(n=Count('pk')).values('n')[:1]), 0)


def playlist_cards(user, compact=False):
    if compact:
        items = PlaylistItem.objects.select_related('anime').only(
            'id', 'playlist_id', 'anime_id', 'position', 'added_at',
            'anime__id', 'anime__poster', 'anime__poster_url').order_by('position', 'added_at')[:3]
        queryset = Playlist.objects.select_related('user').prefetch_related(
            Prefetch('items', queryset=items, to_attr='cover_items'), 'topics')
    else:
        queryset = Playlist.objects.select_related('user').prefetch_related('items__anime', 'topics')
    return queryset.annotate(
        likes_count=count_for(PlaylistLike),
        favorites_count_ann=count_for(FavoritePlaylist),
        items_count_ann=count_for(PlaylistItem),
        is_liked=Exists(PlaylistLike.objects.filter(playlist_id=OuterRef('pk'), user_id=user.pk)) if user.is_authenticated else Value(False),
        is_favorited_ann=Exists(FavoritePlaylist.objects.filter(playlist_id=OuterRef('pk'), user_id=user.pk)) if user.is_authenticated else Value(False),
    )


def discover(queryset, params):
    search = params.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
    for topic in filter(None, params.get('topics', '').split(',')):
        queryset = queryset.filter(topics__slug=topic)
    for genre in filter(None, params.get('genre', '').split(',')):
        queryset = queryset.filter(Exists(PlaylistItem.objects.filter(
            playlist_id=OuterRef('pk'), anime__genres__contains=[genre])))
    if params.get('year'):
        queryset = queryset.filter(Exists(PlaylistItem.objects.filter(
            playlist_id=OuterRef('pk'), anime__year=params['year'])))
    days = {'week': 7, 'month': 30}.get(params.get('period', 'all'))
    if days:
        queryset = queryset.filter(created_at__gte=timezone.now() - timedelta(days=days))
    ordering = params.get('ordering', '-created_at')
    if ordering in ('-likes_count', 'likes_count'):
        queryset = queryset.annotate(period_likes=count_for(PlaylistLike))
        return queryset.order_by('-period_likes' if ordering.startswith('-') else 'period_likes', '-created_at', 'pk')
    aliases = {'items_count': 'items_count_ann', 'favorites_count': 'favorites_count_ann'}
    field = ordering.lstrip('-')
    if field not in ('created_at', 'updated_at', 'title', *aliases):
        ordering = '-created_at'
    else:
        ordering = ('-' if ordering.startswith('-') else '') + aliases.get(field, field)
    return queryset.order_by(ordering, 'pk')
