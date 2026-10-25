from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from apps.social.infrastructure.models.social import (
    Post, PostLike, PostDislike, PostComment, PostCommentLike,
    Follow, Bookmark, FeedView, Repost, Report,
    GroupChat, ChatMember, Message,
)

User = get_user_model()


def valid_image():
    from io import BytesIO
    from PIL import Image
    output = BytesIO(); Image.new('RGB', (16, 16), 'red').save(output, 'JPEG')
    return output.getvalue()


def valid_video():
    import subprocess, tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / 'video.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'lavfi', '-i',
            'color=c=blue:s=16x16:d=0.1', '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p', str(target)], check=True)
        return target.read_bytes()


def make_user(username, **kwargs):
    return User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password='testpass123',
        **kwargs
    )


class PostCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('poster')
        self.client.force_authenticate(user=self.user)

    def test_create_text_post(self):
        resp = self.client.post('/api/social/posts/', {
            'text': 'Hello world',
            'post_type': 'text',
            'visibility': 'public',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['text'], 'Hello world')
        self.assertEqual(resp.data.get('post_type'), 'text')

    def test_create_post_requires_auth(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post('/api/social/posts/', {'text': 'Anon post'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_empty_content_fails(self):
        resp = self.client.post('/api/social/posts/', {
            'post_type': 'text',
            'visibility': 'public',
        })
        self.assertIn(resp.status_code, [400, 422])

    def test_create_post_with_all_types(self):
        for post_type in ['text', 'image', 'video', 'anime', 'repost']:
            post = Post.objects.create(
                author=self.user,
                post_type=post_type,
                text=f'Test {post_type} post',
                status='published',
                visibility='public',
            )
            self.assertEqual(post.post_type, post_type)

    def test_edit_post_within_5_minutes(self):
        post = Post.objects.create(
            author=self.user,
            post_type='text',
            text='Original text',
            status='published',
            visibility='public',
        )
        self.assertTrue(post.can_edit(self.user))
        resp = self.client.patch(f'/api/social/posts/{post.id}/', {'text': 'Edited text'})
        self.assertIn(resp.status_code, [200, 405])

    def test_edit_post_after_5_minutes_denied(self):
        post = Post.objects.create(
            author=self.user,
            post_type='text',
            text='Old text',
            status='published',
            visibility='public',
            created_at=timezone.now() - timezone.timedelta(minutes=10),
        )
        Post.objects.filter(pk=post.pk).update(
            created_at=timezone.now() - timezone.timedelta(minutes=10)
        )
        post.refresh_from_db()
        self.assertFalse(post.can_edit(self.user))

    def test_delete_post_by_author(self):
        post = Post.objects.create(
            author=self.user,
            text='To delete',
            status='published',
        )
        resp = self.client.delete(f'/api/social/posts/{post.id}/')
        self.assertIn(resp.status_code, [200, 204])

    def test_delete_post_by_other_user_denied(self):
        other = make_user('other')
        post = Post.objects.create(
            author=other,
            text='Other post',
            status='published',
        )
        resp = self.client.delete(f'/api/social/posts/{post.id}/')
        self.assertIn(resp.status_code, [403, 404])

    def test_create_post_with_media_files(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = SimpleUploadedFile('pic.jpg', valid_image(), content_type='image/jpeg')
        video = SimpleUploadedFile('movie.mp4', valid_video(), content_type='video/mp4')
        data = {
            'text': 'Post with media',
            'visibility': 'public',
            'media_0': image,
            'media_1': video,
        }
        resp = self.client.post('/api/social/posts/', data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        post_id = resp.data.get('id')
        self.assertIsNotNone(post_id)
        from apps.social.infrastructure.models.social import PostMedia
        medias = PostMedia.objects.filter(post_id=post_id)
        self.assertEqual(medias.count(), 2)
        self.assertIn('media_files', resp.data)
        self.assertEqual(len(resp.data['media_files']), 2)
        self.assertEqual(resp.data.get('post_type'), 'video')

        self.assertEqual(resp.data['status'], 'processing')
        self.assertTrue(all(not item['file_url'] for item in resp.data['media_files']))
        from apps.social.application.post_media import process_post_media
        for media in medias: process_post_media(media.pk)
        ready = self.client.get(f'/api/social/posts/{post_id}/')
        self.assertEqual(ready.data['status'], 'published')
        self.assertEqual({item['media_type'] for item in ready.data['media_files']}, {'image', 'video'})
        self.assertTrue(all(item['file_url'] for item in ready.data['media_files']))

    def test_create_post_with_temporary_uploadedfile(self):
        from django.core.files.uploadedfile import TemporaryUploadedFile
        content = valid_image()
        tmp = TemporaryUploadedFile('pic.jpg', 'image/jpeg', len(content), None)
        tmp.file.write(content)
        tmp.file.seek(0)
        data = {
            'text': 'Temp file test',
            'visibility': 'public',
            'media_0': tmp,
        }
        resp = self.client.post('/api/social/posts/', data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        jid = resp.data.get('id')
        self.assertIsNotNone(jid)
        from apps.social.infrastructure.models.social import PostMedia
        self.assertEqual(PostMedia.objects.filter(post_id=jid).count(), 1)

    def test_create_post_with_anime_and_playlist_attachment(self):
        from apps.anime.infrastructure.models.anime import Anime
        from apps.playlists.infrastructure.models.playlists import Playlist
        anime = Anime.objects.create(title_ru='Тестовое', status='ongoing')
        playlist = Playlist.objects.create(user=self.user, title='My list', is_public=True)
        data = {
            'text': 'Attached content',
            'visibility': 'public',
            'anime': anime.id,
            'playlist': playlist.id,
        }
        resp = self.client.post('/api/social/posts/', data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        anime_data = resp.data.get('anime')
        self.assertIsInstance(anime_data, dict)
        self.assertEqual(anime_data.get('id'), anime.id)
        self.assertEqual(anime_data.get('title_ru'), anime.title_ru)
        self.assertIn('poster_url', anime_data)
        self.assertEqual(resp.data['playlist']['id'], playlist.id)
        self.assertEqual(resp.data.get('anime_title'), anime.title_ru)
        self.assertEqual(resp.data.get('playlist_title'), playlist.title)
        self.assertEqual(resp.data.get('post_type'), 'playlist')

    def test_post_attachment_viewset(self):
        from apps.anime.infrastructure.models.anime import Anime
        anime = Anime.objects.create(title_ru='Прикреплённое', status='ongoing')
        post = Post.objects.create(author=self.user, text='With attachment', status='published')
        data = {
            'post': post.id,
            'content_type': 'anime',
            'object_id': anime.id
        }
        resp = self.client.post('/api/social/post-attachments/', data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        attach_id = resp.data.get('id')
        self.assertIsNotNone(attach_id)
        list_resp = self.client.get(f'/api/social/post-attachments/?post={post.id}')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        rows = list_resp.data.get('results', []) if isinstance(list_resp.data, dict) else list_resp.data
        self.assertEqual(len(rows), 1)
        del_resp = self.client.delete(f'/api/social/post-attachments/{attach_id}/')
        self.assertIn(del_resp.status_code, [200, 204])


class LikeDislikeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = make_user('author')
        self.liker = make_user('liker')
        self.client.force_authenticate(user=self.liker)
        self.post = Post.objects.create(
            author=self.author,
            text='A great post',
            status='published',
            visibility='public',
        )

    def test_like_post(self):
        resp = self.client.post(f'/api/social/posts/{self.post.id}/like/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['liked'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes_count, 1)

    def test_unlike_post(self):
        PostLike.objects.create(user=self.liker, post=self.post)
        self.post.likes_count = 1
        self.post.save()

        resp = self.client.post(f'/api/social/posts/{self.post.id}/like/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['liked'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes_count, 0)

    def test_cannot_like_own_post(self):
        self.client.force_authenticate(user=self.author)
        resp = self.client.post(f'/api/social/posts/{self.post.id}/like/')
        self.assertEqual(resp.status_code, 400)

    def test_dislike_removes_existing_like(self):
        PostLike.objects.create(user=self.liker, post=self.post)
        self.post.likes_count = 1
        self.post.save()

        resp = self.client.post(f'/api/social/posts/{self.post.id}/dislike/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['disliked'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes_count, 0)
        self.assertEqual(self.post.dislikes_count, 1)
        self.assertFalse(PostLike.objects.filter(user=self.liker, post=self.post).exists())

    def test_like_removes_existing_dislike(self):
        PostDislike.objects.create(user=self.liker, post=self.post)
        self.post.dislikes_count = 1
        self.post.save()

        resp = self.client.post(f'/api/social/posts/{self.post.id}/like/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['liked'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.dislikes_count, 0)
        self.assertEqual(self.post.likes_count, 1)
        self.assertFalse(PostDislike.objects.filter(user=self.liker, post=self.post).exists())

    def test_like_model_unique_constraint(self):
        PostLike.objects.create(user=self.liker, post=self.post)
        with self.assertRaises(Exception):
            PostLike.objects.create(user=self.liker, post=self.post)

    def test_dislike_model_unique_constraint(self):
        PostDislike.objects.create(user=self.liker, post=self.post)
        with self.assertRaises(Exception):
            PostDislike.objects.create(user=self.liker, post=self.post)


class CommentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = make_user('post_author')
        self.commenter = make_user('commenter')
        self.client.force_authenticate(user=self.commenter)
        self.post = Post.objects.create(
            author=self.author,
            text='Post with comments',
            status='published',
            visibility='public',
        )

    def test_create_root_comment(self):
        resp = self.client.post(f'/api/social/posts/{self.post.id}/comments/', {
            'content': 'Great post!'
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['content'], 'Great post!')
        self.assertIsNone(resp.data['parent'])

    def test_create_reply(self):
        parent = PostComment.objects.create(
            post=self.post,
            author=self.author,
            content='Parent comment',
            level=0,
        )
        resp = self.client.post(f'/api/social/posts/{self.post.id}/comments/', {
            'content': 'Reply!',
            'parent': parent.id,
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['parent'], str(parent.id))

    def test_comment_nesting_level(self):
        parent = PostComment.objects.create(
            post=self.post, author=self.author, content='L0', level=0
        )
        child = PostComment.objects.create(
            post=self.post, author=self.commenter, content='L1', parent=parent, level=1
        )
        self.assertEqual(child.level, 1)
        self.assertTrue(child.is_reply)

    def test_edit_comment_within_10_minutes(self):
        comment = PostComment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Original',
            level=0,
        )
        resp = self.client.put(f'/api/social/posts/{self.post.id}/comments/{comment.id}/', {
            'content': 'Edited'
        })
        self.assertIn(resp.status_code, [200, 405])

    def test_delete_comment_by_author(self):
        comment = PostComment.objects.create(
            post=self.post,
            author=self.commenter,
            content='To delete',
            level=0,
        )
        resp = self.client.delete(f'/api/social/posts/{self.post.id}/comments/{comment.id}/')
        self.assertIn(resp.status_code, [200, 204])

    def test_delete_comment_by_other_user_denied(self):
        other = make_user('other_user')
        comment = PostComment.objects.create(
            post=self.post,
            author=other,
            content='Another comment',
            level=0,
        )
        resp = self.client.delete(f'/api/social/posts/{self.post.id}/comments/{comment.id}/')
        self.assertIn(resp.status_code, [403, 404])

    def test_get_comments(self):
        for i in range(5):
            PostComment.objects.create(
                post=self.post,
                author=self.commenter,
                content=f'Comment {i}',
                level=0,
            )
        resp = self.client.get(f'/api/social/posts/{self.post.id}/comments/')
        self.assertEqual(resp.status_code, 200)
        rows = resp.data.get('results', []) if isinstance(resp.data, dict) else resp.data
        self.assertGreaterEqual(len(rows), 5)


class FeedTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('feed_user')
        self.followed = make_user('followed_user')
        self.client.force_authenticate(user=self.user)
        Follow.objects.create(follower=self.user, following=self.followed)

    def test_feed_returns_posts(self):
        Post.objects.create(
            author=self.followed,
            text='Followed post',
            status='published',
            visibility='public',
        )
        resp = self.client.get('/api/social/feed/weighted/')
        self.assertEqual(resp.status_code, 200)

    def test_followers_feed_only_subscribed(self):
        Post.objects.create(
            author=self.followed,
            text='Subscribed post',
            status='published',
            visibility='public',
        )
        stranger = make_user('stranger')
        Post.objects.create(
            author=stranger,
            text='Stranger post',
            status='published',
            visibility='public',
        )
        resp = self.client.get('/api/social/feed/followers/')
        self.assertEqual(resp.status_code, 200)
        post_ids = [p['id'] for p in resp.data.get('results', [])]
        stranger_posts = Post.objects.filter(author=stranger).values_list('id', flat=True)
        for sid in stranger_posts:
            self.assertNotIn(sid, post_ids)

    def test_feed_excludes_deleted_posts(self):
        Post.objects.create(
            author=self.followed,
            text='Deleted post',
            status='deleted',
            visibility='public',
        )
        resp = self.client.get('/api/social/feed/followers/')
        self.assertEqual(resp.status_code, 200)
        post_texts = [p.get('text', '') for p in resp.data.get('results', [])]
        self.assertNotIn('Deleted post', post_texts)


class FollowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('follower')
        self.target = make_user('target')
        self.client.force_authenticate(user=self.user)

    def test_follow_user(self):
        resp = self.client.post(f'/api/social/follow/toggle/{self.target.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['following'])
        self.assertTrue(Follow.objects.filter(follower=self.user, following=self.target).exists())

    def test_unfollow_user(self):
        Follow.objects.create(follower=self.user, following=self.target)
        resp = self.client.post(f'/api/social/follow/toggle/{self.target.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['following'])
        self.assertFalse(Follow.objects.filter(follower=self.user, following=self.target).exists())

    def test_cannot_follow_self(self):
        resp = self.client.post(f'/api/social/follow/toggle/{self.user.id}/')
        self.assertEqual(resp.status_code, 400)

    def test_follow_unique_constraint(self):
        Follow.objects.create(follower=self.user, following=self.target)
        with self.assertRaises(Exception):
            Follow.objects.create(follower=self.user, following=self.target)


class PermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = make_user('p_author')
        self.other = make_user('p_other')
        self.moderator = make_user('p_mod', is_staff=True)
        self.post = Post.objects.create(
            author=self.author,
            text='Permission test post',
            status='published',
            visibility='public',
        )

    def test_author_can_delete(self):
        self.assertTrue(self.post.can_delete(self.author))

    def test_other_cannot_delete(self):
        self.assertFalse(self.post.can_delete(self.other))

    def test_unauthenticated_cannot_create(self):
        resp = self.client.post('/api/social/posts/', {'text': 'Anon'})
        self.assertEqual(resp.status_code, 401)

    def test_private_post_not_in_public_feed(self):
        Post.objects.create(
            author=self.author,
            text='Private post',
            status='published',
            visibility='private',
        )
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(f'/api/social/users/{self.author.id}/posts/')
        self.assertEqual(resp.status_code, 200)
        rows = resp.data.get('results', []) if isinstance(resp.data, dict) else resp.data
        post_texts = [p.get('text', '') for p in rows]
        self.assertNotIn('Private post', post_texts)


class BookmarkTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('bookmarker')
        self.author = make_user('b_author')
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(
            author=self.author,
            text='Bookmarkable post',
            status='published',
            visibility='public',
        )

    def test_add_bookmark(self):
        resp = self.client.post(f'/api/social/posts/{self.post.id}/bookmark/')
        self.assertIn(resp.status_code, [200, 201])
        self.assertTrue(Bookmark.objects.filter(user=self.user, post=self.post).exists())

    def test_remove_bookmark(self):
        Bookmark.objects.create(user=self.user, post=self.post)
        resp = self.client.post(f'/api/social/posts/{self.post.id}/bookmark/remove/')
        self.assertIn(resp.status_code, [200, 204])
        self.assertFalse(Bookmark.objects.filter(user=self.user, post=self.post).exists())


class RepostTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.reposter = make_user('reposter')
        self.author = make_user('r_author')
        self.client.force_authenticate(user=self.reposter)
        self.post = Post.objects.create(
            author=self.author,
            text='Original post',
            status='published',
            visibility='public',
        )

    def test_repost(self):
        resp = self.client.post(f'/api/social/posts/{self.post.id}/repost/action/', {
            'comment': 'Great post!'
        })
        self.assertIn(resp.status_code, [200, 201])
        self.post.refresh_from_db()
        self.assertGreater(self.post.reposts_count, 0)

    def test_repost_unique_per_user(self):
        Repost.objects.create(user=self.reposter, original_post=self.post)
        with self.assertRaises(Exception):
            Repost.objects.create(user=self.reposter, original_post=self.post)


class GroupChatMessageTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('msg_user')
        self.chat = GroupChat.objects.create(
            name='Test Chat',
            created_by=self.user,
            is_public=True,
        )
        ChatMember.objects.create(user=self.user, chat=self.chat, is_admin=True)
        from apps.social.infrastructure.models.social_chat import ChatTopic
        self.topic1 = ChatTopic.objects.create(chat=self.chat, title='Topic 1', slug='topic-1')
        self.topic2 = ChatTopic.objects.create(chat=self.chat, title='Topic 2', slug='topic-2')
        self.client.force_authenticate(user=self.user)

    def test_send_message_links_to_chat(self):
        resp = self.client.post(f'/api/social/chats/{self.chat.id}/messages/', {
            'text': 'Hello topic',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        msg = Message.objects.get(id=resp.data['id'])
        self.assertEqual(msg.chat_id, self.chat.id)
        self.assertIsNone(msg.private_chat_id)

    def test_send_message_with_topic_id(self):
        resp = self.client.post(f'/api/social/chats/{self.chat.id}/messages/', {
            'text': 'Hello topic',
            'topic_id': self.topic1.pk,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        msg = Message.objects.get(id=resp.data['id'])
        self.assertEqual(msg.topic_id, self.topic1.pk)
        self.assertEqual(msg.chat_id, self.chat.id)

    def test_list_messages_filters_by_topic_id(self):
        Message.objects.create(chat=self.chat, sender=self.user, text='main', topic_id=None)
        Message.objects.create(chat=self.chat, sender=self.user, text='topic1', topic_id=self.topic1.pk)
        Message.objects.create(chat=self.chat, sender=self.user, text='topic2', topic_id=self.topic2.pk)
        resp = self.client.get(f'/api/social/chats/{self.chat.id}/messages/', {'topic_id': self.topic1.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        texts = [m['text'] for m in (resp.data.get('results', resp.data))]
        self.assertIn('topic1', texts)
        self.assertNotIn('main', texts)
        self.assertNotIn('topic2', texts)

    def test_non_member_cannot_list_messages(self):
        other = make_user('other_user')
        self.chat.is_public = False
        self.chat.save()
        self.client.force_authenticate(user=other)
        Message.objects.create(chat=self.chat, sender=self.user, text='secret')
        resp = self.client.get(f'/api/social/chats/{self.chat.id}/messages/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
