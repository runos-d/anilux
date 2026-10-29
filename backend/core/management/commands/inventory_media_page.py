import json
import os
from collections import Counter

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.db.models import Max

from core.media_inventory import describe_fields, file_fields, inventory_page, private_page


class Command(BaseCommand):
    help = 'Describe FileFields or save one bounded keyset page to a private manifest; never upload/delete'

    def add_arguments(self, parser):
        parser.add_argument('--describe', action='store_true')
        parser.add_argument('--model')
        parser.add_argument('--after-id', type=int, default=0)
        parser.add_argument('--through-id', type=int)
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--hash-budget-mib', type=int, default=0)
        parser.add_argument('--manifest')

    def handle(self, **options):
        if options['describe']:
            self.stdout.write(json.dumps({'fields': describe_fields(), 'database_access': False,
                                          'complete_storage_inventory': False}))
            return
        if not options['model'] or not options['manifest']:
            raise CommandError('--model and --manifest required; names must never go to stdout')
        if not (0 <= options['after_id'] < 2**63 and 1 <= options['limit'] <= 500
                and 0 <= options['hash_budget_mib'] <= 64):
            raise CommandError('after-id >=0, limit 1..500, hash budget 0..64 MiB required')
        try:
            model = apps.get_model(options['model'])
        except (ValueError, LookupError) as error:
            raise CommandError('Unknown model') from error
        if not isinstance(model._meta.pk, models.IntegerField) or not file_fields(model):
            raise CommandError('Model needs integer primary key and FileFields')
        through = options['through_id']
        if through is not None and not 0 <= through < 2**63:
            raise CommandError('through-id must be >=0')
        try:
            # Open before SQL: existing pages cannot be overwritten, even on retry.
            with private_page(options['manifest']) as output:
                if through is None:
                    through = model._base_manager.aggregate(value=Max('pk'))['value'] or 0
                page = inventory_page(model, after_id=options['after_id'], through_id=through,
                    limit=options['limit'], hash_budget=options['hash_budget_mib']*1024*1024)
                json.dump(page, output)
                output.flush()
                os.fsync(output.fileno())
        except (ValueError, OSError) as error:
            raise CommandError('Manifest creation/inventory failed; use a new private page path') from error
        self.stdout.write(json.dumps({key: page[key] for key in
            ('model', 'rows', 'next_after_id', 'through_id', 'has_more', 'complete_storage_inventory')} | {
                'reference_statuses': dict(Counter(item['status'] for item in page['references'])),
                'source_preserved': True, 'private_names_printed': False}))
