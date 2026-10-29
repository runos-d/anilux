"""On-demand bounded operational snapshot; never emit credentials or payloads."""
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.db.models import Count, Min
from django.utils import timezone


class Command(BaseCommand):
    help = 'Report outbox backlog and MySQL connection/query counters (no user data)'

    def handle(self, **options):
        from apps.social.infrastructure.models.conversation import ChatEvent
        from apps.social.infrastructure.models.post_lifecycle import PostEvent
        now = timezone.now()
        result = {'schema_version': 1, 'captured_at': now.isoformat(), 'outbox': {}}
        for name, model in (('chat', ChatEvent), ('post', PostEvent)):
            summary = model.objects.filter(delivered_at__isnull=True).aggregate(count=Count('pk'), oldest=Min('created_at'))
            result['outbox'][name] = {'pending': summary['count'],
                'oldest_age_seconds': max(0, (now - summary['oldest']).total_seconds()) if summary['oldest'] else 0}
        if connection.vendor == 'mysql':
            with connection.cursor() as cursor:
                cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Threads_running','Questions','Slow_queries','Bytes_received','Bytes_sent')")
                result['mysql'] = {key: int(value) for key, value in cursor.fetchall()}
        if settings.CELERY_BROKER_URL.startswith(('redis://', 'rediss://')):
            from redis import Redis
            client = Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=.5, socket_connect_timeout=.5)
            queues = ('celery', 'events', 'notifications', 'recommendations', 'maintenance',
                      'reports', 'post_media', 'catalog_imports', 'media_downloads')
            try:
                with client.pipeline(transaction=False) as pipe:
                    for name in queues:
                        pipe.llen(name)
                    result['queue_ready'] = dict(zip(queues, pipe.execute()))
            except Exception:
                result['queue_ready'] = {'available': False}
            finally:
                client.close()
        self.stdout.write(json.dumps(result, indent=2))
