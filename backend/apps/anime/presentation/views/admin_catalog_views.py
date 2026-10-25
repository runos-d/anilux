from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.anime.models import Anime, Franchise
from apps.anime.infrastructure.models.anime import CatalogHideRule, CatalogVisibility
from apps.anime.application.catalog_visibility import hidden_anime, rule_query, invalidate


class PrivateAdminResponse:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response


def page_result(request, qs, render):
    try:
        page = max(1, int(request.query_params.get('page', 1)))
        size = max(1, min(100, int(request.query_params.get('page_size', 20))))
    except (ValueError, TypeError):
        raise serializers.ValidationError('Некорректная страница.')
    count = qs.count()
    page = min(page, max(1, (count + size - 1) // size))
    return {'count': count, 'page': page, 'page_size': size,
            'results': [render(row) for row in qs[(page-1)*size:page*size]]}


def anime_data(row):
    return {**{key: getattr(row, key) for key in ('id', 'title_ru', 'title_en', 'slug', 'year',
            'kind', 'status', 'episodes', 'score', 'franchise_order')},
            'poster_url': row.poster_image_url,
            'franchise': {'id': row.franchise_id, 'name': row.franchise.name} if row.franchise_id else None}


def franchise_data(row, detail=False):
    data = {key: getattr(row, key) for key in ('id', 'name', 'slug', 'description', 'score',
                                              'year_start', 'year_end', 'genres')}
    entries = row.entries.order_by('franchise_order', 'pk')
    first = entries.first()
    data.update(parts_count=entries.count(), cover=row.poster_image_url or (first.poster_image_url if first else ''))
    if detail:
        data['entries'] = [anime_data(part) for part in entries.select_related('franchise')]
    return data


class FranchiseWrite(serializers.ModelSerializer):
    class Meta:
        model = Franchise
        fields = ['name', 'description']


class AnimeId(serializers.Serializer):
    anime_id = serializers.IntegerField(min_value=1)


class OrderWrite(serializers.Serializer):
    anime_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)


class AdminFranchiseViewSet(PrivateAdminResponse, viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        qs = Franchise.objects.order_by('name', 'pk')
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return Response(page_result(request, qs, franchise_data))

    def create(self, request):
        serializer = FranchiseWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = serializer.save()
        row.slug = f'{row.slug[:230] or "franchise"}-{row.pk}'
        row.save(update_fields=['slug'])
        invalidate()
        return Response(franchise_data(row), status=201)

    @action(detail=False, methods=['post'])
    def rebuild(self, request):
        automatic = Anime.objects.filter(shikimori_id__isnull=False, franchise_manual=False)
        reset_count = automatic.count()
        refresh_before = timezone.now().isoformat()
        from apps.anime.application.franchise_sync import (
            ACTIVE_REBUILD_KEY,
            REBUILD_STATUS_TTL,
            rebuild_status_key,
            sync_franchises,
        )
        active_id = cache.get(ACTIVE_REBUILD_KEY)
        active_status = cache.get(rebuild_status_key(active_id)) if active_id else None
        if active_id and active_status and active_status.get('state') in ('queued', 'running'):
            return Response({
                'queued': True,
                'reused': True,
                'rebuild_id': active_id,
                'anime_scheduled': active_status.get('total', reset_count),
                'single_links_removed': 0,
            }, status=202)
        rebuild_id = uuid.uuid4().hex
        cache.set(rebuild_status_key(rebuild_id), {
            'state': 'queued',
            'total': reset_count,
            'processed': 0,
            'remaining': reset_count,
            'message': 'Пересборка поставлена в очередь',
        }, REBUILD_STATUS_TTL)
        try:
            task = sync_franchises.delay(
                limit=100,
                continue_until_done=True,
                refresh_provider=True,
                rebuild_id=rebuild_id,
                total=reset_count,
                refresh_before=refresh_before,
            )
        except Exception:
            cache.set(rebuild_status_key(rebuild_id), {
                'state': 'failed',
                'total': reset_count,
                'processed': 0,
                'remaining': reset_count,
                'message': 'Не удалось поставить пересборку в очередь',
            }, REBUILD_STATUS_TTL)
            return Response({'detail': 'Не удалось поставить пересборку в очередь.'}, status=503)
        return Response({
            'queued': True,
            'task_id': str(task.id),
            'rebuild_id': rebuild_id,
            'anime_scheduled': reset_count,
            'single_links_removed': 0,
        }, status=202)

    @action(detail=False, methods=['get'], url_path=r'rebuild-status/(?P<rebuild_id>[0-9a-f]{32})')
    def rebuild_status(self, request, rebuild_id=None):
        from apps.anime.application.franchise_sync import ACTIVE_REBUILD_KEY, rebuild_status_key
        status = cache.get(rebuild_status_key(rebuild_id))
        if status is None:
            return Response({'detail': 'Статус пересборки не найден.'}, status=404)
        active_id = cache.get(ACTIVE_REBUILD_KEY)
        if status.get('state') == 'queued' and active_id and active_id != rebuild_id:
            active_status = cache.get(rebuild_status_key(active_id))
            if active_status and active_status.get('state') in ('queued', 'running'):
                return Response({**active_status, 'rebuild_id': active_id})
        return Response({**status, 'rebuild_id': status.get('rebuild_id', rebuild_id)})

    def retrieve(self, request, pk=None):
        return Response(franchise_data(get_object_or_404(Franchise, pk=pk), True))

    def partial_update(self, request, pk=None):
        row = get_object_or_404(Franchise, pk=pk)
        serializer = FranchiseWrite(row, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        invalidate()
        return Response(franchise_data(row))

    @transaction.atomic
    def destroy(self, request, pk=None):
        row = get_object_or_404(Franchise.objects.select_for_update(), pk=pk)
        row.entries.update(franchise=None, franchise_order=0, franchise_manual=True)
        row.delete()
        transaction.on_commit(invalidate)
        return Response(status=204)

    @action(detail=True, methods=['post'], url_path='add-anime')
    @transaction.atomic
    def add_anime(self, request, pk=None):
        row = get_object_or_404(Franchise.objects.select_for_update(), pk=pk)
        serializer = AnimeId(data=request.data)
        serializer.is_valid(raise_exception=True)
        anime = get_object_or_404(Anime.objects.select_for_update(), pk=serializer.validated_data['anime_id'])
        old = anime.franchise
        if anime.franchise_id != row.pk:
            anime.franchise_order = max(row.entries.values_list('franchise_order', flat=True), default=-1) + 1
        anime.franchise, anime.franchise_manual = row, True
        anime.save(update_fields=['franchise', 'franchise_order', 'franchise_manual'])
        if old and old.pk != row.pk:
            old.update_aggregated_data()
        row.update_aggregated_data()
        transaction.on_commit(invalidate)
        return Response(franchise_data(row, True))

    @action(detail=True, methods=['post'], url_path='remove-anime')
    @transaction.atomic
    def remove_anime(self, request, pk=None):
        row = get_object_or_404(Franchise.objects.select_for_update(), pk=pk)
        serializer = AnimeId(data=request.data)
        serializer.is_valid(raise_exception=True)
        anime = get_object_or_404(Anime.objects.select_for_update(), pk=serializer.validated_data['anime_id'], franchise=row)
        anime.franchise, anime.franchise_order, anime.franchise_manual = None, 0, True
        anime.save(update_fields=['franchise', 'franchise_order', 'franchise_manual'])
        row.update_aggregated_data()
        transaction.on_commit(invalidate)
        return Response(franchise_data(row, True))

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def reorder(self, request, pk=None):
        row = get_object_or_404(Franchise.objects.select_for_update(), pk=pk)
        serializer = OrderWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['anime_ids']
        parts = list(row.entries.select_for_update())
        if len(ids) != len(set(ids)) or set(ids) != {part.pk for part in parts}:
            raise serializers.ValidationError({'anime_ids': 'Передайте каждую часть франшизы ровно один раз.'})
        positions = {pk: index for index, pk in enumerate(ids)}
        for part in parts:
            part.franchise_order, part.franchise_manual = positions[part.pk], True
        Anime.objects.bulk_update(parts, ['franchise_order', 'franchise_manual'])
        transaction.on_commit(invalidate)
        return Response(franchise_data(row, True))


class AdminAnimeSearch(PrivateAdminResponse, APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'results': []})
        rows = Anime.objects.select_related('franchise').filter(
            Q(title_ru__icontains=q) | Q(title_en__icontains=q)).order_by('title_ru', 'pk')[:50]
        hidden = set(hidden_anime().filter(pk__in=[row.pk for row in rows]).values_list('pk', flat=True))
        return Response({'results': [{**anime_data(row), 'is_available': row.is_available and row.pk not in hidden} for row in rows]})


class CatalogOptions(PrivateAdminResponse, APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        genres, studios, kinds = set(), set(), set()
        for row in Anime.objects.values('genres', 'studios', 'kind').iterator():
            genres.update(value for value in (row['genres'] or []) if isinstance(value, str))
            studios.update(value for value in (row['studios'] or []) if isinstance(value, str))
            if row['kind']:
                kinds.add(row['kind'])
        return Response({'genres': sorted(genres), 'studios': sorted(studios), 'kinds': sorted(kinds)})


class RuleWrite(serializers.ModelSerializer):
    class Meta:
        model = CatalogHideRule
        fields = ['rule_type', 'value', 'note']


def rule_data(row):
    matching = Anime.objects.filter(rule_query(row))
    return {'id': row.pk, 'rule_type': row.rule_type, 'rule_type_label': row.get_rule_type_display(),
            'value': row.value, 'note': row.note, 'created_at': row.created_at,
            'created_by': row.created_by.username if row.created_by else None,
            'matched_count': matching.count(), 'hidden_count': hidden_anime().filter(pk__in=matching).count()}


class CatalogRules(PrivateAdminResponse, viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        return Response({'results': [rule_data(row) for row in CatalogHideRule.objects.select_related('created_by')]})

    def create(self, request):
        serializer = RuleWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        before = hidden_anime().count()
        from django.db import IntegrityError
        try:
            with transaction.atomic():
                row = serializer.save(created_by=request.user)
                CatalogVisibility.objects.filter(anime__in=Anime.objects.filter(rule_query(row))).update(restored=False)
                transaction.on_commit(invalidate)
        except IntegrityError:
            return Response({'detail': 'Такое правило уже существует'}, status=409)
        return Response({**rule_data(row), 'hidden_now': hidden_anime().count()-before}, status=201)

    @transaction.atomic
    def apply(self, request, pk=None):
        row = get_object_or_404(CatalogHideRule, pk=pk)
        before = hidden_anime().count()
        CatalogVisibility.objects.filter(anime__in=Anime.objects.filter(rule_query(row))).update(restored=False)
        transaction.on_commit(invalidate)
        return Response({**rule_data(row), 'hidden_now': hidden_anime().count()-before})

    @transaction.atomic
    def apply_all(self, request):
        CatalogVisibility.objects.update(restored=False)
        transaction.on_commit(invalidate)
        return Response({'total_hidden': hidden_anime().count()})

    @transaction.atomic
    def destroy(self, request, pk=None):
        row = get_object_or_404(CatalogHideRule, pk=pk)
        before = hidden_anime().count()
        row.delete()
        transaction.on_commit(invalidate)
        return Response({'restored': before-hidden_anime().count()})


class CatalogHidden(PrivateAdminResponse, APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = hidden_anime().select_related('franchise').order_by('title_ru', 'pk')
        q = request.query_params.get('search', '').strip()
        if q:
            qs = qs.filter(Q(title_ru__icontains=q) | Q(title_en__icontains=q))
        return Response(page_result(request, qs, anime_data))

    def post(self, request, pk=None):
        if pk is None:
            serializer = AnimeId(data=request.data)
            serializer.is_valid(raise_exception=True)
            pk = serializer.validated_data['anime_id']
            restored = False
        else:
            restored = True
        anime = get_object_or_404(Anime.objects.select_related('franchise'), pk=pk)
        CatalogVisibility.objects.update_or_create(anime=anime, defaults={
            'manual_hidden': not restored, 'restored': restored})
        invalidate()
        return Response(anime_data(anime))
