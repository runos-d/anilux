import json
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F


class Command(BaseCommand):
    help = 'Mark a bounded keyset page of recommendation projections for versioned rebuild (dry-run default)'

    def add_arguments(self, parser):
        parser.add_argument('--after-id', type=int, default=0)
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--apply', action='store_true')

    def handle(self, **options):
        from apps.anime.models import RecommendationSnapshot
        if not 1 <= options['limit'] <= 500 or options['after_id'] < 0:
            raise CommandError('limit must be 1..500 and after-id nonnegative')
        ids = list(RecommendationSnapshot.objects.filter(pk__gt=options['after_id']).order_by('pk')
                   .values_list('pk', flat=True)[:options['limit']])
        if options['apply'] and ids:
            RecommendationSnapshot.objects.filter(pk__in=ids).update(dirty=True, revision=F('revision')+1)
        # Durable dirty rows are retried by the existing bounded periodic worker;
        # no broker availability or full-library computation is needed here.
        self.stdout.write(json.dumps({'applied': options['apply'], 'selected': len(ids),
                                      'next_after_id': ids[-1] if ids else None}))
