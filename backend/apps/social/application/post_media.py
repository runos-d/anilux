import hashlib
import json
import logging
import mimetypes
import subprocess
import queue
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.social.infrastructure.models.post_lifecycle import PostUpload
from apps.social.infrastructure.models.social import Post, PostMedia
from apps.social.infrastructure.post_storage import post_private_storage as storage

logger = logging.getLogger(__name__)
MAX_BYTES = 250 * 1024 * 1024
CHUNK_BYTES = 4 * 1024 * 1024
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.mkv', '.avi', '.m4v'}


def validate_declaration(filename, size):
    try:
        size = int(size)
    except (ValueError, TypeError):
        raise ValidationError({'size': 'Укажите размер файла'})
    if not 0 < size <= MAX_BYTES:
        raise ValidationError({'size': 'Общий объём вложений поста -максимум 250 МБ'})
    if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        raise ValidationError({'filename': 'Неподдерживаемый формат изображения или видео'})
    return size


def make_upload(owner, filename, size):
    size = validate_declaration(filename, size)
    upload = PostUpload.objects.create(owner=owner, filename=Path(filename).name[:255], expected_size=size,
                                       expires_at=timezone.now() + timedelta(hours=24))
    upload.original_path = f'uploads/{upload.pk}/original{Path(filename).suffix.lower()}'
    upload.save(update_fields=['original_path'])
    path = Path(storage.path(upload.original_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=False)
    return upload


def validate_file(upload):
    path = Path(storage.path(upload.original_path))
    if path.stat().st_size != upload.expected_size or upload.offset != upload.expected_size:
        raise ValidationError({'file': 'Файл загружен не полностью'})
    with path.open('rb') as source:
        header = source.read(32)
        source.seek(0)
        checksum = hashlib.file_digest(source, 'sha256').hexdigest()
    extension = Path(upload.filename).suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        from PIL import Image
        try:
            with Image.open(path) as picture:
                if picture.width * picture.height > 100_000_000:
                    raise ValueError('Слишком большое разрешение изображения')
                picture.verify()
        except Exception as error:
            raise ValidationError({'file': 'Повреждённое или неподдерживаемое изображение'}) from error
        kind = 'image'
    else:
        valid = (b'ftyp' in header or header.startswith(b'\x1aE\xdf\xa3') or
                 header.startswith(b'RIFF') and header[8:12] == b'AVI ')
        if not valid:
            raise ValidationError({'file': 'Содержимое файла не соответствует видео'})
        kind = 'video'
    upload.checksum = checksum
    upload.state = 'uploaded'
    upload.metadata = {'media_type': kind}
    upload.save(update_fields=['checksum', 'state', 'metadata', 'offset'])
    return upload


def stage_file(owner, file):
    upload = make_upload(owner, file.name, file.size)
    with Path(storage.path(upload.original_path)).open('wb') as output:
        for chunk in file.chunks():
            output.write(chunk)
    upload.offset = file.size
    return validate_file(upload)


def queue_media(media_id):
    from django.core.cache import cache
    key = f'post-media:queued:{media_id}'
    try:
        if not cache.add(key, 1, 7200): return
        kind = PostMedia.objects.filter(pk=media_id).values_list('media_type', flat=True).first()
        process_post_media.apply_async(args=[media_id], queue='celery' if kind == 'image' else 'post_media')
    except Exception:
        try: cache.delete(key)
        except Exception: pass
        logger.warning('Media job remains queued for periodic recovery', exc_info=True)


def link_uploads(post, uploads, active=True):
    media = []
    for index, upload in enumerate(uploads):
        record = PostMedia.objects.create(post=post, upload=upload, file=upload.original_path,
            media_type=upload.metadata['media_type'], file_size=upload.expected_size,
            mime_type=mimetypes.guess_type(upload.filename)[0] or 'application/octet-stream',
            order=index, processing_state='queued', is_active=active)
        upload.state = 'queued'
        upload.save(update_fields=['state'])
        transaction.on_commit(lambda pk=record.pk: queue_media(pk), robust=True)
        media.append(record)
    return media


def probe_video(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_streams', '-show_format', '-of', 'json', str(path)],
                            capture_output=True, check=True, timeout=30)
    data = json.loads(result.stdout)
    video = next((stream for stream in data['streams'] if stream['codec_type'] == 'video'), None)
    if not video or not video.get('width') or not video.get('height'):
        raise ValueError('В файле отсутствует видеодорожка')
    return data, video


def run_video_command(arguments, duration, progress, start, span, timeout=1800):
    events = queue.Queue()
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(arguments + ['-progress', 'pipe:1', '-nostats'], stdout=subprocess.PIPE,
                                   stderr=errors, text=True)
        def read():
            for line in process.stdout:
                events.put(line)
            events.put(None)
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        deadline = time.monotonic() + timeout
        try:
            while True:
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(arguments, timeout)
                try:
                    line = events.get(timeout=.5)
                except queue.Empty:
                    continue
                if line is None: break
                if line.startswith('out_time_us=') and duration > 0:
                    try: fraction = min(1, max(0, int(line.split('=', 1)[1]) / 1_000_000 / duration))
                    except ValueError: continue
                    progress(round(start + span * fraction))
            process.wait(timeout=max(.1, deadline-time.monotonic()))
            if process.returncode:
                errors.seek(0)
                raise subprocess.CalledProcessError(process.returncode, arguments, stderr=errors.read(4000))
            progress(start + span)
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
            reader.join(timeout=2)
            process.stdout.close()


def convert_video(path, directory, progress=lambda value: None):
    data, video = probe_video(path)
    variants = {}
    duration = float(data.get('format', {}).get('duration') or 0)
    audio = [stream for stream in data['streams'] if stream['codec_type'] == 'audio']
    compatible = video.get('codec_name') == 'h264' and video.get('pix_fmt') in ('yuv420p', 'yuvj420p') and all(stream.get('codec_name') == 'aac' for stream in audio)
    common = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-protocol_whitelist', 'file,pipe',
              '-threads', '2', '-i', str(path), '-map', '0:v:0', '-map', '0:a:0?', '-movflags', '+faststart']
    preview = directory / '720p.mp4'
    preview_arguments = ['-vf', 'scale=w=min(1280\\,iw):h=min(720\\,ih):force_original_aspect_ratio=decrease:force_divisible_by=2',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '2500k', '-bufsize', '5000k',
        '-pix_fmt', 'yuv420p', '-threads', '2', '-c:a', 'aac', '-b:a', '128k']
    small = video['width'] <= 1280 and video['height'] <= 720
    bitrate = float(data.get('format', {}).get('bit_rate') or 0)
    if compatible and small and 0 < bitrate <= 2_500_000:
        preview_arguments = ['-c', 'copy']
    run_video_command(common + preview_arguments + [str(preview)], duration, progress, 0, 70)
    original = directory / 'original.mp4'
    if compatible:
        arguments = ['-c', 'copy']
    else:
        arguments = ['-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                     '-threads', '2', '-c:a', 'aac', '-b:a', '160k']
    if preview_arguments == ['-c', 'copy']:
        original = preview
        progress(95)
    else:
        run_video_command(common + arguments + [str(original)], duration, progress, 70, 25)
    poster = directory / 'poster.webp'
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-threads', '2', '-i', str(preview),
                    '-frames:v', '1', '-vf', 'scale=480:-2', str(poster)], capture_output=True, check=True, timeout=60)
    progress(99)
    for quality, file in (('720p', preview), ('original', original), ('poster', poster)):
        variants[quality] = file.relative_to(Path(storage.location)).as_posix()
    return variants, video['width'], video['height'], duration


def finish_post(post):
    from apps.social.application.post_commands import record_event
    if post.is_deleted:
        return
    media = list(post.media_files.filter(pk__in=post.pending_edit.get('new_media_ids', []))) if post.pending_edit else list(post.media_files.filter(is_active=True))
    if not media or any(item.processing_state != 'ready' for item in media):
        return
    if post.pending_edit:
        pending = post.pending_edit
        keep = pending.get('retain_media_ids', [])
        from apps.social.application.post_file_gc import schedule_cleanup
        removed = list(post.media_files.filter(is_active=True).exclude(pk__in=keep))
        for item in removed: schedule_cleanup(item)
        post.media_files.filter(pk__in=[item.pk for item in removed]).update(is_active=False)
        post.media_files.filter(pk__in=[item.pk for item in media]).update(is_active=True)
        from types import SimpleNamespace
        from apps.social.presentation.serializers.social_serializers import PostUpdateSerializer
        from apps.social.application.post_commands import validate_shared
        request = SimpleNamespace(user=post.author, data=pending['payload'], FILES={})
        from apps.social.application.post_counts import remember_related
        remember_related(post)
        serializer = PostUpdateSerializer(post, data=pending['payload'], partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        validate_shared(serializer.validated_data, post.author)
        serializer.save(edited_at=timezone.now())
        post.pending_edit = {}
        post.edited_at = timezone.now()
        post.save()
        record_event(post, 'post_updated')
    elif post.status in ('processing', 'failed'):
        post.status = 'published'
        post.published_at = timezone.now()
        post.save(update_fields=['status', 'published_at'])
        record_event(post, 'new_post')


@shared_task(bind=True, name='social.process_post_media', queue='post_media', max_retries=3,
             time_limit=3700, soft_time_limit=3650, acks_late=True, reject_on_worker_lost=True)
def process_post_media(self, media_id):
    from django.core.cache import cache
    try: cache.delete(f'post-media:queued:{media_id}')
    except Exception: pass
    with transaction.atomic():
        media = PostMedia.objects.select_for_update().select_related('post', 'upload').filter(pk=media_id).first()
        if not media or media.processing_state == 'ready' or media.post.is_deleted:
            return
        redelivered = (self.request.delivery_info or {}).get('redelivered', False)
        if media.processing_state == 'processing' and media.processing_started_at and not redelivered:
            if media.processing_started_at > timezone.now()-timedelta(seconds=3700): return
        media.processing_state = 'processing'
        media.processing_progress = 0
        media.processing_started_at = timezone.now()
        media.processing_error = ''
        media.save(update_fields=['processing_state', 'processing_progress', 'processing_error', 'processing_started_at'])
        PostUpload.objects.filter(pk=media.upload_id).update(state='processing')
    try:
        source = Path(storage.path(media.upload.original_path))
        directory = Path(storage.location) / 'processed' / str(media.pk)
        directory.mkdir(parents=True, exist_ok=True)
        last_progress, last_write = -1, 0
        def update_progress(value):
            nonlocal last_progress, last_write
            value = max(0, min(99, value))
            now = time.monotonic()
            if value <= last_progress or now-last_write < 1 and value < 99: return
            PostMedia.objects.filter(pk=media_id, processing_state='processing',
                processing_started_at=media.processing_started_at).update(processing_progress=value)
            last_progress, last_write = value, now
        if media.media_type == 'video':
            variants, width, height, duration = convert_video(source, directory, update_progress)
            display_path = variants['720p']
            poster_path = variants['poster']
        else:
            from PIL import Image, ImageOps
            with Image.open(source) as picture:
                animated = getattr(picture, 'is_animated', False)
                picture = ImageOps.exif_transpose(picture)
                width, height = picture.size
                picture.thumbnail((2560, 2560))
                if picture.mode not in ('RGB', 'RGBA'):
                    picture = picture.convert('RGBA' if 'transparency' in picture.info else 'RGB')
                output = directory / 'image.webp'
                picture.save(output, 'WEBP', quality=90)
            poster_path = output.relative_to(Path(storage.location)).as_posix()
            display_path = media.upload.original_path if animated else poster_path
            variants, duration = {}, 0
        with transaction.atomic():
            from apps.users.infrastructure.models.users import User
            User.objects.select_for_update().only('id').get(pk=media.post.author_id)
            post = Post.objects.select_for_update().get(pk=media.post_id)
            item = PostMedia.objects.select_for_update().get(pk=media.pk)
            item.file.name, item.poster.name = display_path, poster_path
            item.thumbnail.name = poster_path
            item.variants = variants
            item.width, item.height, item.duration = width, height, int(duration)
            item.processing_state = 'ready'
            item.processing_progress = 100
            item.processing_error = ''
            item.save()
            PostUpload.objects.filter(pk=item.upload_id).update(state='ready')
            finish_post(post)
    except Exception as error:
        with transaction.atomic():
            PostMedia.objects.filter(pk=media_id).update(processing_state='failed', processing_error=str(error)[:500])
            PostUpload.objects.filter(pk=media.upload_id).update(state='failed', error=str(error)[:500])
            Post.objects.filter(pk=media.post_id, status='processing').update(status='failed')
        if self.request.retries < self.max_retries:
            raise self.retry(exc=error, countdown=30 * (2 ** self.request.retries))
        raise


@shared_task(name='social.recover_post_media')
def recover_post_media():
    stale = timezone.now() - timedelta(hours=2)
    for pk in PostMedia.objects.filter(processing_state='queued', post__is_deleted=False).values_list('pk', flat=True)[:50]:
        queue_media(pk)
    for pk in PostMedia.objects.filter(processing_state='processing', processing_started_at__lt=stale).values_list('pk', flat=True)[:10]:
        queue_media(pk)
