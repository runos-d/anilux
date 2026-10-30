"""Read cgroup counters through the local engine, without entering API quotas.

The parent collector bounds this helper's lifetime. No container environment,
addresses, payloads or credentials are exported.
"""
import argparse
import http.client
import json
import os
import re
import socket
import subprocess


def engine_get(endpoint, path):
    if endpoint.startswith('npipe://') and os.name == 'nt':
        pipe = open(endpoint.removeprefix('npipe://').replace('/', '\\'), 'r+b', buffering=0)
        transport = type('Pipe', (), {'makefile': lambda self, *a, **k: pipe})()
        send = pipe.write
    elif endpoint.startswith('unix://'):
        transport = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        transport.settimeout(5)
        transport.connect(endpoint.removeprefix('unix://'))
        send = transport.sendall
        pipe = None
    else:
        raise ValueError('Only local Docker named-pipe / Unix endpoints are allowed')
    try:
        send(f'GET {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n'.encode('ascii'))
        response = http.client.HTTPResponse(transport)
        response.begin()
        if response.status != 200:
            raise ValueError('Docker stats endpoint unavailable')
        body = response.read(4 * 1024 * 1024 + 1)
        if len(body) > 4 * 1024 * 1024:
            raise ValueError('Docker response exceeds collector budget')
        return json.loads(body)
    finally:
        if pipe:
            pipe.close()
        else:
            transport.close()


def collect(endpoint, ids):
    result = []
    for identifier in ids:
        if not re.fullmatch('[a-f0-9]{12,64}', identifier):
            raise ValueError('Expected a container ID')
        info = engine_get(endpoint, f'/containers/{identifier}/json')
        labels = info.get('Config', {}).get('Labels', {})
        if labels.get('com.docker.compose.project') != 'animecore-scalability-lab':
            raise ValueError('Only the isolated lab is allowed')
        if labels.get('com.docker.compose.service') != 'api':
            continue
        stats = engine_get(endpoint, f'/containers/{identifier}/stats?stream=false&one-shot=true')
        cpu = stats.get('cpu_stats', {})
        result.append({'container_id': identifier, 'name': info['Name'], 'read': stats.get('read'),
            'cpu_usage_ns': cpu.get('cpu_usage', {}).get('total_usage'),
            'system_cpu_usage_ns': cpu.get('system_cpu_usage'),
            'online_cpus': cpu.get('online_cpus'), 'throttling': cpu.get('throttling_data', {}),
            'memory_usage_bytes': stats.get('memory_stats', {}).get('usage'),
            'pids': stats.get('pids_stats', {}).get('current')})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ids', nargs='+')
    args = parser.parse_args()
    endpoint = subprocess.run(['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
        check=True, capture_output=True, text=True, timeout=5).stdout.strip()
    print(json.dumps(collect(endpoint, args.ids)))
