import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.users.infrastructure.models.users import User
from core.media_inventory import inventory_page


class MediaInventoryTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.media = self.root/'public'
        self.media.mkdir()
        changed = override_settings(MEDIA_ROOT=str(self.media), CHAT_PRIVATE_MEDIA_ROOT=str(self.root/'chat'),
                                    POST_PRIVATE_MEDIA_ROOT=str(self.root/'post'))
        changed.enable()
        self.addCleanup(changed.disable)
        User.objects.bulk_create([User(username=f'inventory-{i}', email=f'i{i}@example.test', password='!', avatar=name)
            for i, name in enumerate(('secret-name.bin', 'missing.bin', '../outside.bin'))])
        self.users = list(User.objects.filter(username__startswith='inventory-').order_by('pk'))
        (self.media/'secret-name.bin').write_bytes(b'contents')

    def run_page(self, path, **options):
        output = StringIO()
        call_command('inventory_media_page', model='users.User', manifest=str(path), stdout=output, **options)
        self.assertNotIn('secret-name', output.getvalue())
        return json.loads(output.getvalue()), json.loads(path.read_text())

    def test_keyset_page_has_watermark_hashes_and_private_names_only_in_manifest(self):
        first = self.root/'page1.json'
        with self.assertNumQueries(2):
            summary, page = self.run_page(first, limit=2, hash_budget_mib=1)
        self.assertEqual(page['rows'], 2)
        self.assertTrue(summary['has_more'])
        self.assertEqual(page['references'][0]['sha256'], hashlib.sha256(b'contents').hexdigest())
        self.assertEqual(page['references'][1]['status'], 'missing')
        User.objects.bulk_create([User(username='inventory-new', email='new@example.test', password='!', avatar='new.bin')])
        _, next_page = self.run_page(self.root/'page2.json', after_id=summary['next_after_id'],
                                     through_id=summary['through_id'])
        self.assertEqual(next_page['rows'], 1)
        self.assertEqual(next_page['references'][0]['status'], 'invalid_path')
        self.assertFalse(next_page['has_more'])
        self.assertTrue((self.media/'secret-name.bin').exists())

    def test_hash_budget_and_unsupported_storage_are_explicit(self):
        User.objects.filter(pk=self.users[1].pk).update(avatar='second.bin')
        (self.media/'second.bin').write_bytes(b'contents')
        page = inventory_page(User, after_id=0, through_id=self.users[1].pk, limit=2, hash_budget=8)
        self.assertIn('sha256', page['references'][0])
        self.assertNotIn('sha256', page['references'][1])
        self.assertFalse(page['complete_storage_inventory'])

    def test_manifest_cannot_overwrite_follow_symlink_or_enter_checkout(self):
        target = self.root/'page.json'
        target.write_text('preserved')
        for path in (target, Path(settings.BASE_DIR)/'never-create-private-inventory.json'):
            with self.assertRaises(CommandError):
                self.run_page(path)
        self.assertEqual(target.read_text(), 'preserved')
        link = self.root/'symlink.json'
        link.symlink_to(target)
        with self.assertRaises(CommandError):
            self.run_page(link)
        self.assertEqual(target.read_text(), 'preserved')

    def test_schema_description_uses_no_database_and_does_not_infer_visibility(self):
        output = StringIO()
        with self.assertNumQueries(0):
            call_command('inventory_media_page', describe=True, stdout=output)
        description = json.loads(output.getvalue())
        self.assertGreater(len(description['fields']), 20)
        self.assertTrue(all(not row['visibility_inferred'] for row in description['fields']))
