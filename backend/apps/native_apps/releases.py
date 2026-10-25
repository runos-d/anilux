import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.utils import timezone

TARGETS = {
    'windows': ('Windows', '.exe'), 'android': ('Android', '.apk'),
    'deb': ('Ubuntu / Debian', '.deb'), 'appimage': ('Linux', '.AppImage'),
    'flatpak': ('Flatpak', '.flatpak'), 'ios': ('iPhone / iPad', '.ipa'),
}


def site_url(value=None):
    value = value or getattr(settings, 'NATIVE_APP_SITE_URL', '') or getattr(settings, 'SEO_PUBLIC_ORIGIN', '') or settings.SITE_URL
    url = urlsplit(str(value or ''))
    if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
        raise ValueError('Set SITE_URL to the public http(s) origin of the website')
    if url.path not in ('', '/') or url.query or url.fragment:
        raise ValueError('SITE_URL must contain only the website origin')
    port = url.port
    host = url.hostname.encode('idna').decode('ascii').lower()
    if ':' in host: host = '['+host+']'
    if port and port != {'http':80,'https':443}[url.scheme]: host += ':'+str(port)
    return f'{url.scheme}://{host}'


def source_root():
    return Path(settings.BASE_DIR) / 'native'


def identity(value=None):
    origin = site_url(value)
    digest = hashlib.sha256()
    for base, dirs, files in os.walk(source_root()):
        dirs[:] = sorted(d for d in dirs if d not in ('node_modules', 'build', '.gradle', 'dist', '.git', '__pycache__'))
        for name in sorted(files):
            path = Path(base) / name
            digest.update(path.relative_to(source_root()).as_posix().encode())
            digest.update(path.read_bytes())
    version = getattr(settings, 'NATIVE_APP_VERSION', '0.1.0')
    key = hashlib.sha256(f'{origin}\n{version}\n{digest.hexdigest()}'.encode()).hexdigest()[:24]
    return key, origin, version


def release_dir(key):
    if not re.fullmatch(r'[a-f0-9]{24}', key):
        raise ValueError('Invalid release id')
    return Path(settings.DATA_DIR) / 'native_releases' / key


def read_manifest(key):
    try:
        return json.loads((release_dir(key) / 'manifest.json').read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_manifest(key, data):
    folder = release_dir(key)
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder / f'manifest.{os.getpid()}.tmp'
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(folder / 'manifest.json')


def public_manifest(release=None):
    key, origin, version = release or identity()
    data = read_manifest(key)
    entries = []
    for target, (label, suffix) in TARGETS.items():
        artifact = data.get('artifacts', {}).get(target, {})
        name = artifact.get('filename', '')
        path = release_dir(key) / name
        ready = (artifact.get('status') == 'ready' and Path(name).name == name and
                 name.endswith(suffix) and path.is_file() and path.resolve().is_relative_to(release_dir(key).resolve()))
        state = 'ready' if ready else ('failed' if artifact.get('status') == 'ready' else artifact.get('status', 'pending'))
        if target == 'ios' and not ready and not os.environ.get('NATIVE_MAC_BUILD_COMMAND'):
            state = 'requires_signing'
        entries.append({'platform': target, 'label': label,
            'status': state,
            'url': f'/api/application/releases/{key}/{name}' if ready else None,
            'size': artifact.get('size') if ready else None,
            'sha256': artifact.get('sha256') if ready else None})
    return {'release': key, 'site_url': origin, 'version': version,
            'status': data.get('status', 'pending'), 'artifacts': entries}


def schedule_build(force=False):
    from django.core.cache import cache
    from .tasks import build_release
    key, origin, version = identity()
    existing = read_manifest(key)
    if not force and existing.get('status') == 'ready' and all(
        row['status'] == 'ready' or (row['platform'] == 'ios' and row['status'] == 'requires_signing'
        and not os.environ.get('NATIVE_MAC_BUILD_COMMAND')) for row in public_manifest((key, origin, version))['artifacts']):
        return key
    lock = f'native-build:scheduled:{key}'
    if not cache.add(lock, True, 6 * 3600):
        return key
    try:
        data = existing or {'site_url': origin, 'version': version, 'artifacts': {}}
        data.update(status='queued', updated_at=timezone.now().isoformat())
        write_manifest(key, data)
        build_release.apply_async(args=[key, origin, version], queue='native_builds',
            retry=False, task_id=f'native-build-{key}')
    except Exception:
        cache.delete(lock)
        data.update(status='failed')
        write_manifest(key, data)
        raise
    return key
