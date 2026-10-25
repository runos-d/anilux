import mimetypes
from apps.social.infrastructure.models.social import PostMedia
from apps.social.infrastructure.post_storage import post_private_storage as storage


def legacy_fields(post):
    return [(kind, getattr(post, kind + '_file')) for kind in ('image', 'video') if getattr(post, kind + '_file')]


def register_legacy_media(post):
    registered = {}
    for kind, file in legacy_fields(post):
        size = storage.size(file.name) if storage.exists(file.name) else 0
        media, _ = PostMedia.objects.get_or_create(post=post, file=file.name, defaults={
            'media_type': kind, 'file_size': size, 'mime_type': mimetypes.guess_type(file.name)[0] or '',
            'processing_state': 'ready', 'is_active': True})
        registered['legacy:' + kind] = media.pk
    if registered:
        getattr(post, '_prefetched_objects_cache', {}).pop('media_files', None)
    return registered
