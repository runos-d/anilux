import time
import os
from unittest import skipUnless

from django.conf import settings
from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import ChatMember, GroupChat, Message, PrivateChat
from apps.social.infrastructure.models.social_chat import ChatBackup
from apps.social.infrastructure.models.conversation import ChatEvent
from . import conversations as service


@skipUnless(getattr(settings, 'CHAT_INTEGRATION_TESTS', False), 'Requires disposable Redis and Celery worker')
class ChatTransportIntegrationTests(TransactionTestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='transport_a', email='transport_a@test.local')
        self.b = User.objects.create_user(username='transport_b', email='transport_b@test.local')
        self.chat = PrivateChat.objects.create(user1=self.a, user2=self.b)

    def test_real_worker_channel_delivery_and_duplicate_job(self):
        from asgiref.sync import async_to_sync
        from channels.db import database_sync_to_async
        from channels.routing import URLRouter
        from channels.testing import WebsocketCommunicator
        from rest_framework_simplejwt.tokens import AccessToken
        from .routing import websocket_urlpatterns
        from .tasks_chat import deliver_chat_event
        token = str(AccessToken.for_user(self.b))

        async def scenario():
            socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.chat.public_id}/?type=private&token={token}')
            self.assertTrue((await socket.connect())[0])
            self.assertEqual('init', (await socket.receive_json_from())['action'])
            message, _ = await database_sync_to_async(service.send_message)(self.chat, self.a,
                {'text': 'real worker', 'client_message_id': 'transport-command'})
            frame = await socket.receive_json_from(timeout=25)
            self.assertEqual(('new_message', message.pk), (frame['action'], frame['message']['id']))
            event = await database_sync_to_async(lambda: ChatEvent.objects.get(kind='new_message', payload__message__id=message.pk))()
            for _ in range(50):
                if await database_sync_to_async(lambda: ChatEvent.objects.filter(pk=event.pk, delivered_at__isnull=False).exists())():
                    break
                import asyncio
                await asyncio.sleep(.1)
            await database_sync_to_async(lambda: deliver_chat_event.delay(event.pk).get(timeout=25))()
            self.assertTrue(await socket.receive_nothing(timeout=.3))
            await socket.disconnect()
        async_to_sync(scenario)()

    def test_backup_file_is_built_by_real_worker_and_can_be_restored(self):
        from django.core.files.base import ContentFile
        from apps.social.infrastructure.models.social import Attachment
        from .chat_backups import restore_backup
        from .tasks import backup_chat_task
        group = GroupChat.objects.create(name='Worker archive', created_by=self.a)
        ChatMember.objects.create(chat=group, user=self.a, is_admin=True)
        message, _ = service.send_message(group, self.a, {'text': 'archive through broker', 'client_message_id': 'worker-archive'})
        attachment = Attachment.objects.create(message=message, type='file', file=ContentFile(b'worker bytes', name='worker.txt'),
            file_name='worker.txt', file_size=12, mime_type='text/plain')
        backup = ChatBackup.objects.create(chat=group, created_by=self.a)
        result = backup_chat_task.delay(backup.pk).get(timeout=30)
        backup.refresh_from_db()
        self.assertEqual('completed', backup.status, (result, backup.error_message))
        self.assertTrue(backup.backup_file.storage.exists(backup.backup_file.name))
        service.change_message(message.pk, self.a, delete=True)
        restore_backup(backup.pk, self.a)
        message.refresh_from_db()
        self.assertFalse(message.is_deleted)
        with attachment.file.open() as file:
            self.assertEqual(b'worker bytes', file.read())

    def test_large_history_returns_bounded_snapshot_and_pages(self):
        size = int(os.environ.get('CHAT_TEST_HISTORY_MESSAGES', '5000'))
        conversation = service.get_conversation(self.chat)
        Message.objects.bulk_create([Message(private_chat=self.chat, conversation=conversation, sender=self.a,
            text=f'History {seq}', seq=seq, public_id=10000000 + seq) for seq in range(1, size + 1)], batch_size=500)
        client = APIClient()
        client.force_authenticate(self.b)
        started = time.perf_counter()
        with CaptureQueriesContext(connection) as queries:
            response = client.get(f'/api/social/chats/{self.chat.public_id}/messages/', {'type': 'private'})
        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual(list(range(size - 49, size + 1)), [m['seq'] for m in response.data['results']])
        self.assertEqual(size - 49, response.data['next_cursor'])
        self.assertTrue(response.data['has_more'])
        self.assertLessEqual(len(queries), 15)
        print(f'CHAT_HISTORY messages={size} SQL={len(queries)} seconds={time.perf_counter()-started:.3f} bytes={len(response.content)}')

    def test_crashed_worker_backup_is_recovered_by_expired_lease(self):
        import subprocess
        import sys
        import tempfile
        import uuid
        from datetime import timedelta
        from django.utils import timezone
        from .chat_backups import read_archive
        from .tasks import backup_chat_task, requeue_pending_chat_backups
        group = GroupChat.objects.create(name='Crash recovery', created_by=self.a)
        ChatMember.objects.create(chat=group, user=self.a, is_admin=True)
        message, _ = service.send_message(group, self.a,
            {'text': 'Preserved across worker crash', 'client_message_id': 'crash-backup'})
        backup = ChatBackup.objects.create(chat=group, created_by=self.a)
        queue = 'chat-crash-' + uuid.uuid4().hex
        code = '''import os, django
django.setup()
from apps.social.application import chat_backups
original = chat_backups.snapshot
def crash(*args, **kwargs):
    original(*args, **kwargs)
    os._exit(17)
chat_backups.snapshot = crash
from config.celery import app
app.worker_main(['worker', '--pool=solo', '-l', 'warning', '-Q', os.environ['CHAT_CRASH_QUEUE'],
                 '--hostname=crash@%h', '--without-gossip', '--without-mingle', '--without-heartbeat'])
'''
        env = dict(os.environ, CHAT_TEST_USE_TEST_DB='1', CHAT_CRASH_QUEUE=queue,
                   DJANGO_SETTINGS_MODULE=settings.SETTINGS_MODULE)
        with tempfile.TemporaryFile() as log:
            worker = subprocess.Popen([sys.executable, '-c', code], env=env, stdout=log, stderr=log)
            try:
                backup_chat_task.apply_async(args=[backup.pk], queue=queue)
                worker.wait(timeout=45)
                log.seek(0)
                self.assertEqual(17, worker.returncode, log.read().decode(errors='replace')[-2000:])
                backup.refresh_from_db()
                self.assertEqual('creating', backup.status)
                self.assertIsNotNone(backup.processing_started_at)
                self.assertFalse(backup.backup_file)
                self.assertTrue(Message.objects.filter(pk=message.pk, is_deleted=False).exists())
                ChatBackup.objects.filter(pk=backup.pk).update(processing_started_at=timezone.now() - timedelta(minutes=7))
                result = requeue_pending_chat_backups.delay().get(timeout=25)
                self.assertEqual(1, result['queued'])
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    backup.refresh_from_db()
                    if backup.status != 'creating':
                        break
                    time.sleep(.1)
                self.assertEqual('completed', backup.status, backup.error_message)
                self.assertEqual(1, ChatBackup.objects.filter(chat=group).count())
                archive, manifest = read_archive(backup)
                archive.close()
                self.assertTrue(any(row['model'] == 'social.message' and row['pk'] == message.pk
                                    for row in manifest['records']))
            finally:
                if worker.poll() is None:
                    worker.terminate()
                    try:
                        worker.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        worker.kill()
                        worker.wait(timeout=5)

    def test_fifty_connections_receive_once_and_revoked_members_are_closed(self):
        clients = int(os.environ.get('CHAT_TEST_FANOUT_CLIENTS', '50'))
        self.assertTrue(clients >= 50 and clients % 10 == 0)
        import asyncio
        from asgiref.sync import async_to_sync
        from channels.db import database_sync_to_async
        from channels.routing import URLRouter
        from channels.testing import WebsocketCommunicator
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.social.infrastructure.models.social_chat import ChatBan
        from .routing import websocket_urlpatterns
        group = GroupChat.objects.create(name='Fanout load', created_by=self.a)
        ChatMember.objects.create(chat=group, user=self.a, is_admin=True)
        viewers = [User.objects.create_user(username=f'fanout_{i}', email=f'fanout_{i}@test.local') for i in range(clients // 10)]
        for user in viewers:
            ChatMember.objects.create(chat=group, user=user)
        tokens = [str(AccessToken.for_user(user)) for user in viewers]

        async def scenario():
            sockets = []
            try:
                for index in range(clients):
                    socket = WebsocketCommunicator(URLRouter(websocket_urlpatterns),
                        f'/ws/chat/{group.public_id}/?type=group&token={tokens[index // 10]}')
                    self.assertTrue((await socket.connect())[0])
                    sockets.append(socket)
                    self.assertEqual('init', (await socket.receive_json_from())['action'])
                started = time.perf_counter()
                first, _ = await database_sync_to_async(service.send_message)(group, self.a,
                    {'text': 'fifty viewers', 'client_message_id': 'fanout-first'})
                async def receive_message(socket, message):
                    for _ in range(20):
                        frame = await socket.receive_json_from(timeout=30)
                        if frame.get('action') == 'new_message' and frame['message']['id'] == message.pk:
                            return
                    self.fail('Expected message did not arrive')
                await asyncio.gather(*(receive_message(socket, first) for socket in sockets))
                self.assertTrue(all(await asyncio.gather(*(socket.receive_nothing(timeout=.1) for socket in sockets))))
                print(f'CHAT_FANOUT clients={clients} seconds={time.perf_counter()-started:.3f}')
                await database_sync_to_async(ChatBan.objects.create)(chat=group, user=viewers[0], banned_by=self.a)
                second, _ = await database_sync_to_async(service.send_message)(group, self.a,
                    {'text': 'after revocation', 'client_message_id': 'fanout-second'})
                closes = await asyncio.gather(*(socket.receive_output(timeout=30) for socket in sockets[:10]))
                self.assertTrue(all(frame['type'] == 'websocket.close' and frame['code'] == 4004 for frame in closes))
                await asyncio.gather(*(receive_message(socket, second) for socket in sockets[10:]))
            finally:
                await asyncio.gather(*(socket.disconnect() for socket in sockets))
        async_to_sync(scenario)()
