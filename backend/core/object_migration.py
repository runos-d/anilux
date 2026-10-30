"""Copy-first S3 preparation. No live-path cutover, redirects or source deletion."""
import hashlib
from pathlib import Path, PurePosixPath

CHUNK = 65536


def storage_roots():
    from django.conf import settings
    return {'public': settings.MEDIA_ROOT, 'chat': settings.CHAT_PRIVATE_MEDIA_ROOT,
        'post': getattr(settings, 'POST_PRIVATE_MEDIA_ROOT', Path(settings.DATA_DIR)/'private_post_media'),
        'downloads': getattr(settings, 'DOWNLOAD_ROOT', Path(settings.MEDIA_ROOT).parent/'private_downloads')}


def source_path(root, name):
    relative = PurePosixPath(name)
    if not name or '\\' in name or relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Expected a relative media path')
    root = Path(root).resolve(strict=True)
    path = root.joinpath(*relative.parts).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Media path escapes its storage root')
    return path


def sha256_stream(stream):
    digest = hashlib.sha256()
    size = 0
    while block := stream.read(CHUNK):
        size += len(block)
        digest.update(block)
    return size, digest.hexdigest()


def mirror_file(client, *, bucket, root, name, domain, apply=False, transfer_config=None):
    if domain not in ('chat', 'post', 'public') or not bucket:
        raise ValueError('Explicit bucket and known media domain required')
    path = source_path(root, name)
    before = path.stat()
    with path.open('rb') as stream:
        size, digest = sha256_stream(stream)
    key = f'{domain}/sha256/{digest[:2]}/{digest}'
    result = {'schema_version': 1, 'domain': domain, 'legacy_name': name,
              'object_key': key, 'bytes': size, 'sha256': digest, 'verified': False, 'applied': apply}
    if not apply:
        return result
    options = {'ExtraArgs': {'Metadata': {'sha256': digest}, 'CacheControl': 'private, no-store'}}
    if transfer_config is not None:
        options['Config'] = transfer_config
    # upload_file streams multipart uploads; source paths remain unchanged.
    # Content addressing makes retries idempotent; verify actual remote bytes,
    # rather than trusting an ETag (multipart ETags are not file hashes).
    client.upload_file(str(path), bucket, key, **options)
    body = client.get_object(Bucket=bucket, Key=key)['Body']
    try:
        remote_size, remote_hash = sha256_stream(body)
    finally:
        body.close()
    after = path.stat()
    if (size, digest) != (remote_size, remote_hash):
        raise RuntimeError('Remote object checksum mismatch; source preserved')
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('Source changed during copy; no mapping may be activated')
    result['verified'] = True
    return result


def s3_client(endpoint=None):
    import boto3
    from botocore.config import Config
    # Standard workload identity/credential chain; never put keys in a manifest.
    return boto3.client('s3', endpoint_url=endpoint or None, config=Config(
        connect_timeout=2, read_timeout=10, max_pool_connections=4,
        retries={'mode': 'standard', 'total_max_attempts': 3}))


def transfer_config():
    from boto3.s3.transfer import TransferConfig
    return TransferConfig(multipart_threshold=8 * 1024 * 1024, multipart_chunksize=8 * 1024 * 1024,
                          max_concurrency=2, max_io_queue=4, io_chunksize=CHUNK, preferred_transfer_client='classic')
