"""Database-backed admission: one queue cap across all HTTP instances."""
from datetime import timedelta
import hashlib
import json
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, Throttled
from apps.anime.models import BackgroundJob, WorkGate


def enqueue(kind, payload, task):
    identity = {key: value for key, value in payload.items() if key != 'client_ip'}
    key = hashlib.sha256(json.dumps([kind, identity], sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        WorkGate.objects.get_or_create(name=kind)
        WorkGate.objects.select_for_update().get(name=kind)
        job = BackgroundJob.objects.filter(key=key).first()
        if job and job.status in ('pending', 'processing', 'ready'):
            return job
        if job and job.updated_at > timezone.now() - timedelta(seconds=60):
            raise Throttled(wait=60, detail=job.error or 'Повторите подготовку позже')
        if BackgroundJob.objects.filter(kind=kind, status__in=['pending', 'processing']).count() >= (20 if kind == 'download' else 10):
            raise Throttled(wait=30, detail='Очередь заполнена. Повторите позже.')
        if job:
            job.status, job.result, job.error = 'pending', {}, ''
            job.save(update_fields=['status', 'result', 'error', 'updated_at'])
        else:
            job = BackgroundJob.objects.create(kind=kind, key=key, payload=payload)
        def publish():
            try:
                task.apply_async(args=[str(job.pk)], queue='media_downloads' if kind == 'download' else 'catalog_imports', retry=False)
            except Exception:
                BackgroundJob.objects.filter(pk=job.pk).update(status='failed', error='Сервис подготовки временно недоступен', updated_at=timezone.now())
        transaction.on_commit(publish)
    job.refresh_from_db()
    if job.status == 'failed':
        failure = APIException(job.error)
        failure.status_code = 503
        raise failure
    return job
