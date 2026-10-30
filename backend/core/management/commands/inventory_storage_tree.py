"""Names go only into a new private manifest; stdout contains aggregate counts."""
import json
from django.core.management.base import BaseCommand, CommandError
from core.media_inventory import private_page
from core.storage_inventory import scan_storage
from core.object_migration import storage_roots


class Command(BaseCommand):
    help = 'Stream a bounded physical storage inventory, without changing source files'

    def add_arguments(self, parser):
        parser.add_argument('--domain', choices=('public', 'chat', 'post', 'downloads'), required=True)
        parser.add_argument('--prefix', default='')
        parser.add_argument('--manifest', required=True)
        parser.add_argument('--max-entries', type=int, default=10000)
        parser.add_argument('--max-seconds', type=int, default=30)
        parser.add_argument('--hash-budget-mib', type=int, default=0)

    def handle(self, **options):
        try:
            with private_page(options['manifest']) as output:
                result = scan_storage(storage_roots()[options['domain']], output, domain=options['domain'], prefix=options['prefix'],
                    max_entries=options['max_entries'], max_seconds=options['max_seconds'],
                    hash_budget=options['hash_budget_mib']*1024*1024)
        except (OSError, ValueError):
            # Do not print an exception that may contain a private source name.
            raise CommandError('Inventory rejected or failed; preserve manifest and inspect privately') from None
        self.stdout.write(json.dumps(result))
