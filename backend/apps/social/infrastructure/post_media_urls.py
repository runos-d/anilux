from urllib.parse import quote
from django.core import signing
from django.core.cache import cache
import hashlib


def media_url(name, request=None):
    if not name: return None
    user = getattr(request, 'user', None)
    viewer = user.pk if user and user.is_authenticated else None
    key = f'post-media-ticket-v1:{viewer}:{hashlib.sha256(str(name).encode()).hexdigest()}'
    ticket = cache.get_or_set(key, lambda: signing.dumps({'name': name, 'user': viewer}, salt='post-media-v1'), timeout=3600)
    path = '/api/social/post-media/path/' + quote(str(name), safe='/') + '?ticket=' + quote(ticket, safe='')
    return request.build_absolute_uri(path) if request else path
