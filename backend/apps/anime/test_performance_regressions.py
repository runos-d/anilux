import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from asgiref.sync import async_to_sync
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.core.cache import cache
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework.exceptions import Throttled
from redis.exceptions import ConnectionError as RedisConnectionError
from apps.anime.models import Anime, Franchise, BackgroundJob
from apps.users.infrastructure.models.users import User, PrivacySettings


class PerformanceRegressions(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create([User(username=f'perf-{i}', email=f'perf-{i}@example.test', password='!') for i in range(25)])
        cls.viewer = User.objects.first()
        PrivacySettings.objects.bulk_create([PrivacySettings(user=user, who_can_see_profile_photo='contacts') for user in User.objects.all()])
        Franchise.objects.bulk_create([Franchise(name=f'Франшиза {i}', slug=f'perf-{i}') for i in range(20)])
        Anime.objects.bulk_create([Anime(title_ru=f'Аниме {i}-{j}', slug=f'perf-{i}-{j}', is_available=True, has_cyrillic=True,
            shikimori_id=i * 10 + j + 1, year=2024, episodes=12, franchise_id=pk)
            for i, pk in enumerate(Franchise.objects.values_list('pk', flat=True)) for j in range(2)])
        cls.anime = Anime.objects.first()

    def setUp(self):
        cache.clear()
        self.api = APIClient()

    def test_missing_slug_does_not_scan_titles(self):
        with patch('apps.anime.presentation.views.anime_views.legacy_anime_slug') as legacy:
            with CaptureQueriesContext(connection) as sql:
                response = self.api.get('/api/anime/no-such-title/')
        self.assertEqual(response.status_code, 404)
        legacy.assert_not_called()
        self.assertLessEqual(len(sql), 4)

    def test_franchise_page_has_constant_query_budget(self):
        for size in (1, 20):
            with CaptureQueriesContext(connection) as sql:
                response = self.api.get(f'/api/anime/franchises/?page_size={size}')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.data['results']), size)
            self.assertLessEqual(len(sql), 5)

    def test_contact_only_avatar_search_is_batched(self):
        self.api.force_authenticate(self.viewer)
        with CaptureQueriesContext(connection) as sql:
            response = self.api.get('/api/users/search/?search=perf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 20)
        self.assertLessEqual(len(sql), 3)

    def test_catalog_page_size_is_bounded(self):
        Anime.objects.bulk_create([Anime(title_ru=f'Cap {i}', slug=f'cap-{i}', is_available=True, has_cyrillic=True,
            shikimori_id=10000+i, year=2024, episodes=12) for i in range(110)])
        response = self.api.get('/api/anime/?page_size=500&group_franchises=false')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 100)

    def test_invalid_pagination_never_returns_500(self):
        for query in ('page_size=0', 'page=-1', 'page_size=abc', 'page_size=-5'):
            response = self.api.get('/api/anime/franchises/?' + query)
            self.assertIn(response.status_code, (200, 400))

    def test_detail_does_not_call_external_provider(self):
        with patch('apps.anime.presentation.views.anime_views.anime_service.search_by_shikimori_id') as provider:
            for _ in range(3):
                self.assertEqual(self.api.get(f'/api/anime/{self.anime.pk}/').status_code, 200)
        provider.assert_not_called()

    def test_online_snapshot_reads_only_requested_ids(self):
        self.api.force_authenticate(self.viewer)
        with patch('core.online_status.online_status.get_online_users') as all_online, patch(
            'core.online_status.online_status.get_users_data', return_value={self.viewer.pk: {'user_id': self.viewer.pk}}
        ) as batch:
            response = self.api.get(f'/api/users/online/?ids={self.viewer.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['results'][0]['is_online'])
        all_online.assert_not_called()
        batch.assert_called_once()

    def test_presence_listing_uses_index_and_one_mget(self):
        from core.online_status import online_status
        client = Mock()
        client.zrangebyscore.return_value = ['user_online:1', 'user_online:2']
        client.mget.return_value = ['{"user_id":1}', '{"user_id":2}']
        with patch.object(online_status, '_get_client', return_value=client):
            self.assertEqual(len(online_status.get_online_users()), 2)
        client.keys.assert_not_called()
        client.get.assert_not_called()
        client.mget.assert_called_once()

    def test_revocation_uses_indexed_session_ownership(self):
        from apps.users.application.token_sessions import revoke_sessions
        stores = []
        for user in User.objects.all()[:4]:
            session = SessionStore()
            session['_auth_user_id'] = str(user.pk)
            session['_auth_user_hash'] = user.get_session_auth_hash()
            session.save()
            stores.append((user, session.session_key))
        with patch.object(Session, 'get_decoded', side_effect=AssertionError('Global session decode')):
            revoke_sessions(self.viewer)
        for user, key in stores:
            self.assertEqual(Session.objects.filter(session_key=key).exists(), user.pk != self.viewer.pk)

    def test_nonrecipient_socket_does_not_query_authorization(self):
        from apps.social.application.consumers import GlobalEventsConsumer
        consumer = GlobalEventsConsumer()
        consumer.user_id = self.viewer.pk
        consumer.authorized = AsyncMock()
        async_to_sync(consumer._send_event_to_client)({'type': 'new_message', 'target_users': [-1], 'data': {}})
        consumer.authorized.assert_not_awaited()

    def test_addressed_events_use_user_groups(self):
        from core.redis_events import event_publisher
        layer = SimpleNamespace(group_send=AsyncMock())
        client = Mock()
        with patch.object(event_publisher, '_get_client', return_value=client), patch('channels.layers.get_channel_layer', return_value=layer):
            event_publisher.publish_event('new_message', {}, target_users=[self.viewer.pk])
        client.publish.assert_not_called()
        self.assertEqual(layer.group_send.await_args.args[0], f'user_{self.viewer.pk}')

    def test_stream_enqueues_instead_of_running_ffmpeg(self):
        with patch('apps.anime.application.background_tasks.prepare_download.apply_async') as publish, patch('subprocess.run') as process:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.api.get(f'/api/anime/{self.anime.pk}/stream/')
        self.assertEqual(response.status_code, 202)
        publish.assert_called_once()
        process.assert_not_called()

    def test_media_format_is_not_treated_as_a_renderer(self):
        with patch('apps.anime.application.background_tasks.prepare_download.apply_async'):
            for media_format in ('mp4', 'mp3', 'audio'):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.api.get(f'/api/anime/{self.anime.pk}/stream/?format={media_format}')
                self.assertEqual(response.status_code, 202)
        response = self.api.get(f'/api/anime/{self.anime.pk}/clip/?format=mp4')
        self.assertEqual(response.status_code, 401)

    def test_download_queue_has_global_admission_cap(self):
        from apps.anime.application.background_work import enqueue
        BackgroundJob.objects.bulk_create([BackgroundJob(kind='download', key=str(i), payload={}) for i in range(20)])
        task = Mock()
        with self.assertRaises(Throttled):
            enqueue('download', {'another': True}, task)
        task.apply_async.assert_not_called()

    def test_ready_file_is_async_and_supports_range(self):
        from apps.anime.presentation.views.prepared_downloads import job_file
        with tempfile.TemporaryDirectory() as root, override_settings(DOWNLOAD_ROOT=root):
            job = BackgroundJob.objects.create(kind='download', key='range', status='ready',
                payload={'anime_id': self.anime.pk, 'format': 'mp4', 'episode': 1})
            job_file(job).write_bytes(b'0123456789')
            response = self.api.get(f'/api/anime/{self.anime.pk}/stream/?job_id={job.pk}', HTTP_RANGE='bytes=2-4')
            self.assertEqual(response.status_code, 206)
            self.assertTrue(response.is_async)
            self.assertEqual(response['Content-Range'], 'bytes 2-4/10')
            async def consume():
                return b''.join([chunk async for chunk in response.streaming_content])
            self.assertEqual(async_to_sync(consume)(), b'234')

    def test_download_worker_limits_process_size_and_time(self):
        from apps.anime.application.background_tasks import prepare_download
        with tempfile.TemporaryDirectory() as root, override_settings(DOWNLOAD_ROOT=root):
            job = BackgroundJob.objects.create(kind='download', key='worker', payload={'anime_id': self.anime.pk,
                'episode': 1, 'season': 1, 'format': 'mp4', 'quality': '720', 'full': True, 'start': 0})
            def run(cmd, **kwargs):
                self.assertIn('-fs', cmd)
                self.assertIn('-t', cmd)
                self.assertEqual(kwargs['timeout'], 180)
                Path(cmd[-1]).write_bytes(b'video')
                return SimpleNamespace(returncode=0)
            with patch('apps.anime.application.anime_service.anime_service.get_anime_m3u8', return_value='https://example.test/video.m3u8'), patch('subprocess.run', side_effect=run), patch('shutil.disk_usage', return_value=SimpleNamespace(free=10**10)):
                prepare_download.run(str(job.pk))
            job.refresh_from_db()
            self.assertEqual(job.status, 'ready')
            self.assertEqual(job.result['bytes'], 5)

    def test_import_returns_a_job_before_provider_work(self):
        with patch('apps.anime.application.background_tasks.import_requested_catalog.apply_async'), patch(
            'apps.anime.presentation.views.anime_views.KodikUserAddView._import_one'
        ) as provider:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.api.post('/api/anime/kodik/user-add/', {'shikimori_ids': [20000]}, format='json')
        self.assertEqual(response.status_code, 202)
        provider.assert_not_called()

    def test_readiness_fails_for_dependency_failure(self):
        with patch('config.health.check_database', side_effect=RuntimeError('down')):
            response = self.api.get('/health/ready/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['dependencies']['database'], 'unavailable')
        self.assertEqual(self.api.get('/health/live/').status_code, 200)

    def test_cache_failure_returns_bounded_503(self):
        from core.cache_backend import CacheUnavailable
        class Probe(APIView):
            permission_classes = [AllowAny]
            throttle_classes = [AnonRateThrottle]
            def get(self, request): return Response({'ok': True})
        with patch.object(AnonRateThrottle.cache, 'get', side_effect=CacheUnavailable()):
            response = Probe.as_view()(APIRequestFactory().get('/probe/'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '5')

    def test_cache_circuit_does_not_repeat_failed_network_call(self):
        from core.cache_backend import CircuitRedisCache, CacheUnavailable
        backend = CircuitRedisCache('redis://localhost:1/0', {'OPTIONS': {}})
        with patch('django_redis.cache.RedisCache.get', side_effect=RedisConnectionError()) as network:
            second_thread_backend = CircuitRedisCache('redis://localhost:1/0', {'OPTIONS': {}})
            for instance in (backend, second_thread_backend):
                with self.assertRaises(CacheUnavailable): instance.get('key')
        self.assertEqual(network.call_count, 1)

    def test_all_feed_modes_page_without_global_snapshots(self):
        from rest_framework.request import Request
        from apps.social.application.post_feed import page
        from apps.social.infrastructure.models.social import Post
        from apps.social.infrastructure.models.post_lifecycle import PostFeedSnapshot
        Post.objects.bulk_create([Post(author=self.viewer, text=f'Post {i}', likes_count=i, comments_count=i % 3) for i in range(60)])
        for mode, sort in [('extended', 'new'), ('extended', 'old'), ('extended', 'best'), ('extended', 'discussed'), ('weighted', 'new'), ('hot', 'new')]:
            def request(cursor=None):
                values = {'sort': sort, 'page_size': 20}
                if cursor:
                    values['cursor'] = cursor
                result = Request(APIRequestFactory().get('/feed/', values))
                result.user = self.viewer
                return result
            first = page(request(), mode)
            second = page(request(first['next_cursor']), mode)
            self.assertEqual(len(first['results']), 20)
            self.assertEqual(len(second['results']), 20)
            self.assertFalse({row['id'] for row in first['results']} & {row['id'] for row in second['results']})
        self.assertEqual(PostFeedSnapshot.objects.count(), 0)

    def test_optional_metadata_negative_cache_is_bounded(self):
        from apps.anime.application.metadata_tasks import refresh_missing_screenshots
        Anime.objects.update(screenshots=['existing'])
        Anime.objects.filter(pk=self.anime.pk).update(screenshots=[])
        with patch('apps.anime.application.metadata_tasks.anime_service.search_by_shikimori_id', return_value=None) as provider:
            for _ in range(3):
                refresh_missing_screenshots.run()
        provider.assert_called_once()

    def test_legacy_title_alias_survives_without_catalog_scan(self):
        anime = Anime.objects.create(title_ru='Новая звезда', slug='custom-unrelated', is_available=True)
        response = self.api.get('/api/anime/novaya-zvezda/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], anime.pk)

    def test_asgi_admission_rejects_overload_and_releases_slots(self):
        from core.asgi_limits import BoundedApplication
        async def run():
            entered, release = asyncio.Event(), asyncio.Event()
            async def application(scope, receive, send):
                entered.set()
                await release.wait()
            bounded = BoundedApplication(application, http_limit=1)
            first = asyncio.create_task(bounded({'type': 'http'}, AsyncMock(), AsyncMock()))
            await entered.wait()
            messages = []
            async def collect(value): messages.append(value)
            await bounded({'type': 'http'}, AsyncMock(), collect)
            self.assertEqual(messages[0]['status'], 503)
            release.set()
            await first
            self.assertEqual(bounded.active['http'], 0)
        async_to_sync(run)()
