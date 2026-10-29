"""Private local file responses with bounded ASGI streaming and single ranges."""
import asyncio
import re
from django.http import HttpResponse, StreamingHttpResponse


def byte_range(value, size):
    if value is None:
        return 0, size - 1, 200
    if len(value) > 128:
        raise ValueError('Range header too long')
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
    if not match or not any(match.groups()) or size <= 0:
        raise ValueError('Invalid range')
    left, right = match.groups()
    if left:
        start, end = int(left), min(int(right), size - 1) if right else size - 1
    else:
        suffix = int(right)
        if suffix == 0:
            raise ValueError('Empty suffix')
        start, end = max(0, size - suffix), size - 1
    if start >= size or end < start:
        raise ValueError('Unsatisfiable range')
    return start, end, 206


def private_file_response(path, *, method, range_header, size, content_type, headers):
    try:
        start, end, status = byte_range(range_header, size)
    except ValueError:
        return HttpResponse(status=416, headers={**headers, 'Content-Range': f'bytes */{size}'})
    headers = {**headers, 'Content-Length': str(end - start + 1)}
    if status == 206:
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
    if method == 'HEAD':
        return HttpResponse(status=status, content_type=content_type, headers=headers)
    # Open in the synchronous Django view's worker. Register close even if a
    # disconnect occurs before the async iterator starts. Never buffer the file.
    handle = path.open('rb')
    try:
        handle.seek(start)
        async def chunks():
            remaining = end - start + 1
            try:
                while remaining > 0:
                    chunk = await asyncio.to_thread(handle.read, min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
            finally:
                handle.close()
        response = StreamingHttpResponse(chunks(), status=status, content_type=content_type, headers=headers)
        response._resource_closers.append(handle.close)
        return response
    except BaseException:
        handle.close()
        raise
