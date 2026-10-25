from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.anime.infrastructure.models.anime import Anime
from apps.social.application import conversations as service
from apps.social.infrastructure.models.social import PrivateChat, GroupChat, ChatMember, Message, Attachment
from apps.social.infrastructure.models.social_chat import ChatInviteLink, ChatJoinRequest, PrivateChatSettings, GroupMemberSettings
from apps.users.infrastructure.models.users import User


class RequestedChatFixes(TestCase):
    def setUp(self):
        cache.clear()
        self.a = User.objects.create_user(username='requested_a', email='requested_a@test.local')
        self.b = User.objects.create_user(username='requested_b', email='requested_b@test.local')
        self.c = User.objects.create_user(username='requested_c', email='requested_c@test.local')
        self.private = PrivateChat.objects.create(user1=self.a, user2=self.b)
        self.group = GroupChat.objects.create(name='Closed group', created_by=self.a, is_public=False)
        self.members = {user.pk: ChatMember.objects.create(chat=self.group, user=user, is_admin=user == self.a) for user in [self.a, self.b]}
        self.client = APIClient()
        self.client.force_authenticate(self.a)
        enqueue = patch('apps.social.application.conversations.enqueue_event')
        enqueue.start(); self.addCleanup(enqueue.stop)

    def test_attachment_search_searches_all_catalog_and_paginates_without_duplicates(self):
        Anime.objects.bulk_create([Anime(title_ru=f'Other {i}', slug=f'other-search-{i}', score=10) for i in range(80)])
        Anime.objects.bulk_create([Anime(title_ru=f'Rare Catalog {i}', title_en=f'Rare Catalog {i}', slug=f'rare-search-{i}', score=1) for i in range(25)])
        first = self.client.get('/api/anime/attachment-search/', {'q': 'rare catalog', 'limit': 20}).data
        second = self.client.get('/api/anime/attachment-search/', {'q': 'rare catalog', 'limit': 20, 'page': 2}).data
        self.assertEqual(first['count'], 25)
        self.assertEqual([len(first['results']), len(second['results'])], [20, 5])
        self.assertTrue(first['has_more']); self.assertFalse(second['has_more'])
        self.assertEqual(len({row['id'] for row in first['results'] + second['results']}), 25)

    def test_attachment_search_supports_japanese_and_normalized_titles(self):
        one_piece = Anime.objects.create(title_ru='Ван-Пис', title_en='One Piece', title_jp='ワンピース')
        japanese = Anime.objects.create(title_ru='', title_en='', title_jp='ワンピース 映画', slug='japanese-search-only')
        for query in ['ВАН ПИС', 'OnePiece']:
            data = self.client.get('/api/anime/attachment-search/', {'q': query}).data
            self.assertEqual([row['id'] for row in data['results']], [one_piece.pk])
        data = self.client.get('/api/anime/attachment-search/', {'q': 'ワンピース'}).data
        self.assertEqual({row['id'] for row in data['results']}, {one_piece.pk, japanese.pk})

    def test_private_group_link_grants_access_without_approval_and_expires_in_24_hours(self):
        path = '/api/social/chat-invite-links/'
        before = timezone.now()
        response = self.client.post(path, {'chat': self.group.public_id,
            'expires_at': (before + timezone.timedelta(days=7)).isoformat()}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        invite = ChatInviteLink.objects.get(pk=response.data['id'])
        self.assertAlmostEqual((invite.expires_at - before).total_seconds(), 86400, delta=2)
        edited = self.client.patch(f'{path}{invite.pk}/', {'expires_at': (before + timezone.timedelta(days=30)).isoformat()}, format='json')
        self.assertEqual(edited.status_code, 200)
        invite.refresh_from_db()
        self.assertAlmostEqual((invite.expires_at - before).total_seconds(), 86400, delta=2)
        self.assertEqual(service.join_invite(invite.invite_link, self.c)['status'], 'joined')
        self.assertFalse(ChatJoinRequest.objects.filter(chat=self.group, user=self.c, status='pending').exists())
        self.client.force_authenticate(self.c)
        self.assertEqual(self.client.get(f'/api/social/group-chats/{self.group.public_id}/member-settings/').status_code, 200)

    def test_expired_and_legacy_indefinite_links_cannot_admit_new_members(self):
        invite = ChatInviteLink.objects.create(chat=self.group, creator=self.a)
        with patch('apps.social.infrastructure.models.social_chat.timezone.now', return_value=invite.effective_expires_at):
            with self.assertRaises(ValidationError): service.join_invite(invite.invite_link, self.c)
        ChatInviteLink.objects.filter(pk=invite.pk).update(created_at=timezone.now() - timezone.timedelta(hours=25), expires_at=None)
        with self.assertRaises(ValidationError): service.join_invite(invite.invite_link, self.c)
        self.assertFalse(ChatMember.objects.filter(chat=self.group, user=self.c).exists())

    def test_video_larger_than_25_mb_and_more_than_ten_small_files_can_be_sent(self):
        path = f'/api/social/chats/{self.private.public_id}/messages/'
        video = SimpleUploadedFile('video.mp4', b'v' * (26 * 1024 * 1024), content_type='video/mp4')
        response = self.client.post(path, {'chat_type': 'private', 'client_message_id': 'large-video', 'media_0': video}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['attachments'][0]['file_size'], 26 * 1024 * 1024)
        files = {f'media_{i}': SimpleUploadedFile(f'{i}.txt', b'hello') for i in range(11)}
        response = self.client.post(path, {'chat_type': 'private', 'client_message_id': 'eleven-files', **files}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data['attachments']), 11)

    def test_total_file_limit_and_appending_respect_existing_message_size(self):
        mib = 1024 * 1024
        service.validate_message_file_size([SimpleNamespace(size=200 * mib), SimpleNamespace(size=50 * mib)])
        with self.assertRaises(ValidationError):
            service.validate_message_file_size([SimpleNamespace(size=200 * mib), SimpleNamespace(size=50 * mib + 1)])
        message, _ = service.send_message(self.private, self.a, {'text': 'Files', 'client_message_id': 'file-total'})
        Attachment.objects.create(message=message, type='file', file=SimpleUploadedFile('small.txt', b'small'), file_size=service.MAX_MESSAGE_FILE_BYTES)
        with self.assertRaises(ValidationError): service.add_attachment(message.pk, self.a, SimpleUploadedFile('extra.txt', b'x'))
        self.assertEqual(message.attachments.count(), 1)

    def test_muted_private_and_group_chats_leave_sidebar_alerts_but_keep_unread_history(self):
        for chat in [self.private, self.group]: service.send_message(chat, self.a, {'text': 'Unread', 'client_message_id': f'unread-{chat.pk}'})
        self.client.force_authenticate(self.b)
        self.assertEqual(len(self.client.get('/api/social/chats/unread/').data), 2)
        private = PrivateChatSettings.objects.create(chat=self.private, user=self.b, notifications_enabled=False)
        group = GroupMemberSettings.objects.create(membership=self.members[self.b.pk], muted_until=timezone.now() + timezone.timedelta(hours=1))
        self.assertEqual(self.client.get('/api/social/chats/unread/').data, [])
        for chat, kind in [(self.private, 'private'), (self.group, 'group')]:
            self.assertGreater(self.client.get(f'/api/social/chats/{chat.public_id}/', {'type': kind}).data['unread_count'], 0)
        private.notifications_enabled = True; private.save()
        group.muted_until = timezone.now() - timezone.timedelta(seconds=1); group.save()
        self.assertEqual(len(self.client.get('/api/social/chats/unread/').data), 2)

    def test_block_and_unblock_messages_have_text_and_repeated_actions_are_idempotent(self):
        base = f'/api/social/private-chats/{self.private.public_id}'
        for action in ['block', 'unblock']:
            for _ in range(2): self.assertEqual(self.client.post(f'{base}/{action}/').status_code, 200)
        notices = Message.objects.filter(private_chat=self.private, message_type='system').order_by('pk')
        self.assertEqual(notices.count(), 2)
        self.assertEqual(list(notices.values_list('system_action', flat=True)), ['block', 'unblock'])
        self.assertTrue(all(message.text for message in notices))
        Message.objects.filter(pk=notices.first().pk).update(text='')
        history = self.client.get(f'/api/social/chats/{self.private.public_id}/messages/', {'type': 'private'}).data['results']
        self.assertTrue(all(message['text'] for message in history))
