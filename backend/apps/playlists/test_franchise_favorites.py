from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.anime.models import Anime, Franchise
from apps.playlists.models import FavoriteAnime
from apps.users.models import UserLibrary


class FranchiseFavoriteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='franchise-favorites',
            password='test',
        )
        self.franchise = Franchise.objects.create(
            name='Любимая франшиза',
            slug='favorite-franchise',
        )
        self.parts = [
            Anime.objects.create(
                title_ru=f'Любимая часть {index}',
                slug=f'favorite-part-{index}',
                year=2024,
                franchise=self.franchise,
                franchise_order=index,
            )
            for index in range(1, 4)
        ]
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.franchise_url = (
            f'/api/playlists/favorites/anime/franchise/{self.franchise.pk}/'
        )
        self.collection_url = '/api/users/library/'

    def grouped_collection(self):
        response = self.api.get(
            self.collection_url,
            {'is_favorite': 'true', 'group_franchises': 'true'},
        )
        self.assertEqual(200, response.status_code, response.data)
        return response.data

    def test_franchise_toggle_changes_every_part_atomically(self):
        response = self.api.put(self.franchise_url)
        self.assertEqual(200, response.status_code, response.data)
        self.assertTrue(response.data['is_favorite'])
        self.assertEqual(
            {part.pk for part in self.parts},
            set(response.data['anime_ids']),
        )
        self.assertEqual(3, FavoriteAnime.objects.filter(user=self.user).count())
        self.assertEqual(
            3,
            UserLibrary.objects.filter(user=self.user, is_favorite=True).count(),
        )
        self.assertEqual(
            {part.pk for part in self.parts},
            set(self.api.get('/api/playlists/favorites/anime/ids/').data['anime_ids']),
        )

        collection = self.grouped_collection()
        self.assertEqual(1, collection['count'])
        card = collection['results'][0]
        self.assertEqual('franchise', card['item_type'])
        self.assertEqual(self.franchise.pk, card['franchise_id'])
        self.assertEqual(
            {part.pk for part in self.parts},
            {entry['id'] for entry in card['franchise']['entries']},
        )

        response = self.api.delete(self.franchise_url)
        self.assertEqual(200, response.status_code, response.data)
        self.assertFalse(response.data['is_favorite'])
        self.assertFalse(FavoriteAnime.objects.filter(user=self.user).exists())
        self.assertFalse(
            UserLibrary.objects.filter(user=self.user, is_favorite=True).exists()
        )

    def test_individual_parts_collapse_only_when_the_franchise_is_complete(self):
        for part in self.parts[:2]:
            response = self.api.post(
                '/api/playlists/favorites/anime/',
                {'anime': part.pk},
                format='json',
            )
            self.assertEqual(201, response.status_code, response.data)

        collection = self.grouped_collection()
        self.assertEqual(2, collection['count'])
        self.assertEqual(
            {'anime'},
            {row['item_type'] for row in collection['results']},
        )

        response = self.api.post(
            '/api/playlists/favorites/anime/',
            {'anime': self.parts[2].pk},
            format='json',
        )
        self.assertEqual(201, response.status_code, response.data)
        collection = self.grouped_collection()
        self.assertEqual(1, collection['count'])
        self.assertEqual('franchise', collection['results'][0]['item_type'])

        response = self.api.delete(
            '/api/playlists/favorites/anime/remove/',
            {'anime_id': self.parts[2].pk},
            format='json',
        )
        self.assertEqual(204, response.status_code, response.data)
        collection = self.grouped_collection()
        self.assertEqual(2, collection['count'])
        self.assertEqual(
            {part.pk for part in self.parts[:2]},
            {row['anime_id'] for row in collection['results']},
        )
