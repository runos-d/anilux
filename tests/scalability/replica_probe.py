"""Cold-bootstrap an empty lab replica, then rehearse lag/restart recovery.

Never reset/drop an existing schema, promote a writer or change API routing.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
PROJECT = 'animecore-scalability-lab'
COORDINATES = re.compile(rb"CHANGE (?:REPLICATION SOURCE|MASTER) TO (?:SOURCE|MASTER)_LOG_FILE='(lab-bin\.[0-9]+)', (?:SOURCE|MASTER)_LOG_POS=([0-9]+)")
TABLES = ('users_user', 'anime_anime', 'social_post', 'social_message', 'social_chatevent', 'social_chatmember')


def command(args, **options):
    return subprocess.run(args, cwd=ROOT, capture_output=True, check=True, timeout=180, **options).stdout


def container(service):
    ids = command(['docker', 'ps', '-q', '--filter', f'label=com.docker.compose.project={PROJECT}',
                   '--filter', f'label=com.docker.compose.service={service}']).decode().split()
    if len(ids) != 1:
        raise RuntimeError('Expected exactly one isolated '+service)
    # Never save Config.Env, which may contain credentials in other projects.
    labels = json.loads(command(['docker', 'inspect', '--format', '{{json .Config.Labels}}', ids[0]]))
    if labels.get('com.docker.compose.project') != PROJECT or labels.get('com.docker.compose.service') != service:
        raise RuntimeError('Container identity mismatch')
    return ids[0]


def mysql(node, sql):
    return command(['docker', 'exec', '-i', node, 'env', 'MYSQL_PWD=disposable-lab',
        'mysql', '-uroot', '-N', '-B', 'scalability_lab'], input=sql.encode()).decode().strip()


def counts(node):
    return {table: int(mysql(node, f'SELECT COUNT(*) FROM `{table}`')) for table in TABLES}


def checksums(node):
    return {row.split('\t')[0].split('.')[-1]: row.split('\t')[1]
            for row in mysql(node, 'CHECKSUM TABLE '+','.join(f'`{table}`' for table in TABLES)).splitlines()}


def status(node):
    rows = mysql(node, "SELECT SERVICE_STATE FROM performance_schema.replication_connection_status").splitlines()
    appliers = mysql(node, "SELECT SERVICE_STATE,LAST_ERROR_NUMBER FROM performance_schema.replication_applier_status_by_worker").splitlines()
    return {'receiver_on': bool(rows) and all(row == 'ON' for row in rows),
            'appliers_on': bool(appliers) and all(row == 'ON\t0' for row in appliers),
            'super_read_only': mysql(node, 'SELECT @@global.super_read_only') == '1'}


def wait_coordinate(source, replica):
    file, position, *_ = mysql(source, 'SHOW MASTER STATUS').split('\t')
    if not re.fullmatch(r'lab-bin\.[0-9]+', file) or not position.isdigit():
        raise RuntimeError('Unexpected lab binlog coordinates')
    waited = mysql(replica, f"SELECT SOURCE_POS_WAIT('{file}',{position},30)")
    if waited in ('NULL', '-1'):
        raise RuntimeError('Replica did not reach the source checkpoint')


def bootstrap(source, replica, folder):
    if mysql(source, 'SELECT DATABASE(),@@server_id,@@log_bin') != 'scalability_lab\t101\t1':
        raise RuntimeError('Start the lab replication overlay before bootstrap')
    if mysql(replica, 'SELECT DATABASE(),@@server_id') != 'scalability_lab\t102':
        raise RuntimeError('Replica identity mismatch')
    if mysql(replica, "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='scalability_lab'") != '0':
        raise RuntimeError('Replica schema is not empty; refusing to overwrite existing data')
    mysql(source, "CREATE USER IF NOT EXISTS 'lab_replica'@'%' IDENTIFIED BY 'disposable-replication' REQUIRE SSL; "
                  "GRANT REPLICATION SLAVE ON *.* TO 'lab_replica'@'%'")
    dump = folder/'synthetic-source.sql'
    with os.fdopen(os.open(dump, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output:
        subprocess.run(['docker', 'exec', source, 'env', 'MYSQL_PWD=disposable-lab', 'mysqldump', '-uroot',
            '--single-transaction', '--source-data=2', '--set-gtid-purged=OFF', '--no-tablespaces',
            '--skip-add-drop-table', 'scalability_lab'], cwd=ROOT, stdout=output,
            stderr=subprocess.PIPE, check=True, timeout=180)
    # Only read a small header for coordinates; dump stays private/ignored.
    with dump.open('rb') as stream:
        coordinate = COORDINATES.search(stream.read(65536))
    if not coordinate:
        raise RuntimeError('No source checkpoint in synthetic dump')
    with dump.open('rb') as source_file:
        subprocess.run(['docker', 'exec', '-i', replica, 'env', 'MYSQL_PWD=disposable-lab',
            'mysql', '-uroot', 'scalability_lab'], cwd=ROOT, stdin=source_file,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=180)
    file, position = coordinate.group(1).decode(), int(coordinate.group(2))
    mysql(replica, f"CHANGE REPLICATION SOURCE TO SOURCE_HOST='lab-mysql',SOURCE_USER='lab_replica',"
        f"SOURCE_PASSWORD='disposable-replication',SOURCE_LOG_FILE='{file}',SOURCE_LOG_POS={position},SOURCE_SSL=1; "
        'SET PERSIST super_read_only=ON; START REPLICA')
    wait_coordinate(source, replica)
    before, after = counts(source), counts(replica)
    if before != after:
        raise RuntimeError('Replica counts mismatch')
    source_checksums, replica_checksums = checksums(source), checksums(replica)
    if source_checksums != replica_checksums or 'NULL' in source_checksums.values():
        raise RuntimeError('Replica checksums mismatch/unavailable')
    state = status(replica)
    if not all(state.values()):
        raise RuntimeError('Replica threads/read-only state is not healthy')
    digest = hashlib.sha256()
    with dump.open('rb') as stream:
        while block := stream.read(65536):
            digest.update(block)
    return {'bootstrap': True, 'counts_match': True, 'checksums_match': True, 'checksums': source_checksums,
            'counts': before, 'dump_bytes': dump.stat().st_size,
            'dump_sha256': digest.hexdigest(), 'replication': state}


def recover(source, replica):
    if mysql(source, 'SELECT DATABASE(),@@server_id,@@log_bin') != 'scalability_lab\t101\t1':
        raise RuntimeError('Unexpected lab source identity')
    if mysql(replica, 'SELECT DATABASE(),@@server_id') != 'scalability_lab\t102':
        raise RuntimeError('Unexpected lab replica identity')
    if mysql(replica, 'SELECT HOST FROM performance_schema.replication_connection_configuration') != 'lab-mysql':
        raise RuntimeError('Replica is connected to an unexpected source')
    if not status(replica)['super_read_only']:
        raise RuntimeError('Refusing a writable/unprovisioned replica')
    mysql(source, 'CREATE TABLE IF NOT EXISTS scalability_replication_probe '
                  '(id varchar(36) PRIMARY KEY, value integer NOT NULL) ENGINE=InnoDB')
    wait_coordinate(source, replica)
    marker = str(uuid.uuid4())
    started = time.monotonic()
    mysql(replica, 'STOP REPLICA SQL_THREAD')
    try:
        mysql(source, f"INSERT INTO scalability_replication_probe(id,value) VALUES ('{marker}',1)")
        stale = mysql(replica, f"SELECT COUNT(*) FROM scalability_replication_probe WHERE id='{marker}'") == '0'
    finally:
        mysql(replica, 'START REPLICA SQL_THREAD')
    wait_coordinate(source, replica)
    applied = mysql(replica, f"SELECT value FROM scalability_replication_probe WHERE id='{marker}'") == '1'
    if not stale or not applied:
        raise RuntimeError('Paused-applier recovery did not behave as expected')
    try:
        mysql(replica, f"UPDATE scalability_replication_probe SET value=3 WHERE id='{marker}'")
    except subprocess.CalledProcessError as error:
        if b'1290' not in (error.stderr or b''):
            raise
    else:
        raise RuntimeError('Read-only replica unexpectedly accepted an application write')
    # Restart only the replica; skip-replica-start requires an explicit operator step.
    command(['docker', 'restart', replica])
    for _ in range(60):
        try:
            mysql(replica, 'SELECT 1')
            break
        except subprocess.CalledProcessError:
            time.sleep(.5)
    mysql(replica, 'START REPLICA')
    mysql(source, f"UPDATE scalability_replication_probe SET value=2 WHERE id='{marker}'")
    wait_coordinate(source, replica)
    exactly_once = mysql(replica, f"SELECT COUNT(*),MAX(value) FROM scalability_replication_probe WHERE id='{marker}'") == '1\t2'
    state = status(replica)
    if not exactly_once or not all(state.values()):
        raise RuntimeError('Restart recovery or persisted read-only fence failed')
    return {'paused_applier_observed_stale_read': stale, 'caught_up': applied,
            'restart_updates_exactly_once': exactly_once, 'application_write_rejected': True,
            'seconds': time.monotonic()-started,
            'replication': state}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('bootstrap', 'recover'))
    args = parser.parse_args()
    source, replica = container('lab-mysql'), container('lab-replica')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT/'.tmp'/'scalability'/f'{stamp}-replica-{args.phase}'
    folder.mkdir(parents=True)
    # Dumps contain synthetic sessions. They never enter published evidence.
    metadata = {'phase': args.phase, 'source_commit': command(['git', 'rev-parse', 'HEAD']).decode().strip(),
                'dirty': bool(command(['git', 'status', '--porcelain']).strip()),
                'source_hashes': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                    ('tests/scalability/replica_probe.py', 'deploy/scalability/compose.replica.yml')},
                'containers': {role: command(['docker', 'inspect', '--format',
                    '{{.Image}} {{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}', node]).decode().strip()
                    for role, node in (('source', source), ('replica', replica))}}
    try:
        result = bootstrap(source, replica, folder) if args.phase == 'bootstrap' else recover(source, replica)
    except Exception as error:
        # Never publish raw SQL/connection errors or a dump to Git/stdout.
        (folder/'result.json').write_text(json.dumps({**metadata, 'passed': False,
            'error_type': type(error).__name__, 'capacity_certified': False}, indent=2))
        raise
    result.update(metadata, passed=True)
    result.update(capacity_certified=False, api_reads_use_replica=False, writer_promoted=False)
    (folder/'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'evidence_directory': str(folder), **result}, indent=2))


if __name__ == '__main__':
    main()
