"""Real Redis native receive/capacity tests, only on the isolated lab endpoint."""
import asyncio
import os
import time
import uuid
from unittest import IsolatedAsyncioTestCase, skipUnless

from core.channel_layer import BoundedRedisChannelLayer
from core.group_events import send_to_users


@skipUnless(os.environ.get('SCALABILITY_REDIS_TESTS') == 'true', 'Requires isolated lab Redis')
class UserMulticastTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # No endpoint override and no flush: never touch a user's Redis keys.
        prefix = 'multicast-test-' + uuid.uuid4().hex
        self.layers = [BoundedRedisChannelLayer(hosts=[('lab-realtime', 6379)], prefix=prefix,
                       capacity=1, expiry=2, group_expiry=2) for _ in range(3)]

    async def asyncTearDown(self):
        for layer in self.layers:
            await layer.close_pools()

    async def test_union_delivers_once_per_native_channel_and_only_current_members(self):
        sender, node1, node2 = self.layers
        a, b = await node1.new_channel(), await node1.new_channel()
        c, outsider = await node2.new_channel(), await node2.new_channel()
        for group, channel in [('user_1', a), ('user_1', c), ('user_2', b), ('user_2', a), ('user_3', outsider)]:
            await sender.group_add(group, channel)
        await sender.connection(0).zadd(sender._group_key('user_3'), {outsider: time.time()-10})
        event = {'type': 'conversation_event', 'payload': {'action': 'new_message', 'event_id': 7}}
        await send_to_users(sender, [1, 2, 3], event)
        # One Redis frame for each API process, despite overlapping groups.
        for node, channel in ((node1, a), (node2, c)):
            self.assertEqual(await sender.connection(0).zcard(sender.prefix+node.non_local_name(channel)), 1)
        for node, channel in ((node1, a), (node1, b), (node2, c)):
            received = await asyncio.wait_for(node.receive(channel), 1)
            self.assertEqual(received, {**event, 'recipients': [1, 2, 3]})
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(node2.receive(outsider), .1)

    async def test_native_process_capacity_and_message_expiry_are_preserved(self):
        sender, node, _ = self.layers
        channel = await node.new_channel()
        await sender.group_add('user_1', channel)
        await sender.user_groups_send(['user_1'], {'type': 'test', 'value': 1})
        await sender.user_groups_send(['user_1'], {'type': 'test', 'value': 2})
        self.assertEqual((await asyncio.wait_for(node.receive(channel), 1))['value'], 1)
        key = sender.prefix+node.non_local_name(channel)
        # An expired message must not consume capacity for the next send.
        await sender.connection(0).zadd(key, {b'old-frame': time.time()-10})
        await sender.user_groups_send(['user_1'], {'type': 'test', 'value': 3})
        self.assertEqual((await asyncio.wait_for(node.receive(channel), 1))['value'], 3)

    async def test_bounded_user_only_interface_rejects_invalid_and_oversized_groups(self):
        sender = self.layers[0]
        for groups in (['conversation_1'], ['user_secret'], [f'user_{i}' for i in range(257)]):
            with self.assertRaises(ValueError):
                await sender.user_groups_send(groups, {'type': 'test'})
        await sender.connection(0).zadd(sender._group_key('user_1'),
            {f'specific.bounded!{i}': time.time() for i in range(257)})
        with self.assertRaisesRegex(ValueError, 'channel budget'):
            await sender.user_groups_send(['user_1'], {'type': 'test'})
