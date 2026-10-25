from apps.social.infrastructure.post_media_urls import media_url


def content_visible(content, request):
    if not content: return False
    from apps.social.application.conversations import check_shareable
    from rest_framework.exceptions import APIException
    try:
        check_shareable(content, getattr(request, 'user', None))
        return True
    except APIException:
        return False


def original_post(post, context):
    if not post.original_post_id:
        return None
    originals = context.get('post_originals')
    if originals is None:
        originals = context.setdefault('post_original_details', {})
        if post.original_post_id not in originals:
            from apps.social.application.post_access import readable_posts
            from apps.social.application.post_feed import read_queryset
            from apps.social.infrastructure.models.social import Post
            user = getattr(context.get('request'), 'user', None)
            originals[post.original_post_id] = read_queryset(readable_posts(Post.objects.filter(pk=post.original_post_id), user), user).first()
    return originals.get(post.original_post_id)


class PostReadMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.pk)
        data['public_id'] = str(instance.public_id)
        data['version'] = instance.version
        request = self.context.get('request')
        if instance.playlist and not content_visible(instance.playlist, request): data['playlist'] = None
        if instance.reactor_post and not content_visible(instance.reactor_post, request): data['reactor_post'] = None
        data['attachments_data'] = [item for item in data.get('attachments_data', [])
                                    if item.get('content_type') != 'unavailable']
        for field in ('image_file', 'video_file'):
            file = getattr(instance, field)
            if file:
                data[field] = media_url(file.name, self.context.get('request'))
        if instance.image_file or instance.video_file:
            data['media_url'] = data.get('video_file') or data.get('image_file')
            from apps.social.application.post_legacy_media import legacy_fields, storage
            existing = {item.file.name for item in instance.media_files.all() if item.file}
            for kind, file in legacy_fields(instance):
                if file.name not in existing:
                    data.setdefault('media_files', []).append({
                        'id': 'legacy:' + kind, 'post': str(instance.pk), 'media_type': kind,
                        'url': data[kind + '_file'], 'file_size': storage.size(file.name) if storage.exists(file.name) else 0,
                        'processing_state': 'ready', 'sources': []})
        data['processing'] = bool(instance.pending_edit) or instance.status in ('processing', 'failed')
        if instance.pending_edit and request and request.user.pk == instance.author_id:
            from .social_serializers import PostMediaSerializer
            data['processing_media'] = PostMediaSerializer(
                [item for item in instance.media_files.all() if item.pk in instance.pending_edit.get('new_media_ids', [])],
                many=True, context=self.context).data
        return data


def anime_card(anime, request=None, rating=None):
    if anime is None: return None
    poster = anime.poster.url if anime.poster else anime.poster_url or None
    if poster and request and not poster.startswith(('http:', 'https:')): poster = request.build_absolute_uri(poster)
    return {'id': anime.pk, 'title_ru': anime.title_ru, 'title_en': anime.title_en,
            'slug': anime.slug, 'year': anime.year, 'description': (anime.description or '')[:240],
            'poster': poster, 'poster_url': poster, 'rating': rating}


def playlist_card(playlist, request=None):
    if not content_visible(playlist, request): return None
    cover = playlist.cover_image.url if playlist.cover_image else None
    if cover and request and not cover.startswith(('http:', 'https:')): cover = request.build_absolute_uri(cover)
    count = getattr(playlist, 'card_items_count', None)
    if count is None: count = playlist.items.count()
    items = getattr(playlist, 'card_items', None)
    if items is None: items = list(playlist.items.select_related('anime').all()[:4])
    anime = [anime_card(item.anime, request) for item in items]
    return {'id': playlist.pk, 'title': playlist.title, 'description': (playlist.description or '')[:240],
            'anime_count': count, 'items_count': count, 'poster_url': cover, 'cover_image': cover, 'anime': anime}


def reactor_card(reactor, request=None):
    if not content_visible(reactor, request): return None
    return {'id': reactor.pk, 'title': reactor.title, 'video_url': reactor.video_url,
            'duration': getattr(reactor, 'duration', None), 'likes_count': reactor.likes_count,
            'comments_count': reactor.comments_count, 'user': {'id': reactor.user_id, 'username': reactor.user.username}}


def attachment_content(attachment, context):
    from apps.anime.infrastructure.models.anime import Anime
    from apps.playlists.infrastructure.models.playlists import Playlist
    from apps.reactor.infrastructure.models.reactor import ReactorPost
    kind = attachment.content_type
    cache = context.get('post_contents', {})
    object_id = str(attachment.object_id).zfill(8) if kind == 'playlist' else attachment.object_id
    if kind in cache: return cache[kind].get(object_id)
    model = {'anime': Anime, 'playlist': Playlist, 'shorts': ReactorPost}.get(kind)
    return model.objects.filter(pk=object_id).first() if model else None


def post_anime(post, context):
    attached = next((item for item in post.attachments.all() if item.content_type == 'anime'), None)
    anime = attachment_content(attached, context) if attached else post.anime
    rating = attached.metadata.get('rating') if attached and isinstance(attached.metadata, dict) else post.anime_rating
    return anime_card(anime, context.get('request'), rating)


from rest_framework import serializers
class PostListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        from apps.anime.infrastructure.models.anime import Anime
        from apps.playlists.infrastructure.models.playlists import Playlist, PlaylistItem
        from apps.reactor.infrastructure.models.reactor import ReactorPost
        from django.db.models import Count, Prefetch
        rows = list(data.all() if hasattr(data, 'all') else data)
        ids = {'anime': set(), 'playlist': set(), 'shorts': set()}
        posts = list(rows)
        from apps.social.application.post_access import readable_posts
        from apps.social.application.post_feed import read_queryset
        from apps.social.infrastructure.models.social import Post
        user = getattr(self.context.get('request'), 'user', None)
        originals = {}
        level = rows
        for _ in range(2):
            targets = {row.original_post_id for row in level if row.original_post_id} - originals.keys()
            if not targets: break
            level = list(read_queryset(readable_posts(Post.objects.filter(pk__in=targets), user), user))
            originals.update((post.pk, post) for post in level)
            posts.extend(level)
        self.context['post_originals'] = originals
        for post in posts:
            for item in post.attachments.all():
                if item.content_type in ids: ids[item.content_type].add(str(item.object_id).zfill(8) if item.content_type == 'playlist' else item.object_id)
            if post.playlist_id: ids['playlist'].add(post.playlist_id)
        previews = PlaylistItem.objects.select_related('anime').order_by('position', 'pk')[:4]
        self.context['post_contents'] = {
            'anime': Anime.objects.in_bulk(ids['anime']),
            'playlist': Playlist.objects.annotate(card_items_count=Count('items')).prefetch_related(Prefetch('items', queryset=previews, to_attr='card_items')).in_bulk(ids['playlist']),
            'shorts': ReactorPost.objects.select_related('user').in_bulk(ids['shorts']),
        }
        return super().to_representation(rows)
