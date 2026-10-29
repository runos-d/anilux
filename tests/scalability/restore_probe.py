"""Host-side MySQL backup/restore rehearsal restricted to the disposable lab."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid

CONTAINER = 'animecore-scalability-lab-lab-mysql-1'
TABLES = ('users_user', 'anime_anime', 'social_post', 'social_message', 'social_chatevent', 'django_migrations')


def execute(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs).stdout


def mysql(sql, database=None):
    args = ['docker', 'exec', '-i', '-e', 'MYSQL_PWD=disposable-lab', CONTAINER,
            'mysql', '-uroot', '--batch', '--raw', '--skip-column-names']
    if database:
        args.append(database)
    return execute(args, input=sql.encode()).decode().strip()


def fingerprint(database):
    result = {}
    for table in TABLES:
        count = int(mysql(f'SELECT COUNT(*) FROM `{table}`', database))
        checksum = mysql(f'CHECKSUM TABLE `{table}` EXTENDED', database).split('\t')[-1]
        result[table] = {'rows': count, 'mysql_checksum': checksum}
    return result


def main():
    state = json.loads(execute(['docker', 'inspect', CONTAINER]))[0]
    labels = state['Config']['Labels']
    if labels.get('com.docker.compose.project') != 'animecore-scalability-lab' or labels.get('com.docker.compose.service') != 'lab-mysql':
        raise RuntimeError('Refusing a non-lab container')
    if mysql('SELECT DATABASE()', 'scalability_lab') != 'scalability_lab':
        raise RuntimeError('Refusing a non-lab schema')
    stamp = uuid.uuid4().hex[:12]
    target = 'scalability_restore_' + stamp
    if mysql(f"SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='{target}'") != '0':
        raise RuntimeError('Refusing to overwrite an existing restore schema')
    folder = Path(__file__).resolve().parents[2] / '.tmp' / 'scalability'
    folder.mkdir(parents=True, exist_ok=True)
    dump = folder / f'restore-{stamp}.sql'
    remote = f'/tmp/scalability-restore-{stamp}.sql'
    before = fingerprint('scalability_lab')
    execute(['docker', 'exec', '-e', 'MYSQL_PWD=disposable-lab', CONTAINER, 'mysqldump', '-uroot',
        '--single-transaction', '--skip-lock-tables', '--set-gtid-purged=OFF', '--no-tablespaces',
        '--routines', '--triggers', '--result-file=' + remote, 'scalability_lab'])
    execute(['docker', 'cp', CONTAINER + ':' + remote, str(dump)])
    digest = hashlib.sha256()
    with dump.open('rb') as source:
        while chunk := source.read(1048576):
            digest.update(chunk)
    mysql(f'CREATE DATABASE `{target}` CHARACTER SET utf8mb4')
    start = time.monotonic()
    with dump.open('rb') as source:
        execute(['docker', 'exec', '-i', '-e', 'MYSQL_PWD=disposable-lab', CONTAINER,
                 'mysql', '-uroot', target], stdin=source)
    seconds = time.monotonic() - start
    after = fingerprint(target)
    report = {'schema_version': 1, 'synthetic_only': True, 'production_rpo_rto_certified': False,
              'backup_bytes': dump.stat().st_size, 'backup_sha256': digest.hexdigest(),
              'restore_seconds': seconds, 'tables': after, 'checksums_and_counts_match': before == after,
              'scope': 'database dump/restore in another schema; not host failover or media restore'}
    (folder / 'restore-result.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if before != after:
        raise RuntimeError('Restore fingerprint mismatch')


if __name__ == '__main__':
    main()
