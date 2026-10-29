import uuid
from django.db import models


class WorkGate(models.Model):
    name = models.CharField(primary_key=True, max_length=32)


class BackgroundJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=16, db_index=True)
    key = models.CharField(max_length=64, unique=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, default='pending', db_index=True)
    result = models.JSONField(default=dict)
    error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['kind', 'status'], name='background_kind_status')]
