import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.anime.models import Anime
from apps.anime.application.release_year import release_year, valid_year


class Command(BaseCommand):
    help = 'Dry-run by default. --apply requires a new --backup file with before/after values.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--backup')

    def handle(self, *args, **options):
        changes = []
        for row in Anime.objects.only('id', 'year', 'raw_kodik_data').iterator(chunk_size=200):
            raw = row.raw_kodik_data or {}
            expected = release_year(raw)
            legacy = valid_year((raw.get('material_data') or {}).get('year'))
            if expected and row.year != expected and (row.year is None or row.year == legacy):
                changes.append({'id': row.pk, 'before': row.year, 'after': expected})
        if options['apply']:
            if not options['backup']:
                raise CommandError('--apply requires --backup')
            path = Path(options['backup'])
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with path.open('x', encoding='utf-8') as output:
                    json.dump({'at': timezone.now().isoformat(), 'changes': changes}, output)
            except FileExistsError as error:
                raise CommandError('Backup already exists; use a new file') from error
            with transaction.atomic():
                rows = {row.pk: row for row in Anime.objects.select_for_update().filter(pk__in=[c['id'] for c in changes])}
                for change in changes:
                    row = rows[change['id']]
                    if row.year != change['before']:
                        raise CommandError('Year changed concurrently; rerun dry-run')
                    row.year = change['after']
                Anime.objects.bulk_update(rows.values(), ['year'], batch_size=200)
            from apps.anime.application.recommendations import invalidate_catalog
            invalidate_catalog()
            for franchise in {row.franchise_id for row in rows.values() if row.franchise_id}:
                from apps.anime.models import Franchise
                Franchise.objects.get(pk=franchise).update_aggregated_data()
        self.stdout.write(json.dumps({'applied': options['apply'], 'changes': len(changes), 'sample': changes[:10]}))
