from datetime import timedelta
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from apps.social.application.post_access import readable_posts
from apps.social.application.post_commands import Conflict, payload_fingerprint, record_event
from apps.social.infrastructure.models.post_lifecycle import PostCommand
from apps.social.infrastructure.models.social import Post, PostComment, PostCommentLike, PostCommentDislike


def comments_for(user, post_id):
    visible = readable_posts(Post.objects.all(), user).filter(pk=post_id)
    if not visible.exists(): raise NotFound('Пост недоступен')
    viewer_id = user.pk if user.is_authenticated else None
    return PostComment.objects.filter(post_id=post_id, post__in=visible).select_related(
        'author', 'parent__author').annotate(
        user_liked=Exists(PostCommentLike.objects.filter(comment_id=OuterRef('pk'), user_id=viewer_id)),
        user_disliked=Exists(PostCommentDislike.objects.filter(comment_id=OuterRef('pk'), user_id=viewer_id)),
        visible_replies=Count('replies', filter=Q(replies__is_deleted=False)))


def locked_post(post_id, user):
    from apps.users.infrastructure.models.users import User
    User.objects.select_for_update().only('id').get(pk=user.pk)
    post = readable_posts(Post.objects.select_for_update(), user).filter(pk=post_id).first()
    if not post: raise NotFound('Пост недоступен')
    return post


@transaction.atomic
def create_comment(request, post_id):
    post = locked_post(post_id, request.user)
    if not post.allow_comments: raise PermissionDenied('Комментарии закрыты')
    key = request.data.get('client_comment_id')
    if key and len(str(key)) > 128: raise ValidationError({'client_comment_id': 'Слишком длинный ключ отправки'})
    fingerprint = payload_fingerprint(request)
    previous = PostCommand.objects.filter(owner=request.user, kind='comment', key=key).select_related('comment').first() if key else None
    if previous:
        if previous.post_id != post.pk or previous.fingerprint != fingerprint: raise Conflict('Ключ комментария уже использован')
        if not previous.comment or previous.comment.is_deleted: raise NotFound('Комментарий удалён')
        return previous.comment, False
    content = str(request.data.get('content', request.data.get('text')) or '').strip()
    if not content or len(content) > 2000: raise ValidationError({'content': 'Комментарий должен содержать от 1 до 2000 символов'})
    parent = None
    parent_id = request.data.get('parent')
    if parent_id:
        parent = PostComment.objects.select_for_update().filter(pk=parent_id, post=post, is_deleted=False).first()
        if not parent: raise ValidationError({'parent': 'Родитель должен принадлежать этому посту'})
        if parent.level >= 10: raise ValidationError({'parent': 'Максимальная глубина ответов -10'})
    comment = PostComment.objects.create(author=request.user, post=post, content=content, parent=parent, level=parent.level+1 if parent else 0)
    comment.path = f'{parent.path}.' if parent else ''
    comment.path += f'{comment.pk:020d}'
    comment.save(update_fields=['path'])
    if parent:
        parent.replies_count = parent.replies.filter(is_deleted=False).count()
        parent.save(update_fields=['replies_count'])
    post.comments_count = post.post_comments.filter(is_deleted=False).count()
    post.save(update_fields=['comments_count'])
    if key: PostCommand.objects.create(owner=request.user, kind='comment', key=key, fingerprint=fingerprint, post=post, comment=comment)
    record_event(post, 'post_comment', comment_id=str(comment.pk), actor_id=request.user.pk,
                 parent_author_id=parent.author_id if parent else None)
    return comment, True


@transaction.atomic
def change_comment(request, post_id, comment_id, delete=False, *, moderation=False):
    from apps.social.application.post_access import is_post_moderator
    moderate_delete = delete and moderation and is_post_moderator(request.user)
    if moderate_delete:
        from apps.users.infrastructure.models.users import User
        User.objects.select_for_update().only('id').get(pk=request.user.pk)
        post = Post.objects.select_for_update().filter(pk=post_id, is_deleted=False).first()
        if not post: raise NotFound('Пост недоступен')
    else:
        post = locked_post(post_id, request.user)
    comment = PostComment.objects.select_for_update().filter(pk=comment_id, post=post).first()
    if not comment: raise NotFound('Комментарий не найден')
    if comment.author_id != request.user.pk and not moderate_delete: raise PermissionDenied('Можно изменять только свой комментарий')
    if delete:
        if not comment.is_deleted:
            comment.is_deleted, comment.content, comment.deleted_at = True, '[комментарий удалён]', timezone.now()
            comment.save(update_fields=['is_deleted', 'content', 'deleted_at'])
            post.comments_count = post.post_comments.filter(is_deleted=False).count()
            post.save(update_fields=['comments_count'])
            if comment.parent_id:
                PostComment.objects.filter(pk=comment.parent_id).update(replies_count=PostComment.objects.filter(parent_id=comment.parent_id, is_deleted=False).count())
            record_event(post, 'post_comment_deleted', comment_id=str(comment.pk))
    else:
        if comment.is_deleted: raise NotFound('Комментарий удалён')
        if comment.created_at <= timezone.now()-timedelta(minutes=10): raise PermissionDenied('Редактирование доступно в течение десяти минут')
        if 'parent' in request.data and str(request.data['parent'] or '') != str(comment.parent_id or ''):
            raise ValidationError({'parent': 'Нельзя перемещать комментарий'})
        content = str(request.data.get('content', request.data.get('text')) or '').strip()
        if not content or len(content) > 2000: raise ValidationError({'content': 'Комментарий должен содержать от 1 до 2000 символов'})
        comment.content, comment.is_edited = content, True
        comment.save(update_fields=['content', 'is_edited', 'updated_at'])
        record_event(post, 'post_comment_updated', comment_id=str(comment.pk))
    return comment


@transaction.atomic
def react_comment(request, comment_id, reaction):
    post_id = PostComment.objects.filter(pk=comment_id).values_list('post_id', flat=True).first()
    if post_id is None: raise NotFound('Комментарий недоступен')
    post = locked_post(post_id, request.user)
    comment = PostComment.objects.select_for_update().filter(pk=comment_id, post=post, is_deleted=False).first()
    if not comment: raise NotFound('Комментарий недоступен')
    if comment.author_id == request.user.pk: raise PermissionDenied('Нельзя оценивать свой комментарий')
    desired = request.data.get('active')
    if desired is not None and not isinstance(desired, bool): raise ValidationError({'active': 'Ожидается true или false'})
    key = request.data.get('client_action_id')
    if key and len(str(key)) > 128: raise ValidationError({'client_action_id': 'Слишком длинный ключ отправки'})
    import hashlib
    fingerprint = hashlib.sha256(f'{comment.pk}:{reaction}:{desired}'.encode()).hexdigest()
    previous = PostCommand.objects.filter(owner=request.user, kind='comment-reaction', key=key).first() if key else None
    if previous:
        if previous.fingerprint != fingerprint: raise Conflict('Ключ действия уже использован')
        return previous.response
    selected, other = (PostCommentLike, PostCommentDislike) if reaction == 'like' else (PostCommentDislike, PostCommentLike)
    old = selected.objects.filter(comment=comment, user=request.user)
    active = not old.exists() if desired is None else desired
    old.delete()
    if active: other.objects.filter(comment=comment, user=request.user).delete()
    if active: selected.objects.create(comment=comment, user=request.user)
    comment.likes_count = PostCommentLike.objects.filter(comment=comment).count()
    comment.dislikes_count = PostCommentDislike.objects.filter(comment=comment).count()
    comment.save(update_fields=['likes_count', 'dislikes_count'])
    record_event(post, 'post_comment_reaction', comment_id=str(comment.pk), actor_id=request.user.pk)
    response = {'success': True, 'liked': PostCommentLike.objects.filter(comment=comment, user=request.user).exists(),
                'disliked': PostCommentDislike.objects.filter(comment=comment, user=request.user).exists(),
                'likes_count': comment.likes_count, 'dislikes_count': comment.dislikes_count}
    if key: PostCommand.objects.create(owner=request.user, kind='comment-reaction', key=key, fingerprint=fingerprint, post=post, comment=comment, response=response)
    return response
