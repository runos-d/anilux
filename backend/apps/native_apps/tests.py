import tempfile
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from asgiref.sync import async_to_sync

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from .releases import TARGETS, identity, public_manifest, read_manifest, release_dir, schedule_build, site_url, write_manifest
from .views import DownloadView, ReleasesView


class NativeReleaseTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = override_settings(DATA_DIR=Path(self.temp.name), SITE_URL='https://example.org',
            NATIVE_APP_SITE_URL='', SEO_PUBLIC_ORIGIN='', NATIVE_APP_VERSION='0.1.0',
            CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
        self.config.enable()
        self.addCleanup(self.config.disable)
        cache.clear()

    def test_domain_changes_release_identity(self):
        first = identity()[0]
        with override_settings(SITE_URL='https://new.example.org'):
            self.assertNotEqual(first, identity()[0])
        self.assertEqual(site_url('https://EXAMPLE.org/'), 'https://example.org')
        self.assertEqual(site_url('https://EXAMPLE.org:443/'), 'https://example.org')
        self.assertEqual(site_url('https://пример.рф'), 'https://xn--e1afmkfd.xn--p1ai')
        with override_settings(SEO_PUBLIC_ORIGIN='https://current.example.org'):
            self.assertEqual(site_url(), 'https://current.example.org')
        for invalid in ('file:///private', 'https://user:secret@example.org', 'https://example.org/path'):
            with self.assertRaises(ValueError): site_url(invalid)

    @patch('apps.native_apps.tasks.build_release.apply_async')
    def test_startup_is_deduplicated_and_ready_release_is_reused(self, publish):
        key = schedule_build()
        schedule_build()
        publish.assert_called_once()
        self.assertEqual(publish.call_args.kwargs['queue'], 'native_builds')
        self.assertEqual(read_manifest(key)['status'], 'queued')
        cache.clear()
        artifacts = {}
        for target, (_, suffix) in TARGETS.items():
            name = 'anilux-'+target+suffix
            (release_dir(key) / name).write_bytes(b'x'*4096)
            artifacts[target] = {'status': 'ready', 'filename': name}
        write_manifest(key, {'status': 'ready', 'artifacts': artifacts})
        schedule_build()
        publish.assert_called_once()

    @patch('apps.native_apps.tasks.build_release.apply_async', side_effect=ConnectionError)
    def test_broker_failure_does_not_leave_permanent_lock(self, publish):
        for _ in range(2):
            with self.assertRaises(ConnectionError): schedule_build()
        self.assertEqual(publish.call_count, 2)
        self.assertEqual(read_manifest(identity()[0])['status'], 'failed')

    def artifact(self):
        key = identity()[0]
        write_manifest(key, {'status': 'ready', 'artifacts': {'windows': {
            'status': 'ready', 'filename': 'anilux.exe', 'size': 4096, 'sha256': 'a'*64}}})
        (release_dir(key) / 'anilux.exe').write_bytes(b'MZ'+b'0'*4094)
        return key

    def test_only_existing_installers_are_public(self):
        key = self.artifact()
        self.assertIsNotNone(public_manifest()['artifacts'][0]['url'])
        (release_dir(key) / 'anilux.exe').unlink()
        row = public_manifest()['artifacts'][0]
        self.assertIsNone(row['url'])
        self.assertNotEqual(row['status'], 'ready')

    def test_download_does_not_expose_private_logs_or_keys(self):
        key = self.artifact()
        factory = APIRequestFactory()
        for name in ('windows.log', 'manifest.json', '../android-release.jks', 'missing.exe'):
            response = DownloadView.as_view()(factory.get('/'), key=key, name=name)
            self.assertEqual(response.status_code, 404)
        response = DownloadView.as_view()(factory.get('/'), key=key, name='anilux.exe')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        async def consume():
            return b''.join([chunk async for chunk in response.streaming_content])
        self.assertEqual(async_to_sync(consume)(), b'MZ'+b'0'*4094)
        response.close()

    @patch('apps.native_apps.tasks.build_release.apply_async')
    def test_configuring_mac_runner_schedules_previously_unsigned_ios(self, publish):
        key=identity()[0]
        artifacts={}
        release_dir(key).mkdir(parents=True)
        for target, (_, suffix) in TARGETS.items():
            name=target+suffix
            (release_dir(key)/name).write_bytes(b'x'*4096)
            artifacts[target]={'status':'ready','filename':name}
        artifacts['ios']={'status':'requires_signing'}
        write_manifest(key,{'status':'ready','artifacts':artifacts})
        with patch.dict(os.environ,{'NATIVE_MAC_BUILD_COMMAND':''}): schedule_build()
        publish.assert_not_called()
        with patch.dict(os.environ,{'NATIVE_MAC_BUILD_COMMAND':'owner-configured-runner'}): schedule_build()
        publish.assert_called_once()

    @patch('apps.native_apps.views.schedule_build')
    def test_visitors_cannot_trigger_builds(self, schedule):
        factory = APIRequestFactory()
        self.assertIn(ReleasesView.as_view()(factory.post('/')).status_code, (401, 403))
        schedule.assert_not_called()
        request = factory.post('/')
        force_authenticate(
            request,
            user=SimpleNamespace(pk=1, is_authenticated=True, is_staff=True, is_superuser=False),
        )
        self.assertEqual(ReleasesView.as_view()(request).status_code, 202)
        schedule.assert_called_once_with(force=True)
