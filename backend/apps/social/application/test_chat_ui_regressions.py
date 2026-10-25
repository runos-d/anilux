import io
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from apps.anime.infrastructure.models.anime import Anime
from apps.social.application import conversations as service
from apps.social.infrastructure.models.social import PrivateChat, GroupChat, ChatMember, MessageAttachment
from apps.social.infrastructure.models.social_chat import ChatTheme, ChatWallpaper
from apps.users.infrastructure.models.users import User


class ChatUIRegressions(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='ui_owner', email='ui_owner@test.local')
        self.peer = User.objects.create_user(username='ui_peer', email='ui_peer@test.local', avatar='avatars/installed.jpg')
        self.other = User.objects.create_user(username='ui_other', email='ui_other@test.local')
        self.private = PrivateChat.objects.create(user1=self.owner, user2=self.peer, public_id=67936103)
        self.group = GroupChat.objects.create(name='UI group', created_by=self.owner, public_id=67936104)
        ChatMember.objects.create(chat=self.group, user=self.owner, is_admin=True)
        ChatMember.objects.create(chat=self.group, user=self.peer)
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        mock = patch('apps.social.application.conversations.enqueue_event')
        mock.start()
        self.addCleanup(mock.stop)

    def base(self, kind):
        chat = self.private if kind == 'private' else self.group
        return f'/api/social/chat-settings/{kind}/{chat.public_id}'

    def test_theme_wallpaper_and_card_radii_persist_with_public_ids_and_warm_cache(self):
        for kind, chat in [('private', self.private), ('group', self.group)]:
            with self.subTest(kind=kind):
                base = self.base(kind)
                self.assertNotEqual(chat.pk, chat.public_id)
                self.assertEqual(self.client.get(base + '/all/').status_code, 200)
                theme = {'message_color_mine': '#123456', 'font_size_px': 18, 'anime_card_border_radius': 22, 'playlist_card_border_radius': 25}
                response = self.client.post(base + '/theme/set/', theme, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                response = self.client.post(base + '/wallpaper/set/', {'wallpaper_type': 'gradient', 'wallpaper_color': '#234567', 'wallpaper_color2': '#345678', 'gradient_angle': 90}, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                saved = self.client.get(base + '/all/').data
                for key, value in theme.items():
                    self.assertEqual(saved['theme'][key], value)
                self.assertEqual(saved['wallpaper']['wallpaper_color'], '#234567')
                lookup = {'private_chat': chat} if kind == 'private' else {'chat': chat}
                self.assertEqual(ChatTheme.objects.filter(user=self.owner, **lookup).count(), 1)
                self.assertEqual(ChatWallpaper.objects.filter(user=self.owner, **lookup).count(), 1)
                self.assertEqual(self.client.delete(base + '/theme/reset/').status_code, 200)
                self.assertEqual(self.client.delete(base + '/wallpaper/reset/').status_code, 200)
                self.assertEqual(self.client.get(base + '/theme/').data['theme']['anime_card_border_radius'], 12)
                self.assertIsNone(self.client.get(base + '/wallpaper/').data['wallpaper'])

    def test_wallpaper_upload_uses_private_record_id(self):
        output = io.BytesIO()
        Image.new('RGB', (8, 8), '#123456').save(output, 'PNG')
        response = self.client.post(self.base('private') + '/wallpaper/set/', {'wallpaper_image': SimpleUploadedFile('wallpaper.png', output.getvalue(), content_type='image/png'), 'wallpaper_blur': '5'}, format='multipart')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(ChatWallpaper.objects.get(user=self.owner).private_chat_id, self.private.pk)
        self.assertEqual(self.client.get(self.base('private') + '/wallpaper/').data['wallpaper']['wallpaper_blur'], 5)

    def test_presets_and_bulk_updates_use_public_ids(self):
        from apps.social.application.chat_settings_service import ChatSettingsService
        for kind in ['private', 'group']:
            base = self.base(kind)
            for noun, presets in [('theme', ChatSettingsService.PRESET_THEMES), ('wallpaper', ChatSettingsService.PRESET_WALLPAPERS)]:
                response = self.client.post(f'{base}/{noun}/preset/', {'preset_id': presets[0]['id']}, format='json')
                self.assertEqual(response.status_code, 200, response.data)
            response = self.client.post(base + '/bulk-update/', {'theme': {'font_size_px': 16}, 'wallpaper': {'wallpaper_color': '#456789'}}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(self.client.get(base + '/all/').data['theme']['font_size_px'], 16)

    def test_customization_rejects_inaccessible_chats_and_invalid_values(self):
        response = self.client.post(self.base('private') + '/theme/set/', {'font_size_px': 'invalid'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(self.base('private') + '/theme/set/', {'font_size_px': 17}, format='json').status_code, 404)
        self.assertFalse(ChatTheme.objects.exists())

    def test_installed_avatar_is_present_in_fresh_chat_and_both_lists(self):
        detail = self.client.get(f'/api/social/chats/{self.private.public_id}/', {'type': 'private'}).data
        self.assertIn('avatars/installed.jpg', detail['other_user']['avatar_url'])
        rows = self.client.get('/api/social/private-chats/').data
        if isinstance(rows, dict): rows = rows['results']
        self.assertIn('avatars/installed.jpg', rows[0]['other_user']['avatar_url'])
        rows = self.client.get('/api/social/chats/').data
        row = next(row for row in rows if row['id'] == self.private.public_id)
        self.assertIn('avatars/installed.jpg', row['other_user']['avatar'])

    def test_administrator_conversation_is_a_real_private_chat(self):
        administrator = User.objects.create_user(
            username='support_admin', email='support@test.local', is_staff=True
        )
        path = '/api/social/private-chats/administrator/'

        created = self.client.post(path)
        self.assertEqual(created.status_code, 201, created.data)
        self.assertTrue(created.data['is_support'])
        self.assertEqual(created.data['name'], 'Администратор')
        chat_id = created.data['id']

        repeated = self.client.post(path)
        self.assertEqual(repeated.status_code, 200, repeated.data)
        self.assertEqual(repeated.data['id'], chat_id)
        self.assertEqual(PrivateChat.objects.filter(is_support=True).count(), 1)

        sent = self.client.post(
            f'/api/social/chats/{chat_id}/messages/',
            {'text': 'Нужна помощь', 'chat_type': 'private'},
            format='json',
        )
        self.assertEqual(sent.status_code, 201, sent.data)

        self.client.force_authenticate(administrator)
        rows = self.client.get('/api/social/private-chats/').data
        if isinstance(rows, dict):
            rows = rows['results']
        support = next(row for row in rows if row['id'] == chat_id)
        self.assertTrue(support['is_support'])
        self.assertEqual(support['other_user']['id'], self.owner.pk)

    def test_public_discussion_join_updates_counts_membership_and_settings_idempotently(self):
        anime = Anime.objects.create(title_ru='Discussion membership')
        chat = GroupChat.objects.create(name='Discussion', anime=anime, is_public=True,
            discussion_type='anime', folder_type='discussions')
        ChatMember.objects.create(chat=chat, user=self.owner)
        detail_path = f'/api/social/chats/{chat.public_id}/'
        settings_path = f'/api/social/group-chats/{chat.public_id}/member-settings/'
        self.client.force_authenticate(self.peer)
        before = self.client.get(detail_path, {'type': 'group'})
        self.assertEqual(before.data['members_count'], 1)
        self.assertIsNone(before.data['user_role'])
        self.assertEqual(self.client.get(settings_path).status_code, 403)
        for _ in range(2):
            joined = self.client.post(f'/api/social/anime/{anime.pk}/discussion-group/join/')
            self.assertEqual(joined.status_code, 200, joined.data)
            self.assertEqual(joined.data['id'], chat.public_id)
            self.assertEqual(joined.data['members_count'], 2)
            self.assertIsNotNone(joined.data['user_role'])
        self.assertEqual(self.client.get(settings_path).status_code, 200)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(detail_path, {'type': 'group'}).data['members_count'], 2)

    def test_group_online_count_uses_presence_instead_of_legacy_database_flag(self):
        User.objects.filter(pk=self.peer.pk).update(is_online=True)
        path = f'/api/social/chats/{self.group.public_id}/'
        with patch('core.online_status.online_status.get_users_data', return_value={}):
            self.assertEqual(self.client.get(path, {'type': 'group'}).data['online_count'], 0)
        with patch('core.online_status.online_status.get_users_data', return_value={self.peer.pk: {'is_active': True}}):
            self.assertEqual(self.client.get(path, {'type': 'group'}).data['online_count'], 1)

    def test_anime_titles_search_respects_history_clear_and_membership(self):
        anime = Anime.objects.create(title_ru='Ван Пис', title_en='One Piece', title_jp='ワンピース')
        message, _ = service.send_message(self.private, self.owner, {'shared_anime': anime, 'client_message_id': 'anime-search'})
        for query in ['Ван', 'Piece', 'ワン']:
            response = self.client.get('/api/social/messages/search/', {'chat_id': self.private.public_id, 'type': 'private', 'q': query})
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual([row['id'] for row in response.data], [message.pk])
        service.clear_history(self.private, self.owner)
        self.assertEqual(self.client.get('/api/social/messages/search/', {'chat_id': self.private.public_id, 'type': 'private', 'q': 'Piece'}).data, [])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/social/messages/search/', {'chat_id': self.private.public_id, 'type': 'private', 'q': 'Piece'}).status_code, 404)

    def test_archive_is_listed_for_its_owner_and_can_be_restored(self):
        path = f'/api/social/private-chats/{self.private.public_id}/settings/'
        self.assertEqual(self.client.put(path, {'is_archived': True}, format='json').status_code, 200)
        rows = self.client.get('/api/social/private-chats/').data
        if isinstance(rows, dict): rows = rows['results']
        self.assertTrue(rows[0]['user_settings']['archived'])
        self.assertFalse(self.private.get_user_settings(self.peer)['archived'])
        self.assertEqual(self.client.put(path, {'archived': False}, format='json').status_code, 200)
        self.assertFalse(self.client.get(path).data['is_archived'])

    def test_search_finds_multiple_anime_cards_once_and_skips_deleted_messages(self):
        anime = Anime.objects.create(title_ru='Ван Пис', title_en='One Piece')
        another = Anime.objects.create(title_ru='Ван Пис: фильм', title_en='One Piece movie')
        message, _ = service.send_message(self.group, self.owner, {'text': 'Советую посмотреть', 'client_message_id': 'multiple-anime-search'})
        for item in [anime, another]:
            MessageAttachment.objects.create(message=message, content_type='anime', object_id=item.pk)
        params = {'chat_id': self.group.public_id, 'type': 'group', 'q': 'Piece'}
        response = self.client.get('/api/social/messages/search/', params)
        self.assertEqual([row['id'] for row in response.data], [message.pk])
        service.change_message(message.pk, self.owner, delete=True)
        self.assertEqual(self.client.get('/api/social/messages/search/', params).data, [])

    def test_card_only_messages_accept_json_and_multipart_aliases(self):
        anime = Anime.objects.create(title_ru='Карточка без текста')
        path = f'/api/social/chats/{self.private.public_id}/messages/'
        for encoding in ['json', 'multipart']:
            for key in ['anime_ids', 'anime_ids[]']:
                response = self.client.post(path, {key: [anime.pk], 'chat_type': 'private', 'client_message_id': f'{encoding}-{key}'}, format=encoding)
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data['attachments'][0]['data']['id'], anime.pk)

    def test_group_name_description_and_basic_notifications_persist(self):
        path = f'/api/social/group-chats/{self.group.public_id}/'
        response = self.client.patch(path, {'name': 'Новое название', 'description': 'Описание группы'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Новое название')
        self.assertEqual(self.group.description, 'Описание группы')
        for kind, chat in [('private', self.private), ('group', self.group)]:
            path = f'/api/social/{kind}-chats/{chat.public_id}/' + ('user-settings/' if kind == 'private' else 'member-settings/')
            response = self.client.put(path, {'notifications_enabled': False, 'muted_until': None}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertFalse(self.client.get(path).data['notifications_enabled'])
