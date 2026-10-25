import json
import time
from pathlib import Path, PurePosixPath

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from apps.social.infrastructure.chat_storage import ChatPrivateStorage, chat_private_storage


class Command(BaseCommand):
    help = 'Report missing/orphaned private chat files; never delete files.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-hours', type=float, default=24)
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        if options['older_than_hours'] < 0 or not 1 <= options['limit'] <= 1000:
            raise CommandError('Invalid age or sample limit')
        root = Path(chat_private_storage.location)
        references = set()
        for model in apps.get_app_config('social').get_models():
            for field in model._meta.fields:
                if isinstance(field, models.FileField) and isinstance(field.storage, ChatPrivateStorage):
                    references.update(model.objects.exclude(**{field.name: ''}).values_list(field.name, flat=True))
        references.discard(None)
        invalid, missing = [], []
        for name in sorted(references):
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:
                invalid.append(name)
            elif not (root / name).is_file():
                missing.append(name)
        cutoff = time.time() - options['older_than_hours'] * 3600
        orphan_count, orphan_bytes, samples = 0, 0, []
        for path in root.rglob('*'):
            if path.is_symlink() or not path.is_file():
                continue
            name = path.relative_to(root).as_posix()
            if name in references:
                continue
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            if stat.st_mtime > cutoff:
                continue
            orphan_count += 1
            orphan_bytes += stat.st_size
            if len(samples) < options['limit']:
                samples.append(name)
        self.stdout.write(json.dumps({'root': str(root), 'referenced_files': len(references),
            'missing_count': len(missing), 'missing_sample': missing[:options['limit']],
            'invalid_count': len(invalid), 'invalid_sample': invalid[:options['limit']],
            'orphan_count': orphan_count, 'orphan_bytes': orphan_bytes, 'orphan_sample': samples,
            'older_than_hours': options['older_than_hours'], 'read_only': True}, ensure_ascii=False))
