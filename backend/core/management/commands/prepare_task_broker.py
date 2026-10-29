import json
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Provision the fixed isolated task queues before starting RabbitMQ workers (dry-run default)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, **options):
        from config.celery import app
        from django.conf import settings
        if settings.CELERY_QUEUE_PROFILE != 'isolated' or not settings.CELERY_QUORUM_QUEUES:
            raise CommandError('Queue provisioning requires isolated RabbitMQ quorum configuration')
        queues = [*app.conf.task_queues, app.conf.site_dead_letter_queue]
        if options['apply']:
            try:
                with app.connection_for_write() as broker:
                    broker.ensure_connection(max_retries=0)
                    with broker.channel() as channel:
                        for queue in queues:
                            queue(channel).declare()
            except Exception as error:
                raise CommandError('Queue provisioning failed; inspect private broker logs') from None
        self.stdout.write(json.dumps({'applied': options['apply'], 'durable_queues': len(queues),
            'names': [queue.name for queue in queues]}))
