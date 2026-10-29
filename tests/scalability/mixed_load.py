"""Bounded authenticated HTTP + durable chat probe, with recipient verification."""
import argparse
import asyncio
import json
from pathlib import Path
import resource
import random
import time
import uuid
from collections import Counter
from itertools import zip_longest
import aiohttp
from http_load import Histogram, AUTH_PATHS


async def run(args):
    base = 'http://frontend'
    sources = [Path('/lab-data/load-users.json'), Path('/lab-data/load-rooms.json')]
    if any(source.stat().st_size > 16 * 1024 * 1024 for source in sources):
        raise RuntimeError('Fixture exceeds lab memory budget')
    fixture, rooms = (json.loads(source.read_text()) for source in sources)
    if fixture['identity'] != 'scalability-disposable-lab' or rooms['identity'] != fixture['identity']:
        raise RuntimeError('Not a disposable fixture')
    grouped = {}
    for user in fixture['users']:
        grouped.setdefault(str(rooms['rooms'][str(user['user_id'])]), []).append(user)
    # Keep inactive receiving rooms connected too, to detect cross-room leaks.
    users = [user for group in zip_longest(*grouped.values()) for user in group if user is not None][:args.users]
    if len(users) != args.users:
        raise RuntimeError('Insufficient synthetic sessions')
    sockets, readers, commands = [], [], {}
    http, delivery, ack, drift = Histogram(), Histogram(), Histogram(), Histogram()
    delivery_by_socket = {'global': Histogram(), 'chat': Histogram()}
    statuses = Counter()
    unexpected = duplicates = frame_errors = offered = dropped = sent = 0
    max_frame_received = 0
    start_cpu = time.process_time()
    heartbeat_at = {}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(limit=args.users*2+32)) as session:
        async with session.get(base+'/__lab_identity') as response:
            if response.status != 200 or (await response.json())['identity'] != fixture['identity']:
                raise RuntimeError('Refusing a non-isolated target')
        async def reader(ws, user, kind, ready):
            nonlocal unexpected, duplicates, frame_errors, max_frame_received
            async for message in ws:
                if message.type != aiohttp.WSMsgType.TEXT:
                    if message.type == aiohttp.WSMsgType.ERROR:
                        frame_errors += 1
                    continue
                max_frame_received = max(max_frame_received, len(message.data.encode()))
                data = json.loads(message.data)
                if data.get('action') == 'init':
                    ready.set()
                if data.get('action') == 'error':
                    frame_errors += 1
                command = commands.get((data.get('message') or {}).get('client_message_id'))
                if not command:
                    continue
                if data.get('action') == 'message_ack' and not command['acked']:
                    command['acked'] = True
                    ack.add(time.monotonic()-command['start'])
                if data.get('action') == 'new_message':
                    key = (user['user_id'], kind)
                    if str(rooms['rooms'][str(user['user_id'])]) != str(command['room']):
                        unexpected += 1
                    elif key in command['received']:
                        duplicates += 1
                    else:
                        command['received'].add(key)
                        delivery.add(time.monotonic()-command['start'])
                        delivery_by_socket[kind].add(time.monotonic()-command['start'])
        async def heartbeat():
            nonlocal frame_errors
            while True:
                now = time.monotonic()
                for ws, deadline in list(heartbeat_at.items()):
                    if now >= deadline and not ws.closed:
                        try:
                            await ws.send_json({'action': 'ping', 'is_active': True})
                        except (aiohttp.ClientError, ConnectionError):
                            frame_errors += 1
                        heartbeat_at[ws] = now + random.uniform(20, 25)
                await asyncio.sleep(1)
        heartbeat_task = asyncio.create_task(heartbeat())
        try:
            for user in users:
                for kind in ('global', 'chat'):
                    room = rooms['rooms'][str(user['user_id'])]
                    path = '/ws/global/' if kind == 'global' else f'/ws/chat/{room}/?type=group'
                    ws = await session.ws_connect(base.replace('http:', 'ws:')+path,
                        protocols=('animecore.v2', 'auth.'+user['access']), max_msg_size=1048576)
                    ready = asyncio.Event()
                    readers.append(asyncio.create_task(reader(ws, user, kind, ready)))
                    sockets.append((user, kind, room, ws))
                    heartbeat_at[ws] = time.monotonic() + random.uniform(20, 25)
                    if kind == 'chat':
                        await asyncio.wait_for(ready.wait(), 15)
                await asyncio.sleep(.025)
            started = time.monotonic()
            load_started_at_unix = time.time()
            pending = set()
            next_http = next_send = 0
            async def request(index, scheduled):
                drift.add(max(0, time.monotonic()-scheduled))
                begin = time.monotonic()
                user = users[index % len(users)]
                try:
                    async with session.get(base+AUTH_PATHS[index % len(AUTH_PATHS)],
                        headers={'Authorization': 'Bearer '+user['access']}) as response:
                        async for block in response.content.iter_chunked(65536):
                            pass
                        statuses[str(response.status)] += 1
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    statuses['network_error'] += 1
                http.add(time.monotonic()-begin)
            while time.monotonic()-started < args.seconds:
                elapsed = time.monotonic()-started
                if next_http < args.rate*args.seconds and elapsed >= next_http/args.rate:
                    offered += 1
                    if len(pending) >= 32:
                        dropped += 1
                    else:
                        task = asyncio.create_task(request(next_http, started+next_http/args.rate))
                        pending.add(task)
                        task.add_done_callback(pending.discard)
                    next_http += 1
                if elapsed >= next_send and len(commands) < 200:
                    user, kind, room, ws = sockets[1]
                    key = str(uuid.uuid4())
                    commands[key] = {'room': room, 'start': time.monotonic(), 'acked': False, 'received': set(),
                        'expected': sum(str(other[2]) == str(room) for other in sockets)}
                    await ws.send_json({'action': 'send_message', 'text': 'Synthetic mixed '+key, 'client_message_id': key})
                    sent += 1
                    next_send += 1  # one durable send/s, explicitly independent of HTTP rate
                await asyncio.sleep(.005)
            if pending:
                await asyncio.gather(*pending)
            deadline = time.monotonic()+10
            while time.monotonic() < deadline and any(not row['acked'] or len(row['received']) < row['expected'] for row in commands.values()):
                await asyncio.sleep(.05)
            expected = sum(row['expected'] for row in commands.values())
            received = sum(len(row['received']) for row in commands.values())
            result = {'schema_version': 1, 'capacity_certified': False, 'profile': 'mixed-chat-http-smoke',
                'users': len(users), 'sockets': len(sockets), 'fixture_room_size': rooms['room_size'],
                'connected_users_per_room': list(Counter(str(rooms['rooms'][str(user['user_id'])]) for user in users).values()),
                'seconds': args.seconds, 'offered_http_rps': args.rate, 'http_expected': args.rate*args.seconds,
                'load_started_at_unix': load_started_at_unix, 'load_finished_at_unix': time.time(),
                'http_offered': offered,
                'http_completed': http.count, 'statuses': dict(statuses), 'generator_dropped': dropped,
                'durable_sends': sent, 'acks': ack.count, 'expected_deliveries': expected, 'unique_deliveries': received,
                'duplicates': duplicates, 'unexpected_recipients': unexpected, 'frame_errors': frame_errors,
                'max_received_frame_bytes': max_frame_received, 'response_frame_budget_bytes': 1048576,
                'http_ms': {'p95': http.percentile(.95), 'p99': http.percentile(.99)},
                'delivery_ms': {'p95': delivery.percentile(.95), 'p99': delivery.percentile(.99)},
                'delivery_by_socket_ms': {kind: {'count': hist.count, 'p95': hist.percentile(.95), 'p99': hist.percentile(.99)}
                                          for kind, hist in delivery_by_socket.items()},
                'generator': {'schedule_delay_p99_ms': drift.percentile(.99),
                              'cpu_seconds': time.process_time()-start_cpu,
                              'max_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
            result['passed_smoke'] = (ack.count == sent and expected == received and not unexpected and not frame_errors
                and offered == args.rate*args.seconds
                and not dropped and statuses.get('200', 0) == offered and (http.percentile(.95) or 60001) <= 1000
                and (delivery.percentile(.95) or 60001) <= 1000 and (drift.percentile(.99) or 0) <= 100)
            print(json.dumps(result, indent=2))
            return 0 if result['passed_smoke'] else 2
        finally:
            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)
            for _, _, _, ws in sockets:
                await ws.close()
            await asyncio.gather(*readers, return_exceptions=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', type=int, default=12)
    parser.add_argument('--seconds', type=int, default=20)
    parser.add_argument('--rate', type=int, default=5)
    args = parser.parse_args()
    if not (2 <= args.users <= 120 and 1 <= args.seconds <= 60 and 1 <= args.rate <= 30):
        parser.error('users 2..120, seconds 1..60 and rate 1..30 required')
    raise SystemExit(asyncio.run(run(args)))
