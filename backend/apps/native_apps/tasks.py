import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import signal
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .releases import TARGETS, read_manifest, release_dir, source_root, write_manifest

logger = logging.getLogger(__name__)


def compile_installer(command, log):
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        code = process.wait(timeout=3600)
        if code: raise subprocess.CalledProcessError(code, command)
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        raise


@shared_task(name='native_apps.build_release', acks_late=True,
             reject_on_worker_lost=True, time_limit=14400, soft_time_limit=14300)
def build_release(key, origin, version):
    import fcntl
    folder = release_dir(key)
    folder.mkdir(parents=True, exist_ok=True)
    lease = (folder / '.build.lock').open('a')
    try: fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lease.close()
        return
    data = read_manifest(key)
    data.update(status='building', site_url=origin, version=version,
                updated_at=timezone.now().isoformat())
    data.setdefault('artifacts', {})
    write_manifest(key, data)
    try:
        for target, (_, suffix) in TARGETS.items():
            previous = data['artifacts'].get(target, {})
            if previous.get('status') == 'ready' and (folder / previous.get('filename', '')).is_file():
                continue
            if target == 'ios' and not os.environ.get('NATIVE_MAC_BUILD_COMMAND'):
                data['artifacts'][target] = {'status': 'requires_signing'}
                write_manifest(key, data)
                continue
            data['artifacts'][target] = {'status': 'building'}
            write_manifest(key, data)
            work_root = Path(settings.DATA_DIR) / 'native_build_work'
            work_root.mkdir(parents=True, exist_ok=True)
            try:
                with tempfile.TemporaryDirectory(prefix=target+'-', dir=work_root) as temporary:
                    output = Path(temporary) / ('anilux-'+version+'-'+target+suffix)
                    command = ['python', str(source_root() / 'build.py'), '--target', target,
                               '--site-url', origin, '--version', version, '--output', str(output)]
                    with (folder / (target+'.log')).open('ab') as log:
                        compile_installer(command, log)
                    if not output.is_file() or output.stat().st_size < 1024:
                        raise RuntimeError('Builder did not produce an installer')
                    with output.open('rb') as file:
                        digest = hashlib.file_digest(file, 'sha256').hexdigest()
                    filename = f'anilux-{version}-{target}-{digest[:12]}{suffix}'
                    shutil.move(str(output), str(folder / filename))
                    data['artifacts'][target] = {'status': 'ready', 'filename': filename,
                        'size': (folder / filename).stat().st_size, 'sha256': digest}
            except Exception:
                logger.exception('Native %s build failed for release %s', target, key)
                data['artifacts'][target] = {'status': 'failed'}
            write_manifest(key, data)
        data['status'] = 'failed' if any(a.get('status') == 'failed' for a in data['artifacts'].values()) else 'ready'
        data['updated_at'] = timezone.now().isoformat()
        write_manifest(key, data)
    finally:
        lease.close()
        cache.delete(f'native-build:scheduled:{key}')
