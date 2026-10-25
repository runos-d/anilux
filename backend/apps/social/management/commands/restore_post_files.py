import hashlib
import json
import shutil
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.social.infrastructure.models.post_lifecycle import PostFileCleanup
from apps.social.infrastructure.post_storage import post_private_storage


class Command(BaseCommand):
    help = 'Validate quarantined files; restore only with --apply. Existing files are never overwritten.'

    def add_arguments(self, parser):
        selector = parser.add_mutually_exclusive_group(required=True)
        selector.add_argument('--job-id', type=int)
        selector.add_argument('--quarantine-id')
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        root = Path(post_private_storage.location).resolve()
        job = None
        if options['job_id']:
            job = PostFileCleanup.objects.filter(pk=options['job_id']).first()
            if not job: raise CommandError('Cleanup job does not exist')
            entries = job.manifest
        else:
            directory = (root / '.trash' / options['quarantine_id']).resolve()
            if not directory.is_relative_to(root / '.trash'): raise CommandError('Invalid quarantine path')
            try: entries = [json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))]
            except (OSError, ValueError) as error: raise CommandError(str(error))
        checked = []
        for entry in entries:
            if entry.get('missing'): continue
            source = (root / entry['quarantine']).resolve()
            target_root = Path(settings.MEDIA_ROOT).resolve() if entry.get('source_root') == 'legacy' else root
            target = (target_root / entry['name']).resolve()
            if not source.is_relative_to(root / '.trash') or not target.is_relative_to(target_root):
                raise CommandError('File path is outside the storage root')
            if target.exists(): raise CommandError(f'File already exists: {entry["name"]}')
            if not source.is_file(): raise CommandError(f'Quarantine file is missing: {entry["name"]}')
            with source.open('rb') as file: checksum = hashlib.file_digest(file, 'sha256').hexdigest()
            if checksum != entry['sha256'] or source.stat().st_size != entry['bytes']:
                raise CommandError(f'Checksum/size mismatch: {entry["name"]}')
            checked.append((source, target))
        if options['apply']:
            for source, target in checked:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
            if job:
                job.state = 'restored'; job.save(update_fields=['state'])
        self.stdout.write(f'{"Restored" if options["apply"] else "Validated"}: {len(checked)} file(s)')
