from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.db.models import Q, Count, Max
from rest_framework.pagination import PageNumberPagination
from apps.playlists.infrastructure.models.playlists import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist, PlaylistShareLink
from apps.playlists.presentation.serializers.playlists_serializers import (
    PlaylistSerializer, PlaylistCreateSerializer, PlaylistUpdateSerializer,
    PlaylistItemSerializer, PlaylistItemCreateSerializer, PlaylistItemUpdateSerializer,
    ReorderItemsSerializer,
    FavoriteAnimeSerializer, FavoritePlaylistSerializer,
    AddToPlaylistSerializer
)
import re
from rest_framework.exceptions import PermissionDenied
from django.utils.cache import patch_vary_headers
from apps.playlists.models import PlaylistLike, PlaylistTopic
from apps.playlists.presentation.discovery import playlist_cards, discover
from apps.playlists.topics import TOPICS, TOPIC_GROUPS
from apps.playlists.application import append_anime_items, set_anime_favorites
from apps.anime.infrastructure.models.anime import Anime, Franchise


def parse_anime_link(url):
    patterns = {
        'jut.su': r'jut\.su/([^/]+)/?',
        'animego.org': r'animego\.org/anime/([^/]+)',
        'sovetromantica.com': r'sovetromantica\.com/anime/([^/]+)',
        'anilibria.tv': r'anilibria\.tv/release/([^/]+)',
    }
    for site, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            title_slug = match.group(1)
            anime = Anime.objects.filter(slug__icontains=title_slug).first() or \
                    Anime.objects.filter(title_ru__icontains=title_slug.replace('-', ' ')).first() or \
                    Anime.objects.filter(title_en__icontains=title_slug.replace('-', ' ')).first()
            return anime
    url_lower = url.lower()
    for word in ['anime', 'season', 'series']:
        if word in url_lower:
            for part in reversed(url.split('/')):
                if part and len(part) > 3:
                    anime = Anime.objects.filter(title_ru__icontains=part.replace('-', ' ')).first() or \
                            Anime.objects.filter(title_en__icontains=part.replace('-', ' ')).first()
                    if anime:
                        return anime
    return None


class StandardPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        patch_vary_headers(response, ['Authorization', 'Cookie'])
        return response

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def counts(self, request):
        mine = Playlist.objects.filter(user=request.user).aggregate(
            all=Count('pk'), public=Count('pk', filter=Q(visibility='public')),
            private=Count('pk', filter=Q(visibility='private')), link=Count('pk', filter=Q(visibility='link')))
        mine['favorites'] = FavoritePlaylist.objects.filter(user=request.user).filter(
            Q(playlist__visibility='public') | Q(playlist__user=request.user)).count()
        return Response(mine)

    def get_serializer_class(self):
        if self.action == 'create':
            return PlaylistCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlaylistUpdateSerializer
        return PlaylistSerializer

    def _get_user_library_cache(self, anime_ids):
        request = self.request
        if not request or not request.user.is_authenticated:
            return {}
        try:
            from apps.users.infrastructure.models.users import UserLibrary
            libs = UserLibrary.objects.filter(
                user=request.user,
                anime_id__in=anime_ids
            )
            return {lib.anime_id: lib for lib in libs}
        except Exception:
            return {}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        include_items = self.request.query_params.get('include_items') == 'true'
        context['include_items'] = include_items
        if self.action == 'retrieve' and include_items and self.kwargs.get('pk'):
            try:
                anime_ids = list(
                    PlaylistItem.objects.filter(
                        playlist_id=self.kwargs.get('pk'),
                        anime_id__isnull=False,
                    )
                    .values_list('anime_id', flat=True)
                )
                cache = self._get_user_library_cache(anime_ids) if anime_ids else {}
                context['user_library_cache'] = cache
            except Exception:
                pass
        return context

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'public', 'discovery_options', 'get_items'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        with transaction.atomic():
            locked = get_object_or_404(Playlist.objects.select_for_update(), pk=serializer.instance.pk)
            if locked.user_id != self.request.user.pk:
                raise PermissionDenied('Редактировать плейлист может только автор')
            serializer.instance = locked
            serializer.save()

    @action(detail=True, methods=['put', 'delete'], url_path='like')
    def like(self, request, pk=None):
        with transaction.atomic():
            playlist = get_object_or_404(Playlist.objects.select_for_update().only('pk', 'visibility'), pk=pk, visibility='public')
            if request.method == 'PUT':
                PlaylistLike.objects.get_or_create(user=request.user, playlist=playlist)
            else:
                PlaylistLike.objects.filter(user=request.user, playlist=playlist).delete()
            return Response({
                'is_liked': request.method == 'PUT',
                'likes_count': PlaylistLike.objects.filter(playlist=playlist).count(),
            })

    @action(detail=False, methods=['get'], url_path='discovery-options')
    def discovery_options(self, request):
        if request.query_params.get('topics_only') == 'true':
            return Response({'topics': TOPICS, 'topic_groups': TOPIC_GROUPS, 'genres': []})
        genres = set()
        rows = Anime.objects.filter(playlistitem__playlist__visibility='public').values_list('genres', flat=True).distinct()
        for values in rows.iterator():
            genres.update(g for g in (values or []) if isinstance(g, str))
        return Response({'topics': TOPICS, 'topic_groups': TOPIC_GROUPS, 'genres': sorted(genres)})

    def get_queryset(self):
        if self.action not in ('list', 'public', 'retrieve', 'my'):
            queryset = Playlist.objects.select_related('user')
        else:
            include_items = self.action == 'retrieve' and self.request.query_params.get('include_items') == 'true'
            queryset = playlist_cards(self.request.user, compact=not include_items)
        user = self.request.user

        if self.action == 'public':
            return self._apply_common_filters(queryset.filter(visibility='public'))

        if self.action == 'list':
            if self.request.query_params.get('is_public') in ('true', '1', 'True'):
                return self._apply_common_filters(queryset.filter(visibility='public'))
            my = self.request.query_params.get('my')
            if my in ('true', '1', 'True'):
                if not user.is_authenticated:
                    return Playlist.objects.none()
                queryset = queryset.filter(user=user)
                visibility = self.request.query_params.get('visibility')
                if visibility in ('public', 'private', 'link'):
                    queryset = queryset.filter(visibility=visibility)
                return self._apply_common_filters(queryset)

            favorites = self.request.query_params.get('favorites')
            if favorites in ('true', '1', 'True'):
                if not user.is_authenticated:
                    return Playlist.objects.none()
                fav_ids = FavoritePlaylist.objects.filter(user=user).values_list('playlist_id', flat=True)
                queryset = queryset.filter(id__in=fav_ids).filter(Q(visibility='public') | Q(user=user))
                return self._apply_common_filters(queryset)

            user_id = self.request.query_params.get('user')
            if user_id:
                try:
                    target_user_id = int(user_id)
                except (ValueError, TypeError):
                    return Playlist.objects.none()
                
                visibility = self.request.query_params.get('visibility')
                
                if user.is_authenticated and user.id == target_user_id:
                    queryset = queryset.filter(user_id=target_user_id)
                    if visibility in ('public', 'private', 'link'):
                        queryset = queryset.filter(visibility=visibility)
                else:
                    queryset = queryset.filter(
                        user_id=target_user_id,
                        visibility='public'
                    )
                
                return self._apply_common_filters(queryset)

            is_public = self.request.query_params.get('is_public')
            if is_public in ('true', '1', 'True'):
                queryset = queryset.filter(visibility='public')
                return self._apply_common_filters(queryset)

            if user.is_authenticated:
                queryset = queryset.filter(
                    Q(visibility='public') | Q(user=user)
                ).distinct()
            else:
                queryset = queryset.filter(visibility='public')

        if self.action != 'list':
            queryset = queryset.filter(Q(visibility='public') | Q(user=user)) if user.is_authenticated else queryset.filter(visibility='public')
        return self._apply_common_filters(queryset)

    def _apply_common_filters(self, queryset):
        return discover(queryset, self.request.query_params)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        playlist.invalidate_share_links()
        if playlist.cover_image:
            try:
                playlist.cover_image.delete()
            except Exception:
                pass
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my(self, request):
        playlists = self._apply_common_filters(
            playlist_cards(request.user, compact=True).filter(user=request.user)
        )
        page = self.paginate_queryset(playlists)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def public(self, request):
        playlists = self.get_queryset()
        page = self.paginate_queryset(playlists)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(playlists, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['post'], url_path='share-link')
    def generate_share_link(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)

        ttl_days = int(request.data.get('ttl_days', 30))
        playlist.invalidate_share_links()
        link = playlist.get_or_create_share_link(ttl_days=ttl_days)

        return Response({
            'token': link.token,
            'expires_at': link.expires_at,
            'share_url': f"{request.build_absolute_uri('/').rstrip('/')}/playlist/shared/{link.token}",
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='share-link')
    def revoke_share_link(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        playlist.invalidate_share_links()
        return Response({'message': 'Ссылка деактивирована'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='update-visibility')
    @transaction.atomic
    def update_visibility(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)

        visibility = request.data.get('visibility')
        if visibility not in ('public', 'private', 'link'):
            return Response({'error': 'Допустимые значения: public, private, link'}, status=status.HTTP_400_BAD_REQUEST)

        playlist = Playlist.objects.select_for_update().get(pk=playlist.pk)
        old = playlist.visibility
        playlist.visibility = visibility
        playlist.save(update_fields=['visibility'])

        if visibility == 'link' and old != 'link':
            playlist.get_or_create_share_link()
        elif old == 'link' and visibility != 'link':
            playlist.invalidate_share_links()

        serializer = self.get_serializer(playlist)
        return Response(serializer.data)


    @action(detail=True, methods=['post'])
    def update_cover(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        
        if 'cover_image' in request.FILES:
            playlist.cover_image = request.FILES['cover_image']
            playlist.cover_mode = 'custom'
            playlist.save(update_fields=['cover_image', 'cover_mode', 'updated_at'])
            return Response(self.get_serializer(playlist).data)
        
        playlist.cover_mode = 'auto'
        playlist.save(update_fields=['cover_mode', 'updated_at'])
        return Response(self.get_serializer(playlist).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def add_item(self, request, pk=None):
        from apps.anime.infrastructure.models.anime import Franchise, Anime as AnimeModel
        
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        playlist = Playlist.objects.select_for_update().get(pk=playlist.pk)
        serializer = PlaylistItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            anime_id = serializer.validated_data.get('anime_id')
            nested_playlist_id = serializer.validated_data.get('nested_playlist_id')
            franchise_id = serializer.validated_data.get('franchise_id')
            
            if franchise_id:
                try:
                    franchise = Franchise.objects.get(id=franchise_id)
                    anime_list = AnimeModel.objects.filter(franchise=franchise).order_by('franchise_order')
                    
                    added, _ = append_anime_items(playlist, list(anime_list.values_list('pk', flat=True)), notes=f"Из франшизы: {franchise.name}")
                    added_count = len(added)
                    return Response({
                        'message': f'Добавлено {added_count} аниме из франшизы {franchise.name}',
                        'added_count': added_count
                    }, status=status.HTTP_201_CREATED)
                except Franchise.DoesNotExist:
                    return Response({'error': 'Франшиза не найдена'}, status=status.HTTP_404_NOT_FOUND)
            
            if anime_id and PlaylistItem.objects.filter(playlist=playlist, anime_id=anime_id).exists():
                return Response({'error': 'Аниме уже есть в плейлисте'}, status=status.HTTP_400_BAD_REQUEST)
            if nested_playlist_id:
                if nested_playlist_id == playlist.id:
                    return Response({'error': 'Нельзя добавить плейлист самого в себя'}, status=status.HTTP_400_BAD_REQUEST)
                if PlaylistItem.objects.filter(playlist=playlist, nested_playlist_id=nested_playlist_id).exists():
                    return Response({'error': 'Плейлист уже добавлен'}, status=status.HTTP_400_BAD_REQUEST)
            
            item = serializer.save(playlist=playlist)
            cache = self._get_user_library_cache([item.anime_id]) if item.anime_id else {}
            return Response(PlaylistItemSerializer(item, context={'request': request, 'user_library_cache': cache}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='batch-add-items')
    @transaction.atomic
    def batch_add_items(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user_id != request.user.pk:
            raise PermissionDenied('Нет прав')
        playlist = Playlist.objects.select_for_update().get(pk=playlist.pk)
        anime_ids = request.data.get('anime_ids', [])
        if not isinstance(anime_ids, list) or not anime_ids or len(anime_ids) > 1000 or any(type(value) is not int or value < 1 for value in anime_ids):
            return Response({'error': 'Укажите от 1 до 1000 идентификаторов аниме'}, status=400)
        added, skipped = append_anime_items(playlist, anime_ids)
        return Response({
            'added': PlaylistItemSerializer(added, many=True, context={'request': request, 'user_library_cache': {}}).data,
            'skipped': skipped, 'added_count': len(added), 'skipped_count': len(skipped),
        }, status=201)

    @action(detail=False, methods=['get'], url_path='search-for-nested')
    def search_for_nested(self, request):
        search = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 20))
        
        if not search:
            playlists = Playlist.objects.filter(user=request.user).order_by('-updated_at')[:limit]
        else:
            playlists = Playlist.objects.filter(
                Q(title__icontains=search),
                Q(user=request.user) | Q(visibility='public')
            ).distinct().order_by('-updated_at')[:limit]
        
        from apps.playlists.presentation.serializers.playlists_serializers import NestedPlaylistSerializer
        serializer = NestedPlaylistSerializer(playlists, many=True, context={'request': request})
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })

    @action(detail=True, methods=['post'])
    def add_by_link(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        url = request.data.get('url')
        if not url:
            return Response({'error': 'Не указана ссылка'}, status=status.HTTP_400_BAD_REQUEST)
        anime = parse_anime_link(url)
        if not anime:
            return Response({'error': 'Не удалось распознать аниме по ссылке'}, status=status.HTTP_400_BAD_REQUEST)
        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response({'error': 'Аниме уже есть в плейлисте'}, status=status.HTTP_400_BAD_REQUEST)
        item = PlaylistItem.objects.create(playlist=playlist, anime=anime, notes=request.data.get('notes', ''))
        cache = self._get_user_library_cache([item.anime_id]) if item.anime_id else {}
        return Response(PlaylistItemSerializer(item, context={'request': request, 'user_library_cache': cache}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        playlist = self.get_object()
        anime_id = request.data.get('anime_id')
        item_id = request.data.get('item_id')
        if not anime_id and not item_id:
            return Response({'error': 'Не указан anime_id или item_id'}, status=status.HTTP_400_BAD_REQUEST)
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        try:
            if anime_id:
                item = PlaylistItem.objects.get(playlist=playlist, anime_id=anime_id)
            else:
                item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            item.delete()
            PlaylistItem.objects.filter(playlist=playlist, position__gt=item.position).update(
                position=models.F('position') - 1
            )
            playlist.update_cover()
            playlist.recalculate_total_duration()
            return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)
        except PlaylistItem.DoesNotExist:
            return Response({'error': 'Элемент не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='items')
    def get_items(self, request, pk=None):
        playlist = self.get_object()
        
        user = request.user
        if playlist.user != user and playlist.visibility != 'public':
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        
        items_qs = PlaylistItem.objects.filter(playlist=playlist).select_related('anime').order_by('position', 'added_at')
        
        ordering = request.query_params.get('ordering', 'position')
        allowed_orderings = ['position', '-position', 'added_at', '-added_at', 'anime__title_ru', '-anime__title_ru', 'anime__year', '-anime__year', 'anime__score', '-anime__score']
        if ordering in allowed_orderings:
            items_qs = items_qs.order_by(ordering)
        
        paginator = StandardPagination()
        page = paginator.paginate_queryset(items_qs, request)
        anime_ids = [item.anime_id for item in page if item.anime_id]
        cache = self._get_user_library_cache(anime_ids) if anime_ids else {}
        serializer = PlaylistItemSerializer(page, many=True, context={'request': request, 'user_library_cache': cache})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def reorder_items(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReorderItemsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        requested = serializer.validated_data['items']
        requested_ids = [row['id'] for row in requested]
        if len(requested_ids) != len(set(requested_ids)):
            return Response({'error': 'ID элементов не должны повторяться'}, status=400)
        with transaction.atomic():
            items = {item.id: item for item in PlaylistItem.objects.select_for_update().filter(playlist=playlist, id__in=requested_ids)}
            if set(items) != set(requested_ids):
                return Response({'error': 'Один или несколько элементов не принадлежат плейлисту'}, status=400)
            positions = [row['position'] for row in requested]
            if len(positions) != len(set(positions)):
                return Response({'error': 'Позиции не должны повторяться'}, status=400)
            for row in requested:
                items[row['id']].position = row['position']
            PlaylistItem.objects.bulk_update(items.values(), ['position'])
        playlist.update_cover()
        playlist.recalculate_total_duration()
        return Response({'message': 'Порядок обновлён'})

    @action(detail=True, methods=['post'], url_path='update-item-notes')
    def update_item_notes(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        item_id = request.data.get('item_id')
        notes = request.data.get('notes', '')
        if not item_id:
            return Response({'error': 'Не указан item_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            item.notes = notes
            item.save(update_fields=['notes'])
            cache = self._get_user_library_cache([item.anime_id]) if item.anime_id else {}
            return Response(PlaylistItemSerializer(item, context={'request': request, 'user_library_cache': cache}).data)
        except PlaylistItem.DoesNotExist:
            return Response({'error': 'Элемент не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        playlist = self.get_object()
        favorite, created = FavoritePlaylist.objects.get_or_create(user=request.user, playlist=playlist)
        if created:
            return Response({'message': 'Добавлено в избранное'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Уже в избранном'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def unfavorite(self, request, pk=None):
        playlist = self.get_object()
        deleted, _ = FavoritePlaylist.objects.filter(user=request.user, playlist=playlist).delete()
        if deleted:
            return Response({'message': 'Убрано из избранного'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Не в избранном'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def duplicate(self, request, pk=None):
        original = self.get_object()
        new_playlist = Playlist.objects.create(
            user=request.user,
            title=f"{original.title} (копия)",
            description=original.description,
            visibility='private'
        )
        source_items = list(original.items.all())
        PlaylistItem.objects.bulk_create([
            PlaylistItem(playlist=new_playlist, anime_id=item.anime_id, nested_playlist_id=item.nested_playlist_id,
                         notes=item.notes, position=item.position)
            for item in source_items
        ], batch_size=500)
        new_playlist.topics.set(original.topics.all())
        new_playlist.recalculate_total_duration()
        context = self.get_serializer_context()
        context['user_library_cache'] = self._get_user_library_cache([item.anime_id for item in source_items if item.anime_id])
        new_playlist = playlist_cards(request.user).get(pk=new_playlist.pk)
        return Response(self.get_serializer(new_playlist, context=context).data, status=status.HTTP_201_CREATED)



class PlaylistByShareTokenView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            link = PlaylistShareLink.objects.select_related('playlist__user').get(token=token)
        except PlaylistShareLink.DoesNotExist:
            return Response({'error': 'Ссылка не найдена или недействительна'}, status=status.HTTP_404_NOT_FOUND)

        if not link.is_valid:
            return Response({'error': 'Ссылка истекла или была отозвана'}, status=status.HTTP_410_GONE)

        playlist = link.playlist
        if playlist.visibility == 'private':
            return Response({'error': 'Плейлист недоступен'}, status=status.HTTP_403_FORBIDDEN)

        paginator = StandardPagination()
        items = PlaylistItem.objects.filter(playlist=playlist).select_related('anime').order_by('position', 'added_at')
        page = paginator.paginate_queryset(items, request)
        if paginator.page.number == 1:
            link.touch()
        serializer = PlaylistSerializer(playlist, context={'request': request})
        data = dict(serializer.data)
        data['items'] = PlaylistItemSerializer(page, many=True, context={'request': request}).data
        data['items_next'] = paginator.get_next_link()
        return Response(data)



class AddToPlaylistView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToPlaylistSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        anime_id = data['anime_id']
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)

        playlist_id = data.get('playlist_id')
        new_playlist_title = data.get('new_playlist_title')

        if playlist_id:
            try:
                playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            except Playlist.DoesNotExist:
                return Response({'error': 'Плейлист не найден или нет прав'}, status=status.HTTP_404_NOT_FOUND)
        else:
            visibility = data.get('new_playlist_visibility', 'public')
            playlist = Playlist.objects.create(
                user=request.user,
                title=new_playlist_title,
                description=data.get('new_playlist_description', ''),
                visibility=visibility,
            )
            if visibility == 'link':
                playlist.get_or_create_share_link()

        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response({'error': 'Аниме уже есть в плейлисте'}, status=status.HTTP_400_BAD_REQUEST)

        item = PlaylistItem.objects.create(playlist=playlist, anime=anime, notes=data.get('notes', ''))
        playlist.update_cover()
        return Response({
            'message': 'Добавлено',
            'playlist_id': playlist.id,
            'item_id': item.id
        }, status=status.HTTP_201_CREATED)


class FavoriteAnimeViewSet(viewsets.ModelViewSet):
    queryset = FavoriteAnime.objects.all()
    serializer_class = FavoriteAnimeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return FavoriteAnime.objects.filter(user=self.request.user).select_related('anime').order_by('-created_at', '-pk')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        anime_id = request.data.get('anime')
        if not anime_id:
            return Response({'error': 'Не указан anime'}, status=status.HTTP_400_BAD_REQUEST)
        if not Anime.objects.filter(pk=anime_id).exists():
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)
        existing = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).first()
        set_anime_favorites(request.user, [anime_id], True)
        favorite = FavoriteAnime.objects.select_related('anime').get(
            user=request.user,
            anime_id=anime_id,
        )
        return Response(
            self.get_serializer(favorite).data,
            status=status.HTTP_200_OK if existing else status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        anime_id = request.data.get('anime_id')
        if anime_id:
            if FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).exists():
                set_anime_favorites(request.user, [anime_id], False)
                return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)
        favorite = self.get_object()
        set_anime_favorites(request.user, [favorite.anime_id], False)
        return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def check(self, request):
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'Нет anime_id'}, status=status.HTTP_400_BAD_REQUEST)
        is_favorite = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).exists()
        return Response({'is_favorite': is_favorite})

    @action(detail=False, methods=['get'], url_path='ids')
    def ids(self, request):
        return Response({
            'anime_ids': list(
                FavoriteAnime.objects.filter(user=request.user)
                .order_by('anime_id')
                .values_list('anime_id', flat=True)
            )
        })

    @action(detail=False, methods=['delete'], url_path='remove')
    def remove_favorite(self, request):
        anime_id = request.data.get('anime_id')
        if not anime_id:
            return Response({'error': 'Нет anime_id'}, status=status.HTTP_400_BAD_REQUEST)
        if FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).exists():
            set_anime_favorites(request.user, [anime_id], False)
            return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Не в избранном'}, status=status.HTTP_404_NOT_FOUND)

    @action(
        detail=False,
        methods=['get', 'put', 'delete'],
        url_path=r'franchise/(?P<franchise_id>[^/.]+)',
    )
    def franchise(self, request, franchise_id=None):
        from apps.anime.application.catalog_visibility import visible_anime

        franchises = Franchise.objects.all()
        try:
            franchise = franchises.get(pk=franchise_id)
        except (Franchise.DoesNotExist, ValueError):
            franchise = get_object_or_404(franchises, slug=franchise_id)

        anime_ids = list(
            visible_anime()
            .filter(franchise=franchise)
            .order_by('franchise_order', 'year', 'pk')
            .values_list('pk', flat=True)
        )
        if not anime_ids:
            return Response({'error': 'Во франшизе нет доступных аниме'}, status=404)

        if request.method == 'PUT':
            set_anime_favorites(request.user, anime_ids, True)
        elif request.method == 'DELETE':
            set_anime_favorites(request.user, anime_ids, False)

        favorite_ids = set(
            FavoriteAnime.objects.filter(
                user=request.user,
                anime_id__in=anime_ids,
            ).values_list('anime_id', flat=True)
        )
        return Response({
            'franchise_id': franchise.pk,
            'anime_ids': anime_ids,
            'is_favorite': len(favorite_ids) == len(anime_ids),
            'favorite_anime_ids': sorted(favorite_ids),
        })


class FavoritePlaylistViewSet(viewsets.ModelViewSet):
    queryset = FavoritePlaylist.objects.all()
    serializer_class = FavoritePlaylistSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return FavoritePlaylist.objects.filter(user=self.request.user).filter(
            Q(playlist__visibility='public') | Q(playlist__user=self.request.user)
        ).select_related('playlist__user').prefetch_related(
            'playlist__items__anime', 'playlist__topics', 'playlist__likes', 'playlist__favorited_by'
        ).order_by('-created_at', '-pk')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def all(self, request):
        favorites = self.get_queryset()
        page = self.paginate_queryset(favorites)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class PlaylistItemViewSet(viewsets.ModelViewSet):
    queryset = PlaylistItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return PlaylistItemUpdateSerializer
        return PlaylistItemSerializer

    def get_queryset(self):
        return PlaylistItem.objects.filter(playlist__user=self.request.user).select_related('anime', 'playlist')

    def perform_create(self, serializer):
        playlist_id = self.kwargs.get('playlist_pk')
        if playlist_id:
            playlist = get_object_or_404(Playlist, id=playlist_id)
            if playlist.user != self.request.user:
                raise PermissionError("Нет прав")
            serializer.save(playlist=playlist)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        playlist = item.playlist
        item.delete()
        PlaylistItem.objects.filter(playlist=playlist, position__gt=item.position).update(
            position=models.F('position') - 1
        )
        playlist.update_cover()
        return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)


class PlaylistSearchView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))
        if not search:
            return Response({'results': []})
        queryset = Playlist.objects.filter(
            Q(title__icontains=search) | Q(description__icontains=search),
            visibility='public'
        ).select_related('user').prefetch_related('items__anime')[:limit]
        serializer = PlaylistSerializer(queryset, many=True, context={'request': request})
        return Response({'results': serializer.data, 'count': len(serializer.data)})
