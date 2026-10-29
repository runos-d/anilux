"""Keep blocking receive shorter than the Redis socket deadline."""
from channels_redis.core import RedisChannelLayer
import asyncio
import time
import logging
from itertools import islice

logger = logging.getLogger(__name__)

# Same expiry/capacity admission as channels-redis 4.3 group_send. One message
# per process Redis key; __asgi_channel__ routes it through the native receiver.
UNION_SEND_LUA = """
    local over_capacity = 0
    local current_time = ARGV[#ARGV - 1]
    local expiry = ARGV[#ARGV]
    for i=1,#KEYS do
        if redis.call('ZCOUNT', KEYS[i], '-inf', '+inf') < tonumber(ARGV[i + #KEYS]) then
            redis.call('ZADD', KEYS[i], current_time, ARGV[i])
            redis.call('EXPIRE', KEYS[i], expiry)
        else
            over_capacity = over_capacity + 1
        end
    end
    return over_capacity
"""


class BoundedRedisChannelLayer(RedisChannelLayer):
    # RedisChannelLayer normally blocks for 5 seconds. A shorter socket timeout
    # must also shorten that blocking read, otherwise idle sockets disconnect.
    brpop_timeout = 0.5

    async def user_groups_send(self, groups, message):
        """Union bounded *current* user-group members; never cache ACL or DTOs.

        Sending the same event 60 times into one process's Redis queue serializes
        transport receive and fragments fresh-auth batches. Native channel lists
        let that process receive once and dispatch to its own channels normally.
        """
        groups = list(islice(iter(groups), 257))
        if len(groups) > 256:
            raise ValueError('User group batch exceeds 256')
        groups = list(dict.fromkeys(groups))
        partitions = {}
        for group in groups:
            self.require_valid_group_name(group)
            if not group.startswith('user_') or not group[5:].isdigit():
                raise ValueError('Only addressed user groups may be combined')
            partitions.setdefault(self.consistent_hash(group), []).append(group)
        channel_names = set()
        for index, names in partitions.items():
            pipe = self.connection(index).pipeline(transaction=False)
            for group in names:
                key = self._group_key(group)
                pipe.zremrangebyscore(key, 0, int(time.time()) - self.group_expiry)
                # A user has <=10 connections per API; reject abnormal growth
                # before an unbounded membership response can enter Python.
                pipe.zrange(key, 0, 256)
            rows = await pipe.execute()
            for channels in rows[1::2]:
                if len(channels) > 256:
                    raise ValueError('User group exceeds channel budget')
                channel_names.update(channel.decode('utf8') for channel in channels)
            if len(channel_names) > 8192:
                raise ValueError('User group union exceeds channel budget')
        connections, messages, capacities = self._map_channel_keys_to_connection(sorted(channel_names), message)
        for index, keys in connections.items():
            connection = self.connection(index)
            pipe = connection.pipeline(transaction=False)
            for key in keys:
                pipe.zremrangebyscore(key, 0, int(time.time()) - int(self.expiry))
            await pipe.execute()
            args = [messages[key] for key in keys] + [capacities[key] for key in keys] + [time.time(), self.expiry]
            over_capacity = await connection.eval(UNION_SEND_LUA, len(keys), *keys, *args)
            if over_capacity:
                logger.info('%s of %s process queues over capacity in user group union', over_capacity, len(keys))

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
