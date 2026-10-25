from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status, mixins
from django.utils import timezone
from datetime import timedelta

from apps.notifications.infrastructure.models.notifications import Complaint, Notification, Reminder, NotificationSetting, EpisodeSubscription
from apps.notifications.presentation.serializers.notifications_serializers import (
    ComplaintSerializer, NotificationSerializer,
    ReminderSerializer, ReminderCreateSerializer,
    NotificationSettingSerializer,
)
from apps.notifications.presentation.serializers.episode_sub_serializer import EpisodeSubscriptionSerializer
from apps.notifications.application.services import NotificationService
from apps.anime.infrastructure.models.anime import Anime, Franchise


class ComplaintViewSet(ModelViewSet):
    queryset = Complaint.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        return self.queryset.filter(complainant=self.request.user)

    def perform_create(self, serializer):
        complaint = serializer.save(complainant=self.request.user)
        try:
            from apps.users.application.signals import notify_admin
            user_display = self.request.user.nickname or self.request.user.username
            notify_admin(
                title=f'⚠️ Новая жалоба от @{user_display}',
                content=(
                    f'Тип: {complaint.get_complaint_type_display()}, '
                    f'Причина: {complaint.get_reason_display()}. '
                    f'Описание: {complaint.description[:200] if complaint.description else "-"}'
                ),
                notif_type='warning',
                link='/admin/complaints',
            )
        except Exception as e:
            pass


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = self.queryset.filter(
            user=self.request.user,
            is_deleted=False,
        ).order_by('-created_at')

        ntype = self.request.query_params.get('type')
        if ntype:
            qs = qs.filter(type=ntype)

        unread = self.request.query_params.get('unread')
        if unread in ('1', 'true'):
            qs = qs.filter(is_read=False)

        important = self.request.query_params.get('important')
        if important in ('1', 'true'):
            qs = qs.filter(is_important=True)

        flashing = self.request.query_params.get('flashing')
        if flashing in ('1', 'true'):
            one_minute_ago = timezone.now() - timedelta(minutes=1)
            qs = qs.filter(is_read=False, created_at__gte=one_minute_ago)

        return qs


    def destroy(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_deleted = True
        notification.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        cnt = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False,
        ).count()

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        flashing_cnt = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False,
            created_at__gte=one_minute_ago
        ).count()

        return Response({
            'count': cnt,
            'flashing_count': flashing_cnt
        })

    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        try:
            qs = Notification.objects.filter(
                user=request.user,
                is_deleted=False,
            ).order_by('-created_at')[:8]
            serializer = self.get_serializer(qs, many=True)
            unread_count = Notification.objects.filter(
                user=request.user, is_read=False, is_deleted=False
            ).count()

            one_minute_ago = timezone.now() - timedelta(minutes=1)
            flashing_count = Notification.objects.filter(
                user=request.user,
                is_read=False,
                is_deleted=False,
                created_at__gte=one_minute_ago
            ).count()

            return Response({
                'results': serializer.data,
                'unread_count': unread_count,
                'flashing_count': flashing_count,
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in notifications/recent: {e}", exc_info=True)
            return Response({
                'results': [],
                'unread_count': 0,
                'flashing_count': 0,
                'error': 'Failed to load notifications'
            }, status=500)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response({
            'status': 'ok',
            'id': notification.id,
            'is_read': True,
        })

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({'status': 'ok', 'count': count})

    @action(detail=True, methods=['post'], url_path='toggle_important')
    def toggle_important(self, request, pk=None):
        notification = self.get_object()
        notification.is_important = not notification.is_important
        notification.save(update_fields=['is_important'])
        return Response({
            'status': 'ok',
            'id': notification.id,
            'is_important': notification.is_important,
        })

    @action(detail=False, methods=['delete'], url_path='clean')
    def clean(self, request):
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True,
            is_important=False,
        ).update(is_deleted=True), None
        return Response({'status': 'ok'})

    @action(detail=False, methods=['delete'], url_path='delete_all')
    def delete_all(self, request):
        Notification.objects.filter(
            user=request.user,
            is_important=False,
        ).update(is_deleted=True)
        return Response({'status': 'ok'})


class ReminderViewSet(ModelViewSet):
    queryset = Reminder.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ReminderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = ReminderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from django.db import transaction
        from apps.anime.models import CalendarRelease
        values = dict(serializer.validated_data)
        release_id = values.pop('calendar_release_id', None)
        anime_id = values.pop('anime_id', None)
        franchise_id = values.pop('franchise_id', None)
        release = CalendarRelease.objects.filter(pk=release_id).first() if release_id else None
        if release_id and not release:
            return Response({'calendar_release_id': 'Релиз не найден'}, status=404)
        if release and not release.episode and release.data.get('kind') != 'movie':
            return Response({'calendar_release_id': 'Номер серии пока неизвестен'}, status=400)
        anime = (Anime.objects.filter(shikimori_id=release.shikimori_id).first() if release
                 else Anime.objects.filter(pk=anime_id).first() if anime_id else None)
        franchise = Franchise.objects.filter(pk=franchise_id).first() if franchise_id else None
        if franchise_id and not franchise:
            return Response({'franchise_id': 'Франшиза не найдена'}, status=404)
        if not release and not anime and not franchise:
            return Response({'anime_id': 'Аниме не найдено'}, status=404)
        if anime_id and release and (not anime or anime.pk != anime_id):
            return Response({'anime_id': 'Аниме не соответствует релизу'}, status=400)
        if anime and not anime.is_available:
            return Response({'anime_id': 'Аниме недоступно'}, status=403)
        if franchise and not franchise.entries.filter(is_available=True).exists():
            return Response({'franchise_id': 'Франшиза недоступна'}, status=403)
        if release:
            follow = values.pop('follow_schedule', 'reminder_time' not in values)
            if not follow and 'reminder_time' not in values:
                return Response({'reminder_time': 'Укажите время ручного напоминания'}, status=400)
            if follow:
                values['reminder_time'] = release.aired_at
            values['follow_schedule'] = follow
        elif values.pop('follow_schedule', False):
            return Response({'follow_schedule': 'Укажите релиз календаря'}, status=400)
        with transaction.atomic():
            from apps.users.models import User
            User.objects.select_for_update().get(pk=request.user.pk)
            identity = {'user': request.user, 'calendar_release': release}
            if not release:
                identity.update(reminder_time=values.pop('reminder_time'))
                if franchise:
                    identity['franchise'] = franchise
                else:
                    identity['anime'] = anime
            reminder, created = Reminder.objects.get_or_create(
                **identity, defaults={**values, 'anime': anime, 'franchise': franchise})
            if release and not created and not reminder.is_active and not reminder.available_notified_at:
                for key, value in values.items():
                    setattr(reminder, key, value)
                reminder.is_active, reminder.is_triggered = True, False
                reminder.save()
        return Response(ReminderSerializer(reminder).data, status=201 if created else 200)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_active = False
        reminder.save(update_fields=['is_active'])
        return Response({'status': 'deactivated'})

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_triggered = False
        if not reminder.calendar_release_id and not (reminder.repeat_weekly or reminder.repeat_interval_days):
            reminder.is_active = False
        reminder.save(update_fields=['is_triggered', 'is_active'])
        return Response({'status': 'acknowledged'})

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        now = timezone.now()
        reminders = self.get_queryset().filter(
            is_active=True,
            reminder_time__gte=now - timedelta(minutes=1),
            reminder_time__lte=now + timedelta(minutes=60),
        ).order_by('reminder_time')[:20]
        return Response(ReminderSerializer(reminders, many=True).data)

    @action(detail=False, methods=['post'])
    def check_and_trigger(self, request):
        from apps.notifications.application.episode_events import process_reminders
        from apps.notifications.application.episode_verification import queue_due_verifications
        queue_due_verifications(request.user)
        triggered_ids = process_reminders(request.user)

        return Response({
            'triggered_count': len(triggered_ids),
            'triggered_ids': triggered_ids
        })


class NotificationSettingViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSettingSerializer

    def get_object(self):
        try:
            obj, _ = NotificationSetting.objects.get_or_create(user=self.request.user)
            return obj
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting notification settings: {e}")
            return NotificationSetting(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error retrieving notification settings: {e}")
            return Response({
                'push_enabled': True,
                'email_enabled': True,
                'sound_enabled': True,
                'dnd_enabled': False,
                'dnd_start': None,
                'dnd_end': None,
                'auto_clean_read_days': 30,
                'auto_clean_unread_days': 90,
                'type_settings': {},
                'updated_at': None
            })

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating notification settings: {e}")
            return Response({'error': str(e)}, status=400)

class EpisodeSubscriptionViewSet(ModelViewSet):
    serializer_class = EpisodeSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    queryset = EpisodeSubscription.objects.all()
    def get_queryset(self):
        rows = EpisodeSubscription.objects.filter(user=self.request.user).select_related('anime').order_by('-updated_at')
        anime_id = self.request.query_params.get('anime_id')
        return rows.filter(anime_id=anime_id) if anime_id and anime_id.isdigit() else rows
    def create(self, request, *args, **kwargs):
        from django.db import transaction
        from apps.anime.models import KodikAvailability
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        anime = values.pop('anime')
        active = values.get('is_active', True)
        with transaction.atomic():
            from apps.users.models import User
            User.objects.select_for_update().get(pk=request.user.pk)
            obj, created = EpisodeSubscription.objects.get_or_create(user=request.user, anime=anime)
            rebaseline = created or (active and not obj.is_active)
            available = KodikAvailability.objects.filter(anime=anime).first()
            for key, value in values.items():
                setattr(obj, key, value)
            obj.is_active = active
            obj.manually_disabled = not active
            if rebaseline:
                obj.baseline_initialized = available is not None or anime.status == 'announced'
                obj.notified_episodes = available.episodes if available else []
                obj.last_notified_episode = available.last_episode if available else 0
            obj.save()
        return Response(self.get_serializer(obj).data, status=201 if created else 200)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.manually_disabled = True
        instance.save(update_fields=['is_active', 'manually_disabled'])

    def perform_update(self, serializer):
        active = serializer.validated_data.get('is_active', serializer.instance.is_active)
        values = {'manually_disabled': not active}
        if active and not serializer.instance.is_active:
            from apps.anime.models import KodikAvailability
            available = KodikAvailability.objects.filter(anime=serializer.instance.anime).first()
            values.update(notified_episodes=available.episodes if available else [],
                baseline_initialized=available is not None or serializer.instance.anime.status == 'announced',
                last_notified_episode=available.last_episode if available else 0)
        serializer.save(**values)

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = not obj.is_active
        obj.manually_disabled = not obj.is_active
        if obj.is_active:
            from apps.anime.models import KodikAvailability
            available = KodikAvailability.objects.filter(anime=obj.anime).first()
            obj.notified_episodes = available.episodes if available else []
            obj.baseline_initialized = available is not None or obj.anime.status == 'announced'
            obj.last_notified_episode = available.last_episode if available else 0
        obj.save()
        return Response({'is_active': obj.is_active})

    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, pk=None):
        obj = self.get_object()
        obj.is_paused = not obj.is_paused
        if obj.is_paused:
            from django.utils import timezone
            from datetime import timedelta
            obj.paused_until = timezone.now() + timedelta(days=7)
        else:
            obj.paused_until = None
        obj.save(update_fields=['is_paused','paused_until'])
        return Response({'is_paused': obj.is_paused})
