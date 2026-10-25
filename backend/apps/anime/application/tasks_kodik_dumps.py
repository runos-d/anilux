import logging

from celery import shared_task

from apps.anime.application import kodik_dump_service

logger = logging.getLogger(__name__)


@shared_task(name="apps.anime.import_kodik_dumps", time_limit=3600, soft_time_limit=3300)
def import_kodik_dumps_task(force: bool = False, max_new: int = 3000):
    result = kodik_dump_service.sync_catalog(force=force, max_new=max_new)
    from apps.anime.application.recommendations import invalidate_catalog
    invalidate_catalog()
    return result


@shared_task(name="apps.anime.import_kodik_calendar", time_limit=240, soft_time_limit=200)
def import_kodik_calendar_task(force: bool = False):
    result = kodik_dump_service.sync_calendar(force=force)
    return result
