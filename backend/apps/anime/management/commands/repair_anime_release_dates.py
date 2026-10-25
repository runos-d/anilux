from django.core.management.base import BaseCommand

from apps.anime.application.release_year import premiere_date
from apps.anime.infrastructure.models.anime import Anime


class Command(BaseCommand):
    help = 'Заполняет пустую дату премьеры из сохранённых данных Kodik; без --apply работает как dry-run.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Сохранить найденные даты.')
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **options):
        apply_changes = options['apply']
        batch_size = max(1, min(options['batch_size'], 5000))
        candidates = Anime.objects.filter(release_date__isnull=True).only(
            'id', 'release_date', 'release_date_string', 'raw_kodik_data'
        ).order_by('pk')
        pending = []
        found = 0
        updated = 0
        for anime in candidates.iterator(chunk_size=batch_size):
            exact = premiere_date(anime.raw_kodik_data or {})
            if not exact:
                continue
            found += 1
            if not apply_changes:
                continue
            anime.release_date = exact
            anime.release_date_string = exact.isoformat()
            pending.append(anime)
            if len(pending) >= batch_size:
                Anime.objects.bulk_update(pending, ['release_date', 'release_date_string'], batch_size=batch_size)
                updated += len(pending)
                pending = []
        if pending:
            Anime.objects.bulk_update(pending, ['release_date', 'release_date_string'], batch_size=batch_size)
            updated += len(pending)
        mode = 'applied' if apply_changes else 'dry-run'
        self.stdout.write(self.style.SUCCESS(f'{mode}: found={found}, updated={updated}'))
