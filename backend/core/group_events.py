from itertools import islice
import asyncio


async def send_to_groups(layer, groups, event, batch_size=16):
    """Bound fanout and batch away empty Redis groups in large recipient lists."""
    remaining = iter(groups)
    while candidates := list(islice(remaining, 256)):
        if len(candidates) > batch_size and hasattr(layer, 'nonempty_groups'):
            candidates = await layer.nonempty_groups(candidates)
        for offset in range(0, len(candidates), batch_size):
            batch = candidates[offset:offset + batch_size]
            await asyncio.gather(*(layer.group_send(group, event(group) if callable(event) else event) for group in batch))


async def renew_socket_groups(consumer, groups):
    """Called by serialized, authenticated client heartbeats, never a TTL auth cache."""
    layer = consumer.channel_layer
    now = asyncio.get_running_loop().time()
    interval = min(90, max(1, getattr(layer, 'group_expiry', 300) / 3))
    previous = getattr(consumer, 'group_refresh_at', None)
    if previous is not None and now - previous < interval:
        return True
    try:
        if hasattr(layer, 'renew_groups'):
            await layer.renew_groups(groups, consumer.channel_name)
        else:
            for group in groups:
                await layer.group_add(group, consumer.channel_name)
    except Exception:
        await consumer.close(code=1013)
        return False
    consumer.group_refresh_at = now
    return True
