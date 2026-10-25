from django.db.models import Count, Q
from apps.social.infrastructure.models.social import Post

COUNTERS = ('likes', 'dislikes', 'comments', 'reposts')


def counter_rows(queryset=None):
    return (queryset if queryset is not None else Post.objects.all()).annotate(
        actual_likes=Count('likes', distinct=True), actual_dislikes=Count('dislikes', distinct=True),
        actual_comments=Count('post_comments', filter=Q(post_comments__is_deleted=False), distinct=True),
        actual_reposts=Count('reposts_of', filter=Q(reposts_of__is_deleted=False, reposts_of__status='published'), distinct=True))


def differences(post):
    return {kind: {'stored': getattr(post, kind+'_count'), 'actual': getattr(post, 'actual_'+kind)}
        for kind in COUNTERS if getattr(post, kind+'_count') != getattr(post, 'actual_'+kind)}
