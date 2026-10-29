from unittest.mock import patch

from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.anime.application import recommendations
from apps.anime.models import Anime, RecommendationSnapshot
from apps.users.infrastructure.models.users import User, UserLibrary


class RecommendationReadBoundsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='bounded-recommendations')
        self.anime = Anime.objects.create(title_ru='Общий результат', score=8, episodes=12,
                                         is_available=True, has_cyrillic=True)
        self.public = recommendations.build(None)
        RecommendationSnapshot.objects.create(key='public', data=self.public, dirty=False,
            algorithm_version=recommendations.ALGORITHM_VERSION, generated_at=timezone.now())

    def test_cold_personal_read_uses_public_snapshot_without_personal_build(self):
        with patch.object(recommendations, 'build', side_effect=AssertionError('HTTP must not build')), \
                patch.object(recommendations, 'queue_refresh') as queue:
            result = recommendations.read(self.user, 'top_anime')
        self.assertFalse(result['has_personalization'])
        self.assertEqual(result['top_anime'], self.public['top_anime'])
        queue.assert_called_once_with(f'user:{self.user.pk}')

    def test_empty_public_fallback_never_builds_with_user(self):
        RecommendationSnapshot.objects.all().delete()
        with patch.object(recommendations, 'build', wraps=recommendations.build) as build, \
                patch.object(recommendations, 'queue_refresh'):
            recommendations.read(self.user)
        build.assert_called_once_with(None)

    def test_dirty_projection_drops_old_history_reasons_and_checks_visibility(self):
        private_data = {**self.public, 'has_personalization': True, 'user_genres': ['Old history'],
                        'based_on_watched': [{'id': self.anime.pk, 'reason': 'Old history'}]}
        RecommendationSnapshot.objects.create(key=f'user:{self.user.pk}', user=self.user,
            data=private_data, dirty=True, algorithm_version=recommendations.ALGORITHM_VERSION)
        Anime.objects.filter(pk=self.anime.pk).update(is_available=False)
        with patch.object(recommendations, 'queue_refresh'):
            result = recommendations.read(self.user)
        self.assertFalse(result['has_personalization'])
        self.assertNotIn('Old history', str(result))
        self.assertFalse(any(result[section] for section in recommendations.SECTIONS))

    def test_live_exclusion_queries_are_scoped_to_candidates(self):
        UserLibrary.objects.create(user=self.user, anime=self.anime, status='hidden')
        with patch.object(recommendations, 'queue_refresh'), CaptureQueriesContext(connection) as sql:
            result = recommendations.read(self.user)
        self.assertFalse(any(result[section] for section in recommendations.SECTIONS))
        library_reads = [q['sql'] for q in sql if 'FROM `users_userlibrary`' in q['sql']]
        self.assertEqual(len(library_reads), 1)
        self.assertIn('anime_id` IN', library_reads[0])
        self.assertLessEqual(len(sql), 10)

    def test_catalog_invalidation_during_build_cannot_publish_old_projection(self):
        snapshot = RecommendationSnapshot.objects.get(key='public')
        original = snapshot.data
        def concurrent_build(user):
            with patch('apps.seo.signals.schedule_hubs'):
                recommendations.invalidate_catalog()
            return {'movies': [], 'stale_worker': True}
        with patch.object(recommendations, 'build', side_effect=concurrent_build):
            self.assertIsNone(recommendations.refresh_recommendations('public'))
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.data, original)
        self.assertTrue(snapshot.dirty)
        self.assertGreater(snapshot.revision, 1)

    def test_projection_rebuild_is_dry_by_default_and_bounded(self):
        import io
        import json
        from django.core.management import call_command
        snapshot = RecommendationSnapshot.objects.get(key='public')
        out = io.StringIO()
        call_command('rebuild_recommendations', limit=1, stdout=out)
        self.assertFalse(json.loads(out.getvalue())['applied'])
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.revision, 1)
        call_command('rebuild_recommendations', limit=1, apply=True, stdout=io.StringIO())
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.revision, 2)
        self.assertTrue(snapshot.dirty)
