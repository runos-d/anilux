from unittest import skipUnless

from django.test import TestCase
from rest_framework.test import APIClient

from apps.dubs.infrastructure.models.dubs import Person
from config.feature_flags import FEATURE_DUBS_ENABLED


@skipUnless(FEATURE_DUBS_ENABLED, "Dubs HTTP API is disabled in the first-release profile")
class PersonApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = Person.objects.create(
            name='Тестовый сейю',
            slug='test-voice-actor',
            roles=['voice_actor'],
        )
        Person.objects.create(
            name='Тестовый режиссёр',
            slug='test-director',
            roles=['director'],
        )

    def setUp(self):
        self.api = APIClient()

    def test_list_and_detail_do_not_build_an_automatic_json_field_filter(self):
        listing = self.api.get('/api/dubs/people/')
        self.assertEqual(200, listing.status_code)
        self.assertEqual(2, listing.data['count'])
        detail = self.api.get(f'/api/dubs/people/{self.actor.pk}/')
        self.assertEqual(200, detail.status_code)

    def test_role_query_uses_the_explicit_json_contains_filter(self):
        response = self.api.get('/api/dubs/people/', {'role': 'voice_actor'})
        self.assertEqual(200, response.status_code)
        self.assertEqual([str(self.actor.pk)], [row['id'] for row in response.data['results']])

    def test_unknown_person_is_not_found_instead_of_raising_server_error(self):
        self.assertEqual(404, self.api.get('/api/dubs/people/316/').status_code)
