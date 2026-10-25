from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from apps.anime.models import Anime, Excerpt
from apps.anime.application.excerpts import attachment_data
from apps.social.application.tests import make_user
from apps.social.infrastructure.models.social import PrivateChat, Message, PostAttachment
from apps.users.models import UserLibrary


class ExcerptTests(TestCase):
    def setUp(self):
        self.owner = make_user('excerpt_owner')
        self.other = make_user('excerpt_other')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.anime = Anime.objects.create(title_ru='Диапазон', title_en='Range', slug='range', episodes=12,
            kodik_link='https://kodikplayer.com/serial/1/hash/720p',
            raw_kodik_data={'type': 'anime-serial', 'translation': {'id': 77, 'title': 'Озвучка'},
                'seasons': {'2': {'episodes': {'3': 'https://kodikplayer.com/seria/3/hash/720p'}}}})
        self.payload = dict(anime_id=self.anime.pk, season=2, episode=3, translation_id=77,
                            start=10.25, end=11.75, duration=1200.5, title='', description='')

    def create(self, **values):
        response = self.client.post('/api/anime/excerpts/', {**self.payload, **values}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        return response.data

    def detail(self, pk): return f'/api/anime/excerpts/{pk}/'
    def shared(self, data): return '/api/anime/excerpts/shared/' + data['share_path'].split('/')[-1] + '/'

    def test_crud_search_and_cross_device(self):
        first = self.create(title='Первая', description='разговор')
        second = self.create(title='Вторая')
        device = APIClient(); device.force_authenticate(self.owner)
        self.assertEqual([second['id'], first['id']], [row['id'] for row in device.get('/api/anime/excerpts/').data['results']])
        for term in ('разговор', 'Первая', 'Range', 'Диапазон'):
            self.assertTrue(device.get('/api/anime/excerpts/', {'q': term}).data['results'])
        response = device.patch(self.detail(first['id']), {'start': 9.5, 'end': 12.5, 'title': 'Правка'}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual('Правка', self.client.get(self.detail(first['id'])).data['title'])
        self.assertEqual(204, device.delete(self.detail(first['id'])).status_code)
        self.assertEqual(404, self.client.get(self.detail(first['id'])).status_code)

    def test_range_and_immutable_identity_validation(self):
        for values in ({'start': -1}, {'end': 10.25}, {'end': 1201}, {'start': 'NaN'}, {'end': 'Infinity'},
                       {'episode': 4}, {'season': 3}, {'translation_id': 78}, {'duration': 0}):
            response = self.client.post('/api/anime/excerpts/', {**self.payload, **values}, format='json')
            self.assertEqual(400, response.status_code, (values, response.data))
        row = self.create()
        self.assertEqual((2, 3, 77), (row['season'], row['episode'], row['translation_id']))
        for values in ({'episode': 4}, {'translation_id': 78}, {'duration': 4000}, {'player_link': 'https://attacker.test'}, {'start': 12}):
            self.assertEqual(400, self.client.patch(self.detail(row['id']), values, format='json').status_code)

    def test_private_guest_share_and_permanent_revocation(self):
        row = self.create()
        self.client.force_authenticate(self.other)
        for method in ('get', 'patch', 'delete'):
            response = getattr(self.client, method)(self.detail(row['id']))
            self.assertEqual(404, response.status_code)
        self.assertEqual([], self.client.get('/api/anime/excerpts/').data['results'])
        guest = APIClient()
        self.assertIn(guest.post('/api/anime/excerpts/', self.payload, format='json').status_code, (401, 403))
        self.client.force_authenticate(self.owner)
        shared = self.client.patch(self.detail(row['id']), {'shared': True}, format='json').data
        url = self.shared(shared)
        self.assertEqual(200, guest.get(url).status_code)
        self.assertIn('no-store', guest.get(url)['Cache-Control'])
        self.client.patch(self.detail(row['id']), {'shared': False}, format='json')
        self.assertEqual(404, guest.get(url).status_code)
        self.assertIsNone(attachment_data(row['id']))
        shared_again = self.client.patch(self.detail(row['id']), {'shared': True}, format='json').data
        self.assertNotEqual(shared['share_path'], shared_again['share_path'])
        self.assertEqual(404, guest.get(url).status_code)
        self.assertEqual(200, guest.get(self.shared(shared_again)).status_code)

    def test_chat_attachment_only_own_and_live(self):
        row = self.create()
        chat = PrivateChat.objects.create(user1=self.owner, user2=self.other, public_id=85000001)
        path = f'/api/social/chats/{chat.public_id}/messages/'
        response = self.client.post(path, {'chat_type': 'private', 'excerpt_ids': [row['id']], 'client_message_id': 'excerpt-chat'}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        self.assertEqual('excerpt', response.data['attachments'][0]['type'])
        self.assertTrue(Excerpt.objects.get(pk=row['id']).shared)
        self.client.patch(self.detail(row['id']), {'title': 'Обновлено', 'end': 15}, format='json')
        self.client.force_authenticate(self.other)
        history = self.client.get(path, {'type': 'private'})
        self.assertEqual('Обновлено', history.data['results'][0]['attachments'][0]['data']['title'])
        response = self.client.post(path, {'chat_type': 'private', 'excerpt_ids': [row['id']], 'client_message_id': 'stolen'}, format='json')
        self.assertEqual(400, response.status_code)
        self.client.force_authenticate(self.owner)
        self.client.delete(self.detail(row['id']))
        self.assertTrue(self.client.get(path, {'type': 'private'}).data['results'][0]['attachments'][0]['data']['unavailable'])

    def test_post_attachment_live_access_and_rollback(self):
        row = self.create()
        response = self.client.post('/api/social/posts/', {'excerpt_ids': [row['id']], 'visibility': 'private'}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        post_id = response.data['id']
        post_path = f'/api/social/posts/{post_id}/'
        self.assertEqual('excerpt', response.data['attachments_data'][0]['content_type'])
        self.assertTrue(Excerpt.objects.get(pk=row['id']).shared)
        self.client.patch(self.detail(row['id']), {'title': 'Новая карточка'}, format='json')
        self.assertEqual('Новая карточка', self.client.get(post_path).data['attachments_data'][0]['excerpt_data']['title'])
        self.client.force_authenticate(self.other)
        self.assertIn(self.client.get(post_path).status_code, (403, 404))
        self.assertEqual(400, self.client.post('/api/social/posts/', {'excerpt_ids': [row['id']]}, format='json').status_code)
        self.client.force_authenticate(self.owner)
        self.client.patch(self.detail(row['id']), {'shared': False}, format='json')
        self.assertIsNone(self.client.get(post_path).data['attachments_data'][0]['excerpt_data'])
        self.assertEqual(1, PostAttachment.objects.filter(content_type='excerpt').count())

    def test_blocked_anime_and_playback_reads_do_not_touch_library(self):
        library = UserLibrary.objects.create(user=self.owner, anime=self.anime, status='planned')
        before = UserLibrary.objects.filter(pk=library.pk).values().get()
        row = self.create(shared=True)
        for _ in range(3):
            self.client.get(self.detail(row['id'])); APIClient().get(self.shared(row))
        self.assertEqual(before, UserLibrary.objects.filter(pk=library.pk).values().get())
        self.anime.is_available = False; self.anime.save(update_fields=['is_available'])
        self.assertEqual(404, self.client.get(self.detail(row['id'])).status_code)
        self.assertEqual(404, APIClient().get(self.shared(row)).status_code)
        self.assertIsNone(attachment_data(row['id']))
        self.assertEqual(404, self.client.post('/api/anime/excerpts/', self.payload, format='json').status_code)

    def test_provider_failure_and_film_identity(self):
        self.anime.shikimori_id = 99; self.anime.save(update_fields=['shikimori_id'])
        with patch('apps.anime.application.anime_service.anime_service.get_translations', side_effect=RuntimeError('offline')):
            self.assertEqual(503, self.client.post('/api/anime/excerpts/', {**self.payload, 'translation_id': 78}, format='json').status_code)
        self.anime.raw_kodik_data = {'type': 'anime', 'translation': {'id': 77, 'title': 'Film'}, 'link': 'https://kodikplayer.com/video/4/hash/720p'}
        self.anime.save(update_fields=['raw_kodik_data'])
        self.assertIn('/video/', self.create(season=1, episode=1)['player_link'])
