import json
from django.core.management.base import BaseCommand, CommandError
from core.project_schema import project_schema_status


class Command(BaseCommand):
    help = 'Reject pending migrations, missing model tables or missing columns'

    def handle(self, **options):
        result = project_schema_status()
        if not result['ready']:
            raise CommandError('Project schema is not ready: ' + json.dumps(result))
        if options['verbosity']:
            self.stdout.write('Project schema is ready')
