from datetime import timedelta
from collections import deque

from django.core import signing
import hashlib
from django.db.models import Prefetch, Q, Exists, OuterRef, F
from django.db.models.functions import Coalesce
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
                         if key not in ('cursor', 'page', 'page_size'))
    snapshot_mode = mode[:8] + ':' + hashlib.sha256(signature.encode()).hexdigest()[:20]
    following = set(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
    groups = set(GroupMembership.objects.filter(user=user).values_list('group_id', flat=True))
    base = readable_posts(Post.objects.all(), user).exclude(post_type='system').annotate(feed_date=Coalesce('published_at', 'created_at'))
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
    if mode == 'extended' and request.query_params.get('sort', 'new') == 'new':
        direct_salt = 'post-feed-direct-v1'
        cutoff = timezone.now()
        boundary = None
        if cursor:
            try:
                position = signing.loads(cursor, salt=direct_salt, max_age=900)
                if position.get('mode') != snapshot_mode:
                    raise ValueError()
                cutoff = parse_datetime(position['cutoff'])
                boundary_date = parse_datetime(position['date'])
                if not cutoff or not boundary_date:
                    raise ValueError()
                boundary = (boundary_date, position['id'])
            except (signing.BadSignature, KeyError, ValueError, TypeError):
                raise ValidationError({'cursor': 'Курсор устарел или недействителен. Обновите ленту.'})
        visible = base.filter(feed_date__lte=cutoff)
        unpinned = visible.exclude(is_pinned=True)
        if boundary:
            unpinned = unpinned.filter(
                Q(feed_date__lt=boundary[0]) | Q(feed_date=boundary[0], pk__lt=boundary[1])
            )
        offset = 0 if cursor else (old_page - 1) * limit
        rows = list(unpinned.order_by('-feed_date', '-pk').values_list('pk', 'feed_date')[offset:offset + limit + 1])
        more = len(rows) > limit
        rows = rows[:limit]
        selected = [pk for pk, _ in rows]
        pinned = list(visible.filter(is_pinned=True).order_by('-pinned_at', '-pk').values_list('pk', flat=True)[:20]) \
            if not cursor and old_page == 1 else []
        pinned = [pk for pk in pinned if pk not in selected]
        queryset = read_queryset(visible.filter(pk__in=pinned + selected), user)
        posts = {post.pk: post for post in queryset}
        next_cursor = None
        if more and rows:
            last_id, last_date = rows[-1]
            next_cursor = signing.dumps({
                'mode': snapshot_mode, 'cutoff': cutoff.isoformat(),
                'date': last_date.isoformat(), 'id': str(last_id),
            }, salt=direct_salt)
        from apps.social.presentation.serializers.social_serializers import FeedPostSerializer
        return {
            'results': FeedPostSerializer(
                [posts[pk] for pk in pinned + selected if pk in posts],
                many=True, context={'request': request},
            ).data,
            'count': visible.count(),
            'next_cursor': next_cursor,
            'next': old_page + 1 if next_cursor else None,
            'previous': old_page - 1 if old_page > 1 else None,
        }
    if cursor:
        try:
            position = signing.loads(cursor, salt='post-feed-v1', max_age=900)
            snapshot = PostFeedSnapshot.objects.get(pk=position['snapshot'], owner=user, mode=snapshot_mode)
            offset = int(position['offset'])
            if not 0 <= offset <= len(snapshot.ids):
                raise ValueError()
        except (signing.BadSignature, KeyError, ValueError, PostFeedSnapshot.DoesNotExist):
            raise ValidationError({'cursor': 'Курсор устарел или недействителен. Обновите ленту.'})
    else:
        snapshot = None
        if old_page > 1:
            snapshot = PostFeedSnapshot.objects.filter(owner=user, mode=snapshot_mode, expires_at__gt=timezone.now()).order_by('-created_at').first()
        if snapshot is None:
            rows = list(base.exclude(is_pinned=True).order_by(*order_by).values('pk', 'author_id', 'group_id').iterator(chunk_size=2000))
            if mode == 'weighted':
                buckets = [deque(), deque(), deque()]
                for row in rows:
                    index = 0 if row['author_id'] in following or row['author_id'] == user.pk else 1 if row['group_id'] in groups else 2
                    buckets[index].append(row['pk'])
                order = []
                while any(buckets):
                    for index, amount in ((0, 14), (1, 3), (2, 3)):
                        for _ in range(amount):
                            if buckets[index]:
                                order.append(buckets[index].popleft())
                ids = order
            else:
                ids = [row['pk'] for row in rows]
            snapshot = PostFeedSnapshot.objects.create(owner=user, mode=snapshot_mode, ids=ids,
                                                       expires_at=timezone.now()+timedelta(minutes=15))
        offset = (old_page-1)*limit
    selected = []
    while offset < len(snapshot.ids) and len(selected) < limit:
        candidates = snapshot.ids[offset:offset + limit - len(selected)]
        visible = set(base.filter(pk__in=candidates).values_list('pk', flat=True))
        offset += len(candidates)
        selected.extend(pk for pk in candidates if pk in visible)
    pinned = list(base.filter(is_pinned=True).order_by('-pinned_at', '-pk').values_list('pk', flat=True)[:20]) if not cursor and old_page == 1 else []
    pinned = [pk for pk in pinned if pk not in selected]
    queryset = read_queryset(base.filter(pk__in=pinned+selected), user)
    posts = {post.pk: post for post in queryset}
    next_cursor = signing.dumps({'snapshot': str(snapshot.pk), 'offset': offset}, salt='post-feed-v1') if offset < len(snapshot.ids) else None
    from apps.social.presentation.serializers.social_serializers import FeedPostSerializer
    return {'results': FeedPostSerializer([posts[pk] for pk in pinned+selected if pk in posts], many=True, context={'request': request}).data,
            'count': base.filter(feed_date__lte=snapshot.created_at).count(), 'next_cursor': next_cursor,
            'next': old_page+1 if next_cursor else None, 'previous': old_page-1 if old_page>1 else None}


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
