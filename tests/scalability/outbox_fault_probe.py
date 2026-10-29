"""Pause only the labelled lab broker, preserve SQL, resume and verify recovery."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

from replica_probe import ROOT, command, container


def main():
    broker = container('rabbitmq')
    # Consumers must already be running before this producer is allowed.
    container('events')
    folder = ROOT/'.tmp'/'scalability'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-outbox-fault')
    folder.mkdir(parents=True)
    compose = ['docker', 'compose', '--env-file', '.env.example', '-f', 'deploy/scalability/compose.yml',
        '-f', 'deploy/scalability/compose.queues.yml', '-f', 'deploy/scalability/compose.rabbitmq.yml',
        'run', '--rm', '--no-deps', '-v', str(ROOT/'tests'/'scalability')+':/load:ro',
        'migrate', 'python', '/load/broker_probe.py']

    def phase(*args):
        started = time.monotonic()
        process = subprocess.run([*compose, *args], cwd=ROOT, capture_output=True, text=True, timeout=45)
        # Operational diagnostics stay local; published output is structured.
        (folder/(args[0]+'.log')).write_text(process.stdout+process.stderr)
        process.check_returncode()
        rows = [json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
        return rows[-1], time.monotonic()-started

    command(['docker', 'pause', broker])
    try:
        produced, publish_seconds = phase('produce')
    finally:
        # Even a timeout/failed assertion must not leave the broker paused.
        command(['docker', 'unpause', broker])
    if not produced.get('message_saved') or not produced.get('pending_at_observation'):
        raise RuntimeError('SQL/outbox did not remain pending during the paused broker')
    recovered, recover_seconds = phase('recover', '--event-id', str(int(produced['event_id'])))
    if not recovered.get('outbox_published') or not recovered.get('duplicate_task_completed'):
        raise RuntimeError('Outbox recovery/duplicate task failed')
    result = {'passed': True, 'capacity_certified': False, 'client_delivery_verified': False,
        'sql_saved_while_broker_paused': True, 'outbox_recovered': True, 'duplicate_task_safe': True,
        'producer_cli_seconds': publish_seconds, 'recovery_cli_seconds': recover_seconds,
        'source_commit': command(['git', 'rev-parse', 'HEAD']).decode().strip()}
    (folder/'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'evidence_directory': str(folder), **result}, indent=2))


if __name__ == '__main__':
    main()
