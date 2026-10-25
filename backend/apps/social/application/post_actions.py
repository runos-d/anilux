from types import SimpleNamespace
import uuid
import hashlib
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from apps.social.application.post_access import readable_posts, resolve_post_id
from apps.social.application.post_commands import Conflict, create_post, record_event, payload_fingerprint
from apps.social.infrastructure.models.post_lifecycle import PostCommand
from apps.social.infrastructure.models.social import Post, Repost, Bookmark, FeedView, Group, GroupMembership, GroupChat, PrivateChat
from apps.users.infrastructure.models.users import User


def lock_post(request, post_id):
    User.objects.select_for_update().only('id').get(pk=request.user.pk)
    post = readable_posts(Post.objects.select_for_update(), request.user).filter(pk=resolve_post_id(post_id)).first()
    if not post: raise NotFound('Пост недоступен')
    return post


@transaction.atomic
def bookmark(request, post_id, desired=None):
    post = lock_post(request, post_id)
    if desired is None: desired = request.data.get('active')
    existing = Bookmark.objects.filter(user=request.user, post=post)
    key = request.data.get('client_action_id')
    if key and len(str(key)) > 128: raise ValidationError({'client_action_id': 'Слишком длинный ключ отправки'})
    fingerprint = f'{post.pk}:{desired}'
    command = PostCommand.objects.filter(owner=request.user, kind='bookmark', key=key).first() if key else None
    if command:
        if command.fingerprint != fingerprint: raise Conflict()
        return command.response
    if desired is not None and not isinstance(desired, bool): raise ValidationError({'active': 'Ожидается true или false'})
    if desired is None: desired = not existing.exists()
    if desired: Bookmark.objects.get_or_create(user=request.user, post=post)
    else: existing.delete()
    result = {'success': True, 'bookmarked': desired}
    if key: PostCommand.objects.create(owner=request.user, kind='bookmark', key=key, fingerprint=fingerprint, post=post, response=result)
    record_event(post, 'post_bookmarked', actor_id=request.user.pk)
    return result


@transaction.atomic
def repost(request, post_id, remove=False):
    original = lock_post(request, post_id)
    if remove or request.data.get('action') == 'unrepost':
        existing = list(Post.objects.filter(author=request.user, original_post=original, post_type='repost', is_deleted=False))
        from apps.social.application.post_commands import delete_post
        for post in existing: delete_post(post.pk, request.user)
        deleted = Repost.objects.filter(original_post=original, user=request.user).delete()[0]
        original.reposts_count = Post.objects.filter(original_post=original, status='published', is_deleted=False).count()
        original.save(update_fields=['reposts_count'])
        record_event(original, 'post_repost_removed', actor_id=request.user.pk)
        return {'success': True, 'removed': bool(deleted or existing)}
    if original.post_type == 'system' or original.visibility == 'private': raise PermissionDenied('Этот пост нельзя репостить')
    key = str(request.data.get('client_action_id') or uuid.uuid4())
    if len(key) > 128: raise ValidationError({'client_action_id': 'Слишком длинный ключ отправки'})
    fingerprint = hashlib.sha256((payload_fingerprint(request) + ':' + str(original.pk)).encode()).hexdigest()
    command = PostCommand.objects.filter(owner=request.user, kind='repost', key=key).first()
    if command:
        if command.fingerprint != fingerprint: raise Conflict()
        return command.response
    destination = request.data.get('destination', 'feed')
    if destination == 'chat' or request.data.get('action') == 'forward':
        chat_id = request.data.get('chat_id') or request.data.get('target_id')
        if not chat_id: raise ValidationError({'chat_id': 'Выберите чат'})
        model = GroupChat if request.data.get('chat_type') == 'group' else PrivateChat
        chat = model.objects.filter(Q(pk=chat_id) | Q(public_id=chat_id)).first()
        if not chat: raise NotFound('Чат не найден')
        from apps.social.application.conversations import send_message
        message, created = send_message(chat, request.user, {'text': request.data.get('message', ''),
            'shared_post': original, 'client_message_id': str(uuid.uuid5(uuid.NAMESPACE_URL, f'post-forward:{request.user.pk}:{key}'))})
        if created:
            original.shares_count += 1
            original.save(update_fields=['shares_count'])
        result = {'success': True, 'message_id': str(message.pk), 'chat_id': str(chat.public_id), 'action': 'forward'}
        output = None
    else:
        if destination not in ('feed', 'group'): raise ValidationError({'destination': 'Неизвестное место публикации'})
        group = None
        if destination == 'group':
            group = Group.objects.filter(pk=request.data.get('target_id') or request.data.get('group_id')).first()
            if not group: raise NotFound('Группа не найдена')
            if group.creator_id != request.user.pk and not GroupMembership.objects.filter(group=group, user=request.user).exists():
                raise PermissionDenied('Для публикации вступите в группу')
        existing = Post.objects.filter(author=request.user, original_post=original, group=group, post_type='repost', is_deleted=False).first()
        if existing: output = existing
        else:
            from apps.social.presentation.serializers.social_serializers import PostCreateSerializer
            payload = {'text': request.data.get('comment', ''), 'original_post': original.pk, 'post_type': 'repost',
                       'client_post_id': str(uuid.uuid5(uuid.NAMESPACE_URL, f'repost:{request.user.pk}:{key}'))}
            if group: payload['group'] = group.pk
            output, _ = create_post(SimpleNamespace(user=request.user, data=payload, FILES={}), PostCreateSerializer)
            Repost.objects.get_or_create(original_post=original, user=request.user, defaults={'comment': payload['text']})
        original.reposts_count = Post.objects.filter(original_post=original, status='published', is_deleted=False).count()
        original.save(update_fields=['reposts_count'])
        result = {'success': True, 'post_id': str(output.pk), 'action': 'repost', 'already_reposted': bool(existing)}
        record_event(original, 'post_reposted', actor_id=request.user.pk, already_reposted=bool(existing))
    PostCommand.objects.create(owner=request.user, kind='repost', key=key, fingerprint=fingerprint, post=output or original, response=result)
    return result


@transaction.atomic
def view(request, post_id):
    post = lock_post(request, post_id)
    if post.author_id != request.user.pk:
        _, created = FeedView.objects.get_or_create(user=request.user, post=post)
        if created:
            post.views_count = FeedView.objects.filter(post=post).count()
            post.save(update_fields=['views_count'])
    return {'success': True, 'views_count': post.views_count}


@transaction.atomic
def pin(request, post_id, active):
    post = lock_post(request, post_id)
    if post.author_id != request.user.pk: raise PermissionDenied('Закреплять можно только свои посты')
    if active:
        old = list(Post.objects.filter(author=request.user, is_pinned=True).exclude(pk=post.pk))
        Post.objects.filter(pk__in=[row.pk for row in old]).update(is_pinned=False, pinned_at=None)
        for row in old: record_event(row, 'post_unpinned', actor_id=request.user.pk)
    post.is_pinned, post.pinned_at = active, timezone.now() if active else None
    post.save(update_fields=['is_pinned', 'pinned_at'])
    record_event(post, 'post_pinned' if active else 'post_unpinned', actor_id=request.user.pk)
    return {'success': True, 'is_pinned': active}


@transaction.atomic
def hide(request, post_id):
    from apps.social.infrastructure.models.social import UserPostHidden
    post = lock_post(request, post_id)
    UserPostHidden.objects.get_or_create(user=request.user, post=post)
    record_event(post, 'post_hidden', actor_id=request.user.pk)
    return {'success': True, 'hidden': True}
