"""Aggregate observed phase deltas, never infer a cause from a queue snapshot."""
import argparse
import json
from pathlib import Path
import re

METRIC = re.compile(r'^site_ws_phase_seconds_(count|sum|bucket)\{operation="([^"]+)",phase="([^"]+)"(?:,le="([^"]+)")?\} (\S+)$')


def metrics(sample):
    result = {}
    for address, body in sample['observer'].get('api_metrics', {}).items():
        for line in body.splitlines():
            match = METRIC.fullmatch(line)
            if match:
                kind, operation, phase, bound, value = match.groups()
                result[(address, operation, phase, kind, bound)] = float(value)
    return result


def summarize(folder):
    result = json.loads((folder/'result.json').read_text())
    start, end = result['load_started_at_unix'], result['load_finished_at_unix']
    samples = [json.loads(line) for line in (folder/'resources.jsonl').read_text().splitlines()]
    samples = [s for s in samples if start <= s.get('observer', {}).get('captured_at_unix', 0) <= end
               and not s['observer'].get('probe_unavailable')]
    # Observer data may repeat; require two distinct timestamps and stable nodes.
    if len(samples) < 2 or samples[0]['observer']['captured_at_unix'] == samples[-1]['observer']['captured_at_unix']:
        raise ValueError('Insufficient successful samples inside the load stage')
    first, last = metrics(samples[0]), metrics(samples[-1])
    if {k[0] for k in first} != {k[0] for k in last}:
        raise ValueError('API membership changed: compare each generation separately')
    totals = {}
    for key, after in last.items():
        before = first.get(key, 0)
        if after < before:
            raise ValueError('Counter reset: process restarted during measured interval')
        _, operation, phase, kind, bound = key
        row = totals.setdefault((operation, phase), {'count': 0, 'sum': 0, 'buckets': {}})
        if kind == 'bucket':
            row['buckets'][bound] = row['buckets'].get(bound, 0) + after - before
        else:
            row[kind] += after - before
    phases = []
    for (operation, phase), row in sorted(totals.items()):
        if not row['count']:
            continue
        bounds = sorted((float(bound), count) for bound, count in row['buckets'].items())
        def quantile(q):
            bound = next((bound for bound, count in bounds if count >= q*row['count']), float('inf'))
            return bound*1000 if bound != float('inf') else None
        phases.append({'operation': operation, 'phase': phase, 'observations': int(row['count']),
                       'mean_ms': row['sum']/row['count']*1000,
                       'p95_bucket_upper_ms': quantile(.95), 'p99_bucket_upper_ms': quantile(.99)})
    return {'capacity_certified': False, 'phase_intervals_are_nested': True,
            'sampled_seconds': samples[-1]['observer']['captured_at_unix']-samples[0]['observer']['captured_at_unix'],
            'api_replicas': len({key[0] for key in last}), 'phases': phases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.folder), indent=2))
