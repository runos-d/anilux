import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Min, Q
from django.utils import timezone
from apps.social.infrastructure.models.social import PostMedia
from apps.social.infrastructure.models.post_lifecycle import PostEvent, PostUpload, PostFileCleanup


class Command(BaseCommand):
    help = 'Report durable post events, media leases and cleanup backlog as JSON'

    def handle(self, **options):
        now = timezone.now()
        events = PostEvent.objects.filter(delivered_at__isnull=True)
        oldest = events.aggregate(value=Min('created_at'))['value']
        stalled = PostMedia.objects.filter(processing_state='processing').filter(
            Q(processing_started_at__lt=now-timedelta(hours=2)) |
            Q(processing_started_at__isnull=True, created_at__lt=now-timedelta(hours=2))).count()
        age = (now-oldest).total_seconds() if oldest else 0
        self.stdout.write(json.dumps({
            'observed_at': now.isoformat(), 'outbox_pending': events.count(),
            'oldest_event_seconds': round(age, 3), 'media_stalled': stalled,
            'media_queued': PostMedia.objects.filter(processing_state='queued', post__is_deleted=False).count(),
            'media_failed': PostMedia.objects.filter(processing_state='failed', post__is_deleted=False).count(),
            'expired_unbound_uploads': PostUpload.objects.filter(expires_at__lt=now, postmedia__isnull=True).count(),
            'cleanup_due': PostFileCleanup.objects.filter(state='queued', not_before__lte=now).count(),
            'healthy': age <= 30 and stalled == 0,
        }, indent=2))
