import hashlib
import json
import os
import time
import uuid
from pathlib import Path, PurePosixPath

from django.apps import apps
from django.db import models
from django.core.management.base import CommandError
from apps.social.infrastructure.chat_storage import ChatPrivateStorage, chat_private_storage


def references():
    result = set()
    for model in apps.get_app_config('social').get_models():
        for field in model._meta.fields:
            if isinstance(field, models.FileField) and isinstance(field.storage, ChatPrivateStorage):
                result.update(model.objects.exclude(**{field.name: ''}).values_list(field.name, flat=True))
    result.discard(None)
    return result


def safe_path(root, name):
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or '..' in relative.parts or '\\' in name:
        raise CommandError('Invalid private file path')
    path = root / name
    if not path.resolve().is_relative_to(root):
        raise CommandError('Private file leaves its storage root')
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise CommandError('Symbolic links are not eligible for collection')
        if parent == root:
            break
    return path


def storage_roots():
    original = Path(chat_private_storage.location)
    if original.is_symlink():
        raise CommandError('Private storage root is a symbolic link')
    root = original.resolve()
    quarantine = root.parent / 'chat_file_quarantine'
    if quarantine.is_symlink():
        raise CommandError('Quarantine root is a symbolic link')
    return root, quarantine.resolve()


def fingerprint(path):
    stat = path.stat(follow_symlinks=False)
    return (stat.st_size, stat.st_mtime_ns, stat.st_ino, stat.st_dev)


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def journal(path, manifest):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf8') as output:
        json.dump(manifest, output, ensure_ascii=False, indent=2)
        output.flush(); os.fsync(output.fileno())
    temporary.replace(path)


def collect(*, age_hours=24, limit=100, apply=False):
    root, quarantine = storage_roots()
    known = references()
    for name in known:
        safe_path(root, name)
    cutoff = time.time() - age_hours * 3600
    candidates, total = [], 0
    for path in root.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        safe_path(root, name)
        if name in known:
            continue
        try:
            state = fingerprint(path)
        except FileNotFoundError:
            continue
        if state[1] > cutoff * 1e9:
            continue
        total += 1
        if len(candidates) < limit:
            candidates.append((name, state))
    result = {'dry_run': not apply, 'eligible': total, 'batch_count': len(candidates),
              'batch_bytes': sum(state[0] for _, state in candidates), 'collected': 0}
    if not apply or not candidates:
        return result
    if references() != known:
        raise CommandError('File references changed; stop writers and repeat the audit')
    run_id = uuid.uuid4().hex
    run = safe_path(quarantine, run_id)
    run.mkdir(parents=True, exist_ok=False)
    manifest = {'version': 1, 'root': str(root), 'files': []}
    manifest_path = run / 'manifest.json'
    journal(manifest_path, manifest)
    for name, expected in candidates:
        source = safe_path(root, name)
        if not source.exists() or fingerprint(source) != expected:
            continue
        checksum = digest(source)
        if fingerprint(source) != expected:
            continue
        target = safe_path(run, 'files/' + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        entry = {'name': name, 'sha256': checksum, 'size': expected[0], 'status': 'moving'}
        manifest['files'].append(entry)
        journal(manifest_path, manifest)
        source.rename(target)
        entry['status'] = 'quarantined'
        journal(manifest_path, manifest)
        result['collected'] += 1
    result['run_id'] = run_id
    return result


def restore(run_id):
    if len(run_id) != 32 or any(char not in '0123456789abcdef' for char in run_id):
        raise CommandError('Invalid quarantine run ID')
    root, quarantine = storage_roots()
    run = safe_path(quarantine, run_id)
    manifest_path = safe_path(run, 'manifest.json')
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    if manifest.get('version') != 1 or manifest.get('root') != str(root):
        raise CommandError('Quarantine belongs to another storage root')
    planned = []
    for entry in manifest['files']:
        source = safe_path(run, 'files/' + entry['name'])
        target = safe_path(root, entry['name'])
        if target.exists():
            if digest(target) != entry['sha256']:
                raise CommandError('Restore conflicts with an existing private file')
        elif not source.is_file() or digest(source) != entry['sha256']:
            raise CommandError('Quarantined file is missing or damaged')
        planned.append((source, target, entry))
    restored = 0
    for source, target, entry in planned:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            restored += 1
        entry['status'] = 'restored'
        journal(manifest_path, manifest)
    return {'run_id': run_id, 'restored': restored}
