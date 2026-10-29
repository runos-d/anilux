from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from core.object_migration import mirror_file, source_path


class ObjectMigrationTests(TestCase):
    def test_dry_run_never_calls_storage_and_copy_is_verified_without_source_change(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'private.txt'
            path.write_bytes(b'private bytes')
            dry = mirror_file(None, bucket='private-test', root=folder, name=path.name, domain='chat')
            self.assertFalse(dry['applied'])
            def upload(source, bucket, key, **kwargs):
                self.assertEqual(Path(source).read_bytes(), b'private bytes')
                self.assertNotIn('ACL', kwargs['ExtraArgs'])
                self.assertEqual(kwargs['ExtraArgs']['CacheControl'], 'private, no-store')
            remote = BytesIO(b'private bytes')
            result = mirror_file(SimpleNamespace(upload_file=upload, get_object=lambda **kw: {'Body': remote}),
                bucket='private-test', root=folder, name=path.name, domain='chat', apply=True)
            self.assertTrue(result['verified'])
            self.assertTrue(remote.closed)
            self.assertEqual(path.read_bytes(), b'private bytes')
            self.assertEqual(dry['object_key'], result['object_key'])

    def test_corruption_never_produces_verified_mapping(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'data'
            path.write_bytes(b'original')
            client = SimpleNamespace(upload_file=lambda *a, **kw: None,
                                     get_object=lambda **kw: {'Body': BytesIO(b'corrupt')})
            with self.assertRaises(RuntimeError):
                mirror_file(client, bucket='private-test', root=folder, name='data', domain='post', apply=True)
            self.assertEqual(path.read_bytes(), b'original')

    def test_path_escape_and_absolute_names_are_rejected(self):
        with TemporaryDirectory() as folder:
            for name in ('../secrets', '/secrets', 'folder\\secrets'):
                with self.assertRaises(ValueError):
                    source_path(folder, name)
