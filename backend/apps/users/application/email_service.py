from html import escape
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.utils.crypto import get_random_string
import logging


CONFIRM_SALT = "users.email-confirm.v1"
RESET_SALT = "users.password-reset.v1"
logger = logging.getLogger(__name__)


def _cache_key(purpose: str, user_id: int) -> str:
    return f"auth-token:{purpose}:{user_id}"


def issue_one_time_token(user, purpose: str) -> str:
    nonce = get_random_string(32)
    cache.set(
        _cache_key(purpose, user.pk),
        nonce,
        timeout=(
            settings.EMAIL_CONFIRM_TOKEN_TTL_SECONDS
            if purpose == "confirm"
            else settings.PASSWORD_RESET_TOKEN_TTL_SECONDS
        ),
    )
    salt = CONFIRM_SALT if purpose == "confirm" else RESET_SALT
    return signing.dumps(
        {"uid": user.pk, "email": user.email.lower(), "nonce": nonce},
        salt=salt,
        compress=True,
    )


def consume_one_time_token(token: str, purpose: str):
    from apps.users.infrastructure.models.users import User

    salt = CONFIRM_SALT if purpose == "confirm" else RESET_SALT
    max_age = (
        settings.EMAIL_CONFIRM_TOKEN_TTL_SECONDS
        if purpose == "confirm"
        else settings.PASSWORD_RESET_TOKEN_TTL_SECONDS
    )
    data = signing.loads(token, salt=salt, max_age=max_age)
    key = _cache_key(purpose, data["uid"])
    expected = cache.get(key)
    if not expected or expected != data.get("nonce"):
        raise signing.BadSignature("Token was already used or superseded")
    user = User.objects.get(pk=data["uid"], email__iexact=data["email"])
    cache.delete(key)
    return user


def _send(*, to: str, subject: str, heading: str, body: str, action: str, url: str) -> None:
    from apps.users.infrastructure.models.users import SuppressedEmail

    if SuppressedEmail.objects.filter(email__iexact=to).exists():
        return
    brand = settings.PROJECT_BRAND_NAME
    safe_brand = escape(brand)
    safe_heading = escape(heading)
    safe_body = escape(body)
    safe_action = escape(action)
    safe_url = escape(url, quote=True)
    html = f"""<!doctype html><html><body style="font-family:Arial,sans-serif">
<h1>{safe_brand}</h1><h2>{safe_heading}</h2><p>{safe_body}</p>
<p><a href="{safe_url}">{safe_action}</a></p>
<p>{safe_brand}</p></body></html>"""
    message = EmailMultiAlternatives(
        subject=f"{subject} — {brand}",
        body=f"{body}\n\n{url}\n\n{brand}",
        from_email=settings.TRANSACTIONAL_FROM_EMAIL,
        to=[to],
        reply_to=[settings.TRANSACTIONAL_REPLY_TO_EMAIL]
        if settings.TRANSACTIONAL_REPLY_TO_EMAIL
        else None,
    )
    message.attach_alternative(html, "text/html")
    message.send(fail_silently=settings.EMAIL_FAIL_SILENTLY)


def send_confirmation(user) -> None:
    token = issue_one_time_token(user, "confirm")
    url = f"{settings.FRONTEND_PUBLIC_URL}/confirm-email?{urlencode({'token': token})}"
    _send(
        to=user.email,
        subject="Подтверждение email",
        heading="Подтвердите email",
        body="Подтвердите адрес, чтобы завершить регистрацию.",
        action="Подтвердить email",
        url=url,
    )


def send_password_reset(user) -> None:
    token = issue_one_time_token(user, "reset")
    url = f"{settings.FRONTEND_PUBLIC_URL}/reset-password?{urlencode({'token': token})}"
    _send(
        to=user.email,
        subject="Восстановление пароля",
        heading="Сброс пароля",
        body="Если вы запрашивали новый пароль, продолжите по ссылке.",
        action="Задать новый пароль",
        url=url,
    )


def send_password_changed(user) -> None:
    _send(
        to=user.email,
        subject="Пароль изменён",
        heading="Пароль изменён",
        body="Пароль вашей учётной записи был изменён. Если это были не вы, обратитесь в поддержку.",
        action="Открыть сайт",
        url=settings.FRONTEND_PUBLIC_URL,
    )


def dispatch_transactional_email(user, kind: str) -> None:
    senders = {
        "confirmation": send_confirmation,
        "password_reset": send_password_reset,
        "password_changed": send_password_changed,
    }
    if kind not in senders:
        raise ValueError("Unsupported transactional email kind")
    if settings.EMAIL_PROVIDER == "mailpit" or getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        senders[kind](user)
        return
    try:
        from apps.users.application.email_tasks import send_transactional_email

        send_transactional_email.delay(user.pk, kind)
    except Exception:
        logger.exception("Failed to enqueue transactional email kind=%s", kind)
