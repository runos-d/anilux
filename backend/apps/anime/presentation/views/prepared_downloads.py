import asyncio
from pathlib import Path
import re
import uuid
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.anime.models import Anime, BackgroundJob
from apps.anime.application.background_work import enqueue


def download_root():
    return Path(getattr(settings, 'DOWNLOAD_ROOT', Path(settings.MEDIA_ROOT).parent / 'private_downloads'))


def job_file(job):
    return download_root() / (job.pk.hex + '.' + job.payload['format'])


class DownloadInput(serializers.Serializer):
    episode = serializers.IntegerField(min_value=1, max_value=100000, default=1)
    season = serializers.IntegerField(min_value=0, max_value=10000, default=1)
    start = serializers.FloatField(min_value=0, max_value=14400, default=0)
    end = serializers.FloatField(min_value=0, max_value=100000, default=99999)
    translation_id = serializers.IntegerField(min_value=1, required=False)
    quality = serializers.ChoiceField(choices=['360', '480', '720', '1080'], default='720')
    format = serializers.ChoiceField(choices=['mp4', 'mp3', 'audio'], default='mp4')


class DownloadContentNegotiation(DefaultContentNegotiation):
    def filter_renderers(self, renderers, format):
        # These values select a media file, not a DRF response renderer.
        if format in ('mp4', 'mp3', 'audio'):
            return renderers
        return super().filter_renderers(renderers, format)


class PreparedDownloadView(APIView):
    content_negotiation_class = DownloadContentNegotiation
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        get_object_or_404(Anime.objects.only('pk'), pk=pk, is_available=True)
        token = request.query_params.get('job_id')
        if token:
            try:
                token = uuid.UUID(token)
            except ValueError:
                raise NotFound()
            job = get_object_or_404(BackgroundJob, pk=token, kind='download')
            if job.payload['anime_id'] != pk:
                raise NotFound()
        else:
            values = DownloadInput(data=request.query_params)
            values.is_valid(raise_exception=True)
            payload = dict(values.validated_data)
            import math
            if not all(math.isfinite(payload[key]) for key in ['start', 'end']) or payload['end'] <= payload['start']:
                return Response({'error': 'Некорректный диапазон'}, status=400)
            payload['full'] = payload['end'] >= 99999
            if not payload['full'] and payload['end'] - payload['start'] > 14400:
                return Response({'error': 'Слишком длинный диапазон'}, status=400)
            payload.update(anime_id=pk, client_ip=request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR') or '1.1.1.1')
            payload['format'] = 'mp3' if payload['format'] == 'audio' else payload['format']
            from apps.anime.application.background_tasks import prepare_download
            job = enqueue('download', payload, prepare_download)
        if job.status == 'failed':
            return Response({'error': job.error}, status=422)
        if job.status != 'ready':
            return Response({'job_id': str(job.pk), 'status': job.status, 'retry_after': 2}, status=202, headers={'Retry-After': '2', 'Cache-Control': 'private, no-store'})
        path = job_file(job)
        if not path.is_file():
            BackgroundJob.objects.filter(pk=job.pk).update(status='failed', error='Файл истёк. Запросите подготовку заново.')
            return Response({'error': 'Файл истёк. Запросите подготовку заново.'}, status=410)
        size = path.stat().st_size
        content_type = 'audio/mpeg' if job.payload['format'] == 'mp3' else 'video/mp4'
        if request.META.get('HTTP_X_MEDIA_ACCEL') == '1':
            response = HttpResponse(content_type=content_type)
            response['X-Accel-Redirect'] = '/_prepared_downloads/' + path.name
        else:
            start, stop = 0, size - 1
            value = request.META.get('HTTP_RANGE')
            if value:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
                if not match or not any(match.groups()):
                    return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
                first, last = match.groups()
                start, stop = (int(first), min(int(last) if last else stop, stop)) if first else (max(0, size - int(last)), stop)
                if start > stop or start >= size:
                    return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
            async def chunks():
                handle = await asyncio.to_thread(path.open, 'rb')
                try:
                    await asyncio.to_thread(handle.seek, start)
                    remaining = stop - start + 1
                    while remaining:
                        chunk = await asyncio.to_thread(handle.read, min(65536, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
                finally:
                    await asyncio.to_thread(handle.close)
            response = StreamingHttpResponse(chunks(), status=206 if value else 200, content_type=content_type)
            response['Content-Length'] = str(stop - start + 1)
            if value:
                response['Content-Range'] = f'bytes {start}-{stop}/{size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Disposition'] = f'attachment; filename="Episode_{job.payload["episode"]}.{job.payload["format"]}"'
        response['Cache-Control'] = 'private, max-age=300'
        return response
