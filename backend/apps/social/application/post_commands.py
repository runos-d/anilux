import hashlib
import json
import uuid
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError as ModelValidationError
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from apps.social.application.post_access import readable_posts, group_access
from apps.social.application.post_media import MAX_BYTES, link_uploads, stage_file
from apps.social.infrastructure.models.post_lifecycle import PostCommand, PostEvent, PostUpload
from apps.social.infrastructure.models.social import Group, Post, PostLike, PostDislike, Follow


class Conflict(APIException):
    status_code = 409
    default_detail = 'Пост уже изменён. Обновите данные и повторите действие.'


@transaction.atomic
def record_event(post, kind, **payload):
    if kind == 'post_updated' and hasattr(post, '_previous_visibility'):
        payload['access_before'] = {'visibility': post._previous_visibility, 'group_id': post._previous_group_id}
    if kind in ('new_post', 'post_updated', 'post_deleted'):
        from apps.social.application.post_counts import refresh_related
        refresh_related(post)
    if post.original_post_id: payload['original_post_id'] = str(post.original_post_id)
    event = PostEvent.objects.create(post=post, kind=kind, payload={
        'post_id': str(post.pk), 'version': post.version, **payload})
    def dispatch():
        try:
            deliver_post_event.delay(str(event.pk))
        except Exception:
            pass
    transaction.on_commit(dispatch, robust=True)
    return event


def payload_fingerprint(request):
    values = {}
    for key in sorted(request.data):
        if key in ('client_post_id', 'client_edit_id', 'client_action_id', 'version') or key in request.FILES:
            continue
        values[key] = request.data.getlist(key) if hasattr(request.data, 'getlist') else request.data[key]
    files = []
    for key in sorted(request.FILES):
        for file in request.FILES.getlist(key):
            digest = hashlib.sha256()
            for chunk in file.chunks():
                digest.update(chunk)
            file.seek(0)
            files.append((key, file.name, file.size, digest.hexdigest()))
    return hashlib.sha256(json.dumps({'values': values, 'files': files}, sort_keys=True, default=str).encode()).hexdigest()


def list_value(payload, field):
    value = payload.getlist(field + '[]') or payload.getlist(field) if hasattr(payload, 'getlist') else payload.get(field, [])
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str) and value[0].lstrip().startswith('['):
        value = value[0]
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            value = [value]
    if not isinstance(value, list):
        raise ValidationError({field: 'Ожидается список идентификаторов'})
    if any(not isinstance(item, (str, int)) or isinstance(item, bool) for item in value):
        raise ValidationError({field: 'Некорректный идентификатор'})
    return value


def prepare_uploads(request, retained=()):
    uploads = []
    ids = list_value(request.data, 'media_ids')
    if len(ids) != len(set(ids)):
        raise ValidationError({'media_ids': 'Вложения не должны повторяться'})
    try:
        uploads = list(PostUpload.objects.select_for_update().filter(pk__in=ids, owner=request.user, state='uploaded',
                                                                    expires_at__gt=timezone.now(), postmedia__isnull=True))
    except (ValueError, ModelValidationError) as error:
        raise ValidationError({'media_ids': 'Некорректное вложение'}) from error
    if len(uploads) != len(ids):
        raise ValidationError({'media_ids': 'Вложение недоступно, уже использовано или загрузка не завершена'})
    by_id = {str(upload.pk): upload for upload in uploads}
    uploads = [by_id[str(pk)] for pk in ids]
    files = [file for key in request.FILES for file in request.FILES.getlist(key)]
    retained_bytes = sum(item.file_size or (item.file.size if item.file else 0) for item in retained)
    if retained_bytes + sum(item.expected_size for item in uploads) + sum(file.size for file in files) > MAX_BYTES:
        raise ValidationError({'files': 'Общий объём вложений поста -максимум 250 МБ'})
    from apps.social.application.post_media import validate_declaration
    for file in files:
        validate_declaration(file.name, file.size)
    for file in files:
        uploads.append(stage_file(request.user, file))
    return uploads


def validate_shared(validated, user):
    from apps.social.application.conversations import check_shareable
    for field in ('anime', 'playlist', 'reactor_post', 'original_post'):
        value = validated.get(field)
        if value:
            check_shareable(value, user)

    from apps.anime.infrastructure.models.anime import Anime
    from apps.playlists.infrastructure.models.playlists import Playlist
    from apps.reactor.infrastructure.models.reactor import ReactorPost
    for field, model in (('anime_ids', Anime), ('playlist_ids', Playlist), ('reactor_ids', ReactorPost)):
        if field not in validated:
            continue
        ids = set(validated[field])
        values = list(model.objects.filter(pk__in=ids))
        if len(values) != len(ids):
            raise ValidationError({field: 'Некоторые вложения не найдены'})
        for value in values:
            check_shareable(value, user)
    if 'excerpt_ids' in validated:
        from apps.anime.models import Excerpt
        ids = set(validated['excerpt_ids'])
        if Excerpt.objects.filter(pk__in=ids, author=user, anime__is_available=True).count() != len(ids):
            raise ValidationError({'excerpt_ids': 'Отрывок недоступен или принадлежит другому автору'})
    group = validated.get('group')
    if group:
        from apps.social.infrastructure.models.social import GroupMembership, Group
        if group.creator_id != user.pk and not GroupMembership.objects.filter(group=group, user=user).exists():
            raise PermissionDenied('Для публикации вступите в группу')


def ratings_value(payload):
    raw = payload.getlist('anime_ratings[]') or payload.getlist('anime_ratings') if hasattr(payload, 'getlist') else payload.get('anime_ratings', [])
    if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], str) and raw[0].lstrip().startswith('['): raw = raw[0]
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except ValueError: raw = [raw]
    if not isinstance(raw, list): raise ValidationError({'anime_ratings': 'Ожидается список оценок'})
    return [None if item in ('', None) else item for item in raw]


def command_data(request):
    data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
    for field in ('anime_ids', 'playlist_ids', 'reactor_ids', 'anime_ratings', 'excerpt_ids'):
        if field in request.data or field + '[]' in request.data:
            data[field] = list_value(request.data, field) if field != 'anime_ratings' else ratings_value(request.data)
    return data


@transaction.atomic
def create_post(request, serializer_class):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().only('id').get(pk=request.user.pk)
    key = str(request.data.get('client_post_id') or uuid.uuid4())
    if len(key) > 36:
        raise ValidationError({'client_post_id': 'Слишком длинный ключ отправки'})
    fingerprint = payload_fingerprint(request)
    previous = PostCommand.objects.filter(owner=request.user, kind='create', key=key).select_related('post').first()
    if previous:
        if previous.fingerprint != fingerprint:
            raise Conflict('С этим ключом уже отправлен другой пост')
        if not previous.post or previous.post.is_deleted:
            raise NotFound('Пост удалён')
        return previous.post, False
    legacy = Post.objects.filter(author=request.user, client_post_id=key).first()
    if legacy:
        if legacy.is_deleted: raise NotFound('Пост удалён')
        PostCommand.objects.create(owner=request.user, kind='create', key=key, fingerprint=fingerprint, post=legacy)
        return legacy, False
    data = command_data(request)
    for name in list(data):
        if name.startswith('media_') or name == 'media':
            del data[name]
    serializer = serializer_class(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    validate_shared(serializer.validated_data, request.user)
    uploads = prepare_uploads(request)
    serializer.validated_data.pop('image_file', None)
    serializer.validated_data.pop('video_file', None)
    requested_status = request.data.get('status', 'published')
    if requested_status not in ('draft', 'published'):
        raise ValidationError({'status': 'Допустимы draft и published'})
    post = serializer.save(author=request.user, status='draft', client_post_id=key[:36])
    if uploads:
        link_uploads(post, uploads)
        post.post_type = 'video' if any(u.metadata['media_type'] == 'video' for u in uploads) else 'image'
    if not uploads:
        post.post_type = 'repost' if post.original_post_id else 'video' if post.video_url or post.reactor_post_id else 'playlist' if post.playlist_id else 'anime' if post.anime_id else 'image' if post.image_url else 'text'
    post.status = ('processing' if uploads else 'published') if requested_status == 'published' else 'draft'
    post.published_at = timezone.now() if post.status == 'published' else None
    post.save()
    PostCommand.objects.create(owner=request.user, kind='create', key=key, fingerprint=fingerprint, post=post)
    if post.status == 'published':
        record_event(post, 'new_post')
    return post, True


@transaction.atomic
def edit_post(request, post_id, serializer_class, partial=True):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().only('id').get(pk=request.user.pk)
    post = Post.objects.select_for_update().filter(group_access(request.user)).filter(pk=post_id, is_deleted=False).first()
    if not post:
        raise NotFound('Пост не найден')
    key = request.data.get('client_edit_id')
    if key and len(str(key)) > 128: raise ValidationError({'client_edit_id': 'Слишком длинный ключ отправки'})
    fingerprint = payload_fingerprint(request) if key else None
    previous = PostCommand.objects.filter(owner=request.user, kind='edit', key=key).first() if key else None
    if previous:
        if previous.post_id != post.pk or previous.fingerprint != fingerprint:
            raise Conflict('Ключ редактирования уже использован для другого изменения')
        return post
    if not post.can_edit(request.user):
        raise PermissionDenied('Редактирование доступно автору в течение пяти минут')
    if post.pending_edit:
        raise Conflict('Предыдущие вложения ещё обрабатываются')
    if 'version' in request.data:
        try:
            matches = int(request.data['version']) == post.version
        except (ValueError, TypeError):
            raise ValidationError({'version': 'Укажите версию поста'})
        if not matches:
            raise Conflict()
    from apps.social.application.post_legacy_media import register_legacy_media
    legacy = register_legacy_media(post)
    retained = list(post.media_files.filter(is_active=True))
    if 'retain_media_ids' in request.data or 'retain_media_ids[]' in request.data:
        keep = {str(legacy.get(str(pk), pk)) for pk in list_value(request.data, 'retain_media_ids')}
        if keep - {str(item.pk) for item in retained}:
            raise ValidationError({'retain_media_ids': 'Вложение не принадлежит посту'})
        retained = [item for item in retained if str(item.pk) in keep]
    serializer = serializer_class(post, data=command_data(request), partial=partial, context={'request': request})
    serializer.is_valid(raise_exception=True)
    validate_shared(serializer.validated_data, request.user)
    fields = serializer.validated_data
    if 'original_post' in request.data and str(request.data.get('original_post') or '') != str(post.original_post_id or ''):
        raise ValidationError({'original_post': 'Исходный пост репоста нельзя менять'})
    from apps.social.application.post_counts import remember_related
    remember_related(post)
    for kind in ('image', 'video'):
        if 'legacy:' + kind in legacy: fields[kind + '_file'] = None
    has_content = any(fields.get(name, getattr(post, name, None)) for name in ('text', 'title', 'image_url', 'video_url', 'image_file', 'video_file', 'original_post'))
    for ids, relation in (('anime_ids', 'anime'), ('playlist_ids', 'playlist'), ('reactor_ids', 'reactor_post')):
        has_content = has_content or bool(fields[ids] if ids in fields else fields.get(relation, getattr(post, relation)))
    has_content = has_content or bool(fields.get('excerpt_ids'))
    replaced_kinds = [kind for field, kind in (('anime_ids', 'anime'), ('playlist_ids', 'playlist'), ('reactor_ids', 'shorts'), ('excerpt_ids', 'excerpt')) if field in fields]
    has_content = has_content or post.attachments.exclude(content_type__in=replaced_kinds).exists()
    if not has_content and not retained and not request.FILES and not list_value(request.data, 'media_ids'):
        raise ValidationError('Пост должен содержать текст или вложение')
    uploads = prepare_uploads(request, retained)
    post.version += 1
    if uploads:
        fields = {field: value.pk if hasattr(value, 'pk') else value
                  for field, value in serializer.validated_data.items()}
        media = link_uploads(post, uploads, active=False)
        post.pending_edit = {'payload': fields, 'retain_media_ids': [item.pk for item in retained],
                             'new_media_ids': [item.pk for item in media]}
        post.save(update_fields=['version', 'pending_edit'])
    else:
        serializer.save(version=post.version, edited_at=timezone.now())
        from apps.social.application.post_file_gc import schedule_cleanup
        removed = list(post.media_files.filter(is_active=True).exclude(pk__in=[item.pk for item in retained]))
        for item in removed: schedule_cleanup(item)
        post.media_files.filter(pk__in=[item.pk for item in removed]).update(is_active=False)
        record_event(post, 'post_updated')
    if key:
        PostCommand.objects.create(owner=request.user, kind='edit', key=key, fingerprint=fingerprint, post=post)

    return post


@transaction.atomic
def delete_post(post_id, user, *, moderation=False):
    from apps.users.infrastructure.models.users import User
    author_id = Post.objects.filter(pk=post_id).values_list('author_id', flat=True).first()
    if author_id: User.objects.select_for_update().only('id').get(pk=author_id)
    post = Post.objects.select_for_update().filter(pk=post_id).first()
    if not post:
        raise NotFound('Пост не найден')
    from apps.social.application.post_access import is_post_moderator
    if not post.can_delete(user) and not (moderation and is_post_moderator(user)):
        raise PermissionDenied('Вы можете удалять только свои посты')
    if not post.is_deleted:
        from apps.social.application.post_legacy_media import register_legacy_media
        register_legacy_media(post)
        post.is_deleted, post.status, post.deleted_at = True, 'deleted', timezone.now()
        post.pending_edit = {}
        post.version += 1
        post.save()
        from apps.social.application.post_file_gc import schedule_cleanup
        for media in post.media_files.all(): schedule_cleanup(media)
        record_event(post, 'post_deleted')
    return post


@transaction.atomic
def publish_post(post_id, user):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().only('id').get(pk=user.pk)
    post = Post.objects.select_for_update().filter(group_access(user)).filter(pk=post_id, author=user, is_deleted=False).first()
    if not post: raise NotFound('Черновик не найден')
    if post.status == 'draft':
        media = list(post.media_files.filter(is_active=True))
        post.status = 'published' if all(item.processing_state == 'ready' for item in media) else 'processing'
        post.published_at = timezone.now() if post.status == 'published' else None
        post.version += 1
        post.save(update_fields=['status', 'published_at', 'version'])
        if post.status == 'published': record_event(post, 'new_post')
    return post


@transaction.atomic
def cancel_pending_edit(post_id, user):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().only('id').get(pk=user.pk)
    post = Post.objects.select_for_update().filter(group_access(user)).filter(pk=post_id, author=user, is_deleted=False).first()
    if not post: raise NotFound('Пост не найден')
    if post.pending_edit:
        from apps.social.application.post_file_gc import schedule_cleanup
        for media in post.media_files.filter(pk__in=post.pending_edit.get('new_media_ids', [])): schedule_cleanup(media)
        post.pending_edit = {}
        post.version += 1
        post.save(update_fields=['version', 'pending_edit'])
        record_event(post, 'post_updated')
    return post


@transaction.atomic
def react(post_id, user, reaction, key=None, desired=None):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().only('id').get(pk=user.pk)
    post = readable_posts(Post.objects.select_for_update(), user).filter(pk=post_id).first()
    if not post:
        raise NotFound('Пост недоступен')
    if post.author_id == user.pk:
        raise ValidationError('Нельзя оценивать свой пост')
    if not post.can_like(user): raise ValidationError('Реакции к этому посту недоступны')
    if desired is not None and not isinstance(desired, bool): raise ValidationError({'active': 'Ожидается true или false'})
    if key and len(str(key)) > 128: raise ValidationError({'client_action_id': 'Слишком длинный ключ отправки'})
    fingerprint = f'{post.pk}:{reaction}:{desired}'
    previous_command = PostCommand.objects.filter(owner=user, kind='reaction', key=key).first() if key else None
    if previous_command:
        if previous_command.fingerprint != fingerprint: raise Conflict('Ключ действия уже использован')
        return previous_command.response
    selected, other = (PostLike, PostDislike) if reaction == 'like' else (PostDislike, PostLike)
    previous = selected.objects.filter(post=post, user=user)
    active = not previous.exists() if desired is None else desired
    previous.delete()
    if active: other.objects.filter(post=post, user=user).delete()
    if active:
        selected.objects.create(post=post, user=user)
    post.likes_count = PostLike.objects.filter(post=post).count()
    post.dislikes_count = PostDislike.objects.filter(post=post).count()
    post.save(update_fields=['likes_count', 'dislikes_count'])
    record_event(post, 'post_reaction', actor_id=user.pk, reaction=reaction, active=active)
    response = {'liked': PostLike.objects.filter(post=post, user=user).exists(),
            'disliked': PostDislike.objects.filter(post=post, user=user).exists(),
            'likes_count': post.likes_count, 'dislikes_count': post.dislikes_count}
    if key:
        PostCommand.objects.create(owner=user, kind='reaction', key=key, fingerprint=fingerprint, post=post, response=response)
    return response



@shared_task(name='social.deliver_post_event')
def deliver_post_event(event_id):
    from core.redis_client import redis_pubsub_manager
    with transaction.atomic():
        event = PostEvent.objects.select_for_update().filter(pk=event_id).first()
        if not event or event.delivered_at:
            return
        post = event.post
        from apps.users.infrastructure.models.users import User
        from core.online_status import online_status
        from apps.users.infrastructure.models.users import User
        from apps.social.infrastructure.models.social import GroupMembership
        from django.db.models import Q
        targets = {post.author_id, *[row['user_id'] for row in online_status.get_online_users() if 'user_id' in row]}
        if event.payload.get('actor_id'): targets.add(event.payload['actor_id'])
        users = User.objects.filter(pk__in=targets, is_active=True)
        visibility = Q(pk=post.author_id)
        if post.visibility == 'public': visibility |= Q(pk__in=targets)
        elif post.visibility == 'followers': visibility |= Q(pk__in=Follow.objects.filter(following_id=post.author_id).values('follower_id'))
        elif post.visibility == 'friends':
            visibility |= Q(pk__in=Follow.objects.filter(following_id=post.author_id).values('follower_id')) & Q(pk__in=Follow.objects.filter(follower_id=post.author_id).values('following_id'))
        users = users.filter(visibility)
        if post.group_id and post.group.is_private:
            users = users.filter(Q(pk=post.group.creator_id) | Q(pk__in=GroupMembership.objects.filter(group_id=post.group_id).values('user_id')))
        if post.is_deleted and event.kind != 'post_deleted': users = users.none()
        targets = set(users.values_list('pk', flat=True))
        before = event.payload.get('access_before')
        if before and (before['visibility'] != post.visibility or before['group_id'] != post.group_id):
            old_users = User.objects.filter(pk__in={post.author_id, *[row['user_id'] for row in online_status.get_online_users() if 'user_id' in row]}, is_active=True)
            previous = Q(pk=post.author_id)
            if before['visibility'] == 'public': previous |= Q(is_active=True)
            elif before['visibility'] == 'followers': previous |= Q(pk__in=Follow.objects.filter(following_id=post.author_id).values('follower_id'))
            elif before['visibility'] == 'friends':
                previous |= Q(pk__in=Follow.objects.filter(following_id=post.author_id).values('follower_id')) & Q(pk__in=Follow.objects.filter(follower_id=post.author_id).values('following_id'))
            old_users = old_users.filter(previous)
            group = Group.objects.filter(pk=before['group_id']).first() if before['group_id'] else None
            if group and group.is_private:
                old_users = old_users.filter(Q(pk=group.creator_id) | Q(pk__in=GroupMembership.objects.filter(group=group).values('user_id')))
            targets.update(old_users.values_list('pk', flat=True))
        targets = sorted(targets)
        notifications = []
        actor_id = event.payload.get('actor_id')
        if actor_id and not post.is_deleted:
            actor = User.objects.filter(pk=actor_id).first()
            kind = None
            if event.kind == 'post_reaction' and event.payload.get('active') and event.payload.get('reaction') == 'like': kind = 'like'
            if event.kind == 'post_comment': kind = 'comment'
            if event.kind == 'post_reposted' and not event.payload.get('already_reposted'): kind = 'repost'
            if kind == 'like' and not PostLike.objects.filter(post=post, user_id=actor_id).exists(): kind = None
            if kind == 'repost' and not Post.objects.filter(original_post=post, author_id=actor_id, status='published', is_deleted=False).exists(): kind = None
            if kind == 'comment':
                from apps.social.infrastructure.models.social import PostComment
                if not PostComment.objects.filter(pk=event.payload.get('comment_id'), post=post, is_deleted=False).exists(): kind = None
            if kind and actor:
                recipients = {post.author_id}
                if kind == 'comment' and event.payload.get('parent_author_id'): recipients.add(event.payload['parent_author_id'])
                from apps.notifications.application.services import NotificationService
                for recipient in User.objects.filter(pk__in=recipients).exclude(pk=actor_id):
                    if not readable_posts(Post.objects.filter(pk=post.pk), recipient).exists(): continue
                    notification = NotificationService.create_notification(user=recipient, notification_type=kind,
                        title={'comment': 'Новый комментарий', 'like': 'Новая отметка «Нравится»', 'repost': 'Новый репост'}[kind],
                        content=f'{actor.username} ' + {'comment': 'прокомментировал ваш пост', 'like': 'оценил ваш пост', 'repost': 'поделился вашим постом'}[kind],
                        link=f'/post/{post.pk}', content_object=post, send_ws=False,
                        dedupe_key=f'post-event:{event.pk}:{recipient.pk}')
                    if notification: notifications.append(notification)
        client = redis_pubsub_manager._get_redis_client()
        if client is None:
            raise ConnectionError('Redis недоступен')
        message = json.dumps({'type': event.kind, 'event_type': event.kind,
            'event_id': str(event.pk), 'target_users': targets, 'data': event.payload,
            'timestamp': timezone.now().isoformat()})
        pipeline = client.pipeline()
        pipeline.publish('realtime_updates', message)
        pipeline.lpush('realtime_queue', message)
        pipeline.ltrim('realtime_queue', 0, 99)
        for notification in notifications:
            packet = json.dumps({'type': 'notification', 'event_type': 'notification',
                'event_id': f'{event.pk}:notification:{notification.user_id}', 'target_users': [notification.user_id],
                'data': {'notification': {'id': notification.pk, 'type': notification.type, 'title': notification.title,
                    'content': notification.content, 'link': notification.link, 'icon': notification.icon,
                    'is_read': False, 'created_at': notification.created_at.isoformat()}}})
            pipeline.publish('realtime_updates', packet)
            pipeline.lpush('realtime_queue', packet)

        pipeline.execute()
        event.delivered_at = timezone.now()
        event.attempts += 1
        event.error = ''
        event.save(update_fields=['delivered_at', 'attempts', 'error'])


@shared_task(name='social.retry_post_events')
def retry_post_events():
    for pk in PostEvent.objects.filter(delivered_at__isnull=True).values_list('pk', flat=True)[:100]:
        try:
            deliver_post_event(str(pk))
        except Exception as error:
            PostEvent.objects.filter(pk=pk).update(attempts=F('attempts') + 1, error=str(error)[:500])
