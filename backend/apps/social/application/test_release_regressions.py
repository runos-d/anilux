from hashlib import sha256

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from unittest.mock import patch
from rest_framework.test import APIClient

from apps.notifications.infrastructure.models.notifications import PushSubscription
from apps.social.application.tests import make_user
from apps.social.infrastructure.models.social import Follow, Group, GroupMembership, Post, PostAttachment, PostComment, PrivateChat


class ReleaseRegressions(TestCase):
    def setUp(self):
        self.owner = make_user('release_owner')
        self.reader = make_user('release_reader')
        self.client = APIClient()
        self.client.force_authenticate(self.reader)

    def post(self, **values):
        return Post.objects.create(author=self.owner, text='Release post', status='published', **values)

    def test_guest_reads_only_comments_of_public_posts(self):
        public = self.post()
        private = self.post(visibility='private')
        comment = PostComment.objects.create(post=public, author=self.reader, content='Public comment')
        guest = APIClient()
        response = guest.get(f'/api/social/posts/{public.pk}/comments/')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(str(comment.pk), response.data[0]['id'])
        self.assertEqual(404, guest.get(f'/api/social/posts/{private.pk}/comments/').status_code)
        self.assertEqual(401, guest.post(f'/api/social/posts/{public.pk}/comments/', {'text': 'Guest write'}).status_code)

    def test_playlist_counts_are_batched_and_do_not_expose_private_favorites(self):
        from apps.playlists.infrastructure.models.playlists import Playlist, FavoritePlaylist
        Playlist.objects.create(id='10000001', user=self.reader, title='Public', visibility='public')
        Playlist.objects.create(id='10000002', user=self.reader, title='Private', visibility='private')
        Playlist.objects.create(id='10000003', user=self.reader, title='Link', visibility='link')
        hidden = Playlist.objects.create(id='10000004', user=self.owner, title='Hidden', visibility='private')
        FavoritePlaylist.objects.create(user=self.reader, playlist=hidden)
        response = self.client.get('/api/playlists/playlists/counts/')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual({'all': 3, 'public': 1, 'private': 1, 'link': 1, 'favorites': 0}, response.data)

    def test_counter_repair_is_read_only_by_default_and_preserves_content(self):
        from io import StringIO
        from apps.social.application.post_commands import deliver_post_event
        import uuid
        post = self.post(comments_count=9)
        output = StringIO()
        call_command('repair_post_counters', stdout=output)
        post.refresh_from_db(); self.assertEqual(9, post.comments_count)
        call_command('repair_post_counters', apply=True, stdout=output)
        post.refresh_from_db(); self.assertEqual(0, post.comments_count)
        self.assertEqual('Release post', post.text)
        self.assertEqual(1, post.version)
        deliver_post_event(str(uuid.uuid4()))

    def test_missing_subscription_table_is_rejected_despite_recorded_migrations(self):
        tables = [table for table in connection.introspection.table_names() if table != 'users_subscription']
        with patch.object(connection.introspection, 'table_names', return_value=tables):
            with self.assertRaisesMessage(CommandError, 'users_subscription'):
                call_command('check_project_schema')

    def test_combined_list_uses_public_ids_and_respects_clear_and_hide(self):
        from apps.social.application import conversations as service
        chat = PrivateChat.objects.create(user1=self.owner, user2=self.reader)
        first, _ = service.send_message(chat, self.owner, {'text': 'Visible'})
        latest, _ = service.send_message(chat, self.owner, {'text': 'Deleted'})
        service.change_message(latest.pk, self.owner, delete=True)
        rows = self.client.get('/api/social/chats/').data
        row = next(row for row in rows if row['id'] == chat.public_id)
        self.assertEqual(row['last_message_text'], first.text)
        service.clear_history(chat, self.reader)
        rows = self.client.get('/api/social/chats/').data
        self.assertIsNone(next(row for row in rows if row['id'] == chat.public_id)['last_message_text'])
        service.clear_history(chat, self.reader, hide=True)
        self.assertNotIn(chat.public_id, [row['id'] for row in self.client.get('/api/social/chats/').data])

    def test_missing_history_index_is_rejected(self):
        describe = connection.introspection.get_constraints
        def missing(cursor, table):
            values = describe(cursor, table)
            return {name: value for name, value in values.items() if value['columns'] != ['private_chat_id', 'seq']} if table == 'social_message' else values
        with patch.object(connection.introspection, 'get_constraints', side_effect=missing):
            with self.assertRaisesMessage(CommandError, 'social_mess_private_541ee8_idx'):
                call_command('check_project_schema')

    def test_deleting_private_chat_hides_it_for_both_participants(self):
        from apps.social.application import conversations as service
        chat = PrivateChat.objects.create(user1=self.owner, user2=self.reader)
        service.send_message(chat, self.owner, {'text': 'Still visible to the reader'})
        service.clear_history(chat, self.owner, hide=True)
        for path in ('/api/social/chats/', '/api/social/private-chats/'):
            response = self.client.get(path)
            rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
            self.assertNotIn(chat.public_id, [row['id'] for row in rows])
        self.client.force_authenticate(self.owner)
        for path in ('/api/social/chats/', '/api/social/private-chats/'):
            response = self.client.get(path)
            rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
            self.assertNotIn(chat.public_id, [row['id'] for row in rows])

    def test_online_status_uses_presence_key_in_both_lists(self):
        chat = PrivateChat.objects.create(user1=self.owner, user2=self.reader)
        for online in ({self.owner.pk: {'user_id': self.owner.pk, 'is_active': False}}, {}):
            with patch('core.online_status.online_status.get_users_data', return_value=online):
                for path in ('/api/social/chats/', '/api/social/private-chats/'):
                    response = self.client.get(path)
                    rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
                    row = next(row for row in rows if row['id'] == chat.public_id)
                    self.assertEqual(row['other_user']['is_online'], bool(online))

    def test_private_summary_uses_request_origin_for_participant_and_sender_avatar(self):
        from apps.social.application import conversations as service
        self.owner.avatar = 'avatars/local-release-test.jpg'
        self.owner.save(update_fields=['avatar'])
        chat = PrivateChat.objects.create(user1=self.owner, user2=self.reader)
        service.send_message(chat, self.owner, {'text': 'Avatar context'})
        response = self.client.get('/api/social/private-chats/')
        rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
        row = next(row for row in rows if row['id'] == chat.public_id)
        expected = 'http://testserver' + self.owner.avatar.url
        self.assertEqual(row['other_user']['avatar_url'], expected)
        self.assertEqual(row['last_message']['sender']['avatar_url'], expected)

    def test_json_create_retry_is_scoped_to_author_and_empty_is_rejected(self):
        own = self.post(client_post_id='same-local-key')
        response = self.client.post('/api/social/posts/', {'text': 'My post', 'client_post_id': 'same-local-key'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotEqual(response.data['id'], own.pk)
        retry = self.client.post('/api/social/posts/', {'text': 'My post', 'client_post_id': 'same-local-key'}, format='json')
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.data['id'], response.data['id'])
        before = Post.objects.count()
        self.assertEqual(self.client.post('/api/social/posts/', {}, format='json').status_code, 400)
        self.assertEqual(Post.objects.count(), before)

    def test_update_and_delete_enforce_author_and_missing_returns_404(self):
        post = self.post()
        self.assertEqual(self.client.patch(f'/api/social/posts/{post.pk}/', {'text': 'hacked'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(f'/api/social/posts/{post.pk}/').status_code, 403)
        self.assertEqual(self.client.get('/api/social/posts/999999999/').status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(f'/api/social/posts/{post.pk}/', {'text': 'updated'}, format='json').status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.text, 'updated')

    def test_visibility_on_detail_profile_and_weighted_feed(self):
        private = self.post(visibility='private')
        followers = self.post(visibility='followers')
        friends = self.post(visibility='friends')
        for post in (private, followers, friends):
            self.assertEqual(self.client.get(f'/api/social/posts/{post.pk}/').status_code, 404)
        Follow.objects.create(follower=self.reader, following=self.owner)
        self.assertEqual(self.client.get(f'/api/social/posts/{followers.pk}/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/social/posts/{friends.pk}/').status_code, 404)
        for path in (f'/api/social/users/{self.owner.pk}/posts/', '/api/social/feed/weighted/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, response.data)
            rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
            self.assertNotIn(private.pk, [row['id'] for row in rows])
        Follow.objects.create(follower=self.owner, following=self.reader)
        self.assertEqual(self.client.get(f'/api/social/posts/{friends.pk}/').status_code, 200)

    def test_private_group_needs_membership(self):
        group = Group.objects.create(name='Release group', slug='release-private', creator=self.owner, is_private=True)
        post = self.post(group=group)
        self.assertEqual(self.client.get(f'/api/social/posts/{post.pk}/').status_code, 404)
        GroupMembership.objects.create(group=group, user=self.reader)
        self.assertEqual(self.client.get(f'/api/social/posts/{post.pk}/').status_code, 200)

    def test_comment_and_attachment_cannot_be_changed_by_other_user(self):
        post = self.post()
        comment = PostComment.objects.create(post=post, author=self.owner, content='Keep this')
        attachment = PostAttachment.objects.create(post=post, content_type='anime', object_id=999)
        self.assertEqual(self.client.patch(f'/api/social/posts/{post.pk}/comments/{comment.pk}/', {'content': 'hacked'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(f'/api/social/posts/{post.pk}/comments/{comment.pk}/').status_code, 403)
        self.assertEqual(self.client.delete(f'/api/social/post-attachments/{attachment.pk}/').status_code, 403)
        self.assertEqual(self.client.patch(f'/api/social/post-attachments/{attachment.pk}/', {'metadata': {'hacked': True}}, format='json').status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Keep this')

    def test_partial_anime_update_keeps_playlist_attachments(self):
        post = self.post()
        attachment = PostAttachment.objects.create(post=post, content_type='playlist', object_id=999)
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f'/api/social/posts/{post.pk}/', {'anime_ids': []}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(PostAttachment.objects.filter(pk=attachment.pk).exists())

    def test_push_endpoint_is_full_length_unique_and_hash_updates(self):
        endpoint = 'https://push.example.test/' + 'a' * 4096
        subscription = PushSubscription.objects.create(user=self.owner, endpoint=endpoint)
        subscription.refresh_from_db()
        self.assertEqual(subscription.endpoint, endpoint)
        self.assertEqual(subscription.endpoint_hash, sha256(endpoint.encode()).hexdigest())
        with self.assertRaises(IntegrityError), transaction.atomic():
            PushSubscription.objects.create(user=self.reader, endpoint=endpoint)
        subscription.endpoint += 'b'
        subscription.save(update_fields=['endpoint'])
        subscription.refresh_from_db()
        self.assertEqual(subscription.endpoint_hash, sha256(subscription.endpoint.encode()).hexdigest())
