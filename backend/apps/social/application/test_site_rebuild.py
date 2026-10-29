import hashlib
from io import BytesIO
from unittest.mock import patch

from django.test import TestCase
from core.test_helpers import stream_body
from PIL import Image
from rest_framework.test import APIClient

from apps.social.application.tests import make_user
from apps.social.infrastructure.models.social import Post, PostMedia, Follow
from apps.social.infrastructure.models.post_lifecycle import PostUpload, PostEvent
from apps.social.infrastructure.post_storage import post_private_storage
from apps.anime.infrastructure.models.anime import Anime, Franchise
from apps.anime.application.recommendations import build, refresh_recommendations
from apps.users.infrastructure.models.users import UserLibrary


class SiteRebuildTests(TestCase):
    def test_old_draft_enters_new_feed_at_publication_without_changing_creation_date(self):
        from datetime import timedelta
        from django.utils import timezone
        draft = Post.objects.create(author=self.owner, text='Old draft', status='draft')
        original = timezone.now()-timedelta(days=30)
        Post.objects.filter(pk=draft.pk).update(created_at=original)
        Post.objects.create(author=self.reader, text='Earlier publication')
        response = self.client.post(f'/api/social/posts/{draft.pk}/publish/')
        self.assertEqual(200, response.status_code, response.data)
        draft.refresh_from_db()
        self.assertEqual(original, draft.created_at)
        response = self.client.get('/api/social/feed/extended/', {'page_size':20,'date_range':'day'})
        self.assertEqual(str(draft.pk), response.data['results'][0]['id'])

    def test_repost_lists_batch_original_permissions_and_reaction_flags(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from apps.social.infrastructure.models.social import PostLike
        sources = [Post.objects.create(author=self.reader, text=f'Original {index}',
                   visibility='private' if index % 5 == 0 else 'public') for index in range(60)]
        for source in sources:
            Post.objects.create(author=self.owner, post_type='repost', original_post=source)
        PostLike.objects.create(user=self.owner, post=sources[-1])
        for endpoint in ('posts/', 'feed/extended/'):
            with CaptureQueriesContext(connection) as small:
                first = self.client.get('/api/social/'+endpoint, {'page_size':20})
            with CaptureQueriesContext(connection) as large:
                second = self.client.get('/api/social/'+endpoint, {'page_size':50})
            self.assertEqual(200, second.status_code, second.data)
            self.assertLessEqual(len(large), len(small)+1)
            self.assertLessEqual(len(large), 20)
            reposts = [row for row in second.data['results'] if row['post_type'] == 'repost']
            self.assertEqual(50, len(reposts))
            for row in reposts:
                source_id = Post.objects.get(pk=row['id']).original_post_id
                original = row.get('original_post_data')
                if Post.objects.get(pk=source_id).visibility == 'private':
                    self.assertIsNone(original)
                else:
                    self.assertEqual(str(source_id), original['id'])
                    if source_id == sources[-1].pk: self.assertTrue(original['is_liked'])

    def test_calendar_import_failure_preserves_last_successful_snapshot(self):
        from apps.anime.infrastructure.models.read_models import CalendarSnapshot
        from apps.anime.application.tasks_kodik_dumps import import_kodik_calendar_task
        from apps.anime.application.anime_service import anime_service
        entries = [{'anime': {'id': 1, 'name': 'Saved'}, 'next_episode': 2, 'next_episode_at': '2026-10-11T12:00:00Z'}]
        snapshot = CalendarSnapshot.objects.create(entries=entries)
        with patch('apps.anime.application.kodik_dump_service.sync_calendar', side_effect=OSError('Source unavailable')):
            with self.assertRaises(OSError): import_kodik_calendar_task.run()
        snapshot.refresh_from_db()
        self.assertEqual(entries, snapshot.entries)
        with patch('apps.anime.application.kodik_dump_service.get_calendar_entries', return_value=None), \
             patch('apps.anime.application.anime_service.external_anime_api.get_calendar', side_effect=AssertionError('HTTP must not wait for providers')):
            self.assertEqual(entries, anime_service.get_calendar())

    def test_stable_media_tickets_do_not_bypass_current_permissions(self):
        import time
        from apps.social.application.post_media import process_post_media
        created = self.client.post('/api/social/posts/', {'media_ids':[self.upload()], 'visibility':'private'}, format='json')
        post = Post.objects.get(pk=created.data['id'])
        process_post_media(post.media_files.get().pk)
        first = self.client.get(f'/api/social/posts/{post.pk}/').data['media_files'][0]['url']
        later = time.time()+5
        with patch('django.core.signing.time.time', return_value=later):
            second = self.client.get(f'/api/social/posts/{post.pk}/').data['media_files'][0]['url']
        self.assertEqual(first, second)
        self.assertEqual(200, self.client.get(first).status_code)
        self.client.delete(f'/api/social/posts/{post.pk}/')
        self.assertEqual(404, self.client.get(first).status_code)

    def test_post_lists_batch_viewer_flags_and_keep_stable_cursors(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from django.contrib.contenttypes.models import ContentType
        from apps.social.infrastructure.models.social import Favorite
        rows = [Post.objects.create(author=self.reader, text=f'Batch {index}') for index in range(60)]
        Favorite.objects.create(user=self.owner, content_type=ContentType.objects.get_for_model(Post), object_id=rows[-1].pk)
        with CaptureQueriesContext(connection) as small_queries:
            first = self.client.get('/api/social/posts/', {'page_size':20})
        with CaptureQueriesContext(connection) as large_queries:
            larger = self.client.get('/api/social/posts/', {'page_size':50})
        self.assertEqual(200, first.status_code, first.data)
        self.assertEqual(20, len(first.data['results']))
        self.assertEqual(50, len(larger.data['results']))
        self.assertTrue(first.data['results'][0]['is_favorited'])
        self.assertLessEqual(len(large_queries), 10)
        self.assertLessEqual(len(large_queries), len(small_queries)+1)
        next_page = self.client.get('/api/social/posts/', {'page_size':20,'cursor':first.data['next_cursor']})
        self.assertEqual(200, next_page.status_code, next_page.data)
        self.assertFalse(set(row['id'] for row in first.data['results']) & set(row['id'] for row in next_page.data['results']))

    def test_moderation_deletes_private_content_through_transactional_commands(self):
        from apps.social.infrastructure.models.social import Report, PostComment
        from apps.social.infrastructure.models.post_lifecycle import PostFileCleanup
        from apps.social.application.post_media import process_post_media
        created = self.client.post('/api/social/posts/', {'text': 'Private', 'visibility': 'private', 'media_ids': [self.upload()]}, format='json')
        self.assertEqual(201, created.status_code, created.data)
        post = Post.objects.get(pk=created.data['id'])
        media = post.media_files.get()
        process_post_media(media.pk)
        comment = PostComment.objects.create(post=post, author=self.owner, content='Private comment')
        Post.objects.filter(pk=post.pk).update(comments_count=1)
        self.reader.is_staff = True
        self.reader.save(update_fields=['is_staff'])
        self.client.force_authenticate(self.reader)
        report = Report.objects.create(reporter=self.reader, content_type='comment', content_id=comment.pk, reason='other')
        body = {'status': 'resolved', 'action': 'delete_content'}
        response = self.client.patch(f'/api/social/moderation/reports/{report.pk}/', body, format='json')
        self.assertEqual(200, response.status_code, response.data)
        comment.refresh_from_db(); post.refresh_from_db()
        self.assertTrue(comment.is_deleted)
        self.assertEqual(0, post.comments_count)
        self.assertTrue(PostEvent.objects.filter(post=post, kind='post_comment_deleted').exists())
        report = Report.objects.create(reporter=self.reader, content_type='post', content_id=post.pk, reason='other')
        response = self.client.patch(f'/api/social/moderation/reports/{report.pk}/', body, format='json')
        self.assertEqual(200, response.status_code, response.data)
        post.refresh_from_db(); self.owner.refresh_from_db()
        self.assertEqual('deleted', post.status)
        self.assertTrue(post.is_deleted)
        self.assertEqual(0, self.owner.posts_count)
        self.assertTrue(PostFileCleanup.objects.filter(media=media).exists())
        self.assertEqual(1, PostEvent.objects.filter(post=post, kind='post_deleted').count())
        self.assertEqual(400, self.client.patch(f'/api/social/moderation/reports/{report.pk}/', body, format='json').status_code)

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.owner = make_user('site_owner')
        self.reader = make_user('site_reader')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def anime(self, suffix, **fields):
        return Anime.objects.create(title_ru='Аниме ' + suffix, slug='site-' + suffix, score=9, is_available=True, **fields)

    def image(self):
        target = BytesIO()
        Image.new('RGB', (32, 24), 'blue').save(target, 'PNG')
        return target.getvalue()

    def upload(self, content=None):
        content = content or self.image()
        response = self.client.post('/api/social/post-uploads/', {'filename': 'image.png', 'size': len(content)}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        pk = response.data['id']
        response = self.client.patch('/api/social/post-uploads/' + pk + '/', content, content_type='application/octet-stream',
            HTTP_UPLOAD_OFFSET='0', HTTP_UPLOAD_CHECKSUM=hashlib.sha256(content).hexdigest())
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['offset'], len(content))
        response = self.client.post('/api/social/post-uploads/' + pk + '/complete/')
        self.assertEqual(response.status_code, 200, response.data)
        return pk

    def test_grouping_happens_before_pagination(self):
        franchise = Franchise.objects.create(name='Франшиза', slug='site-franchise')
        for index in range(4):
            self.anime(str(index), franchise=franchise, franchise_order=index+1)
        self.anime('solo')
        first = self.client.get('/api/anime/', {'group_franchises': 'true', 'page_size': 1})
        second = self.client.get('/api/anime/', {'group_franchises': 'true', 'page_size': 1, 'page': 2})
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data['count'], 2)
        self.assertEqual(len(second.data['results']), 1)
        self.assertNotEqual(first.data['results'][0]['id'], second.data['results'][0]['id'])

    def test_public_catalog_cache_is_shared_but_library_filters_are_isolated(self):
        anime = self.anime('shared-cache')
        first = self.client.get('/api/anime/', {'page_size': 50, 'ordering': '-score'})
        self.client.force_authenticate(self.reader)
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        with CaptureQueriesContext(connection) as queries:
            second = self.client.get('/api/anime/', {'ordering': '-score', 'page_size': 50})
        self.assertEqual(first.data, second.data)
        self.assertEqual(0, len(queries))
        UserLibrary.objects.create(user=self.reader, anime=anime, status='completed')
        excluded = self.client.get('/api/anime/', {'excluded_library_statuses': 'completed'})
        self.assertEqual(0, excluded.data['count'])
        self.client.force_authenticate(self.owner)
        included = self.client.get('/api/anime/', {'excluded_library_statuses': 'completed'})
        self.assertEqual(1, included.data['count'])

    def test_recommendation_reason_matches_source_and_hidden_is_immediate(self):
        source = self.anime('source', genres=['Приключения'], kind='tv')
        target = self.anime('target', genres=['Приключения'], kind='tv')
        UserLibrary.objects.create(user=self.owner, anime=source, status='completed', rating=9)
        refresh_recommendations('user:' + str(self.owner.pk))
        response = self.client.get('/api/anime/home/personalized/', {'sections': 'based_on_watched'})
        row = next(row for row in response.data['based_on_watched'] if row['id'] == target.pk)
        self.assertEqual(row['reason_details']['source_anime_id'], source.pk)
        self.assertIn(source.title_ru, row['reason'])
        UserLibrary.objects.create(user=self.owner, anime=target, status='hidden')
        response = self.client.get('/api/anime/home/personalized/', {'sections': 'based_on_watched'})
        self.assertNotIn(target.pk, [row['id'] for row in response.data['based_on_watched']])

    def test_invalid_sections_and_month_are_400(self):
        self.assertEqual(self.client.get('/api/anime/home/personalized/?sections=wrong').status_code, 400)
        self.assertEqual(self.client.get('/api/anime/calendar/?month=2026-13').status_code, 400)

    def test_idempotency_rejects_changed_payload(self):
        data = {'text': 'Сохранить', 'client_post_id': 'site-command'}
        first = self.client.post('/api/social/posts/', data, format='json')
        second = self.client.post('/api/social/posts/', data, format='json')
        conflict = self.client.post('/api/social/posts/', {**data, 'text': 'Другой текст'}, format='json')
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(PostEvent.objects.filter(kind='new_post').count(), 1)

    def test_edit_version_and_author_are_enforced(self):
        post = Post.objects.create(author=self.owner, text='Original')
        path = f'/api/social/posts/{post.pk}/'
        response = self.client.patch(path, {'text': 'Changed', 'version': 1}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['version'], 2)
        self.assertEqual(self.client.patch(path, {'text': 'Lost', 'version': 1}, format='json').status_code, 409)
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.patch(path, {'text': 'Hacked'}, format='json').status_code, 403)

    def test_upload_resume_checksum_and_owner(self):
        content = self.image()
        response = self.client.post('/api/social/post-uploads/', {'filename': 'image.png', 'size': len(content)}, format='json')
        path = '/api/social/post-uploads/' + response.data['id'] + '/'
        self.assertEqual(self.client.patch(path, content, content_type='application/octet-stream',
            HTTP_UPLOAD_OFFSET='0', HTTP_UPLOAD_CHECKSUM='wrong').status_code, 400)
        self.assertEqual(self.client.get(path).data['offset'], 0)
        halfway = len(content)//2
        for offset, chunk in ((0, content[:halfway]), (halfway, content[halfway:])):
            response = self.client.patch(path, chunk, content_type='application/octet-stream',
                HTTP_UPLOAD_OFFSET=str(offset), HTTP_UPLOAD_CHECKSUM=hashlib.sha256(chunk).hexdigest())
            self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.patch(path, content, content_type='application/octet-stream',
            HTTP_UPLOAD_OFFSET='0', HTTP_UPLOAD_CHECKSUM=hashlib.sha256(content).hexdigest()).status_code, 409)
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_media_post_not_visible_until_ready_and_range_rechecks_access(self):
        upload_id = self.upload()
        response = self.client.post('/api/social/posts/', {'media_ids': [upload_id], 'visibility': 'private'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        pk = response.data['id']
        self.assertEqual(response.data['status'], 'processing')
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.get(f'/api/social/posts/{pk}/').status_code, 404)
        from apps.social.application.post_media import process_post_media
        process_post_media(PostMedia.objects.get(post_id=pk).pk)
        self.client.force_authenticate(self.owner)
        response = self.client.get(f'/api/social/posts/{pk}/')
        self.assertEqual(response.data['status'], 'published')
        url = response.data['media_files'][0]['url'].replace('http://testserver', '')
        result = self.client.get(url, HTTP_RANGE='bytes=0-9')
        self.assertEqual(result.status_code, 206)
        self.assertEqual(len(stream_body(result)), 10)
        self.assertEqual(self.client.head(url).status_code, 200)
        self.assertEqual(self.client.get(url, HTTP_RANGE='bytes=999999-').status_code, 416)
        post = Post.objects.get(pk=pk)
        post.is_deleted = True
        post.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_aggregate_limit_before_saving(self):
        response = self.client.post('/api/social/post-uploads/', {'filename': 'video.mp4', 'size': 250*1024*1024+1}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PostUpload.objects.exists())

    def test_invalid_upload_id_is_400(self):
        response = self.client.post('/api/social/posts/', {'media_ids': ['invalid']}, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Post.objects.exists())

    def test_multipart_media_ids_use_the_same_pipeline(self):
        import json
        response = self.client.post('/api/social/posts/', {'media_ids': json.dumps([self.upload()]),
            'text': 'Multipart', 'client_post_id': 'multipart-media'}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'processing')
        self.assertEqual(len(response.data['media_files']), 1)

    def test_comment_retry_parent_and_deleted_tree(self):
        post = Post.objects.create(author=self.owner, text='Commented')
        other = Post.objects.create(author=self.owner, text='Other')
        path = f'/api/social/posts/{post.pk}/comments/'
        data = {'content': 'Root', 'client_comment_id': 'root-retry'}
        first = self.client.post(path, data, format='json')
        second = self.client.post(path, data, format='json')
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(self.client.post(f'/api/social/posts/{other.pk}/comments/',
            {'content': 'Wrong', 'parent': first.data['id']}, format='json').status_code, 400)
        reply = self.client.post(path, {'content': 'Reply', 'parent': first.data['id']}, format='json')
        self.assertEqual(reply.status_code, 201, reply.data)
        self.assertEqual(self.client.delete(path + first.data['id'] + '/').status_code, 204)
        rows = self.client.get(path, {'sort': 'tree'}).data
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]['is_deleted'])
        post.refresh_from_db()
        self.assertEqual(post.comments_count, 1)

    def test_reaction_retries_do_not_toggle_twice(self):
        post = Post.objects.create(author=self.reader, text='React')
        path = f'/api/social/posts/{post.pk}/like/'
        payload = {'client_action_id': 'reaction-retry', 'active': True}
        first = self.client.post(path, payload, format='json')
        second = self.client.post(path, payload, format='json')
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data, second.data)
        self.assertEqual(post.likes.count(), 1)

    def test_repost_group_and_hashtag_counters_follow_committed_lifecycle(self):
        from apps.social.infrastructure.models.social import Group, Hashtag
        group = Group.objects.create(name='Counters', creator=self.owner)
        original = Post.objects.create(author=self.reader, text='Original')
        response = self.client.post('/api/social/posts/', {'text': 'Repost #first', 'group': group.pk, 'original_post': original.pk}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        pk = response.data['id']
        original.refresh_from_db(); group.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(1, self.owner.posts_count)
        self.assertEqual(1, original.reposts_count); self.assertEqual(1, group.posts_count)
        self.assertEqual(1, Hashtag.objects.get(name='first').posts_count)
        response = self.client.patch(f'/api/social/posts/{pk}/', {'text': 'Edited #second', 'version': 1}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(0, Hashtag.objects.get(name='first').posts_count)
        self.assertEqual(1, Hashtag.objects.get(name='second').posts_count)
        self.assertEqual(400, self.client.patch(f'/api/social/posts/{pk}/', {'text': 'Cycle', 'original_post': pk, 'version': 2}, format='json').status_code)
        self.assertEqual(200, self.client.delete(f'/api/social/posts/{pk}/').status_code)
        original.refresh_from_db(); group.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(0, self.owner.posts_count)
        self.assertEqual(0, original.reposts_count); self.assertEqual(0, group.posts_count)
        self.assertEqual(0, Hashtag.objects.get(name='second').posts_count)

    def test_repost_action_counts_canonical_posts_and_generic_delete(self):
        original = Post.objects.create(author=self.reader, text='Original')
        direct = self.client.post('/api/social/posts/', {'text': 'Direct', 'original_post': original.pk}, format='json')
        self.assertEqual(201, direct.status_code, direct.data)
        action = self.client.post(f'/api/social/posts/{original.pk}/repost/', {'client_action_id': 'repost-once'}, format='json')
        self.assertEqual(200, action.status_code, action.data)
        original.refresh_from_db()
        self.assertEqual(1, original.reposts_count)
        self.assertEqual(200, self.client.delete(f"/api/social/posts/{direct.data['id']}/").status_code)
        original.refresh_from_db()
        self.assertEqual(0, original.reposts_count)

    def test_reports_deduplicate_and_cannot_retarget_private_content(self):
        public = Post.objects.create(author=self.reader, text='Report this')
        private = Post.objects.create(author=self.reader, text='Private', visibility='private')
        payload = {'content_type': 'post', 'content_id': str(public.pk), 'reason': 'spam'}
        first = self.client.post('/api/social/reports/', payload, format='json')
        again = self.client.post('/api/social/reports/', payload, format='json')
        self.assertEqual(201, first.status_code, first.data)
        self.assertEqual(200, again.status_code, again.data)
        self.assertEqual(first.data['id'], again.data['id'])
        updated = self.client.patch(f"/api/social/reports/{first.data['id']}/", {'content_id': private.pk, 'status': 'resolved'}, format='json')
        self.assertEqual(200, updated.status_code, updated.data)
        self.assertEqual(public.pk, updated.data['content_id'])
        self.assertEqual('pending', updated.data['status'])
        action = self.client.post(f'/api/social/posts/{public.pk}/report/', {'reason': 'spam'}, format='json')
        self.assertEqual(200, action.status_code, action.data)
        self.assertEqual(first.data['id'], action.data['id'])
        self.assertEqual(404, self.client.post(f'/api/social/posts/{private.pk}/report/', {'reason': 'spam'}, format='json').status_code)
        self.assertEqual(400, self.client.post('/api/social/reports/', {**payload, 'content_id': 'broken'}, format='json').status_code)

    def test_media_replacement_activates_only_current_generation(self):
        from apps.social.application.post_media import process_post_media
        response = self.client.post('/api/social/posts/', {'media_ids': [self.upload()]}, format='json')
        pk = response.data['id']
        process_post_media(PostMedia.objects.get(post_id=pk).pk)
        for version in (1, 2):
            response = self.client.patch(f'/api/social/posts/{pk}/',
                {'version': version, 'media_ids': [self.upload()], 'retain_media_ids': []}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
            post = Post.objects.get(pk=pk)
            process_post_media(post.pending_edit['new_media_ids'][0])
            self.assertEqual(PostMedia.objects.filter(post_id=pk, is_active=True).count(), 1)
        self.assertEqual(PostMedia.objects.filter(post_id=pk, is_active=False).count(), 2)

    def test_animated_images_preserve_frames_and_have_a_light_poster(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.social.application.post_media import process_post_media
        data = BytesIO()
        frames = [Image.new('RGB', (32, 24), color) for color in ('blue', 'red')]
        frames[0].save(data, 'GIF', save_all=True, append_images=frames[1:], duration=100, loop=0)
        response = self.client.post('/api/social/posts/', {'text': 'Animation',
            'image_file': SimpleUploadedFile('motion.gif', data.getvalue(), content_type='image/gif')}, format='multipart')
        self.assertEqual(201, response.status_code, response.data)
        media = PostMedia.objects.get(post_id=response.data['id'])
        process_post_media(media.pk); media.refresh_from_db()
        with Image.open(media.file.path) as animation: self.assertEqual(2, animation.n_frames)
        self.assertNotEqual(media.file.name, media.poster.name)
        self.assertEqual(hashlib.sha256(data.getvalue()).hexdigest(), hashlib.sha256(media.file.read()).hexdigest())

    def test_retry_requeues_failed_media_once_and_updates_visible_status(self):
        response = self.client.post('/api/social/posts/', {'media_ids': [self.upload()]}, format='json')
        post = Post.objects.get(pk=response.data['id']); media = post.media_files.get()
        Post.objects.filter(pk=post.pk).update(status='failed')
        PostMedia.objects.filter(pk=media.pk).update(processing_state='failed')
        PostUpload.objects.filter(pk=media.upload_id).update(state='failed')
        with patch('apps.social.presentation.views.post_uploads.queue_media') as queue:
            path = f'/api/social/post-uploads/{media.upload_id}/retry/'
            self.assertEqual(200, self.client.post(path).status_code)
            self.assertEqual(200, self.client.post(path).status_code)
            self.assertEqual(1, queue.call_count)
        post.refresh_from_db(); media.refresh_from_db()
        self.assertEqual('processing', post.status); self.assertEqual('queued', media.processing_state)

    def test_privacy_change_reaches_former_online_readers_without_post_content(self):
        import json
        from apps.social.application.post_commands import deliver_post_event
        post = Post.objects.create(author=self.owner, text='Previously public')
        response = self.client.patch(f'/api/social/posts/{post.pk}/', {'visibility':'private', 'version':1}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        event = PostEvent.objects.get(post=post, kind='post_updated')
        with patch('core.online_status.online_status.get_online_ids', return_value=[self.reader.pk]), \
             patch('core.redis_client.redis_pubsub_manager._get_redis_client') as redis:
            deliver_post_event(str(event.pk))
            packet = json.loads(redis.return_value.pipeline.return_value.publish.call_args_list[0].args[1])
        self.assertIn(self.reader.pk, packet['target_users'])
        self.assertNotIn('text', packet['data'])
        self.client.force_authenticate(self.reader)
        self.assertEqual(404, self.client.get(f'/api/social/posts/{post.pk}/').status_code)

    def test_extended_and_ranked_feeds_enforce_private_access(self):
        public = Post.objects.create(author=self.reader, text='Public')
        private = Post.objects.create(author=self.reader, text='Secret', visibility='private', likes_count=100)
        for path in ('extended', 'hot', 'top', 'trending'):
            response = self.client.get(f'/api/social/feed/{path}/')
            self.assertEqual(response.status_code, 200, response.data)
            rows = response.data['results'] if isinstance(response.data, dict) else response.data
            self.assertIn(str(public.pk), [row['id'] for row in rows])
            self.assertNotIn(str(private.pk), [row['id'] for row in rows])
        self.assertEqual(self.client.post('/api/social/bookmarks/toggle/', {'post_id': private.pk}, format='json').status_code, 404)

    def test_repost_and_chat_forward_are_idempotent(self):
        from apps.social.infrastructure.models.social import PrivateChat, Message
        original = Post.objects.create(author=self.reader, text='Shared')
        path = f'/api/social/posts/{original.pk}/repost/action/'
        data = {'client_action_id': 'repost-command'}
        first = self.client.post(path, data, format='json')
        second = self.client.post(path, data, format='json')
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data, second.data)
        self.assertEqual(Post.objects.filter(original_post=original).count(), 1)
        chat = PrivateChat.objects.create(user1=self.owner, user2=self.reader)
        data = {'client_action_id': 'forward-command', 'destination': 'chat', 'chat_id': chat.public_id}
        first = self.client.post(path, data, format='json')
        second = self.client.post(path, data, format='json')
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data, second.data)
        self.assertEqual(Message.objects.filter(private_chat=chat, shared_post=original).count(), 1)

    def test_draft_publish_and_deleted_media_job_do_not_publish(self):
        from apps.social.application.post_media import process_post_media
        response = self.client.post('/api/social/posts/', {'text': 'Draft', 'status': 'draft'}, format='json')
        pk = response.data['id']
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.get(f'/api/social/posts/{pk}/').status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(f'/api/social/posts/{pk}/publish/').data['status'], 'published')
        response = self.client.post('/api/social/posts/', {'media_ids': [self.upload()]}, format='json')
        media = PostMedia.objects.get(post_id=response.data['id'])
        self.client.delete(f'/api/social/posts/{media.post_id}/')
        process_post_media(media.pk)
        self.assertFalse(Post.objects.filter(pk=media.post_id, status='published').exists())

    def test_video_variants_are_seekable_and_never_upscaled(self):
        import tempfile
        import subprocess
        from pathlib import Path
        from apps.social.application.post_media import convert_video, probe_video
        root = Path(post_private_storage.location)
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            source = Path(folder)/'source.mp4'
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24',
                '-t', '1', '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p', str(source)], check=True, timeout=30)
            variants, width, height, duration = convert_video(source, Path(folder))
            self.assertEqual((width, height), (320, 180))
            for quality in ('720p', 'original'):
                path = Path(post_private_storage.path(variants[quality]))
                _, video = probe_video(path)
                self.assertLessEqual(video['width'], width)
                self.assertLessEqual(video['height'], height)
                self.assertEqual(video['codec_name'], 'h264')
                raw = path.read_bytes()
                self.assertLess(raw.index(b'moov'), raw.index(b'mdat'))

    def test_feed_cursor_has_no_duplicates_or_empty_second_page(self):
        for index in range(45):
            Post.objects.create(author=self.reader, text=str(index))
        seen = []
        cursor = None
        for _ in range(3):
            params = {'page_size': 20}
            if cursor:
                params['cursor'] = cursor
            response = self.client.get('/api/social/feed/weighted/', params)
            self.assertEqual(response.status_code, 200, response.data)
            seen.extend(row['id'] for row in response.data['results'])
            cursor = response.data['next_cursor']
        self.assertEqual(len(seen), 45)
        self.assertEqual(len(set(seen)), 45)

    def test_ranked_cursor_keeps_order_when_reactions_change(self):
        posts = [Post.objects.create(author=self.reader, text=str(index), likes_count=index) for index in range(9)]
        first = self.client.get('/api/social/feed/top/', {'page_size': 4}).data
        Post.objects.filter(pk=posts[0].pk).update(likes_count=1000)
        second = self.client.get('/api/social/feed/top/', {'page_size': 4, 'cursor': first['next_cursor']}).data
        third = self.client.get('/api/social/feed/top/', {'page_size': 4, 'cursor': second['next_cursor']}).data
        ids = [row['id'] for page in (first, second, third) for row in page['results']]
        self.assertEqual(ids, [str(post.pk) for post in reversed(posts)])

    def test_private_post_is_not_available_in_favorites_or_report(self):
        from django.contrib.contenttypes.models import ContentType
        from apps.social.infrastructure.models.social import Favorite
        post = Post.objects.create(author=self.reader, text='private', visibility='private')
        content_type = ContentType.objects.get_for_model(Post)
        Favorite.objects.create(user=self.owner, content_type=content_type, object_id=post.pk)
        response = self.client.get('/api/social/favorites/')
        rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
        self.assertEqual([], list(rows))
        self.assertEqual(403, self.client.post('/api/social/favorites/', {'content_type': 'post', 'object_id': str(post.pk)}, format='json').status_code)
        self.assertEqual(404, self.client.post('/api/social/reports/', {'content_type': 'post', 'content_id': str(post.pk)}, format='json').status_code)

    def test_playlist_card_preserves_leading_zero_id_and_legacy_attachment(self):
        from apps.playlists.infrastructure.models.playlists import Playlist, PlaylistItem
        playlist = Playlist.objects.create(id='01234567', user=self.owner, title='Leading zero', visibility='public')
        anime = self.anime('playlist-preview')
        PlaylistItem.objects.bulk_create([PlaylistItem(playlist=playlist, anime=anime, position=0)])
        response = self.client.post('/api/social/posts/', {'playlist_ids': [1234567]}, format='json')
        self.assertEqual(201, response.status_code, response.data)
        self.assertEqual('01234567', response.data['playlist']['id'])
        self.assertEqual('01234567', response.data['attachments_data'][0]['playlist_data']['id'])
        self.assertEqual(anime.pk, response.data['attachments_data'][0]['playlist_data']['anime'][0]['id'])
        response = self.client.get('/api/social/feed/extended/')
        post = next(row for row in response.data['results'] if row['id'] == str(Post.objects.get(playlist=playlist).pk))
        self.assertEqual('01234567', post['attachments_data'][0]['playlist_data']['id'])
        self.assertEqual(1, len(post['attachments_data'][0]['playlist_data']['anime']))

    def test_account_deletion_does_not_recreate_recommendation_snapshot(self):
        from apps.anime.infrastructure.models.read_models import RecommendationSnapshot
        UserLibrary.objects.create(user=self.reader, anime=self.anime('delete-user'), status='completed')
        self.assertTrue(RecommendationSnapshot.objects.filter(user=self.reader).exists())
        self.reader.delete()
        self.assertFalse(RecommendationSnapshot.objects.filter(key=f'user:{self.reader.pk}').exists())

    def test_quarantined_file_can_be_validated_and_restored(self):
        import json
        from pathlib import Path
        from django.core.management import call_command
        from django.core.management.base import CommandError
        from apps.social.application.post_file_gc import remove_verified
        path = Path(post_private_storage.location) / 'restore-test' / 'image.png'
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(self.image())
        entry = remove_verified('restore-test/image.png')
        quarantine_id = Path(entry['quarantine']).parts[1]
        call_command('restore_post_files', quarantine_id=quarantine_id)
        self.assertFalse(path.exists())
        call_command('restore_post_files', quarantine_id=quarantine_id, apply=True)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])
        with self.assertRaises(CommandError): call_command('restore_post_files', quarantine_id=quarantine_id, apply=True)

    def test_multipart_attachment_lists_and_removal_are_validated(self):
        import json
        first, second = self.anime('multi-first'), self.anime('multi-second')
        response = self.client.post('/api/social/posts/', {'text': 'Original #old',
            'anime_ids': json.dumps([first.pk, second.pk]), 'anime_ratings': '[9,8]',
            'client_post_id': 'multipart-attachments'}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        pk = response.data['id']
        post = Post.objects.get(pk=pk)
        self.assertEqual(post.attachments.count(), 2)
        self.assertEqual(post.anime_id, first.pk)
        response = self.client.patch(f'/api/social/posts/{pk}/', {'text': 'Changed #new',
            'anime_ids': json.dumps([second.pk]), 'anime_ratings': '[10]',
            'playlist_ids': '[]', 'version': 1, 'client_edit_id': 'multipart-edit'}, format='multipart')
        self.assertEqual(response.status_code, 200, response.data)
        post.refresh_from_db()
        self.assertEqual(post.anime_id, second.pk)
        self.assertEqual(post.anime_rating, 10)
        self.assertEqual(post.attachments.count(), 1)
        self.assertEqual(list(post.hashtag_links.values_list('hashtag__name', flat=True)), ['new'])
        response = self.client.patch(f'/api/social/posts/{pk}/', {'text': '', 'anime_ids': '[]', 'version': 2}, format='multipart')
        self.assertEqual(response.status_code, 400, response.data)
        post.refresh_from_db()
        self.assertEqual(post.anime_id, second.pk)
        response = self.client.patch(f'/api/social/posts/{pk}/', {'anime_ids': '[]', 'version': 2}, format='multipart')
        self.assertEqual(response.status_code, 200, response.data)
        post.refresh_from_db()
        self.assertIsNone(post.anime_id)
        self.assertEqual(post.attachments.count(), 0)

    def test_legacy_upload_persists_full_offset(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        response = self.client.post('/api/social/posts/', {'text': 'Photo',
            'media_0': SimpleUploadedFile('legacy.png', self.image(), content_type='image/png')}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        upload = PostMedia.objects.get(post_id=response.data['id']).upload
        self.assertEqual(upload.offset, upload.expected_size)

    def test_profile_group_and_hashtag_lists_filter_visibility(self):
        from apps.social.infrastructure.models.social import Group, Hashtag, PostHashtag
        group = Group.objects.create(creator=self.owner, name='Secret', is_private=True)
        private = Post.objects.create(author=self.owner, text='Private', visibility='private')
        grouped = Post.objects.create(author=self.owner, text='Group', group=group)
        public = Post.objects.create(author=self.owner, text='Public')
        tag = Hashtag.objects.create(name='privacy-list')
        for post in (private, grouped, public): PostHashtag.objects.create(post=post, hashtag=tag)
        self.client.force_authenticate(self.reader)
        for path in (f'/api/social/users/{self.owner.pk}/posts/', '/api/social/hashtags/privacy-list/', '/api/social/users/me/feed/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual([row['id'] for row in response.data['results']], [str(public.pk)])
        self.assertEqual(self.client.get(f'/api/social/groups/{group.pk}/posts/').status_code, 403)
        self.client.force_authenticate(None)
        response = self.client.get(f'/api/social/users/{self.owner.pk}/posts/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([row['id'] for row in response.data['results']], [str(public.pk)])

    def test_post_public_id_and_old_urls_resolve_to_same_post(self):
        post = Post.objects.create(author=self.owner, text='URL')
        for value in (post.pk, post.public_id):
            response = self.client.get(f'/api/social/posts/{value}/')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data['id'], str(post.pk))
            comment = self.client.post(f'/api/social/posts/{value}/comments/', {'content': 'Reply'}, format='json')
            self.assertEqual(comment.status_code, 201, comment.data)
        response = self.client.patch(f'/api/social/posts/{post.public_id}/', {'text': 'Updated', 'version': 1}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        post.refresh_from_db(); self.assertEqual(post.text, 'Updated')
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.post(f'/api/social/posts/{post.public_id}/like/', {'active': True}, format='json').status_code, 200)

    def test_delayed_cleanup_keeps_shared_files_and_quarantines_unshared(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.social.application.post_file_gc import gc_post_files
        from apps.social.infrastructure.models.post_lifecycle import PostFileCleanup
        post = Post.objects.create(author=self.owner, text='File')
        shared = Post.objects.create(author=self.owner, text='Shared')
        upload_id = self.upload()
        upload = PostUpload.objects.get(pk=upload_id)
        media = PostMedia.objects.create(post=post, upload=upload, file=upload.original_path, is_active=False)
        other = PostMedia.objects.create(post=shared, file=upload.original_path)
        job = PostFileCleanup.objects.create(media=media, not_before=timezone.now()-timedelta(seconds=1))
        gc_post_files()
        self.assertTrue(post_private_storage.exists(upload.original_path))
        job.refresh_from_db(); self.assertEqual(job.state, 'complete')
        shared.is_deleted = True; shared.save()
        second = PostFileCleanup.objects.create(media=other, not_before=timezone.now()-timedelta(seconds=1))
        gc_post_files()
        self.assertFalse(post_private_storage.exists(upload.original_path))
        second.refresh_from_db(); entry = second.manifest[0]
        self.assertEqual(entry['sha256'], hashlib.sha256(self.image()).hexdigest())
        self.assertTrue(post_private_storage.exists(entry['quarantine']))

    def test_total_size_includes_retained_media_and_boundary(self):
        from apps.social.application.post_media import MAX_BYTES
        post = Post.objects.create(author=self.owner, text='Size')
        media = PostMedia.objects.create(post=post, file_size=MAX_BYTES-1)
        upload_id = self.upload()
        response = self.client.patch(f'/api/social/posts/{post.pk}/', {'media_ids': [upload_id], 'version': 1}, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        post.refresh_from_db(); self.assertEqual(post.version, 1)
        self.assertTrue(post.media_files.get(pk=media.pk).is_active)
        response = self.client.post('/api/social/post-uploads/', {'filename': 'large.mp4', 'size': MAX_BYTES}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        response = self.client.post('/api/social/post-uploads/', {'filename': 'large.mp4', 'size': MAX_BYTES+1}, format='json')
        self.assertEqual(response.status_code, 400, response.data)

    def test_legacy_root_attachment_is_retained_and_counts_toward_limit(self):
        from django.core.files.base import ContentFile
        from apps.social.application.post_media import MAX_BYTES
        post = Post.objects.create(author=self.owner, text='Legacy attachment')
        post.image_file.save('old.png', ContentFile(self.image()))
        response = self.client.get(f'/api/social/posts/{post.pk}/')
        self.assertEqual('legacy:image', response.data['media_files'][0]['id'])
        self.assertEqual(len(self.image()), response.data['media_files'][0]['file_size'])
        with patch('apps.social.application.post_legacy_media.storage.size', return_value=MAX_BYTES):
            response = self.client.patch(f'/api/social/posts/{post.pk}/', {'text': 'Updated', 'media_ids': [self.upload()], 'version': 1}, format='json')
        self.assertEqual(400, response.status_code, response.data)
        self.assertFalse(post.media_files.exists())
        response = self.client.patch(f'/api/social/posts/{post.pk}/', {'text': 'Updated', 'retain_media_ids': ['legacy:image'], 'version': 1}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        post.refresh_from_db()
        self.assertFalse(post.image_file)
        media = post.media_files.get()
        self.assertTrue(media.is_active)
        self.assertTrue(post_private_storage.exists(media.file.name))
        response = self.client.patch(f'/api/social/posts/{post.pk}/', {'text': 'No attachment', 'retain_media_ids': [], 'version': 2}, format='json')
        self.assertEqual(200, response.status_code, response.data)
        media.refresh_from_db()
        self.assertFalse(media.is_active)
        from apps.social.infrastructure.models.post_lifecycle import PostFileCleanup
        self.assertTrue(PostFileCleanup.objects.filter(media=media).exists())
