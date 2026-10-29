import base64
import os
import shutil
import subprocess
import tempfile
import logging

import requests
from django.core.cache import cache
from django.http import StreamingHttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.anime.infrastructure.models.anime import Anime
from apps.anime.presentation.serializers.anime_serializers import ClipTaskCreateSerializer
from apps.anime.application.anime_service import anime_service
from apps.anime.application.direct_video import DirectVideoService
from apps.anime.application.tasks import process_clip_task

logger = logging.getLogger(__name__)

FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"


class KodikInstantScreenshotView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, pk):
        import traceback
        try:
            Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.data.get("episode", 1))
        season = int(request.data.get("season", 1))
        timestamp = float(request.data.get("timestamp", 0))
        translation_id = request.data.get("translation_id")
        quality = request.data.get("quality", "720")
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        if timestamp < 0:
            return Response({"error": "timestamp не может быть отрицательным"}, status=400)

        cache_key = f"screenshot:{pk}:{episode}:{season}:{translation_id or 'any'}:{timestamp:.1f}"
        cached = cache.get(cache_key)
        if cached:
            return Response({"image_base64": cached, "cached": True})

        try:
            m3u8_url = anime_service.get_anime_m3u8(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality,
            )
        except Exception as e:
            logger.debug(f"[SCREENSHOT] anime_service.get_anime_m3u8 error: {e}")
            logger.debug(traceback.format_exc())
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)

        if not m3u8_url:
            return Response({"error": "Не удалось получить видео URL из Kodik"}, status=404)

        try:
            hours = int(timestamp // 3600)
            minutes = int((timestamp % 3600) // 60)
            seconds = int(timestamp % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name

            video_url = m3u8_url
            is_mp4 = False
            if m3u8_url and m3u8_url.endswith(".m3u8"):
                mp4_candidate = m3u8_url.replace(".m3u8", ".mp4")
                try:
                    resp = requests.head(mp4_candidate, timeout=3, allow_redirects=True)
                    if resp.status_code == 200:
                        video_url = mp4_candidate
                        is_mp4 = True
                        logger.debug(f"[SCREENSHOT] Using direct MP4 for fast seek: {video_url[:80]}...")
                except Exception:
                    pass

            cmd = [
                FFMPEG_PATH,
                "-y",
                "-ss", time_str,
            ]

            if not is_mp4:
                cmd.extend([
                    "-analyzeduration", "3M",
                    "-probesize", "3M",
                    "-fflags", "+discardcorrupt+nobuffer",
                ])

            cmd.extend([
                "-i", video_url,
                "-frames:v", "1",
                "-q:v", "2",
                "-vf", "scale=1280:-1",
                "-an",
                "-f", "image2",
                tmp_path,
            ])

            logger.debug(f"[SCREENSHOT] ffmpeg cmd: {' '.join(cmd[:8])}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.debug(f"[SCREENSHOT] ffmpeg error: {result.stderr}")
                return Response(
                    {"error": f"Ошибка ffmpeg: {result.stderr[:200]}"},
                    status=500,
                )

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return Response({"error": "Скриншот не создан"}, status=500)

            with open(tmp_path, "rb") as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
            base64_url = f"data:image/jpeg;base64,{base64_data}"

            cache.set(cache_key, base64_url, 86400)

            os.unlink(tmp_path)

            return Response({
                "image_base64": base64_url,
                "cached": False,
                "timestamp": timestamp,
            })

        except subprocess.TimeoutExpired:
            return Response({"error": "Таймаут создания скриншота"}, status=504)
        except Exception as e:
            logger.debug(f"[SCREENSHOT] Internal error: {e}")
            logger.debug(traceback.format_exc())
            return Response({"error": f"Внутренняя ошибка: {str(e)}"}, status=500)


class KodikClipCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, pk):
        import traceback
        try:
            Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.data.get("episode", 1))
        season = int(request.data.get("season", 1))
        start = float(request.data.get("start", 0))
        end = float(request.data.get("end", 0))
        label = request.data.get("label", "clip")
        translation_id = request.data.get("translation_id")
        quality = request.data.get("quality", "720")

        fmt = request.data.get("format", "mp4")
        if fmt not in ("mp4", "mp3"):
            fmt = "mp4"

        is_full_episode = isinstance(label, str) and label.startswith('Episode_')
        if not is_full_episode and end <= start:
            return Response({"error": "end должен быть больше start"}, status=400)

        if not is_full_episode and end - start > 300:
            if not request.user.is_authenticated:
                return Response({"error": "Требуется авторизация"}, status=401)

            from apps.users.infrastructure.models.users import UserProfileSettings
            try:
                profile = UserProfileSettings.objects.get(user=request.user)
                if not profile.is_premium:
                    return Response({"error": "Скачивание фрагментов доступно только для премиум пользователей"}, status=403)
            except UserProfileSettings.DoesNotExist:
                return Response({"error": "Скачивание фрагментов доступно только для премиум пользователей"}, status=403)

        if is_full_episode and end - start > 3600:
            return Response({"error": "Максимальная длительность серии 1 час"}, status=400)

        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")
        try:
            m3u8_url = anime_service.get_anime_m3u8(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality,
            )
        except Exception as e:
            logger.debug(f"[CLIP] anime_service.get_anime_m3u8 error: {e}")
            logger.debug(traceback.format_exc())
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)

        serializer = ClipTaskCreateSerializer(data={
            "anime": pk,
            "task_type": "clip",
            "episode": episode,
            "season": season,
            "start_time": start,
            "end_time": end,
            "label": label,
            "quality": quality,
            "format": fmt,
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            task = serializer.save(
                user=request.user if request.user.is_authenticated else None,
                video_url=m3u8_url or "",
            )
        except Exception as e:
            logger.debug(f"[CLIP] serializer.save error: {e}")
            logger.debug(traceback.format_exc())
            return Response({"error": f"Ошибка сохранения задачи: {str(e)}"}, status=500)

        try:
            process_clip_task.delay(str(task.id))
        except Exception as e:
            logger.debug(f"[CLIP] Celery error: {e}")

        return Response({
            "task_id": str(task.id),
            "status": "pending",
            "message": "Фрагмент создаётся",
        }, status=202)


from .prepared_downloads import PreparedDownloadView

class KodikStreamView(PreparedDownloadView):
    pass


class DirectVideoUrlView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        import asyncio
        import traceback

        try:
            Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.GET.get("episode", 1))
        season = int(request.GET.get("season", 1))
        translation_id = request.GET.get("translation_id")
        quality = request.GET.get("quality", "720")

        try:
            result = asyncio.run(DirectVideoService.get_anime_episode_url(
                anime_id=pk,
                episode=episode,
                season=season,
                translation_id=translation_id,
                quality=quality
            ))

            if not result:
                return Response({"error": "Не удалось получить видео"}, status=404)

            return Response({
                "url": result["url"],
                "quality": result["quality"],
                "source": result["source"],
                "is_m3u8": result.get("is_m3u8", False),
            })

        except Exception as e:
            logger.debug(f"[DIRECT_URL] Error: {e}")
            logger.debug(traceback.format_exc())
            return Response({"error": f"Ошибка получения видео: {str(e)}"}, status=500)
