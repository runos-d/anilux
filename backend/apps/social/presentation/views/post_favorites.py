from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.social.application.conversations import check_shareable
from apps.social.application.post_access import readable_posts, resolve_post_id
from apps.social.infrastructure.models.social import Favorite, Post
from apps.social.presentation.serializers.social_serializers import FavoriteSerializer


def target(request):
    data = request.data if request.method != 'GET' else request.query_params
    kind, object_id = data.get('content_type'), data.get('object_id')
    if kind not in ('post', 'anime', 'playlist', 'reactorpost', 'user', 'group'):
        raise ValidationError({'content_type': 'Неподдерживаемый тип избранного'})
    content_type = ContentType.objects.filter(model=kind).first()
    if not content_type: raise NotFound('Объект не найден')
    if kind == 'post': object_id = resolve_post_id(object_id)
    try: obj = content_type.model_class().objects.filter(pk=str(int(object_id)).zfill(8) if kind == 'playlist' else int(object_id)).first()
    except (ValueError, TypeError): raise ValidationError({'object_id': 'Укажите идентификатор объекта'})
    if not obj: raise NotFound('Объект не найден')
    check_shareable(obj, request.user)
    return content_type, obj.pk


class FavoriteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        base = Favorite.objects.filter(user=self.request.user).select_related('content_type').order_by('-created_at', '-pk')
        if self.request.method == 'DELETE': return base
        return base.filter(~Q(content_type__model='post') | Q(object_id__in=readable_posts(Post.objects.all(), self.request.user).values('pk')))

    @action(detail=False, methods=['get'])
    def check(self, request):
        content_type, object_id = target(request)
        return Response({'is_favorited': Favorite.objects.filter(user=request.user, content_type=content_type, object_id=object_id).exists(),
                         'content_type': content_type.model, 'object_id': str(object_id)})

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from apps.users.infrastructure.models.users import User
        User.objects.select_for_update().get(pk=request.user.pk)
        content_type, object_id = target(request)
        favorite, created = Favorite.objects.get_or_create(user=request.user, content_type=content_type, object_id=object_id)
        return Response({'success': True, 'is_favorited': True, 'id': str(favorite.pk)}, status=201 if created else 200)

    @action(detail=False, methods=['post', 'delete'])
    @transaction.atomic
    def toggle(self, request):
        from apps.users.infrastructure.models.users import User
        User.objects.select_for_update().get(pk=request.user.pk)
        content_type, object_id = target(request)
        query = Favorite.objects.filter(user=request.user, content_type=content_type, object_id=object_id)
        desired = request.data.get('active', False if request.method == 'DELETE' else not query.exists())
        if type(desired) is not bool: raise ValidationError({'active': 'Ожидается true или false'})
        if desired: Favorite.objects.get_or_create(user=request.user, content_type=content_type, object_id=object_id)
        else: query.delete()
        return Response({'success': True, 'is_favorited': desired})

    def perform_update(self, serializer):
        content_type = serializer.validated_data.get('content_type', serializer.instance.content_type)
        object_id = serializer.validated_data.get('object_id', serializer.instance.object_id)
        if content_type != serializer.instance.content_type or object_id != serializer.instance.object_id:
            raise ValidationError('Нельзя менять объект существующей записи избранного')
        serializer.save()
