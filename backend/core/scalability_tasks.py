"""Lab-only protocol probe; imported only by the disposable lab Celery app."""
from celery import shared_task
from django.conf import settings


@shared_task(bind=True, name='scalability.lab_retry_probe', max_retries=1, acks_late=True,
             reject_on_worker_lost=True)
def lab_retry_probe(self):
    if settings.DATABASES['default']['HOST'] != 'lab-mysql' or settings.DATABASES['default']['NAME'] != 'scalability_lab':
        raise RuntimeError('Probe is restricted to the disposable lab')
    if not self.request.retries:
        raise self.retry(countdown=1)
    return {'retried': self.request.retries, 'completed': True}
