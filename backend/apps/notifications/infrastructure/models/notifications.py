from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.users.infrastructure.models.users import User
from apps.anime.infrastructure.models.anime import Anime


class Complaint(models.Model):
    COMPLAINT_TYPES = [
        ('playlist', 'Плейлист'),
        ('playlist_item', 'Элемент плейлиста'),
        ('comment', 'Комментарий'),
        ('reactor_post', 'Reactor пост'),
        ('group', 'Группа'),
        ('dub', 'Озвучка'),
        ('user', 'Пользователь'),
    ]

    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('harassment', 'Харассмент'),
        ('inappropriate', 'Неподходящий контент'),
        ('copyright', 'Нарушение авторских прав'),
        ('misleading', 'Вводящая в заблуждение информация'),
        ('broken_link', 'Битая ссылка'),
        ('duplicate', 'Дубликат'),
        ('spoiler', 'Спойлер без предупреждения'),
        ('other', 'Другое'),
    ]

    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('investigating', 'Расследуется'),
        ('resolved', 'Решена'),
        ('dismissed', 'Отклонена'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    complainant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')

    complaint_type = models.CharField(max_length=20, choices=COMPLAINT_TYPES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    resolution = models.TextField(blank=True)
    action_taken = models.CharField(max_length=32, blank=True)
    source_report_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    target_snapshot = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Complaint by {self.complainant.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like', 'Лайк'),
        ('dislike', 'Дизлайк'),
        ('heart', 'Сердечко'),
        ('comment', 'Комментарий'),
        ('reply', 'Ответ на комментарий'),
        ('mention', 'Упоминание'),
        ('follow', 'Подписка'),
        ('repost', 'Репост'),
        ('message', 'Сообщение'),
        ('group_message', 'Сообщение в группе'),
        ('group_invite', 'Приглашение в группу'),
        ('achievement', 'Достижение'),
        ('contest', 'Новый конкурс'),
        ('contest_vote', 'Голосование'),
        ('contest_results', 'Результаты конкурса'),
        ('contest_win', 'Победа в конкурсе'),
        ('reminder_episode', 'Напоминание о серии'),
        ('episode_available', 'Новая серия доступна'),
        ('episode_delayed', 'Выход серии задерживается'),
        ('reminder_event', 'Напоминание о событии'),
        ('reminder_contest', 'Напоминание о конкурсе'),
        ('system', 'Системное'),
        ('warning', 'Предупреждение'),
        ('security', 'Безопасность'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    link = models.CharField(max_length=500, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    dedupe_key = models.CharField(max_length=255, blank=True, db_index=True, default='')
    enable_push = models.BooleanField(default=True)
    enable_sound = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'is_deleted', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    franchise = models.ForeignKey('anime.Franchise', on_delete=models.CASCADE,
                                  related_name='reminders', null=True, blank=True)
    calendar_release = models.ForeignKey('anime.CalendarRelease', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='reminders')
    follow_schedule = models.BooleanField(default=False)
    delay_notified_at = models.DateTimeField(null=True, blank=True)
    available_notified_at = models.DateTimeField(null=True, blank=True)

    reminder_time = models.DateTimeField(verbose_name='Время напоминания')
    repeat_weekly = models.BooleanField(default=False, verbose_name='Повторять еженедельно')
    repeat_interval_days = models.PositiveIntegerField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    timezone_name = models.CharField(max_length=80, default='UTC')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    enable_sound = models.BooleanField(default=True, verbose_name='Звук уведомления')
    enable_push = models.BooleanField(default=True, verbose_name='Пуш-уведомление')

    is_active = models.BooleanField(default=True, verbose_name='Активно')
    is_triggered = models.BooleanField(default=False, verbose_name='Сработало')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reminder_time']
        verbose_name = 'Напоминание'
        verbose_name_plural = 'Напоминания'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['anime', 'is_active']),
            models.Index(fields=['reminder_time', 'is_active']),
        ]
        constraints = [models.UniqueConstraint(fields=('user', 'calendar_release'), name='calendar_reminder_identity')]

    def __str__(self):
        return f"Reminder for {self.user.username}: {self.franchise_id or self.anime_id or self.calendar_release_id}"


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField()
    endpoint_hash = models.CharField(max_length=64, unique=True, editable=False)
    p256dh = models.TextField(blank=True)
    auth = models.TextField(blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['-last_active']
        indexes = [models.Index(fields=['user','is_active'])]

    def save(self, *args, **kwargs):
        from hashlib import sha256
        self.endpoint_hash = sha256(self.endpoint.encode('utf-8')).hexdigest()
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'endpoint_hash'}
        return super().save(*args, **kwargs)

class EpisodeSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='episode_subs')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='episode_subs')
    is_active = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    paused_until = models.DateTimeField(null=True, blank=True)
    last_notified_episode = models.IntegerField(default=0)
    manually_disabled = models.BooleanField(default=False)
    baseline_initialized = models.BooleanField(default=False)
    notified_episodes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-updated_at']
        unique_together = [['user','anime']]
        indexes = [models.Index(fields=['user','is_active']), models.Index(fields=['anime','is_active'])]

class EpisodeNotice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=160, unique=True)
    notification = models.ForeignKey(Notification, null=True, blank=True, on_delete=models.SET_NULL)
    processed = models.BooleanField(default=False)


class NotificationSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notif_settings')

    type_settings = models.JSONField(default=dict)

    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)

    dnd_enabled = models.BooleanField(default=False)
    dnd_start = models.TimeField(null=True, blank=True)
    dnd_end = models.TimeField(null=True, blank=True)

    auto_clean_read_days = models.IntegerField(default=30)
    auto_clean_unread_days = models.IntegerField(default=90)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки уведомлений'

    def __str__(self):
        return f"NotificationSettings for {self.user.username}"
