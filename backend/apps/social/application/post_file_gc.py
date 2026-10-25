import hashlib
import json
import uuid
import shutil
from datetime import timedelta
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from apps.social.infrastructure.models.post_lifecycle import PostFileCleanup, PostUpload, PostFeedSnapshot
from apps.social.infrastructure.models.social import PostMedia, Post
from apps.social.infrastructure.post_storage import post_private_storage as storage


def schedule_cleanup(media):
    PostFileCleanup.objects.get_or_create(media=media, defaults={'not_before': timezone.now()+timedelta(hours=24)})


def referenced(name, media):
    other = PostMedia.objects.exclude(pk=media.pk).filter(
        Q(is_active=True, post__is_deleted=False) | Q(processing_state__in=['queued', 'processing']))
    if other.filter(Q(file=name) | Q(poster=name) | Q(thumbnail=name) | Q(upload__original_path=name) |
                    Q(variants__720p=name) | Q(variants__original=name)).exists(): return True
    if Post.objects.filter(is_deleted=False).filter(Q(image_file=name) | Q(video_file=name)).exists(): return True
    return PostUpload.objects.exclude(pk=media.upload_id).filter(original_path=name, postmedia__isnull=True).exists()


def remove_verified(name):
    path = Path(storage.path(name)).resolve()
    roots = [Path(storage.location).resolve(), Path(settings.MEDIA_ROOT).resolve()]
    if not any(path.is_relative_to(root) for root in roots): raise ValueError('Файл за пределами хранилища')
    if not path.is_file(): return {'name': name, 'missing': True}
    with path.open('rb') as source: checksum = hashlib.file_digest(source, 'sha256').hexdigest()
    size = path.stat().st_size
    destination = Path(storage.location) / '.trash' / str(uuid.uuid4()) / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'name': name, 'bytes': size, 'sha256': checksum,
                'source_root': 'private' if path.is_relative_to(roots[0]) else 'legacy',
                'quarantine': destination.relative_to(Path(storage.location)).as_posix()}
    (destination.parent / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    shutil.move(str(path), str(destination))
    return manifest


@shared_task(name='social.gc_post_files')
def gc_post_files():
    for job_id in PostFileCleanup.objects.filter(state='queued', not_before__lte=timezone.now()).values_list('pk', flat=True)[:100]:
        try:
            with transaction.atomic():
                job = PostFileCleanup.objects.select_for_update().get(pk=job_id)
                media = PostMedia.objects.select_for_update().select_related('post', 'upload').get(pk=job.media_id)
                if not media.post.is_deleted and (media.is_active or media.pk in media.post.pending_edit.get('new_media_ids', [])):
                    job.state = 'cancelled'; job.save(update_fields=['state']); continue
                if media.processing_state == 'processing' and (not media.processing_started_at or media.processing_started_at > timezone.now()-timedelta(hours=2)): continue
                names = {field.name for field in (media.file, media.thumbnail, media.poster) if field}
                names.update(media.variants.values())
                if media.upload: names.add(media.upload.original_path)
                job.manifest = [remove_verified(name) for name in sorted(names) if name and not referenced(name, media)]
                job.state, job.completed_at, job.error = 'complete', timezone.now(), ''
                job.save(update_fields=['manifest', 'state', 'completed_at', 'error'])
        except Exception as error:
            PostFileCleanup.objects.filter(pk=job_id).update(error=str(error)[:500])
    for upload_id in PostUpload.objects.filter(expires_at__lt=timezone.now(), postmedia__isnull=True).values_list('pk', flat=True)[:100]:
        with transaction.atomic():
            upload = PostUpload.objects.select_for_update().filter(pk=upload_id).first()
            if upload and not PostMedia.objects.filter(upload=upload).exists():
                if upload.original_path: remove_verified(upload.original_path)
                upload.delete()
    root = Path(storage.location) / 'uploads'
    if root.exists():
        cutoff = timezone.now().timestamp() - 86400
        for directory in list(root.iterdir())[:1000]:
            if not directory.is_dir() or directory.stat().st_mtime >= cutoff: continue
            try: upload_id = uuid.UUID(directory.name)
            except ValueError: continue
            if PostUpload.objects.filter(pk=upload_id).exists(): continue
            for path in directory.iterdir():
                if not path.is_file(): continue
                name = path.relative_to(Path(storage.location)).as_posix()
                if not PostMedia.objects.filter(Q(file=name) | Q(upload__original_path=name)).exists(): remove_verified(name)
    PostFeedSnapshot.objects.filter(expires_at__lt=timezone.now()).delete()
