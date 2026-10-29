"""Real Redis A/B: 2000 addressed groups, 120 with a socket, unique prefix."""
import asyncio
import json
import time
import uuid
from types import SimpleNamespace

import django
django.setup()
from django.conf import settings
from asgiref.sync import async_to_sync
from core.channel_layer import BoundedRedisChannelLayer
from core.group_events import send_to_groups

assert settings.REDIS_HOST == 'audit-redis'


async def run():
    layer = BoundedRedisChannelLayer(hosts=[{'host':'audit-redis','port':6379}],
        prefix=f'fanout-benchmark-{uuid.uuid4().hex}', capacity=1000)
    groups = [f'user_{i}' for i in range(2000)]
    results = []
    try:
        channels = [await layer.new_channel() for _ in range(120)]
        for name, channel in zip(groups, channels):
            await layer.group_add(name, channel)
        for label, target in [('original', SimpleNamespace(group_send=layer.group_send)), ('batched_empty_groups', layer)]:
            durations = []
            for _ in range(3):
                start = time.perf_counter()
                await send_to_groups(target, groups, lambda name: {'type':'test.event','recipient':name})
                durations.append((time.perf_counter() - start) * 1000)
                for name, channel in zip(groups, channels):
                    message = await asyncio.wait_for(layer.receive(channel), 5)
                    assert message['recipient'] == name
            results.append({'mode':label, 'milliseconds':durations, 'verified_recipients_each_round':120})
        return results
    finally:
        await layer.flush()
        await layer.close_pools()


print(json.dumps(async_to_sync(run)()))
