from django.core.management.base import BaseCommand
from apps.seo.tasks import refresh_hubs


class Command(BaseCommand):
    help = 'Refresh SEO hub candidate inventory; public pages always read live data.'

    def handle(self, **options):
        self.stdout.write(f'SEO hubs: {refresh_hubs()}')
