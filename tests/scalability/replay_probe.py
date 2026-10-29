"""Lab-only functional reconnect/replay, rich replies and duplicate commands.

This deliberately small probe is not a reconnect-storm/capacity test.
"""
import asyncio
import json
from pathlib import Path
import time
import uuid

import aiohttp


async def run():
    base = 'http://frontend'
    paths = [Path('/lab-data/'+name) for name in ('load-users.json', 'load-rooms.json')]
    if any(path.stat().st_size > 16*1024*1024 for path in paths):
        raise RuntimeError('Fixture exceeds bounded memory budget')
    fixture, rooms = [json.loads(path.read_text()) for path in paths]
    if fixture['identity'] != 'scalability-disposable-lab' or rooms['identity'] != fixture['identity']:
        raise RuntimeError('Not disposable fixtures')
    receiver = fixture['users'][0]
    room = rooms['rooms'][str(receiver['user_id'])]
    sender = next(user for user in fixture['users'][1:] if rooms['rooms'][str(user['user_id'])] == room)
    outsider = next(user for user in fixture['users'] if rooms['rooms'][str(user['user_id'])] != room)
    opened = []
    start = time.monotonic()
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        async with session.get(base+'/__lab_identity') as response:
            if response.status != 200 or (await response.json())['identity'] != fixture['identity']:
                raise RuntimeError('Refusing non-isolated target')

        async def connect(user, kind):
            path = '/ws/global/' if kind == 'global' else f'/ws/chat/{room}/?type=group'
            ws = await session.ws_connect(base.replace('http:', 'ws:')+path,
                protocols=('animecore.v2', 'auth.'+user['access']), max_msg_size=1048576)
            opened.append(ws)
            initial = await ws.receive_json(timeout=15) if kind == 'chat' else None
            if initial is not None and initial.get('action') != 'init':
                raise AssertionError('Missing initial snapshot')
            return ws, initial

        async def command(ws, values):
            await ws.send_json(values)
            # Own live events may arrive before ACK. Never buffer without a bound.
            for _ in range(32):
                frame = await ws.receive_json(timeout=15)
                if frame.get('action') == 'error':
                    raise AssertionError('Command was rejected')
                if frame.get('action') == 'message_ack' and frame['message']['client_message_id'] == values['client_message_id']:
                    return frame['message']
            raise AssertionError('ACK frame budget exceeded')

        async def replay(user, cursor):
            async with session.get(f'{base}/api/social/chats/{room}/events/?type=group&after={cursor}',
                    headers={'Authorization': 'Bearer '+user['access']}) as response:
                return response.status, await response.json()

        try:
            global_ws, _ = await connect(receiver, 'global')
            receiver_ws, initial = await connect(receiver, 'chat')
            cursor = initial['event_cursor']
            await receiver_ws.close()
            await global_ws.close()
            sender_ws, _ = await connect(sender, 'chat')
            messages, commands = [], []
            for index in range(5):
                values = {'action': 'send_message', 'text': f'Synthetic offline reply {index} '+('text '*80),
                          'client_message_id': str(uuid.uuid4())}
                if messages:
                    values['reply_to_id'] = messages[0]['id']
                commands.append(values)
                messages.append(await command(sender_ws, values))
                await asyncio.sleep(.15)
            duplicate = await command(sender_ws, commands[-1])
            if duplicate['id'] != messages[-1]['id']:
                raise AssertionError('Duplicate command created a different message')
            await connect(receiver, 'global')
            await connect(receiver, 'chat')
            status, page = await replay(receiver, cursor)
            expected = {message['id'] for message in messages}
            replayed = [event for event in page.get('events', []) if (event.get('message') or {}).get('id') in expected
                        and event['action'] == 'new_message']
            if status != 200 or page.get('has_more') or len(replayed) != 5 or {e['message']['id'] for e in replayed} != expected:
                raise AssertionError('Offline messages did not replay exactly once')
            if any(event['message'].get('reply_text') is None for event in replayed[1:]):
                raise AssertionError('Rich reply projection missing')
            denied, _ = await replay(outsider, cursor)
            if denied not in (403, 404):
                raise AssertionError('Cross-room replay was not denied')
            last = messages[-1]
            headers = {'Authorization': 'Bearer '+sender['access']}
            async with session.post(f"{base}/api/social/messages/{last['id']}/edit/", headers=headers,
                    json={'text': 'Synthetic current edited content', 'version': last['version']}) as response:
                if response.status != 200:
                    raise AssertionError('Edit failed')
            _, edited = await replay(receiver, cursor)
            current = [event['message'] for event in edited['events'] if event['action'] == 'new_message'
                       and (event.get('message') or {}).get('id') == last['id']]
            if len(current) != 1 or current[0]['text'] != 'Synthetic current edited content':
                raise AssertionError('Replay returned stale pre-edit content')
            async with session.post(f"{base}/api/social/messages/{last['id']}/delete/", headers=headers) as response:
                if response.status != 204:
                    raise AssertionError('Delete failed')
            _, deleted = await replay(receiver, cursor)
            if any(event['action'] in ('new_message', 'message_edited') and
                   (event.get('message') or {}).get('id') == last['id'] for event in deleted['events']):
                raise AssertionError('Deleted message leaked through replay')
            print(json.dumps({'profile': 'reconnect-rich-replay', 'capacity_certified': False, 'passed': True,
                'offline_messages': 5, 'rich_replies': 4, 'replayed_unique_messages': len(replayed),
                'duplicate_command_idempotent': True, 'cross_room_replay_denied': True,
                'replay_uses_current_edits_and_deletions': True, 'seconds': time.monotonic()-start,
                'reconnect_storm_tested': False}, indent=2))
            return 0
        finally:
            for ws in opened:
                await ws.close()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(run()))
