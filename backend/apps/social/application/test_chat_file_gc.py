import io
import json
import os
import tempfile
import time
from pathlib import Path
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from unittest.mock import patch

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import PrivateChat, Attachment
from apps.social.infrastructure.chat_storage import chat_private_storage
from . import conversations as service


class ChatFileCollectionTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='chat-gc-tests-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'private'
        setting = override_settings(CHAT_PRIVATE_MEDIA_ROOT=str(self.root))
        setting.enable(); self.addCleanup(setting.disable)
        user = User.objects.create_user(username='gc_a', email='gc_a@test.local')
        peer = User.objects.create_user(username='gc_b', email='gc_b@test.local')
        chat = PrivateChat.objects.create(user1=user, user2=peer)
        with patch('apps.social.application.conversations.enqueue_event'):
            message, _ = service.send_message(chat, user, {'text': 'Referenced', 'client_message_id': 'gc-message'})
        self.file = Attachment.objects.create(message=message, type='file', file=ContentFile(b'keep', name='keep.bin'),
            file_name='keep.bin', file_size=4, mime_type='application/octet-stream')
        self.age(Path(self.file.file.path))
        self.orphan = self.root / 'attachments' / 'orphan.bin'
        self.orphan.write_bytes(b'quarantine bytes'); self.age(self.orphan)
        self.recent = self.root / 'attachments' / 'upload-in-progress.bin'
        self.recent.write_bytes(b'young')

    def age(self, path):
        old = time.time() - 48 * 3600
        os.utime(path, (old, old))

    def command(self, *args):
        output = io.StringIO(); call_command('gc_chat_files', *args, stdout=output)
        return json.loads(output.getvalue())

    def test_dry_run_and_maintenance_guard_leave_all_files(self):
        result = self.command()
        self.assertEqual((True, 1, 0), (result['dry_run'], result['eligible'], result['collected']))
        with self.assertRaises(CommandError):
            self.command('--apply')
        for age in ('nan', 'inf', '23'):
            with self.subTest(age=age), self.assertRaises(CommandError):
                self.command('--older-than-hours', age, '--apply', '--writers-stopped')
        self.assertTrue(self.orphan.exists())
        self.assertTrue(chat_private_storage.exists(self.file.file.name))
        self.assertTrue(self.recent.exists())

    def test_collection_and_idempotent_restore_preserve_bytes(self):
        result = self.command('--apply', '--writers-stopped')
        self.assertEqual(1, result['collected'])
        self.assertFalse(self.orphan.exists())
        self.assertTrue(chat_private_storage.exists(self.file.file.name))
        self.assertTrue(self.recent.exists())
        self.assertEqual(1, self.command('--restore', result['run_id'], '--writers-stopped')['restored'])
        self.assertEqual(b'quarantine bytes', self.orphan.read_bytes())
        self.assertEqual(0, self.command('--restore', result['run_id'], '--writers-stopped')['restored'])

    def test_restore_conflict_does_not_replace_current_bytes(self):
        result = self.command('--apply', '--writers-stopped')
        self.orphan.write_bytes(b'new current bytes')
        with self.assertRaises(CommandError):
            self.command('--restore', result['run_id'], '--writers-stopped')
        self.assertEqual(b'new current bytes', self.orphan.read_bytes())

    def test_invalid_paths_and_symlinks_are_rejected(self):
        from .chat_file_gc import safe_path
        for name in ('../outside.bin', '/outside.bin', 'attachments\\outside.bin'):
            with self.subTest(name=name), self.assertRaises(CommandError):
                safe_path(self.root, name)
        external = Path(self.directory.name) / 'outside.bin'; external.write_bytes(b'outside')
        link = self.root / 'attachments' / 'link.bin'; link.symlink_to(external)
        with self.assertRaises(CommandError):
            safe_path(self.root, 'attachments/link.bin')
        result = self.command('--apply', '--writers-stopped')
        self.assertEqual(1, result['collected'])
        self.assertEqual(b'outside', external.read_bytes())
