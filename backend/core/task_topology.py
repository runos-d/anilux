"""Opt-in worker separation; broker migration and routing are independent switches."""
from kombu import Exchange, Queue

QUEUES = ('celery', 'events', 'notifications', 'recommendations', 'maintenance',
          'reports', 'post_media', 'media_downloads', 'catalog_imports', 'native_builds')
ROUTES = {
    'apps.social.application.tasks_chat.deliver_chat_event': 'events',
    'apps.social.application.tasks_chat.retry_chat_outbox': 'events',
    'social.deliver_post_event': 'events',
    'social.retry_post_events': 'events',
    'notifications.*': 'notifications',
    'apps.notifications.application.celery_tasks.*': 'notifications',
    'apps.users.application.email_tasks.*': 'notifications',
    'users.send_transactional_email': 'notifications',
    'anime.refresh_recommendations': 'recommendations',
    'anime.refresh_dirty_recommendations': 'recommendations',
    'anime.warm_public_catalog': 'recommendations',
    'users.build_data_export': 'reports',
    'users.expire_data_exports': 'reports',
    'apps.social.application.tasks.backup_chat_task': 'reports',
    'apps.social.application.tasks.requeue_pending_chat_backups': 'reports',
    'anime.sync_franchises': 'catalog_imports',
    'apps.anime.import_kodik_*': 'catalog_imports',
    'social.process_post_media': 'post_media',
    'anime.refresh_missing_screenshots': 'catalog_imports',
    'seo.*': 'maintenance',
    'social.gc_post_files': 'maintenance',
    'social.recover_post_media': 'maintenance',
    'anime.cleanup_background_work': 'maintenance',
    'anime.prune_presence_index': 'maintenance',
}


def worker_topology(profile='legacy', *, quorum=False, broker_url='', max_length=10000):
    if profile not in ('legacy', 'isolated'):
        raise ValueError('CELERY_QUEUE_PROFILE must be legacy or isolated')
    if quorum and (profile != 'isolated' or not broker_url.startswith(('amqp://', 'amqps://'))):
        raise ValueError('Quorum queues require isolated profile and RabbitMQ')
    if profile == 'legacy':
        return {}
    exchange = Exchange('celery', type='topic' if quorum else 'direct', durable=True)
    arguments = {'x-max-length': max(100, min(1000000, int(max_length))), 'x-overflow': 'reject-publish'} if quorum else {}
    dead_letter = None
    if quorum:
        arguments.update({'x-queue-type': 'quorum', 'x-delivery-limit': 20,
                          'x-dead-letter-exchange': 'failed', 'x-dead-letter-routing-key': 'failed'})
    queues = [Queue(name, exchange, routing_key=name, durable=True, queue_arguments=dict(arguments)) for name in QUEUES]
    if quorum:
        # A single-node lab checks protocol compatibility, not replicated durability.
        dead_letter = Queue('failed', Exchange('failed', type='direct', durable=True), routing_key='failed',
                            durable=True, queue_arguments={'x-queue-type': 'quorum', 'x-max-length': 10000,
                                                          'x-overflow': 'reject-publish'})
    result = {'task_queues': queues, 'task_routes': {name: {'queue': queue} for name, queue in ROUTES.items()},
              'task_create_missing_queues': False, 'worker_prefetch_multiplier': 1,
              'broker_pool_limit': 10, 'result_expires': 3600,
              'task_annotations': {name: {'acks_late': True, 'reject_on_worker_lost': True}
                  for name in ('apps.social.application.tasks_chat.deliver_chat_event', 'social.deliver_post_event',
                               'anime.refresh_recommendations')}}
    if quorum:
        result.update(task_default_queue_type='quorum', worker_detect_quorum_queues=True,
                      task_default_exchange_type='topic',
                      event_queue_exclusive=True, control_queue_exclusive=True,
                      site_dead_letter_queue=dead_letter,
                      site_bounded_publish=True,
                      broker_transport_options={'confirm_publish': True, 'read_timeout': 2, 'write_timeout': 2})
    return result
