"""Collect reproducible lab evidence, preserving failed results and resource samples."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def command(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=30, check=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=('public-http-smoke', 'authenticated-http-smoke', 'mixed-chat-http-smoke'), required=True)
    parser.add_argument('--rate', type=int, default=5)
    parser.add_argument('--seconds', type=int, default=20)
    parser.add_argument('--users', type=int, default=12)
    args = parser.parse_args()
    if not (1 <= args.rate <= 30 and 1 <= args.seconds <= 60 and 2 <= args.users <= 120):
        parser.error('Probe bounds: rate 1..30, seconds 1..60, users 2..120')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT / '.tmp' / 'scalability' / f'{stamp}-{args.profile}'
    folder.mkdir(parents=True)
    ids = command(['docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project=animecore-scalability-lab']).splitlines()
    if not ids:
        raise RuntimeError('Start the isolated lab first')
    images = json.loads(command(['docker', 'inspect', *ids]))
    # Deliberately retain only image identities/resource limits, never Config.Env.
    metadata = {'schema_version': 1, 'capacity_certified': False, 'started_at': stamp,
        'git_sha': command(['git', 'rev-parse', 'HEAD']),
        'tracked_diff_sha256': hashlib.sha256(command(['git', 'diff', 'HEAD']).encode()).hexdigest(),
        'dirty': bool(command(['git', 'status', '--porcelain'])),
        'profile_settings': vars(args),
        'generator_image_id': command(['docker', 'image', 'inspect', 'animecore-scalability-backend:lab', '--format', '{{.Id}}']),
        'source_files_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for pattern in ('tests/scalability/*.py', 'backend/core/*.py', 'backend/config/*.py',
                            'deploy/scalability/*.yml', 'backend/apps/social/application/live_projection.py',
                            'backend/apps/social/application/post_feed.py', 'backend/apps/social/application/tasks_chat.py',
                            'backend/apps/anime/application/recommendations.py') for path in ROOT.glob(pattern)},
        'docker_host_cpu_memory': command(['docker', 'info', '--format', '{{.NCPU}} {{.MemTotal}}']),
        'shared_host_generator': True,
        'containers': [{'name': item['Name'], 'image_id': item['Image'],
            'memory_limit_bytes': item['HostConfig']['Memory'], 'nano_cpus': item['HostConfig']['NanoCpus']}
            for item in images]}
    (folder/'manifest.json').write_text(json.dumps(metadata, indent=2))
    compose = ['docker', 'compose', '--env-file', '.env.example', '-f', 'deploy/scalability/compose.yml',
               'run', '--rm', '--no-deps', '--entrypoint', 'python', 'generator']
    if args.profile == 'mixed-chat-http-smoke':
        invocation = [*compose, '/load/mixed_load.py', '--users', str(args.users)]
    else:
        invocation = [*compose, '/load/http_load.py', '--profile', args.profile]
    invocation += ['--rate', str(args.rate), '--seconds', str(args.seconds)]
    started = time.monotonic()
    with (folder/'result.json').open('w') as out, (folder/'generator.log').open('w') as error, \
            (folder/'resources.jsonl').open('w') as resources:
        process = subprocess.Popen(invocation, cwd=ROOT, stdout=out, stderr=error)
        while process.poll() is None:
            sample = {'elapsed_seconds': time.monotonic()-started}
            try:
                # Generator containers are ephemeral and don't exist in the
                # pre-run inventory, so refresh IDs each time.
                live = command(['docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project=animecore-scalability-lab']).splitlines()
                sample['docker_stats'] = [json.loads(line) for line in command(
                    ['docker', 'stats', '--no-stream', '--format', '{{json .}}', *live]).splitlines()]
                sample['database_outbox'] = json.loads(command(['docker', 'exec',
                    'animecore-scalability-lab-api-1', 'python', 'manage.py', 'scalability_snapshot']))
                sample['broker_queues'] = json.loads(command(['docker', 'exec', 'animecore-scalability-lab-api-1',
                    'python', '-c', "import json,requests; r=requests.get('http://rabbitmq:15672/api/queues/lab',auth=('lab','disposable-lab'),timeout=2); r.raise_for_status(); print(json.dumps([{k:q.get(k) for k in ('name','messages_ready','messages_unacknowledged')} for q in r.json()]))"]))
            except (subprocess.SubprocessError, ValueError):
                sample['probe_unavailable'] = True
            resources.write(json.dumps(sample)+'\n')
            resources.flush()
            if process.poll() is None:
                time.sleep(2)
        code = process.wait()
    print(json.dumps({'evidence_directory': str(folder), 'generator_exit_code': code,
                      'capacity_certified': False}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
