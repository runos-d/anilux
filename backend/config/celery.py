import os
from celery import Celery
from celery.schedules import crontab
import logging


logger = logging.getLogger(__name__)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config', task_cls='core.bounded_tasks:BoundedPublishTask')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.imports = (
    'apps.native_apps.tasks',
    'apps.anime.application.tasks',
    'apps.anime.application.metadata_tasks',
    'apps.anime.application.background_tasks',
    'apps.anime.application.tasks_kodik_dumps',
    'apps.social.application.tasks',
    'apps.social.application.tasks_chat',
    'apps.anime.application.recommendations',
    'apps.anime.application.site_reads',
    'apps.anime.application.franchise_sync',
    'apps.social.application.post_media',
    'apps.social.application.post_commands',
    'apps.social.application.post_file_gc',
    'apps.notifications.application.celery_tasks',
    'apps.users.application.email_tasks',
    'apps.users.application.user_data_tasks',
    'apps.seo.tasks',
)

app.conf.beat_schedule = {
    'missing-screenshots': {'task': 'anime.refresh_missing_screenshots', 'schedule': 60.0},
    'presence-index-expiry': {'task': 'anime.prune_presence_index', 'schedule': 60.0},
    'background-work-cleanup': {'task': 'anime.cleanup_background_work', 'schedule': 60.0},
    'episode-events': {'task': 'notifications.process_episode_events', 'schedule': 60.0},
    'shikimori-franchise-sync': {'task': 'anime.sync_franchises', 'schedule': 90.0},
    'catalog-first-page': {'task': 'anime.warm_public_catalog', 'schedule': 120.0},
    'post-file-gc': {'task': 'social.gc_post_files', 'schedule': 3600.0},
    'post-outbox': {'task': 'social.retry_post_events', 'schedule': 5.0},
    'post-media-recovery': {'task': 'social.recover_post_media', 'schedule': 60.0},
    'recommendation-read-models': {'task': 'anime.refresh_dirty_recommendations', 'schedule': 15.0},
    'chat-outbox': {'task': 'apps.social.application.tasks_chat.retry_chat_outbox', 'schedule': 5.0},
    'chat-backups': {'task': 'apps.social.application.tasks.requeue_pending_chat_backups', 'schedule': 60.0},
    'chat-scheduled': {'task': 'social.send_scheduled_messages', 'schedule': 10.0},
    'chat-expired-bans': {'task': 'social.cleanup_expired_bans', 'schedule': 60.0},
    'chat-expired-restrictions': {'task': 'social.cleanup_expired_restrictions', 'schedule': 60.0},
    'chat-expired-invites': {'task': 'social.cleanup_expired_invite_links', 'schedule': 60.0},
    'user-data-export-expiry': {'task': 'users.expire_data_exports', 'schedule': crontab(minute='17', hour='3')},
    'kodik-catalog-import': {
        'task': 'apps.anime.import_kodik_dumps',
        'schedule': crontab(minute='24,54'),
    },
    'kodik-calendar-import': {
        'task': 'apps.anime.import_kodik_calendar',
        'schedule': crontab(minute='12,42'),
    },
}

app.conf.update(
    result_extended=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=280,
    task_default_queue='celery',
    task_default_exchange='celery',
    task_default_routing_key='celery',
)

from django.conf import settings
from core.task_topology import worker_topology
app.conf.update(**worker_topology(settings.CELERY_QUEUE_PROFILE,
    quorum=settings.CELERY_QUORUM_QUEUES, broker_url=settings.CELERY_BROKER_URL,
    max_length=settings.CELERY_QUEUE_MAX_LENGTH))
if settings.ROOT_URLCONF == 'config.urls_scalability_lab':
    app.conf.imports = (*app.conf.imports, 'core.scalability_tasks')

app.set_default()

app.conf.beat_schedule['seo-hub-inventory'] = {
    'task': 'seo.refresh_hubs', 'schedule': crontab(minute='*/15'),
}

@app.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}')
