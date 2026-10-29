import asyncio
import threading
from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import TransactionTestCase

from apps.social.application.conversation_consumer import ConversationConsumer
from apps.social.infrastructure.models.social import PrivateChat
from apps.social.presentation.views import conversation_views
from apps.users.infrastructure.models.users import User


class IndependentConversationTests(TransactionTestCase):
    def test_slow_room_snapshot_does_not_block_another_room(self):
        users = [User.objects.create_user(username=f'independent-{i}', email=f'i-{i}@example.test') for i in range(3)]
        chats = [PrivateChat.objects.create(user1=users[0], user2=user) for user in users[1:]]
        entered, release = threading.Event(), threading.Event()
        original_history = conversation_views.history

        def history(chat, *args, **kwargs):
            if chat.pk == chats[0].pk:
                entered.set()
                if not release.wait(10):
                    raise RuntimeError('Test did not release the blocked room')
            return original_history(chat, *args, **kwargs)

        async def scenario():
            consumers = []
            for chat in chats:
                consumer = ConversationConsumer()
                consumer.chat, consumer.user, consumer.topic_id = chat, users[0], None
                consumers.append(consumer)
            slow = asyncio.create_task(consumers[0].snapshot())
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait, 3))
                other = await asyncio.wait_for(consumers[1].snapshot(), timeout=3)
                self.assertEqual(('init', chats[1].public_id), (other['action'], other['chat_id']))
                self.assertFalse(release.is_set())
            finally:
                release.set()
                await slow

        with patch.object(conversation_views, 'history', side_effect=history):
            async_to_sync(scenario)()
