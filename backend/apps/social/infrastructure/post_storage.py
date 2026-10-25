from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PostPrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=getattr(settings, 'POST_PRIVATE_MEDIA_ROOT', Path(settings.DATA_DIR) / 'private_post_media'), base_url='/api/social/post-media/path/')

    def path(self, name):
        private = super().path(name)
        if name.startswith('posts/') and not Path(private).exists():
            return str(Path(settings.MEDIA_ROOT) / name)
        return private


post_private_storage = PostPrivateStorage()
