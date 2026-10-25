from celery import shared_task


@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    name="users.send_transactional_email",
)
def send_transactional_email(self, user_id: int, kind: str):
    from apps.users.application.email_service import (
        send_confirmation,
        send_password_changed,
        send_password_reset,
    )
    from apps.users.infrastructure.models.users import User

    sender = {
        "confirmation": send_confirmation,
        "password_reset": send_password_reset,
        "password_changed": send_password_changed,
    }.get(kind)
    if sender is None:
        raise ValueError("Unsupported transactional email kind")
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user and user.email:
        sender(user)
