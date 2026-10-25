import mimetypes
import hashlib
import re
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core import signing
from django.http import FileResponse, StreamingHttpResponse, HttpResponse
from django.utils.http import content_disposition_header
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound, PermissionDenied, APIException

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import Message, Attachment
from apps.social.infrastructure.models.social_chat import ScheduledMessage
from apps.social.infrastructure.chat_storage import chat_private_storage
from apps.social.application import conversations as service


def public_chat_file_denied(request, path=None):
    return HttpResponse(status=404)


@api_view(['GET', 'HEAD'])
@permission_classes([AllowAny])
def chat_media(request, name):
    path = PurePosixPath(name)
    if '\\' in name or path.is_absolute() or '..' in path.parts or not name.startswith(('message_media/', 'attachments/', 'scheduled_messages/')):
        raise NotFound('Файл не найден')
    user = request.user
    ticket = request.query_params.get('ticket')
    if ticket:
        try:
            try:
                grant = signing.loads(ticket, salt='chat-media-v1', max_age=settings.CHAT_MEDIA_TICKET_MAX_AGE)
            except signing.SignatureExpired:
                grant = signing.loads(ticket, salt='chat-media-v1')
                if not request.user.is_authenticated or grant.get('user') != request.user.pk:
                    raise signing.BadSignature()
            if grant.get('name') != name:
                raise signing.BadSignature()
            user = User.objects.get(pk=grant['user'], is_active=True)
        except (signing.BadSignature, User.DoesNotExist, KeyError):
            raise PermissionDenied('Ссылка истекла или недействительна')
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Требуется авторизация')
    message_ids = Attachment.objects.filter(file=name).values_list('message_id', flat=True)
    thumb_ids = Attachment.objects.filter(thumbnail=name).values_list('message_id', flat=True)
    from django.db.models import Q
    candidates = Message.objects.filter(Q(media=name) | Q(pk__in=message_ids) | Q(pk__in=thumb_ids)).select_related('chat', 'private_chat')
    permitted = False
    for job in ScheduledMessage.objects.filter(sender=user, media=name).select_related('chat', 'private_chat'):
        try:
            service.check_access(job.chat or job.private_chat, user)
            permitted = True
            break
        except APIException:
            continue
    for message in candidates:
        try:
            if service.visible_messages(message.parent_chat, user).filter(pk=message.pk).exists():
                if request.query_params.get('download') and message.chat_id and message.chat.restrict_saving_content and message.sender_id != user.pk:
                    continue
                permitted = True
                break
        except APIException:
            continue
    if not permitted or not chat_private_storage.exists(name):
        raise NotFound('Файл недоступен')
    file = chat_private_storage.open(name, 'rb')
    size = file.size
    mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    cache_control = 'private, no-store'
    etag = None
    if mime.startswith('video/'):
        stat = Path(chat_private_storage.path(name)).stat()
        etag = '"' + hashlib.sha256(f'{name}:{size}:{stat.st_mtime_ns}'.encode()).hexdigest() + '"'
        cache_control = 'private, no-cache, must-revalidate'
        if etag in request.headers.get('If-None-Match', '').split(', ') or request.headers.get('If-None-Match') == '*':
            file.close()
            return HttpResponse(status=304, headers={'ETag': etag, 'Cache-Control': cache_control, 'Accept-Ranges': 'bytes'})
    range_header = request.headers.get('Range')
    if etag and request.headers.get('If-Range') and request.headers['If-Range'] != etag:
        range_header = None
    if range_header:
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
        if not match or not any(match.groups()) or not size:
            file.close()
            return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
        start, end = match.groups()
        start, end = (int(start), min(int(end), size - 1) if end else size - 1) if start else (max(0, size - int(end)), size - 1)
        if start >= size or end < start:
            file.close()
            return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
        file.seek(start)

        def chunks():
            remaining = end - start + 1
            try:
                while remaining:
                    chunk = file.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
            finally:
                file.close()

        response = StreamingHttpResponse(chunks(), status=206, content_type=mime)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Content-Length'] = end - start + 1
        response._resource_closers.append(file.close)
    else:
        response = FileResponse(file, content_type=mime)
        response['Content-Length'] = size
    response['Content-Disposition'] = content_disposition_header(bool(request.query_params.get('download')) or mime in ('text/html', 'image/svg+xml'), path.name)
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = cache_control
    if etag: response['ETag'] = etag
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "sandbox; default-src 'none'"
    return response
