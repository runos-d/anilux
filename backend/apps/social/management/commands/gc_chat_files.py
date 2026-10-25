import json
import math
from django.core.management.base import BaseCommand, CommandError
from apps.social.application.chat_file_gc import collect, restore


class Command(BaseCommand):
    help = 'Audit or quarantine old unreferenced chat files during a maintenance window.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-hours', type=float, default=24)
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--writers-stopped', action='store_true')
        parser.add_argument('--restore', metavar='RUN_ID')

    def handle(self, **options):
        if not math.isfinite(options['older_than_hours']) or options['older_than_hours'] < 24 or not 1 <= options['limit'] <= 1000:
            raise CommandError('Age must be at least 24 hours and limit must be 1..1000')
        if options['apply'] and options['restore']:
            raise CommandError('Choose collection or restore')
        if (options['apply'] or options['restore']) and not options['writers_stopped']:
            raise CommandError('Stop backend/worker/beat before moving files; pass --writers-stopped')
        result = restore(options['restore']) if options['restore'] else collect(
            age_hours=options['older_than_hours'], limit=options['limit'], apply=options['apply'])
        self.stdout.write(json.dumps(result, ensure_ascii=False))
