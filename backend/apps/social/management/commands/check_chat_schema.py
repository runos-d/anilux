import json
from django.core.management.base import BaseCommand, CommandError
from apps.social.application.chat_schema import chat_schema_status


class Command(BaseCommand):
    help = 'Refuse backend/worker startup when chat migrations or columns are missing.'

    def handle(self, **options):
        status = chat_schema_status()
        if not status['ready']:
            raise CommandError('Chat schema is not ready: ' + json.dumps(status) +
                '. Run migrations first: docker compose run --rm --no-deps migrate')
        if options['verbosity']:
            self.stdout.write('Chat schema is ready.')
