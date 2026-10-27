from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from apps.anime.models import Anime, Franchise
from apps.anime.application.franchise_sync import sync_franchise
from apps.anime.application.catalog_visibility import hidden_anime


class AdminCatalogTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(username='catalog-admin', email='admin@example.test', is_staff=True)
        self.reader = get_user_model().objects.create_user(username='catalog-reader', email='reader@example.test')
        self.a = Anime.objects.create(title_ru='Тестовая часть', title_en='Part', year=2020, shikimori_id=101, score=8,
                                      genres=['Драма'], studios=['Studio'], kind='tv', status='released')
        self.b = Anime.objects.create(title_ru='Следующая часть', year=2021, shikimori_id=102, score=6,
                                      genres=['Драма'], kind='movie', status='released')
        self.client.force_authenticate(self.admin)

    def request(self, method, url, data=None):
        with self.captureOnCommitCallbacks(execute=True):
            return getattr(self.client, method)('/api/anime/admin/' + url, data=data or {}, format='json')

    def rule(self, kind, value):
        response = self.request('post', 'catalog-rules/', {'rule_type': kind, 'value': value})
        self.assertEqual(201, response.status_code, response.data)
        return response.data['id']

    def test_permissions_cover_reads_and_writes(self):
        for user in (None, self.reader):
            self.client.force_authenticate(user)
            for url in ('franchises/', 'anime-search/', 'catalog-options/', 'catalog-rules/', 'catalog-hidden/'):
                self.assertIn(self.request('get', url).status_code, (401, 403), url)
                self.assertIn(self.request('post', url).status_code, (401, 403), url)

    def test_franchise_crud_move_reorder_and_aggregate_cleanup(self):
        response = self.request('post', 'franchises/', {'name': 'Ручная франшиза', 'description': 'Тест'})
        self.assertEqual(201, response.status_code, response.data)
        pk = response.data['id']
        old = Franchise.objects.create(name='Старая')
        self.a.franchise = old; self.a.save()
        for part in (self.a, self.b):
            response = self.request('post', f'franchises/{pk}/add-anime/', {'anime_id': part.pk})
            self.assertEqual(200, response.status_code, response.data)
        old.refresh_from_db(); self.assertIsNone(old.score)
        self.assertIsNone(old.year_start)
        detail = self.request('get', f'franchises/{pk}/').data
        self.assertEqual(2, detail['parts_count']); self.assertEqual(7, detail['score'])
        for ids in ([self.a.pk, self.a.pk], [self.a.pk], [self.a.pk, 999999]):
            self.assertEqual(400, self.request('post', f'franchises/{pk}/reorder/', {'anime_ids': ids}).status_code)
        response = self.request('post', f'franchises/{pk}/reorder/', {'anime_ids': [self.b.pk, self.a.pk]})
        self.assertEqual([self.b.pk, self.a.pk], [row['id'] for row in response.data['entries']])
        self.assertEqual(200, self.request('patch', f'franchises/{pk}/', {'description': ''}).status_code)
        self.assertEqual(200, self.request('post', f'franchises/{pk}/remove-anime/', {'anime_id': self.b.pk}).status_code)
        self.assertEqual(404, self.request('post', f'franchises/{pk}/remove-anime/', {'anime_id': self.b.pk}).status_code)
        self.assertEqual(204, self.request('delete', f'franchises/{pk}/').status_code)
        self.a.refresh_from_db(); self.assertIsNone(self.a.franchise_id); self.assertTrue(self.a.franchise_manual)

    def test_manual_membership_and_order_survive_provider_sync(self):
        franchise = Franchise.objects.create(name='Ручная')
        self.a.franchise = franchise; self.a.franchise_manual = True; self.a.franchise_order = 10; self.a.save()
        graph = {'nodes': [{'id': 101, 'name': 'Provider', 'date': 1}, {'id': 102, 'name': 'Provider 2', 'date': 2}]}
        with patch('apps.anime.application.franchise_sync.shikimori_api.get_franchise', return_value=graph):
            result = sync_franchise(102)
        self.assertTrue(result['success'])
        self.a.refresh_from_db(); self.assertEqual((franchise.pk, 10), (self.a.franchise_id, self.a.franchise_order))

    @patch('apps.anime.application.franchise_sync.sync_franchises.delay')
    def test_rebuild_queues_provider_sync_and_keeps_manual_links(self, delay):
        delay.return_value.id = 'task-1'
        manual = Franchise.objects.create(name='Ручная')
        self.a.franchise = manual; self.a.franchise_manual = True; self.a.save()
        response = self.request('post', 'franchises/rebuild/')
        self.assertEqual(202, response.status_code, response.data)
        self.a.refresh_from_db()
        self.assertEqual(manual.pk, self.a.franchise_id)
        kwargs = delay.call_args.kwargs
        self.assertEqual(100, kwargs['limit'])
        self.assertTrue(kwargs['continue_until_done'])
        self.assertTrue(kwargs['refresh_provider'])
        self.assertEqual(response.data['rebuild_id'], kwargs['rebuild_id'])
        self.assertEqual(1, kwargs['total'])
        self.assertTrue(kwargs['refresh_before'])
        status = self.request('get', f"franchises/rebuild-status/{response.data['rebuild_id']}/")
        self.assertEqual(200, status.status_code)
        self.assertEqual('queued', status.data['state'])

    def test_catalog_cache_invalidated_and_availability_preserved(self):
        public = APIClient()
        self.assertEqual(2, public.get('/api/anime/').data['count'])
        self.request('post', 'catalog-hidden/', {'anime_id': self.a.pk})
        self.assertEqual(1, public.get('/api/anime/').data['count'])
        self.a.refresh_from_db(); self.assertTrue(self.a.is_available)
        self.assertEqual(200, public.get(f'/api/anime/{self.a.slug}/').status_code)
        self.request('post', f'catalog-hidden/{self.a.pk}/restore/')
        self.assertEqual(2, public.get('/api/anime/').data['count'])

    def test_overlapping_rules_restore_exception_reapply_and_manual_hide(self):
        genre = self.rule('genre', 'Драма')
        kind = self.rule('kind', 'tv')
        self.assertEqual(2, hidden_anime().count())
        self.request('delete', f'catalog-rules/{genre}/')
        self.assertEqual([self.a.pk], list(hidden_anime().values_list('pk', flat=True)))
        self.request('post', f'catalog-hidden/{self.a.pk}/restore/')
        self.assertEqual(0, hidden_anime().count())
        self.request('post', f'catalog-rules/{kind}/')
        self.assertEqual(1, hidden_anime().count())
        self.request('post', 'catalog-hidden/', {'anime_id': self.b.pk})
        self.request('delete', f'catalog-rules/{kind}/')
        self.assertEqual([self.b.pk], list(hidden_anime().values_list('pk', flat=True)))

    def test_rules_cover_new_imports_and_each_filter(self):
        self.rule('studio', 'Studio')
        new = Anime.objects.create(title_ru='Новая часть', studios=['Studio'])
        self.assertTrue(hidden_anime().filter(pk=new.pk).exists())
        franchise = Franchise.objects.create(name='Название франшизы')
        self.b.franchise = franchise; self.b.save()
        self.rule('franchise', 'франшизы')
        self.assertTrue(hidden_anime().filter(pk=self.b.pk).exists())
        self.rule('title', 'Part')
        self.assertEqual(400, self.request('post', 'catalog-rules/', {'rule_type': 'bad', 'value': 'abc'}).status_code)
        self.assertEqual(409, self.request('post', 'catalog-rules/', {'rule_type': 'title', 'value': 'Part'}).status_code)
        self.assertEqual(400, self.request('post', 'catalog-hidden/', {'anime_id': -1}).status_code)
        self.assertEqual(400, self.request('get', 'catalog-hidden/', {'page': 'bad'}).status_code)
        self.assertEqual(['Studio'], self.request('get', 'catalog-options/').data['studios'])
        self.assertGreater(len(self.request('get', 'anime-search/', {'q': 'часть'}).data['results']), 0)

    def test_candidate_graph_excludes_manga_orders_anime_and_keeps_other_search_hits(self):
        from apps.anime.presentation.views.anime_views import KodikSearchCandidatesView
        graph = {'nodes': [
            {'id': 102, 'name': 'Следующая часть', 'date': 2, 'url': '/animes/102'},
            {'id': 103, 'name': 'Манга', 'date': 0, 'url': '/mangas/103'},
            {'id': 101, 'name': 'Тестовая часть', 'date': 1, 'url': '/animes/101'},
        ]}
        results = [{'shikimori_id': 101, 'year': 2020}, {'shikimori_id': 104, 'title': 'Другая франшиза', 'year': 2021}]
        provider = lambda sid: {'id': f'serial-{sid}', 'year': 2020 if sid == '101' else 2021, 'title': 'Часть'}
        with patch('apps.anime.presentation.views.anime_views.anime_service.get_franchise', return_value=graph), \
             patch('apps.anime.presentation.views.anime_views.anime_service.get_franchise_slug', return_value=None), \
             patch('apps.anime.presentation.views.anime_views.anime_service.search_by_shikimori_id', side_effect=provider):
            groups = KodikSearchCandidatesView()._build_franchise_groups(results)
        self.assertEqual([101, 102], [item['shikimori_id'] for item in groups[0]['items']])
        self.assertEqual(self.a.slug, groups[0]['items'][0]['anime_slug'])
        self.assertEqual(2020, groups[0]['year'])
        self.assertEqual(104, groups[1]['items'][0]['shikimori_id'])
