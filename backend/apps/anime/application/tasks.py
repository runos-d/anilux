import logging
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from celery import shared_task
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from apps.anime.infrastructure.models.anime import ClipTask

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300, countdown=60)
def rebuild_franchises_task(self, shikimori_ids: List[int], dry_run: bool = False):
    from django.core.cache import cache
    from apps.anime.application.anime_service import anime_service
    from apps.anime.infrastructure.models.anime import Anime, Franchise
    import re

    def _find_common_prefix(strings: List[str]) -> str:
        if not strings:
            return ""
        if len(strings) == 1:
            return strings[0]
        min_len = min(len(s) for s in strings)
        prefix_len = 0
        for i in range(min_len):
            char = strings[0][i]
            if all(s[i] == char for s in strings):
                prefix_len += 1
            else:
                break
        return strings[0][:prefix_len]

    def _resolve_franchise_name(nodes: List[Dict[str, Any]], franchise_slug: Optional[str]) -> str:
        if not nodes:
            return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
        
        first_node = nodes[0]
        first_id = first_node.get("id")
        if first_id is None:
            return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
        try:
            first_id = int(first_id)
        except (TypeError, ValueError):
            return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
        
        try:
            from apps.anime.infrastructure.api.shikimori import shikimori_api
            franchise_data = shikimori_api.get_franchise(first_id)
            if not franchise_data:
                return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
            
            franchise_nodes = franchise_data.get("nodes", []) or []
            if not franchise_nodes:
                return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
            
            max_weight = max((node.get("weight", 0) for node in franchise_nodes), default=0)
            if max_weight == 0:
                return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
            
            max_weight_names = [
                node.get("name", "").strip()
                for node in franchise_nodes
                if node.get("weight", 0) == max_weight and node.get("name")
            ]
            if not max_weight_names:
                return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
            
            common_prefix = _find_common_prefix(max_weight_names)
            if not common_prefix:
                return franchise_slug.replace("_", " ").strip() if franchise_slug else ""
            
            cleaned = re.sub(r'[\s:,\--]+$', '', common_prefix).strip()
            return cleaned or (franchise_slug.replace("_", " ").strip() if franchise_slug else "")
        except Exception:
            return franchise_slug.replace("_", " ").strip() if franchise_slug else ""

    task_id = self.request.id
    cache.set(f"import_task:{task_id}", {
        "running": True,
        "finished": False,
        "success": None,
        "stopped": False,
        "log": "",
        "command": "rebuild_franchises",
        "started": datetime.now().isoformat(),
    }, timeout=3600)

    log_lines = []
    processed = 0
    created_franchises = 0
    updated_anime = 0
    errors = 0

    try:
        for shikimori_id in shikimori_ids:
            try:
                graph = anime_service.build_franchise_graph(shikimori_id)
                nodes = graph.get("nodes", []) or []
                if not nodes:
                    continue

                franchise_slug = nodes[0].get("url", "").strip("/").split("/")[-1] if nodes[0].get("url") else ""
                franchise_name = _resolve_franchise_name(nodes, franchise_slug)
                current_node = nodes[0] if nodes else None

                if not dry_run:
                    franchise, _ = Franchise.objects.update_or_create(
                        name=franchise_name,
                        defaults={
                            "slug": franchise_slug,
                        },
                    )

                node_ids = []
                for n in nodes:
                    raw_id = n.get("id")
                    if raw_id is None:
                        continue
                    try:
                        node_ids.append(int(raw_id))
                    except (TypeError, ValueError):
                        continue

                anime_map = {}
                if node_ids:
                    for anime in Anime.objects.filter(shikimori_id__in=node_ids):
                        anime_map[anime.shikimori_id] = anime

                for node in nodes:
                    raw_id = node.get("id")
                    if raw_id is None:
                        continue
                    try:
                        node_id = int(raw_id)
                    except (TypeError, ValueError):
                        continue
                    weight = node.get("weight", 0)
                    node_name = node.get("name") or ""
                    node_year = node.get("year")
                    node_kind = node.get("kind") or "tv"
                    node_poster = node.get("image_url") or ""
                    node_url = node.get("url") or ""

                    if not dry_run and node_id in anime_map:
                        anime = anime_map[node_id]
                        anime.franchise_order = weight
                        anime.save(update_fields=["franchise_order", "updated_at"])
                        updated_anime += 1

                if not dry_run:
                    created_franchises += 1

                processed += 1
                if processed % 20 == 0:
                    log_lines.append(f"Обработано {processed}/{len(shikimori_ids)}")
            except Exception as e:
                errors += 1
                log_lines.append(f"Ошибка для {shikimori_id}: {e}")
                continue

        result_summary = {
            "processed": processed,
            "created_franchises": created_franchises,
            "updated_anime": updated_anime,
            "errors": errors,
        }
        log_lines.append(f"Готово: {result_summary}")
        cache.set(f"import_task:{task_id}", {
            "running": False,
            "finished": True,
            "success": True,
            "stopped": False,
            "log": "\n".join(log_lines),
            "command": "rebuild_franchises",
            "started": cache.get(f"import_task:{task_id}", {}).get("started"),
            "stats": result_summary,
        }, timeout=3600)
        return {"status": "success", "result": result_summary}
    except Exception as e:
        log_lines.append(f"Критическая ошибка: {str(e)}")
        cache.set(f"import_task:{task_id}", {
            "running": False,
            "finished": True,
            "success": False,
            "stopped": False,
            "log": "\n".join(log_lines),
            "command": "rebuild_franchises",
            "started": cache.get(f"import_task:{task_id}", {}).get("started"),
        }, timeout=3600)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=300, countdown=60)
def run_kodik_import_task(self, mode: str = "update", limit: int | None = None, download_posters: bool = False):
    from django.core.cache import cache
    from apps.anime.application.anime_service import anime_service
    from apps.anime.infrastructure.models.anime import Anime
    from apps.anime.infrastructure.api.external_anime_api import external_anime_api

    task_id = self.request.id
    cache.set(f"import_task:{task_id}", {
        "running": True,
        "finished": False,
        "success": None,
        "stopped": False,
        "log": "",
        "command": "import_from_kodik",
        "started": datetime.now().isoformat(),
    }, timeout=3600)

    log_lines = []
    try:
        update_existing = mode == "full"

        params = {
            'limit': 100,
            'types': 'anime,anime-serial',
            'with_material_data': True,
            'with_seasons': True,
            'with_episodes': True,
        }

        def fetch_page(page_params):
            try:
                data = external_anime_api.list_materials(**page_params)
                return data
            except Exception as e:
                return {'error': str(e), 'results': []}

        first_page = fetch_page(params)
        all_items = first_page.get('results', [])
        next_page = first_page.get('next_page')
        
        while next_page and (not limit or len(all_items) < limit):
            page_data = fetch_page({"next_page": next_page})
            all_items.extend(page_data.get('results', []))
            next_page = page_data.get('next_page')
            import time
            time.sleep(0.5)
        
        if limit:
            all_items = all_items[:limit]
        
        log_lines.append(f"Загружено {len(all_items)} аниме из Kodik, начинаем параллельный импорт...")
        cache.set(f"import_task:{task_id}", {
            "running": True,
            "finished": False,
            "success": None,
            "stopped": False,
            "log": "\n".join(log_lines),
            "command": "import_from_kodik",
            "started": cache.get(f"import_task:{task_id}", {}).get("started"),
        }, timeout=3600)

        existing_shikimori = set()
        if not update_existing:
            existing_shikimori = set(Anime.objects.filter(
                shikimori_id__isnull=False
            ).values_list('shikimori_id', flat=True))

        stats = {
            'imported': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        shared_lock = threading.Lock()

        def process_item(item):
            shikimori_id = item.get('shikimori_id')
            if not shikimori_id:
                with shared_lock:
                    stats['skipped'] += 1
                return None
            
            with shared_lock:
                if not update_existing and shikimori_id in existing_shikimori:
                    stats['skipped'] += 1
                    return None
            
            try:
                anime, created = anime_service.import_anime(
                    item, 
                    update_existing=update_existing, 
                    download_posters=download_posters,
                )
                with shared_lock:
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                    stats['imported'] += 1
                    existing_shikimori.add(shikimori_id)
                return {'shikimori_id': shikimori_id, 'created': created}
            except Exception as e:
                with shared_lock:
                    stats['errors'] += 1
                logger.warning(f"Ошибка импорта {shikimori_id}: {e}")
                return None

        max_workers = 10
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_item, item) for item in all_items]
            
            for i, future in enumerate(as_completed(futures)):
                if i % 10 == 0:
                    with shared_lock:
                        progress_stats = dict(stats)
                    cache.set(f"import_task:{task_id}", {
                        "running": True,
                        "finished": False,
                        "success": None,
                        "stopped": False,
                        "log": f"Обработано {i+1}/{len(all_items)}... Создано: {progress_stats['created']}, Обновлено: {progress_stats['updated']}",
                        "command": "import_from_kodik",
                        "started": cache.get(f"import_task:{task_id}", {}).get("started"),
                        "stats": progress_stats,
                    }, timeout=3600)
                future.result()

        result = {
            'imported': stats['imported'],
            'created': stats['created'],
            'updated': stats['updated'],
            'skipped': stats['skipped'],
            'errors': stats['errors'],
        }
        
        log_lines.append(f"Импорт завершен: {result}")
        cache.set(f"import_task:{task_id}", {
            "running": False,
            "finished": True,
            "success": True,
            "stopped": False,
            "log": "\n".join(log_lines),
            "command": "import_from_kodik",
            "started": cache.get(f"import_task:{task_id}", {}).get("started"),
            "stats": result,
        }, timeout=3600)
        return {"status": "success", "result": result}
        
    except Exception as e:
        log_lines.append(f"Ошибка: {str(e)}")
        import traceback
        log_lines.append(traceback.format_exc())
        cache.set(f"import_task:{task_id}", {
            "running": False,
            "finished": True,
            "success": False,
            "stopped": False,
            "log": "\n".join(log_lines),
            "command": "import_from_kodik",
            "started": cache.get(f"import_task:{task_id}", {}).get("started"),
        }, timeout=3600)
        raise


@shared_task(bind=True, max_retries=2, default_retry_delay=300, countdown=60)
def process_clip_task(self, task_id: str):
    from apps.anime.infrastructure.models.anime import ClipTask
    from apps.anime.application.video_processor import (
        take_screenshot,
        download_clip,
        screenshot_to_base64,
        get_clip_duration,
        check_requirements,
    )
    from apps.anime.application.db_video_extractor import get_anime_video_links_by_id, get_best_quality_url
    from django.core.files.base import ContentFile
    from django.utils import timezone
    import os
    import tempfile
    from pathlib import Path
    
    try:
        task = ClipTask.objects.get(id=task_id)
    except ClipTask.DoesNotExist:
        logger.info(f"[TASK] ClipTask {task_id} not found")
        return
    yt_dlp_ok, ffmpeg_ok = True, True
    
    task.status = 'processing'
    task.started_at = timezone.now()
    task.save()
    
    if not task.video_url:
        video_info = get_anime_video_links_by_id(task.anime_id)
        if video_info and video_info.get(task.quality):
            task.video_url = video_info[task.quality]
            task.save()
    
    if not task.video_url:
        task.status = 'failed'
        task.error_message = "Не удалось получить ссылку на видео"
        task.completed_at = timezone.now()
        task.save()
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        if task.task_type == 'screenshot':
            result = _process_screenshot(task, tmpdir_path)
        else:
            result = _process_video_clip(task, tmpdir_path)
        
        if result['success']:
            task.status = 'ready'
            task.result_file = result['file']
            task.thumbnail = result.get('thumbnail')
            task.duration = result.get('duration')
            task.file_size = result.get('file_size')
            task.error_message = ''
            logger.info(f"[TASK] Task {task_id} completed successfully")
        else:
            task.status = 'failed'
            task.error_message = result.get('error', 'Неизвестная ошибка')
            logger.info(f"[TASK] Task {task_id} failed: {task.error_message}")
        
        task.completed_at = timezone.now()
        task.save()


def _process_screenshot(task: 'ClipTask', tmpdir: Path) -> dict:
    from apps.anime.application.video_processor import take_screenshot, screenshot_to_base64
    from django.core.files.base import ContentFile
    
    try:
        timestamp_str = f"{task.timestamp:.3f}".replace('.', '_')
        filename = f"screenshot_{task.anime.id}_{timestamp_str}.jpg"
        filepath = tmpdir / filename
        
        logger.info(f"[SCREENSHOT] Creating screenshot at {task.timestamp}s")
        
        result_path = take_screenshot(
            video_url=task.video_url,
            timestamp=task.timestamp,
            output_path=str(filepath),
            quality=2
        )
        
        if not result_path:
            return {'success': False, 'error': 'Не удалось создать скриншот'}
        
        with open(result_path, 'rb') as f:
            content = ContentFile(f.read())
            task.result_file.save(filename, content, save=False)
        
        file_size = os.path.getsize(result_path)
        
        thumb_filename = f"thumb_{filename.replace('.jpg', '.png')}"
        with open(result_path, 'rb') as f:
            thumb_content = ContentFile(f.read())
            task.thumbnail.save(thumb_filename, thumb_content, save=False)
        
        return {
            'success': True,
            'file': task.result_file,
            'thumbnail': task.thumbnail,
            'file_size': file_size,
        }
    
    except Exception as e:
        logger.info(f"[SCREENSHOT] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e)}


def _process_video_clip(task: 'ClipTask', tmpdir: Path) -> dict:
    from apps.anime.application.video_processor import download_clip, take_screenshot, get_clip_duration
    from django.core.files.base import ContentFile
    import subprocess
    import shutil
    
    FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    
    try:
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
            return f"{minutes:02d}:{secs:05.2f}"
        
        start_str = format_time(task.start_time)
        end_str = format_time(task.end_time)
        
        safe_label = task.label.replace(' ', '_').replace('/', '_') if task.label else 'clip'
        is_mp3 = task.format == 'mp3'
        ext = 'mp3' if is_mp3 else 'mp4'
        filename = f"{safe_label}_{task.anime.id}_ep{task.episode}_{start_str.replace(':', '-')}-{end_str.replace(':', '-')}.{ext}"
        filepath = tmpdir / filename
        
        logger.info(f"[CLIP] Downloading clip from {start_str} to {end_str} (format={task.format})")
        
        if is_mp3:
            cmd = [
                "/usr/bin/ffmpeg",
                '-y',
                '-ss', start_str,
                '-i', task.video_url,
                '-to', end_str,
                '-vn',
                '-c:a', 'libmp3lame',
                '-q:a', '2',
                '-threads', '2',
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.info(f"[CLIP] ffmpeg mp3 error: {result.stderr}")
                return {'success': False, 'error': f"Ошибка ffmpeg: {result.stderr[:200]}"}
            result_path = str(filepath)
        else:
            result_path = download_clip(
                video_url=task.video_url,
                start_time=start_str,
                end_time=end_str,
                output_path=str(filepath),
                use_keyframes=True
            )
        
        if not result_path or not os.path.exists(result_path) or os.path.getsize(result_path) == 0:
            return {'success': False, 'error': 'Не удалось скачать фрагмент'}
        
        with open(result_path, 'rb') as f:
            content = ContentFile(f.read())
            task.result_file.save(filename, content, save=False)
        
        file_size = os.path.getsize(result_path)
        duration = get_clip_duration(result_path) if not is_mp3 else (task.end_time - task.start_time)
        
        if not is_mp3:
            thumbnail_path = tmpdir / f"thumb_{filename.replace('.mp4', '.jpg')}"
            
            thumb_result = take_screenshot(
                video_url=result_path,
                timestamp=0,
                output_path=str(thumbnail_path),
                quality=5
            )
            
            if thumb_result:
                with open(thumb_result, 'rb') as f:
                    thumb_content = ContentFile(f.read())
                    thumb_filename = f"thumb_{filename.replace('.mp4', '.jpg')}"
                    task.thumbnail.save(thumb_filename, thumb_content, save=False)
        
        return {
            'success': True,
            'file': task.result_file,
            'thumbnail': task.thumbnail,
            'duration': duration,
            'file_size': file_size,
        }
    
    except Exception as e:
        logger.info(f"[CLIP] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=300, countdown=60)
def sync_anime_metadata_task(self, anime_id: int):
    from apps.anime.infrastructure.models.anime import Anime

    try:
        anime = Anime.objects.get(pk=anime_id)
    except Anime.DoesNotExist:
        return {"status": "skipped", "reason": "anime_not_found"}

    return {
        "status": "completed",
        "anime_id": anime_id,
    }

