import uuid
from django.conf import settings
from django.db import models


class Excerpt(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='excerpts')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, related_name='excerpts')
    season = models.PositiveIntegerField(default=1)
    episode = models.PositiveIntegerField(default=1)
    translation_id = models.PositiveIntegerField()
    translation_title = models.CharField(max_length=255)
    player_link = models.URLField(max_length=1000)
    duration = models.FloatField()
    start = models.FloatField()
    end = models.FloatField()
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    shared = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        indexes = [models.Index(fields=['author', '-created_at'], name='excerpt_author_created')]
        constraints = [
            models.CheckConstraint(condition=models.Q(start__gte=0), name='excerpt_start_nonnegative'),
            models.CheckConstraint(condition=models.Q(end__gt=models.F('start')), name='excerpt_positive_range'),
            models.CheckConstraint(condition=models.Q(end__lte=models.F('duration')), name='excerpt_within_duration'),
        ]
