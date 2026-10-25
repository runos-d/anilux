from types import SimpleNamespace
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.social.application.post_access import resolve_post_id
from apps.social.application.post_commands import edit_post
from apps.social.infrastructure.models.social import Post, PostAttachment
from apps.social.presentation.serializers.social_serializers import PostUpdateSerializer


@transaction.atomic
def change_attachment(request, instance=None, delete=False):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().get(pk=request.user.pk)
    post_id = resolve_post_id(request.data.get('post', instance.post_id if instance else None))
    if instance and post_id != instance.post_id:
        raise ValidationError({'post': 'Перемещение вложения в другой пост не поддерживается'})
    post = Post.objects.select_for_update().get(pk=post_id)
    if not post.can_edit(request.user): raise PermissionDenied('Редактирование доступно автору в течение пяти минут')
    kind = request.data.get('content_type', instance.content_type if instance else None)
    if kind not in ('anime', 'playlist', 'shorts', 'excerpt'): raise ValidationError({'content_type': 'Неподдерживаемый тип вложения'})
    try: object_id = int(request.data.get('object_id', instance.object_id if instance else None))
    except (ValueError, TypeError): raise ValidationError({'object_id': 'Укажите идентификатор вложения'})
    attachments = list(post.attachments.all())
    values = {name: [row.object_id for row in attachments if row.content_type == name and (not instance or row.pk != instance.pk)]
              for name in ('anime', 'playlist', 'shorts', 'excerpt')}
    if not delete and object_id not in values[kind]: values[kind].append(object_id)
    payload = {'anime_ids': values['anime'], 'playlist_ids': [str(value).zfill(8) for value in values['playlist']], 'reactor_ids': values['shorts'], 'excerpt_ids': values['excerpt']}
    for field in ('version', 'client_edit_id'):
        if field in request.data: payload[field] = request.data[field]
    command = SimpleNamespace(data=payload, FILES=request.FILES, user=request.user)
    edit_post(command, post.pk, PostUpdateSerializer, partial=True)
    return PostAttachment.objects.filter(post=post, content_type=kind, object_id=object_id).first() if not delete else None
