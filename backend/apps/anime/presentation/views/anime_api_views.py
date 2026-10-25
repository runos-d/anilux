from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.anime.application.cache_utils import safe_cache_get, safe_cache_set
from apps.anime.application.catalog_visibility import hidden_values, visible_anime
import logging



logger = logging.getLogger(__name__)


class GenresAPI(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        try:
            revision = safe_cache_get('catalog:revision', 0)
            cache_key = f'catalog:facets:genres:v1:{revision}'
            cached = safe_cache_get(cache_key)
            if cached is not None:
                return Response({'genres': cached})
            distinct_genres = visible_anime().exclude(genres__isnull=True).exclude(genres=[]).values_list('genres', flat=True)
            blocked = hidden_values('genre')
            genre_set = set()
            for genres_list in distinct_genres:
                if isinstance(genres_list, list):
                    for genre in genres_list:
                        if isinstance(genre, str) and genre.strip():
                            if genre.strip().casefold() not in blocked:
                                genre_set.add(genre.strip())
                        elif isinstance(genre, dict):
                            name = genre.get("name") or genre.get("title") or genre.get("russian")
                            if isinstance(name, str) and name.strip():
                                if name.strip().casefold() not in blocked:
                                    genre_set.add(name.strip())
            sorted_genres = sorted(genre_set, key=lambda s: s.lower())
            safe_cache_set(cache_key, sorted_genres, timeout=3600)
            return Response({'genres': sorted_genres})
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения жанров: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CatalogTypesAPI(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        try:
            revision = safe_cache_get('catalog:revision', 0)
            cache_key = f'catalog:facets:types:v1:{revision}'
            cached = safe_cache_get(cache_key)
            if cached is not None:
                return Response({'types': cached})
            blocked = hidden_values('kind')
            distinct_kinds = visible_anime().exclude(kind__isnull=True).exclude(kind='').values_list('kind', flat=True).distinct().order_by('kind')
            sorted_kinds = sorted(kind for kind in distinct_kinds if kind.casefold() not in blocked)
            safe_cache_set(cache_key, sorted_kinds, timeout=3600)
            return Response({'types': sorted_kinds})
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения типов: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
