import asyncio
import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from asgiref.sync import async_to_sync
from django.conf import settings
from django.test import SimpleTestCase

from core.channel_layer import BoundedRedisChannelLayer
from core.group_events import send_to_groups, renew_socket_groups


class GroupFanoutTests(SimpleTestCase):
    def test_large_recipient_list_skips_empty_groups_with_bounded_concurrency(self):
        async def scenario():
            delivered, pending, peak = {}, 0, 0
            async def live(names):
                self.assertLessEqual(len(names), 256)
                return [name for name in names if int(name[5:]) % 10 == 0]
            async def send(name, frame):
                nonlocal pending, peak
                pending += 1
                peak = max(peak, pending)
                await asyncio.sleep(0)
                delivered[name] = frame
                pending -= 1
            layer = SimpleNamespace(nonempty_groups=AsyncMock(side_effect=live), group_send=send)
            await send_to_groups(layer, (f'user_{i}' for i in range(2000)), lambda name: {'recipient': name})
            self.assertEqual(200, len(delivered))
            self.assertLessEqual(peak, 16)
            self.assertEqual(8, layer.nonempty_groups.await_count)
            self.assertTrue(all(frame == {'recipient': name} for name, frame in delivered.items()))
        async_to_sync(scenario)()

    def test_generic_layer_and_failed_membership_lookup_preserve_delivery_rules(self):
        async def scenario():
            layer = SimpleNamespace(group_send=AsyncMock())
            await send_to_groups(layer, (f'group_{i}' for i in range(40)), {'type':'test.event'})
            self.assertEqual(layer.group_send.await_count, 40)
            layer.nonempty_groups = AsyncMock(side_effect=RuntimeError('Redis unavailable'))
            layer.group_send.reset_mock()
            with self.assertRaises(RuntimeError):
                await send_to_groups(layer, (f'group_{i}' for i in range(40)), {})
            layer.group_send.assert_not_awaited()
        async_to_sync(scenario)()

    def test_real_redis_delivers_live_groups_and_ignores_expired_members(self):
        async def scenario():
            host = {'host': settings.REDIS_HOST, 'port': settings.REDIS_PORT, 'db': settings.REDIS_DB}
            if settings.REDIS_PASSWORD:
                host['password'] = settings.REDIS_PASSWORD
            layer = BoundedRedisChannelLayer(hosts=[host], prefix=f'fanout-test-{uuid.uuid4().hex}')
            try:
                first, second = await layer.new_channel(), await layer.new_channel()
                await layer.group_add('live_first', first)
                await layer.group_add('live_second', second)
                connection = layer.connection(layer.consistent_hash('expired'))
                key = layer._group_key('expired')
                await connection.zadd(key, {first: int(time.time()) - layer.group_expiry - 1})
                await connection.expire(key, 60)
                groups = ['live_first', 'live_second', 'expired', *(f'empty_{i}' for i in range(250))]
                self.assertEqual(['live_first', 'live_second'], await layer.nonempty_groups(groups))
                await send_to_groups(layer, groups, lambda name: {'type':'test.event', 'recipient':name})
                self.assertEqual('live_first', (await asyncio.wait_for(layer.receive(first), 3))['recipient'])
                self.assertEqual('live_second', (await asyncio.wait_for(layer.receive(second), 3))['recipient'])
                await layer.renew_groups(['expired'], first)
                self.assertEqual(['expired'], await layer.nonempty_groups(['expired']))
                await layer.group_send('expired', {'type':'test.event','recipient':'renewed'})
                self.assertEqual('renewed', (await asyncio.wait_for(layer.receive(first), 3))['recipient'])
            finally:
                await layer.flush()
                await layer.close_pools()
        async_to_sync(scenario)()

    def test_heartbeats_refresh_current_subscriptions_without_refreshing_on_every_frame(self):
        async def scenario():
            layer = SimpleNamespace(group_expiry=300, renew_groups=AsyncMock())
            consumer = SimpleNamespace(channel_layer=layer, channel_name='socket', close=AsyncMock())
            self.assertTrue(await renew_socket_groups(consumer, {'user_1', 'old_subscription'}))
            self.assertTrue(await renew_socket_groups(consumer, {'user_1'}))
            self.assertEqual(layer.renew_groups.await_count, 1)
            consumer.group_refresh_at -= 100
            self.assertTrue(await renew_socket_groups(consumer, {'user_1', 'new_subscription'}))
            self.assertEqual(layer.renew_groups.await_count, 2)
            self.assertEqual(layer.renew_groups.await_args.args, ({'user_1', 'new_subscription'}, 'socket'))
            consumer.close.assert_not_awaited()
        async_to_sync(scenario)()

    def test_failed_group_renewal_requires_reconnect(self):
        async def scenario():
            layer = SimpleNamespace(group_expiry=300, renew_groups=AsyncMock(side_effect=RuntimeError('Redis unavailable')))
            consumer = SimpleNamespace(channel_layer=layer, channel_name='socket', close=AsyncMock())
            self.assertFalse(await renew_socket_groups(consumer, {'user_1'}))
            consumer.close.assert_awaited_once_with(code=1013)
            self.assertFalse(hasattr(consumer, 'group_refresh_at'))
        async_to_sync(scenario)()
