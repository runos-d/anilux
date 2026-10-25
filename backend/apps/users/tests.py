from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.infrastructure.models.users import User, UserSession, UserSettings
from apps.social.infrastructure.models.social import Follow

UserModel = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = UserModel.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        user = UserModel.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_str_representation(self):
        user = UserModel.objects.create_user(username='str_user', email='str@test.com', password='testpass123')
        self.assertIn('str_user', str(user))

    def test_generate_unique_id(self):
        user = UserModel.objects.create_user(username='uid_user', email='uid@test.com', password='testpass123')
        unique_id = user.generate_unique_id()
        self.assertIsNotNone(unique_id)
        self.assertEqual(len(unique_id), 12)
        self.assertTrue(unique_id.isdigit())

    def test_ensure_unique_id(self):
        user = UserModel.objects.create_user(username='ensure_user', email='ensure@test.com', password='testpass123')
        unique_id = user.ensure_unique_id()
        self.assertIsNotNone(unique_id)
        self.assertEqual(user.unique_id, unique_id)


class UserSessionModelTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(username='session_user', email='session@test.com', password='testpass123')

    def test_create_user_session(self):
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_session_key',
            device_info='Chrome on Windows',
            ip_address='127.0.0.1',
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.session_key, 'test_session_key')

    def test_str_representation(self):
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_key',
            device_info='Test Device',
        )
        self.assertIn('session_user', str(session))


class UserSettingsModelTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(username='settings_user', email='settings@test.com', password='testpass123')

    def test_create_user_settings(self):
        settings, _ = UserSettings.objects.get_or_create(
            user=self.user,
            defaults={'theme': 'dark', 'ui_style': 'modern'},
        )
        settings.theme = 'dark'
        settings.ui_style = 'modern'
        settings.save()
        self.assertEqual(settings.user, self.user)
        self.assertEqual(settings.theme, 'dark')

    def test_str_representation(self):
        settings, _ = UserSettings.objects.get_or_create(user=self.user)
        self.assertIn('settings_user', str(settings))


class UserAPIViewTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(username='api_user', email='api@test.com', password='testpass123')
        self.client = APIClient()

    def test_current_user_includes_follow_counts(self):
        follower = UserModel.objects.create_user(
            username='follower', email='follower@test.com', password='testpass123'
        )
        second_follower = UserModel.objects.create_user(
            username='second_follower', email='second-follower@test.com', password='testpass123'
        )
        followed = UserModel.objects.create_user(
            username='followed', email='followed@test.com', password='testpass123'
        )
        Follow.objects.create(follower=follower, following=self.user)
        Follow.objects.create(follower=second_follower, following=self.user)
        Follow.objects.create(follower=self.user, following=followed)
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/users/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['followers_count'], 2)
        self.assertEqual(response.data['following_count'], 1)
        self.assertFalse(response.data['is_premium'])
        self.assertIsNone(response.data['subscription'])

    def test_refresh_for_deleted_user_returns_unauthorized(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.user.delete()

        response = self.client.post(
            '/api/users/token/refresh/',
            {'refresh': refresh},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'token_not_valid')
