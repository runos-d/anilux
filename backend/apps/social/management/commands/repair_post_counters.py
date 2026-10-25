import json
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.social.application.post_audit import counter_rows, differences
from apps.social.application.post_commands import record_event
from apps.social.infrastructure.models.social import Post
from apps.users.infrastructure.models.users import User


class Command(BaseCommand):
    help = 'Preview counter repairs; --apply changes only derived counters'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, **options):
        changes = []
        for candidate in counter_rows().iterator(chunk_size=100):
            if not differences(candidate): continue
            with transaction.atomic():
                User.objects.select_for_update().only('id').get(pk=candidate.author_id)
                locked = Post.objects.select_for_update().filter(pk=candidate.pk).first()
                if not locked: continue
                current = counter_rows(Post.objects.filter(pk=locked.pk)).get()
                fields = differences(current)
                if not fields: continue
                changes.append({'id': str(current.pk), 'fields': fields})
                if options['apply']:
                    Post.objects.filter(pk=current.pk).update(**{kind+'_count': value['actual'] for kind, value in fields.items()})
                    record_event(locked, 'post_updated')
        self.stdout.write(json.dumps({'applied': options['apply'], 'changes': changes}, indent=2))
