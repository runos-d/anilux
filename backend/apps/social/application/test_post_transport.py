import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from unittest import skipUnless
from unittest.mock import patch
from django.conf import settings
from django.db import close_old_connections
from django.test import TransactionTestCase
from PIL import Image
from rest_framework.test import APIClient
from apps.social.application.tests import make_user
from apps.social.infrastructure.models.social import Post, PostMedia
from apps.social.infrastructure.models.post_lifecycle import PostEvent


@skipUnless(getattr(settings, 'CHAT_INTEGRATION_TESTS', False), 'Requires disposable Redis and Celery worker')
class PostTransportTests(TransactionTestCase):
    def setUp(self):
        self.owner = make_user('post_transport_owner')
        self.reader = make_user('post_transport_reader')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def wait_ready(self, post):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            post.refresh_from_db()
            if post.status != 'processing': break
            time.sleep(.1)
        self.assertEqual('published', post.status)
        self.assertTrue(post.media_files.filter(processing_state='ready').exists())

    def test_resume_and_real_worker_publish_secure_media(self):
        data = BytesIO(); Image.new('RGB', (32, 24), 'blue').save(data, 'PNG')
        content = data.getvalue() + b'\0' * (4 * 1024 * 1024 + 17)
        upload = self.client.post('/api/social/post-uploads/', {'filename': 'resume.png', 'size': len(content)}, format='json')
        self.assertEqual(201, upload.status_code, upload.data)
        path = f"/api/social/post-uploads/{upload.data['id']}/"
        first = content[:4*1024*1024]
        response = self.client.patch(path, first, content_type='application/octet-stream', HTTP_UPLOAD_OFFSET='0', HTTP_UPLOAD_CHECKSUM=hashlib.sha256(first).hexdigest())
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(len(first), self.client.get(path).data['offset'])
        response = self.client.patch(path, first, content_type='application/octet-stream', HTTP_UPLOAD_OFFSET='0', HTTP_UPLOAD_CHECKSUM=hashlib.sha256(first).hexdigest())
        self.assertEqual(409, response.status_code)
        rest = content[len(first):]
        response = self.client.patch(path, rest, content_type='application/octet-stream', HTTP_UPLOAD_OFFSET=str(len(first)), HTTP_UPLOAD_CHECKSUM=hashlib.sha256(rest).hexdigest())
        self.assertEqual(200, response.status_code, response.data)
        response = self.client.post(path+'complete/', {'checksum': hashlib.sha256(content).hexdigest()}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        response = self.client.post('/api/social/posts/', {'text': 'real resumable upload', 'media_ids': [upload.data['id']], 'client_post_id': 'real-resume'}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        post = Post.objects.get(pk=response.data['id'])
        self.wait_ready(post)
        self.client.force_authenticate(self.reader)
        response = self.client.get(f'/api/social/posts/{post.pk}/')
        self.assertEqual(200, response.status_code, response.data)
        self.assertTrue(response.data['media_files'][0]['url'])
        from apps.social.application.post_media import process_post_media
        process_post_media.delay(post.media_files.get().pk).get(timeout=25)
        self.assertEqual(1, PostMedia.objects.filter(post=post).count())
        self.assertEqual(1, PostEvent.objects.filter(post=post, kind='new_post').count())

    def test_concurrent_create_and_outbox_retry_do_not_duplicate_notifications(self):
        def create():
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(self.owner)
                response = client.post('/api/social/posts/', {'text': 'same command', 'client_post_id': 'parallel-create'}, format='json')
                return response.status_code, response.data['id']
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: create(), range(2)))
        self.assertEqual(1, len({result[1] for result in results}))
        self.assertEqual([200, 201], sorted(result[0] for result in results))
        post = Post.objects.get(pk=results[0][1])
        from apps.social.application.post_commands import deliver_post_event
        with patch.object(deliver_post_event, 'delay'):
            self.client.force_authenticate(self.reader)
            response = self.client.post(f'/api/social/posts/{post.pk}/like/', {'active': True, 'client_action_id':'transport-like'}, format='json')
            self.assertEqual(200, response.status_code, response.data)
        event = PostEvent.objects.get(post=post, kind='post_reaction')
        with patch('core.redis_client.redis_pubsub_manager._get_redis_client', return_value=None):
            with self.assertRaises(ConnectionError): deliver_post_event(str(event.pk))
        event.refresh_from_db(); self.assertIsNone(event.delivered_at)
        deliver_post_event.delay(str(event.pk)).get(timeout=25)
        deliver_post_event.delay(str(event.pk)).get(timeout=25)
        from apps.notifications.infrastructure.models.notifications import Notification
        self.assertEqual(1, Notification.objects.filter(dedupe_key=f'post-event:{event.pk}:{self.owner.pk}').count())
