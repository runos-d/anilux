import subprocess
import sys
from unittest.mock import patch
from django.test import TestCase, SimpleTestCase
from core.test_helpers import stream_body
from rest_framework.test import APIClient
from apps.anime.models import Anime, Franchise
from apps.social.application.tests import make_user
from apps.social.infrastructure.models.social import GroupChat, Post, PostMedia
from apps.social.application.post_media import run_video_command


class ChatDiscussionSearchTests(TestCase):
    def test_franchise_discussion_is_found_by_any_member_title(self):
        owner, reader = make_user('franchise-owner'), make_user('franchise-reader')
        franchise = Franchise.objects.create(name='Невероятное приключение')
        Anime.objects.create(title_ru='Стальной шар', title_en='Steel Ball Run', title_jp='スティール', franchise=franchise)
        target = GroupChat.objects.create(name='Обсуждение франшизы', created_by=owner,
            franchise_id=franchise.pk, folder_type='discussions', is_public=True)
        GroupChat.objects.create(name='Steel Ball Run private', created_by=owner,
            franchise_id=franchise.pk, folder_type='discussions', is_public=False)
        client = APIClient(); client.force_authenticate(reader)
        for query in ('Стальной шар', 'Steel Ball', 'スティール'):
            response = client.get('/api/social/group-chats/', {'search': query})
            self.assertEqual(200, response.status_code, response.data)
            rows = response.data if isinstance(response.data, list) else response.data['results']
            self.assertEqual([str(target.public_id)], [str(row['id']) for row in rows])

    def test_searches_titles_beyond_first_page_and_excludes_private_discussions(self):
        owner, reader = make_user('search-owner'), make_user('search-reader')
        anime = Anime.objects.create(title_ru='Невероятное приключение ДжоДжо', title_en='JoJo no Kimyou na Bouken')
        target = GroupChat.objects.create(name='Обсуждение', created_by=owner, anime=anime, folder_type='discussions', is_public=True)
        hidden = GroupChat.objects.create(name='JoJo private', created_by=owner, anime=anime, folder_type='discussions', is_public=False)
        for index in range(30):
            GroupChat.objects.create(name=f'Other {index}', created_by=owner, folder_type='discussions', is_public=True)
        client = APIClient(); client.force_authenticate(reader)
        for query in ('ДжоДжо', 'JoJo'):
            response = client.get('/api/social/group-chats/', {'search': query})
            self.assertEqual(200, response.status_code, response.data)
            rows = response.data if isinstance(response.data, list) else response.data['results']
            self.assertEqual([str(target.public_id)], [str(row['id']) for row in rows])

    def test_media_progress_survives_detail_read_and_ready_reports_completion(self):
        owner = make_user('progress-owner')
        post = Post.objects.create(author=owner, text='Progress', status='processing')
        media = PostMedia.objects.create(post=post, media_type='video', processing_state='processing', processing_progress=43)
        client = APIClient(); client.force_authenticate(owner)
        response = client.get(f'/api/social/posts/{post.pk}/')
        self.assertEqual(43, response.data['media_files'][0]['processing_progress'])
        PostMedia.objects.filter(pk=media.pk).update(processing_state='ready', processing_progress=0)
        response = client.get(f'/api/social/posts/{post.pk}/')
        self.assertEqual(100, response.data['media_files'][0]['processing_progress'])


class VideoProgressTests(SimpleTestCase):
    def test_real_subprocess_reports_timeline_and_failure(self):
        progress = []
        run_video_command([sys.executable, '-c', "print('out_time_us=1000000'); print('out_time_us=2000000')"], 2, progress.append, 0, 70, timeout=5)
        self.assertIn(35, progress)
        self.assertEqual(70, progress[-1])
        with self.assertRaises(subprocess.CalledProcessError):
            run_video_command([sys.executable, '-c', 'raise SystemExit(1)'], 2, progress.append, 0, 70, timeout=5)


class PostUploadOrderingTests(TestCase):
    def test_parallel_uploads_preserve_user_order_and_images_avoid_video_queue(self):
        from apps.social.application.post_media import make_upload, queue_media
        from apps.social.application.post_commands import prepare_uploads
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser
        owner = make_user('ordered-upload-owner')
        first = make_upload(owner, 'first.png', 1)
        second = make_upload(owner, 'second.png', 1)
        for upload in (first, second):
            upload.state = 'uploaded'; upload.save(update_fields=['state'])
        ids = [str(upload.pk) for upload in sorted((first, second), key=lambda row: row.pk, reverse=True)]
        request = Request(APIRequestFactory().post('/', {'media_ids': ids}, format='json'), parsers=[JSONParser()])
        request.user = owner
        self.assertEqual(ids, [str(upload.pk) for upload in prepare_uploads(request)])
        post = Post.objects.create(author=owner)
        for kind, expected_queue in (('image', 'celery'), ('video', 'post_media')):
            media = PostMedia.objects.create(post=post, media_type=kind, processing_state='queued')
            with patch('apps.social.application.post_media.process_post_media.apply_async') as enqueue:
                queue_media(media.pk)
                enqueue.assert_called_once_with(args=[media.pk], queue=expected_queue)


class ChatVideoCacheTests(TestCase):
    def test_revalidation_keeps_bytes_private_and_revokes_cached_access(self):
        from django.core.files.base import ContentFile
        from apps.social.infrastructure.models.social import PrivateChat, Message
        from apps.social.application.conversations import clear_history
        from apps.social.infrastructure.chat_storage import private_file_url
        from rest_framework.test import APIRequestFactory
        owner, reader = make_user('video-owner'), make_user('video-reader')
        chat = PrivateChat.objects.create(user1=owner, user2=reader)
        message = Message.objects.create(private_chat=chat, sender=owner, text='Video')
        message.media.save('sample.mp4', ContentFile(b'video-bytes-for-range-test'))
        request = APIRequestFactory().get('/'); request.user = reader
        url = private_file_url(message.media, request)
        self.assertEqual(url, private_file_url(message.media, request))
        client = APIClient()
        first = client.get(url, HTTP_RANGE='bytes=0-4')
        self.assertEqual(206, first.status_code)
        self.assertEqual(b'video', stream_body(first))
        etag = first['ETag']
        self.assertEqual('private, no-cache, must-revalidate', first['Cache-Control'])
        response = client.get(url, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(304, response.status_code)
        self.assertEqual(b'', response.content)
        clear_history(chat, reader, hide=True)
        response = client.get(url, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(404, response.status_code)
