"""Regression coverage for the project review of 2026-10-28."""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.base import ContentFile
from unittest.mock import patch
from apps.users.infrastructure.models.users import User, PrivacySettings, DataExport
from apps.users.application.data_management import collect_export_data
from django.utils import timezone
from datetime import timedelta

class ReviewRegressions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='audit-user', email='audit@example.test', password='Strong-password-764!')
        cls.other = User.objects.create_user(username='audit-other', email='other@example.test', password='Strong-password-764!')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_password_contract(self):
        r = self.client.post('/api/users/change-password/', {'old_password':'Strong-password-764!', 'new_password':'Changed-password-964!', 'confirm_password':'Changed-password-964!'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_verification_mutable(self):
        r = self.client.patch('/api/users/profile/', {'email_verified':True, 'phone_verified':True}, format='json')
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified or self.user.phone_verified)

    def test_private_avatar(self):
        self.user.avatar.save('review.txt', ContentFile(b'avatar'), save=True)
        PrivacySettings.objects.update_or_create(user=self.user, defaults={'who_can_see_profile_photo':'nobody'})
        self.client.force_authenticate(None)
        r = self.client.get(f'/api/users/profile/{self.user.pk}/')
        self.assertIsNone(r.data.get('avatar_url'))

    def test_missing_user(self):
        self.client.raise_request_exception = False
        r = self.client.get('/api/users/profile/99999999/')
        self.assertEqual(r.status_code, 404)

    def test_export_all_categories(self):
        from apps.users.application.data_management import EXPORT_CATEGORIES
        for category in sorted(EXPORT_CATEGORIES):
            try:
                value = collect_export_data(self.user, [category])
            except Exception as exc:
                self.fail(f"{category}: {exc}")

    def test_terminated_tokens_still_work(self):
        refresh = RefreshToken.for_user(self.user)
        r = self.client.post('/api/users/sessions/terminate-all/', {}, format='json')
        fresh = APIClient()
        r2 = fresh.post('/api/users/token/refresh/', {'refresh':str(refresh)}, format='json')
        self.assertEqual(r2.status_code, 401)

    def test_storage_shape(self):
        r = self.client.get('/api/users/storage-usage/')
        self.assertIn('breakdown', r.data)

    def test_anonymous_catalog_crud(self):
        from apps.anime.models import Anime
        anime = Anime.objects.create(title_ru='Тест аудита', slug='audit-anime', is_available=True)
        self.client.force_authenticate(None)
        r = self.client.patch('/api/anime/audit-anime/', {'description':'anonymous mutation'}, format='json')
        anime.refresh_from_db()
        self.assertEqual(r.status_code, 405)
        r = self.client.delete('/api/anime/audit-anime/')
        self.assertEqual(r.status_code, 405)

    def test_realtime_event_scope(self):
        event = {'type':'new_message', 'data': {'message': {'text':'private audit secret'}}, 'target_users':[self.other.pk]}
        with patch('core.redis_events.event_publisher.get_recent_events', return_value=[event]):
            r = self.client.get('/api/users/realtime/')
        self.assertEqual(r.status_code, 410)
        self.assertNotIn('events', r.data)

    def test_email_change_keeps_verification(self):
        self.user.email_verified = True
        self.user.save(update_fields=['email_verified'])
        r = self.client.patch('/api/users/profile/', {'email':'unverified-new@example.test'}, format='json')
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertEqual(self.user.email, 'audit@example.test')

    def test_delete_account_keeps_forwarded_file(self):
        from apps.social.infrastructure.models.social import PrivateChat, Message, Attachment
        from apps.social.application.conversations import get_conversation
        from apps.users.application.data_management import delete_user_account
        third = User.objects.create_user(username='audit-third', email='third@example.test', password='Strong-password-764!')
        origin_chat = PrivateChat.objects.create(user1=self.user, user2=self.other)
        dest_chat = PrivateChat.objects.create(user1=self.other, user2=third)
        first = Message.objects.create(private_chat=origin_chat, conversation=get_conversation(origin_chat), sender=self.user, text='original', seq=1)
        second = Message.objects.create(private_chat=dest_chat, conversation=get_conversation(dest_chat), sender=self.other, text='forwarded', forwarded_from=first, seq=1)
        a = Attachment.objects.create(message=first, type='file', file=ContentFile(b'forwarded', name='shared-audit.txt'), file_name='shared.txt', file_size=9, mime_type='text/plain')
        b = Attachment.objects.create(message=second, type='file', file=a.file.name, file_name='shared.txt', file_size=9, mime_type='text/plain')
        delete_user_account(self.user.pk)
        self.assertTrue(Attachment.objects.filter(pk=b.pk).exists())
        self.assertTrue(b.file.storage.exists(b.file.name))

    def test_calendar_alias(self):
        self.client.raise_request_exception = False
        r = self.client.get('/api/anime/catalog/calendar/')
        self.assertEqual(r.status_code, 200)

    def test_search_leaks_hidden_contact_data(self):
        self.other.phone_number = '+70000000000'
        self.other.save(update_fields=['phone_number'])
        PrivacySettings.objects.update_or_create(user=self.other, defaults={'who_can_see_email':'nobody', 'who_can_see_phone':'nobody', 'who_can_see_last_seen':'nobody'})
        r = self.client.get('/api/users/search/?search=audit-other')
        row = r.data['results'][0]
        self.assertIsNone(row.get('email'))
        self.assertIsNone(row.get('phone_number'))

    def test_unpublished_news_detail(self):
        from apps.social.infrastructure.models.social_news import News
        self.other.avatar.save('news-audit.txt', ContentFile(b'avatar'), save=True)
        item = News.objects.create(author=self.other, title='private draft', content='private draft body', is_published=False)
        self.client.force_authenticate(None)
        r = self.client.get(f'/api/social/news/{item.pk}/')
        self.assertEqual(r.status_code, 404)

    def test_user_search_query_growth(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        def count_queries():
            with CaptureQueriesContext(connection) as captured:
                r = self.client.get('/api/users/search/?search=audit-count-')
            return len(captured), r.status_code
        User.objects.create_user(username='audit-count-0', email='count0@example.test', password='password123!')
        one = count_queries()
        for index in range(1, 10):
            User.objects.create_user(username=f'audit-count-{index}', email=f'count{index}@example.test', password='password123!')
        ten = count_queries()
        self.assertLessEqual(ten[0], one[0] + 2)


    def test_news_without_author_avatar(self):
        from apps.social.infrastructure.models.social_news import News
        item = News.objects.create(author=self.other, title='published without avatar', content='body', is_published=True)
        self.client.force_authenticate(None)
        self.client.raise_request_exception = False
        r = self.client.get(f'/api/social/news/{item.pk}/')
        self.assertEqual(r.status_code, 200)

    def test_disabled_forwarding(self):
        from apps.social.infrastructure.models.social import PrivateChat, Message
        from apps.social.application.conversations import get_conversation
        third = User.objects.create_user(username='audit-third', email='third@example.test', password='Strong-password-764!')
        origin = PrivateChat.objects.create(user1=self.user, user2=self.other)
        dest = PrivateChat.objects.create(user1=self.other, user2=third)
        msg = Message.objects.create(private_chat=origin, conversation=get_conversation(origin), sender=self.user, text='private message', seq=1)
        PrivacySettings.objects.update_or_create(user=self.user, defaults={'allow_message_forwarding':False})
        self.client.force_authenticate(self.other)
        r = self.client.post(f'/api/social/messages/{msg.pk}/forward/', {'private_chat_id':dest.public_id}, format='json')
        self.assertEqual(r.status_code, 403)



    def test_bound_credentials_are_revoked_per_device(self):
        from django.core.cache import cache
        cache.clear()
        first, second = APIClient(), APIClient()
        body = {'email': self.user.email, 'password': 'Strong-password-764!'}
        login_a = first.post('/api/users/login/', body, format='json')
        login_b = second.post('/api/users/login/', body, format='json')
        self.assertEqual(login_a.status_code, 200)
        self.assertEqual(login_b.status_code, 200)
        a, b = login_a.data['tokens'], login_b.data['tokens']
        first.credentials(HTTP_AUTHORIZATION='Bearer ' + a['access'])
        second.credentials(HTTP_AUTHORIZATION='Bearer ' + b['access'])
        sessions = first.get('/api/users/sessions/active/').data
        self.assertEqual(sum(row['is_current_device'] for row in sessions), 1)
        self.assertEqual(first.post('/api/users/sessions/terminate-all/', {}, format='json').status_code, 200)
        self.assertEqual(first.get('/api/users/profile/').status_code, 200)
        self.assertEqual(second.get('/api/users/profile/').status_code, 401)
        self.assertEqual(APIClient().post('/api/users/token/refresh/', {'refresh': b['refresh']}, format='json').status_code, 401)
        self.assertEqual(APIClient().post('/api/users/token/refresh/', {'refresh': a['refresh']}, format='json').status_code, 200)

    def test_hidden_avatar_file_requires_owner_even_through_legacy_media_url(self):
        self.user.avatar.save('hidden-avatar.txt', ContentFile(b'private avatar'), save=True)
        PrivacySettings.objects.filter(user=self.user).update(who_can_see_profile_photo='nobody')
        for client, allowed in [(self.client, True), (APIClient(), False)]:
            for url in (self.user.avatar.url, '/data/media/' + self.user.avatar.name):
                response = client.get(url)
                self.assertEqual(response.status_code, 200 if allowed else 404)
                if allowed:
                    self.assertEqual(response['Cache-Control'], 'private, no-store')
                    # Consume through ClientHandler's wrapper; an extra close()
                    # would emit request_finished again inside TestCase's atomic.
                    self.assertEqual(b''.join(response.streaming_content), b'private avatar')

    def test_clear_cache_is_scoped_and_rejects_deleting_messages(self):
        from apps.users.application.storage_service import StorageService
        service = StorageService(self.user)
        folder = service._cache_path()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'example.tmp').write_bytes(b'cache')
        self.assertGreater(service.get_storage_usage()['cache'], 0)
        response = self.client.post('/api/users/clear-cache/', {'items':['cache']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse((folder / 'example.tmp').exists())
        self.assertEqual(self.client.post('/api/users/clear-cache/', {'items':['messages']}, format='json').status_code, 400)

    def test_sync_preferences_persist_without_claiming_a_background_job_ran(self):
        response = self.client.put('/api/users/sync-settings/', {'wifi_only':False}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.get('/api/users/sync-settings/').data['wifi_only'])
        self.assertEqual(self.client.post('/api/users/sync-settings/', {}, format='json').status_code, 409)

    def test_logout_revokes_header_credentials_without_a_cookie(self):
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        login = client.post('/api/users/login/', {'email':self.user.email, 'password':'Strong-password-764!'}, format='json')
        tokens = login.data['tokens']
        client.cookies.clear()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        self.assertEqual(client.post('/api/users/logout/', {'refresh':tokens['refresh']}, format='json').status_code, 200)
        self.assertEqual(client.get('/api/users/profile/').status_code, 401)

    def test_password_change_rotates_current_credentials_and_revokes_old_access(self):
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        login = client.post('/api/users/login/', {'email':self.user.email, 'password':'Strong-password-764!'}, format='json')
        old = login.data['tokens']['access']
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + old)
        response = client.post('/api/users/change-password/', {'current_password':'Strong-password-764!', 'new_password':'Other-strong-password-775!'}, format='json')
        self.assertEqual(response.status_code, 200)
        fresh = APIClient()
        fresh.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['tokens']['access'])
        self.assertEqual(fresh.get('/api/users/profile/').status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + old)
        self.assertEqual(client.get('/api/users/profile/').status_code, 401)

    def test_cookie_socket_authorization_expires_with_the_server_session(self):
        from django.contrib.sessions.models import Session
        from django.contrib.sessions.backends.db import SessionStore
        from rest_framework.exceptions import AuthenticationFailed
        from apps.users.application.token_sessions import validate_socket_session
        session = SessionStore()
        session['_auth_user_id'] = str(self.user.pk)
        session['_auth_user_hash'] = self.user.get_session_auth_hash()
        session.save()
        scope = {'session': session}
        validate_socket_session(scope, self.user)
        Session.objects.filter(session_key=session.session_key).delete()
        with self.assertRaises(AuthenticationFailed):
            validate_socket_session(scope, self.user)

    def test_legacy_requester_gets_bound_credentials_when_other_sessions_are_revoked(self):
        legacy = RefreshToken.for_user(self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(legacy.access_token))
        response = client.post('/api/users/sessions/terminate-all/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('tokens', response.data)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['tokens']['access'])
        self.assertEqual(client.get('/api/users/profile/').status_code, 200)
