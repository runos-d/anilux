import json
import os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from core.object_migration import mirror_file, s3_client, transfer_config, storage_roots


class Command(BaseCommand):
    help = 'Hash one media file; --apply uploads/verifies a private S3 copy without changing live paths'

    def add_arguments(self, parser):
        parser.add_argument('--domain', choices=('chat', 'post', 'public'), required=True)
        parser.add_argument('--name', required=True)
        parser.add_argument('--bucket', required=True)
        parser.add_argument('--endpoint')
        parser.add_argument('--manifest')
        parser.add_argument('--apply', action='store_true')

    def handle(self, **options):
        root = storage_roots()[options['domain']]
        if options['apply'] and not options['manifest']:
            raise CommandError('--apply requires a private manifest path outside the checkout')
        given_manifest = Path(options['manifest']) if options['manifest'] else None
        if given_manifest and given_manifest.is_symlink():
            raise CommandError('Manifest must not be a symlink')
        manifest = given_manifest.resolve() if given_manifest else None
        base = Path(settings.BASE_DIR).resolve()
        checkout = base.parent if (base.parent / '.git').exists() else base
        if manifest and manifest.is_relative_to(checkout):
            raise CommandError('Private manifests must be outside the source checkout')
        if manifest and manifest.exists() and manifest.stat().st_mode & 0o077:
            raise CommandError('Existing manifest permissions must be 600')
        if options['endpoint'] and not options['endpoint'].startswith('https://'):
            raise CommandError('Object storage endpoint must use HTTPS')
        try:
            result = mirror_file(s3_client(options['endpoint']) if options['apply'] else None,
                bucket=options['bucket'], root=root, name=options['name'], domain=options['domain'],
                apply=options['apply'], transfer_config=transfer_config() if options['apply'] else None)
        except (ImportError, ValueError) as error:
            raise CommandError(str(error)) from error
        if manifest:
            # One complete verified record per append; run one migration writer
            # per manifest. No local file or public ID is renamed or deleted.
            with os.fdopen(os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), 'a') as output:
                output.write(json.dumps(result) + '\n')
                output.flush()
                os.fsync(output.fileno())
        self.stdout.write(json.dumps({'applied': result['applied'], 'verified': result['verified'],
                                      'bytes': result['bytes'], 'source_preserved': True}))
