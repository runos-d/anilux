import json
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.social.application.post_audit import counter_rows, differences
from apps.social.infrastructure.models.social import Post, PostMedia
from apps.social.infrastructure.models.post_lifecycle import PostCommand
from apps.social.infrastructure.post_storage import post_private_storage


class Command(BaseCommand):
    help = 'Read-only audit of post counters, idempotency keys and media files'

    def add_arguments(self, parser):
        parser.add_argument('--file-limit', type=int, default=1000)

    def handle(self, **options):
        rows = counter_rows()
        mismatches = []
        for post in rows.iterator(chunk_size=100):
            fields = differences(post)
            if fields: mismatches.append({'id': str(post.pk), 'fields': fields})
        missing, checked = [], 0
        media = PostMedia.objects.filter(post__is_deleted=False, is_active=True, processing_state='ready').select_related('upload')
        for item in media.order_by('pk')[:max(0, options['file_limit'])]:
            names = {field.name for field in (item.file, item.poster, item.thumbnail) if field}
            names.update(item.variants.values())
            if item.upload: names.add(item.upload.original_path)
            for name in sorted(filter(None, names)):
                checked += 1
                if not post_private_storage.exists(name): missing.append({'media_id': str(item.pk), 'name': name})
        duplicate_keys = PostCommand.objects.values('owner_id', 'kind', 'key').annotate(total=Count('pk')).filter(total__gt=1).count()
        self.stdout.write(json.dumps({'posts': rows.count(), 'counter_mismatches': mismatches,
            'duplicate_command_keys': duplicate_keys, 'files_checked': checked, 'missing_files': missing,
            'healthy': not mismatches and not missing and duplicate_keys == 0}, indent=2))
