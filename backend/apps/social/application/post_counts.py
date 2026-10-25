from apps.social.infrastructure.models.social import Post, Group, Hashtag
from apps.users.infrastructure.models.users import User


def remember_related(post):
    post._previous_tag_ids = list(post.hashtag_links.values_list('hashtag_id', flat=True))
    post._previous_group_id = post.group_id
    post._previous_visibility = post.visibility


def refresh_related(post):
    User.objects.select_for_update().only('id').get(pk=post.author_id)
    User.objects.filter(pk=post.author_id).update(posts_count=Post.objects.filter(
        author_id=post.author_id, status='published', is_deleted=False).count())
    if post.original_post_id:
        original = Post.objects.select_for_update().filter(pk=post.original_post_id).first()
        if original:
            count = Post.objects.filter(original_post=original, status='published', is_deleted=False).count()
            Post.objects.filter(pk=original.pk).update(reposts_count=count)
    groups = {post.group_id, getattr(post, '_previous_group_id', None)} - {None}
    for group in Group.objects.select_for_update().filter(pk__in=groups).order_by('pk'):
        Group.objects.filter(pk=group.pk).update(posts_count=Post.objects.filter(group=group, status='published', is_deleted=False).count())
    tags = set(getattr(post, '_previous_tag_ids', [])) | set(post.hashtag_links.values_list('hashtag_id', flat=True))
    for tag in Hashtag.objects.select_for_update().filter(pk__in=tags).order_by('pk'):
        Hashtag.objects.filter(pk=tag.pk).update(posts_count=tag.post_links.filter(post__status='published', post__is_deleted=False).count())
