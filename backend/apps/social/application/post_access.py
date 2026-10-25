from django.db.models import Q

from apps.social.infrastructure.models.social import Follow, Group, GroupMembership


def is_post_moderator(user):
    return bool(user and user.is_authenticated and (
        user.is_staff or user.is_superuser or getattr(user, 'role', None) in ('moderator', 'admin')))


def readable_posts(queryset, user, *, include_own_pending=False):
    queryset = queryset.filter(is_deleted=False)
    states = Q(status='published')
    visibility = Q(visibility='public')
    if user and user.is_authenticated:
        if include_own_pending:
            states |= Q(author=user, status__in=['draft', 'processing', 'failed'])
        following = Follow.objects.filter(follower=user).values('following_id')
        followers = Follow.objects.filter(following=user).values('follower_id')
        visibility |= Q(author=user)
        visibility |= Q(visibility='followers', author_id__in=following)
        visibility |= Q(visibility='friends', author_id__in=following) & Q(author_id__in=followers)
    return queryset.filter(states & visibility & group_access(user))


def group_access(user):
    permitted = Q(is_private=False)
    if user and user.is_authenticated:
        permitted |= Q(creator=user) | Q(pk__in=GroupMembership.objects.filter(user=user).values('group_id'))
    return Q(group__isnull=True) | Q(group_id__in=Group.objects.filter(permitted).values('pk'))


def resolve_post_id(value):
    from apps.social.infrastructure.models.social import Post
    from rest_framework.exceptions import NotFound
    try: value = int(value)
    except (TypeError, ValueError): raise NotFound('Пост не найден')
    primary = Post.objects.filter(pk=value).values_list('pk', flat=True).first()
    if primary is not None: return primary
    primary = Post.objects.filter(public_id=value).values_list('pk', flat=True).first()
    if primary is None: raise NotFound('Пост не найден')
    return primary
