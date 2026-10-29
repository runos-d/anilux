from datetime import timedelta
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import time
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from apps.anime.models import BackgroundJob


def claim(pk):
    if not BackgroundJob.objects.filter(pk=pk, status='pending').update(status='processing', updated_at=timezone.now()):
        return None
    return BackgroundJob.objects.get(pk=pk)


@shared_task(name='anime.prepare_download', time_limit=240, soft_time_limit=220, acks_late=True)
def prepare_download(pk):
    job = claim(pk)
    if not job:
        return
    from apps.anime.presentation.views.prepared_downloads import download_root, job_file
    from .anime_service import anime_service
    root = download_root()
    root.mkdir(parents=True, exist_ok=True)
    part = root / (job.pk.hex + '.part.' + job.payload['format'])
    maximum = getattr(settings, 'DOWNLOAD_MAX_BYTES', 512 * 1024 * 1024)
    try:
        if shutil.disk_usage(root).free < maximum * 2:
            raise RuntimeError('Недостаточно свободного места. Повторите позже.')
        data = job.payload
        source = anime_service.get_anime_m3u8(anime_id=data['anime_id'], episode=data['episode'],
            season=data['season'], translation_id=data.get('translation_id'), quality=data['quality'],
            user_ip=data.get('client_ip', '1.1.1.1'))
        if not source:
            raise RuntimeError('Видео сейчас недоступно')
        duration = 14400 if data['full'] else data['end'] - data['start']
        cmd = [shutil.which('ffmpeg') or '/usr/bin/ffmpeg', '-nostdin', '-y', '-hide_banner', '-loglevel', 'error',
               '-rw_timeout', '10000000', '-ss', str(data['start']), '-i', source, '-t', str(duration), '-fs', str(maximum)]
        cmd += ['-vn', '-c:a', 'libmp3lame', '-b:a', '192k'] if data['format'] == 'mp3' else ['-c', 'copy', '-movflags', '+faststart']
        with tempfile.TemporaryFile() as errors:
            result = subprocess.run(cmd + [str(part)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=errors, timeout=180)
        if result.returncode or not part.is_file() or not part.stat().st_size:
            raise RuntimeError('Не удалось подготовить видео')
        size = part.stat().st_size
        if size >= maximum:
            raise RuntimeError('Видео превышает допустимый размер')
        os.replace(part, job_file(job))
        BackgroundJob.objects.filter(pk=pk).update(status='ready', result={'bytes': size}, error='', updated_at=timezone.now())
    except Exception as error:
        BackgroundJob.objects.filter(pk=pk).update(status='failed', error=str(error)[:500], updated_at=timezone.now())
    finally:
        part.unlink(missing_ok=True)


@shared_task(name='anime.import_requested_catalog', time_limit=900, soft_time_limit=870, acks_late=True)
def import_requested_catalog(pk):
    job = claim(pk)
    if not job:
        return
    from apps.anime.presentation.views.anime_views import KodikUserAddView
    from apps.anime.models import Anime
    view = KodikUserAddView()
    ids, results, imported = job.payload['ids'], [], []
    deadline = time.monotonic() + 840
    try:
        existing_rows = {row.shikimori_id: row for row in Anime.objects.filter(shikimori_id__in=ids).only('pk', 'shikimori_id', 'slug', 'title_ru', 'title_en')}
        existing = set(existing_rows)
        for sid in ids:
            if sid in existing:
                row = existing_rows[sid]
                results.append({'shikimori_id': sid, 'slug': row.slug, 'title': row.title_ru or row.title_en, 'ok': True, 'existing': True})
                continue
            try:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Превышено время подготовки. Повторите оставшиеся тайтлы.')
                item = view._import_one(sid, job.payload.get('download_posters', False))
                imported.append(item['anime_id'])
                results.append({'shikimori_id': sid, 'slug': item['slug'], 'title': item['title'], 'ok': True})
            except Exception as error:
                results.append({'shikimori_id': sid, 'ok': False, 'message': str(error)[:200]})
            BackgroundJob.objects.filter(pk=pk).update(result={'results': results, 'current': len(results), 'total': len(ids)}, updated_at=timezone.now())
        if imported:
            view._build_franchise_for_ids(ids, imported)
        BackgroundJob.objects.filter(pk=pk).update(status='ready', result={'results': results, 'existing': sorted(existing),
            'current': len(results), 'total': len(ids), 'message': f'Обработано: {len(results)}'}, updated_at=timezone.now())
    except Exception as error:
        BackgroundJob.objects.filter(pk=pk).update(status='failed', error=str(error)[:500], updated_at=timezone.now())


@shared_task(name='anime.cleanup_background_work', time_limit=30)
def cleanup_background_work():
    from apps.anime.presentation.views.prepared_downloads import download_root, job_file
    now = timezone.now()
    for job in BackgroundJob.objects.filter(kind='download', status='ready', updated_at__lt=now - timedelta(hours=1))[:100]:
        job_file(job).unlink(missing_ok=True)
        BackgroundJob.objects.filter(pk=job.pk).update(status='failed', error='Срок хранения файла истёк', updated_at=now - timedelta(minutes=2))
    BackgroundJob.objects.filter(status__in=['pending', 'processing'], updated_at__lt=now - timedelta(minutes=20)).update(
        status='failed', error='Подготовка прервана. Повторите запрос.', updated_at=now - timedelta(minutes=2))
    BackgroundJob.objects.filter(status__in=['failed', 'ready'], updated_at__lt=now - timedelta(days=1)).delete()
    root = download_root()
    if root.exists():
        for path in root.iterdir():
            if path.is_file() and path.stat().st_mtime < time.time() - 7200:
                path.unlink(missing_ok=True)
