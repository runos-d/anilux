import re
import unicodedata

from django.db.models import Q, Value
from django.db.models.functions import Lower, Replace
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.anime.infrastructure.models.anime import Anime


@api_view(['GET'])
@permission_classes([AllowAny])
def attachment_anime_search(request):
    query = unicodedata.normalize('NFKC', request.query_params.get('q', '')).strip().casefold().replace('ё', 'е')
    try:
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
    except (ValueError, TypeError):
        raise ValidationError('Некорректная страница поиска')
    if page < 1 or not 1 <= limit <= 100:
        raise ValidationError('Некорректная страница поиска')
    words = re.findall(r'\w+', query, flags=re.UNICODE)
    queryset = Anime.objects.all()
    annotations = {}
    for field in ['title_ru', 'title_en', 'title_jp', 'slug']:
        expression = Lower(field)
        for original, replacement in [('ё', 'е'), (' ', ''), ('-', ''), (':', ''), ('_', '')]:
            expression = Replace(expression, Value(original), Value(replacement))
        annotations[f'search_{field}'] = expression
    queryset = queryset.annotate(**annotations)
    if not words:
        queryset = queryset.none()
    for word in words:
        match = Q()
        for field in annotations:
            match |= Q(**{f'{field}__contains': word.replace('_', '')})
        queryset = queryset.filter(match)
    count = queryset.count()
    rows = queryset.order_by('-score', 'id')[(page - 1) * limit:page * limit]
    return Response({'count': count, 'page': page, 'has_more': page * limit < count, 'results': [{
        'id': anime.pk, 'slug': anime.slug, 'title_ru': anime.title_ru,
        'title_en': anime.title_en, 'title_jp': anime.title_jp, 'year': anime.year,
        'kind': anime.kind, 'episodes': anime.episodes, 'score': anime.score,
        'poster_url': anime.poster_image_url,
    } for anime in rows]})
