from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from apps.anime.infrastructure.models.anime import ClipTask, Anime
from apps.anime.presentation.serializers.anime_serializers import ClipTaskSerializer, ClipTaskCreateSerializer
from apps.anime.application.tasks import process_clip_task


class ClipTaskViewSet(viewsets.ModelViewSet):
    queryset = ClipTask.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClipTaskCreateSerializer
        return ClipTaskSerializer
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ClipTask.objects.filter(
                Q(user=self.request.user) | Q(user__isnull=True)
            ).order_by('-created_at')
        return ClipTask.objects.filter(user__isnull=True).order_by('-created_at')
    
    def perform_create(self, serializer):
        anime = serializer.validated_data.get('anime')
        
        if not anime:
            raise serializers.ValidationError({'anime': 'Аниме не указано'})
        
        instance = serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
        
        process_clip_task.delay(str(instance.id))
        
        return instance
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        task = self.get_object()
        
        if task.status != 'failed':
            return Response(
                {'error': 'Можно повторить только неудачные задачи'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'pending'
        task.error_message = ''
        task.started_at = None
        task.completed_at = None
        task.save()
        
        process_clip_task.delay(str(task.id))
        
        return Response({'status': 'pending', 'message': 'Задача перезапущена'})


class ScreenshotView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def post(self, request):
        from apps.anime.presentation.serializers.anime_serializers import ClipTaskCreateSerializer
        
        anime_id = request.data.get('anime_id')
        timestamp = request.data.get('timestamp')
        episode = request.data.get('episode', 1)
        
        if not anime_id or not timestamp:
            return Response(
                {'error': 'Требуется anime_id и timestamp'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {'error': 'Аниме не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClipTaskCreateSerializer(data={
            'anime': anime_id,
            'task_type': 'screenshot',
            'episode': episode,
            'timestamp': float(timestamp),
            'quality': '720',
        })
        
        if serializer.is_valid():
            task = serializer.save(user=request.user if request.user.is_authenticated else None)
            process_clip_task.delay(str(task.id))
            
            return Response({
                'task_id': str(task.id),
                'status': 'pending',
                'message': 'Скриншот создаётся'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



