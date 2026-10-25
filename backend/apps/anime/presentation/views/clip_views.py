from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from celery.result import AsyncResult
from django.core.cache import cache

from ...application.clip_tasks import create_clip_async


class ClipCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        anime_id = request.data.get('anime_id')
        episode = int(request.data.get('episode', 1))
        season = int(request.data.get('season', 1))
        translation_id = request.data.get('translation_id')
        start_sec = int(request.data.get('start', 0))
        end_sec = int(request.data.get('end', 105))
        
        if not anime_id:
            return Response({"error": "anime_id required"}, status=400)
        
        cache_key = f"clip:{anime_id}:{episode}:{season}:{translation_id}:{start_sec}:{end_sec}"
        
        cached_url = cache.get(cache_key)
        if cached_url:
            return Response({
                "status": "ready",
                "url": cached_url,
                "task_id": None
            })
        
        user_ip = request.META.get('REMOTE_ADDR', '1.1.1.1')
        task = create_clip_async.delay(
            anime_id, episode, season, translation_id, start_sec, end_sec, user_ip
        )
        
        return Response({
            "status": "processing",
            "task_id": task.id,
            "message": "Клип нарезается. Используйте /api/anime/clip/status/ для проверки"
        }, status=202)


class ClipStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({"error": "task_id required"}, status=400)
        
        from celery.result import AsyncResult
        
        try:
            result = AsyncResult(task_id)
            
            if result.status == 'FAILURE':
                return Response({
                    "status": "failed",
                    "error": str(result.info)
                }, status=500)
            
            if result.status == 'SUCCESS':
                data = result.result
                return Response({
                    "status": "ready",
                    "url": data.get('url'),
                    "data": data
                })
            
            return Response({
                "status": "processing",
                "task_id": task_id
            })
            
        except Exception as e:
            return Response({
                "status": "failed", 
                "error": str(e)
            }, status=500)