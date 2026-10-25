import hashlib
import os
from django.core.exceptions import ValidationError as ModelValidationError
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.social.application.post_commands import Conflict
from apps.social.application.post_media import CHUNK_BYTES, make_upload, validate_file, queue_media
from apps.social.infrastructure.models.post_lifecycle import PostUpload
from apps.social.infrastructure.models.social import PostMedia
from apps.social.infrastructure.post_storage import post_private_storage as storage


def representation(upload):
    return {'id': str(upload.pk), 'media_id': str(upload.pk), 'offset': upload.offset,
            'size': upload.expected_size, 'state': upload.state, 'chunk_size': CHUNK_BYTES,
            'expires_at': upload.expires_at.isoformat(), 'error': upload.error}


class PostUploadViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = '[0-9a-f-]+'

    def get_upload(self, pk, lock=False):
        queryset = PostUpload.objects.select_for_update() if lock else PostUpload.objects.all()
        try:
            upload = queryset.get(pk=pk, owner=self.request.user)
        except (PostUpload.DoesNotExist, ValueError, ModelValidationError):
            raise NotFound('Загрузка не найдена')
        if upload.expires_at <= timezone.now() and not PostMedia.objects.filter(upload=upload).exists():
            raise NotFound('Срок загрузки истёк')
        return upload

    def create(self, request):
        upload = make_upload(request.user, str(request.data.get('filename') or ''), request.data.get('size'))
        return Response(representation(upload), status=201)

    def retrieve(self, request, pk=None):
        return Response(representation(self.get_upload(pk)))

    @transaction.atomic
    def partial_update(self, request, pk=None):
        upload = self.get_upload(pk, lock=True)
        try:
            offset = int(request.headers.get('Upload-Offset', -1))
        except (ValueError, TypeError):
            raise ValidationError({'offset': 'Некорректное смещение'})
        if upload.state != 'uploading' or offset != upload.offset:
            return Response({**representation(upload), 'detail': 'Смещение загрузки изменилось'}, status=409)
        chunk = request._request.read(CHUNK_BYTES + 1)
        if not chunk or len(chunk) > CHUNK_BYTES or upload.offset + len(chunk) > upload.expected_size:
            raise ValidationError({'file': 'Некорректный размер части файла'})
        checksum = request.headers.get('Upload-Checksum')
        if not checksum or hashlib.sha256(chunk).hexdigest() != checksum:
            raise ValidationError({'file': 'Контрольная сумма части файла не совпадает'})
        with Path(storage.path(upload.original_path)).open('r+b') as target:
            target.truncate(upload.offset)
            target.seek(upload.offset)
            target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        upload.offset += len(chunk)
        upload.save(update_fields=['offset'])
        return Response(representation(upload))

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def complete(self, request, pk=None):
        upload = self.get_upload(pk, lock=True)
        if upload.state == 'uploading':
            validate_file(upload)
        return Response(representation(upload))

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def retry(self, request, pk=None):
        from apps.users.infrastructure.models.users import User
        from apps.social.infrastructure.models.social import Post
        User.objects.select_for_update().only('id').get(pk=request.user.pk)
        upload = self.get_upload(pk)
        media = PostMedia.objects.filter(upload=upload, post__author=request.user, post__is_deleted=False).first()
        if not media:
            raise NotFound('Вложение не найдено')
        post = Post.objects.select_for_update().get(pk=media.post_id)
        if post.is_deleted: raise NotFound('Пост удалён')
        media = PostMedia.objects.select_for_update().get(pk=media.pk)
        if media.processing_state == 'failed':
            PostMedia.objects.filter(pk=media.pk, processing_state='failed').update(processing_state='queued', processing_error='')
            PostUpload.objects.filter(pk=upload.pk).update(state='queued', error='')
            if post.status == 'failed': Post.objects.filter(pk=post.pk).update(status='processing')
            queue_media(media.pk)
        return Response({'queued': True})
