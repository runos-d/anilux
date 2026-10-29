"""Open-loop, bounded HTTP lab generator; no credentials, unbounded samples or retries."""
import argparse
import asyncio
from collections import Counter
import json
import math
import resource
import time
from pathlib import Path

import aiohttp

PATHS = ('/api/anime/?page_size=20', '/api/anime/franchises/?page_size=20',
         '/api/anime/?search=capacity&page_size=20', '/api/anime/home/')
AUTH_PATHS = (PATHS[0], '/api/social/feed/?page_size=20&include_count=false', PATHS[2],
              '/api/anime/home/personalized/')


class Histogram:
    """1ms buckets to 60s. Memory doesn't grow during a soak."""
    def __init__(self):
        self.counts = Counter()
        self.count = 0

    def add(self, seconds):
        self.counts[min(60000, max(0, math.ceil(seconds * 1000)))] += 1
        self.count += 1

    def percentile(self, p):
        if not self.count:
            return None
        total = 0
        for ms, count in sorted(self.counts.items()):
            total += count
            if total >= math.ceil(self.count * p):
                return ms


async def run(args):
    if args.base != 'http://frontend':
        raise RuntimeError('Only the disposable frontend in the isolated Compose network is accepted')
    users = []
    if args.profile == 'authenticated-http-smoke':
        source = Path('/lab-data/load-users.json')
        if source.stat().st_size > 16 * 1024 * 1024:
            raise RuntimeError('Credential fixture exceeds lab budget')
        fixture = json.loads(source.read_text())
        if fixture.get('identity') != 'scalability-disposable-lab' or not 1 <= len(fixture['users']) <= 10000:
            raise RuntimeError('Invalid disposable credentials')
        users = fixture['users']
    paths = AUTH_PATHS if users else PATHS
    connector = aiohttp.TCPConnector(limit=args.concurrency)
    async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.get(args.base + '/__lab_identity') as response:
            if response.status != 200 or (await response.json()).get('identity') != 'scalability-disposable-lab':
                raise RuntimeError('Refusing a target without disposable identity')
        durations, drift = Histogram(), Histogram()
        statuses, pending = Counter(), set()
        routes = {index: {'latency': Histogram(), 'statuses': Counter()} for index in range(len(paths))}
        bytes_received = 0
        offered = dropped = 0
        start_cpu, start = time.process_time(), time.monotonic()

        async def request(index, scheduled):
            nonlocal bytes_received
            drift.add(time.monotonic() - scheduled)
            begin = time.monotonic()
            try:
                headers = {'Authorization': 'Bearer ' + users[index % len(users)]['access']} if users else {}
                async with session.get(args.base + paths[index % len(paths)], headers=headers) as response:
                    # Drain bounded chunks, never buffer entire responses in the load process.
                    async for block in response.content.iter_chunked(65536):
                        bytes_received += len(block)
                    statuses[str(response.status)] += 1
                    routes[index % len(paths)]['statuses'][str(response.status)] += 1
            except (aiohttp.ClientError, asyncio.TimeoutError):
                statuses['network_error'] += 1
                routes[index % len(paths)]['statuses']['network_error'] += 1
            durations.add(time.monotonic() - begin)
            routes[index % len(paths)]['latency'].add(time.monotonic() - begin)

        for index in range(args.rate * args.seconds):
            scheduled = start + index / args.rate
            await asyncio.sleep(max(0, scheduled - time.monotonic()))
            offered += 1
            if len(pending) >= args.concurrency:
                dropped += 1
                continue
            task = asyncio.create_task(request(index, scheduled))
            pending.add(task)
            task.add_done_callback(pending.discard)
        if pending:
            await asyncio.gather(*pending)
        await asyncio.sleep(max(0, start + args.seconds - time.monotonic()))
        elapsed = time.monotonic() - start
        errors = sum(count for status, count in statuses.items() if status != '200')
        result = {'schema_version': 1, 'capacity_certified': False, 'profile': args.profile,
                  'rotating_synthetic_identities': len(users),
                  'offered_rps': args.rate, 'seconds': args.seconds, 'offered': offered,
                  'completed': durations.count, 'statuses': dict(statuses), 'dropped_by_generator': dropped,
                  'completed_rps_including_drain': durations.count / elapsed,
                  'latency_ms': {f'p{p}': durations.percentile(p / 100) for p in (50, 95, 99)},
                  'generator': {'concurrency': args.concurrency, 'schedule_delay_p99_ms': drift.percentile(.99),
                                'cpu_seconds': time.process_time() - start_cpu,
                                'max_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
                  'response_bytes': bytes_received, 'elapsed_seconds': elapsed,
                  'routes': {str(index): {'path': paths[index], 'statuses': dict(row['statuses']),
                      'p95_ms': row['latency'].percentile(.95), 'p99_ms': row['latency'].percentile(.99)}
                      for index, row in routes.items()},
                  'passed_smoke': not errors and not dropped and (drift.percentile(.99) or 0) <= 100
                                  and (durations.percentile(.95) or 60001) <= 1000}
        print(json.dumps(result, indent=2))
        return 0 if result['passed_smoke'] else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://frontend')
    parser.add_argument('--profile', choices=('public-http-smoke', 'authenticated-http-smoke'), default='public-http-smoke')
    parser.add_argument('--rate', type=int, default=5)
    parser.add_argument('--seconds', type=int, default=20)
    parser.add_argument('--concurrency', type=int, default=32)
    args = parser.parse_args()
    if not (1 <= args.rate <= 10000 and 1 <= args.seconds <= 86400 and 1 <= args.concurrency <= 2000):
        parser.error('rate/seconds/concurrency outside lab bounds')
    raise SystemExit(asyncio.run(run(args)))
