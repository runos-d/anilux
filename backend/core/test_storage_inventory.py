import hashlib
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from core.storage_inventory import scan_storage


class StorageInventoryTests(SimpleTestCase):
    def test_roots_match_live_defaults_without_optional_settings(self):
        from core.object_migration import storage_roots
        with patch('django.conf.settings', SimpleNamespace(MEDIA_ROOT='/files/media',
                CHAT_PRIVATE_MEDIA_ROOT='/files/chats', DATA_DIR='/files')):
            roots = storage_roots()
        self.assertEqual(roots['post'], Path('/files/private_post_media'))
        self.assertEqual(roots['downloads'], Path('/files/private_downloads'))

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base/'storage'
        self.root.mkdir()
        (self.root/'orphan-private.bin').write_bytes(b'orphan')
        (self.root/'exports').mkdir()
        (self.root/'exports'/'private.json').write_text('{}')

    def scan(self, name='manifest.jsonl', **kwargs):
        with (self.base/name).open('w') as output:
            summary = scan_storage(self.root, output, **kwargs)
        rows = [json.loads(line) for line in (self.base/name).read_text().splitlines()]
        return summary, rows

    def test_stream_contains_unreferenced_files_and_bounded_hashes_without_sql(self):
        summary, rows = self.scan(hash_budget=8)
        self.assertTrue(summary['scan_completed'])
        self.assertEqual(summary['files'], 2)
        self.assertEqual(summary['hashed_bytes'], 8)
        orphan = next(row for row in rows if row.get('legacy_name') == 'orphan-private.bin')
        self.assertEqual(orphan['sha256'], hashlib.sha256(b'orphan').hexdigest())
        self.assertFalse(summary['complete_storage_inventory'])

    def test_budget_marks_partial_and_prefix_cannot_escape_or_follow_symlink(self):
        summary, rows = self.scan(max_entries=1)
        self.assertFalse(summary['scan_completed'])
        self.assertEqual(summary['entries'], 1)
        link = self.root/'outside'
        link.symlink_to(self.base, target_is_directory=True)
        for prefix in ('../', '/etc', 'outside'):
            with self.assertRaises(ValueError):
                self.scan(name='rejected.jsonl', prefix=prefix)
        summary, rows = self.scan(name='with-link.jsonl')
        self.assertEqual(summary['symlinks'], 1)
        self.assertFalse(any('manifest.jsonl' in row.get('legacy_name', '') for row in rows))

    def test_command_names_are_private_and_existing_manifest_is_preserved(self):
        target = self.base/'private.jsonl'
        output = StringIO()
        with override_settings(MEDIA_ROOT=str(self.root)):
            call_command('inventory_storage_tree', domain='public', manifest=str(target), stdout=output)
            saved = target.read_bytes()
            self.assertNotIn('orphan-private', output.getvalue())
            with self.assertRaises(CommandError):
                call_command('inventory_storage_tree', domain='public', manifest=str(target))
            self.assertEqual(target.read_bytes(), saved)
        self.assertEqual((self.root/'orphan-private.bin').read_bytes(), b'orphan')
