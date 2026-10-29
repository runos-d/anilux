import mimetypes
from pathlib import PurePosixPath, Path
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.db.models import Q
from django.http import HttpResponse
from django.utils.http import content_disposition_header
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny

from apps.social.application.post_access import readable_posts, group_access
from apps.social.infrastructure.models.social import Post, PostMedia
from apps.social.infrastructure.post_storage import post_private_storage as storage
from apps.users.infrastructure.models.users import User
from core.file_delivery import private_file_response


from apps.social.infrastructure.post_media_urls import media_url


@api_view(['GET', 'HEAD'])
@permission_classes([AllowAny])
def serve_post_media(request, name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise NotFound()
    user = request.user
    ticket = request.query_params.get('ticket')
    if ticket:
        try:
            grant = signing.loads(ticket, salt='post-media-v1', max_age=86400)
            if grant['name'] != name:
                raise signing.BadSignature()
            if grant['user'] is not None:
                user = User.objects.get(pk=grant['user'], is_active=True)
        except (signing.BadSignature, KeyError, ValueError):
            raise PermissionDenied('Ссылка на файл истекла или недействительна')
        except User.DoesNotExist:
            raise PermissionDenied('Файл недоступен')
    candidates = PostMedia.objects.filter(Q(is_active=True) | Q(post__author=user) if user.is_authenticated else Q(is_active=True)).filter(Q(file=name) | Q(thumbnail=name) | Q(poster=name) |
        Q(upload__original_path=name) | Q(variants__720p=name) | Q(variants__original=name)).values('post_id')
    posts = Post.objects.filter(Q(pk__in=candidates) | Q(image_file=name) | Q(video_file=name))
    permitted = readable_posts(posts, user).exists()
    if user.is_authenticated:
        permitted = permitted or posts.filter(group_access(user), author=user, is_deleted=False).exists()
        if user.is_staff or user.is_superuser:
            permitted = permitted or posts.exists()
    if not permitted or not storage.exists(name):
        raise NotFound('Файл недоступен')
    physical = Path(storage.path(name))
    size = physical.stat().st_size
    mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    headers = {'Cache-Control': 'private, no-store', 'Accept-Ranges': 'bytes', 'X-Content-Type-Options': 'nosniff',
               'Content-Disposition': content_disposition_header(bool(request.query_params.get('download')), path.name)}
    if request.headers.get('X-Post-Accel') == '1':
        root = Path(settings.MEDIA_ROOT) if name.startswith('posts/') and not (Path(storage.location) / name).exists() else Path(storage.location)
        internal = '/_post_legacy/' if root == Path(settings.MEDIA_ROOT) else '/_post_private/'
        response = HttpResponse(content_type=mime, headers=headers)
        response['X-Accel-Redirect'] = internal + quote(physical.relative_to(root).as_posix(), safe='/')
        return response
    return private_file_response(physical, method=request.method, range_header=request.headers.get('Range'),
                                 size=size, content_type=mime, headers=headers)
