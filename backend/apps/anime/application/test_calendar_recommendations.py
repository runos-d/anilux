import importlib
import json
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.apps import apps
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.anime.application import kodik_dump_service as dumps, recommendations
from apps.anime.application.calendar_history import merge_calendar
from apps.anime.application.tasks_kodik_dumps import import_kodik_calendar_task
from apps.anime.models import Anime, CalendarRelease, CalendarSnapshot, RecommendationSnapshot
from apps.users.infrastructure.models.users import User, UserLibrary


def entry(sid=1, episode=1, date='2026-09-30T23:30:00Z', title='История'):
    return {'id': sid, 'episode': episode, 'aired_at': date, 'russian': title,
            'english': 'History', 'kind': 'tv', 'episodes': 12}


class CalendarHistoryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.now = datetime(2026, 10, 12, 10, tzinfo=dt_timezone.utc)

    def test_sequential_import_retains_past_marks_future_and_moves_without_duplicates(self):
        past = entry()
        future = entry(2, 4, '2026-11-01T00:30:00Z')
        with patch('django.utils.timezone.now', return_value=self.now):
            merge_calendar([past, future])
            merge_calendar([entry(3, 1, '2026-10-20T10:00:00Z')])
            self.assertEqual(3, CalendarRelease.objects.count())
            self.assertFalse(CalendarRelease.objects.get(shikimori_id=1).schedule_uncertain)
            self.assertTrue(CalendarRelease.objects.get(shikimori_id=2).schedule_uncertain)
            corrected = entry(2, 4, '2026-10-31T22:30:00Z', 'Перенесено')
            corrected_past = entry(1, 1, '2026-09-29T10:15:00Z', 'Исправлено')
            for _ in range(2):
                merge_calendar([corrected, corrected_past])
            self.assertEqual(3, CalendarRelease.objects.count())
            moved = CalendarRelease.objects.get(shikimori_id=2)
            self.assertFalse(moved.schedule_uncertain)
            self.assertEqual('Перенесено', moved.data['russian'])
            response = self.client.get('/api/anime/calendar/', {'month': '2026-09', 'timezone': 'UTC'})
            self.assertEqual(200, response.status_code)
            release = response.data['days'][0]['items'][0]
            self.assertEqual('Исправлено', release['anime']['title_ru'])
            self.assertEqual('10:15', release['time'])

    def test_device_timezone_changes_day_month_and_search_covers_saved_history(self):
        merge_calendar([entry()])
        for zone, month, date, time in [('Europe/Moscow', '2026-10', '2026-10-01', '02:30'),
                                        ('America/Los_Angeles', '2026-09', '2026-09-30', '16:30')]:
            response = self.client.get('/api/anime/calendar/', {'month': month, 'timezone': zone})
            self.assertEqual(200, response.status_code)
            day = next(day for day in response.data['days'] if day['in_month'])
            self.assertEqual(date, day['date'])
            self.assertEqual(time, day['items'][0]['time'])
        response = self.client.get('/api/anime/calendar/', {'month': '2025-01'})
        self.assertEqual([], response.data['days'])
        response = self.client.get('/api/anime/calendar/', {'search': 'История'})
        self.assertEqual(1, response.data['total'])
        self.assertEqual(400, self.client.get('/api/anime/calendar/', {'timezone': 'bad/timezone'}).status_code)

    def test_api_cache_refreshes_immediately_after_correction(self):
        merge_calendar([entry()])
        first = self.client.get('/api/anime/calendar/', {'month': '2026-09'}).data
        merge_calendar([entry(date='2026-09-28T12:00:00Z', title='Новое имя')])
        second = self.client.get('/api/anime/calendar/', {'month': '2026-09'}).data
        self.assertNotEqual(first['days'], second['days'])
        self.assertEqual('Новое имя', second['days'][0]['items'][0]['anime']['title_ru'])

    def test_calendar_returns_local_anime_identity_for_page_navigation(self):
        Anime.objects.create(title_ru='Другой тайтл', shikimori_id=900)
        anime = Anime.objects.create(title_ru='История', slug='istoriya', shikimori_id=777)
        merge_calendar([entry(sid=777)])
        response = self.client.get('/api/anime/calendar/', {'month': '2026-09', 'timezone': 'UTC'})
        card = response.data['days'][0]['items'][0]['anime']
        self.assertEqual(anime.pk, card['id'])
        self.assertEqual('istoriya', card['slug'])
        self.assertEqual(777, card['shikimori_id'])

    def test_next_episode_adds_a_release_without_overwriting_previous_episode(self):
        merge_calendar([entry(episode=1)])
        for _ in range(2):
            merge_calendar([entry(episode=2, date='2026-10-07T23:30:00Z')])
        self.assertEqual({1, 2}, set(CalendarRelease.objects.values_list('episode', flat=True)))
        self.assertEqual('2026-09-30', CalendarRelease.objects.get(episode=1).aired_at.date().isoformat())

    def test_import_failure_and_invalid_payload_never_mark_absence(self):
        future = entry(date='2099-01-01T00:00:00Z')
        merge_calendar([future])
        with patch.object(dumps, 'download_dump', side_effect=OSError('offline')):
            with self.assertRaises(OSError):
                import_kodik_calendar_task.run()
        with self.assertRaises(ValueError):
            merge_calendar([entry(), entry(date='invalid')])
        self.assertEqual([future], CalendarSnapshot.objects.get().entries)
        self.assertEqual(1, CalendarRelease.objects.count())
        self.assertFalse(CalendarRelease.objects.get().schedule_uncertain)
        for invalid in ({'error': 'not a calendar'}, [None], [{'anime': {'id': 1}}]):
            with self.assertRaises(dumps.DumpError):
                dumps.normalize_calendar(invalid)

    def test_successful_empty_and_unchanged_source_are_imported_from_file_not_stale_cache(self):
        with TemporaryDirectory() as folder, override_settings(KODIK_DUMP_DIR=folder):
            source = Path(folder) / 'calendar.json'
            raw = [{'anime': {'id': 1, 'russian': 'Первый'}, 'next_episode': 1,
                    'next_episode_at': '2099-01-01T00:00:00Z'}]
            source.write_text(json.dumps(raw), encoding='utf-8')
            with patch.object(dumps, 'download_dump', return_value=(source, False)):
                import_kodik_calendar_task.run()
                cache.set(dumps.CALENDAR_CACHE_KEY, [entry(sid=999)])
                import_kodik_calendar_task.run()
                self.assertEqual(1, CalendarRelease.objects.count())
                source.write_text('[]', encoding='utf-8')
                import_kodik_calendar_task.run()
            self.assertTrue(CalendarRelease.objects.get().schedule_uncertain)
            self.assertEqual([], CalendarSnapshot.objects.get().entries)

    def test_seed_migration_preserves_snapshot_and_existing_title_data(self):
        from django.db import connection
        original = [entry(), {'anime': {'id': 2, 'russian': 'Старый формат'},
                               'next_episode': 2, 'next_episode_at': '2026-08-01T12:00:00Z'}]
        CalendarSnapshot.objects.create(entries=original)
        migration = importlib.import_module('apps.anime.migrations.0009_calendarrelease')
        with connection.schema_editor() as editor:
            migration.preserve_snapshot(apps, editor)
        self.assertEqual(original, CalendarSnapshot.objects.get().entries)
        self.assertEqual(2, CalendarRelease.objects.count())
        self.assertEqual('Старый формат', CalendarRelease.objects.get(shikimori_id=2).data['russian'])


class RecommendationRulesTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='recommendation_test')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.movies = [Anime.objects.create(title_ru=f'Фильм {index}', kind=kind, episodes=episodes,
                                            score=8, is_available=True)
                       for index, (kind, episodes) in enumerate([('movie', 1), ('movie', 2),
                                                                ('movie', None), ('movie', 0), ('ova', 1)])]

    def test_generator_legacy_and_real_api_exclude_multi_unknown_and_ova(self):
        from apps.anime.presentation.views.anime_views import PersonalizedRecommendationsView
        valid = self.movies[0].pk
        self.assertEqual([valid], [r['id'] for r in recommendations.build()['movies']])
        legacy = PersonalizedRecommendationsView()._get_movies_high_rated()
        self.assertEqual([valid], [r['anime_id'] for r in legacy])
        response = self.client.get('/api/anime/home/personalized/', {'sections': 'movies'})
        self.assertEqual(200, response.status_code)
        self.assertEqual([valid], [r['id'] for r in response.data['movies']])

    def test_obsolete_snapshot_never_returns_old_movies_or_explanations(self):
        snapshot = RecommendationSnapshot.objects.create(key='public', data={
            'movies': [{'id': row.pk, 'kind': 'movie', 'episodes': 1, 'reason': 'Старое объяснение'}
                       for row in self.movies]}, dirty=False, generated_at=timezone.now())
        with patch.object(recommendations, 'queue_refresh'):
            data = recommendations.read(None, 'movies')
        self.assertEqual([self.movies[0].pk], [r['id'] for r in data['movies']])
        self.assertNotIn('Старое', data['movies'][0]['reason'])
        snapshot.data = recommendations.build()
        snapshot.algorithm_version = recommendations.ALGORITHM_VERSION
        snapshot.save()
        Anime.objects.filter(pk=self.movies[0].pk).update(episodes=2)
        with patch.object(recommendations, 'queue_refresh'):
            self.assertEqual([], recommendations.read(None, 'movies')['movies'])

    def test_personalization_reasons_are_grounded_and_collection_exclusions_survive(self):
        source = Anime.objects.create(title_ru='Любимое приключение', kind='tv', genres=['Приключения'], score=9)
        target = Anime.objects.create(title_ru='Новое приключение', kind='tv', genres=['Приключения'],
                                      score=6.5, episodes=12, is_available=True)
        UserLibrary.objects.create(user=self.user, anime=source, status='completed', rating=9)
        data = recommendations.build(self.user)
        reason = next(row for row in data['based_on_watched'] if row['id'] == target.pk)
        self.assertIn(source.title_ru, reason['reason'])
        self.assertIn(target.title_ru, reason['reason'])
        self.assertEqual(['Приключения'], reason['reason_details']['genres'])
        self.assertEqual(source.pk, reason['reason_details']['source_anime_id'])
        genre_reason = next(row for row in data['top_rated_in_genres'] if row['id'] == target.pk)
        self.assertNotIn('Высокий рейтинг', genre_reason['reason'])
        UserLibrary.objects.create(user=self.user, anime=self.movies[0], status='hidden')
        recommendations.refresh_recommendations('user:' + str(self.user.pk))
        self.assertEqual([], recommendations.read(self.user, 'movies')['movies'])
