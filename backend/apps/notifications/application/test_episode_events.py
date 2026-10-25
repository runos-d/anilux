import importlib
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta, timezone as utc
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.anime.models import Anime, CalendarRelease, KodikAvailability
from apps.anime.infrastructure.models.anime import UserEpisodeProgress
from apps.anime.application.calendar_history import merge_calendar
from apps.anime.application.episode_availability import record_availability, provider_episodes
from apps.anime.application import kodik_dump_service as dumps
from apps.notifications.models import Reminder, EpisodeSubscription, Notification, EpisodeNotice
from apps.notifications.application.episode_events import process_subscriptions, process_reminders
from apps.notifications.application.celery_tasks import process_episode_events
from apps.users.models import User, UserLibrary, UserLibraryArchive


def provider(last=2, **extras):
    return {'type': 'anime-serial', 'id': 'serial-episode-test', 'link': '//kodik.test/serial/1',
            'shikimori_id': '1100', 'last_episode': last,
            'material_data': {'anime_episodes': 12, 'episodes_total': 12, 'anime_status': 'ongoing'}, **extras}


class EpisodeLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='episode_owner')
        self.other = User.objects.create_user(username='episode_other')
        self.anime = Anime.objects.create(title_ru='Проверка серий', shikimori_id=1100,
            episodes=12, kind='tv', score=8, is_available=True, raw_kodik_data=provider())
        record_availability(self.anime, provider())
        from .episode_verification import mark_verified
        mark_verified([1100])
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def add(self, **extra):
        response = self.client.post('/api/users/library/', {'anime': self.anime.pk, **extra}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        return UserLibrary.objects.get(pk=response.data['id'])

    def release(self, episode=3, when=None):
        date = when or timezone.now() + timedelta(days=1)
        merge_calendar([{'id': 1100, 'episode': episode, 'aired_at': date.isoformat(),
                         'russian': self.anime.title_ru, 'kind': 'tv'}])
        return CalendarRelease.objects.get(shikimori_id=1100, episode=episode)

    def reminder(self, release, **extra):
        response = self.client.post('/api/notifications/reminders/',
            {'calendar_release_id': release.pk, **extra}, format='json')
        self.assertIn(response.status_code, (200, 201), response.data)
        return Reminder.objects.get(pk=response.data['id'])

    def test_add_auto_subscribe_manual_disable_survives_progress_status_and_upserts(self):
        item = self.add()
        sub = EpisodeSubscription.objects.get(user=self.user, anime=self.anime)
        self.assertTrue(sub.is_active)
        self.assertEqual([1, 2], sub.notified_episodes)
        self.assertEqual(200, self.client.patch(f'/api/notifications/episode-subs/{sub.pk}/',
            {'is_active': False}, format='json').status_code)
        self.client.patch(f'/api/users/library/{item.pk}/', {'current_episode': 1}, format='json')
        self.client.patch(f'/api/users/library/{item.pk}/', {'status': 'on_hold'}, format='json')
        self.client.post('/api/users/library/', {'anime': self.anime.pk, 'status': 'started'}, format='json')
        sub.refresh_from_db()
        self.assertFalse(sub.is_active)
        self.assertTrue(sub.manually_disabled)
        record_availability(self.anime, provider(3))
        process_subscriptions()
        self.assertEqual(0, Notification.objects.filter(user=self.user, type='episode_available').count())
        response = self.client.post('/api/notifications/episode-subs/', {'anime_id': self.anime.pk}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(sub.pk, response.data['id'])
        self.assertTrue(response.data['is_active'])

    def test_removal_preserves_progress_and_does_not_resubscribe_during_later_watch(self):
        item = self.add(status='started', current_episode=2, episodes_watched=2)
        self.assertEqual(200, self.client.delete(f'/api/users/library/{item.pk}/').status_code)
        self.assertFalse(UserLibrary.objects.filter(user=self.user, anime=self.anime).exists())
        self.assertEqual(2, UserLibraryArchive.objects.get(user=self.user).progress['current_episode'])
        sub = EpisodeSubscription.objects.get(user=self.user, anime=self.anime)
        self.assertFalse(sub.is_active)
        response = self.client.post(f'/api/anime/{self.anime.pk}/episode-progress/',
            {'action': 'mark', 'episode_number': 3}, format='json')
        self.assertEqual(200, response.status_code)
        sub.refresh_from_db()
        self.assertFalse(sub.is_active)
        self.assertFalse(UserLibrary.objects.filter(user=self.user, anime=self.anime).exists())
        self.assertTrue(UserEpisodeProgress.objects.filter(user=self.user, episode_number=3, status='watched').exists())
        restored = self.add()
        self.assertEqual(3, restored.current_episode)
        sub.refresh_from_db()
        self.assertTrue(sub.is_active)

    def test_new_membership_subscribes_again_but_active_subscription_retries_keep_pending_episode(self):
        item = self.add(current_episode=2)
        sub = EpisodeSubscription.objects.get(user=self.user, anime=self.anime)
        self.client.patch(f'/api/notifications/episode-subs/{sub.pk}/', {'is_active': False}, format='json')
        self.client.delete(f'/api/users/library/{item.pk}/')
        self.add()
        sub.refresh_from_db()
        self.assertTrue(sub.is_active)
        self.assertFalse(sub.manually_disabled)
        record_availability(self.anime, provider(3))
        self.client.post('/api/notifications/episode-subs/', {'anime_id': self.anime.pk}, format='json')
        self.release(when=timezone.now())
        self.assertEqual(1, process_subscriptions())

    def test_metadata_is_not_a_release_and_completed_title_reopens_only_on_hosted_episode(self):
        item = self.add(status='completed', current_episode=2, episodes_watched=2)
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])
        record_availability(self.anime, provider(2, title='Новый постер', translation={'id': 999}))
        item.refresh_from_db()
        self.assertEqual('completed', item.status)
        self.release(when=timezone.now())
        record_availability(self.anime, provider(3))
        item.refresh_from_db()
        self.assertEqual('started', item.status)
        self.assertEqual(2, item.current_episode)
        home = self.client.get('/api/anime/home/').data
        row = home['new_episodes'][0]
        self.assertEqual((3, 1, 3), (row['latest_episode'], row['unwatched_count'], row['next_episode']))
        self.assertIn('continue_watching', home)
        self.assertIn('rewatch', home)
        self.assertIn('recommendations', home)
        response = self.client.post(f'/api/anime/{self.anime.pk}/episode-progress/',
            {'action': 'mark', 'episode_number': 3}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])
        item.refresh_from_db()
        self.assertEqual(3, item.real_episodes_watched)
        self.release(episode=4, when=timezone.now())
        record_availability(self.anime, provider(4))
        self.assertEqual(1, self.client.get('/api/anime/home/').data['new_episodes'][0]['unwatched_count'])

    def test_subscription_repeat_and_another_translation_do_not_repeat_notices_even_after_delete(self):
        self.add()
        self.release(when=timezone.now())
        record_availability(self.anime, provider(3))
        self.assertEqual(1, process_subscriptions())
        first = Notification.objects.get(user=self.user, type='episode_available')
        self.assertIn('Серия 3', first.title)
        first.is_deleted = True
        first.save()
        for _ in range(2):
            record_availability(self.anime, provider(3, translation={'id': 9}))
            self.assertEqual(0, process_subscriptions())
        self.assertEqual(1, Notification.objects.filter(user=self.user, type='episode_available').count())
        self.assertEqual(1, EpisodeNotice.objects.filter(user=self.user).count())

    def test_guest_home_and_other_users_unavailable_hidden_and_dropped_titles(self):
        self.add()
        self.release(when=timezone.now())
        record_availability(self.anime, provider(3))
        self.assertEqual(1, len(self.client.get('/api/anime/home/').data['new_episodes']))
        guest = APIClient()
        response = guest.get('/api/anime/home/')
        self.assertEqual([], response.data['new_episodes'])
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('Authorization', response['Vary'])
        self.client.force_authenticate(self.other)
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])
        self.client.force_authenticate(self.user)
        for state in ('hidden', 'dropped'):
            UserLibrary.objects.filter(user=self.user).update(status=state)
            self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])
        UserLibrary.objects.filter(user=self.user).update(status='started')
        self.anime.is_available = False
        self.anime.save()
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])
        self.assertEqual(0, process_subscriptions())

    def test_announced_first_episode_is_a_real_release_not_an_unknown_historic_baseline(self):
        self.anime.status = 'announced'
        self.anime.save()
        KodikAvailability.objects.filter(anime=self.anime).delete()
        self.add()
        self.release(episode=1, when=timezone.now())
        record_availability(self.anime, provider(1))
        self.assertEqual(1, process_subscriptions())
        self.assertEqual(1, self.client.get('/api/anime/home/').data['new_episodes'][0]['latest_episode'])

    def test_dump_actual_episode_integration_ignores_planned_count_and_repeated_records(self):
        self.add(status='completed', current_episode=2)
        record = provider(3)
        with patch.object(dumps, 'download_dump', return_value=(Path('fixture.json'), True)), \
             patch.object(dumps, 'iter_json_array', side_effect=lambda path: iter([record])), \
             patch.object(dumps, '_mark_imported'):
            result = dumps._sync_catalog(True, 0, False, False)
            repeated = dumps._sync_catalog(True, 0, False, False)
        self.assertEqual(1, result['availability_changed'])
        self.assertEqual(0, repeated['availability_changed'])
        self.assertEqual(3, KodikAvailability.objects.get(anime=self.anime).last_episode)
        self.assertEqual(12, Anime.objects.get(pk=self.anime.pk).episodes)

    def test_progress_holes_are_not_marked_watched_by_an_episode_count(self):
        item = self.add()
        UserEpisodeProgress.objects.create(user=self.user, anime=self.anime, episode_number=2, status='watched')
        self.release(when=timezone.now())
        record_availability(self.anime, provider(3))
        row = self.client.get('/api/anime/home/').data['new_episodes'][0]
        self.assertEqual((1, 3), (row['unwatched_count'], row['next_episode']))
        from apps.users.application.library_episodes import unseen_episodes
        self.assertEqual([1, 3], unseen_episodes(item))

    def test_home_new_episodes_excludes_historic_equal_unknown_and_future_dates(self):
        item = self.add()
        self.release(episode=3, when=item.added_at - timedelta(days=1))
        self.release(episode=4, when=item.added_at)
        self.release(episode=6, when=timezone.now() + timedelta(days=1))
        record_availability(self.anime, provider(6))
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])

    def test_home_counts_and_watch_target_include_only_new_unseen_releases(self):
        item = self.add()
        self.release(episode=3, when=item.added_at + timedelta(microseconds=1))
        self.release(episode=4, when=timezone.now())
        self.release(episode=5, when=timezone.now())
        record_availability(self.anime, provider(7))
        UserEpisodeProgress.objects.create(user=self.user, anime=self.anime, episode_number=4, status='watched')
        row = self.client.get('/api/anime/home/').data['new_episodes'][0]
        self.assertEqual((5, 2, 3), (row['latest_episode'], row['unwatched_count'], row['next_episode']))
        for episode in (3, 5):
            UserEpisodeProgress.objects.create(user=self.user, anime=self.anime, episode_number=episode, status='watched')
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])

    def test_home_new_episodes_uses_readded_membership_date(self):
        item = self.add()
        self.release(when=timezone.now())
        self.client.delete(f'/api/users/library/{item.pk}/')
        new_item = self.add()
        record_availability(self.anime, provider(3))
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])
        self.release(when=new_item.added_at + timedelta(microseconds=1))
        self.assertEqual(3, self.client.get('/api/anime/home/').data['new_episodes'][0]['next_episode'])

    def test_home_dated_new_episode_does_not_depend_on_migration_snapshot_baseline(self):
        item = self.add()
        self.release(when=timezone.now())
        record_availability(self.anime, provider(3))
        UserLibrary.objects.filter(pk=item.pk).update(episode_baseline=[1, 2, 3])
        self.assertEqual(3, self.client.get('/api/anime/home/').data['new_episodes'][0]['next_episode'])

    def test_home_scheduled_but_unavailable_episode_is_not_shown(self):
        self.add()
        self.release(when=timezone.now())
        self.assertEqual([], self.client.get('/api/anime/home/').data['new_episodes'])

    def test_genuine_saved_watch_progress_above_an_old_translation_is_retained(self):
        item = UserLibrary.objects.create(user=self.user, anime=self.anime, status='completed',
            current_episode=12, episodes_watched=12, real_episodes_watched=12)
        record_availability(self.anime, provider(12))
        item.refresh_from_db()
        self.assertEqual('completed', item.status)
        self.assertEqual(12, item.real_episodes_watched)
        self.assertEqual(0, process_subscriptions())
        self.release(episode=13, when=timezone.now())
        record_availability(self.anime, provider(13))
        item.refresh_from_db()
        self.assertEqual('started', item.status)
        self.assertEqual(1, process_subscriptions())

    def test_episode_released_before_or_at_membership_is_never_announced_on_late_import(self):
        item = self.add()
        self.release(episode=3, when=item.added_at - timedelta(days=2))
        self.release(episode=4, when=item.added_at)
        self.release(episode=5, when=timezone.now())
        record_availability(self.anime, provider(5))
        self.assertEqual(1, process_subscriptions())
        self.assertIn('Серия 5', Notification.objects.get(user=self.user, type='episode_available').title)
        self.assertEqual(0, process_subscriptions())

    def test_unknown_or_future_release_waits_for_date_evidence(self):
        item = self.add()
        record_availability(self.anime, provider(3))
        self.assertEqual(0, process_subscriptions())
        self.release(when=timezone.now() + timedelta(days=1))
        self.assertEqual(0, process_subscriptions())
        self.release(when=item.added_at + timedelta(microseconds=1))
        self.assertEqual(1, process_subscriptions())
        self.assertEqual(0, process_subscriptions())

    def test_pause_and_calendar_backfill_do_not_announce_historic_release(self):
        item = self.add()
        sub = EpisodeSubscription.objects.get(user=self.user, anime=self.anime)
        sub.is_paused = True; sub.save()
        record_availability(self.anime, provider(3))
        self.release(when=item.added_at - timedelta(seconds=1))
        self.assertEqual(0, process_subscriptions())
        sub.is_paused = False; sub.save()
        self.assertEqual(0, process_subscriptions())
        self.assertFalse(Notification.objects.filter(user=self.user, type='episode_available').exists())

    def test_readd_uses_new_membership_date_even_if_original_subscription_is_old(self):
        item = self.add()
        release = self.release(when=timezone.now())
        self.client.delete(f'/api/users/library/{item.pk}/')
        new_item = self.add()
        self.assertLess(release.aired_at, new_item.added_at)
        record_availability(self.anime, provider(3))
        self.assertEqual(0, process_subscriptions())

    def test_automatic_episode_notice_requires_collection_membership(self):
        EpisodeSubscription.objects.create(user=self.user, anime=self.anime,
            is_active=True, baseline_initialized=True, notified_episodes=[1, 2])
        self.release(when=timezone.now())
        record_availability(self.anime, provider(3))
        self.assertEqual(0, process_subscriptions())
        self.assertFalse(Notification.objects.filter(user=self.user, type='episode_available').exists())
        self.add()
        self.assertEqual(0, process_subscriptions())

    def test_delayed_initial_snapshot_can_announce_a_proven_new_release(self):
        KodikAvailability.objects.filter(anime=self.anime).delete()
        item = self.add()
        self.release(episode=1, when=item.added_at - timedelta(days=1))
        self.release(episode=2, when=timezone.now())
        record_availability(self.anime, provider(2))
        self.assertEqual(1, process_subscriptions())
        self.assertIn('Серия 2', Notification.objects.get(user=self.user, type='episode_available').title)

    def test_delayed_initial_snapshot_does_not_mark_a_new_release_as_watched(self):
        KodikAvailability.objects.filter(anime=self.anime).delete()
        item = self.add(status='completed', current_episode=1)
        self.release(episode=1, when=item.added_at - timedelta(days=1))
        self.release(episode=2, when=timezone.now())
        record_availability(self.anime, provider(2))
        item.refresh_from_db()
        self.assertEqual('started', item.status)
        self.assertEqual(1, item.watched_through)
        self.assertEqual(1, process_subscriptions())

    def test_calendar_api_exposes_stable_identity_and_date_moves_only_bound_reminder(self):
        release = self.release()
        bound = self.reminder(release)
        manual_time = timezone.now() + timedelta(hours=4)
        manual = Reminder.objects.create(user=self.user, anime=self.anime, reminder_time=manual_time)
        moved = release.aired_at + timedelta(days=2)
        self.release(when=moved)
        bound.refresh_from_db(); manual.refresh_from_db()
        self.assertEqual(moved, bound.reminder_time)
        self.assertEqual(manual_time, manual.reminder_time)
        data = self.client.get('/api/anime/calendar/', {'month': moved.strftime('%Y-%m'), 'timezone': 'Europe/Moscow'}).data
        self.assertTrue(any(item['calendar_release_id'] == release.pk for day in data['days'] for item in day['items']))
        repeated = self.reminder(release)
        self.assertEqual(bound.pk, repeated.pk)

    def test_editing_bound_time_stops_automatic_date_moves(self):
        release = self.release()
        reminder = self.reminder(release)
        manual_time = timezone.now() + timedelta(hours=3)
        response = self.client.patch(f'/api/notifications/reminders/{reminder.pk}/',
            {'reminder_time': manual_time.isoformat()}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        self.release(when=release.aired_at + timedelta(days=3))
        reminder.refresh_from_db()
        self.assertFalse(reminder.follow_schedule)
        self.assertEqual(manual_time, reminder.reminder_time)

    def test_delay_then_availability_with_subscription_and_repeated_jobs_sends_each_phase_once(self):
        self.add()
        release = self.release(when=timezone.now() - timedelta(minutes=5))
        reminder = self.reminder(release)
        self.assertEqual([reminder.pk], process_reminders())
        delayed = Notification.objects.get(user=self.user, type='episode_delayed')
        self.assertNotIn('/watch', delayed.link)
        self.assertIn('пока недоступна', delayed.content)
        for _ in range(2):
            self.assertEqual([], process_reminders())
        record_availability(self.anime, provider(3))
        for _ in range(3):
            process_episode_events.run()
        self.assertEqual(1, Notification.objects.filter(user=self.user, type='episode_delayed').count())
        self.assertEqual(1, Notification.objects.filter(user=self.user, type='episode_available').count())
        reminder.refresh_from_db()
        self.assertFalse(reminder.is_active)
        self.assertIsNotNone(reminder.available_notified_at)

    def test_calendar_reminder_can_precede_catalog_import_and_resolves_when_anime_arrives(self):
        merge_calendar([{'id': 1199, 'episode': 1, 'aired_at': (timezone.now() - timedelta(minutes=1)).isoformat(),
                         'russian': 'Будущий тайтл', 'kind': 'tv'}])
        release = CalendarRelease.objects.get(shikimori_id=1199)
        reminder = self.reminder(release)
        self.assertIsNone(reminder.anime_id)
        self.assertEqual([reminder.pk], process_reminders(verified_shikimori_ids={1199}))
        anime = Anime.objects.create(shikimori_id=1199, title_ru='Будущий тайтл', is_available=True)
        record_availability(anime, provider(1, shikimori_id='1199'))
        self.assertEqual([reminder.pk], process_reminders())
        reminder.refresh_from_db()
        self.assertEqual(anime.pk, reminder.anime_id)

    def test_manual_weekly_reminder_keeps_device_clock_across_dst_and_repeats_once(self):
        due = datetime(2026, 10, 25, 10, 30, tzinfo=utc.utc)
        reminder = Reminder.objects.create(user=self.user, anime=self.anime, reminder_time=due,
            repeat_weekly=True, timezone_name='America/Los_Angeles', enable_push=False)
        with patch('django.utils.timezone.now', return_value=due):
            self.assertEqual([reminder.pk], process_reminders())
            self.assertEqual([], process_reminders())
        reminder.refresh_from_db()
        self.assertEqual(datetime(2026, 11, 1, 11, 30, tzinfo=utc.utc), reminder.reminder_time)
        notice = Notification.objects.get(user=self.user, type='reminder_episode')
        self.assertFalse(notice.enable_push)
        with patch('django.utils.timezone.now', return_value=reminder.reminder_time):
            self.assertEqual([reminder.pk], process_reminders())
        self.assertEqual(2, Notification.objects.filter(user=self.user, type='reminder_episode').count())

    def test_custom_repeat_end_date_and_overdue_manual_reminder(self):
        due = timezone.now() - timedelta(days=1)
        response = self.client.post('/api/notifications/reminders/', {'anime_id': self.anime.pk,
            'reminder_time': due.isoformat(), 'repeat_interval_days': 14,
            'end_date': (due + timedelta(days=7)).isoformat()}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        reminder = Reminder.objects.get(pk=response.data['id'])
        self.assertEqual([reminder.pk], process_reminders())
        reminder.refresh_from_db()
        self.assertFalse(reminder.is_active)
        self.assertEqual([], process_reminders())

    def test_permission_and_calendar_identity_validation(self):
        item = self.add()
        sub = EpisodeSubscription.objects.get(user=self.user)
        reminder = self.reminder(self.release())
        self.client.force_authenticate(self.other)
        self.assertEqual(404, self.client.patch(f'/api/notifications/episode-subs/{sub.pk}/', {'is_active': False}).status_code)
        self.assertEqual(404, self.client.delete(f'/api/notifications/reminders/{reminder.pk}/').status_code)
        self.assertEqual(403, self.client.delete(f'/api/users/library/{item.pk}/').status_code)
        self.client.force_authenticate(self.user)
        self.assertEqual(400, self.client.post('/api/notifications/reminders/',
            {'calendar_release_id': reminder.calendar_release_id, 'anime_id': 999}, format='json').status_code)
        self.assertEqual(400, self.client.post('/api/notifications/reminders/',
            {'anime_id': self.anime.pk, 'reminder_time': timezone.now().isoformat(), 'timezone_name': 'bad/zone'}, format='json').status_code)

    def test_seed_preserves_explicit_off_and_legacy_progress(self):
        from django.db import connection
        item = self.add(status='completed', current_episode=12, episodes_watched=12)
        sub = EpisodeSubscription.objects.get(user=self.user)
        sub.is_active = False; sub.save()
        migration = importlib.import_module('apps.notifications.migrations.0007_episode_baselines')
        with connection.schema_editor() as editor:
            migration.seed(apps, editor)
        item.refresh_from_db(); sub.refresh_from_db()
        self.assertEqual((12, 12), (item.current_episode, item.episodes_watched))
        self.assertEqual(2, item.watched_through)
        self.assertFalse(sub.is_active)
        self.assertTrue(sub.manually_disabled)

    def test_unverified_metadata_cannot_claim_provider_availability(self):
        self.assertIsNone(provider_episodes({'type': 'anime-serial', 'link': '//kodik.test/1',
            'episodes_count': 12, 'material_data': {'episodes_total': 12, 'episodes_aired': 6}}))
        self.assertIsNone(provider_episodes(provider(4, link='')))
        self.assertEqual({1, 3}, provider_episodes(provider(10, seasons={'1': {
            'episodes': {'1': '//kodik.test/1', '2': '', '3': '//kodik.test/3'}}})))

    def test_stale_missing_episode_is_verified_in_background_before_delay(self):
        from .episode_verification import verify_title
        self.add(status='completed', current_episode=2)
        reminder = self.reminder(self.release(when=timezone.now() - timedelta(minutes=1)))
        cache.clear()
        self.assertEqual([], process_reminders())
        with patch('apps.anime.infrastructure.api.kodik.kodik_api._get', return_value={'results': [provider(3)]}) as request:
            self.assertTrue(verify_title(1100))
        self.assertEqual(1, request.call_count)
        self.assertEqual(1, request.call_args.kwargs['retries'])
        reminder.refresh_from_db()
        self.assertIsNotNone(reminder.available_notified_at)
        self.assertEqual(0, Notification.objects.filter(type='episode_delayed').count())

    def test_failed_or_incomplete_live_check_does_not_claim_a_delay(self):
        from .episode_verification import verify_title
        reminder = self.reminder(self.release(when=timezone.now() - timedelta(minutes=1)))
        cache.clear()
        for response in (OSError('offline'), {'results': [provider(2)], 'next_page': '//kodik.test/page2'}):
            kwargs = {'side_effect': response} if isinstance(response, Exception) else {'return_value': response}
            with patch('apps.anime.infrastructure.api.kodik.kodik_api._get', **kwargs):
                self.assertFalse(verify_title(1100))
        reminder.refresh_from_db()
        self.assertIsNone(reminder.delay_notified_at)
        self.assertEqual(0, Notification.objects.filter(type='episode_delayed').count())
        with patch('apps.anime.infrastructure.api.kodik.kodik_api._get', return_value={'results': [provider(2)]}):
            self.assertTrue(verify_title(1100))
        self.assertEqual(1, Notification.objects.filter(type='episode_delayed').count())

    def test_live_empty_results_remove_stale_available_episodes_without_treating_errors_as_absence(self):
        from .episode_verification import verify_title
        reminder = self.reminder(self.release(episode=2, when=timezone.now() - timedelta(minutes=1)))
        cache.clear()
        with patch('apps.anime.infrastructure.api.kodik.kodik_api._get', return_value={'results': [], 'error': 'unavailable'}):
            self.assertFalse(verify_title(1100))
        self.assertEqual([1, 2], KodikAvailability.objects.get(anime=self.anime).episodes)
        with patch('apps.anime.infrastructure.api.kodik.kodik_api._get', return_value={'results': []}):
            self.assertTrue(verify_title(1100))
        self.assertEqual([], KodikAvailability.objects.get(anime=self.anime).episodes)
        self.assertEqual(1, Notification.objects.filter(type='episode_delayed').count())

    def test_stale_positive_snapshot_does_not_offer_a_missing_episode(self):
        reminder = self.reminder(self.release(episode=2, when=timezone.now() - timedelta(minutes=1)))
        KodikAvailability.objects.filter(anime=self.anime).update(updated_at=timezone.now()-timedelta(days=1))
        cache.clear()
        self.assertEqual([], process_reminders())
        self.assertEqual(0, Notification.objects.filter(type='episode_available').count())

    def test_successful_full_dump_disappearance_clears_availability_and_failed_dump_preserves_it(self):
        with patch.object(dumps, 'download_dump', return_value=(Path('fixture.json'), True)), \
             patch.object(dumps, 'iter_json_array', side_effect=lambda path: iter([])), patch.object(dumps, '_mark_imported'):
            dumps._sync_catalog(True, 0, False, False)
        self.assertEqual([], KodikAvailability.objects.get(anime=self.anime).episodes)
        record_availability(self.anime, provider(2))
        with TemporaryDirectory() as folder, override_settings(KODIK_DUMP_DIR=folder), \
             patch.object(dumps, 'download_dump', side_effect=dumps.DumpError('offline')):
            dumps._sync_catalog(True, 0, False, False)
        self.assertEqual([1, 2], KodikAvailability.objects.get(anime=self.anime).episodes)


class ConcurrentEpisodeDeliveryTests(TransactionTestCase):
    def test_subscription_and_calendar_workers_share_one_durable_available_notice(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        cache.clear()
        user = User.objects.create_user(username='concurrent_episode')
        anime = Anime.objects.create(shikimori_id=1100, title_ru='Параллельные задачи', is_available=True)
        record_availability(anime, provider(2))
        UserLibrary.objects.create(user=user, anime=anime)
        merge_calendar([{'id': 1100, 'episode': 3, 'aired_at': timezone.now().isoformat(), 'kind': 'tv'}])
        release = CalendarRelease.objects.get(shikimori_id=1100)
        Reminder.objects.create(user=user, anime=anime, calendar_release=release,
            follow_schedule=True, reminder_time=release.aired_at)
        record_availability(anime, provider(3))
        barrier = Barrier(2)
        def run(function):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return function()
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run, process_subscriptions)
            second = pool.submit(run, process_reminders)
            first.result(timeout=30); second.result(timeout=30)
        self.assertEqual(1, Notification.objects.filter(user=user, type='episode_available').count())
        self.assertEqual(1, EpisodeNotice.objects.filter(user=user).count())
