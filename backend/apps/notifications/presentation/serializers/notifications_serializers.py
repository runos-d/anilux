from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from apps.notifications.infrastructure.models.notifications import Complaint, Notification, Reminder, NotificationSetting
from apps.anime.presentation.serializers.anime_serializers import AnimeSerializer


class ComplaintSerializer(serializers.ModelSerializer):
    complainant_username = serializers.CharField(source='complainant.username', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complainant', 'complainant_username', 'complaint_type', 'reason',
            'description', 'status', 'assigned_to', 'resolution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'complainant', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    is_flashing = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'content', 'icon', 'link',
            'is_read', 'is_important', 'is_deleted', 'is_flashing',
            'created_at', 'read_at', 'expires_at',
            'enable_push', 'enable_sound',
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'is_deleted']

    def get_is_flashing(self, obj):
        if obj.is_read:
            return False
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        return obj.created_at > one_minute_ago


class ReminderSerializer(serializers.ModelSerializer):
    anime_detail = serializers.SerializerMethodField()

    def get_anime_detail(self, obj):
        if obj.franchise:
            return {
                'id': obj.franchise.pk,
                'slug': obj.franchise.slug,
                'title_ru': obj.franchise.name,
                'title_en': obj.franchise.name,
                'poster_url': obj.franchise.poster_image_url,
                'target_type': 'franchise',
            }
        if obj.anime:
            return AnimeSerializer(obj.anime, context=self.context).data
        data = obj.calendar_release.data if obj.calendar_release else {}
        return {'id': None, 'title_ru': data.get('russian') or data.get('name') or 'Аниме',
                'poster_url': data.get('poster_url') or (data.get('image') or {}).get('original')}

    class Meta:
        model = Reminder
        fields = [
            'id', 'anime', 'franchise', 'anime_detail', 'reminder_time', 'repeat_weekly',
            'comment', 'enable_sound', 'enable_push', 'is_active', 'is_triggered', 'created_at',
            'calendar_release', 'follow_schedule', 'delay_notified_at', 'available_notified_at',
            'repeat_interval_days', 'end_date', 'timezone_name'
        ]
        read_only_fields = ['id', 'is_triggered', 'created_at', 'calendar_release',
                            'delay_notified_at', 'available_notified_at']

    def validate(self, attrs):
        from apps.notifications.application.reminder_validation import validate_timezone
        if 'timezone_name' in attrs:
            validate_timezone(attrs['timezone_name'])
        if 'repeat_interval_days' in attrs and attrs['repeat_interval_days'] is not None and not 1 <= attrs['repeat_interval_days'] <= 365:
            raise serializers.ValidationError({'repeat_interval_days': 'Укажите интервал от 1 до 365 дней'})
        if self.instance and self.instance.calendar_release_id:
            anime = attrs.get('anime')
            if anime and anime.shikimori_id != self.instance.calendar_release.shikimori_id:
                raise serializers.ValidationError({'anime': 'Аниме не соответствует релизу'})
            if attrs.get('repeat_weekly') or attrs.get('repeat_interval_days'):
                raise serializers.ValidationError('Напоминание о конкретной серии не повторяется; используйте ручное напоминание')
            if 'reminder_time' in attrs:
                attrs['follow_schedule'] = False
        elif attrs.get('follow_schedule'):
            raise serializers.ValidationError('Автоматический перенос доступен только для релиза календаря')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReminderCreateSerializer(serializers.Serializer):
    anime_id = serializers.IntegerField(required=False)
    franchise_id = serializers.IntegerField(required=False, min_value=1)
    calendar_release_id = serializers.IntegerField(required=False, min_value=1)
    follow_schedule = serializers.BooleanField(required=False)
    reminder_time = serializers.DateTimeField(required=False)
    repeat_weekly = serializers.BooleanField(default=False)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
    enable_sound = serializers.BooleanField(default=True, required=False)
    enable_push = serializers.BooleanField(default=True, required=False)
    repeat_interval_days = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=365)
    end_date = serializers.DateTimeField(required=False, allow_null=True)
    timezone_name = serializers.CharField(default='UTC', max_length=80)

    def validate_timezone_name(self, value):
        from apps.notifications.application.reminder_validation import validate_timezone
        return validate_timezone(value)

    def validate(self, attrs):
        targets = [attrs.get('calendar_release_id'), attrs.get('anime_id'), attrs.get('franchise_id')]
        if sum(bool(value) for value in targets) != 1:
            raise serializers.ValidationError('Укажите один объект напоминания: релиз, аниме или франшизу')
        if not attrs.get('calendar_release_id') and not attrs.get('reminder_time'):
            raise serializers.ValidationError({'reminder_time': 'Укажите время напоминания'})
        if attrs.get('calendar_release_id') and (attrs.get('repeat_weekly') or attrs.get('repeat_interval_days')):
            raise serializers.ValidationError('Напоминание о конкретной серии не повторяется')
        if attrs.get('end_date') and attrs.get('reminder_time') and attrs['end_date'] < attrs['reminder_time']:
            raise serializers.ValidationError({'end_date': 'Конец повторений раньше времени напоминания'})
        return attrs


class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = [
            'push_enabled', 'email_enabled', 'sound_enabled',
            'type_settings',
            'dnd_enabled', 'dnd_start', 'dnd_end',
            'auto_clean_read_days', 'auto_clean_unread_days',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
