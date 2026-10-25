import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class UploadUUIDField(models.UUIDField):
    def db_parameters(self, connection):
        parameters = super().db_parameters(connection)
        parameters['collation'] = 'utf8mb4_unicode_ci' if self.db_type(connection) == 'char(32)' else None
        return parameters


class PostUpload(models.Model):
    id = UploadUUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    expected_size = models.PositiveBigIntegerField()
    offset = models.PositiveBigIntegerField(default=0)
    state = models.CharField(max_length=20, default='uploading', db_index=True)
    original_path = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict)
    checksum = models.CharField(max_length=64, blank=True)
    error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)


class PostCommand(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=30)
    key = models.CharField(max_length=128)
    fingerprint = models.CharField(max_length=64)
    response = models.JSONField(default=dict)
    post = models.ForeignKey('social.Post', null=True, on_delete=models.SET_NULL)
    comment = models.ForeignKey('social.PostComment', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner', 'kind', 'key'], name='post_command_owner_kind_key')]


class PostEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey('social.Post', on_delete=models.CASCADE)
    kind = models.CharField(max_length=40)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=500, blank=True)


class PostFeedSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mode = models.CharField(max_length=30)
    ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)


class PostFileCleanup(models.Model):
    media = models.OneToOneField('social.PostMedia', on_delete=models.CASCADE)
    not_before = models.DateTimeField(db_index=True)
    state = models.CharField(max_length=20, default='queued', db_index=True)
    manifest = models.JSONField(default=list)
    error = models.CharField(max_length=500, blank=True)
    completed_at = models.DateTimeField(null=True)
