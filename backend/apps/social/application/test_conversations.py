from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, AsyncMock

from django.db import close_old_connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import GroupChat, PrivateChat, ChatMember, Message, MessageReadStatus
from apps.social.infrastructure.models.social_chat import ChatTopic, MessagePin, MessageReaction, ScheduledMessage, ChatBan, ChatInviteLink, ChatJoinRequest
from apps.social.infrastructure.models.conversation import ChatEvent, ConversationUserState
from apps.social.application import conversations as service


class ConversationTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='chat_a', email='chat_a@test.local', password='test')
        self.b = User.objects.create_user(username='chat_b', email='chat_b@test.local', password='test')
        self.outsider = User.objects.create_user(username='chat_c', email='chat_c@test.local', password='test')
        self.private = PrivateChat.objects.create(user1=self.a, user2=self.b, public_id=80000001)
        self.group = GroupChat.objects.create(id=self.private.pk, name='Group', created_by=self.a, public_id=80000002)
        ChatMember.objects.create(chat=self.group, user=self.a, is_admin=True)
        ChatMember.objects.create(chat=self.group, user=self.b)
        self.client = APIClient()
        self.client.force_authenticate(self.a)

    def send(self, chat=None, text='Hello', key='command-1', user=None):
        return service.send_message(chat or self.private, user or self.a, {'text': text, 'client_message_id': key})[0]

    def test_identical_pks_have_distinct_conversations_and_rooms(self):
        self.assertNotEqual(service.room(self.private), service.room(self.group))
        self.assertEqual(service.resolve_chat(self.private.public_id, self.a).pk, self.private.pk)
        with self.assertRaises(ValidationError):
            service.resolve_chat(self.private.pk, self.a)

    def test_shared_history_serializer_preserves_viewer_and_reply_projection(self):
        from apps.social.presentation.views.conversation_views import history
        original = self.send()
        service.send_message(self.private, self.b, {'text': 'Reply', 'reply_to': original,
                                                   'client_message_id': 'history-reply'})
        service.mark_read(self.private, self.b, [original.pk])
        for viewer in (self.a, self.b):
            messages, _ = history(self.private, viewer)
            expected = [service.serialize_message(message, viewer) for message in messages]
            self.assertEqual(service.serialize_messages(messages, viewer), expected)

    def test_delete_event_projects_current_unread_count(self):
        first = self.send()
        self.send(key='later')
        service.change_message(first.pk, self.a, delete=True)
        event = ChatEvent.objects.get(kind='message_deleted')
        self.assertEqual(service.event_for_user(event, self.b)['unread_count'], 1)
        self.assertIsNone(service.event_for_user(event, self.outsider))

    def test_send_retry_is_idempotent_but_identical_text_is_not_deduplicated(self):
        original = self.send()
        self.assertEqual(original.pk, self.send().pk)
        second = self.send(key='command-2')
        self.assertNotEqual(original.pk, second.pk)
        self.assertEqual([1, 2], list(Message.objects.order_by('seq').values_list('seq', flat=True)))
        self.assertEqual(2, ChatEvent.objects.filter(kind='new_message').count())
        with self.assertRaises(ValidationError):
            self.send(text='changed')

    def test_blocked_sender_and_nonmember_cannot_send(self):
        self.private.user2_blocked = True
        self.private.save()
        with self.assertRaises(PermissionDenied):
            self.send()
        with self.assertRaises(PermissionDenied):
            self.send(self.group, user=self.outsider)

    def test_reply_and_topic_cannot_cross_chat(self):
        message = self.send()
        with self.assertRaises(ValidationError):
            service.send_message(self.group, self.a, {'text': 'reply', 'reply_to': message})
        topic = ChatTopic.objects.create(chat=self.group, title='Topic', slug='topic')
        with self.assertRaises(ValidationError):
            service.send_message(self.private, self.a, {'text': 'topic', 'topic_id': topic.pk})

    def test_read_only_requested_messages_and_deleted_not_unread(self):
        first, second = self.send(), self.send(key='second')
        result = service.mark_read(self.private, self.b, [first.pk])
        self.assertEqual(1, result['unread_count'])
        self.assertEqual(1, MessageReadStatus.objects.filter(user=self.b).count())
        service.change_message(second.pk, self.a, delete=True)
        self.assertEqual(0, service.unread_count(self.private, self.b))
        self.assertEqual([], service.mark_read(self.private, self.b, [first.pk])['message_ids'])

    def test_rollback_does_not_leave_message_or_event(self):
        before = ChatEvent.objects.count()
        try:
            with transaction.atomic():
                self.send()
                raise RuntimeError('rollback')
        except RuntimeError:
            pass
        self.assertEqual(0, Message.objects.count())
        self.assertEqual(before, ChatEvent.objects.count())

    def test_http_public_id_roundtrip_and_retry(self):
        url = f'/api/social/chats/{self.private.public_id}/messages/?type=private'
        data = {'text': 'HTTP', 'client_message_id': 'http-command'}
        first = self.client.post(url, data, format='json')
        self.assertEqual(201, first.status_code, first.data)
        again = self.client.post(url, data, format='json')
        self.assertEqual(200, again.status_code, again.data)
        self.assertEqual(first.data['id'], again.data['id'])
        self.assertEqual(self.private.public_id, first.data['chat_id'])
        self.assertEqual(1, len(self.client.get(url).data['results']))
        detail = self.client.get(f'/api/social/chats/{self.private.public_id}/?type=private')
        self.assertEqual(200, detail.status_code, detail.data)
        self.assertEqual('private', detail.data['type'])

    def test_catchup_contains_edit_and_delete_of_old_messages(self):
        msg = self.send()
        cursor = service.get_conversation(self.private).event_seq
        service.change_message(msg.pk, self.a, text='Edited', version=1)
        service.change_message(msg.pk, self.a, delete=True)
        response = self.client.get(f'/api/social/chats/{self.private.public_id}/events/', {'type': 'private', 'after': cursor})
        self.assertEqual(['message_deleted'], [e['action'] for e in response.data['events']])

    def test_search_does_not_disclose_private_messages(self):
        self.send(text='secret')
        allowed = self.client.get('/api/social/messages/search/', {'chat_id': self.private.public_id, 'type': 'private', 'q': 'secret'})
        self.assertEqual(200, allowed.status_code, allowed.data)
        self.assertEqual(1, len(allowed.data))
        self.client.force_authenticate(self.outsider)
        response = self.client.get('/api/social/messages/search/', {'chat_id': self.private.public_id, 'type': 'private', 'q': 'secret'})
        self.assertIn(response.status_code, (403, 404))

    def test_reactions_use_one_source_and_preserve_other_users(self):
        msg = self.send()
        service.react(msg.pk, self.a, '👍', True)
        service.react(msg.pk, self.b, '👍', True)
        service.react(msg.pk, self.a, '👍', False)
        msg.refresh_from_db()
        self.assertEqual({'👍': [self.b.pk]}, msg.reactions)
        response = self.client.get(f'/api/social/messages/{msg.pk}/reactions/')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(self.b.pk, response.data[0]['user']['id'])
        with self.assertRaises(NotFound):
            service.react(msg.pk, self.outsider, '👍')

    def test_reselecting_reaction_is_idempotent_and_another_emoji_replaces_it(self):
        msg = self.send()
        self.assertEqual('added', service.react(msg.pk, self.a, '👍')['status'])
        self.assertEqual('unchanged', service.react(msg.pk, self.a, '👍')['status'])
        result = service.react(msg.pk, self.a, '❤️')
        self.assertEqual('replaced', result['status'])
        self.assertEqual({'❤️': [self.a.pk]}, result['reactions'])

    def test_pin_access_and_delete_remove_pin(self):
        msg = self.send()
        with self.assertRaises(NotFound):
            service.pin(msg.pk, self.outsider, True)
        service.pin(msg.pk, self.a, True)
        self.assertTrue(MessagePin.objects.filter(message=msg).exists())
        service.change_message(msg.pk, self.a, delete=True)
        self.assertFalse(MessagePin.objects.filter(message=msg).exists())

    def test_deleting_private_chat_hides_it_for_both_and_new_message_restores_it(self):
        msg = self.send()
        service.clear_history(self.private, self.b, hide=True)
        self.assertEqual(0, service.visible_messages(self.private, self.b).count())
        self.assertEqual(0, service.visible_messages(self.private, self.a).count())
        states = ConversationUserState.objects.filter(conversation=service.get_conversation(self.private))
        self.assertEqual({self.a.pk, self.b.pk}, set(states.filter(hidden=True).values_list('user_id', flat=True)))
        self.send(key='after-clear')
        self.assertEqual(1, service.visible_messages(self.private, self.b).count())
        self.assertFalse(ConversationUserState.objects.get(user=self.b).hidden)
        self.assertFalse(ConversationUserState.objects.get(user=self.a).hidden)
        msg.refresh_from_db()
        self.assertFalse(msg.is_deleted)

    def test_group_delete_requires_owner_and_final_event_survives(self):
        with self.assertRaises(PermissionDenied):
            service.delete_group(self.group, self.b)
        service.delete_group(self.group, self.a)
        event = ChatEvent.objects.get(kind='chat_deleted')
        self.assertIsNone(event.conversation_id)
        self.assertEqual(self.group.public_id, event.payload['chat_id'])

    def test_group_update_and_anime_discussion_delete_reject_member(self):
        self.client.force_authenticate(self.b)
        self.group.discussion_type = 'anime'
        self.group.save()
        url = f'/api/social/group-chats/{self.group.public_id}/'
        self.assertIn(self.client.patch(url, {'name': 'Hacked'}, format='json').status_code, (400, 403))
        self.assertEqual(403, self.client.delete(url).status_code)
        self.assertEqual(403, self.client.post(url + 'delete_group_chat/').status_code)
        self.group.refresh_from_db()
        self.assertEqual('Group', self.group.name)

    def test_forward_creates_message_and_is_idempotent(self):
        msg = self.send()
        url = f'/api/social/messages/{msg.pk}/forward/'
        data = {'chat_id': self.group.public_id, 'chat_type': 'group', 'client_message_id': 'forward-command'}
        first = self.client.post(url, data, format='json')
        self.assertEqual(201, first.status_code, first.data)
        again = self.client.post(url, data, format='json')
        self.assertEqual(200, again.status_code, again.data)
        self.assertEqual(first.data['id'], again.data['id'])
        self.assertEqual(msg.pk, Message.objects.get(pk=first.data['id']).forwarded_from_id)

    def test_folder_create_add_preview_reorder_and_access(self):
        response = self.client.post('/api/social/chat-folders/', {'name': 'My chats', 'order': 0}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        pk = response.data['id']
        base = f'/api/social/chat-folders/{pk}/'
        added = self.client.post(base + 'add_chat/', {'chat_id': self.private.public_id, 'chat_type': 'private'}, format='json')
        self.assertEqual(200, added.status_code, added.data)
        preview = self.client.get(base + 'preview/')
        self.assertEqual(200, preview.status_code, preview.data)
        self.assertEqual(self.private.public_id, preview.data['chats'][0]['id'])
        reorder = self.client.patch('/api/social/chat-folders/reorder/', {'folder_ids': [pk]}, format='json')
        self.assertEqual(200, reorder.status_code, reorder.data)
        self.client.force_authenticate(self.b)
        self.assertEqual(404, self.client.get(base).status_code)

    def test_scheduled_public_id_and_worker_retry(self):
        from django.utils import timezone
        from datetime import timedelta
        from apps.social.application.tasks_chat import send_scheduled_messages
        response = self.client.post('/api/social/scheduled-messages/', {'private_chat': self.private.public_id,
            'text': 'Scheduled', 'scheduled_at': (timezone.now() + timedelta(minutes=1)).isoformat()}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        job = ScheduledMessage.objects.get(pk=response.data['id'])
        job.scheduled_at = timezone.now() - timedelta(seconds=1)
        job.save()
        self.assertEqual(1, send_scheduled_messages())
        self.assertEqual(0, send_scheduled_messages())
        self.assertEqual(1, Message.objects.filter(text='Scheduled').count())

    def test_pagination_and_edit_conflict(self):
        for i in range(55):
            self.send(key=f'page-{i}')
        url = f'/api/social/chats/{self.private.public_id}/messages/'
        page = self.client.get(url, {'type': 'private'}).data
        self.assertEqual(50, len(page['results']))
        older = self.client.get(url, {'type': 'private', 'before': page['next_cursor']}).data
        self.assertEqual(5, len(older['results']))
        self.assertFalse(set(m['id'] for m in page['results']) & set(m['id'] for m in older['results']))
        msg = Message.objects.first()
        service.change_message(msg.pk, self.a, text='Changed', version=1)
        result = self.client.post(f'/api/social/messages/{msg.pk}/edit/', {'text': 'Stale', 'version': 1}, format='json')
        self.assertEqual(409, result.status_code, result.data)

    def test_ban_revokes_replay_and_unread(self):
        self.send(chat=self.group)
        ChatBan.objects.create(chat=self.group, user=self.b, banned_by=self.a)
        self.client.force_authenticate(self.b)
        result = self.client.get(f'/api/social/chats/{self.group.public_id}/events/', {'type': 'group'})
        self.assertEqual(403, result.status_code)
        from apps.social.application.unread_count_service import unread_service
        self.assertEqual(0, unread_service.get_total(self.b.pk))

    def test_invite_limits_target_and_repeated_join(self):
        self.group.is_public = True
        self.group.save()
        invite = ChatInviteLink.objects.create(chat=self.group, creator=self.a, usage_limit=1, target_user=self.outsider)
        with self.assertRaises(PermissionDenied):
            service.join_invite(invite.invite_link, self.b)
        self.assertEqual('joined', service.join_invite(invite.invite_link, self.outsider)['status'])
        self.assertEqual('joined', service.join_invite(invite.invite_link, self.outsider)['status'])
        invite.refresh_from_db()
        self.assertEqual(1, invite.usage_count)

    def test_private_group_invite_joins_immediately_and_consumes_usage_once(self):
        invite = ChatInviteLink.objects.create(chat=self.group, creator=self.a, usage_limit=1)
        self.assertEqual('joined', service.join_invite(invite.invite_link, self.outsider)['status'])
        self.assertEqual('joined', service.join_invite(invite.invite_link, self.outsider)['status'])
        self.assertFalse(ChatJoinRequest.objects.filter(user=self.outsider, status='pending').exists())
        invite.refresh_from_db()
        self.assertEqual(1, invite.usage_count)
        self.assertEqual(1, ChatMember.objects.filter(chat=self.group, user=self.outsider).count())

    def test_outbox_failure_leaves_retryable_event(self):
        from apps.social.application.tasks_chat import deliver_chat_event
        msg = self.send()
        event = ChatEvent.objects.get(kind='new_message', payload__message__id=msg.pk)
        with patch('channels.layers.get_channel_layer') as layer:
            layer.return_value.group_send = AsyncMock(side_effect=RuntimeError('unavailable'))
            with self.assertRaises(RuntimeError):
                deliver_chat_event.run(event.pk)
        event.refresh_from_db()
        self.assertIsNone(event.delivered_at)

    def test_outbox_addressed_frames_do_not_repeat_all_recipients(self):
        from apps.social.application.tasks_chat import deliver_chat_event
        message = self.send()
        event = ChatEvent.objects.get(kind='new_message', payload__message__id=message.pk)
        with patch('channels.layers.get_channel_layer') as layer:
            from types import SimpleNamespace
            layer.return_value = SimpleNamespace(group_send=AsyncMock())
            deliver_chat_event.run(event.pk)
            frames = {call.args[0]: call.args[1] for call in layer.return_value.group_send.await_args_list}
        self.assertCountEqual(frames[f'conversation_{event.conversation_id}']['recipients'], [self.a.pk,self.b.pk])
        self.assertEqual(frames[f'user_{self.a.pk}']['recipients'], [self.a.pk])
        self.assertEqual(frames[f'user_{self.b.pk}']['recipients'], [self.b.pk])

    def test_malformed_commands_are_validation_errors(self):
        with self.assertRaises(ValidationError):
            service.send_message(self.private, self.a, {'text': ['invalid']})
        with self.assertRaises(ValidationError):
            service.send_message(self.group, self.a, {'text': 'text', 'topic_id': 'invalid'})
        msg = self.send()
        response = self.client.post(f'/api/social/messages/{msg.pk}/edit/', {'text': 'changed', 'version': 'invalid'}, format='json')
        self.assertEqual(400, response.status_code)

    def test_personal_clear_hides_previews_and_quoted_old_text(self):
        from apps.social.presentation.serializers.social_serializers import MessageSerializer
        from types import SimpleNamespace
        original = self.send(text='old private text')
        service.clear_history(self.private, self.b)
        self.client.force_authenticate(self.b)
        detail = self.client.get(f'/api/social/chats/{self.private.public_id}/?type=private')
        self.assertIsNone(detail.data['last_message'])
        reply, _ = service.send_message(self.private, self.a, {'text': 'new reply', 'reply_to': original})
        serialized = MessageSerializer(reply, context={'request': SimpleNamespace(user=self.b)}).data
        for field in ('reply_text', 'reply_sender_username', 'reply_to_message'):
            self.assertIsNone(serialized[field])
        service.change_message(original.pk, self.a, delete=True)
        self.assertIsNone(service.serialize_message(reply, self.a)['reply_text'])
        self.assertFalse(service.user_can_receive({'action': 'new_message', 'conversation_id': reply.conversation_id,
            'message': {'id': original.pk}}, self.b.pk))

    def test_attachment_requires_author_and_stores_one_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.social.infrastructure.models.social import Attachment
        message = self.send()
        url = f'/api/social/messages/{message.pk}/attachments/upload/'
        self.client.force_authenticate(self.b)
        denied = self.client.post(url, {'file': SimpleUploadedFile('test.txt', b'content', content_type='text/plain')})
        self.assertEqual(403, denied.status_code, denied.data)
        self.assertEqual(0, Attachment.objects.count())
        self.client.force_authenticate(self.a)
        result = self.client.post(url, {'file': SimpleUploadedFile('test.txt', b'content', content_type='text/plain')})
        self.assertEqual(201, result.status_code, result.data)
        attachment = Attachment.objects.get(message=message)
        self.addCleanup(attachment.file.delete, False)
        from urllib.parse import urlsplit
        self.assertTrue(urlsplit(result.data['url']).path.endswith(attachment.file.url))
        self.assertIn('ticket=', result.data['url'])
        message.refresh_from_db()
        self.assertEqual(2, message.version)
        self.assertEqual('message_edited', ChatEvent.objects.order_by('-pk').first().kind)
        invalid = self.client.post(url, {'file': SimpleUploadedFile('bad.png', b'not an image', content_type='image/png')})
        self.assertEqual(400, invalid.status_code, invalid.data)
        self.assertEqual(1, Attachment.objects.count())

    def test_invite_management_denies_member_and_chat_reassignment(self):
        invite = ChatInviteLink.objects.create(chat=self.group, creator=self.a)
        url = f'/api/social/chat-invite-links/{invite.pk}/'
        self.client.force_authenticate(self.b)
        self.assertEqual([], self.client.get('/api/social/chat-invite-links/').data['results'])
        self.assertIn(self.client.post(url + 'revoke/').status_code, (403, 404))
        self.assertIn(self.client.delete(url).status_code, (403, 404))
        self.client.force_authenticate(self.a)
        other = GroupChat.objects.create(name='Other', created_by=self.a)
        ChatMember.objects.create(chat=other, user=self.a)
        moved = self.client.patch(url, {'chat': other.public_id}, format='json')
        self.assertEqual(400, moved.status_code, moved.data)
        invite.refresh_from_db()
        self.assertFalse(invite.is_revoked)
        self.assertEqual(self.group.pk, invite.chat_id)
        self.assertEqual(200, self.client.post(url + 'revoke/').status_code)

    def test_slow_mode_respects_settings_and_retry_without_blocking_receipts(self):
        from apps.social.infrastructure.models.social_chat import ChatSlowMode
        config = ChatSlowMode.objects.create(chat=self.group, enabled=True, delay=60, custom_delays={str(self.b.pk): 120})
        first = self.send(chat=self.group, user=self.b)
        self.assertEqual(first.pk, self.send(chat=self.group, user=self.b).pk)
        with self.assertRaises(ValidationError):
            self.send(chat=self.group, user=self.b, key='too-early')
        service.mark_read(self.group, self.a, [first.pk])
        config.enabled = False
        config.save()
        self.send(chat=self.group, user=self.b, key='disabled')

    def test_moderation_mutations_require_permission_and_preserve_chat(self):
        ban = ChatBan.objects.create(chat=self.group, user=self.outsider, banned_by=self.a)
        self.client.force_authenticate(self.b)
        base = f'/api/social/chat-bans/{ban.pk}/'
        self.assertEqual(404, self.client.patch(base, {'reason': 'Hacked'}, format='json').status_code)
        self.assertEqual(404, self.client.delete(base).status_code)
        ban.refresh_from_db()
        self.assertEqual('', ban.reason)
        self.client.force_authenticate(self.a)
        other = GroupChat.objects.create(name='Other ban', created_by=self.a)
        ChatMember.objects.create(chat=other, user=self.a)
        self.assertEqual(400, self.client.patch(base, {'chat': other.public_id}, format='json').status_code)
        self.assertEqual(204, self.client.delete(base).status_code)

    def test_legacy_ban_unban_uses_real_schema(self):
        base = f'/api/social/group-chats/{self.group.public_id}/'
        bad = self.client.post(base + 'ban_user/', {'user_id': self.b.pk, 'until_date': 'invalid'}, format='json')
        self.assertEqual(400, bad.status_code, bad.data)
        banned = self.client.post(base + 'ban_user/', {'user_id': self.b.pk, 'reason': 'Test'}, format='json')
        self.assertEqual(200, banned.status_code, banned.data)
        with self.assertRaises(PermissionDenied):
            self.send(chat=self.group, user=self.b)
        unbanned = self.client.post(base + 'unban_user/', {'user_id': self.b.pk}, format='json')
        self.assertEqual(200, unbanned.status_code, unbanned.data)
        self.send(chat=self.group, user=self.b)

    def test_retention_preserves_pins_and_emits_versioned_deletion(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.social.application.tasks_chat import cleanup_old_messages
        first = self.send()
        protected = self.send(key='protected')
        service.pin(protected.pk, self.a, True)
        Message.objects.filter(pk__in=[first.pk, protected.pk]).update(created_at=timezone.now() - timedelta(days=400))
        self.assertEqual(1, cleanup_old_messages.run(365))
        self.assertEqual(0, cleanup_old_messages.run(365))
        first.refresh_from_db()
        protected.refresh_from_db()
        self.assertTrue(first.is_deleted)
        self.assertEqual(2, first.version)
        self.assertFalse(protected.is_deleted)
        self.assertTrue(MessagePin.objects.filter(message=protected).exists())
        event = ChatEvent.objects.get(kind='message_deleted', payload__message_id=first.pk)
        self.assertEqual(2, event.payload['version'])

    def test_legacy_delete_removes_private_chat_for_both_users(self):
        original = self.send()
        result = self.client.delete(f'/api/social/private-chats/{self.private.public_id}/delete/')
        self.assertEqual(200, result.status_code, result.data)
        self.assertEqual('deleted_for_both', result.data['action'])
        self.assertTrue(PrivateChat.objects.filter(pk=self.private.pk).exists())
        self.assertTrue(Message.objects.filter(pk=original.pk, is_deleted=False).exists())
        self.assertEqual(0, service.visible_messages(self.private, self.b).count())
        self.assertEqual(0, service.visible_messages(self.private, self.a).count())

    def test_private_settings_aliases_preserve_and_update_legacy_preferences(self):
        self.private.user1_archived = True
        self.private.save()
        url = f'/api/social/private-chats/{self.private.public_id}/settings/'
        initial = self.client.get(url)
        self.assertEqual(200, initial.status_code, initial.data)
        self.assertTrue(initial.data['is_archived'])
        self.assertEqual(self.private.public_id, initial.data['chat_id'])
        updated = self.client.put(url, {'archived': False, 'pinned': True, 'blocked': False, 'notifications': False}, format='json')
        self.assertEqual(200, updated.status_code, updated.data)
        self.private.refresh_from_db()
        self.assertFalse(self.private.user1_archived)
        self.assertTrue(self.private.user1_pinned)
        self.assertFalse(self.private.user1_notifications)
        self.assertTrue(updated.data['is_muted'])
        blocked = self.client.patch(url, {'is_blocked': 'invalid'}, format='json')
        self.assertEqual(400, blocked.status_code, blocked.data)

    def test_group_list_excludes_banned_chats_without_failing_other_rows(self):
        self.send(chat=self.group)
        ChatBan.objects.create(chat=self.group, user=self.b, banned_by=self.a)
        self.client.force_authenticate(self.b)
        response = self.client.get('/api/social/group-chats/')
        self.assertEqual(200, response.status_code, response.data)
        self.assertNotIn(self.group.public_id, [row['id'] for row in response.data['results']])

    def test_live_outbox_uses_current_versions_and_quote_visibility(self):
        old = self.send(text='quoted private text')
        reply, _ = service.send_message(self.private, self.a, {'text': 'reply', 'reply_to': old})
        event = ChatEvent.objects.get(kind='new_message', payload__message__id=reply.pk)
        service.change_message(old.pk, self.a, delete=True)
        service.change_message(reply.pk, self.a, text='current reply')
        payload = service.live_event_for_user(service.event_envelope(event), self.b.pk)
        self.assertEqual('current reply', payload['message']['text'])
        self.assertIsNone(payload['message']['reply_text'])
        service.clear_history(self.private, self.b)
        self.assertIsNone(service.live_event_for_user(service.event_envelope(event), self.b.pk))

    def test_hidden_setting_and_other_member_ban_do_not_break_list(self):
        url = f'/api/social/private-chats/{self.private.public_id}/settings/'
        response = self.client.patch(url, {'is_hidden': True}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual([], self.client.get('/api/social/private-chats/').data['results'])
        self.send(user=self.b)
        self.assertEqual(1, len(self.client.get('/api/social/private-chats/').data['results']))
        member = ChatMember.objects.get(chat=self.group, user=self.b)
        member.is_banned = True
        member.save()
        listed = self.client.get('/api/social/group-chats/')
        self.assertEqual(200, listed.status_code, listed.data)
        self.assertIn(self.group.public_id, [row['id'] for row in listed.data['results']])

    def test_individual_slow_mode_and_replayed_unread_count_are_current(self):
        from apps.social.infrastructure.models.social_chat import ChatRestriction, ChatSlowMode
        ChatSlowMode.objects.create(chat=self.group, enabled=False)
        ChatRestriction.objects.create(chat=self.group, user=self.b, restricted_by=self.a, restriction_type='slow_mode', slow_mode_delay=60)
        self.send(self.group, user=self.b, key='individual-delay')
        with self.assertRaises(ValidationError):
            self.send(self.group, user=self.b, key='individual-delay-second')
        self.send(key='unread-first')
        event = service.record_event(self.private, 'unread_updated', {'user_id': self.b.pk, 'unread_count': 1}, recipients=[self.b.pk])
        self.send(key='unread-second')
        self.assertEqual(2, service.event_for_user(event, self.b)['unread_count'])


class ConcurrentSendTests(TransactionTestCase):
    @patch('apps.social.application.conversations.enqueue_event')
    def test_parallel_commands_and_retries(self, enqueue):
        a = User.objects.create_user(username='parallel_a', email='parallel_a@test.local')
        b = User.objects.create_user(username='parallel_b', email='parallel_b@test.local')
        chat = PrivateChat.objects.create(user1=a, user2=b)
        service.get_conversation(chat)

        def send(key):
            close_old_connections()
            try:
                obj, _ = service.send_message(PrivateChat.objects.get(pk=chat.pk), User.objects.get(pk=a.pk),
                    {'text': 'parallel', 'client_message_id': key})
                return obj.pk
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(send, ['repeat'] * 8 + [f'unique-{i}' for i in range(12)]))
        self.assertEqual(1, len(set(ids[:8])))
        self.assertEqual(13, Message.objects.count())
        self.assertEqual(list(range(1, 14)), list(Message.objects.order_by('seq').values_list('seq', flat=True)))


class WebSocketConversationTests(TransactionTestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='ws_a', email='ws_a@test.local')
        self.b = User.objects.create_user(username='ws_b', email='ws_b@test.local')
        self.outsider = User.objects.create_user(username='ws_c', email='ws_c@test.local')
        self.chat = PrivateChat.objects.create(user1=self.a, user2=self.b)
        self.enqueue_patch = patch('apps.social.application.conversations.enqueue_event')
        self.enqueue_patch.start()
        self.addCleanup(self.enqueue_patch.stop)

    def test_reply_history_and_live_ack_survive_websocket_reconnect(self):
        import json
        from asgiref.sync import async_to_sync
        from channels.routing import URLRouter
        from channels.testing import WebsocketCommunicator
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.social.application.routing import websocket_urlpatterns

        original, _ = service.send_message(self.chat, self.a, {'text': 'Original'})
        reply, _ = service.send_message(self.chat, self.b, {'text': 'Reply', 'reply_to': original})
        dto = json.loads(json.dumps(service.serialize_message(reply, self.a)))
        client = APIClient()
        client.force_authenticate(self.a)
        response = client.get(f'/api/social/chats/{self.chat.public_id}/messages/?type=private')
        expected_date = response.data['results'][1]['reply_to_message']['created_at']
        self.assertEqual(expected_date, dto['reply_to_message']['created_at'])
        token = str(AccessToken.for_user(self.a))

        async def scenario():
            for attempt in range(2):
                socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns),
                    f'/ws/chat/{self.chat.public_id}/?type=private&token={token}')
                try:
                    self.assertTrue((await socket.connect())[0])
                    snapshot = await socket.receive_json_from()
                    self.assertEqual('init', snapshot['action'])
                    self.assertEqual(2 + attempt, len(snapshot['messages']))
                    self.assertEqual(expected_date, snapshot['messages'][1]['reply_to_message']['created_at'])
                    if attempt == 0:
                        await socket.send_json_to({'action': 'send_message', 'text': 'Live reply',
                            'reply_to_id': original.pk, 'client_message_id': 'live-reply'})
                        ack = await socket.receive_json_from()
                        self.assertEqual('message_ack', ack['action'])
                        self.assertEqual(expected_date, ack['message']['reply_to_message']['created_at'])
                finally:
                    await socket.disconnect()

        async_to_sync(scenario)()

    def test_ws_send_retry_and_receipt_share_http_services(self):
        from asgiref.sync import async_to_sync
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        token = str(AccessToken.for_user(self.a))
        async def scenario():
            socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.chat.public_id}/?type=private&token={token}')
            connected, _ = await socket.connect()
            self.assertTrue(connected)
            initial = await socket.receive_json_from()
            self.assertEqual('init', initial['action'])
            command = {'action': 'send_message', 'text': 'Websocket', 'client_message_id': 'ws-command'}
            await socket.send_json_to(command)
            first = await socket.receive_json_from()
            await socket.send_json_to(command)
            second = await socket.receive_json_from()
            self.assertEqual(first['message']['id'], second['message']['id'])
            await socket.disconnect()
        async_to_sync(scenario)()
        self.assertEqual(1, Message.objects.count())
        self.assertEqual(1, ChatEvent.objects.filter(kind='new_message').count())

    def test_malformed_json_closes_with_a_protocol_error(self):
        from asgiref.sync import async_to_sync
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        async def scenario():
            token = str(AccessToken.for_user(self.a))
            socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns),
                f'/ws/chat/{self.chat.public_id}/?type=private&token={token}')
            self.assertTrue((await socket.connect())[0])
            await socket.receive_json_from()
            await socket.send_to(text_data='{')
            response = await socket.receive_output()
            self.assertEqual(response, {'type': 'websocket.close', 'code': 1007})
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_ws_denies_outsider_and_invalid_token(self):
        from asgiref.sync import async_to_sync
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        async def scenario():
            for token, expected in [(str(AccessToken.for_user(self.outsider)), 4004), ('invalid', 4001)]:
                socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.chat.public_id}/?type=private&token={token}')
                connected, code = await socket.connect()
                self.assertFalse(connected)
                self.assertEqual(expected, code)
                await socket.disconnect()
        async_to_sync(scenario)()

    def test_expired_connection_cannot_receive_or_keep_alive(self):
        from asgiref.sync import async_to_sync
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        from django.utils import timezone
        token = AccessToken.for_user(self.a)
        expiry = token['exp']
        async def scenario():
            socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.chat.public_id}/?type=private&token={token}')
            self.assertTrue((await socket.connect())[0])
            await socket.receive_json_from()
            with patch('apps.social.application.conversation_consumer.timezone.now', return_value=timezone.datetime.fromtimestamp(expiry + 1, tz=timezone.get_current_timezone())):
                await socket.send_json_to({'action': 'ping'})
                frame = await socket.receive_output()
                self.assertEqual('websocket.close', frame['type'])
                self.assertEqual(4001, frame['code'])
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_typing_reaches_other_member_and_disabled_account_cannot_ping(self):
        from asgiref.sync import async_to_sync
        from channels.db import database_sync_to_async
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        async def scenario():
            sockets = [WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.chat.public_id}/?type=private&token={AccessToken.for_user(user)}') for user in (self.a, self.b)]
            try:
                for socket in sockets:
                    self.assertTrue((await socket.connect())[0])
                    await socket.receive_json_from()
                await sockets[0].send_json_to({'action': 'typing_start'})
                frame = await sockets[1].receive_json_from()
                self.assertEqual(('user_typing', self.a.pk, True), (frame['action'], frame['user_id'], frame['is_typing']))
                await sockets[0].receive_json_from()
                await database_sync_to_async(User.objects.filter(pk=self.a.pk).update)(is_active=False)
                await sockets[0].send_json_to({'action': 'ping'})
                self.assertEqual(4001, (await sockets[0].receive_output())['code'])
            finally:
                for socket in sockets:
                    await socket.disconnect()
        async_to_sync(scenario)()


class MigrationUpgradeTests(TransactionTestCase):
    def test_preserves_messages_pairs_preferences_and_legacy_topics(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        a = User.objects.create_user(username='upgrade_a', email='upgrade_a@test.local')
        b = User.objects.create_user(username='upgrade_b', email='upgrade_b@test.local')
        executor = MigrationExecutor(connection)
        target = [('social', '0026_repair_legacy_public_ids')]
        latest = executor.loader.graph.leaf_nodes('social')
        old = [('social', '0018_posthashtag_public_id')]
        try:
            executor.migrate(old)
            apps = executor.loader.project_state(old).apps
            Private = apps.get_model('social', 'PrivateChat')
            Group = apps.get_model('social', 'GroupChat')
            LegacyMessage = apps.get_model('social', 'Message')
            Topic = apps.get_model('social', 'ChatTopic')
            import copy
            with connection.schema_editor() as editor:
                for model in (Private, Group, LegacyMessage):
                    nullable = model._meta.get_field('public_id')
                    nonnull = copy.copy(nullable)
                    nonnull.null = False
                    editor.alter_field(model, nonnull, nullable)
            private = Private.objects.create(user1_id=b.pk, user2_id=a.pk, public_id=90000001, code='90000001', user1_archived=True)
            group = Group.objects.create(name='Legacy discussion', discussion_type='franchise', franchise_id=999,
                is_public=True, public_id=90000002, code='90000002')
            general = Topic.objects.create(chat_id=group.pk, title='General', slug='general')
            original = LegacyMessage.objects.create(private_chat_id=private.pk, sender_id=a.pk, text='preserved', client_message_id='old-command')
            from django.core.files.base import ContentFile
            original.media.save('legacy-migration.txt', ContentFile(b'legacy-private-file'))
            legacy_file = original.media.name
            apps.get_model('social', 'Reaction').objects.create(message_id=original.pk, user_id=b.pk, emoji='👍', public_id=90000005)
            with connection.schema_editor() as editor:
                LegacyReaction = apps.get_model('social', 'Reaction')
                editor.remove_field(LegacyReaction, LegacyReaction._meta.get_field('public_id'))
            duplicate = LegacyMessage.objects.create(private_chat_id=private.pk, sender_id=a.pk, text='also preserved', client_message_id='old-command')
            null_group = Group.objects.create(name='Missing public ID', public_id=None, code='90000004')
            orphan = LegacyMessage.objects.create(chat_id=group.pk, sender_id=a.pk, text='legacy topic', topic_id=999999)
            executor = MigrationExecutor(connection)
            executor.migrate([('social', '0025_chat_privacy_and_backups')])
            import importlib
            import itertools
            repair = importlib.import_module('apps.social.migrations.0026_repair_legacy_public_ids')
            candidates = itertools.chain([80000002, 7, 7, 7, 8], range(9, 100000))
            with patch.object(repair.secrets, 'randbelow', side_effect=lambda upper: next(candidates)):
                executor = MigrationExecutor(connection)
                executor.migrate(target)
            current = executor.loader.project_state(target).apps
            NewMessage = current.get_model('social', 'Message')
            migrated = current.get_model('social', 'PrivateChat').objects.get(pk=private.pk)
            self.assertEqual(90000001, migrated.public_id)
            self.assertEqual(90000002, current.get_model('social', 'GroupChat').objects.get(pk=group.pk).public_id)
            self.assertIsNotNone(current.get_model('social', 'GroupChat').objects.get(pk=null_group.pk).public_id)
            self.assertEqual(10000007, current.get_model('social', 'GroupChat').objects.get(pk=null_group.pk).public_id)
            self.assertIsNotNone(NewMessage.objects.get(pk=original.pk).public_id)
            self.assertNotEqual(NewMessage.objects.get(pk=original.pk).public_id, NewMessage.objects.get(pk=duplicate.pk).public_id)
            with connection.cursor() as cursor:
                columns = {column.name: column for column in connection.introspection.get_table_description(cursor, 'social_message')}
            self.assertFalse(columns['public_id'].null_ok)
            self.assertEqual((a.pk, b.pk), (migrated.user1_id, migrated.user2_id))
            self.assertTrue(migrated.user2_archived)
            self.assertEqual('preserved', NewMessage.objects.get(pk=original.pk).text)
            from apps.social.infrastructure.chat_storage import chat_private_storage
            self.assertTrue(chat_private_storage.exists(legacy_file))
            with chat_private_storage.open(legacy_file) as file:
                self.assertEqual(b'legacy-private-file', file.read())
            self.assertEqual({'👍': [b.pk]}, NewMessage.objects.get(pk=original.pk).reactions)
            self.assertTrue(current.get_model('social', 'MessageReaction').objects.filter(message_id=original.pk, user_id=b.pk, emoji='👍').exists())
            self.assertIsNone(NewMessage.objects.get(pk=duplicate.pk).client_message_id)
            topic_message = NewMessage.objects.get(pk=orphan.pk)
            self.assertEqual(general.pk, topic_message.topic_id)
            self.assertEqual(999999, topic_message.legacy_topic_id)
        finally:
            MigrationExecutor(connection).migrate(latest)


@override_settings(CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}})
class GlobalWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='global_a', email='global_a@test.local')
        self.b = User.objects.create_user(username='global_b', email='global_b@test.local')
        self.chat = PrivateChat.objects.create(user1=self.a, user2=self.b)
        for target in ('core.redis_client.redis_pubsub_manager', 'apps.social.application.conversations.enqueue_event'):
            mock = patch(target)
            mock.start()
            self.addCleanup(mock.stop)

    def socket(self, token=None):
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        return WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/global/?token={token or AccessToken.for_user(self.a)}')

    @override_settings(WS_ALLOW_QUERY_TOKEN=False)
    def test_global_and_chat_accept_header_credentials_without_echoing_token(self):
        from asgiref.sync import async_to_sync
        from channels.testing import WebsocketCommunicator
        from channels.routing import URLRouter
        from apps.social.application.routing import websocket_urlpatterns
        from rest_framework_simplejwt.tokens import AccessToken
        async def scenario():
            token = str(AccessToken.for_user(self.a))
            for path in ('/ws/global/', f'/ws/chat/{self.chat.public_id}/?type=private'):
                socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns), path,
                    subprotocols=['animecore.v2', f'auth.{token}'])
                connected, protocol = await socket.connect()
                self.assertTrue(connected)
                self.assertEqual(protocol, 'animecore.v2')
                if '/chat/' in path:
                    self.assertEqual((await socket.receive_json_from())['action'], 'init')
                await socket.send_json_to({'action': 'ping'})
                self.assertEqual((await socket.receive_json_from())['action'], 'pong')
                await socket.disconnect()
            query_socket = self.socket(token)
            connected, code = await query_socket.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4001)
            await query_socket.disconnect()
        async_to_sync(scenario)()

    def test_invalid_header_credential_does_not_fall_back_to_valid_query(self):
        from asgiref.sync import async_to_sync
        async def scenario():
            socket = self.socket()
            socket.scope['subprotocols'] = ['animecore.v2', 'auth.invalid']
            self.assertEqual(await socket.connect(), (False, 4001))
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_invalid_explicit_token_cannot_fall_back_to_cookie(self):
        from asgiref.sync import async_to_sync
        async def scenario():
            socket = self.socket('invalid')
            socket.scope['user'] = self.a
            connected, code = await socket.connect()
            self.assertFalse(connected)
            self.assertEqual(4001, code)
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_expired_token_stops_notification_delivery(self):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from rest_framework_simplejwt.tokens import AccessToken
        from django.utils import timezone
        token = AccessToken.for_user(self.a)
        message, _ = service.send_message(self.chat, self.b, {'text':'expiry test'})
        event = ChatEvent.objects.get(kind='new_message',payload__message__id=message.pk)
        frames = [
            {'type':'notification_event','notification':{'secret':'must not arrive'}},
            {'type':'conversation_event','payload':service.event_envelope(event),'recipients':event.recipients},
        ]
        async def scenario():
            for pending in frames:
                socket = self.socket(str(token))
                self.assertTrue((await socket.connect())[0])
                with patch('apps.social.application.consumers.timezone.now', return_value=timezone.datetime.fromtimestamp(token['exp'] + 1, tz=timezone.get_current_timezone())):
                    await get_channel_layer().group_send(f'user_{self.a.pk}', pending)
                    frame = await socket.receive_output()
                    self.assertEqual(('websocket.close', 4001), (frame['type'], frame['code']))
                await socket.disconnect()
        async_to_sync(scenario)()

    def test_live_delivery_rechecks_revocation_after_a_successful_frame(self):
        from asgiref.sync import async_to_sync
        from channels.db import database_sync_to_async
        from channels.layers import get_channel_layer
        message, _ = service.send_message(self.chat,self.b,{'text':'live auth'})
        event = ChatEvent.objects.get(kind='new_message',payload__message__id=message.pk)
        pending = {'type':'conversation_event','payload':service.event_envelope(event),'recipients':event.recipients}
        async def scenario():
            socket = self.socket()
            self.assertTrue((await socket.connect())[0])
            try:
                await get_channel_layer().group_send(f'user_{self.a.pk}',pending)
                self.assertEqual('new_message',(await socket.receive_json_from())['action'])
                await database_sync_to_async(User.objects.filter(pk=self.a.pk).update)(token_version=1)
                await get_channel_layer().group_send(f'user_{self.a.pk}',pending)
                frame = await socket.receive_output()
                self.assertEqual(('websocket.close',4001),(frame['type'],frame['code']))
            finally:
                await socket.disconnect()
        async_to_sync(scenario)()

    def test_disabled_account_cannot_keep_alive(self):
        from asgiref.sync import async_to_sync
        from channels.db import database_sync_to_async
        async def scenario():
            socket = self.socket()
            self.assertTrue((await socket.connect())[0])
            await database_sync_to_async(User.objects.filter(pk=self.a.pk).update)(is_active=False)
            await socket.send_json_to({'action': 'ping'})
            frame = await socket.receive_output()
            self.assertEqual(4001, frame['code'])
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_legacy_events_use_current_content_and_personal_visibility(self):
        from asgiref.sync import async_to_sync
        from channels.db import database_sync_to_async
        from channels.layers import get_channel_layer
        msg = service.send_message(self.chat, self.b, {'text': 'initial', 'client_message_id': 'legacy-event'})[0]
        async def scenario():
            socket = self.socket()
            self.assertTrue((await socket.connect())[0])
            event = {'type': 'chat_message', 'message': {'id': msg.pk, 'text': 'stale'}}
            await database_sync_to_async(service.change_message)(msg.pk, self.b, text='current')
            await get_channel_layer().group_send(f'user_{self.a.pk}', event)
            frame = await socket.receive_json_from()
            self.assertEqual('current', frame['message']['text'])
            await database_sync_to_async(service.clear_history)(self.chat, self.a)
            await get_channel_layer().group_send(f'user_{self.a.pk}', event)
            self.assertTrue(await socket.receive_nothing(timeout=0.15))
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_subscription_requires_membership_and_is_discarded(self):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        group = GroupChat.objects.create(name='Subscription', created_by=self.b, is_public=True)
        ChatMember.objects.create(chat=group, user=self.a)
        ChatBan.objects.create(chat=group, user=self.a, banned_by=self.b)
        async def scenario():
            socket = self.socket()
            self.assertTrue((await socket.connect())[0])
            await socket.send_json_to({'action': 'subscribe_chat', 'chat_id': group.public_id})
            await socket.send_json_to({'action': 'ping'})
            self.assertEqual('pong', (await socket.receive_json_from())['action'])
            self.assertNotIn(f'chat_{group.pk}', get_channel_layer().groups)
            await socket.disconnect()
            self.assertNotIn(f'user_{self.a.pk}', get_channel_layer().groups)
        async_to_sync(scenario)()


class ChatManagementTests(TestCase):
    def setUp(self):
        from apps.social.infrastructure.models.social import ChatRole
        self.a = User.objects.create_user(username='manage_owner', email='manage_a@test.local')
        self.b = User.objects.create_user(username='manage_admin', email='manage_b@test.local')
        self.c = User.objects.create_user(username='manage_member', email='manage_c@test.local')
        self.d = User.objects.create_user(username='manage_peer', email='manage_d@test.local')
        self.chat = GroupChat.objects.create(name='Management', created_by=self.a, is_public=True)
        for user, admin in ((self.a, True), (self.b, True), (self.c, False), (self.d, True)):
            ChatMember.objects.create(chat=self.chat, user=user, is_admin=admin)
        self.client = APIClient()
        self.client.force_authenticate(self.a)
        self.base = f'/api/social/group-chats/{self.chat.public_id}'
        mock = patch('apps.social.application.conversations.enqueue_event')
        mock.start()
        self.addCleanup(mock.stop)

    def test_roles_use_parent_public_id_and_require_owner_for_all_mutations(self):
        from apps.social.infrastructure.models.social import ChatRole
        path = self.base + '/roles/'
        self.client.force_authenticate(self.c)
        denied = self.client.post(path, {'name': 'Escalated', 'level': 2}, format='json')
        self.assertEqual(403, denied.status_code)
        self.assertFalse(ChatRole.objects.filter(chat=self.chat, name='Escalated').exists())
        self.client.force_authenticate(self.a)
        created = self.client.post(path, {'name': 'Moderator', 'level': 1, 'can_invite_users': True}, format='json')
        self.assertEqual(201, created.status_code, created.data)
        role_id = created.data['id']
        self.assertEqual(self.chat.public_id, created.data['chat'])
        self.assertEqual(400, self.client.patch(path + f'{role_id}/', {'level': 3}, format='json').status_code)
        self.assertEqual(200, self.client.patch(path + f'{role_id}/', {'name': 'Updated'}, format='json').status_code)
        ChatMember.objects.filter(chat=self.chat, user=self.c).update(role_id=role_id)
        self.assertEqual(204, self.client.delete(path + f'{role_id}/').status_code)
        self.assertIsNone(ChatMember.objects.get(chat=self.chat, user=self.c).role_id)

    def test_admin_cannot_change_peers_promote_self_or_grant_admin(self):
        self.client.force_authenticate(self.b)
        role_path = lambda user: self.base + f'/members/{user.pk}/role/'
        for user in (self.b, self.d, self.a):
            self.assertEqual(403, self.client.post(role_path(user), {'is_admin': False}, format='json').status_code)
        response = self.client.post(role_path(self.c), {'is_admin': True}, format='json')
        self.assertEqual(403, response.status_code)
        self.assertFalse(ChatMember.objects.get(chat=self.chat, user=self.c).is_admin)
        self.assertEqual(403, self.client.post(self.base + '/ban_user/', {'user_id': self.d.pk}, format='json').status_code)

    def test_bulk_remove_validates_all_targets_before_changing_members(self):
        self.client.force_authenticate(self.b)
        response = self.client.post(self.base + '/members/bulk-remove/', {'user_ids': [self.c.pk, self.d.pk]}, format='json')
        self.assertEqual(403, response.status_code)
        self.assertTrue(ChatMember.objects.filter(chat=self.chat, user=self.c).exists())
        self.assertEqual(400, self.client.post(self.base + '/members/bulk-remove/', {'user_ids': 'all'}, format='json').status_code)

    def test_bulk_add_enforces_bans_and_capacity_without_partial_additions(self):
        x = User.objects.create_user(username='new_x', email='new_x@test.local')
        y = User.objects.create_user(username='new_y', email='new_y@test.local')
        ChatBan.objects.create(chat=self.chat, user=y, banned_by=self.a)
        path = self.base + '/members/bulk-add/'
        response = self.client.post(path, {'user_ids': [x.pk, y.pk]}, format='json')
        self.assertEqual(403, response.status_code)
        self.assertFalse(ChatMember.objects.filter(chat=self.chat, user=x).exists())
        self.chat.max_members = 4
        self.chat.save(update_fields=['max_members'])
        self.assertEqual(400, self.client.post(path, {'user_ids': [x.pk]}, format='json').status_code)

    def test_role_only_patch_preserves_existing_role_and_ownership_transfer_clears_legacy_owner_role(self):
        from apps.social.infrastructure.models.social import ChatRole
        role = ChatRole.objects.create(chat=self.chat, name='Legacy owner', level=3)
        ChatMember.objects.filter(chat=self.chat, user=self.a).update(role=role)
        custom = ChatRole.objects.create(chat=self.chat, name='Custom', level=0, can_post_messages=True)
        ChatMember.objects.filter(chat=self.chat, user=self.c).update(role=custom)
        response = self.client.post(self.base + f'/members/{self.c.pk}/role/', {'is_admin': True}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(custom.pk, ChatMember.objects.get(chat=self.chat, user=self.c).role_id)
        self.assertEqual(200, self.client.post(self.base + '/transfer-ownership/', {'user_id': self.c.pk}, format='json').status_code)
        self.chat.refresh_from_db()
        self.assertEqual(self.c.pk, self.chat.created_by_id)
        self.assertIsNone(ChatMember.objects.get(chat=self.chat, user=self.a).role_id)

    def test_request_retry_after_rejection_and_no_member_editing_other_requests(self):
        applicant = User.objects.create_user(username='join_applicant', email='join_applicant@test.local')
        self.client.force_authenticate(applicant)
        path = '/api/social/chat-join-requests/'
        first = self.client.post(path, {'chat': self.chat.public_id, 'message': 'Please'}, format='json')
        self.assertEqual(201, first.status_code, first.data)
        identifier = first.data['id']
        self.assertEqual(identifier, self.client.post(path, {'chat': self.chat.public_id}, format='json').data['id'])
        self.client.force_authenticate(self.c)
        self.assertEqual(404, self.client.patch(path + f'{identifier}/', {'message': 'tampered'}, format='json').status_code)
        self.client.force_authenticate(self.a)
        self.assertEqual(200, self.client.post(path + f'{identifier}/reject/').status_code)
        self.client.force_authenticate(applicant)
        retry = self.client.post(path, {'chat': self.chat.public_id, 'message': 'Again'}, format='json')
        self.assertEqual(201, retry.status_code, retry.data)
        self.assertEqual((identifier, 'pending', 'Again'), (retry.data['id'], retry.data['status'], retry.data['message']))
        self.client.force_authenticate(self.a)
        self.assertEqual(200, self.client.post(path + f'{identifier}/approve/').status_code)
        self.assertTrue(ChatMember.objects.filter(chat=self.chat, user=applicant).exists())

    def test_personal_tag_assignments_accept_public_ids_are_idempotent_and_owned(self):
        path = '/api/social/chat-tags/'
        tag = self.client.post(path, {'name': 'Favorite'}, format='json')
        self.assertEqual(201, tag.status_code, tag.data)
        self.assertEqual(400, self.client.post(path, {'name': 'Favorite'}, format='json').status_code)
        assignment_path = '/api/social/chat-tag-assignments/'
        values = {'tag': tag.data['id'], 'group_chat': self.chat.public_id}
        assignment = self.client.post(assignment_path, values, format='json')
        self.assertEqual(201, assignment.status_code, assignment.data)
        self.assertEqual(self.chat.public_id, assignment.data['group_chat'])
        self.assertEqual(assignment.data['id'], self.client.post(assignment_path, values, format='json').data['id'])
        self.client.force_authenticate(self.c)
        self.assertEqual(400, self.client.post(assignment_path, values, format='json').status_code)
        self.assertEqual(404, self.client.delete(assignment_path + f"{assignment.data['id']}/").status_code)
        self.client.force_authenticate(self.a)
        self.assertEqual(204, self.client.delete(assignment_path + f"{assignment.data['id']}/").status_code)


    def test_slow_mode_crud_validates_parameters_permissions_and_parent(self):
        from apps.social.infrastructure.models.social_chat import ChatSlowMode
        path = '/api/social/chat-slow-modes/'
        self.client.force_authenticate(self.c)
        self.assertEqual(403, self.client.post(path, {'chat': self.chat.public_id, 'enabled': True}, format='json').status_code)
        self.client.force_authenticate(self.a)
        created = self.client.post(path, {'chat': self.chat.public_id, 'enabled': True, 'delay': 15}, format='json')
        self.assertEqual(201, created.status_code, created.data)
        item_path = path + str(created.data['id']) + '/'
        self.assertEqual(400, self.client.patch(item_path, {'custom_delays': {str(self.c.pk): 'wrong'}}, format='json').status_code)
        other = GroupChat.objects.create(name='Other mode', created_by=self.a)
        ChatMember.objects.create(chat=other, user=self.a)
        self.assertEqual(400, self.client.patch(item_path, {'chat': other.public_id}, format='json').status_code)
        self.assertEqual(200, self.client.patch(item_path, {'enabled': False}, format='json').status_code)
        self.chat.refresh_from_db()
        self.assertEqual(0, self.chat.slow_mode_delay)
        self.assertEqual(204, self.client.delete(item_path).status_code)
        self.assertFalse(ChatSlowMode.objects.filter(chat=self.chat).exists())

    def test_permission_aliases_agree_and_invite_cannot_grant_admin_role(self):
        from apps.social.application.chat_settings_service import PermissionChecker as OldChecker
        from apps.social.application.chat_services import PermissionChecker as Checker
        from apps.social.infrastructure.models.social import ChatRole
        self.assertIs(OldChecker, Checker)
        self.assertTrue(Checker(self.b, self.chat).has_permission('can_manage_chat').allowed)
        admin_role = ChatRole.objects.create(chat=self.chat, name='Admin grant', level=2, can_manage_chat=True)
        self.client.force_authenticate(self.b)
        response = self.client.post('/api/social/chat-invite-links/', {'chat': self.chat.public_id, 'auto_assign_role': admin_role.pk}, format='json')
        self.assertEqual(403, response.status_code, response.data)
        ChatMember.objects.filter(chat=self.chat, user=self.b).update(is_banned=True)
        self.assertFalse(Checker(self.b, self.chat).has_permission('can_manage_chat').allowed)
