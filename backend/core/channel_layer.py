"""Keep blocking receive shorter than the Redis socket deadline."""
from channels_redis.core import RedisChannelLayer
import asyncio
import time


class BoundedRedisChannelLayer(RedisChannelLayer):
    # RedisChannelLayer normally blocks for 5 seconds. A shorter socket timeout
    # must also shorten that blocking read, otherwise idle sockets disconnect.
    brpop_timeout = 0.5

    async def nonempty_groups(self, groups):
        """Batch current membership reads, without caching presence or permissions.

        Empty groups have nobody to receive a Channels event. Like group_send's
        own membership read, this describes one instant; joining afterwards is
        handled by the consumer's snapshot/replay. Nonempty groups still use
        the original group_send, including its expiry and capacity rules.
        """
        if len(groups) > 256:
            raise ValueError('Group lookup batch is too large')
        partitions = {}
        for group in groups:
            self.require_valid_group_name(group)
            partitions.setdefault(self.consistent_hash(group), []).append(group)
        cutoff = f'({int(time.time()) - self.group_expiry}'

        async def lookup(index, names):
            pipe = self.connection(index).pipeline(transaction=False)
            for name in names:
                pipe.zcount(self._group_key(name), cutoff, '+inf')
            return {name for name, count in zip(names, await pipe.execute()) if count}

        live = set()
        for partition in await asyncio.gather(*(lookup(index, names) for index, names in partitions.items())):
            live.update(partition)
        return [group for group in groups if group in live]

    async def renew_groups(self, groups, channel):
        """Refresh existing consumer subscriptions in bounded Redis pipelines."""
        self.require_valid_channel_name(channel)
        partitions = {}
        for group in set(groups):
            self.require_valid_group_name(group)
            partitions.setdefault(self.consistent_hash(group), []).append(group)
        timestamp = time.time()
        async def refresh(index, names):
            connection = self.connection(index)
            for offset in range(0, len(names), 256):
                pipe = connection.pipeline(transaction=False)
                for group in names[offset:offset + 256]:
                    key = self._group_key(group)
                    pipe.zadd(key, {channel:timestamp})
                    pipe.expire(key, self.group_expiry)
                await pipe.execute()
        await asyncio.gather(*(refresh(index, names) for index, names in partitions.items()))
