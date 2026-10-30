"""Collect reproducible lab evidence, preserving failed results and resource samples."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def command(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=30, check=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=('public-http-smoke', 'authenticated-http-smoke', 'mixed-chat-http-smoke', 'reconnect-rich-replay'), required=True)
    parser.add_argument('--rate', type=int, default=5)
    parser.add_argument('--seconds', type=int, default=20)
    parser.add_argument('--users', type=int, default=12)
    parser.add_argument('--soak', action='store_true')
    args = parser.parse_args()
    if args.soak and args.profile != 'mixed-chat-http-smoke':
        parser.error('--soak is only supported by the bounded mixed probe')
    if not (1 <= args.rate <= 30 and 1 <= args.seconds <= (1800 if args.soak else 60) and 2 <= args.users <= 120):
        parser.error('Probe bounds: rate 1..30, seconds 1..60 (1800 with --soak), users 2..120')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT / '.tmp' / 'scalability' / f'{stamp}-{args.profile}'
    folder.mkdir(parents=True)
    ids = command(['docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project=animecore-scalability-lab']).splitlines()
    if not ids:
        raise RuntimeError('Start the isolated lab first')
    images = json.loads(command(['docker', 'inspect', *ids]))
    tracked_sources = set(command(['git', 'ls-files', '-z']).split('\0'))
    observer_compose = ['docker', 'compose', '--env-file', '.env.example', '-f', 'deploy/scalability/compose.yml']
    if any(item['Config']['Labels'].get('com.docker.compose.service') == 'rabbitmq' for item in images):
        observer_compose += ['-f', 'deploy/scalability/compose.queues.yml', '-f', 'deploy/scalability/compose.rabbitmq.yml']
    command([*observer_compose, 'up', '-d', '--no-deps', '--wait', 'observer'])
    ids = command(['docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project=animecore-scalability-lab']).splitlines()
    images = json.loads(command(['docker', 'inspect', *ids]))
    # Deliberately retain only image identities/resource limits, never Config.Env.
    metadata = {'schema_version': 1, 'capacity_certified': False, 'started_at': stamp,
        'git_sha': command(['git', 'rev-parse', 'HEAD']),
        'tracked_diff_sha256': hashlib.sha256(command(['git', 'diff', 'HEAD']).encode()).hexdigest(),
        'dirty': bool(command(['git', 'status', '--porcelain'])),
        'profile_settings': vars(args),
        'generator_image_id': command(['docker', 'image', 'inspect', 'animecore-scalability-backend:lab', '--format', '{{.Id}}']),
        'source_files_sha256': {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for pattern in ('tests/scalability/*.py', 'backend/**/*.py',
                            'deploy/scalability/*.yml') for path in ROOT.glob(pattern)
            if path.relative_to(ROOT).as_posix() in tracked_sources},
        'docker_host_cpu_memory': command(['docker', 'info', '--format', '{{.NCPU}} {{.MemTotal}}']),
        'shared_host_generator': True,
        'containers': [{'name': item['Name'], 'image_id': item['Image'],
            'memory_limit_bytes': item['HostConfig']['Memory'], 'nano_cpus': item['HostConfig']['NanoCpus'],
            'compose_files': [Path(path).name for path in
                item['Config']['Labels'].get('com.docker.compose.project.config_files', '').split(',') if path],
            'service': item['Config']['Labels'].get('com.docker.compose.service')}
            for item in images]}
    (folder/'manifest.json').write_text(json.dumps(metadata, indent=2))
    compose = ['docker', 'compose', '--env-file', '.env.example', '-f', 'deploy/scalability/compose.yml',
               'run', '--rm', '--no-deps', '--entrypoint', 'python', 'generator']
    if args.profile == 'mixed-chat-http-smoke':
        invocation = [*compose, '/load/mixed_load.py', '--users', str(args.users)]
    elif args.profile == 'reconnect-rich-replay':
        invocation = [*compose, '/load/replay_probe.py']
    else:
        invocation = [*compose, '/load/http_load.py', '--profile', args.profile]
    if args.profile != 'reconnect-rich-replay':
        invocation += ['--rate', str(args.rate), '--seconds', str(args.seconds)]
    if args.soak:
        invocation += ['--soak']
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
                sample['observer'] = json.loads(command(['docker', 'exec',
                    'animecore-scalability-lab-observer-1', 'cat', '/tmp/scalability-observer.json']))
                sample['api_cgroups'] = json.loads(command([sys.executable,
                    'tests/scalability/engine_stats.py', *live]))
            except (subprocess.SubprocessError, ValueError):
                sample['probe_unavailable'] = True
            resources.write(json.dumps(sample)+'\n')
            resources.flush()
            if process.poll() is None:
                time.sleep(2)
        code = process.wait()
    (folder/'completion.json').write_text(json.dumps({'generator_exit_code': code,
        'elapsed_seconds': time.monotonic()-started, 'capacity_certified': False}, indent=2))
    print(json.dumps({'evidence_directory': str(folder), 'generator_exit_code': code,
                      'capacity_certified': False}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
