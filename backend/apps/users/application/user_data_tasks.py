from celery import shared_task

from apps.users.application.data_management import build_user_export, expire_exports


@shared_task(name="users.build_data_export", time_limit=300, soft_time_limit=280)
def build_data_export_task(export_id: int):
    build_user_export(export_id)


@shared_task(name="users.expire_data_exports")
def expire_data_exports_task():
    return expire_exports()
