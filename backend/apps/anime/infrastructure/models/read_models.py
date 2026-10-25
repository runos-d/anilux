from django.conf import settings
from django.db import models


class RecommendationSnapshot(models.Model):
    key = models.CharField(max_length=80, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    data = models.JSONField(default=dict)
    dirty = models.BooleanField(default=True, db_index=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)
    catalog_revision = models.FloatField(default=0)
    algorithm_version = models.PositiveIntegerField(default=0)


class CalendarSnapshot(models.Model):
    key = models.CharField(max_length=40, unique=True, default='kodik')
    entries = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)


class CalendarRelease(models.Model):
    shikimori_id = models.PositiveIntegerField()
    episode = models.PositiveIntegerField(default=0)
    aired_at = models.DateTimeField(db_index=True)
    data = models.JSONField(default=dict)
    schedule_uncertain = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=('shikimori_id', 'episode'), name='calendar_release_identity')]


class KodikAvailability(models.Model):
    anime = models.OneToOneField('anime.Anime', on_delete=models.CASCADE, related_name='kodik_availability')
    episodes = models.JSONField(default=list)
    last_episode = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
