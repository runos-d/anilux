from datetime import timedelta
from collections import deque

from django.core import signing
import hashlib
from django.db.models import Prefetch, Q, Exists, OuterRef, F
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from apps.social.application.post_access import readable_posts
from apps.social.infrastructure.models.post_lifecycle import PostFeedSnapshot
from apps.social.infrastructure.models.social import Post, Follow, GroupMembership, UserPostHidden, PostLike, Bookmark, UserNotInterested
from apps.social.infrastructure.models.social import PostDislike


def read_queryset(queryset, user):
    from django.contrib.contenttypes.models import ContentType
    from apps.social.infrastructure.models.social import Favorite
    user_id = user.pk if user and user.is_authenticated else None
    return queryset.select_related('author', 'anime', 'playlist', 'group', 'reactor_post__user', 'original_post', 'original_post__author', 'original_post__anime', 'original_post__playlist', 'original_post__group').prefetch_related(
        'media_files', 'attachments', 'hashtag_links__hashtag', 'original_post__media_files', 'original_post__attachments', 'original_post__hashtag_links__hashtag').annotate(
        viewer_liked=Exists(PostLike.objects.filter(user_id=user_id, post_id=OuterRef('pk'))),
        viewer_disliked=Exists(PostDislike.objects.filter(user_id=user_id, post_id=OuterRef('pk'))),
        viewer_bookmarked=Exists(Bookmark.objects.filter(user_id=user_id, post_id=OuterRef('pk'))),
        viewer_favorited=Exists(Favorite.objects.filter(user_id=user_id, object_id=OuterRef('pk'), content_type=ContentType.objects.get_for_model(Post))),
        viewer_following=Exists(Follow.objects.filter(follower_id=user_id, following_id=OuterRef('author_id'))))


def ranked(request, mode):
    return page(request, mode)


def page(request, mode='weighted'):
    try:
        limit = max(1, min(int(request.query_params.get('page_size', request.query_params.get('limit', 20))), 100))
        old_page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        raise ValidationError('Некорректный размер страницы')
    user = request.user
    cursor = request.query_params.get('cursor')
    signature = '&'.join(f'{key}={request.query_params.getlist(key)}' for key in sorted(request.query_params)
                         if key not in ('cursor', 'page', 'page_size', 'include_count'))
    snapshot_mode = mode[:8] + ':' + hashlib.sha256(signature.encode()).hexdigest()[:20]
    following = set(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
    groups = set(GroupMembership.objects.filter(user=user).values_list('group_id', flat=True))
    base = readable_posts(Post.objects.all(), user).exclude(post_type='system').annotate(feed_date=F('feed_sort_at'))
    base = base.exclude(pk__in=UserPostHidden.objects.filter(user=user).values('post_id'))
    base = base.exclude(author_id__in=UserNotInterested.objects.filter(user=user).values('target_user_id'))
    order_by = ['-feed_date', '-pk']
    if mode in ('hot', 'top', 'trending'):
        try:
            amount = int(request.query_params.get('days', 7)) if mode == 'top' else int(request.query_params.get('hours', 6 if mode == 'trending' else 24))
            if not 1 <= amount <= (365 if mode == 'top' else 720): raise ValueError()
        except (ValueError, TypeError): raise ValidationError('Некорректный период ленты')
        period = timedelta(days=amount) if mode == 'top' else timedelta(hours=amount)
        base = base.filter(feed_date__gte=timezone.now()-period).annotate(activity=F('likes_count')+F('comments_count')*2+F('views_count'))
        order_by = ['-activity', '-feed_date', '-pk']
    if mode == 'extended':
        params = request.query_params
        if params.get('with_anime') == 'true':
            base = base.filter(Q(anime__isnull=False) | Q(playlist__isnull=False) | Q(attachments__content_type__in=['anime', 'playlist'])).distinct()
        if params.get('anime_id'):
            try:
                base = base.filter(anime_id=int(params['anime_id']))
            except ValueError:
                raise ValidationError({'anime_id': 'Некорректный идентификатор'})
        if params.get('my_posts') == 'true': base = base.filter(author=user)
        if params.get('subscriptions') == 'true': base = base.filter(author_id__in=following)
        if params.get('groups') == 'true': base = base.filter(group_id__in=groups)
        tags = [tag for value in params.getlist('tags') for tag in value.split(',') if tag]
        if tags: base = base.filter(hashtag_links__hashtag__name__in=tags).distinct()
        days = {'day': 1, 'week': 7, 'month': 30}.get(params.get('date_range'))
        if days: base = base.filter(feed_date__gte=timezone.now()-timedelta(days=days))
        orders = {'new': ['-feed_date', '-pk'], 'old': ['feed_date', 'pk'],
                  'best': ['-likes_count', '-feed_date', '-pk'], 'discussed': ['-comments_count', '-feed_date', '-pk']}
        if params.get('sort', 'new') not in orders: raise ValidationError({'sort': 'Неизвестная сортировка'})
        order_by = orders[params.get('sort', 'new')]
    if mode == 'followers':
        base = base.filter(author_id__in=following)
    salt = 'post-feed-bounded-v2'
    cutoff, boundaries = timezone.now(), {}
    if cursor:
        try:
            position = signing.loads(cursor, salt=salt, max_age=900)
            if position['mode'] != snapshot_mode or position['owner'] != str(user.pk):
                raise ValueError()
            cutoff = parse_datetime(position['cutoff'])
            boundaries = position['boundaries']
            if not cutoff or not isinstance(boundaries, dict):
                raise ValueError()
        except (signing.BadSignature, KeyError, ValueError, TypeError):
            raise ValidationError({'cursor': 'Курсор устарел или недействителен. Обновите ленту.'})
    elif old_page > 100:
        raise ValidationError({'page': 'Для дальнейшей загрузки используйте cursor.'})
    visible = base.filter(feed_date__lte=cutoff)
    unpinned = visible.exclude(is_pinned=True)

    def read_slice(queryset, key, order):
        fields = [field.lstrip('-') for field in order]
        boundary = boundaries.get(key)
        if boundary:
            if not isinstance(boundary, list) or len(boundary) != len(fields):
                raise ValidationError({'cursor': 'Некорректный курсор.'})
            condition, equal = Q(pk__in=[]), Q()
            for field, value, ordering in zip(fields, boundary, order):
                if field == 'feed_date':
                    value = parse_datetime(value)
                    if value is None:
                        raise ValidationError({'cursor': 'Некорректная дата курсора.'})
                condition |= equal & Q(**{field + ('__lt' if ordering.startswith('-') else '__gt'): value})
                equal &= Q(**{field: value})
            queryset = queryset.filter(condition)
        offset = 0 if cursor else (old_page - 1) * limit
        return list(queryset.order_by(*order).values(*fields)[offset:offset + limit + 1])

    next_boundaries = dict(boundaries)
    selected, more = [], False
    if mode == 'weighted':
        own = Q(author_id__in=following | {user.pk})
        grouped = Q(group_id__in=groups)
        pools = [read_slice(unpinned.filter(own), '0', ['-feed_date', '-pk']),
                 read_slice(unpinned.exclude(own).filter(grouped), '1', ['-feed_date', '-pk']),
                 read_slice(unpinned.exclude(own).exclude(grouped), '2', ['-feed_date', '-pk'])]
        used = [0, 0, 0]
        while len(selected) < limit:
            previous = len(selected)
            for index, quota in ((0, 14), (1, 3), (2, 3)):
                count = min(quota, limit - len(selected), len(pools[index]) - used[index])
                rows = pools[index][used[index]:used[index] + count]
                selected.extend(row['pk'] for row in rows)
                used[index] += count
                if rows:
                    next_boundaries[str(index)] = [rows[-1]['feed_date'].isoformat(), str(rows[-1]['pk'])]
            if len(selected) == previous:
                break
        more = any(len(pool) > count for pool, count in zip(pools, used))
    else:
        rows = read_slice(unpinned, 'all', order_by)
        more = len(rows) > limit
        rows = rows[:limit]
        selected = [row['pk'] for row in rows]
        if rows:
            next_boundaries['all'] = [value.isoformat() if hasattr(value, 'isoformat') else str(value) if field == 'pk' else value
                                      for field in [item.lstrip('-') for item in order_by] for value in [rows[-1][field]]]
    pinned = list(visible.filter(is_pinned=True).order_by('-pinned_at', '-pk').values_list('pk', flat=True)[:20]) if not cursor and old_page == 1 else []
    ids = [pk for pk in pinned if pk not in selected] + selected
    posts = {post.pk: post for post in read_queryset(visible.filter(pk__in=ids), user)}
    next_cursor = signing.dumps({'mode': snapshot_mode, 'owner': str(user.pk), 'cutoff': cutoff.isoformat(),
                                 'boundaries': next_boundaries}, salt=salt) if more else None
    from apps.social.presentation.serializers.social_serializers import FeedPostSerializer
    return {'results': FeedPostSerializer([posts[pk] for pk in ids if pk in posts], many=True, context={'request': request}).data,
            'count': None if request.query_params.get('include_count', 'true').lower() in ('false', '0') else visible.count(),
            'next_cursor': next_cursor, 'next': old_page + 1 if next_cursor else None,
            'previous': old_page - 1 if old_page > 1 else None}


def chronological_page(request, queryset, scope, *, include_own_pending=False):
    from apps.social.presentation.serializers.social_serializers import PostSerializer
    try:
        limit = max(1, min(int(request.query_params.get('limit', request.query_params.get('page_size', 20))), 100))
        number = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError): raise ValidationError('Некорректная страница')
    identity = f'{getattr(request.user, "pk", None)}:{scope}'
    cutoff = timezone.now()
    cursor = request.query_params.get('cursor')
    boundary = None
    if cursor:
        try:
            position = signing.loads(cursor, salt='post-list-v1', max_age=900)
            if position['scope'] != identity: raise ValueError()
            from django.utils.dateparse import parse_datetime
            cutoff = parse_datetime(position['cutoff'])
            boundary = (parse_datetime(position['created']), int(position['id']))
            if not cutoff or not boundary[0]: raise ValueError()
        except (signing.BadSignature, KeyError, ValueError, TypeError):
            raise ValidationError({'cursor': 'Курсор устарел. Обновите список.'})
    base = readable_posts(queryset, request.user, include_own_pending=include_own_pending).filter(created_at__lte=cutoff)
    total = base.count()
    if boundary:
        base = base.filter(Q(created_at__lt=boundary[0]) | Q(created_at=boundary[0], pk__lt=boundary[1]))
    offset = 0 if cursor else (number-1)*limit
    ids = list(base.order_by('-created_at', '-pk').values_list('pk', flat=True)[offset:offset+limit+1])
    more = len(ids) > limit
    hydrated = {post.pk: post for post in read_queryset(base.filter(pk__in=ids[:limit]), request.user)}
    rows = [hydrated[pk] for pk in ids[:limit] if pk in hydrated]
    next_cursor = signing.dumps({'scope': identity, 'cutoff': cutoff.isoformat(),
        'created': rows[-1].created_at.isoformat(), 'id': str(rows[-1].pk)}, salt='post-list-v1') if more and rows else None
    return {'results': PostSerializer(rows, many=True, context={'request': request}).data,
            'count': total, 'page': number, 'limit': limit, 'next_cursor': next_cursor,
            'next': number+1 if more else None, 'previous': number-1 if number>1 else None}
