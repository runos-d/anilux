import math
import uuid
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from apps.anime.models import Anime, Excerpt
from apps.anime.application.excerpts import available, excerpt_data, material


class ExcerptInput(serializers.Serializer):
    anime_id = serializers.IntegerField(min_value=1)
    season = serializers.IntegerField(min_value=1)
    episode = serializers.IntegerField(min_value=1)
    translation_id = serializers.IntegerField(min_value=1)
    duration = serializers.FloatField(min_value=0.001, max_value=86400)
    start = serializers.FloatField(min_value=0)
    end = serializers.FloatField(min_value=0)
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, max_length=5000)
    shared = serializers.BooleanField(required=False)


def validated(data, instance=None):
    allowed = {'start', 'end', 'title', 'description', 'shared'} if instance else set(ExcerptInput().fields)
    if set(data) - allowed:
        raise ValidationError('Материал отрывка нельзя менять. Создайте новый отрывок.')
    serializer = ExcerptInput(data=data, partial=instance is not None)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    start = values.get('start', instance.start if instance else None)
    end = values.get('end', instance.end if instance else None)
    duration = instance.duration if instance else values['duration']
    if not all(math.isfinite(value) for value in (start, end, duration)) or not 0 <= start < end <= duration:
        raise ValidationError({'end': 'Нужно 0 ≤ начало < конец ≤ длительность видео'})
    return values


def response(data, status=200):
    result = Response(data, status=status)
    result['Cache-Control'] = 'private, no-store'
    result['Vary'] = 'Authorization, Cookie'
    return result


@api_view(['POST'])
@permission_classes([AllowAny])
def excerpt_checks(request):
    class Reference(serializers.Serializer):
        id = serializers.IntegerField(min_value=1)
        token = serializers.UUIDField(required=False, allow_null=True)
        owner = serializers.BooleanField(default=False)
        key = serializers.CharField(max_length=200)
    if not isinstance(request.data, dict) or not isinstance(request.data.get('items'), list) or len(request.data['items']) > 100:
        raise ValidationError('Передайте до 100 отрывков')
    values = Reference(data=request.data['items'], many=True)
    values.is_valid(raise_exception=True)
    rows = {row.pk: row for row in Excerpt.objects.filter(pk__in=[item['id'] for item in values.validated_data]).select_related('anime')}
    result = []
    for item in values.validated_data:
        row = rows.get(item['id'])
        owns = bool(row and item['owner'] and request.user.is_authenticated and row.author_id == request.user.pk)
        shared = bool(row and not item['owner'] and row.shared and item.get('token') == row.share_token)
        result.append({'key': item['key'], 'excerpt': excerpt_data(row, owner=owns) if owns or shared else None})
    return response({'results': result})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def excerpts(request):
    if request.method == 'GET':
        rows = Excerpt.objects.filter(author=request.user).select_related('anime')
        query = request.query_params.get('q', '').strip()[:200]
        if query:
            rows = rows.filter(Q(title__icontains=query) | Q(description__icontains=query) |
                               Q(anime__title_ru__icontains=query) | Q(anime__title_en__icontains=query))
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            raise ValidationError({'page': 'Некорректная страница'})
        count = rows.count()
        results = []
        for row in rows[(page - 1) * 30:page * 30]:
            data = excerpt_data(row, owner=True)
            results.append(data or {'id': row.pk, 'unavailable': True})
        return response({'results': results, 'count': count, 'next': page + 1 if page * 30 < count else None})
    values = validated(request.data)
    anime = Anime.objects.filter(pk=values.pop('anime_id'), is_available=True).first()
    if not anime:
        raise NotFound('Аниме недоступно')
    link, title = material(anime, values['season'], values['episode'], values['translation_id'])
    row = Excerpt.objects.create(author=request.user, anime=anime, player_link=link, translation_title=title, **values)
    return response(excerpt_data(row, owner=True), 201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def excerpt_detail(request, pk):
    row = Excerpt.objects.select_for_update().select_related('anime').filter(pk=pk, author=request.user).first()
    if row is None:
        raise NotFound('Отрывок недоступен')
    if request.method == 'DELETE':
        row.delete()
        return response(None, 204)
    if not available(row):
        raise NotFound('Отрывок недоступен')
    if request.method == 'PATCH':
        values = validated(request.data, row)
        if values.get('shared') is False and row.shared:
            row.share_token = uuid.uuid4()
        for field, value in values.items():
            setattr(row, field, value)
        row.save()
    return response(excerpt_data(row, owner=True))


@api_view(['GET'])
@permission_classes([AllowAny])
def excerpt_shared(request, token):
    row = Excerpt.objects.select_related('anime').filter(share_token=token, shared=True).first()
    data = excerpt_data(row)
    if data is None:
        raise NotFound('Отрывок недоступен')
    return response(data)
