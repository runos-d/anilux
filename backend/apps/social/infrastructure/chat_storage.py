from pathlib import Path
import hashlib
from urllib.parse import quote, urlencode

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core import signing
from django.core.cache import cache
from django.utils.deconstruct import deconstructible


@deconstructible
class ChatPrivateStorage(FileSystemStorage):
    @property
    def location(self):
        return str(Path(settings.CHAT_PRIVATE_MEDIA_ROOT).resolve())

    @property
    def base_location(self):
        return self.location

    def url(self, name):
        return '/api/social/chat-media/' + quote(name, safe='/')


chat_private_storage = ChatPrivateStorage()


def private_file_url(file, request=None):
    if not file:
        return None
    url = file.storage.url(file.name)
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        key = f'chat-media:ticket:{user.pk}:' + hashlib.sha256(file.name.encode()).hexdigest()
        try: ticket = cache.get(key)
        except Exception: ticket = None
        if not ticket:
            ticket = signing.dumps({'name': file.name, 'user': user.pk}, salt='chat-media-v1')
            try: cache.set(key, ticket, max(1, min(900, settings.CHAT_MEDIA_TICKET_MAX_AGE // 2)))
            except Exception: pass
        url += '?' + urlencode({'ticket': ticket})
    return request.build_absolute_uri(url) if request else url
