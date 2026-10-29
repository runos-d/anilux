from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import GroupChat, PrivateChat, ChatMember, Message, MessageAttachment, Post
from apps.social.infrastructure.models.social_chat import ChatBan
from apps.social.infrastructure.models.conversation import ChatEvent, ConversationUserState
from apps.social.application import conversations as service
from apps.social.application.live_projection import Projection, project_records, ChatRead, read_access_records


class LiveProjectionTests(TestCase):
    def setUp(self):
        self.users = [User.objects.create_user(username=f'projection-{i}', email=f'p-{i}@example.test') for i in range(16)]
        self.a, self.b, self.c = self.users[:3]
        self.group = GroupChat.objects.create(name='Projection', created_by=self.a)
        ChatMember.objects.bulk_create([ChatMember(chat=self.group, user=user,
            joined_at=timezone.now()-timedelta(days=2)) for user in self.users])
        self.private = PrivateChat.objects.create(user1=self.a, user2=self.b)

    def event(self, chat=None, **values):
        message, _ = service.send_message(chat or self.group, self.a, {'text':'Hello', **values})
        return ChatEvent.objects.select_related('conversation__group_chat', 'conversation__private_chat').get(
            kind='new_message', payload__message__id=message.pk), message

    def assert_matches(self, event, users):
        expected = {Projection(event.pk,user.pk):service.event_for_user(event,user) for user in users}
        self.assertEqual(project_records(set(expected)), expected)
        return expected

    def test_sixteen_current_plain_projections_use_seven_queries(self):
        event, _ = self.event()
        expected = self.assert_matches(event, self.users)
        with self.assertNumQueries(7):
            self.assertEqual(project_records(set(expected)), expected)

    def test_current_read_permissions_are_batched_for_public_private_and_banned_members(self):
        from rest_framework.exceptions import APIException
        outsider=User.objects.create_user(username='projection-outsider',email='outsider@example.test')
        ChatMember.objects.filter(chat=self.group,user=self.b).update(is_banned=True)
        ChatBan.objects.create(chat=self.group,user=self.c,banned_by=self.a)
        records={ChatRead(service.chat_kind(chat),chat.pk,user.pk)
                 for chat in (self.private,self.group) for user in [*self.users,outsider]}
        def expected():
            result={}
            for chat in (self.private,self.group):
                for user in [*self.users,outsider]:
                    try:service.check_access(chat,user);allowed=True
                    except APIException:allowed=False
                    result[ChatRead(service.chat_kind(chat),chat.pk,user.pk)]=allowed
            return result
        wanted=expected()
        with self.assertNumQueries(5):self.assertEqual(read_access_records(records),wanted)
        self.group.is_public=True;self.group.save(update_fields=['is_public'])
        self.assertEqual(read_access_records(records),expected())
        User.objects.filter(pk=self.a.pk).update(is_active=False)
        self.assertFalse(read_access_records(records)[ChatRead('group',self.group.pk,self.a.pk)])

    def test_read_receipts_clear_bounds_and_private_membership_remain_personal(self):
        event, message = self.event(self.private)
        event.recipients.append(self.c.pk)
        event.save(update_fields=['recipients'])
        service.mark_read(self.private, self.b, [message.pk])
        projected = self.assert_matches(event, [self.a,self.b,self.c])
        self.assertTrue(projected[Projection(event.pk,self.a.pk)]['message']['is_read_by_other'])
        self.assertEqual(projected[Projection(event.pk,self.b.pk)]['unread_count'], 0)
        self.assertIsNone(projected[Projection(event.pk,self.c.pk)])
        ConversationUserState.objects.create(conversation=event.conversation,user=self.b,cleared_through_seq=message.seq)
        self.assertIsNone(self.assert_matches(event,[self.a,self.b])[Projection(event.pk,self.b.pk)])

    def test_current_bans_and_disabled_accounts_are_not_reused_from_previous_batch(self):
        event, _ = self.event()
        self.assert_matches(event,self.users)
        ChatMember.objects.filter(chat=self.group,user=self.b).update(is_banned=True)
        ChatBan.objects.create(chat=self.group,user=self.c,banned_by=self.a,until_date=timezone.now()+timedelta(hours=1))
        projected = self.assert_matches(event,self.users)
        for user in (self.b,self.c):self.assertIsNone(projected[Projection(event.pk,user.pk)])
        User.objects.filter(pk=self.a.pk).update(is_active=False)
        self.assertIsNone(project_records({Projection(event.pk,self.a.pk)})[Projection(event.pk,self.a.pk)])

    def test_history_hidden_before_join_and_latest_message_versions_are_observed(self):
        self.group.history_visible=False
        self.group.save(update_fields=['history_visible'])
        event,message=self.event()
        Message.objects.filter(pk=message.pk).update(created_at=timezone.now()-timedelta(days=1))
        ChatMember.objects.filter(chat=self.group,user=self.b).update(joined_at=timezone.now())
        self.assertIsNone(self.assert_matches(event,[self.a,self.b])[Projection(event.pk,self.b.pk)])
        Message.objects.filter(pk=message.pk).update(text='Current',version=2,created_at=timezone.now()+timedelta(seconds=1))
        projected=self.assert_matches(event,[self.a,self.b])
        self.assertEqual(projected[Projection(event.pk,self.b.pk)]['message']['text'],'Current')
        Message.objects.filter(pk=message.pk).update(is_deleted=True)
        self.assertIsNone(self.assert_matches(event,[self.a,self.b])[Projection(event.pk,self.b.pk)])

    def test_quotes_and_private_shared_content_use_general_viewer_specific_projection(self):
        first,original=self.event(self.private)
        event,message=self.event(self.private,reply_to=original,client_message_id='reply')
        ConversationUserState.objects.create(conversation=event.conversation,user=self.b,cleared_through_seq=original.seq)
        projected=self.assert_matches(event,[self.a,self.b])
        self.assertIsNone(projected[Projection(event.pk,self.b.pk)]['message']['reply_text'])
        self.assertEqual(projected[Projection(event.pk,self.a.pk)]['message']['reply_text'],'Hello')
        post=Post.objects.create(author=self.a,text='Private post',visibility='private',status='published')
        MessageAttachment.objects.create(message=message,content_type='post',object_id=post.pk)
        self.assert_matches(event,[self.a,self.b])
