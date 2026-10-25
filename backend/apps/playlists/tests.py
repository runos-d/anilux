from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.anime.models import Anime
from apps.playlists.models import FavoritePlaylist, Playlist, PlaylistItem, PlaylistLike, PlaylistTopic

BASE = '/api/playlists/playlists/'


class DiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for slug, name in [('cozy', 'Уютное'), ('evening', 'На вечер'), ('beginners', 'Для новичков'),
                           ('friends', 'С друзьями'), ('thoughtful', 'Есть о чём подумать'),
                           ('adventure', 'Навстречу приключениям')]:
            PlaylistTopic.objects.get_or_create(slug=slug, defaults={'name': name})
        cls.owner = get_user_model().objects.create_user(username='playlist-author', password='test')
        cls.reader = get_user_model().objects.create_user(username='playlist-reader', password='test')
        cls.public = Playlist.objects.create(user=cls.owner, title='Вечер', description='Тихий космос')
        cls.other = Playlist.objects.create(user=cls.owner, title='Другой')
        cls.private = Playlist.objects.create(user=cls.owner, title='Секрет', visibility='private')
        cls.link = Playlist.objects.create(user=cls.owner, title='Ссылка', visibility='link')
        cls.public.topics.set(['cozy', 'evening'])
        cls.anime = Anime.objects.create(id=987001, title_ru='Космос', genres=['Фантастика', 'Драма'])
        with patch.object(Playlist, 'update_cover'):
            PlaylistItem.objects.create(playlist=cls.public, anime=cls.anime)

    def setUp(self):
        self.api = APIClient()

    def test_likes_are_idempotent_unique_persistent_and_separate_from_favorites(self):
        anonymous = self.api.get(BASE, {'is_public': True})
        self.assertIn('no-store', anonymous['Cache-Control'])
        self.assertIn('Authorization', anonymous['Vary'])
        self.api.force_authenticate(self.reader)
        FavoritePlaylist.objects.create(user=self.reader, playlist=self.public)
        for _ in range(2):
            response = self.api.put(f'{BASE}{self.public.pk}/like/')
            self.assertEqual({'is_liked': True, 'likes_count': 1}, response.data)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlaylistLike.objects.create(user=self.reader, playlist=self.public)
        fresh = APIClient()
        fresh.force_authenticate(self.reader)
        row = fresh.get(BASE, {'is_public': True}).data['results']
        row = next(p for p in row if p['id'] == self.public.pk)
        self.assertTrue(row['is_liked'])
        self.assertEqual((1, 1), (row['likes_count'], row['favorites_count']))
        for _ in range(2):
            self.assertEqual({'is_liked': False, 'likes_count': 0}, self.api.delete(f'{BASE}{self.public.pk}/like/').data)
        self.assertEqual(1, FavoritePlaylist.objects.count())
        guest = APIClient().get(BASE, {'is_public': True}).data['results']
        self.assertTrue(all(not p['is_liked'] for p in guest))

    def test_permissions_do_not_disclose_private_or_link_playlists(self):
        for user in (None, self.reader, self.owner):
            self.api.force_authenticate(user)
            for ordering in ('-likes_count', 'title', '-updated_at', '-favorites_count'):
                for path in (BASE, BASE + 'public/'):
                    data = self.api.get(path, {'is_public': True, 'ordering': ordering}).data
                    self.assertEqual({self.public.pk, self.other.pk}, {p['id'] for p in data['results']})
            for playlist in (self.private, self.link):
                for method in (self.api.put, self.api.delete):
                    self.assertIn(method(f'{BASE}{playlist.pk}/like/').status_code, (401, 403, 404))
        self.api.force_authenticate(self.reader)
        self.assertEqual(404, self.api.get(f'{BASE}{self.private.pk}/').status_code)
        self.assertEqual(403, self.api.patch(f'{BASE}{self.public.pk}/', {'title': 'Чужая правка'}).status_code)
        self.api.force_authenticate(None)
        self.assertIn(self.api.put(f'{BASE}{self.public.pk}/like/').status_code, (401, 403))

    def test_guest_can_read_public_items_without_disclosing_hidden_playlists(self):
        response = self.api.get(f'{BASE}{self.public.pk}/items/')
        self.assertEqual(200, response.status_code)
        self.assertEqual([self.anime.pk], [row['anime'] for row in response.data['results']])
        for playlist in (self.private, self.link):
            self.assertEqual(404, self.api.get(f'{BASE}{playlist.pk}/items/').status_code)

    def test_public_search_route_is_not_shadowed_by_the_detail_route(self):
        response = self.api.get(f'{BASE}search/', {'q': 'космос', 'limit': 7})
        self.assertEqual(200, response.status_code)
        self.assertEqual([self.public.pk], [row['id'] for row in response.data['results']])

    def test_all_filters_intersect_before_pagination_and_public_alias_matches(self):
        params = {'is_public': True, 'search': 'космос', 'topics': 'cozy,evening', 'genre': 'Фантастика,Драма', 'ordering': '-likes_count', 'period': 'week', 'page_size': 1}
        for path in (BASE, BASE + 'public/'):
            response = self.api.get(path, params)
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, response.data['count'])
            self.assertEqual(self.public.pk, response.data['results'][0]['id'])
        self.assertEqual(0, self.api.get(BASE, {**params, 'genre': 'Фантаст'}).data['count'])
        self.assertEqual(0, self.api.get(BASE, {**params, 'topics': 'beginners'}).data['count'])
        self.assertEqual(0, self.api.get(BASE, {**params, 'search': 'нет совпадений'}).data['count'])

    def test_period_filters_by_playlist_creation_time_and_pagination_ties_are_stable(self):
        now = timezone.now()
        PlaylistLike.objects.create(user=self.owner, playlist=self.public)
        PlaylistLike.objects.create(user=self.reader, playlist=self.public)
        PlaylistLike.objects.create(user=self.owner, playlist=self.other)
        Playlist.objects.filter(pk=self.public.pk).update(created_at=now - timedelta(days=20))
        Playlist.objects.filter(pk=self.other.pk).update(created_at=now - timedelta(days=2))
        expected = {
            'week': [self.other.pk],
            'month': [self.public.pk, self.other.pk],
            'all': [self.public.pk, self.other.pk],
        }
        for period, expected_ids in expected.items():
            data = self.api.get(BASE, {'is_public': True, 'ordering': '-likes_count', 'period': period}).data
            self.assertEqual(expected_ids, [row['id'] for row in data['results']])
        PlaylistLike.objects.all().delete()
        Playlist.objects.all().update(created_at=now)
        ids = [self.api.get(BASE, {'is_public': True, 'ordering': '-likes_count', 'page_size': 1, 'page': page}).data['results'][0]['id'] for page in (1, 2)]
        self.assertEqual(sorted([self.public.pk, self.other.pk]), ids)

    def test_new_updated_and_title_orders_have_stable_results(self):
        now = timezone.now()
        Playlist.objects.filter(pk=self.public.pk).update(created_at=now - timedelta(days=20), updated_at=now)
        Playlist.objects.filter(pk=self.other.pk).update(created_at=now, updated_at=now - timedelta(days=10))
        for ordering, first in [('-created_at', self.other), ('-updated_at', self.public), ('title', self.public)]:
            rows = self.api.get(BASE, {'is_public': True, 'ordering': ordering}).data['results']
            self.assertEqual(first.pk, rows[0]['id'])
        self.api.force_authenticate(self.owner)
        rows = self.api.get(BASE, {'is_public': True, 'my': True, 'ordering': '-likes_count'}).data['results']
        self.assertEqual({self.public.pk, self.other.pk}, {row['id'] for row in rows})

    def test_counts_do_not_multiply_and_card_queries_are_bounded(self):
        for user in (self.owner, self.reader):
            PlaylistLike.objects.create(user=user, playlist=self.public)
            FavoritePlaylist.objects.create(user=user, playlist=self.public)
        with patch.object(Playlist, 'update_cover'):
            PlaylistItem.objects.create(playlist=self.public, anime=self.anime)
        self.api.force_authenticate(self.reader)
        with self.assertNumQueries(4):
            data = self.api.get(BASE, {'is_public': True, 'ordering': '-likes_count'}).data
        row = data['results'][0]
        self.assertEqual((2, 2, 2), (row['likes_count'], row['favorites_count'], row['items_count']))

    def test_author_topic_validation_and_favorite_visibility(self):
        self.api.force_authenticate(self.owner)
        self.assertEqual(200, self.api.patch(f'{BASE}{self.public.pk}/', {'topics': ['beginners']}, format='json').status_code)
        self.assertEqual(['beginners'], list(self.public.topics.values_list('slug', flat=True)))
        for topics in (['invented'], ['cozy', 'evening', 'beginners', 'friends']):
            self.assertEqual(400, self.api.patch(f'{BASE}{self.public.pk}/', {'topics': topics}, format='json').status_code)
        created = self.api.post(BASE, {'title': 'Новый', 'topics': ['cozy']}, format='json')
        self.assertEqual(201, created.status_code)
        self.assertEqual(['cozy'], created.data['topics'])
        self.api.force_authenticate(self.reader)
        FavoritePlaylist.objects.create(user=self.reader, playlist=self.private)
        self.assertEqual(0, self.api.get(BASE, {'favorites': True}).data['count'])
        options = self.api.get(BASE + 'discovery-options/').data
        self.assertEqual(['Драма', 'Фантастика'], options['genres'])
        self.assertEqual(6, len(options['topics']))


class ConcurrentLikeTests(TransactionTestCase):
    def test_simultaneous_retries_and_removals_keep_one_row(self):
        user = get_user_model().objects.create_user(username='parallel-reader')
        playlist = Playlist.objects.create(user=user, title='Parallel')

        def command(method):
            close_old_connections()
            try:
                api = APIClient()
                api.force_authenticate(user)
                return getattr(api, method)(f'{BASE}{playlist.pk}/like/').status_code
            finally:
                close_old_connections()

        for method, expected in [('put', 1), ('delete', 0), ('put', 1)]:
            with ThreadPoolExecutor(max_workers=4) as pool:
                self.assertEqual([200] * 8, list(pool.map(command, [method] * 8)))
            self.assertEqual(expected, PlaylistLike.objects.filter(playlist=playlist).count())


class FastPlaylistWriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.playlists.topics import TOPICS
        for topic in TOPICS:
            PlaylistTopic.objects.update_or_create(slug=topic['slug'], defaults={'name': topic['name']})
        cls.user = get_user_model().objects.create_user(username='fast-playlist-author')
        Anime.objects.bulk_create([Anime(id=988000 + n, title_ru=f'История {n}', slug=f'fast-playlist-{n}', total_duration=24) for n in range(120)])

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def test_create_and_edit_are_atomic_and_never_download_posters(self):
        with patch('requests.get', side_effect=AssertionError('network on playlist save')):
            response = self.api.post(BASE, {'title': 'Подборка', 'topics': ['beginners', 'cozy'],
                                          'items': [{'anime_id': 988000 + n, 'notes': str(n)} for n in range(100)]}, format='json')
            self.assertEqual(201, response.status_code, response.data)
            playlist = Playlist.objects.get(pk=response.data['id'])
            self.assertEqual((100, 2400), (playlist.items.count(), playlist.total_duration))
            retained_id = playlist.items.get(anime_id=988001).pk
            nested = Playlist.objects.create(user=self.user, title='Вложенная', visibility='private')
            nested_item = PlaylistItem.objects.create(playlist=playlist, nested_playlist=nested, position=150)
            response = self.api.patch(f'{BASE}{playlist.pk}/', {'title': 'Обновлённая', 'items': [
                {'anime_id': 988001, 'notes': 'Обновлённая заметка'}, {'anime_id': 988101}]}, format='json')
            self.assertEqual(200, response.status_code, response.data)
            playlist.refresh_from_db()
            self.assertEqual(48, playlist.total_duration)
            self.assertEqual(retained_id, playlist.items.get(anime_id=988001).pk)
            self.assertEqual('Обновлённая заметка', playlist.items.get(pk=retained_id).notes)
            self.assertTrue(playlist.items.filter(pk=nested_item.pk).exists())
            response = self.api.patch(f'{BASE}{playlist.pk}/', {'title': 'Не сохранять', 'items': [{'anime_id': 99999999}]}, format='json')
            self.assertEqual(400, response.status_code)
            playlist.refresh_from_db()
            self.assertEqual('Обновлённая', playlist.title)
            self.assertEqual(3, playlist.items.count())

    def test_write_queries_do_not_grow_per_anime(self):
        counts = []
        for count in (2, 100):
            with CaptureQueriesContext(connection) as queries:
                response = self.api.post(BASE, {'title': 'Объём', 'items': [{'anime_id': 988000 + n} for n in range(count)]}, format='json')
            self.assertEqual(201, response.status_code, response.data)
            counts.append(len(queries))
        self.assertLessEqual(counts[1], counts[0] + 1, counts)

    def test_taxonomy_has_six_choices_one_per_group_and_retains_legacy(self):
        playlist = Playlist.objects.create(user=self.user, title='Прежняя')
        playlist.topics.set(['cozy', 'evening', 'friends'])
        self.assertEqual(200, self.api.patch(f'{BASE}{playlist.pk}/', {'title': 'Название', 'topics': ['cozy', 'evening', 'friends']}, format='json').status_code)
        for topics in (['beginners', 'friends'], ['cozy', 'thoughtful'], ['invented']):
            self.assertEqual(400, self.api.patch(f'{BASE}{playlist.pk}/', {'topics': topics}, format='json').status_code)
        self.assertEqual(200, self.api.patch(f'{BASE}{playlist.pk}/', {'topics': ['evening', 'cozy']}, format='json').status_code)
        with self.assertNumQueries(0):
            options = self.api.get(BASE + 'discovery-options/?topics_only=true')
        self.assertEqual(6, len(options.data['topics']))
        self.assertEqual({'occasion', 'mood'}, {topic['group'] for topic in options.data['topics']})

    def test_custom_cover_survives_item_changes_auto_cover_does_not_fetch(self):
        playlist = Playlist.objects.create(user=self.user, title='Своя обложка', cover_mode='custom', cover_image='playlist_covers/uploaded.jpg')
        with patch('requests.get', side_effect=AssertionError('remote cover')):
            self.assertEqual(200, self.api.patch(f'{BASE}{playlist.pk}/', {'items': [{'anime_id': 988000}]}, format='json').status_code)
            playlist.refresh_from_db()
            self.assertEqual('playlist_covers/uploaded.jpg', playlist.cover_image.name)
            detail = self.api.get(f'{BASE}{playlist.pk}/').data
            self.assertIn('uploaded.jpg', detail['cover_image'])
            response = self.api.post(f'{BASE}{playlist.pk}/update_cover/')
            self.assertEqual(200, response.status_code)
            self.assertIsNone(response.data['cover_image'])

    def test_bulk_add_and_duplicate_remain_bounded(self):
        playlist = Playlist.objects.create(user=self.user, title='Быстро')
        with patch('requests.get', side_effect=AssertionError('remote cover')):
            response = self.api.post(f'{BASE}{playlist.pk}/batch-add-items/', {'anime_ids': list(range(988000, 988100))}, format='json')
            self.assertEqual(100, response.data['added_count'])
            response = self.api.post(f'{BASE}{playlist.pk}/duplicate/')
            self.assertEqual(201, response.status_code, response.data)
            self.assertEqual(100, response.data['items_count'])
