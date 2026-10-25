import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('native_build', Path(__file__).parent / 'native/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class InstallerCacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for file in ('windows/Program.cs', 'android/Main.java', 'desktop/icon.png',
                     'desktop/main.cjs', 'build_windows.py', 'build_android.py',
                     'build.py', 'builder.Dockerfile'):
            path = self.root / 'source' / file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture')
        self.source = patch.object(build, 'ROOT', self.root / 'source')
        self.source.start()
        self.addCleanup(self.source.stop)
        self.environment = patch.dict(os.environ, {'DATA_DIR': str(self.root / 'data')})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.args = SimpleNamespace(target='windows', site_url='https://example.org',
                                    version='0.1.0', output=self.root / 'output.exe')

    def test_reuse_verifies_bytes_and_rejects_corruption(self):
        self.args.output.write_bytes(b'installer fixture' * 100)
        original = self.args.output.read_bytes()
        build.remember(self.args)
        self.args.output.unlink()
        self.assertTrue(build.cached(self.args))
        self.assertEqual(self.args.output.read_bytes(), original)
        build.artifact_cache(self.args).write_bytes(b'corrupted')
        self.assertFalse(build.cached(self.args))

    def test_origin_version_and_used_source_invalidate_cache(self):
        first = build.artifact_cache(self.args)
        self.args.site_url = 'https://other.example.org'
        self.assertNotEqual(first, build.artifact_cache(self.args))
        self.args.site_url = 'https://example.org'
        self.args.version = '0.2.0'
        self.assertNotEqual(first, build.artifact_cache(self.args))
        self.args.version = '0.1.0'
        (build.ROOT / 'android/Main.java').write_text('unrelated change')
        self.assertEqual(first, build.artifact_cache(self.args))
        (build.ROOT / 'windows/Program.cs').write_text('changed')
        self.assertNotEqual(first, build.artifact_cache(self.args))

    def test_android_signing_key_invalidates_cache(self):
        self.args.target = 'android'
        first = build.artifact_cache(self.args)
        key = self.root / 'data/native_signing/android-release.jks'
        key.parent.mkdir(parents=True)
        key.write_bytes(b'private fixture')
        self.assertNotEqual(first, build.artifact_cache(self.args))
        self.assertIsNone(build.artifact_cache(SimpleNamespace(target='ios')))


if __name__ == '__main__':
    unittest.main()
