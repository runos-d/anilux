import io
import json
import zipfile
from unittest.mock import patch
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import GroupChat, ChatMember, Message, Attachment
from apps.social.infrastructure.models.social_chat import ChatBackup, ChatBan, ChatTopic, MessageReaction, MessagePin, ScheduledMessage
from apps.social.infrastructure.models.conversation import ChatEvent
from apps.social.infrastructure.chat_storage import private_file_url, chat_private_storage
from apps.social.application import conversations as service
from apps.social.application.chat_backups import build_backup, restore_backup


class ChatExtensionsTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='ext_owner', email='ext_a@test.local')
        self.b = User.objects.create_user(username='ext_member', email='ext_b@test.local')
        self.c = User.objects.create_user(username='ext_other', email='ext_c@test.local')
        self.chat = GroupChat.objects.create(name='Extensions', created_by=self.a)
        ChatMember.objects.create(chat=self.chat, user=self.a, is_admin=True)
        ChatMember.objects.create(chat=self.chat, user=self.b)
        self.client = APIClient()
        self.client.force_authenticate(self.a)
        self.base = f'/api/social/group-chats/{self.chat.public_id}'
        mock = patch('apps.social.application.conversations.enqueue_event')
        mock.start()
        self.addCleanup(mock.stop)

    def message(self, text='saved', key='archive-message', **values):
        return service.send_message(self.chat, self.a, dict(text=text, client_message_id=key, **values))[0]

    def attachment(self, message):
        return Attachment.objects.create(message=message, type='file',
            file=SimpleUploadedFile('payload.txt', b'0123456789', content_type='text/plain'),
            file_name='payload.txt', file_size=10, mime_type='text/plain')

    def backup(self):
        return build_backup(ChatBackup.objects.create(chat=self.chat, created_by=self.a).pk)

    def test_general_settings_round_trip_slow_mode_and_privacy(self):
        path = self.base + '/settings/'
        result = self.client.put(path, {'has_hidden_members': True, 'restrict_saving_content': True,
            'slow_mode_enabled': True, 'slow_mode_delay': 7}, format='json')
        self.assertEqual(200, result.status_code, result.data)
        self.assertEqual(7, self.client.get(path).data['slow_mode_delay'])
        self.chat.refresh_from_db()
        self.assertEqual(7, self.chat.slow_mode_delay)
        self.client.force_authenticate(self.b)
        self.assertEqual(403, self.client.get(self.base + '/members/').status_code)
        self.assertEqual(403, self.client.patch(path, {'has_hidden_members': False}, format='json').status_code)

    def test_invalid_settings_are_atomic_and_default_permissions_work(self):
        path = self.base + '/settings/'
        result = self.client.patch(path, {'has_hidden_members': True, 'slow_mode_delay': -1}, format='json')
        self.assertEqual(400, result.status_code)
        self.chat.refresh_from_db()
        self.assertFalse(self.chat.has_hidden_members)
        self.assertEqual(400, self.client.patch(path, {'fake': True}, format='json').status_code)
        self.client.patch(path, {'can_invite_users': True, 'can_pin_messages': True}, format='json')
        ChatMember.objects.filter(chat=self.chat, user=self.b).update(can_invite_users=True, can_pin_messages=True)
        self.chat.refresh_from_db()
        service.require_permission(self.chat, self.b, 'can_invite_users')
        service.require_permission(self.chat, self.b, 'can_pin_messages')

    def test_private_media_requires_current_access_and_legacy_urls_are_denied(self):
        attachment = self.attachment(self.message())
        path = chat_private_storage.url(attachment.file.name)
        anonymous = APIClient()
        self.assertEqual(403, anonymous.get(path).status_code)
        request = type('Request', (), {'user': self.b, 'build_absolute_uri': lambda _, url: url})()
        signed = private_file_url(attachment.file, request)
        response = anonymous.get(signed)
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'0123456789', b''.join(response.streaming_content))
        self.assertEqual('private, no-store', response['Cache-Control'])
        for prefix in ('/media/', '/data/media/'):
            self.assertEqual(404, anonymous.get(prefix + attachment.file.name).status_code)
        self.client.force_authenticate(self.c)
        self.assertEqual(404, self.client.get(path).status_code)
        ChatBan.objects.create(chat=self.chat, user=self.b, banned_by=self.a)
        self.assertEqual(404, anonymous.get(signed).status_code)

    def test_media_ranges_invalid_tickets_and_personal_clear(self):
        attachment = self.attachment(self.message())
        path = chat_private_storage.url(attachment.file.name)
        response = self.client.get(path, HTTP_RANGE='bytes=2-4')
        self.assertEqual(206, response.status_code)
        self.assertEqual(b'234', b''.join(response.streaming_content))
        response = self.client.get(path, HTTP_RANGE='bytes=-2')
        self.assertEqual(b'89', b''.join(response.streaming_content))
        self.assertEqual(416, self.client.get(path, HTTP_RANGE='bytes=99-').status_code)
        self.assertEqual(403, self.client.get(path + '?ticket=wrong').status_code)
        self.client.force_authenticate(self.b)
        service.clear_history(self.chat, self.b)
        self.assertEqual(404, self.client.get(path).status_code)

    def test_protected_content_cannot_be_forwarded_or_downloaded(self):
        attachment = self.attachment(self.message())
        self.chat.restrict_saving_content = True
        self.chat.save(update_fields=['restrict_saving_content'])
        self.client.force_authenticate(self.b)
        self.assertEqual(404, self.client.get(chat_private_storage.url(attachment.file.name) + '?download=1').status_code)
        response = self.client.post(f'/api/social/messages/{attachment.message_id}/forward/',
            {'chat_id': self.chat.public_id, 'chat_type': 'group'}, format='json')
        self.assertEqual(403, response.status_code, response.data)

    def test_scheduled_files_are_visible_only_to_the_sender(self):
        job = ScheduledMessage.objects.create(chat=self.chat, sender=self.a,
            scheduled_at=timezone.now() + timedelta(hours=1), media=ContentFile(b'planned', name='planned.txt'))
        path = chat_private_storage.url(job.media.name)
        response = self.client.get(path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'planned', b''.join(response.streaming_content))
        self.client.force_authenticate(self.b)
        self.assertEqual(404, self.client.get(path).status_code)
        self.assertEqual(404, self.client.get('/media/' + job.media.name).status_code)

    def test_background_backup_uses_existing_record_and_download_is_private(self):
        self.message()
        with patch('apps.social.application.tasks.backup_chat_task.delay') as queued, self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/api/social/chat-backups/', {'chat': self.chat.public_id, 'status': 'completed', 'file_size': 9}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        queued.assert_called_once_with(response.data['id'])
        backup = build_backup(response.data['id'])
        again = build_backup(backup.pk)
        self.assertEqual(backup.backup_file.name, again.backup_file.name)
        self.assertEqual(1, ChatBackup.objects.count())
        response = self.client.get(f'/api/social/chat-backups/{backup.pk}/download/')
        self.assertEqual(200, response.status_code)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'PK'))
        self.client.force_authenticate(self.b)
        self.assertEqual(404, self.client.get(f'/api/social/chat-backups/{backup.pk}/download/').status_code)
        self.assertEqual(403, self.client.post('/api/social/chat-backups/', {'chat': self.chat.public_id}, format='json').status_code)

    def test_archive_restores_dependencies_files_and_versions_without_reexecuting_jobs(self):
        topic = ChatTopic.objects.create(chat=self.chat, title='Topic', slug='topic')
        first = self.message(topic_id=topic.pk)
        second = self.message(text='reply', key='archive-reply', reply_to=first, topic_id=topic.pk)
        attachment = self.attachment(first)
        MessageReaction.objects.create(message=first, user=self.b, emoji='👍')
        MessagePin.objects.create(chat=self.chat, message=first, pinned_by=self.a)
        job = ScheduledMessage.objects.create(chat=self.chat, sender=self.a, text='later', scheduled_at=timezone.now() + timedelta(hours=1))
        backup = self.backup()
        with zipfile.ZipFile(backup.backup_file.open('rb')) as archive:
            manifest = json.loads(archive.read('manifest.json'))
        backup.backup_file.close()
        self.assertEqual(1, len(manifest['files']))
        first.refresh_from_db()
        original_time = first.created_at
        service.change_message(first.pk, self.a, delete=True)
        version = Message.objects.get(pk=first.pk).version
        MessageReaction.objects.all().delete()
        MessagePin.objects.all().delete()
        ScheduledMessage.objects.filter(pk=job.pk).delete()
        attachment.file.storage.delete(attachment.file.name)
        preview = restore_backup(backup.pk, self.a, dry_run=True)
        self.assertTrue(preview['dry_run'])
        self.assertTrue(Message.objects.get(pk=first.pk).is_deleted)
        self.assertFalse(attachment.file.storage.exists(attachment.file.name))
        restore_backup(backup.pk, self.a)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(original_time, first.created_at)
        self.assertFalse(first.is_deleted)
        self.assertGreater(first.version, version)
        self.assertEqual(first.pk, second.reply_to_id)
        self.assertEqual(topic.pk, second.topic_id)
        self.assertEqual({'👍': [self.b.pk]}, first.reactions)
        self.assertTrue(first.is_pinned)
        self.assertTrue(attachment.file.storage.exists(attachment.file.name))
        self.assertEqual('cancelled', ScheduledMessage.objects.get(pk=job.pk).status)
        events = ChatEvent.objects.filter(kind='chat_restored').count()
        self.assertTrue(restore_backup(backup.pk, self.a)['already_restored'])
        self.assertEqual(events, ChatEvent.objects.filter(kind='chat_restored').count())

    def test_restore_preserves_new_owner_bans_and_messages_and_hides_late_clear(self):
        first = self.message()
        backup = self.backup()
        service.clear_history(self.chat, self.a, for_all=True)
        clear_event = ChatEvent.objects.filter(kind='chat_cleared').last()
        newest = self.message(text='newer', key='newer')
        ChatMember.objects.create(chat=self.chat, user=self.c, is_admin=True)
        self.chat.created_by = self.c
        self.chat.save(update_fields=['created_by'])
        ChatBan.objects.create(chat=self.chat, user=self.b, banned_by=self.c)
        restore_backup(backup.pk, self.c)
        self.chat.refresh_from_db()
        self.assertEqual(self.c.pk, self.chat.created_by_id)
        self.assertTrue(ChatBan.objects.filter(chat=self.chat, user=self.b).exists())
        self.assertTrue(ChatMember.objects.get(chat=self.chat, user=self.b).is_banned)
        self.assertTrue(Message.objects.filter(pk=newest.pk, is_deleted=False).exists())
        self.assertIsNone(service.event_for_user(clear_event, self.a))

    def test_restore_file_collision_is_rejected(self):
        attachment = self.attachment(self.message())
        backup = self.backup()
        attachment.file.storage.delete(attachment.file.name)
        attachment.file.storage.save(attachment.file.name, ContentFile(b'wrong bytes'))
        with self.assertRaises(ValidationError):
            restore_backup(backup.pk, self.a, dry_run=True)
        self.assertFalse(ChatBackup.objects.get(pk=backup.pk).restored_at)

    def test_restore_missing_external_user_is_rejected_before_any_changes(self):
        ChatMember.objects.create(chat=self.chat, user=self.c)
        service.send_message(self.chat, self.c, {'text': 'deleted account', 'client_message_id': 'external-user'})
        backup = self.backup()
        with zipfile.ZipFile(backup.backup_file.open('rb')) as archive:
            manifest = json.loads(archive.read('manifest.json'))
        backup.backup_file.close()
        for record in manifest['records']:
            if record['model'] == 'social.message':
                record['fields']['sender'] = 9223372036854775000
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w') as archive:
            archive.writestr('manifest.json', json.dumps(manifest))
        backup.backup_file.storage.delete(backup.backup_file.name)
        backup.backup_file.storage.save(backup.backup_file.name, ContentFile(content.getvalue()))
        before = Message.objects.count()
        with self.assertRaises(ValidationError):
            restore_backup(backup.pk, self.a, dry_run=True)
        self.assertEqual(before, Message.objects.count())
        self.assertFalse(ChatBackup.objects.get(pk=backup.pk).restored_at)

    def test_corrupt_archive_and_nonowner_restore_are_rejected(self):
        self.message()
        backup = self.backup()
        ChatMember.objects.filter(chat=self.chat, user=self.b).update(is_admin=True)
        with self.assertRaises(PermissionDenied):
            restore_backup(backup.pk, self.b)
        backup.backup_file.storage.delete(backup.backup_file.name)
        backup.backup_file.storage.save(backup.backup_file.name, ContentFile(b'broken archive'))
        with self.assertRaises(ValidationError):
            restore_backup(backup.pk, self.a)
        self.assertFalse(ChatBackup.objects.get(pk=backup.pk).restored_at)

    def test_pending_backups_are_requeued_after_broker_or_worker_failure(self):
        from apps.social.application.tasks import requeue_pending_chat_backups
        pending = ChatBackup.objects.create(chat=self.chat, created_by=self.a)
        claimed = ChatBackup.objects.create(chat=self.chat, created_by=self.a, processing_started_at=timezone.now())
        abandoned = ChatBackup.objects.create(chat=self.chat, created_by=self.a, processing_started_at=timezone.now() - timedelta(minutes=8))
        with patch('apps.social.application.tasks.backup_chat_task.delay') as queued:
            self.assertEqual({'queued': 2}, requeue_pending_chat_backups())
        self.assertEqual({pending.pk, abandoned.pk}, {c.args[0] for c in queued.call_args_list})
        self.assertEqual('creating', build_backup(claimed.pk).status)

    def test_personal_settings_export_import_round_trip_is_idempotent_and_owned(self):
        from apps.social.infrastructure.models.social import PrivateChat, ChatFolder, ChatFolderChat
        from apps.social.infrastructure.models.social_chat import PrivateChatSettings, GroupMemberSettings, ChatTheme, ChatWallpaper, UserGlobalChatStyle
        private = PrivateChat.objects.create(user1=self.a, user2=self.b)
        folder = ChatFolder.objects.create(user=self.a, name='Work', include_groups=True, include_muted=False, rules={'name': 'ext'})
        ChatFolderChat.objects.create(folder=folder, chat_id=self.chat.public_id, chat_type='group', conversation=service.get_conversation(self.chat))
        settings = PrivateChatSettings.objects.create(user=self.a, chat=private, custom_name='Mine', is_archived=True, folder_id=folder.pk, mentions_only=True)
        other = PrivateChatSettings.objects.create(user=self.b, chat=private, custom_name='Theirs')
        GroupMemberSettings.objects.create(membership=ChatMember.objects.get(chat=self.chat, user=self.a), sound_enabled=False)
        ChatTheme.objects.create(user=self.a, chat=self.chat, accent_color='#123456', font_size_px=18)
        ChatWallpaper.objects.create(user=self.a, private_chat=private, wallpaper_type='gradient', wallpaper_color='#112233', gradient_angle=45)
        UserGlobalChatStyle.objects.create(user=self.a, accent_color='#654321')
        data = self.client.get('/api/social/settings/export/').data
        self.assertEqual('3.0', data['version'])
        self.assertEqual({'type': 'private', 'id': private.public_id}, data['private_chats'][0]['chat'])
        self.assertEqual(1, len(data['private_chats']))
        settings.custom_name = 'Changed'
        settings.save()
        ChatTheme.objects.filter(user=self.a).delete()
        ChatFolder.objects.filter(pk=folder.pk).delete()
        for _ in range(2):
            response = self.client.post('/api/social/settings/import/', data, format='json')
            self.assertEqual(200, response.status_code, response.data)
            self.assertEqual(1, response.data['imported']['private_chats'])
        settings.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual('Mine', settings.custom_name)
        self.assertEqual('Theirs', other.custom_name)
        self.assertTrue(settings.mentions_only)
        private.refresh_from_db()
        self.assertTrue(private.user1_archived)
        self.assertEqual(1, ChatFolder.objects.filter(user=self.a, name='Work').count())
        self.assertEqual(1, ChatFolderChat.objects.filter(folder__user=self.a).count())
        self.assertEqual('#123456', ChatTheme.objects.get(user=self.a, chat=self.chat).accent_color)

    def test_import_validates_entire_file_before_changes_and_rejects_foreign_chats(self):
        data = {'version': '3.0', 'global_style': [{'chat': None, 'settings': {'accent_color': '#123456'}}],
            'group_chats': [{'chat': {'type': 'group', 'id': self.chat.public_id}, 'settings': {'notifications_enabled': False}}]}
        self.client.force_authenticate(self.c)
        response = self.client.post('/api/social/settings/import/', data, format='json')
        self.assertEqual(403, response.status_code)
        from apps.social.infrastructure.models.social_chat import UserGlobalChatStyle
        self.assertFalse(UserGlobalChatStyle.objects.filter(user=self.c).exists())
        self.client.force_authenticate(self.a)
        data['group_chats'][0]['settings']['membership'] = 999
        self.assertEqual(400, self.client.post('/api/social/settings/import/', data, format='json').status_code)
        self.assertFalse(UserGlobalChatStyle.objects.filter(user=self.a).exists())

    def test_settings_image_is_portable_and_invalid_image_does_not_write(self):
        from PIL import Image
        from apps.social.infrastructure.models.social_chat import ChatWallpaper
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        wallpaper = ChatWallpaper.objects.create(user=self.a, chat=self.chat, wallpaper_type='image', wallpaper_image=ContentFile(image.getvalue(), name='wallpaper.png'))
        data = self.client.get('/api/social/settings/export/').data
        ChatWallpaper.objects.filter(pk=wallpaper.pk).delete()
        response = self.client.post('/api/social/settings/import/', data, format='json')
        self.assertEqual(200, response.status_code, response.data)
        current = ChatWallpaper.objects.get(user=self.a, chat=self.chat)
        self.assertTrue(current.wallpaper_image.storage.exists(current.wallpaper_image.name))
        data['wallpapers'][0]['images']['wallpaper_image']['content'] = 'broken'
        self.assertEqual(400, self.client.post('/api/social/settings/import/', data, format='json').status_code)
        self.assertEqual(current.wallpaper_image.name, ChatWallpaper.objects.get(user=self.a, chat=self.chat).wallpaper_image.name)

    def test_discussions_have_site_administrators_and_no_accidental_owner(self):
        self.chat.discussion_type = 'franchise'
        self.chat.save(update_fields=['discussion_type'])
        with self.assertRaises(PermissionDenied):
            service.delete_group(self.chat, self.a)
        with self.assertRaises(PermissionDenied):
            service.require_permission(self.chat, self.a, 'can_delete_chat')
        self.b.is_staff = True
        self.b.save(update_fields=['is_staff'])
        service.require_permission(self.chat, self.b, 'can_manage_chat')
        response = self.client.post(self.base + '/transfer-ownership/', {'user_id': self.b.pk}, format='json')
        self.assertEqual(400, response.status_code)
        self.b.is_staff = False
        self.b.save(update_fields=['is_staff'])
        with self.assertRaises(PermissionDenied):
            service.require_permission(self.chat, self.b, 'can_manage_chat')
        service.leave_group(self.chat, self.a)
        self.assertFalse(ChatMember.objects.filter(chat=self.chat, user=self.a).exists())

    def test_legacy_discussion_endpoints_are_idempotent_and_enforce_bans_and_capacity(self):
        from apps.anime.infrastructure.models.anime import Franchise, Anime
        franchise = Franchise.objects.create(name='Endpoint franchise')
        anime = Anime.objects.create(title_ru='Endpoint anime', franchise=franchise)
        path = f'/api/social/anime/{anime.pk}/discussion-group/'
        response = self.client.get(path)
        self.assertEqual(200, response.status_code, response.data)
        public_id = response.data['id']
        self.assertFalse(response.data['user_joined'])
        for _ in range(2):
            response = self.client.post(path + 'create/')
            self.assertIn(response.status_code, (200, 201))
            self.assertEqual(public_id, response.data['id'])
        chat = GroupChat.objects.get(public_id=public_id)
        self.assertIsNone(chat.created_by_id)
        self.assertEqual(2, ChatTopic.objects.filter(chat=chat).count())
        self.assertEqual(1, ChatMember.objects.filter(chat=chat, user=self.a).count())
        chat.max_members = 1
        chat.save(update_fields=['max_members'])
        self.client.force_authenticate(self.b)
        self.assertEqual(400, self.client.post(path + 'join/').status_code)
        ChatBan.objects.create(chat=chat, user=self.b, banned_by=self.a)
        self.assertEqual(403, self.client.get(path).status_code)
        self.assertEqual(403, self.client.post(path + 'join/').status_code)

    def test_topic_history_search_and_anchor_respect_visibility(self):
        from apps.anime.infrastructure.models.anime import Anime
        from apps.social.infrastructure.models.social import Message
        self.chat.discussion_type = 'franchise'
        self.chat.save(update_fields=['discussion_type'])
        general = ChatTopic.objects.create(chat=self.chat, title='General')
        part = ChatTopic.objects.create(chat=self.chat, title='Part', anime=Anime.objects.create(title_ru='Part'))
        legacy = self.message(text='needle legacy')
        selected = self.message(text='needle part', key='part', topic_id=part.pk)
        general_message = self.message(text='needle general', key='general', topic_id=general.pk, reply_to=selected)
        conv = service.get_conversation(self.chat)
        Message.objects.bulk_create([Message(chat=self.chat, conversation=conv, sender=self.b, topic=part,
            text=f'Later {seq}', seq=seq) for seq in range(20, 120)])
        url = f'/api/social/chats/{self.chat.public_id}/messages/'
        result = self.client.get(url, {'type': 'group', 'topic_id': general.pk})
        self.assertEqual([legacy.pk, general_message.pk], [m['id'] for m in result.data['results']])
        self.assertEqual(part.pk, result.data['results'][1]['reply_to_message']['topic_id'])
        self.assertEqual(part.slug, result.data['results'][1]['reply_to_message']['topic_slug'])
        result = self.client.get(url, {'type': 'group', 'topic_id': part.pk, 'around': selected.pk})
        self.assertEqual(200, result.status_code, result.data)
        self.assertIn(selected.pk, [m['id'] for m in result.data['results']])
        self.assertLessEqual(len(result.data['results']), 50)
        self.assertEqual(400, self.client.get(url, {'type': 'group', 'topic_id': part.pk, 'around': legacy.pk}).status_code)
        result = self.client.get('/api/social/messages/search/', {'chat_id': self.chat.public_id, 'type': 'group', 'topic_id': part.pk, 'q': 'needle'})
        self.assertEqual([selected.pk], [m['id'] for m in result.data])
        self.assertEqual(400, self.client.get('/api/social/messages/search/', {'chat_id': self.chat.public_id, 'type': 'group', 'q': 'needle', 'date_from': 'wrong'}).status_code)
        service.clear_history(self.chat, self.a)
        self.assertEqual(400, self.client.get(url, {'type': 'group', 'around': selected.pk}).status_code)

    def test_owner_can_post_even_when_assigned_a_restrictive_role(self):
        from apps.social.infrastructure.models.social import ChatRole
        role = ChatRole.objects.create(chat=self.chat, name='Read only', can_post_messages=False)
        ChatMember.objects.filter(chat=self.chat, user=self.a).update(role=role, can_send_messages=False)
        self.assertEqual('saved', self.message().text)

    def test_shared_card_stops_disclosing_content_after_privacy_changes(self):
        from apps.social.infrastructure.models.social import Post
        post = Post.objects.create(author=self.a, text='private after sharing')
        message = self.message(shared_post=post)
        self.assertIsNotNone(service.serialize_message(message, self.b)['shared_post_data'])
        post.visibility = 'private'
        post.save(update_fields=['visibility'])
        message.refresh_from_db()
        self.assertIsNone(service.serialize_message(message, self.b)['shared_post_data'])
        self.client.force_authenticate(self.b)
        response = self.client.post(f'/api/social/messages/{message.pk}/forward/',
            {'chat_id': self.chat.public_id, 'chat_type': 'group'}, format='json')
        self.assertEqual(403, response.status_code, response.data)

    def test_list_query_count_is_bounded_as_chats_grow(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from apps.social.infrastructure.models.social import PrivateChat
        private = PrivateChat.objects.create(user1=self.a, user2=self.b)
        service.send_message(private, self.b, {'text': 'private preview', 'client_message_id': 'list-private'})
        self.message()
        counts = {}
        for kind in ('private', 'group'):
            with CaptureQueriesContext(connection) as queries:
                result = self.client.get(f'/api/social/{kind}-chats/')
            self.assertEqual(200, result.status_code, result.data)
            counts[kind] = len(queries)
        for index in range(7):
            peer = User.objects.create_user(username=f'list_peer_{index}', email=f'list_{index}@test.local')
            PrivateChat.objects.create(user1=self.a, user2=peer)
            group = GroupChat.objects.create(name=f'List group {index}', created_by=self.a)
            ChatMember.objects.create(chat=group, user=self.a, is_admin=True)
        for kind in ('private', 'group'):
            with CaptureQueriesContext(connection) as queries, patch('core.online_status.online_status.get_users_data', return_value={}) as batch:
                result = self.client.get(f'/api/social/{kind}-chats/')
            self.assertEqual(200, result.status_code, result.data)
            self.assertEqual(8, result.data['count'])
            self.assertLessEqual(len(queries), counts[kind] + 2, f'{kind}: {counts[kind]} -> {len(queries)} queries')
            batch.assert_called_once()
            print(f'CHAT_LIST_SQL {kind}: 1 chat={counts[kind]}, 8 chats={len(queries)}')

    def test_batch_list_preview_and_unread_follow_clear_and_join_visibility(self):
        from apps.social.infrastructure.models.social import PrivateChat
        private = PrivateChat.objects.create(user1=self.a, user2=self.b)
        service.send_message(private, self.b, {'text': 'old private', 'client_message_id': 'batch-private'})
        self.message(text='old group')
        service.clear_history(private, self.a)
        self.chat.history_visible = False
        self.chat.save(update_fields=['history_visible'])
        ChatMember.objects.filter(chat=self.chat, user=self.a).update(joined_at=timezone.now())
        for kind in ('private', 'group'):
            result = self.client.get(f'/api/social/{kind}-chats/')
            self.assertEqual(200, result.status_code, result.data)
            self.assertIsNone(result.data['results'][0]['last_message'])
            self.assertEqual(0, result.data['results'][0]['unread_count'])

    def test_nested_backup_creation_uses_the_route_parent(self):
        with patch('apps.social.application.tasks.backup_chat_task.delay'), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.base + '/backups/', {}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        self.assertEqual(self.chat.pk, ChatBackup.objects.get(pk=response.data['id']).chat_id)

    def test_restore_preserves_rejoined_membership_identity_permissions_and_preferences(self):
        from apps.social.infrastructure.models.social_chat import GroupMemberSettings
        previous = ChatMember.objects.get(chat=self.chat, user=self.b)
        previous.is_admin = True
        previous.save(update_fields=['is_admin'])
        GroupMemberSettings.objects.update_or_create(membership=previous, defaults={'notifications_enabled': True})
        backup = self.backup()
        ChatMember.objects.filter(chat=self.chat, user=self.b).delete()
        current = ChatMember.objects.create(chat=self.chat, user=self.b, is_admin=False)
        preferences, _ = GroupMemberSettings.objects.update_or_create(membership=current, defaults={'notifications_enabled': False})
        self.assertTrue(restore_backup(backup.pk, self.a, dry_run=True)['dry_run'])
        restore_backup(backup.pk, self.a)
        current.refresh_from_db(); preferences.refresh_from_db()
        self.assertFalse(current.is_admin)
        self.assertFalse(preferences.notifications_enabled)
        self.assertFalse(ChatMember.objects.filter(pk=previous.pk).exists())
        self.assertEqual(1, ChatMember.objects.filter(chat=self.chat, user=self.b).count())

    def test_backup_at_file_limit_and_one_byte_above(self):
        message = self.message()
        item = Attachment.objects.create(message=message, type='file', file=ContentFile(b'x' * 4096, name='boundary.bin'),
            file_name='boundary.bin', file_size=4096, mime_type='application/octet-stream')
        with override_settings(CHAT_BACKUP_MAX_BYTES=4096):
            backup = self.backup()
            self.assertTrue(restore_backup(backup.pk, self.a, dry_run=True)['success'])
            Attachment.objects.create(message=message, type='file', file=ContentFile(b'z', name='overflow.bin'),
                file_name='overflow.bin', file_size=1, mime_type='application/octet-stream')
            overflow = ChatBackup.objects.create(chat=self.chat, created_by=self.a)
            with self.assertRaises(ValidationError):
                build_backup(overflow.pk)
        overflow.refresh_from_db()
        self.assertEqual('failed', overflow.status)
        self.assertFalse(overflow.backup_file)
        self.assertTrue(item.file.storage.exists(item.file.name))

    def test_backup_manifest_limit_fails_before_publishing_archive(self):
        message = self.message(text='Ю' * 20000)
        backup = ChatBackup.objects.create(chat=self.chat, created_by=self.a)
        with override_settings(CHAT_BACKUP_MAX_MANIFEST_BYTES=4096), self.assertRaises(ValidationError):
            build_backup(backup.pk)
        backup.refresh_from_db()
        self.assertEqual('failed', backup.status)
        self.assertFalse(backup.backup_file)
        self.assertEqual('Ю' * 20000, Message.objects.get(pk=message.pk).text)

    def test_analytics_uses_visible_messages_attachments_and_current_event_version(self):
        message = self.message()
        self.attachment(message)
        url = self.base + '/analytics/'
        result = self.client.get(url)
        self.assertEqual(200, result.status_code, result.data)
        self.assertEqual(1, result.data['activity']['total'])
        self.assertEqual(1, result.data['content']['with_media'])
        self.assertEqual(0, result.data['content']['text_only'])
        service.change_message(message.pk, self.a, delete=True)
        self.assertEqual(0, self.client.get(url).data['activity']['total'])
        self.assertEqual(400, self.client.get(url, {'days': 'bad'}).status_code)
        self.client.force_authenticate(self.b)
        self.assertEqual(403, self.client.get(url).status_code)

    def test_expired_media_link_requires_fresh_authentication_for_the_same_user(self):
        import time
        attachment = self.attachment(self.message())
        request = type('Request', (), {'user': self.a, 'build_absolute_uri': lambda _, url: url})()
        with patch('django.core.signing.time.time', return_value=time.time()-3600):
            expired = private_file_url(attachment.file, request)
        self.assertEqual(403, APIClient().get(expired).status_code)
        response = self.client.get(expired)
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'0123456789', b''.join(response.streaming_content))
        self.client.force_authenticate(self.b)
        self.assertEqual(403, self.client.get(expired).status_code)

    def test_large_restore_batches_sql_and_preserves_missing_replies_and_timestamps(self):
        first = self.message()
        Message.objects.bulk_create([Message(chat=self.chat, conversation=first.conversation, sender=self.a,
            text=f'Archived {i}', seq=i, version=1, reply_to=first) for i in range(2, 102)])
        backup = self.backup()
        expected = dict(Message.objects.filter(chat=self.chat).values_list('pk', 'created_at'))
        Message.objects.filter(chat=self.chat).delete()
        with CaptureQueriesContext(connection) as preview_queries:
            restore_backup(backup.pk, self.a, dry_run=True)
        self.assertLess(len(preview_queries), 100)
        with CaptureQueriesContext(connection) as restore_queries:
            restore_backup(backup.pk, self.a)
        self.assertLess(len(restore_queries), 120)
        self.assertEqual(expected, dict(Message.objects.filter(chat=self.chat).values_list('pk', 'created_at')))
        self.assertEqual(100, Message.objects.filter(chat=self.chat, reply_to_id=first.pk).count())
        self.assertEqual({2}, set(Message.objects.filter(chat=self.chat).values_list('version', flat=True)))
        print(f'CHAT_RESTORE_SQL 101 messages: preview={len(preview_queries)}, restore={len(restore_queries)}')

    def test_settings_import_accepts_large_json_and_rejects_oversize_before_writes(self):
        content = json.dumps({'version': '3.0', 'global_style': [{'chat': None,
            'settings': {'accent_color': '#123456'}}]}).encode() + b' ' * (3 * 1024 * 1024)
        self.assertEqual(200, self.client.post('/api/social/settings/import/', content, content_type='application/json').status_code)
        from apps.social.infrastructure.models.social_chat import UserGlobalChatStyle
        with override_settings(CHAT_SETTINGS_IMPORT_MAX_BYTES=512):
            response = self.client.post('/api/social/settings/import/', b'{"version":"3.0"}' + b' ' * 513, content_type='application/json')
        self.assertEqual(400, response.status_code)
        self.assertEqual('#123456', UserGlobalChatStyle.objects.get(user=self.a).accent_color)
