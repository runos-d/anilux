"""Streaming physical inventory, including files with no FileField reference."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time

from core.object_migration import CHUNK


def scan_storage(root, output, *, domain='unspecified', prefix='', max_entries=10000, max_seconds=30, hash_budget=0):
    if os.name != 'posix':
        raise ValueError('Run the inventory in the Linux storage-worker container')
    relative = PurePosixPath(prefix)
    if '\\' in prefix or relative.is_absolute() or '..' in relative.parts or len(prefix) > 1024:
        raise ValueError('Expected a relative directory prefix')
    root = Path(root).resolve(strict=True)
    # No symlink directory is traversed, even when it points inside this root.
    if not 1 <= max_entries <= 1000000 or not 1 <= max_seconds <= 3600 or not 0 <= hash_budget <= 64*1024*1024:
        raise ValueError('Inventory budget out of bounds')
    def emit(row):
        output.write(json.dumps(row, ensure_ascii=True)+'\n')
    emit({'type': 'header', 'schema_version': 1, 'scope': 'physical storage tree',
        'storage_domain': domain, 'prefix': prefix, 'started_at_unix': time.time(),
        'visibility_inferred': False, 'snapshot_consistent': False,
        'complete_storage_inventory': False})
    deadline = time.monotonic()+max_seconds
    counts = {'entries': 0, 'files': 0, 'directories': 0, 'symlinks': 0, 'errors': 0,
              'bytes': 0, 'hashed_bytes': 0}
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(root, directory_flags)
    try:
        for part in relative.parts:
            child = os.open(part, directory_flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        stack = [(os.scandir(descriptor), descriptor, relative)]
    except OSError:
        os.close(descriptor)
        raise ValueError('Inventory prefix must be a directory without symlinks') from None
    reason = None
    def close_directory():
        iterator, descriptor, _ = stack.pop()
        iterator.close()
        os.close(descriptor)
    try:
        while stack:
            if counts['entries'] >= max_entries or time.monotonic() >= deadline:
                reason = 'entry_budget' if counts['entries'] >= max_entries else 'time_budget'
                break
            try:
                iterator, directory, parent = stack[-1]
                entry = next(iterator)
            except StopIteration:
                close_directory()
                continue
            except OSError:
                counts['errors'] += 1
                close_directory()
                continue
            counts['entries'] += 1
            name = parent/entry.name
            row = {'type': 'entry', 'legacy_name': name.as_posix()}
            try:
                before = entry.stat(follow_symlinks=False)
                row.update(bytes=before.st_size, mtime_ns=before.st_mtime_ns)
                if stat.S_ISLNK(before.st_mode):
                    counts['symlinks'] += 1
                    row['status'] = 'symlink_not_followed'
                elif stat.S_ISDIR(before.st_mode):
                    counts['directories'] += 1
                    row['status'] = 'directory'
                    if len(stack) >= 64:
                        counts['errors'] += 1
                        row['status'] = 'depth_budget'
                    else:
                        child = os.open(entry.name, directory_flags, dir_fd=directory)
                        try:
                            stack.append((os.scandir(child), child, name))
                        except OSError:
                            os.close(child)
                            raise
                elif stat.S_ISREG(before.st_mode):
                    counts['files'] += 1
                    counts['bytes'] += before.st_size
                    row['status'] = 'present'
                    if before.st_size <= hash_budget:
                        # Reserve before I/O so failures cannot reuse the budget.
                        hash_budget -= before.st_size
                        descriptor = os.open(entry.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                        with os.fdopen(descriptor, 'rb') as stream:
                            opened = os.fstat(stream.fileno())
                            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                                raise ValueError('Source replaced')
                            digest, size = hashlib.sha256(), 0
                            while block := stream.read(min(CHUNK, max(1, before.st_size-size+1))):
                                size += len(block)
                                if size > before.st_size:
                                    break
                                digest.update(block)
                            after = os.fstat(stream.fileno())
                        counts['hashed_bytes'] += min(size, before.st_size)
                        current = os.stat(entry.name, dir_fd=directory, follow_symlinks=False)
                        if (size != before.st_size or (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino)
                                or (before.st_mtime_ns, before.st_ctime_ns) != (after.st_mtime_ns, after.st_ctime_ns)):
                            row['status'] = 'changed_during_hash'
                            counts['errors'] += 1
                        else:
                            row['sha256'] = digest.hexdigest()
                else:
                    row['status'] = 'special_file_not_opened'
            except (OSError, ValueError):
                counts['errors'] += 1
                row['status'] = 'unreadable_or_changed'
            emit(row)
    finally:
        exhausted = not stack
        while stack:
            close_directory()
    summary = {'type': 'summary', **counts, 'tree_exhausted': exhausted,
        'scan_completed': exhausted and not counts['errors'], 'stopped_reason': reason,
        'complete_storage_inventory': False, 'visibility_inferred': False, 'snapshot_consistent': False}
    emit(summary)
    output.flush()
    os.fsync(output.fileno())
    return summary
