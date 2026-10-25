from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class LibraryPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100


def _serialize_library_item(item):
    anime = item.anime
    poster_url = None
    try:
        if anime.poster and hasattr(anime.poster, 'url'):
            poster_url = anime.poster.url
    except Exception:
        pass
    if not poster_url:
        poster_url = getattr(anime, 'poster_url', None)
    total_episodes = anime.progress_total or anime.episodes or 0
    return {
        'item_type': 'anime',
        'id': item.id,
        'anime': anime.id,
        'anime_id': anime.id,
        'anime_slug': anime.slug,
        'anime_title_ru': anime.title_ru or '',
        'anime_title_en': anime.title_en or '',
        'anime_poster': poster_url,
        'anime_episodes_count': total_episodes,
        'anime_status_display': anime.get_status_display() if hasattr(anime, 'get_status_display') else anime.status,
        'anime_status': anime.status or '',
        'anime_kind': anime.kind or '',
        'anime_year': anime.year,
        'anime_score': anime.score,
        'anime_genres': anime.genres if isinstance(anime.genres, list) else [],
        'anime_episode_duration': anime.episode_duration or None,
        'anime_total_duration': anime.total_duration or None,
        'status': item.status,
        'current_season': item.current_season or 1,
        'current_episode': item.current_episode or 0,
        'episodes_watched': item.effective_episodes_watched,
        'progress_percentage': item.get_progress_percentage() if hasattr(item, 'get_progress_percentage') else (round((item.current_episode / total_episodes) * 100, 1) if total_episodes > 0 else 0),
        'is_favorite': item.is_favorite,
        'rating': item.rating,
        'notes': item.notes or '',
        'added_at': item.added_at.isoformat() if item.added_at else None,
        'started_at': item.started_at.isoformat() if item.started_at else None,
        'completed_at': item.completed_at.isoformat() if item.completed_at else None,
        'updated_at': item.updated_at.isoformat() if item.updated_at else None,
        'rewatch_count': item.rewatch_count or 0,
    }


class UserFavoritesViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def list(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=404)
        else:
            target_user = request.user
        
        queryset = UserLibrary.objects.filter(user=target_user, is_favorite=True).select_related('anime').order_by('-updated_at', '-pk')
        paginator = LibraryPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        results = []
        for item in page:
            anime = item.anime
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
            results.append({
                'id': item.id,
                'anime': anime.id,
                'anime_id': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'anime_episodes': anime.episodes or 0,
                'anime_kind': anime.kind or '',
                'anime_year': anime.year,
                'anime_score': anime.score,
                'anime_status': anime.status or '',
                'anime_genres': anime.genres if isinstance(anime.genres, list) else [],
                'added_at': item.updated_at.isoformat() if item.updated_at else None,
            })
        
        return paginator.get_paginated_response(results)

    def create(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        from apps.anime.infrastructure.models.anime import Anime
        from apps.playlists.application import set_anime_favorites
        
        anime_id = request.data.get('anime')
        if not anime_id:
            return Response({'error': 'anime is required'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        set_anime_favorites(request.user, [anime.pk], True)
        lib = UserLibrary.objects.get(user=request.user, anime=anime)
        
        return Response({
            'id': lib.id,
            'anime': anime.id,
            'message': 'Добавлено в избранное',
        }, status=201)

    def destroy(self, request, pk=None):
        from apps.users.infrastructure.models.users import UserLibrary
        from apps.playlists.application import set_anime_favorites
        
        if pk:
            try:
                item = UserLibrary.objects.get(id=pk, user=request.user)
                set_anime_favorites(request.user, [item.anime_id], False)
                return Response({'success': True, 'message': 'Удалено из избранного'})
            except UserLibrary.DoesNotExist:
                return Response({'error': 'Запись не найдена'}, status=404)
        else:
            anime_id = request.data.get('anime')
            if not anime_id:
                return Response({'error': 'anime_id required'}, status=400)
            
            if UserLibrary.objects.filter(user=request.user, anime_id=anime_id).exists():
                set_anime_favorites(request.user, [anime_id], False)
                return Response({'success': True, 'message': 'Удалено из избранного'})
            return Response({'error': 'Запись не найдена'}, status=404)


class FavoriteThemesViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        from apps.users.infrastructure.models.users import FavoriteTheme
        
        queryset = FavoriteTheme.objects.filter(user=request.user).select_related('anime').order_by('-added_at', '-pk')
        paginator = LibraryPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        results = []
        for item in page:
            anime = item.anime
            results.append({
                'id': item.id,
                'anime': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'theme_type': item.theme_type,
                'theme_type_display': item.get_theme_type_display(),
                'episode': item.episode,
                'season': item.season,
                'title': item.title or '',
                'start_time': item.start_time,
                'end_time': item.end_time,
                'added_at': item.added_at.isoformat() if item.added_at else None,
            })
        
        return paginator.get_paginated_response(results)

    def create(self, request):
        from apps.users.infrastructure.models.users import FavoriteTheme
        from apps.anime.infrastructure.models.anime import Anime
        
        anime_id = request.data.get('anime')
        theme_type = request.data.get('theme_type')  
        episode = request.data.get('episode', 1)
        season = request.data.get('season', 1)
        title = request.data.get('title', '')
        start_time = request.data.get('start_time', 0)
        end_time = request.data.get('end_time')
        
        if not anime_id:
            return Response({'error': 'anime is required'}, status=400)
        if theme_type not in ('opening', 'ending'):
            return Response({'error': 'theme_type must be opening or ending'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        existing = FavoriteTheme.objects.filter(
            user=request.user, anime=anime, 
            theme_type=theme_type, episode=episode, season=season
        ).first()
        
        if existing:
            return Response({'error': 'Уже в избранном', 'id': existing.id}, status=400)
        
        theme = FavoriteTheme.objects.create(
            user=request.user,
            anime=anime,
            theme_type=theme_type,
            episode=episode,
            season=season,
            title=title,
            start_time=start_time,
            end_time=end_time,
        )
        
        return Response({
            'id': theme.id,
            'anime': anime.id,
            'theme_type': theme.theme_type,
            'message': 'Добавлено в избранное',
        }, status=201)

    def destroy(self, request, pk=None):
        from apps.users.infrastructure.models.users import FavoriteTheme
        
        if pk:
            try:
                item = FavoriteTheme.objects.get(id=pk, user=request.user)
                item.delete()
                return Response({'success': True, 'message': 'Удалено из избранного'})
            except FavoriteTheme.DoesNotExist:
                return Response({'error': 'Запись не найдена'}, status=404)
        else:
            anime_id = request.data.get('anime')
            theme_type = request.data.get('theme_type')
            episode = request.data.get('episode')
            season = request.data.get('season', 1)
            
            if not anime_id or not theme_type or not episode:
                return Response({'error': 'anime, theme_type, episode required'}, status=400)
            
            deleted, _ = FavoriteTheme.objects.filter(
                user=request.user, anime_id=anime_id,
                theme_type=theme_type, episode=episode, season=season
            ).delete()
            
            if deleted:
                return Response({'success': True, 'message': 'Удалено из избранного'})
            return Response({'error': 'Запись не найдена'}, status=404)


class FavoriteEpisodesViewSet(viewsets.GenericViewSet,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        from apps.users.infrastructure.models.users import FavoriteEpisode
        
        queryset = FavoriteEpisode.objects.filter(user=request.user).select_related('anime').order_by('-added_at', '-pk')
        paginator = LibraryPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        results = []
        for item in page:
            anime = item.anime
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
            results.append({
                'id': item.id,
                'anime': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'episode': item.episode,
                'season': item.season,
                'note': item.note or '',
                'added_at': item.added_at.isoformat() if item.added_at else None,
            })
        
        return paginator.get_paginated_response(results)

    def create(self, request):
        from apps.users.infrastructure.models.users import FavoriteEpisode
        from apps.anime.infrastructure.models.anime import Anime
        
        anime_id = request.data.get('anime')
        episode = request.data.get('episode', 1)
        season = request.data.get('season', 1)
        note = request.data.get('note', '')
        
        if not anime_id:
            return Response({'error': 'anime is required'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        existing = FavoriteEpisode.objects.filter(
            user=request.user, anime=anime,
            episode=episode, season=season
        ).first()
        
        if existing:
            return Response({'error': 'Уже в избранном', 'id': existing.id}, status=400)
        
        fav_episode = FavoriteEpisode.objects.create(
            user=request.user,
            anime=anime,
            episode=episode,
            season=season,
            note=note,
        )
        
        return Response({
            'id': fav_episode.id,
            'anime': anime.id,
            'episode': episode,
            'message': 'Добавлено в избранное',
        }, status=201)

    def destroy(self, request, pk=None):
        from apps.users.infrastructure.models.users import FavoriteEpisode
        
        if pk:
            try:
                item = FavoriteEpisode.objects.get(id=pk, user=request.user)
                item.delete()
                return Response({'success': True, 'message': 'Удалено из избранного'})
            except FavoriteEpisode.DoesNotExist:
                return Response({'error': 'Запись не найдена'}, status=404)
        else:
            anime_id = request.data.get('anime')
            episode = request.data.get('episode')
            season = request.data.get('season', 1)
            
            if not anime_id or not episode:
                return Response({'error': 'anime, episode required'}, status=400)
            
            deleted, _ = FavoriteEpisode.objects.filter(
                user=request.user, anime_id=anime_id,
                episode=episode, season=season
            ).delete()
            
            if deleted:
                return Response({'success': True, 'message': 'Удалено из избранного'})
            return Response({'error': 'Запись не найдена'}, status=404)


class UserLibraryViewSet(viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'statistics']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def _grouped_favorites(self, request, target_user, ordering):
        from apps.anime.application.catalog_visibility import visible_anime
        from apps.anime.infrastructure.models.anime import Franchise
        from apps.anime.presentation.serializers.anime_serializers import (
            FranchiseEntrySerializer,
            FranchiseSerializer,
        )
        from apps.users.infrastructure.models.users import UserLibrary

        allowed_ordering = [
            '-updated_at', 'updated_at', '-added_at', 'added_at', '-rating',
            'rating', '-current_episode', 'current_episode',
            '-anime__total_duration', 'anime__total_duration',
            '-anime__episode_duration', 'anime__episode_duration',
        ]
        if ordering not in allowed_ordering:
            ordering = '-updated_at'
        favorite_items = list(
            UserLibrary.objects.filter(
                user=target_user,
                anime__isnull=False,
                is_favorite=True,
            )
            .select_related('anime__franchise')
            .order_by(ordering, '-pk')
        )
        favorite_ids = {item.anime_id for item in favorite_items}
        franchise_ids = {
            item.anime.franchise_id
            for item in favorite_items
            if item.anime.franchise_id
        }
        entries_by_franchise = {franchise_id: [] for franchise_id in franchise_ids}
        if franchise_ids:
            for anime in (
                visible_anime()
                .filter(franchise_id__in=franchise_ids)
                .select_related('franchise')
                .order_by('franchise_id', 'franchise_order', 'year', 'pk')
            ):
                entries_by_franchise[anime.franchise_id].append(anime)
        complete_franchises = {
            franchise_id
            for franchise_id, entries in entries_by_franchise.items()
            if entries and {entry.pk for entry in entries}.issubset(favorite_ids)
        }
        franchises = Franchise.objects.in_bulk(complete_franchises)
        emitted_franchises = set()
        projected = []
        search = (request.query_params.get('search') or '').strip().casefold()

        for item in favorite_items:
            franchise_id = item.anime.franchise_id
            franchise_entries = entries_by_franchise.get(franchise_id, [])
            visible_entry_ids = {entry.pk for entry in franchise_entries}
            if (
                franchise_id in complete_franchises
                and item.anime_id in visible_entry_ids
            ):
                if franchise_id in emitted_franchises:
                    continue
                emitted_franchises.add(franchise_id)
                franchise = franchises[franchise_id]
                if search and not any(
                    search in value.casefold()
                    for value in [
                        franchise.name or '',
                        *(entry.title_ru or '' for entry in franchise_entries),
                        *(entry.title_en or '' for entry in franchise_entries),
                    ]
                ):
                    continue
                franchise_data = FranchiseSerializer(
                    franchise,
                    context={'entries_by_franchise': {franchise_id: franchise_entries}},
                ).data
                franchise_data['entries'] = FranchiseEntrySerializer(
                    franchise_entries,
                    many=True,
                ).data
                franchise_data['is_favorite'] = True
                projected.append({
                    'item_type': 'franchise',
                    'id': franchise.pk,
                    'franchise_id': franchise.pk,
                    'anime_ids': [entry.pk for entry in franchise_entries],
                    'franchise': franchise_data,
                })
                continue

            if search and search not in (item.anime.title_ru or '').casefold() and search not in (item.anime.title_en or '').casefold():
                continue
            projected.append(_serialize_library_item(item))

        paginator = LibraryPagination()
        page = paginator.paginate_queryset(projected, request)
        return paginator.get_paginated_response(page)

    def list(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        
        user_id = request.query_params.get('user_id')
        target_user = request.user
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=404)

        is_favorite = request.query_params.get('is_favorite')
        group_franchises = request.query_params.get('group_franchises') in ('true', '1', 'True')
        ordering = request.query_params.get('ordering', '-updated_at')
        if is_favorite in ('true', '1', 'True') and group_franchises:
            return self._grouped_favorites(request, target_user, ordering)

        queryset = UserLibrary.objects.filter(
            user=target_user,
            anime__isnull=False
        ).select_related('anime')
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if is_favorite in ('true', '1', 'True'):
            queryset = queryset.filter(is_favorite=True)
        
        search = request.query_params.get('search')
        if search:
            search_lower = search.lower()
            queryset = queryset.filter(
                Q(anime__title_ru__icontains=search_lower) |
                Q(anime__title_en__icontains=search_lower)
            )
        
        allowed_ordering = ['-updated_at', 'updated_at', '-added_at', 'added_at', '-rating', 'rating', '-current_episode', 'current_episode', '-anime__total_duration', 'anime__total_duration', '-anime__episode_duration', 'anime__episode_duration']
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering, '-pk')

        paginator = LibraryPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        results = []
        for item in page:
            if item.anime:
                results.append(_serialize_library_item(item))
        
        return paginator.get_paginated_response(results)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        from apps.users.infrastructure.models.users import UserLibrary
        from django.db.models import Avg, Sum, Count
        
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=404)
        else:
            user = request.user
        
        if not user or (not user.is_authenticated and not user_id):
            return Response({'error': 'Требуется авторизация'}, status=401)
        
        all_items = UserLibrary.objects.filter(
            user=user, 
            anime__isnull=False
        ).select_related('anime').only(
            'id', 'status', 'current_episode', 'episodes_watched',
            'anime__id', 'anime__episodes', 'anime__progress_total',
            'anime__episode_duration', 'anime__kind'
        )
        
        total = 0
        started = 0
        completed = 0
        on_hold = 0
        dropped = 0
        planned = 0
        favorites = 0
        total_episodes_watched = 0
        total_minutes_watched = 0
        remaining_minutes = 0
        
        for item in all_items:
            total += 1
            
            if item.status == 'started':
                started += 1
            elif item.status == 'completed':
                completed += 1
            elif item.status == 'on_hold':
                on_hold += 1
            elif item.status == 'dropped':
                dropped += 1
            elif item.status == 'planned':
                planned += 1
            
            if item.is_favorite:
                favorites += 1
            
            try:
                anime = item.anime
                if not anime:
                    continue
                    
                if anime.episode_duration:
                    episode_duration = anime.episode_duration
                else:
                    episode_duration = 60 if anime.kind == 'movie' else 24
                
                watched_eps = item.effective_episodes_watched
                
                total_episodes_watched += watched_eps
                
                if item.status in ('started', 'completed') and watched_eps > 0:
                    total_minutes_watched += watched_eps * episode_duration
                
                total_eps = anime.progress_total or anime.episodes or 0
                if item.status == 'started' and total_eps > 0:
                    remaining_eps = total_eps - watched_eps
                    if remaining_eps > 0:
                        remaining_minutes += remaining_eps * episode_duration
                        
            except Exception as e:
                logger.warning(f"Error processing item {item.id}: {e}")
                continue
        
        hours_watched = round(total_minutes_watched / 60, 1)
        hours_remaining = round(remaining_minutes / 60, 1)
        
        return Response({
            'total': total,
            'started': started,
            'completed': completed,
            'on_hold': on_hold,
            'dropped': dropped,
            'planned': planned,
            'favorites': favorites,
            'episodes_watched': total_episodes_watched,
            'hours_watched': hours_watched,
            'hours_remaining': hours_remaining,
            'avg_rating': None,
            'total_rewatches': 0,
        })

    @action(detail=False, methods=['get'])
    def check_anime(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'anime_id is required'}, status=400)
        
        try:
            item = UserLibrary.objects.get(user=request.user, anime_id=anime_id)
            return Response({
                'in_library': True,
                'status': item.status,
                'current_season': item.current_season or 1,
                'current_episode': item.current_episode,
                'watched_episodes': item.effective_episodes_watched,
                'is_favorite': item.is_favorite,
                'rating': item.rating,
            })
        except UserLibrary.DoesNotExist:
            return Response({'in_library': False})

    def destroy(self, request, pk=None):
        from apps.users.infrastructure.models.users import UserLibrary
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.get(id=pk)
            if item.user != request.user:
                return Response({'error': 'Нет прав'}, status=403)
            item.delete()
            return Response({'success': True, 'message': 'Аниме удалено из библиотеки'})
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)

    def retrieve(self, request, pk=None):
        from apps.users.infrastructure.models.users import UserLibrary
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.select_related('anime').get(id=pk)
            
            if item.user != request.user:
                anime = item.anime
                total_episodes = anime.progress_total or anime.episodes or 0
                
                poster_url = None
                try:
                    if anime.poster and hasattr(anime.poster, 'url'):
                        poster_url = anime.poster.url
                except Exception:
                    pass
                if not poster_url:
                    poster_url = getattr(anime, 'poster_url', None)
                
                return Response({
                    'id': item.id,
                    'anime': anime.id,
                    'anime_id': anime.id,
                    'anime_title_ru': anime.title_ru or '',
                    'anime_title_en': anime.title_en or '',
                    'anime_poster': poster_url,
                    'anime_episodes_count': total_episodes,
                    'anime_status_display': anime.get_status_display() if hasattr(anime, 'get_status_display') else anime.status,
                    'status': item.status,
                    'current_season': item.current_season or 1,
                    'current_episode': item.current_episode or 0,
                    'episodes_watched': item.effective_episodes_watched,
                    'real_episodes_watched': item.real_episodes_watched or 0,
                    'progress_percentage': item.get_progress_percentage() if hasattr(item, 'get_progress_percentage') else 0,
                    'is_favorite': item.is_favorite,
                    'rating': item.rating,
                })
            
            anime = item.anime
            total_episodes = anime.progress_total or anime.episodes or 0
            
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
            return Response({
                'id': item.id,
                'anime': anime.id,
                'anime_id': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'anime_episodes_count': total_episodes,
                'anime_status_display': anime.get_status_display() if hasattr(anime, 'get_status_display') else anime.status,
                'status': item.status,
                'current_season': item.current_season or 1,
                'current_episode': item.current_episode or 0,
                'episodes_watched': item.effective_episodes_watched,
                'real_episodes_watched': item.real_episodes_watched or 0,
                'progress_percentage': item.get_progress_percentage() if hasattr(item, 'get_progress_percentage') else 0,
                'is_favorite': item.is_favorite,
                'rating': item.rating,
                'notes': item.notes or '',
                'added_at': item.added_at.isoformat() if item.added_at else None,
                'started_at': item.started_at.isoformat() if item.started_at else None,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                'rewatch_count': item.rewatch_count or 0,
            })
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)

    def partial_update(self, request, pk=None):
        from apps.users.infrastructure.models.users import UserLibrary
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.get(id=pk)
            if item.user != request.user:
                return Response({'error': 'Нет прав'}, status=403)
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)
        
        status = request.data.get('status')
        current_season = request.data.get('current_season')
        current_episode = request.data.get('current_episode')
        episodes_watched = request.data.get('episodes_watched')
        rating = request.data.get('rating')
        notes = request.data.get('notes')
        is_favorite = request.data.get('is_favorite')
        
        if status is not None:
            item.status = status
            item.user_set_status = True
            if status == 'started' and not item.started_at:
                item.started_at = timezone.now()
            elif status == 'completed' and not item.completed_at:
                item.completed_at = timezone.now()
        
        if current_season is not None:
            item.current_season = current_season
        if current_episode is not None:
            item.current_episode = current_episode
        
        if rating is not None:
            item.rating = rating if 1 <= rating <= 10 else None
        
        if notes is not None:
            item.notes = notes
        
        if is_favorite is not None:
            from apps.playlists.application import set_anime_favorites
            set_anime_favorites(request.user, [item.anime_id], bool(is_favorite))
            item.is_favorite = bool(is_favorite)
        
        item.save()

        if episodes_watched is not None:
            try:
                from apps.users.application.library_episodes import set_watched_progress
                set_watched_progress(
                    request.user, item.anime, episodes_watched,
                    season=item.current_season or 1,
                )
            except (TypeError, ValueError):
                return Response({'error': 'Некорректное количество серий'}, status=400)
        
        return self.retrieve(request, pk)

    @action(detail=True, methods=['post'])
    def mark_favorite(self, request, pk=None):
        from apps.users.infrastructure.models.users import UserLibrary
        from apps.playlists.application import set_anime_favorites
        
        try:
            item = UserLibrary.objects.get(id=pk)
            if item.user != request.user:
                return Response({'error': 'Нет прав'}, status=403)
                
            is_favorite = not item.is_favorite
            set_anime_favorites(request.user, [item.anime_id], is_favorite)
            item.refresh_from_db(fields=['is_favorite', 'updated_at'])
            
            return Response({
                'is_favorite': item.is_favorite,
                'message': 'Добавлено в избранное' if item.is_favorite else 'Убрано из избранного'
            })
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)

    def create(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        from apps.anime.infrastructure.models.anime import Anime
        
        anime_id = request.data.get('anime')
        status = request.data.get('status', 'planned')
        current_season = request.data.get('current_season', 1)
        current_episode = request.data.get('current_episode', 0)
        progress_supplied = 'episodes_watched' in request.data
        rating = request.data.get('rating')
        notes = request.data.get('notes', '')
        
        if not anime_id:
            return Response({'error': 'anime_id is required'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        item, created = UserLibrary.objects.get_or_create(
            user=request.user,
            anime=anime,
            defaults={
                'status': status,
                'user_set_status': True,
                'current_season': current_season,
                'current_episode': current_episode,
                'rating': rating,
                'notes': notes,
            }
        )
        
        if not created:
            if status:
                item.status = status
                item.user_set_status = True
            if rating:
                item.rating = rating
            if notes:
                item.notes = notes
            if current_season:
                item.current_season = current_season
            item.save()

        if progress_supplied:
            try:
                from apps.users.application.library_episodes import set_watched_progress
                explicit_progress = request.data.get('episodes_watched', current_episode)
                set_watched_progress(
                    request.user, anime, explicit_progress,
                    season=current_season or 1,
                )
                item.refresh_from_db()
            except (TypeError, ValueError):
                return Response({'error': 'Некорректное количество серий'}, status=400)
        
        return Response({
            'id': item.id,
            'anime_id': anime.id,
            'status': item.status,
            'message': 'Добавлено в библиотеку' if created else 'Обновлено',
        }, status=201 if created else 200)


from collections import Counter
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()


class UserWrappedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id = request.query_params.get("user_id")
        if user_id:
            try:
                target_user = User.objects.get(pk=int(user_id))
            except (ValueError, User.DoesNotExist):
                return Response({"error": "Пользователь не найден"}, status=404)
        elif request.user.is_authenticated:
            target_user = request.user
        else:
            return Response({"error": "Требуется авторизация или параметр user_id"}, status=401)

        library = UserLibrary.objects.filter(user=target_user, anime__isnull=False).select_related('anime')
        status_counts = {}
        for item in library:
            status_counts[item.status] = status_counts.get(item.status, 0) + 1

        genre_counter = Counter()
        for item in library:
            if item.status not in ('started', 'completed', 'watching', 'rewatching'):
                continue
            watched_episodes = item.effective_episodes_watched
            watch_weight = max(int(watched_episodes), 1)
            anime_genres = getattr(item.anime, 'genres', None) or []
            for genre in anime_genres:
                genre_counter[genre] += watch_weight

        total_genres = sum(genre_counter.values()) or 1
        genres = [
            {
                "name": genre,
                "count": count,
                "pct": round((count / total_genres) * 100, 1),
            }
            for genre, count in genre_counter.most_common()
        ]

        return Response({
            'user': {
                'id': target_user.id,
                'username': target_user.username,
                'display_name': getattr(target_user, 'display_name', target_user.username),
            },
            'counts': {
                'total': library.count(),
                'started': status_counts.get('watching', 0) + status_counts.get('rewatching', 0),
                'completed': status_counts.get('completed', 0),
                'on_hold': status_counts.get('on_hold', 0),
                'dropped': status_counts.get('dropped', 0),
                'planned': status_counts.get('planned', 0),
                'favorites': status_counts.get('favorite', 0),
            },
            'episodes_watched': sum(item.effective_episodes_watched for item in library),
            'hours_watched': sum(item.effective_episodes_watched * 0.5 for item in library),
            'ratings_given': sum(1 for item in library if item.rating is not None),
            'avg_rating': None,
            'rewatches': 0,
            'genres': genres,
            'studios': [],
            'decades': [],
            'kinds': [],
            'top_rated': [],
            'franchises': [],
            'portrait': [],
        })
