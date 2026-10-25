from django.core.management.base import BaseCommand
from apps.anime.application.recommendations import refresh_recommendations
from apps.users.infrastructure.models.users import User


class Command(BaseCommand):
    help = 'Persist public and active-account recommendation snapshots.'

    def add_arguments(self, parser):
        parser.add_argument('--public-only', action='store_true')

    def handle(self, *args, **options):
        from apps.anime.application.site_reads import warm_public_catalog
        warm_public_catalog()
        from apps.anime.application.kodik_dump_service import get_calendar_entries
        from apps.anime.infrastructure.models.read_models import CalendarSnapshot
        entries = get_calendar_entries()
        if entries: CalendarSnapshot.objects.update_or_create(key='kodik', defaults={'entries': entries})
        refresh_recommendations('public')
        count = 1
        if not options['public_only']:
            for pk in User.objects.filter(is_active=True).values_list('pk', flat=True).iterator(chunk_size=100):
                refresh_recommendations(f'user:{pk}')
                count += 1
        self.stdout.write(f'Prepared recommendation snapshots: {count}')
