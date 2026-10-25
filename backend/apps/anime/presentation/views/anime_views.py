from asyncio.log import logger
from urllib.parse import urlparse, quote_plus

from django.conf import settings
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseServerError,
)
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from apps.anime.application.cache_utils import safe_cache_get, safe_cache_set
from django.views.decorators.cache import cache_page, never_cache
from django.utils.decorators import method_decorator
from django.db.models import Q, Min, Max, F, Count, OuterRef, Subquery
from django.utils import timezone
from datetime import timedelta, datetime
import random
import time
import math
import uuid
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from apps.anime.presentation.throttles import (
    StaffExemptRateThrottle,
    StaffExemptAnonRateThrottle,
    SearchRateThrottle,
    ImportRateThrottle,
)
import requests
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from apps.users.infrastructure.models.users import UserLibrary
from apps.anime.infrastructure.models.anime import (
    Anime,
    AnimeEpisodeNotification,
    Franchise,
    Genre,
    Episode,
    Translation,
    CustomDub,
    UserEpisodeProgress,
    WatchHistorySuppression,
    AnimeAnnouncement,
    CatalogSettings,
)
from apps.anime.presentation.serializers.anime_serializers import (
    AnimeSerializer,
    AnimeListSerializer,
    AnimeDetailSerializer,
    GenreSerializer,
    FranchiseSerializer,
    AnnouncementSerializer,
    CatalogSettingsSerializer,
)
from apps.anime.application.search_utils import (
    normalize_search_string,
    normalize_search_string_flexible,
    fuzzy_match,
    flexible_title_match,
    fuzzy_search_anime,
    legacy_anime_slug,
    split_param,
)
from apps.anime.application.anime_service import anime_service
from apps.anime.infrastructure.clients.kodik_config import (
    KODIK_API_TOKEN,
    KODIK_API_BASE,
    KODIK_VIDEO_BASE,
    normalize_kodik_player_link,
)

anime_service = anime_service
anime_parser_service = True
anime_update_service = True


class WatchHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


def split_param(value):
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

class AnimeViewSet(viewsets.ModelViewSet):
    queryset = Anime.objects.all()
    serializer_class = AnimeSerializer
    permission_classes = [permissions.AllowAny]

    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'
    
    def get_object(self):
        lookup = self.kwargs.get('slug') or ''
        match = re.fullmatch(r'(\d+)-.+', lookup)
        exact_id = Anime.objects.filter(slug=lookup).values_list('pk', flat=True).first() if not lookup.isdigit() else None
        query = {'pk': exact_id} if exact_id is not None else ({'pk': match[1] if match else lookup} if match or lookup.isdigit() else {'slug': lookup})
        detail_queryset = Anime.objects.filter(is_available=True).select_related('franchise')
        obj = detail_queryset.filter(**query).first()
        if obj is None:
            from apps.seo.models import SeoAlias
            alias = SeoAlias.objects.filter(path=f'/anime/{lookup}', kind='anime').first()
            if alias:
                obj = detail_queryset.filter(pk=alias.object_id).first()
        if obj is None and lookup:
            legacy_match_id = next(
                (
                    anime_id
                    for anime_id, title_ru in Anime.objects.filter(is_available=True)
                    .values_list('pk', 'title_ru')
                    .iterator()
                    if legacy_anime_slug(title_ru or '') == lookup
                ),
                None,
            )
            if legacy_match_id is not None:
                obj = detail_queryset.filter(pk=legacy_match_id).first()
        if obj is None:
            raise Http404()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        return Anime.objects.select_related("franchise").all()

    def list(self, request, *args, **kwargs):
        import hashlib
        personal = bool(request.query_params.get('excluded_library_statuses') or request.query_params.get('excluded_library_statuses[]'))
        cache_identity = str(request.user.pk) if personal and request.user.is_authenticated else 'public'
        parameters = tuple(sorted((key, tuple(values)) for key, values in request.query_params.lists()))
        cache_key = 'catalog:v7:' + hashlib.sha256((request.get_host() + ':' + cache_identity + ':' +
            str(safe_cache_get('catalog:revision', 0)) + ':' + repr(parameters)).encode()).hexdigest()
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return Response(cached)
        from apps.anime.application.catalog_visibility import is_hidden_value, visible_anime
        queryset = visible_anime().select_related("franchise")

        status_param = request.query_params.get("status")
        if not status_param:
            queryset = queryset.exclude(status="announced")

        slug = request.query_params.get("slug")
        if slug:
            slug_normalized = normalize_search_string(slug)
            slug_words = slug_normalized.split()
            
            if slug_words:
                slug_q = Q()
                for word in slug_words:
                    if len(word) < 2:
                        continue
                    word_q = (
                        Q(title_ru__icontains=word) |
                        Q(title_en__icontains=word) |
                        Q(slug__icontains=word)
                    )
                    if not slug_q:
                        slug_q = word_q
                    else:
                        slug_q &= word_q  
                
                if slug_q:
                    queryset = queryset.filter(slug_q)
            
        search = request.query_params.get("search")
        if search:
            search_normalized = normalize_search_string(search)
            search_words = search_normalized.split()
            
            if search_words:
                search_q = Q()
                for word in search_words:
                    if len(word) < 2:  
                        continue
                    word_q = (
                        Q(title_ru__icontains=word) |
                        Q(title_en__icontains=word) |
                        Q(title_jp__icontains=word) |
                        Q(slug__icontains=word)
                    )
                    if not search_q:
                        search_q = word_q
                    else:
                        search_q &= word_q  
                
                if search_q:
                    queryset = queryset.filter(search_q)

        status_param = request.query_params.get("status")
        if status_param:
            statuses = split_param(status_param)
            if statuses:
                if "finished" in statuses and "released" not in statuses:
                    statuses.append("released")
                queryset = queryset.filter(status__in=statuses)

        type_params = request.query_params.getlist("type")
        if not type_params:
            type_param = request.query_params.get("type")
            if type_param:
                type_params = split_param(type_param)

        if type_params:
            kinds = [k.strip() for k in type_params if k.strip()]
            if kinds:
                queryset = queryset.none() if any(is_hidden_value('kind', kind) for kind in kinds) else queryset.filter(kind__in=kinds)

        genres_param = request.query_params.get("genres")
        genre_logic = request.query_params.get("genre_logic", "OR").upper()  
        if genres_param:
            genre_values = split_param(genres_param)
            genre_names = []
            for val in genre_values:
                if val.isdigit():
                    name = (
                        Genre.objects.filter(id=int(val))
                        .values_list("name", flat=True)
                        .first()
                    )
                    if name:
                        genre_names.append(name)
                else:
                    genre_names.append(val)

            if genre_names:
                if any(is_hidden_value('genre', name) for name in genre_names):
                    queryset = queryset.none()
                elif genre_logic == "AND":
                    for gn in genre_names:
                        queryset = queryset.filter(genres__icontains=gn)
                    queryset = queryset.distinct()
                else:
                    genre_q = Q()
                    for gn in genre_names:
                        genre_q |= Q(genres__icontains=gn)
                    queryset = queryset.filter(genre_q).distinct()

        studio_params = request.query_params.getlist("studio")
        if not studio_params:
            studio_param = request.query_params.get("studio")
            if studio_param:
                studio_params = split_param(studio_param)

        if studio_params:
            studios = [s.strip() for s in studio_params if s.strip()]
            if studios:
                if any(is_hidden_value('studio', studio) for studio in studios):
                    queryset = queryset.none()
                else:
                    studio_q = Q()
                    for s in studios:
                        studio_q |= Q(studios__icontains=s)
                    queryset = queryset.filter(studio_q).distinct()

        year_from = request.query_params.get("year_from")
        year_to = request.query_params.get("year_to")
        if year_from is not None and year_from != '':
            try:
                queryset = queryset.filter(year__gte=int(year_from))
            except ValueError:
                pass
        if year_to is not None and year_to != '':
            try:
                queryset = queryset.filter(year__lte=int(year_to))
            except ValueError:
                pass

        score_from = request.query_params.get("score_from")
        score_to = request.query_params.get("score_to")
        if score_from is not None and score_from != '':
            try:
                queryset = queryset.filter(score__gte=float(score_from))
            except ValueError:
                pass
        if score_to is not None and score_to != '':
            try:
                queryset = queryset.filter(score__lte=float(score_to))
            except ValueError:
                pass

        episodes_from = request.query_params.get("episodes_from")
        episodes_to = request.query_params.get("episodes_to")
        if episodes_from is not None and episodes_from != '':
            try:
                queryset = queryset.filter(episodes__gte=int(episodes_from))
            except ValueError:
                pass

        show_only_franchises = request.query_params.get("show_only_franchises", "").lower() in (
            "true", "1", "yes",
        )
        group_franchises = show_only_franchises or request.query_params.get("group_franchises", "").lower() in (
            "true", "1", "yes",
        )
        if show_only_franchises:
            eligible_franchises = visible_anime().filter(
                franchise_id__isnull=False,
            ).order_by().values('franchise_id').annotate(
                _parts_count=Count('id', distinct=True),
            ).filter(_parts_count__gte=2).values('franchise_id')
            queryset = queryset.filter(franchise_id__in=eligible_franchises)
        if episodes_to is not None and episodes_to != '':
            try:
                ep_to_val = int(episodes_to)
                if ep_to_val > 0:
                    queryset = queryset.filter(
                        episodes__lte=ep_to_val, episodes__isnull=False
                    )
            except ValueError:
                pass

        excluded_library_statuses = request.query_params.get(
            "excluded_library_statuses"
        )
        if excluded_library_statuses and request.user.is_authenticated:
            excluded_statuses = split_param(excluded_library_statuses)
            if excluded_statuses:
                q = Q(user=request.user, status__in=excluded_statuses)

                if 'favorite' in excluded_statuses:
                    q |= Q(user=request.user, is_favorite=True)

                user_library_anime_ids = UserLibrary.objects.filter(q).values_list("anime_id", flat=True)
                if group_franchises:
                    user_library_franchise_ids = Anime.objects.filter(
                        id__in=user_library_anime_ids,
                        franchise_id__isnull=False,
                    ).values_list("franchise_id", flat=True)
                    queryset = queryset.exclude(
                        Q(id__in=user_library_anime_ids) |
                        Q(franchise_id__in=user_library_franchise_ids)
                    )
                else:
                    queryset = queryset.exclude(id__in=user_library_anime_ids)


        elif excluded_library_statuses and not request.user.is_authenticated:
            pass


        season_year = request.query_params.get("season_year")
        if season_year:
            try:
                queryset = queryset.filter(year=int(season_year))
            except ValueError:
                pass

        ordering = request.query_params.get("ordering", "-score")
        shuffle = request.query_params.get("shuffle", "").lower() in (
            "true",
            "1",
            "yes",
        )

        VALID_ORDER_FIELDS = {
            "score",
            "-score",
            "year",
            "-year",
            "title_ru",
            "-title_ru",
            "episodes",
            "-episodes",
            "created_at",
            "-created_at",
        }
        if ordering not in VALID_ORDER_FIELDS:
            ordering = "-score"

        try:
            page_size = max(1, min(int(request.query_params.get("page_size", 20)), 500))
        except ValueError:
            page_size = 20
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        from django.db.models import BigIntegerField, Case, CharField, F, Prefetch, Value, When, Window
        from django.db.models.functions import Cast, Coalesce, Concat, MD5, RowNumber
        total_count = queryset.count()
        if show_only_franchises:
            deduplicated_total = queryset.order_by().values('franchise_id').distinct().count()
        elif group_franchises:
            grouped_franchises = queryset.filter(franchise_id__isnull=False).order_by().values('franchise_id').distinct().count()
            grouped_standalone = queryset.filter(franchise_id__isnull=True).count()
            deduplicated_total = grouped_franchises + grouped_standalone
        else:
            deduplicated_total = total_count
        field = ordering.lstrip('-')
        sort_value = Coalesce(field, Value(0)) if field == 'episodes' else F(field)
        sort_expression = sort_value.desc() if ordering.startswith('-') else sort_value.asc()
        if group_franchises:
            queryset = queryset.annotate(_group_rank=Window(
                expression=RowNumber(), partition_by=[Coalesce('franchise_id', -F('id'), output_field=BigIntegerField())],
                order_by=[sort_expression, F('id').asc()])).filter(_group_rank=1)
        if shuffle:
            seed = request.query_params.get('shuffle_seed') or timezone.now().date().isoformat()
            queryset = queryset.annotate(_shuffle=MD5(Concat(Cast('id', CharField()), Value(seed)))).order_by('_shuffle', 'id')
        else:
            queryset = queryset.order_by(sort_expression, 'id')

        if show_only_franchises:
            page_franchise_ids = list(
                queryset.values_list('franchise_id', flat=True)[start:end]
            )
            franchise_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(page_franchise_ids)],
                default=len(page_franchise_ids),
            )
            franchises = list(
                Franchise.objects.filter(pk__in=page_franchise_ids)
                .order_by(franchise_order)
            )
            from apps.anime.application.catalog_visibility import visible_anime as visible_catalog_anime
            visible_entries = visible_catalog_anime().filter(
                franchise_id__in=page_franchise_ids,
            ).order_by('franchise_order', 'pk')
            entries_by_franchise = {franchise_id: [] for franchise_id in page_franchise_ids}
            for entry in visible_entries:
                entries_by_franchise.setdefault(entry.franchise_id, []).append(entry)
            results = FranchiseSerializer(
                franchises,
                many=True,
                context={'entries_by_franchise': entries_by_franchise},
            ).data
            response_data = {
                'results': results,
                'count': deduplicated_total,
                'total_count': deduplicated_total,
                'page': page,
                'page_size': page_size,
                'total_pages': max((deduplicated_total + page_size - 1) // page_size, 1),
            }
            safe_cache_set(cache_key, response_data, 300)
            return Response(response_data)

        page_ids = list(queryset.values_list('id', flat=True)[start:end])
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(page_ids)], default=len(page_ids))
        entries = Anime.objects.only('id', 'franchise_id', 'franchise_order', 'poster', 'poster_url',
                                     'episodes', 'episode_duration', 'total_duration').order_by('franchise_order', 'id')
        data_queryset = Anime.objects.filter(pk__in=page_ids).select_related('franchise').prefetch_related(
            Prefetch('franchise__entries', queryset=entries)).order_by(preserved_order)
        total_pages = max((deduplicated_total + page_size - 1) // page_size, 1)
        serializer = AnimeListSerializer(data_queryset, many=True, context={'request': request})
        results = serializer.data
        response_data = {
                "results": results,
                "count": deduplicated_total if group_franchises else total_count,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        safe_cache_set(cache_key, response_data, 300)
        return Response(response_data)

    def retrieve(self, request, *args, **kwargs):
        try:
            from django.core.cache import cache
            
            anime = self.get_object()
            
            cache_key = f"anime_screenshots_{anime.id}"
            screenshots = cache.get(cache_key)
            
            if screenshots is None and not anime.screenshots and anime.shikimori_id:
                try:
                    result = anime_service.search_by_shikimori_id(
                        anime.shikimori_id, limit=1
                    )
                    if result:
                        screenshots = result.get("screenshots", [])
                        if screenshots:
                            anime.screenshots = screenshots
                            anime.save(update_fields=["screenshots", "updated_at"])
                            cache.set(cache_key, screenshots, 3600)
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Не удалось загрузить скриншоты: {e}")
                    cache.set(cache_key, [], 300)
                    
            serializer = AnimeDetailSerializer(anime)
            return Response(serializer.data)
            
        except Http404:
            return Response(
                {"error": "Аниме не найдено"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            logging.getLogger(__name__).exception(f"Error in AnimeViewSet.retrieve: {e}")
            return Response(
                {
                    "error": f"Ошибка получения аниме: {str(e)}",
                    "detail": traceback.format_exc(),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnimeAnnouncement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = AnimeAnnouncement.objects.all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        type_param = self.request.query_params.get('type')
        if type_param:
            queryset = queryset.filter(type=type_param)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title_ru__icontains=search) | Q(title_en__icontains=search)
            )

        ordering = self.request.query_params.get('ordering', '-created_at')
        valid_orderings = {
            '-created_at', 'created_at',
            '-score', 'score',
            'title_ru', '-title_ru'
        }
        if ordering not in valid_orderings:
            ordering = '-created_at'
        queryset = queryset.order_by(ordering)

        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        lookup = kwargs.get('pk')
        instance = None
        
        try:
            int(lookup)
            instance = self.queryset.filter(id=lookup).first()
        except (ValueError, TypeError):
            instance = self.queryset.filter(slug=lookup).first()
            
            if not instance:
                instance = self.queryset.filter(
                    title_en__isnull=False,
                    title_en__icontains=lookup.replace('-', ' ')
                ).first()
                
                if not instance:
                    words = lookup.split('-')
                    if len(words) > 1:
                        query = Q()
                        for word in words:
                            if len(word) > 2:  
                                query |= Q(title_en__icontains=word)
                        instance = self.queryset.filter(query).first()
            
            if not instance:
                instance = self.queryset.filter(
                    title_ru__icontains=lookup.replace('-', ' ')
                ).first()
                
                if not instance:
                    words = lookup.split('-')
                    if len(words) > 1:
                        query = Q()
                        for word in words:
                            if len(word) > 2:  
                                query |= Q(title_ru__icontains=word)
                        instance = self.queryset.filter(query).first()
            
        if not instance:
            return Response(
                {"detail": "Анонс не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        try:
            page_size = min(int(request.query_params.get("page_size", 20)), 100)
        except ValueError:
            page_size = 20
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        total_pages = max((total_count + page_size - 1) // page_size, 1)

        serializer = self.get_serializer(queryset[start:end], many=True)

        return Response(
            {
                "results": serializer.data,
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )


class FranchiseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Franchise.objects.annotate(
        _public_parts_count=Count("entries", distinct=True),
    ).filter(_public_parts_count__gte=2).prefetch_related("entries")
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FranchiseSerializer
        return FranchiseSerializer

    def get_object(self):
        pk = self.kwargs.get(self.lookup_url_kwarg) or self.kwargs.get("pk")
        queryset = self.filter_queryset(self.get_queryset())
        try:
            obj = queryset.get(pk=pk)
        except (Franchise.DoesNotExist, ValueError):
            obj = get_object_or_404(queryset, slug=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        slug = request.query_params.get("slug")

        if slug:
            qs = qs.filter(name__icontains=slug.replace("-", " "))

        if search:
            qs = qs.filter(name__icontains=search)
        page_size = min(int(request.query_params.get("page_size", 20)), 200)
        page = int(request.query_params.get("page", 1))
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        serializer = FranchiseSerializer(qs[start:end], many=True)
        return Response(
            {
                "results": serializer.data,
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        )

    def retrieve(self, request, *args, **kwargs):
        franchise = self.get_object()
        serializer = FranchiseSerializer(franchise)
        data = serializer.data
        from apps.anime.presentation.serializers.anime_serializers import FranchiseEntrySerializer

        from apps.seo.service import visible_anime
        entries = visible_anime().filter(franchise=franchise).order_by("franchise_order", "year", "pk")
        data["entries"] = FranchiseEntrySerializer(entries, many=True).data
        return Response(data)

    @action(detail=True, methods=["get"])
    def parts(self, request, pk=None):
        try:
            franchise = self.get_object()

            from apps.seo.service import visible_anime
            animes = visible_anime().filter(franchise=franchise).order_by("franchise_order", "year", "id")

            parts_data = []

            for anime in animes:
                poster_url = anime.poster.url if anime.poster else anime.poster_url
                parts_data.append(
                    {
                        "id": anime.id,
                        "title_ru": anime.title_ru,
                        "title_en": anime.title_en,
                        "title_jp": anime.title_jp,
                        "year": anime.year,
                        "kind": anime.kind,
                        "episodes": anime.episodes,
                        "status": anime.status,
                        "score": anime.score,
                        "poster_url": poster_url,
                        "franchise_order": anime.franchise_order,
                    }
                )

            return Response(
                {
                    "franchise_id": franchise.id,
                    "franchise_name": franchise.name,
                    "parts": parts_data,
                    "total": 1,
                }
            )
        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            return Response({"error": str(e)}, status=500)


class SearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [SearchRateThrottle]

    @method_decorator(cache_page(60 * 2))
    def get(self, request):
        raw_query = request.query_params.get("q", "")
        query = raw_query.strip()
        paginated = 'page' in request.query_params or 'page_size' in request.query_params
        try:
            if paginated:
                page = max(int(request.query_params.get('page', 1)), 1)
                page_size = max(1, min(int(request.query_params.get('page_size', 20)), 50))
                limit = min(page * page_size + 1, 500)
            else:
                page = 1
                page_size = 0
                limit = int(request.query_params.get("limit", 500))
                if limit <= 0:
                    limit = 500
                limit = min(limit, 500)
        except Exception:
            page, page_size, limit = (1, 20, 21) if paginated else (1, 0, 500)
        if not query:
            return Response(
                {"error": "Требуется параметр поиска q"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        from django.core.cache import cache
        import hashlib
        cache_key = f"anime:search:{hashlib.md5(quote_plus(query).encode()).hexdigest()}:{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            start = (page - 1) * page_size if paginated else 0
            results = cached[start:start + page_size] if paginated else cached
            return Response(
                {
                    "query": query,
                    "results": results,
                    "total": len(cached),
                    "page": page,
                    "page_size": page_size or len(cached),
                    "has_more": paginated and len(cached) > start + page_size,
                    "source": "cache",
                }
            )
        
        try:
            db_results = fuzzy_search_anime(query, limit)
            try:
                for result in db_results:
                    result.pop("match_score", None)
            except Exception:
                logging.getLogger(__name__).exception("Failed to sanitize db_results")
            
            cache.set(cache_key, db_results, 300)
            
            start = (page - 1) * page_size if paginated else 0
            results = db_results[start:start + page_size] if paginated else db_results
            return Response(
                {
                    "query": query,
                    "results": results,
                    "total": len(db_results),
                    "page": page,
                    "page_size": page_size or len(db_results),
                    "has_more": paginated and len(db_results) > start + page_size,
                    "source": "database",
                }
            )
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            logging.getLogger(__name__).exception("Error in SearchAPIView: %s", tb)
            return Response(
                {
                    "error": f"Ошибка поиска: {str(e)}",
                    "query": query,
                    "results": [],
                    "total": 0,
                    "source": "error",
                    "debug": repr(e),
                    "debug_traceback": tb,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParserStatusAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            if not anime_parser_service:
                return Response(
                    {"error": "Сервис парсера недоступен", "status": "unhealthy"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            health_status = anime_service.health_check()
            return Response(
                {
                    "parsers": health_status,
                    "total_parsers": len(health_status),
                    "active_parsers": sum(
                        1 for status in health_status.values() if status
                    ),
                    "status": "healthy" if any(health_status.values()) else "unhealthy",
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка проверки статуса: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdatesAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))
        try:
            if not anime_update_service:
                return Response(
                    {
                        "error": "Сервис обновлений недоступен",
                        "updates": [],
                        "total": 0,
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            updates = anime_service.get_recent_updates(limit)
            return Response({"updates": updates, "total": len(updates)})
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения обновлений: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GenresViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from apps.anime.application.catalog_visibility import hidden_values
        blocked = hidden_values('genre')
        allowed_ids = [genre.pk for genre in Genre.objects.all() if genre.name.strip().casefold() not in blocked]
        return Genre.objects.filter(pk__in=allowed_ids)

    def list(self, request):
        try:
            genres = self.get_queryset()
            serializer = GenreSerializer(genres, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения жанров: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KodikSearchCandidatesView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [SearchRateThrottle]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"groups": []})
        try:
            raw_results = anime_service.search_anime(query, limit=20)
            groups = self._build_franchise_groups(raw_results)
            return Response({"groups": groups})
        except Exception as e:
            return Response(
                {"error": f"Ошибка поиска: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _map_kind(kind: Optional[str]) -> str:
        value = (kind or "tv").strip().lower()
        mapping = {
            "tv": "tv",
            "tv_special": "tv_special",
            "special": "special",
            "movie": "movie",
            "ova": "ova",
            "ona": "ona",
            "music": "music",
            "clip": "music",
            "anime": "tv",
            "anime-serial": "tv",
            "foreign-movie": "movie",
            "russian-movie": "movie",
            "soviet-cartoon": "movie",
            "foreign-cartoon": "movie",
            "russian-cartoon": "movie",
            "tv_13": "tv",
            "tv_24": "tv",
            "tv_48": "tv",
        }
        return mapping.get(value, value or "tv")

    def _fetch_mal_id(self, shikimori_id: int) -> Optional[int]:
        cache_key = f"shikimori:mal_id:{shikimori_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            from apps.anime.infrastructure.api.shikimori import shikimori_api
            data = shikimori_api.get_anime(shikimori_id)
            if data:
                mal_id = data.get("myanimelist_id")
                if mal_id:
                    cache.set(cache_key, mal_id, timeout=86400)
                    return mal_id
        except Exception:
            pass
        return None

    def _build_franchise_groups(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from apps.anime.infrastructure.models.anime import Anime
        from apps.anime.application.release_year import release_year
        if not results:
            return []

        anchor = results[0]
        anchor_sid = anchor.get("shikimori_id")
        try:
            anchor_sid = int(anchor_sid) if anchor_sid is not None else None
        except (TypeError, ValueError):
            anchor_sid = None

        if anchor_sid is None:
            return self._build_standalone_groups(results)

        franchise_data = anime_service.get_franchise(anchor_sid)
        if not franchise_data:
            return self._build_standalone_groups(results)

        from apps.anime.application.franchise_sync import graph_nodes, node_order
        node_map = graph_nodes(franchise_data, anchor_sid)
        if not node_map:
            return self._build_standalone_groups(results)
        node_ids = sorted(node_map, key=lambda key: (node_order(node_map[key]), key))[:100]
        nodes = [node_map[key] for key in node_ids]
        
        existing_anime = {}
        if node_ids:
            existing_anime = dict(Anime.objects.filter(shikimori_id__in=node_ids).values_list('shikimori_id', 'slug'))

        cached_results: Dict[int, Optional[Dict[str, Any]]] = {}
        uncached_ids: List[int] = []
        for node_id in node_ids:
            cache_key = f"kodik:shikimori:{node_id}"
            cached = safe_cache_get(cache_key)
            if cached is not None:
                cached_results[node_id] = cached
            else:
                uncached_ids.append(node_id)

        kodik_results: Dict[int, Optional[Dict[str, Any]]] = {}
        if uncached_ids:
            def _search_one(node_id: int) -> tuple[int, Optional[Dict[str, Any]]]:
                try:
                    result = anime_service.search_by_shikimori_id(str(node_id))
                    return node_id, result
                except Exception:
                    return node_id, None

            for requested_id in uncached_ids:
                node_id, result = _search_one(requested_id)
                kodik_results[node_id] = result
                cache_key = f"kodik:shikimori:{node_id}"
                safe_cache_set(cache_key, result, timeout=3600)

        all_results = {**cached_results, **kodik_results}

        items: List[Dict[str, Any]] = []
        for node_id in node_ids:
            node = node_map[node_id]
            kodik_result = all_results.get(node_id)
            material_data = (kodik_result or {}).get("material_data") or {}
            node_name = node.get("name") or ""

            if kodik_result:
                items.append({
                    "shikimori_id": node_id,
                    "kodik_id": kodik_result.get("id"),
                    "title_ru": material_data.get("anime_title") or kodik_result.get("title") or node_name,
                    "title_en": kodik_result.get("title_orig") or node_name,
                    "year": release_year(kodik_result) or node.get("year"),
                    "kind": self._map_kind(material_data.get("anime_kind") or kodik_result.get("type") or node.get("kind")),
                    "status": material_data.get("anime_status") or kodik_result.get("status") or "",
                    "episodes": (
                        kodik_result.get("episodes_count")
                        or kodik_result.get("last_episode")
                        or material_data.get("episodes_total")
                    ),
                    "poster_url": material_data.get("anime_poster_url") or kodik_result.get("poster_url") or node.get("image_url") or "",
                    "kodik_available": True,
                    "exists_in_db": node_id in existing_anime,
                    "anime_slug": existing_anime.get(node_id),
                })
            else:
                items.append({
                    "shikimori_id": node_id,
                    "kodik_id": None,
                    "title_ru": node_name,
                    "title_en": node_name,
                    "year": node.get("year"),
                    "kind": self._map_kind(node.get("kind")),
                    "status": "",
                    "episodes": None,
                    "poster_url": node.get("image_url") or "",
                    "kodik_available": False,
                    "exists_in_db": node_id in existing_anime,
                    "anime_slug": existing_anime.get(node_id),
                })

        if not items:
            return self._build_standalone_groups(results)

        franchise_slug = anime_service.get_franchise_slug(anchor_sid) if anchor_sid is not None else None
        franchise_name = self._resolve_franchise_name(nodes, franchise_slug)

        year = items[0].get("year")
        groups = [{
            "name": franchise_name,
            "year": year,
            "items": items,
            "is_franchise": True,
        }]
        others = []
        for result in results:
            try:
                sid = int(result.get('shikimori_id'))
            except (TypeError, ValueError):
                sid = None
            if sid not in node_map:
                others.append(result)
        return groups + self._build_standalone_groups(others)

    def _build_standalone_groups(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from apps.anime.infrastructure.models.anime import Anime
        from apps.anime.application.release_year import release_year
        groups: List[Dict[str, Any]] = []
        seen = set()

        for r in results:
            sid = r.get("shikimori_id")
            try:
                sid = int(sid) if sid is not None else None
            except (TypeError, ValueError):
                sid = None
            if sid is not None and sid in seen:
                continue
            if sid is not None:
                seen.add(sid)

            material_data = (r.get("material_data") or {})
            item = {
                "shikimori_id": sid,
                "kodik_id": r.get("id"),
                "title_ru": material_data.get("anime_title") or r.get("title") or "",
                "title_en": r.get("title_orig") or material_data.get("title_en") or "",
                "year": release_year(r),
                "kind": self._map_kind(material_data.get("anime_kind") or r.get("type")),
                "status": material_data.get("anime_status") or r.get("status") or "",
                "episodes": (
                    r.get("episodes_count")
                    or r.get("last_episode")
                    or material_data.get("episodes_total")
                ),
                "poster_url": material_data.get("anime_poster_url") or r.get("poster_url") or "",
                "kodik_available": True,
            }

            name = item.get("title_ru") or item.get("title_en") or ""
            if not name:
                continue

            groups.append({
                "name": name,
                "year": item.get("year"),
                "items": [item],
                "is_franchise": False,
            })

        existing_anime = {}
        if seen:
            existing_anime = dict(Anime.objects.filter(shikimori_id__in=seen).values_list('shikimori_id', 'slug'))
        
        for group in groups:
            for item in group["items"]:
                item["exists_in_db"] = item["shikimori_id"] in existing_anime
                item["anime_slug"] = existing_anime.get(item["shikimori_id"])

        return groups

    @staticmethod
    def _tokenize_name(name: str) -> List[str]:
        cleaned = name.strip()
        if not cleaned:
            return []
        tokens = []
        for part in cleaned.split():
            token = re.sub(r'^[\W_]+|[\W_]+$', '', part)
            if token:
                tokens.append(token)
        return tokens

    def _resolve_franchise_name(self, nodes: List[Dict[str, Any]], franchise_slug: Optional[str]) -> str:
        if not nodes:
            return self._normalize_slug_to_name(franchise_slug) or ""

        first_node = nodes[0]
        first_id = first_node.get("id")
        if first_id is None:
            return self._normalize_slug_to_name(franchise_slug) or ""
        try:
            first_id = int(first_id)
        except (TypeError, ValueError):
            return self._normalize_slug_to_name(franchise_slug) or ""

        try:
            from apps.anime.infrastructure.api.shikimori import shikimori_api
            franchise_data = shikimori_api.get_franchise(first_id)
            if not franchise_data:
                return self._normalize_slug_to_name(franchise_slug) or ""

            franchise_nodes = franchise_data.get("nodes", []) or []
            if not franchise_nodes:
                return self._normalize_slug_to_name(franchise_slug) or ""

            unique_weights = sorted({node.get("weight", 0) for node in franchise_nodes}, reverse=True)
            top_weights = unique_weights[:2] if len(unique_weights) >= 2 else unique_weights[:1]
            top_weight_names = [
                node.get("name", "").strip()
                for node in franchise_nodes
                if node.get("weight", 0) in top_weights and node.get("name")
            ]
            if not top_weight_names:
                return self._normalize_slug_to_name(franchise_slug) or ""

            common_prefix = KodikSearchCandidatesView._find_common_prefix(top_weight_names)
            if not common_prefix:
                return self._normalize_slug_to_name(franchise_slug) or ""

            import re
            cleaned = re.sub(r"[\s:\.,\--]+\$", "", common_prefix).strip()
            return cleaned or self._normalize_slug_to_name(franchise_slug) or ""
        except Exception:
            return self._normalize_slug_to_name(franchise_slug) or ""

    @staticmethod
    def _find_common_prefix(strings: List[str]) -> str:
        if not strings:
            return ""
        if len(strings) == 1:
            return strings[0]

        min_len = min(len(s) for s in strings)
        prefix_len = 0
        for i in range(min_len):
            char = strings[0][i]
            if all(s[i] == char for s in strings):
                prefix_len += 1
            else:
                break
        return strings[0][:prefix_len]

    def _normalize_slug_to_name(self, slug: Optional[str]) -> str:
        if not slug:
            return ""
        return slug.replace("_", " ").strip()

    def _normalize_for_compare(self, value: str) -> str:
        if not value:
            return ""
        return " ".join(self._tokenize_name(value)).lower()


class KodikImportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        if self._body_too_large(request):
            return Response({"error": "request_body_too_large"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        data = request.data
        if "anime_ids" in data:
            return self._import_ids(request, data)
        if "shikimori_id" in data or "kodik_id" in data:
            from apps.anime.application.kodik_limits import reserve_unique_ids, KodikLimitExceeded
            identifier = data.get("shikimori_id") or data.get("kodik_id")
            try:
                reserve_unique_ids(request, [identifier])
            except KodikLimitExceeded as exc:
                return Response(
                    {"error": "hourly_limit_exceeded"},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(exc.retry_after)},
                )
            return self._import_single_anime(data)
        else:
            return Response({"error": "anime_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _body_too_large(request, limit=64 * 1024):
        try:
            return int(request.META.get("CONTENT_LENGTH") or 0) > limit
        except (TypeError, ValueError):
            return True

    def _import_ids(self, request, data):
        values = data.get("anime_ids")
        if not isinstance(values, list) or not 1 <= len(values) <= 100:
            return Response({"error": "anime_ids must contain 1 to 100 integers"}, status=400)
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values):
            return Response({"error": "anime_ids must contain positive integers"}, status=400)
        identifiers = list(dict.fromkeys(values))
        from apps.anime.application.kodik_limits import reserve_unique_ids, KodikLimitExceeded
        try:
            reserve_unique_ids(request, identifiers)
        except KodikLimitExceeded as exc:
            return Response(
                {"error": "kodik_hourly_limit_exceeded"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(exc.retry_after)},
            )

        from apps.anime.infrastructure.models.anime import Anime
        existing = set(Anime.objects.filter(shikimori_id__in=identifiers).values_list("shikimori_id", flat=True))
        imported = []
        failed = []
        for identifier in identifiers:
            if identifier in existing:
                continue
            response = self._import_single_anime({"shikimori_id": identifier, "update_existing": False})
            if response.status_code < 300:
                imported.append(identifier)
            else:
                failed.append(identifier)
        return Response({"accepted": identifiers, "existing": sorted(existing), "imported": imported, "failed": failed})

    def _import_single_anime(self, data):
        try:
            shikimori_id = data.get("shikimori_id")
            kodik_id = data.get("kodik_id")
            update_existing = data.get("update_existing", False)
            download_posters = bool(data.get("download_posters", False))

            if shikimori_id:
                try:
                    shikimori_id = int(shikimori_id)
                except (ValueError, TypeError):
                    return Response({"error": "Некорректный shikimori_id"}, status=status.HTTP_400_BAD_REQUEST)
                item = anime_service.get_by_shikimori_id(shikimori_id)
            elif kodik_id:
                item = anime_service.get_by_kodik_id(str(kodik_id))
            else:
                return Response({"error": "Требуется shikimori_id"}, status=status.HTTP_400_BAD_REQUEST)

            if not item:
                return Response({"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND)

            anime, created = anime_service.import_anime(item, update_existing=update_existing, download_posters=download_posters)
            return Response({
                "message": "Аниме успешно импортировано",
                "anime_id": anime.id,
                "title": anime.title_ru,
                "created": created,
            })
        except Exception as e:
            return Response({"error": f"Ошибка импорта: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _import_all_anime(self, data):
        try:
            limit = data.get("limit", 0)
            update_existing = data.get("update_existing", False)
            download_posters = bool(data.get("download_posters", False))
            result = anime_service.bulk_import(
                limit=limit if limit > 0 else None,
                update_existing=update_existing,
                download_posters=download_posters,
            )
            return Response({
                "message": "Импорт завершен",
                **result,
            })
        except Exception as e:
            return Response({"error": f"Ошибка массового импорта: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_anime_from_kodik(self, kodik_data):
        from apps.anime.infrastructure.models.anime import Anime

        material_data = kodik_data.get("material_data", {})
        episodes_count = (
            material_data.get("episodes_total") or kodik_data.get("episodes_count") or 1
        )
        genre_names = (
            material_data.get("anime_genres") or material_data.get("genres") or []
        )
        studio_names = material_data.get("anime_studios") or []
        poster_url = (
            material_data.get("anime_poster_url")
            or material_data.get("poster_url")
            or ""
        )
        score = (
            material_data.get("shikimori_rating")
            or material_data.get("kinopoisk_rating")
            or 0.0
        )
        description = (
            material_data.get("anime_description")
            or material_data.get("description")
            or ""
        )
        status_map = {
            "anons": "announced",
            "ongoing": "ongoing",
            "released": "finished",
            "discontinued": "canceled",
        }
        status = status_map.get(
            material_data.get("anime_status", "released"), "finished"
        )
        kind_map = {
            "tv": "tv",
            "tv_13": "tv",
            "tv_24": "tv",
            "tv_48": "tv",
            "movie": "movie",
            "ova": "ova",
            "ona": "ona",
            "special": "special",
            "music": "music",
        }
        kind = kind_map.get(
            material_data.get("anime_kind") or kodik_data.get("type", "tv"), "tv"
        )
        anime, created = Anime.objects.update_or_create(
            shikimori_id=kodik_data.get("shikimori_id"),
            defaults={
                "title_ru": kodik_data.get("title", ""),
                "title_en": kodik_data.get("title_orig", ""),
                "title_jp": kodik_data.get("other_title", ""),
                "description": description,
                "year": kodik_data.get("year"),
                "status": status,
                "kind": kind,
                "episodes": episodes_count,
                "score": score,
                "poster_url": poster_url,
                "genres": genre_names,
                "studios": studio_names,
                "data_source": "kodik",
                "movies": [],
                "ovas": [],
                "movie_count": 0,
                "ova_count": 0,
                "total_items": 1,
            },
        )
        return anime


class KodikFiltersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            filters = anime_service.get_filters()
            return Response(filters)
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения фильтров: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KodikTranslationsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
            if not anime.shikimori_id:
                return Response(
                    {"error": "У аниме нет Shikimori ID"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            translations = anime_service.get_translations(anime.shikimori_id)
            best_episodes = max(
                (t.get("episodes_done") or 0 for t in translations), default=0
            )
            progress_total = anime.progress_total or anime.episodes or 0
            if best_episodes > progress_total:
                Anime.objects.filter(pk=anime.pk).update(
                    progress_total=best_episodes
                )
                progress_total = best_episodes
            kodik_seasons = set()
            for translation in translations:
                seasons_data = translation.get("seasons") or {}
                if not isinstance(seasons_data, dict):
                    continue
                for season_key, season_meta in seasons_data.items():
                    try:
                        season_number = int(season_key)
                    except (TypeError, ValueError):
                        continue
                    if season_number < 0:
                        continue
                    season_episodes = (
                        season_meta.get("episodes")
                        if isinstance(season_meta, dict)
                        else None
                    )
                    if isinstance(season_episodes, (list, tuple)) and season_episodes:
                        kodik_seasons.add(season_number)
            return Response(
                {
                    "translations": translations,
                    "total": len(translations),
                    "progress_total": progress_total,
                    "allow_flat": (
                        (
                            anime.kind in ("movie", "ova", "ona")
                            or (anime.episodes or 0) <= 1
                        )
                        and len(kodik_seasons) <= 1
                    ),
                }
            )
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except requests.RequestException as e:
            return Response(
                {"error": f"Ошибка запроса к API: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения озвучек: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KodikPlayerView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
            return Response({
                "kodik_link": anime.kodik_link,
                "last_episode": anime.last_episode,
            })
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )


class CustomDubListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, anime_id):
        try:
            anime = Anime.objects.get(pk=anime_id)
            custom_dubs = CustomDub.objects.filter(
                anime=anime, status="approved"
            ).order_by("-rating", "-created_at")
            dubs_data = []
            for dub in custom_dubs:
                dubs_data.append(
                    {
                        "id": dub.id,
                        "name": dub.name,
                        "studio": dub.studio,
                        "description": dub.description,
                        "quality": dub.quality,
                        "logo": dub.logo_url,
                        "episodes_done": dub.episodes_done,
                        "total_episodes": dub.total_episodes or anime.episodes,
                        "is_complete": dub.is_complete,
                        "is_custom": True,
                        "rating": dub.rating,
                        "views_count": dub.views_count,
                    }
                )
            return Response({"dubs": dubs_data, "total": len(dubs_data)})
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, anime_id):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Требуется авторизация"}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            anime = Anime.objects.get(pk=anime_id)
            name = request.data.get("name")
            studio = request.data.get("studio", "")
            quality = request.data.get("quality")
            video_url = request.data.get("video_url")
            logo_url = request.data.get("logo_url", "")
            description = request.data.get("description", "")
            episodes_done = request.data.get("episodes_done", 0)
            is_complete = request.data.get("is_complete", False)
            if not name or not quality or not video_url:
                return Response(
                    {
                        "error": "Необходимо указать название, качество и ссылку на видео"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            existing_dub = CustomDub.objects.filter(
                anime=anime, created_by=request.user, name=name
            ).first()
            if existing_dub:
                return Response(
                    {"error": "Вы уже добавляли озвучку с таким названием"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            dub = CustomDub.objects.create(
                anime=anime,
                created_by=request.user,
                name=name,
                studio=studio or name,
                description=description,
                quality=quality,
                video_url=video_url,
                logo_url=logo_url,
                episodes_done=episodes_done or 0,
                total_episodes=anime.episodes,
                is_complete=is_complete,
                status="pending",
            )
            return Response(
                {
                    "message": "Озвучка отправлена на модерацию",
                    "dub_id": dub.id,
                    "status": dub.status,
                },
                status=status.HTTP_201_CREATED,
            )
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка добавления озвучки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomDubDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, anime_id, dub_id):
        try:
            dub = CustomDub.objects.get(id=dub_id, anime_id=anime_id, status="approved")
            CustomDub.objects.filter(pk=dub.pk).update(views_count=F("views_count") + 1)
            return Response(
                {
                    "video_url": dub.video_url,
                    "quality": dub.quality,
                    "name": dub.name,
                    "studio": dub.studio,
                    "logo": dub.logo_url,
                }
            )
        except CustomDub.DoesNotExist:
            return Response(
                {"error": "Озвучка не найдена или не одобрена"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения видео: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(never_cache, name='dispatch')
class RandomAnimeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import random

        try:
            from apps.anime.application.catalog_visibility import hidden_anime
            queryset = Anime.objects.filter(title_ru__regex=r"[а-яёА-ЯЁ]", is_available=True) \
                .exclude(pk__in=hidden_anime().values('pk'))
            bounds = queryset.aggregate(min_id=Min('id'), max_id=Max('id'))
            if bounds['min_id'] is None:
                return Response(
                    {"error": "Нет аниме"}, status=status.HTTP_404_NOT_FOUND
                )
            random_id = random.randint(bounds['min_id'], bounds['max_id'])
            anime = queryset.filter(id__gte=random_id).order_by('id').first()
            if anime is None:
                anime = queryset.order_by('id').first()
            serializer = AnimeSerializer(anime)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentlyWatchingView(APIView):
    permission_classes = [permissions.AllowAny]

    PLAYER_WINDOW = 2 * 60  
    TAB_WINDOW = 10 * 60  
    PROGRESS_WINDOW = 2 * 60  

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        from apps.anime.infrastructure.models.anime import UserActiveTab

        try:
            now = timezone.now()

            player_cutoff = now - timedelta(seconds=self.PLAYER_WINDOW)

            player_tab = (
                UserActiveTab.objects.filter(
                    activity_type="player", last_ping__gte=player_cutoff
                )
                .values("anime_id")
                .annotate(n=Count("user", distinct=True))
            )
            player_tab_map = {r["anime_id"]: r["n"] for r in player_tab}

            progress_cutoff = now - timedelta(seconds=self.PROGRESS_WINDOW)
            progress_rows = (
                UserEpisodeProgress.objects.filter(last_watched__gte=progress_cutoff)
                .values("anime_id")
                .annotate(n=Count("user", distinct=True))
            )
            progress_map = {r["anime_id"]: r["n"] for r in progress_rows}

            tab_cutoff = now - timedelta(seconds=self.TAB_WINDOW)
            watching_tab = (
                UserActiveTab.objects.filter(
                    activity_type="watching", last_ping__gte=tab_cutoff
                )
                .values("anime_id")
                .annotate(n=Count("user", distinct=True))
            )
            watching_tab_map = {r["anime_id"]: r["n"] for r in watching_tab}

            all_ids = set(player_tab_map) | set(progress_map) | set(watching_tab_map)

            if not all_ids:
                return Response({"results": [], "count": 0})

            animes = {a.id: a for a in Anime.objects.filter(id__in=all_ids, title_ru__regex=r"[а-яёА-ЯЁ]")}
            results = []

            for aid in all_ids:
                a = animes.get(aid)
                if not a:
                    continue

                player_count = max(player_tab_map.get(aid, 0), progress_map.get(aid, 0))
                watching_count = watching_tab_map.get(aid, 0)
                total = max(
                    player_count, watching_count
                )  

                data = AnimeSerializer(a).data
                data["viewers_count"] = total
                data["has_active_player"] = aid in player_tab_map or aid in progress_map
                data["has_active_tab"] = aid in watching_tab_map
                results.append(data)

            results.sort(key=lambda x: x["viewers_count"], reverse=True)
            return Response({"results": results, "count": len(results)})

        except Exception as e:
            import traceback

            return Response(
                {"error": str(e), "detail": traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserActiveTabView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from apps.anime.infrastructure.models.anime import UserActiveTab

        anime_id = request.data.get("anime_id")
        activity_type = request.data.get("activity_type", "watching")
        current_episode = request.data.get("current_episode")

        if not anime_id:
            return Response(
                {"error": "Требуется anime_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )

        tab, created = UserActiveTab.objects.update_or_create(
            user=request.user,
            anime=anime,
            defaults={
                "activity_type": activity_type,
                "current_episode": current_episode,
            },
        )

        return Response(
            {
                "anime_id": anime.id,
                "activity_type": tab.activity_type,
                "current_episode": tab.current_episode,
                "last_ping": tab.last_ping.isoformat(),
                "created": created,
            }
        )

    def delete(self, request):
        from apps.anime.infrastructure.models.anime import UserActiveTab

        anime_id = request.query_params.get("anime_id")
        if not anime_id:
            return Response(
                {"error": "Требуется anime_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )

        deleted, _ = UserActiveTab.objects.filter(
            user=request.user, anime=anime
        ).delete()

        return Response(
            {
                "deleted": deleted > 0,
                "anime_id": anime_id,
            }
        )


class HomeAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    CACHE_TTL = 120

    def _build_cache_key(self, request):
        if request.user.is_authenticated:
            return f"home:v2:user:{request.user.id}"
        return "home:v2:anonymous"

    def get(self, request):
        from apps.anime.application.recommendations import read
        user = request.user if request.user.is_authenticated else None
        from apps.users.application.library_episodes import new_episodes_for_user
        recommendations = read(request.user, 'based_on_watched,top_rated')
        response = Response({
            'new_episodes': new_episodes_for_user(user) if user else [],
            'continue_watching': self._get_continue_watching(user) if user else [],
            'rewatch': self._get_rewatch(user) if user else [],
            'recommendations': recommendations['based_on_watched'],
            'trending': recommendations['top_rated'],
        })
        from django.utils.cache import patch_vary_headers
        if request.user.is_authenticated:
            response['Cache-Control'] = 'private, no-store'
            patch_vary_headers(response, ['Authorization', 'Cookie'])
        else:
            response['Cache-Control'] = 'public, max-age=60, stale-while-revalidate=120'
        return response

    def personalized_recommendations(self, request):
        from apps.anime.application.recommendations import read
        return Response(read(request.user, request.query_params.get('sections')))

    def _get_continue_watching(self, user):
        return PersonalizedRecommendationsView()._get_continue_watching(user)

    def _get_rewatch(self, user):
        return PersonalizedRecommendationsView()._get_rewatch(user)

    def _get_recommendations(self, user):
        return PersonalizedRecommendationsView()._get_recommendations(user)

    def _get_trending(self, user=None):
        return PersonalizedRecommendationsView()._get_trending(user)


class PersonalizedRecommendationsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        from apps.anime.application.recommendations import read
        return Response(read(request.user, request.query_params.get('sections')))

    def legacy_build(self, request):
        import random
        user = request.user if request.user.is_authenticated else None
        
        user_genres, user_genre_counts, watched_ids = self._get_user_genre_preferences_detailed(user)
        
        rare_genres = self._get_rare_genres(user_genre_counts)
        
        random_genre = random.choice(user_genres) if user_genres else None
        
        result = {
            "based_on_watched": self._get_based_on_watched(user, watched_ids, 20),
            "similar_style": self._get_similar_style(user, watched_ids, 20, random_genre),
            "top_rated_in_genres": self._get_top_rated_in_genres_new(user_genres, watched_ids, 20),
            "new_in_genres": self._get_new_in_genres_ongoing(user_genres, watched_ids, 20),
            "classics": self._get_classics_high_rated(20),
            "top_anime": self._get_top_anime_last_year(20),
            "new_releases": self._get_new_in_rare_genres(rare_genres, watched_ids, 20),
            "short": self._get_short_anime(20),
            "movies": self._get_movies_high_rated(20),
            "user_genres": user_genres,
            "has_personalization": user is not None and len(watched_ids) > 0,
        }
        
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')
        
        def has_cyrillic(text):
            return bool(CYRILLIC_RE.search(text or ''))
        
        for key in ["based_on_watched", "similar_style", "top_rated_in_genres", 
                    "new_in_genres", "classics", "top_anime", "new_releases", 
                    "short", "movies"]:
            if key in result:
                result[key] = [
                    item for item in result[key]
                    if has_cyrillic(item.get("title", ""))
                ]
        
        return Response(result)

    def post(self, request):
        from apps.users.infrastructure.models.users import UserLibrary
        from apps.anime.infrastructure.models.anime import Anime
        user = request.user if request.user.is_authenticated else None
        if not user:
            return Response({"error": "Требуется авторизация"}, status=401)
        anime_id = request.data.get("anime_id")
        action = request.data.get("action", "hide")
        if not anime_id:
            return Response({"error": "Требуется anime_id"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        if action == "hide":
            UserLibrary.objects.update_or_create(
                user=user, anime=anime,
                defaults={"status": "hidden", "user_set_status": True}
            )
            return Response({"hidden": True, "anime_id": anime_id})
        return Response({"error": "Неизвестное действие"}, status=400)

    def _dedupe_franchises(self, animes):
        seen_franchises = set()
        result = []

        for anime in animes:
            if anime.franchise:
                fid = anime.franchise_id
                if fid not in seen_franchises:
                    seen_franchises.add(fid)
                    result.append(self._anime_to_dict(anime))
            else:
                result.append(self._anime_to_dict(anime))

        return result

    @staticmethod
    def _anime_to_dict(anime):
        poster_url = anime.poster.url if anime.poster else anime.poster_url

        raw_screenshots = anime.screenshots or []
        screenshots: list[str] = []
        if isinstance(raw_screenshots, list):
            for item in raw_screenshots:
                if isinstance(item, str):
                    screenshots.append(item)
                elif isinstance(item, dict):
                    url = item.get("url")
                    if url:
                        screenshots.append(url)

        if anime.franchise:
            franchise = anime.franchise
            franchise_total_duration = 0
            for entry in franchise.entries.all():
                if entry.total_duration:
                    franchise_total_duration += entry.total_duration
                elif entry.episodes and entry.episode_duration:
                    franchise_total_duration += entry.episodes * entry.episode_duration
            return {
                "anime_id": anime.id,
                "slug": anime.slug,
                "title": anime.title_ru or anime.title_en or "",
                "title_en": anime.title_en or "",
                "poster": poster_url,
                "screenshots": screenshots,
                "genres": anime.genres or [],
                "rating": anime.score,
                "rating_count": 0,
                "year": anime.year,
                "status": anime.status,
                "episodes": anime.episodes,
                "description": anime.description or "",
                "is_franchise": True,
                "franchise_id": franchise.id,
                "franchise_name": franchise.name,
                "franchise_slug": franchise.slug,
                "franchise_parts_count": franchise.parts_count,
                "franchise_year_start": franchise.year_start,
                "franchise_year_end": franchise.year_end,
                "franchise_score": franchise.score,
                "franchise_total_duration": franchise_total_duration or None,
                "franchise_all_posters": franchise.all_posters,
                "franchise_entries": [
                    {
                        "id": entry.id,
                        "poster": entry.poster.url if entry.poster and hasattr(entry.poster, "url") else None,
                        "poster_url": entry.poster_url or None,
                        "poster_image_url": entry.poster.url if entry.poster and hasattr(entry.poster, "url") else (entry.poster_url or None),
                        "franchise_order": entry.franchise_order,
                    }
                    for entry in franchise.entries.all().order_by("franchise_order")
                ],
            }

        return {
            "anime_id": anime.id,
            "slug": anime.slug,
            "title": anime.title_ru or anime.title_en or "",
            "title_en": anime.title_en or "",
            "poster": poster_url,
            "screenshots": screenshots,
            "genres": anime.genres or [],
            "rating": anime.score,
            "rating_count": 0,
            "year": anime.year,
            "status": anime.status,
            "episodes": anime.episodes,
            "description": anime.description or "",
            "is_franchise": False,
        }

    def _get_user_genre_preferences_detailed(self, user):
        from apps.users.infrastructure.models.users import UserLibrary
        from collections import Counter
        import math

        if not user:
            return [], {}, set()

        library_items = UserLibrary.objects.filter(
            user=user,
            status__in=("started", "completed")
        ).select_related("anime").only(
            "anime_id", "anime__genres", "rating", "is_favorite",
            "rewatch_count", "updated_at", "current_episode",
            "episodes_watched", "real_episodes_watched",
            "anime__episodes"
        )

        watched_ids = set()
        genre_counter = Counter()
        total_items = 0

        for item in library_items:
            watched_ids.add(item.anime_id)
            total_items += 1

            base_weight = 1.0

            rating_weight = (item.rating or 5) / 10.0
            base_weight *= rating_weight

            if item.is_favorite:
                base_weight += 2.0

            if item.rewatch_count and item.rewatch_count > 0:
                base_weight += max(1, item.rewatch_count) * 0.5

            total_ep = item.anime.episodes or 1
            real_watched = item.real_episodes_watched or item.current_episode or 0
            progress = min(1.0, real_watched / max(1, total_ep))
            base_weight += progress * 1.0

            days_ago = (timezone.now() - item.updated_at).days if item.updated_at else 0
            decay = math.exp(-days_ago / 30.0)
            base_weight *= decay

            anime_genres = item.anime.genres or []
            for genre in anime_genres:
                genre_counter[genre] += base_weight

        if total_items > 0:
            norm_factor = math.sqrt(total_items)
            for genre in genre_counter:
                genre_counter[genre] = genre_counter[genre] / norm_factor

        top_genres = [g for g, _ in genre_counter.most_common(15)]

        return top_genres, dict(genre_counter), watched_ids
    
    def _get_rare_genres(self, genre_counts: dict):
        if not genre_counts:
            return []
        
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1])
        rare_genres = [g for g, _ in sorted_genres[:5]]
        return rare_genres


    def _get_user_watched_profiles(self, user):
        from apps.users.infrastructure.models.users import UserLibrary

        if not user:
            return []

        watched = UserLibrary.objects.filter(
            user=user, status__in=("started", "completed")
        ).select_related("anime").only("anime__id", "anime__genres", "anime__kind", "anime__studios")

        profiles = []
        for item in watched:
            a = item.anime
            profiles.append({
                "id": a.id,
                "genres": set(a.genres or []),
                "kind": a.kind,
                "studios": set(a.studios or []),
            })
        return profiles

    @staticmethod
    def _genre_similarity_score(genres_a, genres_b):
        if not genres_a or not genres_b:
            return 0.0
        intersection = len(genres_a & genres_b)
        union = len(genres_a | genres_b)
        return intersection / union if union else 0.0

    def _pick_diverse_by_genre(self, candidates, genres_pool, limit, exclude_ids):
        import random
        from collections import defaultdict
        
        if not genres_pool:
            random.shuffle(candidates)
            return self._dedupe_franchises(candidates)[:limit]

        genre_buckets = defaultdict(list)
        for anime in candidates:
            if anime.id in exclude_ids:
                continue
            ag = set(anime.genres or [])
            for g in genres_pool:
                if g in ag:
                    genre_buckets[g].append(anime)

        result = []
        seen_ids = set()
        pointers = {g: 0 for g in genres_pool}
        sorted_genres = sorted(genres_pool, key=lambda g: len(genre_buckets.get(g, [])), reverse=True)

        while len(result) < limit:
            added_any = False
            for g in sorted_genres:
                bucket = genre_buckets.get(g, [])
                while pointers[g] < len(bucket):
                    anime = bucket[pointers[g]]
                    pointers[g] += 1
                    if anime.id not in seen_ids:
                        seen_ids.add(anime.id)
                        result.append(anime)
                        added_any = True
                        break
                if len(result) >= limit:
                    break
            if not added_any:
                break

        if len(result) < limit:
            remaining = [a for a in candidates if a.id not in seen_ids and a.id not in exclude_ids]
            random.shuffle(remaining)
            result.extend(remaining[:limit - len(result)])

        return self._dedupe_franchises(result)[:limit]

    def _get_rare_genres_from_db(self, exclude_ids, min_year):
        from apps.anime.infrastructure.models.anime import Anime
        from collections import Counter

        recent = Anime.objects.filter(
            year__gte=min_year,
            score__gte=6.0,
            title_ru__regex=r"[а-яёА-ЯЁ]"
        ).exclude(id__in=exclude_ids).only("genres")

        genre_counter = Counter()
        for anime in recent:
            for g in anime.genres or []:
                genre_counter[g] += 1

        if not genre_counter:
            return []
        rare = [g for g, c in genre_counter.most_common() if 3 <= c <= 15]
        if not rare:
            rare = [g for g, c in genre_counter.most_common()[-20:]]
        return rare[:8]


    def _get_based_on_watched(self, user, exclude_ids, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        if not exclude_ids:
            return []

        profiles = self._get_user_watched_profiles(user)
        if not profiles:
            return []

        all_watched_genres = set()
        for p in profiles:
            all_watched_genres |= p["genres"]

        genre_q = Q()
        for g in list(all_watched_genres)[:15]:
            genre_q |= Q(genres__icontains=g)

        candidates = list(
            Anime.objects.filter(
                genre_q,
                score__gte=6.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:250]
        )

        scored = []
        for anime in candidates:
            ag = set(anime.genres or [])
            max_sim = max(
                (self._genre_similarity_score(ag, p["genres"]) for p in profiles),
                default=0
            )
            type_bonus = 0.05 if any(p["kind"] == anime.kind for p in profiles) else 0
            scored.append((anime, max_sim + type_bonus + (anime.score or 0) * 0.01))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        top = [s[0] for s in scored[:limit * 3]]
        random.shuffle(top)
        return self._dedupe_franchises(top)[:limit]

    def _get_similar_style(self, user, exclude_ids, limit=20, random_genre=None):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        profiles = self._get_user_watched_profiles(user)
        if not profiles:
            return []

        base_profile = random.choice(profiles)
        base_genres = base_profile["genres"]
        base_kind = base_profile["kind"]

        if not base_genres:
            return []

        genre_q = Q()
        for g in base_genres:
            genre_q |= Q(genres__icontains=g)

        candidates = list(
            Anime.objects.filter(
                genre_q,
                score__gte=6.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:200]
        )

        scored = []
        for anime in candidates:
            ag = set(anime.genres or [])
            sim = self._genre_similarity_score(ag, base_genres)
            if base_kind and anime.kind == base_kind:
                sim += 0.1
            scored.append((anime, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [s[0] for s in scored[:limit * 3]]
        random.shuffle(top)
        return self._dedupe_franchises(top)[:limit]

    def _get_top_rated_in_genres_new(self, genres, exclude_ids, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        if not genres:
            return []

        all_picks = []
        seen = set()
        for genre in genres[:6]:
            qs = Anime.objects.filter(
                genres__icontains=genre,
                score__gte=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:10]
            for anime in qs:
                if anime.id not in seen:
                    seen.add(anime.id)
                    all_picks.append(anime)

        random.shuffle(all_picks)
        return self._dedupe_franchises(all_picks)[:limit]

    def _get_new_in_genres_ongoing(self, genres, exclude_ids, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        if not genres:
            return []

        all_picks = []
        seen = set()
        for genre in genres[:6]:
            qs = Anime.objects.filter(
                genres__icontains=genre,
                status="ongoing",
                score__gte=6.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:8]
            for anime in qs:
                if anime.id not in seen:
                    seen.add(anime.id)
                    all_picks.append(anime)

        random.shuffle(all_picks)
        return self._dedupe_franchises(all_picks)[:limit]

    def _get_classics_high_rated(self, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        candidates = list(
            Anime.objects.filter(
                score__gt=7.0,
                year__lte=2010,
                status="finished",
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:150]
        )

        random.shuffle(candidates)
        return self._dedupe_franchises(candidates)[:limit]

    def _get_top_anime_last_year(self, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        from django.utils import timezone

        current_year = timezone.now().year
        min_year = current_year - 1

        candidates = list(
            Anime.objects.filter(
                year__gte=min_year,
                score__gte=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:40]
        )

        return self._dedupe_franchises(candidates)[:limit]

    def _get_new_in_rare_genres(self, rare_genres, exclude_ids, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        from django.utils import timezone
        import random

        current_year = timezone.now().year
        min_year = current_year - 2

        if not rare_genres:
            rare_genres = self._get_rare_genres_from_db(exclude_ids, min_year)

        if not rare_genres:
            return []

        all_picks = []
        seen = set()
        for genre in rare_genres[:8]:
            qs = Anime.objects.filter(
                genres__icontains=genre,
                year__gte=min_year,
                score__gt=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:6]
            for anime in qs:
                if anime.id not in seen:
                    seen.add(anime.id)
                    all_picks.append(anime)

        random.shuffle(all_picks)
        return self._dedupe_franchises(all_picks)[:limit]

    def _get_short_anime(self, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        candidates = list(
            Anime.objects.filter(
                episodes__lte=13,
                episodes__isnull=False,
                score__gt=7.0,
                status="finished",
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:150]
        )

        random.shuffle(candidates)
        return self._dedupe_franchises(candidates)[:limit]

    def _get_movies_high_rated(self, limit=20):
        from apps.anime.infrastructure.models.anime import Anime
        import random

        candidates = list(
            Anime.objects.filter(
                kind="movie",
                episodes=1,
                score__gt=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]",
                franchise__isnull=True,
            )
            .select_related("franchise")
            .order_by("-score")[:150]
        )

        random.shuffle(candidates)
        return self._dedupe_franchises(candidates)[:limit]

    def _get_continue_watching(self, user):
        from apps.users.infrastructure.models.users import UserLibrary
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')

        library_items = (
            UserLibrary.objects.filter(
                user=user, status="started", anime__title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("anime")
            .order_by("-updated_at")[:15]
        )
        result = []
        for item in library_items:
            anime = item.anime
            if not CYRILLIC_RE.search(anime.title_ru or ""):
                continue
            total_episodes = anime.episodes or 1
            progress_percent = (
                min(100, int((item.current_episode / total_episodes) * 100))
                if total_episodes
                else 0
            )
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append(
                {
                    "anime_id": anime.id,
                    "slug": anime.slug,
                    "title": anime.title_ru or anime.title_en or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "current_episode": item.current_episode,
                    "total_episodes": anime.episodes,
                    "progress_percent": progress_percent,
                    "status": anime.status,
                    "last_watched": item.updated_at.isoformat()
                    if item.updated_at
                    else None,
                    "genres": anime.genres or [],
                    "rating": anime.score,
                    "rating_count": 0,
                    "year": anime.year,
                }
            )
        return result

    def _get_rewatch(self, user):
        from apps.users.infrastructure.models.users import UserLibrary
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')

        library_items = (
            UserLibrary.objects.filter(
                user=user, status="completed", anime__title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("anime")
            .order_by("-updated_at")[:10]
        )
        result = []
        for item in library_items:
            anime = item.anime
            if not CYRILLIC_RE.search(anime.title_ru or ""):
                continue
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append(
                {
                    "anime_id": anime.id,
                    "slug": anime.slug,
                    "title": anime.title_ru or anime.title_en or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "completed_date": item.updated_at.isoformat()
                    if item.updated_at
                    else None,
                    "user_rating": item.rating,
                    "genres": anime.genres or [],
                    "rating": anime.score,
                    "rating_count": 0,
                    "year": anime.year,
                    "status": anime.status,
                }
            )
        return result

    def _get_recommendations(self, user):
        from apps.anime.infrastructure.models.anime import Anime
        from collections import Counter

        if not user or not user.is_authenticated:
            top_ids = list(
                Anime.objects.filter(score__gte=7.0, has_cyrillic=True)
                .order_by("-score")
                .values_list("id", flat=True)[:60]
            )
            animes = list(
                Anime.objects.filter(id__in=top_ids).select_related("franchise")
            )
            order = {aid: i for i, aid in enumerate(top_ids)}
            animes.sort(key=lambda a: order[a.id])
            return self._dedupe_franchises(animes)[:20]

        from apps.users.infrastructure.models.users import UserLibrary
        from apps.studios.infrastructure.models.studios import StudioSubscription

        watched_ids = set(
            UserLibrary.objects.filter(
                user=user, status__in=("started", "completed", "on_hold", "planned", "dropped", "hidden")
            ).values_list("anime_id", flat=True)[:500]
        )

        watched_anime_ids = list(
            UserLibrary.objects.filter(
                user=user, status__in=("started", "completed")
            ).values_list("anime_id", flat=True)[:200]
        )
        watched_anime = Anime.objects.filter(
            id__in=watched_anime_ids,
            has_cyrillic=True,
        ).only("id", "genres", "franchise_id", "franchise_order")
        genre_counter = Counter()
        watched_franchise_map = {}
        for anime in watched_anime:
            for g in anime.genres or []:
                genre_counter[g] += 1
            if anime.franchise_id:
                fid = anime.franchise_id
                order = anime.franchise_order or 0
                watched_franchise_map.setdefault(fid, set()).add(order)

        subscribed_studios = list(
            StudioSubscription.objects.filter(user=user)
            .select_related("studio")
            .values_list("studio__name", flat=True)
        )
        if subscribed_studios:
            for studio_obj in StudioSubscription.objects.filter(
                user=user
            ).select_related("studio").only("studio__genre_stats"):
                for g, cnt in (studio_obj.studio.genre_stats or {}).items():
                    genre_counter[g] += max(1, cnt // 10)

        top_genres = [g for g, _ in genre_counter.most_common(10)]

        if top_genres:
            genre_q = Q()
            for g in top_genres:
                genre_q |= Q(genres__icontains=g)
            qs = Anime.objects.filter(
                genre_q, score__gte=6.5, has_cyrillic=True
            )
        else:
            qs = Anime.objects.filter(
                score__gte=7.5, has_cyrillic=True
            )

        studio_bonus_ids = set()
        if subscribed_studios:
            sq = Q()
            for s in subscribed_studios:
                sq |= Q(studios__icontains=s)
            studio_bonus_ids = set(
                Anime.objects.filter(sq, has_cyrillic=True).values_list("id", flat=True)
            )

        top_ids = list(
            qs.exclude(id__in=watched_ids)
            .order_by("-score")
            .values_list("id", flat=True)[:60]
        )
        candidates = list(
            Anime.objects.filter(id__in=top_ids).select_related("franchise")
        )

        filtered_candidates = []
        for anime in candidates:
            if anime.franchise and anime.franchise_id:
                if anime.franchise_id in watched_franchise_map:
                    has_previous = any(
                        order < (anime.franchise_order or 1)
                        for order in watched_franchise_map[anime.franchise_id]
                    )
                    if not has_previous:
                        continue
                else:
                    if (anime.franchise_order or 1) > 1:
                        continue
            filtered_candidates.append(anime)
        candidates = filtered_candidates

        candidates.sort(key=lambda a: (a.score or 0), reverse=True)

        def sort_key(anime):
            base = anime.score or 0
            bonus = 2.0 if anime.id in studio_bonus_ids else 0
            overlap = sum(1 for g in (anime.genres or []) if g in genre_counter)
            return base + bonus + overlap * 0.3

        candidates.sort(key=sort_key, reverse=True)

        def _mmr_select(candidate_list, limit=20, lambda_param=0.7):
            selected = []
            remaining = list(candidate_list)
            if not remaining:
                return selected
            selected.append(remaining[0])
            remaining = remaining[1:]
            while len(selected) < limit and remaining:
                best_mmr = -float('inf')
                best_idx = 0
                selected_genres_set = set()
                for s in selected:
                    selected_genres_set |= set(s.genres or [])
                for i, anime in enumerate(remaining):
                    relevance = anime.score or 0
                    anime_genres = set(anime.genres or [])
                    max_sim = 0.0
                    if selected_genres_set:
                        max_sim = len(anime_genres & selected_genres_set) / max(len(anime_genres), 1)
                    mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                    if mmr > best_mmr:
                        best_mmr = mmr
                        best_idx = i
                selected.append(remaining[best_idx])
                remaining.pop(best_idx)
            return selected

        result_candidates = _mmr_select(candidates, limit=20, lambda_param=0.7)
        return self._dedupe_franchises(result_candidates)[:20]

    def _get_trending(self, user=None):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        from apps.users.infrastructure.models.users import UserLibrary
        from apps.anime.infrastructure.models.anime import Anime

        week_ago = timezone.now() - timedelta(days=7)

        excluded_ids: set = set()
        if user and user.is_authenticated:
            excluded_ids = set(
                UserLibrary.objects.filter(
                    user=user, status__in=("started", "completed", "on_hold", "dropped")
                ).values_list("anime_id", flat=True)
            )

        trending_qs = (
            UserEpisodeProgress.objects.filter(last_watched__gte=week_ago)
            .values("anime_id")
            .annotate(views=Count("user", distinct=True))
            .order_by("-views")[:60]
        )
        trending_ids = [row["anime_id"] for row in trending_qs]

        anime_map = {
            a.id: a
            for a in Anime.objects.filter(
                id__in=trending_ids, has_cyrillic=True
            ).select_related("franchise")
        }

        candidates = []
        for row in trending_qs:
            aid = row["anime_id"]
            if aid in excluded_ids:
                continue
            anime = anime_map.get(aid)
            if not anime:
                continue
            candidates.append((anime, row["views"]))

        seen_franchises = set()
        result = []
        for anime, views in candidates:
            if anime.franchise:
                fid = anime.franchise_id
                if fid not in seen_franchises:
                    seen_franchises.add(fid)
                    d = self._anime_to_dict(anime)
                    d["views_this_week"] = views
                    result.append(d)
            else:
                d = self._anime_to_dict(anime)
                d["views_this_week"] = views
                result.append(d)

            if len(result) >= 20:
                break

        if len(result) < 10:
            existing_ids = {r["anime_id"] for r in result}
            existing_franchises = {
                r.get("franchise_id") for r in result if r.get("franchise_id")
            }
            fallback_top_ids = list(
                Anime.objects.filter(score__isnull=False, has_cyrillic=True)
                .exclude(id__in=excluded_ids | existing_ids)
                .order_by("-score")
                .values_list("id", flat=True)[:60]
            )
            fallback = list(
                Anime.objects.filter(id__in=fallback_top_ids)
                .select_related("franchise")
                .order_by("-score")
            )

            for anime in fallback:
                if anime.franchise:
                    fid = anime.franchise_id
                    if fid in existing_franchises:
                        continue
                    existing_franchises.add(fid)
                if anime.id in existing_ids:
                    continue
                existing_ids.add(anime.id)
                result.append(self._anime_to_dict(anime))
                if len(result) >= 20:
                    break

        return result




class WatchHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _visible_queryset(user):
        progress = UserEpisodeProgress.objects.filter(
            user=user, anime_id=OuterRef("pk")
        )
        latest = progress.order_by(
            "-last_watched", "-season_number", "-episode_number"
        )
        suppression = WatchHistorySuppression.objects.filter(
            user=user, anime_id=OuterRef("pk")
        )

        return (
            Anime.objects.filter(episode_progress__user=user)
            .annotate(
                history_last_watched=Max(
                    "episode_progress__last_watched",
                    filter=Q(episode_progress__user=user),
                ),
                watched_episode_count=Count(
                    "episode_progress",
                    filter=Q(
                        episode_progress__user=user,
                        episode_progress__status__in=["watched", "skipped"],
                    ),
                    distinct=True,
                ),
                latest_season=Subquery(latest.values("season_number")[:1]),
                latest_episode=Subquery(latest.values("episode_number")[:1]),
                latest_status=Subquery(latest.values("status")[:1]),
                latest_position=Subquery(latest.values("last_position")[:1]),
                latest_duration=Subquery(latest.values("duration")[:1]),
                hidden_at=Subquery(suppression.values("hidden_at")[:1]),
            )
            .filter(
                Q(hidden_at__isnull=True)
                | Q(history_last_watched__gt=F("hidden_at"))
            )
            .order_by("-history_last_watched", "-pk")
        )

    @staticmethod
    def _serialize(anime):
        poster = anime.poster_url or ""
        try:
            if anime.poster and hasattr(anime.poster, "url"):
                poster = anime.poster.url
        except Exception:
            pass

        episode = anime.latest_episode or 1
        season = anime.latest_season or 1
        total = anime.progress_total or anime.episodes or 0
        latest_finished = anime.latest_status in ("watched", "skipped")
        continue_episode = episode
        continue_season = season
        if latest_finished and (not total or episode < total):
            continue_episode = episode + 1

        duration = anime.latest_duration or 0
        position = anime.latest_position or 0
        episode_percent = (
            min(100, round(position / duration * 100)) if duration else
            (100 if latest_finished else 0)
        )
        series_percent = (
            min(100, round(anime.watched_episode_count / total * 100))
            if total else 0
        )

        return {
            "anime_id": anime.id,
            "slug": anime.slug,
            "title": anime.title_ru or anime.title_en or "Без названия",
            "title_en": anime.title_en or "",
            "poster": poster,
            "year": anime.year,
            "kind": anime.kind,
            "kind_label": anime.get_kind_display(),
            "score": anime.score,
            "genres": anime.genres or [],
            "season_number": season,
            "episode": episode,
            "continue_season": continue_season,
            "continue_episode": continue_episode,
            "total_episodes": total,
            "watched_episodes": anime.watched_episode_count,
            "episode_status": anime.latest_status,
            "position": position,
            "duration": duration or None,
            "episode_percent": episode_percent,
            "series_percent": series_percent,
            "last_watched": anime.history_last_watched.isoformat(),
            "is_series_completed": bool(total and anime.watched_episode_count >= total),
        }

    def get(self, request):
        base_queryset = self._visible_queryset(request.user)
        summary = {
            "total": base_queryset.count(),
            "in_progress": base_queryset.filter(latest_status="in_progress").count(),
            "watched": base_queryset.filter(
                latest_status__in=["watched", "skipped"]
            ).count(),
        }

        queryset = base_queryset
        query = request.query_params.get("search", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title_ru__icontains=query) | Q(title_en__icontains=query)
            )

        state = request.query_params.get("state", "all")
        if state == "in_progress":
            queryset = queryset.filter(latest_status="in_progress")
        elif state == "watched":
            queryset = queryset.filter(latest_status__in=["watched", "skipped"])

        paginator = WatchHistoryPagination()
        page = paginator.paginate_queryset(queryset, request)
        response = paginator.get_paginated_response(
            [self._serialize(anime) for anime in page]
        )
        response.data["summary"] = summary
        return response

    def post(self, request):
        if request.data.get("action") != "restore":
            return Response({"error": "Неизвестное действие"}, status=400)
        restored, _ = WatchHistorySuppression.objects.filter(
            user=request.user
        ).delete()
        return Response({"restored": restored})

    def delete(self, request):
        anime_ids = list(
            UserEpisodeProgress.objects.filter(user=request.user)
            .values_list("anime_id", flat=True)
            .distinct()
        )
        now = timezone.now()
        existing_ids = set(
            WatchHistorySuppression.objects.filter(
                user=request.user, anime_id__in=anime_ids
            ).values_list("anime_id", flat=True)
        )
        WatchHistorySuppression.objects.filter(
            user=request.user, anime_id__in=anime_ids
        ).update(hidden_at=now)
        WatchHistorySuppression.objects.bulk_create(
            [
                WatchHistorySuppression(
                    user=request.user, anime_id=anime_id, hidden_at=now
                )
                for anime_id in anime_ids
                if anime_id not in existing_ids
            ],
            ignore_conflicts=True,
        )
        return Response({"hidden": len(anime_ids)})


class WatchHistoryItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, anime_id):
        if not UserEpisodeProgress.objects.filter(
            user=request.user, anime_id=anime_id
        ).exists():
            return Response({"error": "Запись истории не найдена"}, status=404)
        WatchHistorySuppression.objects.update_or_create(
            user=request.user,
            anime_id=anime_id,
            defaults={"hidden_at": timezone.now()},
        )
        return Response(status=204)

    def post(self, request, anime_id):
        restored, _ = WatchHistorySuppression.objects.filter(
            user=request.user, anime_id=anime_id
        ).delete()
        return Response({"restored": bool(restored)})


class EpisodeProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, anime_id):
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        try:
            rows = list(
                UserEpisodeProgress.objects.filter(user=request.user, anime=anime)
            )
            data = []
            for r in rows:
                try:
                    pct = r.progress_percent
                except Exception:
                    pct = (
                        round(r.last_position / r.duration * 100)
                        if (r.duration and r.duration > 0)
                        else 0
                    )
                data.append(
                    {
                        "season_number": r.season_number,
                        "episode_number": r.episode_number,
                        "status": r.status,
                        "last_position": r.last_position,
                        "duration": r.duration,
                        "progress_percent": pct,
                        "is_manually_marked": r.is_manually_marked,
                        "watched_at": r.watched_at.isoformat()
                        if r.watched_at
                        else None,
                    }
                )
            watched_count = sum(1 for r in rows if r.status in ("watched", "skipped"))
            total = anime.progress_total or anime.episodes or 0
            return Response(
                {
                    "anime_id": anime_id,
                    "total": total,
                    "watched_count": watched_count,
                    "percent": round(watched_count / total * 100) if total else 0,
                    "episodes": data,
                }
            )
        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            return Response(
                {
                    "anime_id": anime_id,
                    "total": anime.progress_total or anime.episodes or 0,
                    "watched_count": 0,
                    "percent": 0,
                    "episodes": [],
                    "warning": str(e),
                }
            )

    def post(self, request, anime_id):
        episode_number = request.data.get("episode_number")
        season_number = self._season_number(request)
        last_position = request.data.get("last_position", 0)
        duration = request.data.get("duration")
        action_type = request.data.get("action", "progress")
        if action_type == "bulk":
            return self._bulk_sync(request, anime_id)
        if action_type == "mark":
            return self._mark_watched(
                request, anime_id, episode_number, manual=True,
                season_number=season_number,
            )
        if action_type == "skip":
            return self._skip_episode(
                request, anime_id, episode_number, season_number=season_number
            )
        if episode_number is None:
            return Response({"error": "Не указан episode_number"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        ep, created = UserEpisodeProgress.objects.get_or_create(
            user=request.user,
            anime=anime,
            season_number=season_number,
            episode_number=episode_number,
            defaults={"status": "in_progress"},
        )
        previous_status = ep.status
        if ep.status not in ("watched", "skipped"):
            ep.last_watched = timezone.now()
            ep.last_position = int(last_position)
            if duration:
                ep.duration = int(duration)
            if ep.duration and ep.duration > 0:
                pct = ep.last_position / ep.duration * 100
                if pct >= 85:
                    return self._mark_watched(
                        request, anime_id, episode_number,
                        instance=ep, season_number=season_number,
                    )
            ep.status = "in_progress"
            ep.save(update_fields=["last_position", "duration", "status", "last_watched"])
            if created or previous_status != "in_progress":
                self._sync_library(request.user, anime)
        return Response(
            {
                "season_number": ep.season_number,
                "episode_number": ep.episode_number,
                "status": ep.status,
                "last_position": ep.last_position,
                "progress_percent": ep.progress_percent,
            }
        )

    @staticmethod
    def _season_number(request):
        try:
            return max(0, int(request.data.get("season_number", 1)))
        except (TypeError, ValueError):
            return 1

    def _mark_watched(
        self, request, anime_id, episode_number, manual=False, instance=None,
        season_number=1,
    ):
        from django.utils import timezone

        if episode_number is None:
            return Response({"error": "Не указан episode_number"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        if instance is None:
            instance, _ = UserEpisodeProgress.objects.get_or_create(
                user=request.user,
                anime=anime,
                season_number=season_number,
                episode_number=episode_number,
            )
        instance.status = "watched"
        instance.is_manually_marked = manual
        instance.watched_at = timezone.now()
        if instance.duration and not instance.last_position:
            instance.last_position = instance.duration
        instance.save()
        self._sync_library(request.user, anime)
        return Response(
            {
                "season_number": instance.season_number,
                "episode_number": instance.episode_number,
                "status": "watched",
                "is_manually_marked": manual,
                "auto_marked": not manual,
            }
        )

    def _skip_episode(self, request, anime_id, episode_number, season_number=1):
        if episode_number is None:
            return Response({"error": "Не указан episode_number"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        ep, _ = UserEpisodeProgress.objects.get_or_create(
            user=request.user,
            anime=anime,
            season_number=season_number,
            episode_number=episode_number,
        )
        ep.status = "skipped"
        ep.is_manually_marked = True
        ep.last_watched = timezone.now()
        ep.save(update_fields=["status", "is_manually_marked", "last_watched"])
        self._sync_library(request.user, anime)
        return Response(
            {
                "season_number": ep.season_number,
                "episode_number": episode_number,
                "status": "skipped",
            }
        )

    def _bulk_sync(self, request, anime_id):
        reset = request.data.get("reset", False)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        from apps.users.application.library_episodes import (
            reset_watched_progress,
            set_watched_progress,
            set_watched_progress_by_seasons,
        )
        if reset:
            reset_watched_progress(request.user, anime)
            return Response({"reset": True, "watched_count": 0})

        seasons = request.data.get("seasons")
        if isinstance(seasons, (list, dict)):
            items = (
                seasons.items() if isinstance(seasons, dict) else seasons
            )
            counts = set_watched_progress_by_seasons(request.user, anime, items)
            return Response(
                {
                    "watched_count": sum(counts.values()),
                    "seasons": [
                        {
                            "season_number": season,
                            "watched_up_to": watched,
                        }
                        for season, watched in counts.items()
                    ],
                }
            )

        watched_up_to = request.data.get("watched_up_to")
        if watched_up_to is None:
            return Response({"error": "Не указан watched_up_to"}, status=400)
        try:
            total = int(watched_up_to)
            season_number = max(0, int(request.data.get("season_number", 1)))
        except (TypeError, ValueError):
            return Response({"error": "Некорректное значение"}, status=400)
        marked = set_watched_progress(
            request.user, anime, total, season=season_number
        )
        return Response(
            {
                "watched_count": marked,
                "watched_up_to": total,
                "season_number": season_number,
            }
        )

    def _sync_library(self, user, anime):
        try:
            from apps.users.application.library_episodes import sync_library_from_episode_rows
            sync_library_from_episode_rows(user, anime)
        except Exception as e:
            logging.getLogger(__name__).warning("_sync_library error: %s", e)


class EpisodeProgressUndoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, anime_id, episode_number):
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        try:
            season_number = max(0, int(request.data.get("season_number", 1)))
        except (TypeError, ValueError):
            season_number = 1
        try:
            progress = UserEpisodeProgress.objects.get(
                user=request.user,
                anime=anime,
                season_number=season_number,
                episode_number=episode_number,
            )

            if progress.status == "watched":
                progress.status = "not_started"
                progress.is_manually_marked = False
                progress.watched_at = None
                progress.last_position = 0
                progress.save(
                    update_fields=[
                        "status",
                        "is_manually_marked",
                        "watched_at",
                        "last_position",
                    ]
                )

                self._sync_library(request.user, anime)

                prev_watched = (
                    UserEpisodeProgress.objects.filter(
                        user=request.user,
                        anime=anime,
                        status__in=["watched", "skipped"],
                    )
                    .filter(
                        Q(season_number__lt=season_number)
                        | Q(
                            season_number=season_number,
                            episode_number__lt=episode_number,
                        )
                    )
                    .order_by("-season_number", "-episode_number")
                    .first()
                )

                return Response(
                    {
                        "success": True,
                        "season_number": season_number,
                        "episode_number": episode_number,
                        "previous_season": prev_watched.season_number
                        if prev_watched
                        else None,
                        "previous_episode": prev_watched.episode_number
                        if prev_watched
                        else None,
                        "message": f"Отменён просмотр серии {episode_number}",
                    }
                )
            else:
                return Response(
                    {
                        "success": False,
                        "message": "Серия не была отмечена как просмотренная",
                    },
                    status=400,
                )

        except UserEpisodeProgress.DoesNotExist:
            return Response(
                {"success": False, "message": "Запись о просмотре не найдена"},
                status=404,
            )
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"EpisodeProgressUndo error: {e}")
            return Response({"error": str(e)}, status=500)

    def _sync_library(self, user, anime):
        try:
            from apps.users.application.library_episodes import sync_library_from_episode_rows
            sync_library_from_episode_rows(user, anime)

        except Exception as e:
            logging.getLogger(__name__).warning("_sync_library error: %s", e)


class AnimeThemesView(APIView):
    permission_classes = [permissions.AllowAny]

    def _get_cache_key(self, anime_id, episode, season, translation_id):
        tid = translation_id or 'all'
        return f'anime_themes:{anime_id}:{season}:{episode}:{tid}'

    def _get_episode_url(self, anime, episode, season, translation_id):
        shikimori_id = anime.shikimori_id or anime.kodik_id
        if not shikimori_id:
            return None
        return anime_service.get_episode_url(
            shikimori_id, episode, str(season), translation_id
        )

    def _get_segments(self, episode_url, user_ip="1.1.1.1"):
        return anime_service.get_video_segments(episode_url, user_ip)

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.query_params.get("episode", 1))
        season = int(request.query_params.get("season", 1))
        translation_id = request.query_params.get("translation_id")
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
            0
        ].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        try:
            episode_url = self._get_episode_url(anime, episode, season, translation_id)
            if not episode_url:
                return Response(
                    {
                        "opening": None,
                        "ending": None,
                        "error": "Серия не найдена",
                    },
                    status=404,
                )

            opening, ending = self._get_segments(episode_url, user_ip=user_ip)

            return Response(
                {
                    "opening": opening,
                    "ending": ending,
                    "source": "kodik_video_links",
                }
            )

        except requests.RequestException as e:
            return Response(
                {
                    "opening": None,
                    "ending": None,
                    "error": f"Ошибка запроса: {e}",
                },
                status=503,
            )
        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            return Response(
                {"opening": None, "ending": None, "error": str(e)}, status=500
            )


class KodikVideoUrlView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [SearchRateThrottle]

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.query_params.get("episode", 1))
        season = int(request.query_params.get("season", 1))
        translation_id = request.query_params.get("translation_id")

        try:
            external_id = anime.shikimori_id or anime.kodik_id
            if not external_id:
                return Response({"error": "У аниме нет внешнего ID"}, status=404)
            episode_info = anime_service.get_episode_info(
                str(external_id), episode, str(season), translation_id
            )
            if not episode_info:
                return Response({"error": "Серия не найдена"}, status=404)

            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            user_ip = forwarded_for.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")
            links = anime_service.get_video_links(episode_info["url"], user_ip)
            sources = [
                {"quality": quality, "url": url}
                for quality, url in sorted(
                    links.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 0, reverse=True
                )
            ]
            previews = episode_info.get("screenshots") or []
            return Response(
                {
                    "m3u8_url": sources[0]["url"],
                    "sources": sources,
                    "preview": previews[0] if previews else None,
                    "episode": episode,
                    "season": season,
                    "source": "kodik_video_api",
                    "delivery": "direct",
                },
                headers={"Cache-Control": "private, no-store"},
            )

        except requests.RequestException as e:
            return Response({"error": f"Ошибка запроса: {e}"}, status=503)
        except RuntimeError as e:
            logger.warning("Direct player unavailable: %s", e)
            return Response({"error": str(e), "fallback": "kodik"}, status=503)
        except Exception:
            logger.exception("Direct player failed")
            return Response({"error": "Не удалось загрузить видео", "fallback": "kodik"}, status=503)


class KodikClipDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [StaffExemptRateThrottle]

    def _get_episode_player_url(self, anime, episode, season, translation_id):
        shikimori_id = anime.shikimori_id or anime.kodik_id
        if not shikimori_id:
            return None
        return anime_service.get_episode_url(
            shikimori_id, episode, str(season), translation_id
        )

    def _get_m3u8_via_api(self, episode_url, user_ip="1.1.1.1"):
        return anime_service.get_m3u8_url(episode_url, user_ip)

    def get(self, request, pk):
        is_premium = True
        if hasattr(request.user, 'profile_settings'):
            is_premium = request.user.profile_settings.is_premium
        
        if not is_premium:
            return Response(
                {"error": "Доступно только премиум пользователям"}, status=403
            )

        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.query_params.get("episode", 1))
        season = int(request.query_params.get("season", 1))
        translation_id = request.query_params.get("translation_id")
        start_sec = int(request.query_params.get("start", 0))
        end_sec = int(request.query_params.get("end", 120))
        label = request.query_params.get("label", "clip")
        format_type = request.query_params.get("format", "video")  
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
            0
        ].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        episode_url = self._get_episode_player_url(
            anime, episode, season, translation_id
        )
        if not episode_url:
            return Response({"error": "Не удалось найти серию"}, status=404)

        m3u8_url = self._get_m3u8_via_api(episode_url, user_ip=user_ip)
        if not m3u8_url:
            return Response({"error": "Не удалось получить видео"}, status=404)

        import subprocess
        import tempfile
        import os
        from django.http import HttpResponse
        import logging

        logger = logging.getLogger(__name__)
        duration = end_sec - start_sec
        if duration <= 0:
            return Response({"error": "end должен быть больше start"}, status=400)

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            if not os.path.exists("/usr/bin/ffmpeg"):
                logger.error("ffmpeg не найден по пути /usr/bin/ffmpeg")
                return Response({"error": "Сервис ffmpeg недоступен"}, status=503)

            if format_type == "audio":
                cmd = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-ss", str(start_sec),
                    "-i", m3u8_url,
                    "-t", str(duration),
                    "-vn",  
                    "-acodec", "libmp3lame",
                    "-b:a", "192k",
                    "-f", "mp3",
                    "pipe:1",
                ]
                content_type = "audio/mpeg"
                extension = "mp3"
            else:
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    tmp_path = tmp.name
                
                cmd = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-ss", str(start_sec),
                    "-i", m3u8_url,
                    "-t", str(duration),
                    "-c", "copy",
                    "-movflags", "+faststart",
                    tmp_path
                ]
                content_type = "video/mp4"
                extension = "mp4"
            
            logger.info(f"FFmpeg команда: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if process.returncode != 0:
                logger.error(f"FFmpeg stderr: {process.stderr}")
                return Response(
                    {"error": f"Ошибка ffmpeg: {process.stderr[:200]}"},
                    status=500
                )
            
            with open(tmp_path, 'rb') as f:
                output = f.read()
            
            response = HttpResponse(output, content_type=content_type)
            from django.utils.encoding import escape_uri_path
            filename = f"{label.replace(' ', '_')}_{pk}_{episode}.{extension}"
            response["Content-Disposition"] = f"attachment; filename*=UTF-8''{escape_uri_path(filename)}"
            response["Content-Length"] = len(output)
            return response

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout после 120 секунд")
            return Response({"error": "Нарезка видео заняла слишком много времени"}, status=504)
        except Exception as e:
            logger.exception(f"Clip download error: {e}")
            return Response({"error": f"Внутренняя ошибка сервера: {str(e)}"}, status=500)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class AdminTodayAddedAnimeView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        animes = Anime.objects.filter(created_at__gte=today_start, title_ru__regex=r"[а-яёА-ЯЁ]").order_by(
            "-created_at"
        )

        data = []
        for anime in animes[:100]:  
            data.append(
                {
                    "id": anime.id,
                    "title_ru": anime.title_ru or anime.title_en or "",
                    "shikimori_id": anime.shikimori_id,
                    "mal_id": anime.mal_id,
                    "year": anime.year,
                    "status": anime.status,
                    "kind": anime.kind,
                    "episodes": anime.episodes,
                    "score": anime.score,
                    "poster_url": anime.poster_url,
                    "created_at": anime.created_at.isoformat(),
                    "data_source": anime.data_source,
                }
            )

        return Response(
            {
                "count": len(data),
                "today_start": today_start.isoformat(),
                "results": data,
            }
        )


class AnimeEpisodeNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        subscription, created = AnimeEpisodeNotification.objects.get_or_create(
            user=request.user, anime=anime
        )

        if not created:
            subscription.delete()
            return Response({"subscribed": False})

        return Response({"subscribed": True})

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        subscribed = AnimeEpisodeNotification.objects.filter(
            user=request.user, anime=anime
        ).exists()

        return Response({"subscribed": subscribed})


class CatalogSettingsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        settings_obj, _ = CatalogSettings.objects.get_or_create(pk=1)
        serializer = CatalogSettingsSerializer(settings_obj)
        return Response(serializer.data)

    def patch(self, request):
        if not request.user.is_staff:
            return Response({"error": "Forbidden"}, status=403)

        settings_obj, _ = CatalogSettings.objects.get_or_create(pk=1)
        serializer = CatalogSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        from apps.anime.application.catalog_visibility import invalidate
        invalidate()
        return Response(serializer.data)


class CalendarView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        import hashlib
        from apps.anime.infrastructure.models.read_models import CalendarSnapshot
        tz_name = request.query_params.get('timezone', 'UTC')
        try:
            device_tz = ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError):
            return Response({'timezone': 'Укажите корректный часовой пояс IANA'}, status=400)
        now = timezone.now()
        today = now.astimezone(device_tz).date()
        month_param = request.query_params.get("month")
        search = request.query_params.get("search")
        revision = CalendarSnapshot.objects.filter(key='kodik').values_list('updated_at', flat=True).first()
        cache_identity = f"{revision}:{tz_name}:{today}:{month_param or today.strftime('%Y-%m')}:{search or ''}"
        cache_key = 'calendar:v5:' + hashlib.sha256(cache_identity.encode()).hexdigest()
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return Response(cached)

        if month_param:
            try:
                year, month = map(int, month_param.split("-"))
                target_year = year
                target_month = month
            except (ValueError, TypeError):
                target_year = today.year
                target_month = today.month
        else:
            target_year = today.year
            target_month = today.month

        if not (1 <= target_month <= 12 and 1 <= target_year <= 9998):
            return Response({'month': 'Укажите корректный месяц YYYY-MM'}, status=400)
        month_start = today.replace(year=target_year, month=target_month, day=1)
        if target_month == 12:
            month_end = today.replace(year=target_year + 1, month=1, day=1)
        else:
            month_end = today.replace(year=target_year, month=target_month + 1, day=1)

        grid_start = month_start - timedelta(days=month_start.weekday())
        grid_end = month_end + timedelta(days=(-month_end.weekday()) % 7)
        start = datetime.combine(grid_start, datetime.min.time(), tzinfo=device_tz)
        end = datetime.combine(grid_end, datetime.min.time(), tzinfo=device_tz)
        all_history = bool(search and not month_param)

        try:
            raw_entries = anime_service.get_calendar(censored=True,
                start=None if all_history else start, end=None if all_history else end)
        except Exception:
            raw_entries = []

        transformed: List[Dict[str, Any]] = []
        search_query = search.strip() if search else ""

        for raw in raw_entries:
            aired_at_str = raw.get("aired_at") or ""
            aired_at = None
            local_day = None
            time_str = ""

            if aired_at_str:
                try:
                    aired_at = datetime.fromisoformat(aired_at_str.replace("Z", "+00:00"))
                    if not aired_at.tzinfo:
                        from datetime import timezone as dt_timezone
                        aired_at = aired_at.replace(tzinfo=dt_timezone.utc)
                    aired_at = aired_at.astimezone(device_tz)
                    local_day = aired_at.date()
                    time_str = aired_at.strftime("%H:%M")
                except (ValueError, TypeError):
                    pass

            if local_day is None:
                continue

            if not all_history and not (grid_start <= local_day < grid_end):
                continue

            poster_url = raw.get("poster_url") or ""
            if not poster_url:
                image = raw.get("image") or {}
                poster_url = image.get("original", "") or ""

            title_ru = (raw.get("russian") or raw.get("name") or "").strip()
            title_en = (raw.get("english") or raw.get("name") or "").strip()

            if search_query:
                titles = [
                    title_ru,
                    title_en,
                    raw.get("japanese", "") or "",
                ]
                if not flexible_title_match(search_query, *titles):
                    continue

            year_val = None
            if aired_at:
                year_val = aired_at.year

            transformed.append({
                "local_day": local_day,
                "aired_at": aired_at,
                "time": time_str,
                "episode_number": raw.get("episode"),
                "is_upcoming": aired_at > now,
                "schedule_uncertain": raw.get('schedule_uncertain', False),
                "calendar_release_id": raw.get('calendar_release_id'),
                "shikimori_id": raw.get("id"),
                "title_ru": title_ru,
                "title_en": title_en,
                "title_jp": (raw.get("japanese") or "").strip(),
                "year": year_val,
                "kind": raw.get("kind", ""),
                "episodes": raw.get("episodes"),
                "score": raw.get("score"),
                "poster_url": poster_url,
            })

        transformed.sort(key=lambda e: (e["local_day"], e["aired_at"] or datetime.min.replace(tzinfo=None)))

        local_anime = {
            anime.shikimori_id: anime
            for anime in Anime.objects.filter(
                shikimori_id__in={entry["shikimori_id"] for entry in transformed if entry["shikimori_id"]}
            ).only("id", "shikimori_id", "slug")
        }

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for entry in transformed:
            key = entry["local_day"].isoformat()
            grouped.setdefault(key, []).append(entry)

        weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        days = []
        for date_str, items in grouped.items():
            local_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            weekday_idx = local_date.weekday()
            days.append({
                "date": date_str,
                "weekday": weekday_idx,
                "weekday_name": weekday_names[weekday_idx],
                "in_month": local_date.month == target_month and local_date.year == target_year,
                "is_today": local_date == today,
                "items": [
                    {
                        "aired_at": entry["aired_at"].isoformat() if entry["aired_at"] else None,
                        "local_day": entry["local_day"].isoformat(),
                        "time": entry["time"],
                        "episode_number": entry["episode_number"],
                        "is_upcoming": entry["is_upcoming"],
                        "schedule_uncertain": entry['schedule_uncertain'],
                        "calendar_release_id": entry['calendar_release_id'],
                        "anime": {
                            "id": local_anime[entry["shikimori_id"]].pk if entry["shikimori_id"] in local_anime else entry["shikimori_id"],
                            "slug": local_anime[entry["shikimori_id"]].slug if entry["shikimori_id"] in local_anime else None,
                            "shikimori_id": entry["shikimori_id"],
                            "title_ru": entry["title_ru"],
                            "title_en": entry["title_en"],
                            "title_jp": entry["title_jp"],
                            "year": entry["year"],
                            "kind": entry["kind"],
                            "episodes": entry["episodes"],
                            "score": entry["score"],
                            "poster_url": entry["poster_url"],
                            "poster_image_url": entry["poster_url"],
                            "status": None,
                            "genres": [],
                            "franchise_id": None,
                            "release_date": entry["aired_at"].isoformat() if entry["aired_at"] else None,
                            "release_date_string": entry["aired_at"].strftime("%d.%m.%Y") if entry["aired_at"] else None,
                        },
                    }
                    for entry in items
                ],
            })

        days.sort(key=lambda d: d["date"])

        next_month = today.replace(year=target_year, month=target_month, day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        prev_month = today.replace(year=target_year, month=target_month, day=1) - timedelta(days=1)

        response_data = {
            "month_key": month_start.strftime("%Y-%m"),
            "year": target_year,
            "month": target_month,
            "month_label": month_start.strftime("%B %Y"),
            "today": today.isoformat(),
            "grid_start": grid_start.isoformat(),
            "grid_end": grid_end.isoformat(),
            "timezone": tz_name,
            "has_prev": True,
            "has_next": True,
            "next_month_key": next_month.strftime("%Y-%m"),
            "prev_month_key": prev_month.strftime("%Y-%m"),
            "search": search,
            "total": len(transformed),
            "days": days,
        }
        safe_cache_set(cache_key, response_data, timeout=60)
        return Response(response_data)


class KodikUserAddView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ImportRateThrottle]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post(self, request):
        if KodikImportView._body_too_large(request):
            return Response({"error": "request_body_too_large"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        shikimori_id = request.data.get("shikimori_id")
        shikimori_ids = request.data.get("shikimori_ids")
        title = request.data.get("title", "")
        download_posters = bool(request.data.get("download_posters", False))

        if shikimori_ids:
            if not isinstance(shikimori_ids, list) or not 1 <= len(shikimori_ids) <= 100:
                return Response({"error": "shikimori_ids должен содержать от 1 до 100 ID"}, status=400)
            if any(isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0 for value in shikimori_ids):
                return Response({"error": "Все shikimori_ids должны быть положительными целыми"}, status=400)
            ids = list(dict.fromkeys(int(value) for value in shikimori_ids))
            limited = self._reserve(request, ids)
            if limited:
                return limited

            existing = set(Anime.objects.filter(shikimori_id__in=ids).values_list("shikimori_id", flat=True))
            missing_ids = [identifier for identifier in ids if identifier not in existing]

            progress_token = str(uuid.uuid4())
            progress_cache = {
                "token": progress_token,
                "progress_key": f"import_progress:{progress_token}",
                "total": len(missing_ids),
                "current": 0,
                "current_title": "Подготовка...",
            }
            safe_cache_set(f"import_progress:{progress_token}", progress_cache, timeout=3600)

            results = []
            imported_anime = []
            errors = []

            def _do_import(sid: int):
                import logging
                logger = logging.getLogger(__name__)
                try:
                    logger.info(f"Starting import for shikimori_id={sid}")
                    item = self._import_one(sid, download_posters=download_posters, progress_cache=progress_cache)
                    logger.info(f"Completed import for shikimori_id={sid}")
                    return {
                        "shikimori_id": sid,
                        "title": item.get("title", title),
                        "slug": item.get("slug"),
                        "ok": True,
                        "message": "Аниме импортировано",
                        "anime_id": item.get("anime_id"),
                    }
                except Exception as e:
                    logger.error(f"Import failed for shikimori_id={sid}: {e}")
                    return {
                        "shikimori_id": sid,
                        "title": title,
                        "ok": False,
                        "message": str(e)[:200],
                        "anime_id": None,
                    }

            for sid in missing_ids:
                result = _do_import(sid)
                results.append({
                    "shikimori_id": result["shikimori_id"],
                    "title": result["title"],
                    "slug": result.get("slug", ""),
                    "ok": result["ok"],
                    "message": result["message"],
                })
                if result.get("anime_id"):
                    imported_anime.append(result["anime_id"])
                if not result["ok"]:
                    errors.append(result["message"])

            if imported_anime:
                self._build_franchise_for_ids(ids, imported_anime)

            return Response({
                "results": results,
                "message": f"Обработано: {len(results)}; уже существовало: {len(existing)}",
                "existing": sorted(existing),
                "progress_token": progress_token,
            })

        if shikimori_id:
            try:
                identifier = int(shikimori_id)
                if identifier <= 0:
                    raise ValueError
                limited = self._reserve(request, [identifier])
                if limited:
                    return limited
                existing = Anime.objects.filter(shikimori_id=identifier).only("id", "slug", "title_ru").first()
                if existing:
                    return Response({"results": [{"shikimori_id": identifier, "title": existing.title_ru, "slug": existing.slug, "ok": True, "existing": True}], "message": "Аниме уже существует"})
                item = self._import_one(identifier, download_posters=download_posters)
                return Response({
                    "results": [{
                        "shikimori_id": int(shikimori_id),
                        "title": item.get("title", title),
                        "slug": item.get("slug"),
                        "ok": True,
                        "message": "Аниме импортировано",
                    }],
                    "message": "Аниме импортировано",
                })
            except Exception as e:
                return Response({
                    "results": [{
                        "shikimori_id": shikimori_id,
                        "title": title,
                        "ok": False,
                        "message": str(e)[:200],
                    }],
                    "message": str(e)[:200],
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Нет shikimori_id"}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _reserve(request, identifiers):
        from apps.anime.application.kodik_limits import KodikLimitExceeded, reserve_unique_ids
        try:
            reserve_unique_ids(request, identifiers)
        except KodikLimitExceeded as exc:
            return Response(
                {"error": "hourly_limit_exceeded"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(exc.retry_after)},
            )
        return None

    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"error": "Token required"}, status=status.HTTP_400_BAD_REQUEST)

        progress = safe_cache_get(f"import_progress:{token}")
        if not progress:
            return Response({"error": "Progress not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "total": progress.get("total", 0),
            "current": progress.get("current", 0),
            "current_title": progress.get("current_title", ""),
            "percent": round(progress.get("current", 0) / max(progress.get("total", 1), 1) * 100),
        })

    def _import_one(self, shikimori_id: int, download_posters: bool = False, progress_cache: dict = None) -> dict:
        item = anime_service.get_by_shikimori_id(shikimori_id)
        if not item:
            raise ValueError("Аниме не найдено")

        if progress_cache is not None:
            progress_cache["current"] = progress_cache.get("current", 0) + 1
            progress_cache["current_title"] = f"Импорт: {shikimori_id}"
            progress_key = f"import_progress:{progress_cache['token']}"
            safe_cache_set(progress_cache["progress_key"], progress_cache, timeout=3600)

        anime, created = anime_service.import_anime(item, update_existing=True, download_posters=download_posters, skip_video_sync=True)
        slug = getattr(anime, "slug", None) or ""
        title = anime.title_ru or anime.title_en or ""

        try:
            from apps.anime.application.tasks import sync_anime_metadata_task
            sync_anime_metadata_task.delay(anime.id)
        except Exception:
            pass

        return {"slug": slug, "title": title, "created": created, "anime_id": anime.id}

    def _build_franchise_for_ids(self, shikimori_ids: list[int], anime_ids: list[int]) -> None:
        from apps.anime.application.franchise_sync import sync_franchise
        from apps.anime.application.recommendations import invalidate_catalog
        if shikimori_ids:
            result = sync_franchise(shikimori_ids[0])
            if result.get('linked'):
                invalidate_catalog()


class KodikMyRequestsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"results": []})
