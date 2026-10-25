from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from django.utils import timezone
from django.db import models

from apps.social.infrastructure.models.social_support import SupportTicket, SupportMessage
from apps.users.infrastructure.models.users import User


class SupportTicketSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'user', 'user_id', 'username', 'user_avatar',
            'subject', 'status', 'anime_id',
            'created_at', 'updated_at', 'closed_at',
            'last_message', 'unread_count', 'is_admin'
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at', 'updated_at']
    
    def get_user_avatar(self, obj):
        request = self.context.get('request')
        if obj.user.avatar:
            return request.build_absolute_uri(obj.user.avatar.url) if hasattr(obj.user.avatar, 'url') else None
        return None
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'text': last_msg.text[:100],
                'sender_id': last_msg.sender.id,
                'sender_username': last_msg.sender.username,
                'created_at': last_msg.created_at.isoformat(),
                'is_read': last_msg.is_read
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        
        user = request.user
        if user.is_staff or user.is_superuser:
            return obj.messages.filter(is_read=False).exclude(sender=user).count()
        else:
            return obj.messages.filter(is_read=False).exclude(sender=user).count()
    
    def get_is_admin(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return request.user.is_staff or request.user.is_superuser


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.SerializerMethodField()
    sender_is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportMessage
        fields = [
            'id', 'ticket_id', 'sender_id', 'sender_username', 
            'sender_avatar', 'sender_is_admin',
            'text', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at']
    
    def get_sender_avatar(self, obj):
        request = self.context.get('request')
        if obj.sender.avatar:
            return request.build_absolute_uri(obj.sender.avatar.url) if hasattr(obj.sender.avatar, 'url') else None
        return None
    
    def get_sender_is_admin(self, obj):
        return obj.sender.is_staff or obj.sender.is_superuser


class SupportTicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SupportTicketSerializer
    
    def get_serializer_class(self):
        if self.action == 'messages':
            return SupportMessageSerializer
        return SupportTicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return SupportTicket.objects.all().select_related('user')
        else:
            return SupportTicket.objects.filter(user=user).select_related('user')
    
    def create(self, request, *args, **kwargs):
        subject = request.data.get('subject', 'Обращение в поддержку')
        text = request.data.get('text', '').strip()
        anime_id = request.data.get('anime_id')
        
        if not text:
            return Response({'error': 'Текст сообщения обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_ticket = SupportTicket.objects.filter(
            user=request.user,
            status__in=['pending', 'answered']
        ).first()
        
        if existing_ticket:
            message = SupportMessage.objects.create(
                ticket=existing_ticket,
                sender=request.user,
                text=text
            )
            existing_ticket.updated_at = timezone.now()
            existing_ticket.status = 'pending'
            existing_ticket.save()
            
            return Response({
                'ticket_id': existing_ticket.id,
                'message_id': message.id,
                'message': 'Сообщение добавлено в существующее обращение'
            }, status=status.HTTP_201_CREATED)
        
        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=subject,
            anime_id=anime_id if anime_id else None,
            status='pending'
        )
        
        message = SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            text=text
        )
        
        return Response({
            'ticket_id': ticket.id,
            'message_id': message.id,
            'message': 'Обращение создано'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        ticket = self.get_object()
        
        if request.method == 'GET':
            messages = ticket.messages.select_related('sender')

            messages.filter(is_read=False).exclude(sender=request.user).update(
                is_read=True,
                read_at=timezone.now(),
            )
            
            serializer = SupportMessageSerializer(messages, many=True, context={'request': request})
            return Response(serializer.data)
        
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'Текст сообщения обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        if ticket.status == 'closed' and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Обращение закрыто'}, status=status.HTTP_400_BAD_REQUEST)
        
        message = SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            text=text
        )
        
        ticket.updated_at = timezone.now()
        if request.user.is_staff or request.user.is_superuser:
            ticket.status = 'answered'
        else:
            ticket.status = 'pending'
        ticket.save()
        
        serializer = SupportMessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.user != request.user and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
        
        ticket.status = 'closed'
        ticket.closed_at = timezone.now()
        ticket.save()
        
        return Response({'message': 'Обращение закрыто'})
    
    @action(detail=False, methods=['get'])
    def my_active(self, request):
        ticket = SupportTicket.objects.filter(
            user=request.user,
            status__in=['pending', 'answered']
        ).select_related('user').first()
        
        if not ticket:
            return Response({'has_active': False})
        
        serializer = self.get_serializer(ticket, context={'request': request})
        data = serializer.data
        data['has_active'] = True
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def admin_list(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
        
        status_filter = request.query_params.get('status')
        queryset = SupportTicket.objects.all().select_related('user')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
        
        from django.db.models import Count
        
        stats = SupportTicket.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=models.Q(status='pending')),
            answered=Count('id', filter=models.Q(status='answered')),
            closed=Count('id', filter=models.Q(status='closed')),
        )
        
        return Response(stats)
