"""Bounded FileField inventory. Names belong only in a private page manifest."""
import hashlib
import os
from pathlib import Path
import stat

from django.apps import apps
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from core.object_migration import CHUNK, source_path


def file_fields(model):
    return [field for field in model._meta.local_fields if isinstance(field, models.FileField)]


def storage_domain(storage):
    if not isinstance(storage, FileSystemStorage):
        return None
    location = Path(storage.location).resolve()
    for domain, root in (('chat', settings.CHAT_PRIVATE_MEDIA_ROOT),
                         ('post', settings.POST_PRIVATE_MEDIA_ROOT), ('public', settings.MEDIA_ROOT)):
        if location == Path(root).resolve():
            return domain
    return None


def describe_fields():
    return [{'model': model._meta.label_lower, 'field': field.name,
             'storage_domain': storage_domain(field.storage), 'visibility_inferred': False}
            for model in apps.get_models() for field in file_fields(model)]


def private_page(path):
    """Exclusive creation: never clobber another page or append partial JSON."""
    path = Path(path)
    base = Path(settings.BASE_DIR).resolve()
    checkout = base.parent if (base.parent/'.git').exists() else base
    if path.is_symlink() or path.resolve().is_relative_to(checkout):
        raise ValueError('Private manifest must be outside checkout and not a symlink')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(path, flags, 0o600)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError('Private manifest must be a regular file')
    return os.fdopen(descriptor, 'w', encoding='utf-8')


def inventory_page(model, *, after_id, through_id, limit, hash_budget=0):
    fields = file_fields(model)
    rows = list(model._base_manager.filter(pk__gt=after_id, pk__lte=through_id).order_by('pk')
                .values('pk', *(field.name for field in fields))[:limit+1])
    has_more = len(rows) > limit
    rows = rows[:limit]
    references = []
    for row in rows:
        for field in fields:
            name = row[field.name]
            if not name:
                continue
            domain = storage_domain(field.storage)
            item = {'model': model._meta.label_lower, 'pk': row['pk'], 'field': field.name,
                    'legacy_name': name, 'storage_domain': domain, 'status': 'unsupported_storage'}
            references.append(item)
            if domain is None:
                continue
            try:
                path = source_path(field.storage.location, name)
                before = path.stat()
                item.update(status='present', bytes=before.st_size, mtime_ns=before.st_mtime_ns)
                if before.st_size <= hash_budget:
                    digest, size = hashlib.sha256(), 0
                    with path.open('rb') as stream:
                        # A concurrently growing file must not bypass I/O bounds.
                        while block := stream.read(min(CHUNK, max(1, before.st_size-size+1))):
                            size += len(block)
                            if size > before.st_size:
                                break
                            digest.update(block)
                    after = path.stat()
                    hash_budget -= min(size, before.st_size)
                    if size != before.st_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        item['status'] = 'changed_during_hash'
                    else:
                        item['sha256'] = digest.hexdigest()
            except FileNotFoundError:
                item['status'] = 'missing'
            except ValueError:
                item['status'] = 'invalid_path'
            except OSError:
                item['status'] = 'unreadable'
    return {'schema_version': 1, 'model': model._meta.label_lower, 'rows': len(rows),
            'after_id': after_id, 'through_id': through_id, 'limit': limit,
            'next_after_id': rows[-1]['pk'] if rows else after_id, 'has_more': has_more,
            'references': references, 'visibility_inferred': False, 'complete_storage_inventory': False,
            'scope': 'FileFields only; JSON paths, exports, download caches and orphan files require separate inventory'}
