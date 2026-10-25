import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Avg, DurationField, ExpressionWrapper, F, Min, Q
from django.utils import timezone
from apps.social.infrastructure.models.conversation import ChatEvent
from apps.social.infrastructure.models.social_chat import ChatBackup


class Command(BaseCommand):
    help = 'Report chat outbox backlog, delivery latency and backup worker state as JSON'

    def add_arguments(self, parser):
        parser.add_argument('--max-pending-age', type=int, default=30)

    def handle(self, **options):
        now = timezone.now()
        pending = ChatEvent.objects.filter(delivered_at__isnull=True)
        oldest = pending.aggregate(value=Min('created_at'))['value']
        recent = ChatEvent.objects.filter(delivered_at__gte=now - timedelta(minutes=15)).aggregate(
            latency=Avg(ExpressionWrapper(F('delivered_at') - F('created_at'), output_field=DurationField())))['latency']
        stalled = ChatBackup.objects.filter(status='creating', created_at__lt=now-timedelta(minutes=6)).filter(
            Q(processing_started_at__isnull=True) | Q(processing_started_at__lt=now-timedelta(minutes=6))).count()
        age = (now-oldest).total_seconds() if oldest else 0
        self.stdout.write(json.dumps({
            'observed_at': now.isoformat(), 'outbox_pending': pending.count(),
            'oldest_pending_seconds': round(age, 3), 'mean_delivery_seconds_15m': round(recent.total_seconds(), 3) if recent is not None else None,
            'backups_creating': ChatBackup.objects.filter(status='creating').count(),
            'backups_failed': ChatBackup.objects.filter(status='failed').count(), 'backups_stalled': stalled,
            'healthy': age <= options['max_pending_age'] and stalled == 0,
        }, indent=2))
