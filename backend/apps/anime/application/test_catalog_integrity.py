from unittest.mock import patch
from pathlib import Path
from datetime import date
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient
from apps.anime.models import Anime, Franchise
from apps.anime.application.release_year import release_year, premiere_date
from apps.anime.application.franchise_sync import sync_franchise, sync_franchises
from apps.anime.application import kodik_dump_service as dumps


class ReleaseYearTests(SimpleTestCase):
    def test_title_premiere_wins_over_series_metadata(self):
        record = {'year': 2026, 'material_data': {'year': 2012, 'aired_at': '2026-03-19'}}
        self.assertEqual(2026, release_year(record))
        self.assertEqual(date(2026, 3, 19), premiere_date(record))
        record['year'] = 2025
        self.assertEqual(2026, release_year(record))

    def test_invalid_dates_and_years_fall_back_without_inventing_a_year(self):
        self.assertEqual(2026, release_year({'year': '2026', 'material_data': {'aired_at': '2026-99-00', 'year': 2012}}))
        self.assertEqual(2012, release_year({'year': 'bad', 'material_data': {'year': '2012'}}))
        self.assertIsNone(release_year({'year': True, 'material_data': {'year': 0}}))

    def test_dump_corrects_known_bug_but_keeps_manual_year(self):
        light = dumps._light({'year': 2026, 'material_data': {'year': 2012, 'aired_at': '2026-03-19'}})
        release_fields = {'release_date': date(2026, 3, 19), 'release_date_string': '2026-03-19'}
        for year, expected in ((2012, {'year': 2026, **release_fields}), (2025, release_fields)):
            cur = dumps._Cur(1, '', '', None, None, '', None, year)
            group = dumps._new_group(); dumps._collect(group, light, cur)
            self.assertEqual(expected, dumps.plan_update(cur, group, lambda value: value))


class FranchiseTests(TestCase):
    def setUp(self):
        self.older = Anime.objects.create(shikimori_id=14719, title_ru='ДжоДжо', year=2012)
        self.newer = Anime.objects.create(shikimori_id=61469, title_ru='Стальной шар', year=2026)
        self.graph = {'nodes': [
            {'id': 61469, 'name': 'ДжоДжо: Стальной шар', 'date': 1773867600, 'weight': 3, 'url': '/animes/61469'},
            {'id': 14719, 'name': 'ДжоДжо', 'date': 1349467200, 'weight': 3, 'url': '/animes/14719'},
            {'id': 111, 'name': 'Манга', 'date': 100, 'url': '/mangas/111'},
        ]}

    def test_repeat_graph_from_another_anchor_reuses_franchise_and_catalog_groups_before_pagination(self):
        with patch('apps.anime.application.franchise_sync.shikimori_api.get_franchise', return_value=self.graph):
            first = sync_franchise(61469); second = sync_franchise(14719)
        self.assertEqual(first['franchise_id'], second['franchise_id'])
        self.older.refresh_from_db(); self.newer.refresh_from_db()
        self.assertEqual((0, 1), (self.older.franchise_order, self.newer.franchise_order))
        self.assertEqual((2012, 2026), (self.newer.franchise.year_start, self.newer.franchise.year_end))
        client = APIClient()
        response = client.get('/api/anime/', {'group_franchises': 'true', 'page_size': 1})
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(1, response.data['count'])
        self.assertEqual(1, len(response.data['results']))

    def test_failed_or_wrong_graph_does_not_destroy_existing_links(self):
        with patch('apps.anime.application.franchise_sync.shikimori_api.get_franchise', return_value=self.graph):
            sync_franchise(61469)
        self.newer.refresh_from_db(); original = self.newer.franchise_id
        for response in (None, {'nodes': [{'id': 77}]}):
            with patch('apps.anime.application.franchise_sync.shikimori_api.get_franchise', return_value=response):
                self.assertFalse(sync_franchise(61469)['success'])
        self.newer.refresh_from_db()
        self.assertEqual(original, self.newer.franchise_id)

    def test_provider_graph_with_one_local_part_does_not_create_a_franchise(self):
        self.newer.delete()
        stale = Franchise.objects.create(name='Одиночная')
        self.older.franchise = stale
        self.older.save(update_fields=['franchise'])
        with patch('apps.anime.application.franchise_sync.shikimori_api.get_franchise', return_value=self.graph):
            result = sync_franchise(self.older.shikimori_id)
        self.older.refresh_from_db()
        self.assertEqual(0, result['linked'])
        self.assertIsNone(self.older.franchise_id)

    def test_missing_provider_anime_is_checked_without_stopping_rebuild(self):
        stale = Franchise.objects.create(name='Удалённое аниме')
        self.older.franchise = stale
        self.older.save(update_fields=['franchise'])
        with patch('apps.anime.application.franchise_sync.shikimori_api.get_franchise', return_value={'nodes': [], 'links': []}):
            result = sync_franchise(self.older.shikimori_id)
        self.older.refresh_from_db()
        self.assertTrue(result['success'])
        self.assertIsNotNone(self.older.franchise_checked_at)
        self.assertIsNone(self.older.franchise_id)

    def test_public_franchise_api_hides_single_entry_franchises(self):
        single = Franchise.objects.create(name='Одиночная')
        self.older.franchise = single
        self.older.save(update_fields=['franchise'])
        response = APIClient().get('/api/anime/franchises/')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(0, response.data['count'])

    @patch('apps.anime.application.franchise_sync.sync_franchises.apply_async')
    @patch('apps.anime.application.franchise_sync.cache.add', return_value=False)
    def test_full_rebuild_retries_when_periodic_sync_holds_the_lock(self, _cache_add, apply_async):
        result = sync_franchises.run(
            limit=100,
            continue_until_done=True,
            refresh_provider=True,
            rebuild_id='rebuild-token',
            total=2,
            refresh_before='2026-10-21T12:00:00+03:00',
        )
        self.assertEqual({'skipped': 'busy', 'retry_queued': True}, result)
        apply_async.assert_called_once_with(kwargs={
            'limit': 100,
            'continue_until_done': True,
            'refresh_provider': True,
            'rebuild_id': 'rebuild-token',
            'total': 2,
            'refresh_before': '2026-10-21T12:00:00+03:00',
            'provider_failures': 0,
        }, countdown=10)


class AnimeDetailLookupTests(TestCase):
    def test_missing_anime_returns_readable_404(self):
        Anime.objects.create(shikimori_id=62039, title_ru='Существующее аниме', year=2026)

        response = APIClient().get('/api/anime/999999/')

        self.assertEqual(404, response.status_code)
        self.assertEqual({'error': 'Аниме не найдено'}, response.data)


class DumpPersistenceTests(TestCase):
    def test_sync_persists_corrected_year_and_preserves_year_on_other_updates(self):
        from apps.anime.models import Franchise
        franchise = Franchise.objects.create(name='JoJo')
        broken = Anime.objects.create(shikimori_id=61469, title_ru='Стальной шар', year=2012, franchise=franchise)
        manual = Anime.objects.create(shikimori_id=14719, title_ru='ДжоДжо', year=2025)
        records = [
            {'type': 'anime-serial', 'shikimori_id': str(broken.shikimori_id), 'year': 2026,
             'material_data': {'year': 2012, 'aired_at': '2026-03-19'}},
            {'type': 'anime-serial', 'shikimori_id': str(manual.shikimori_id), 'year': 2012,
             'material_data': {'year': 2012, 'anime_status': 'released', 'anime_episodes': 26}},
        ]
        with patch.object(dumps, 'download_dump', return_value=(Path('fixture.json'), True)), \
             patch.object(dumps, 'iter_json_array', side_effect=lambda path: iter(records)), \
             patch.object(dumps, '_mark_imported'), \
             patch('apps.anime.application.recommendations.invalidate_catalog') as invalidate:
            result = dumps._sync_catalog(True, 0, False, False)
        self.assertEqual(1, result['update_fields']['year'])
        self.assertEqual(1, result['update_fields']['release_date'])
        broken.refresh_from_db(); manual.refresh_from_db(); franchise.refresh_from_db()
        self.assertEqual(2026, broken.year)
        self.assertEqual(date(2026, 3, 19), broken.release_date)
        self.assertEqual(2025, manual.year)
        self.assertEqual((2026, 2026), (franchise.year_start, franchise.year_end))
        invalidate.assert_called_once()
