import asyncio
from unittest.mock import AsyncMock
from asgiref.sync import async_to_sync
from django.test import SimpleTestCase
from core.socket_limits import SocketFrameBudget
from core.asgi_limits import BoundedApplication


class SocketLimitTests(SimpleTestCase):
    def test_utf8_limit_and_command_burst_are_enforced(self):
        now = [0.0]
        frames = SocketFrameBudget(clock=lambda: now[0], maximum_bytes=64, rate=2, burst=3)
        self.assertEqual(frames.reject_code('я' * 33), 1009)
        self.assertEqual(frames.reject_code(None), 1003)
        for _ in range(3):
            self.assertIsNone(frames.reject_code('{}'))
        self.assertEqual(frames.reject_code('{}'), 4008)
        now[0] = 0.5
        self.assertIsNone(frames.reject_code('{}'))

    def test_open_connections_do_not_hold_handshake_slots(self):
        async def run():
            accept, release = asyncio.Event(), asyncio.Event()
            async def app(scope, receive, send):
                await accept.wait()
                await send({'type': 'websocket.accept'})
                await release.wait()
            bounded = BoundedApplication(app, socket_limit=2, handshake_limit=1)
            sent = []
            async def collect(value): sent.append(value)
            first = asyncio.create_task(bounded({'type': 'websocket'}, AsyncMock(), collect))
            await asyncio.sleep(0)
            await bounded({'type': 'websocket'}, AsyncMock(), collect)
            self.assertEqual(sent[-1], {'type': 'websocket.close', 'code': 1013})
            accept.set()
            await asyncio.sleep(0)
            self.assertEqual(bounded.pending_handshakes, 0)
            second = asyncio.create_task(bounded({'type': 'websocket'}, AsyncMock(), collect))
            await asyncio.sleep(0)
            self.assertEqual(bounded.active['websocket'], 2)
            release.set()
            await asyncio.gather(first, second)
            self.assertEqual(bounded.active['websocket'], 0)
        async_to_sync(run)()

    def test_cancelled_handshake_releases_capacity(self):
        async def run():
            async def app(scope, receive, send): await asyncio.Event().wait()
            bounded = BoundedApplication(app, handshake_limit=1)
            task = asyncio.create_task(bounded({'type': 'websocket'}, AsyncMock(), AsyncMock()))
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError): await task
            self.assertEqual(bounded.pending_handshakes, 0)
            self.assertEqual(bounded.active['websocket'], 0)
        async_to_sync(run)()

    def test_group_delivery_uses_one_loop_and_bounded_parallelism(self):
        from core.group_events import send_to_groups
        from types import SimpleNamespace
        async def run():
            running, peak, loops, groups = 0, 0, set(), []
            async def send(group, event):
                nonlocal running, peak
                running += 1; peak = max(peak, running); loops.add(id(asyncio.get_running_loop())); groups.append(group)
                await asyncio.sleep(0)
                running -= 1
            await send_to_groups(SimpleNamespace(group_send=send), (f'user_{i}' for i in range(100)), {})
            self.assertEqual(len(set(groups)), 100)
            self.assertEqual(len(loops), 1)
            self.assertLessEqual(peak, 16)
        async_to_sync(run)()
