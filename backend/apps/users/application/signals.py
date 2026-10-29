from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.utils import timezone

from django.contrib.auth import user_logged_in
from django.contrib.sessions.models import Session

from apps.social.infrastructure.models.social import Post
from apps.users.infrastructure.models.users import User, UserSettings, UserProfileSettings


@receiver(post_save, sender=Session)
def index_login_session(sender, instance, raw=False, **kwargs):
    """Index every saved login, including Django admin and cookie-only logins."""
    if raw:
        return
    owner = instance.get_decoded().get('_auth_user_id')
    if owner and str(owner).isdigit():
        from apps.users.infrastructure.models.users import ActiveSession
        ActiveSession.objects.get_or_create(session_key=instance.session_key, defaults={
            'user_id': int(owner), 'ip_address': '127.0.0.1', 'user_agent': '',
        })


def create_level_up_post(user, new_level):
    from apps.social.application.feed_service import SystemPostService

    existing_posts = Post.objects.filter(
        author=user,
        post_type='system',
        system_type='level_up',
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    )

    if not existing_posts.exists():
        return SystemPostService.create_level_up_post(
            user=user,
            new_level=new_level
        )
    return None


def create_achievement_post(user, achievement_name, achievement_level):
    from apps.social.application.feed_service import SystemPostService

    existing_posts = Post.objects.filter(
        author=user,
        post_type='system',
        system_type='achievement_unlocked',
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    )

    if not existing_posts.exists():
        return SystemPostService.create_achievement_post(
            user=user,
            achievement_name=achievement_name,
            achievement_level=achievement_level
        )
    return None


def create_contest_win_post(user, contest_title, place):
    from apps.social.application.feed_service import SystemPostService
    return SystemPostService.create_contest_win_post(
        user=user,
        contest_title=contest_title,
        place=place
    )

def notify_admin(title: str, content: str, notif_type: str = 'system', link: str = ''):
    try:
        admin = User.objects.filter(username='kaiden812').first()
        if not admin:
            admin = User.objects.filter(is_superuser=True).first()
        if admin:
            from apps.notifications.infrastructure.models.notifications import Notification
            Notification.objects.create(
                user=admin,
                type=notif_type,
                title=title,
                content=content,
                icon='🔔',
                link=link,
                is_important=True,
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'notify_admin error: {e}')


@receiver(post_save, sender=User)
def notify_admin_on_registration(sender, instance, created, **kwargs):
    if created:
        display = instance.nickname or instance.username
        notify_admin(
            title=f'👤 Новый пользователь: @{display}',
            content=f'Пользователь @{display} (имя: {instance.username}, email: {instance.email or "-"}) зарегистрировался.',
            notif_type='system',
            link=f'/profile/{instance.id}',
        )


@receiver(pre_save, sender=User)
def generate_unique_id(sender, instance, **kwargs):
    if not instance.unique_id:
        import random
        import string

        while True:
            unique_id = ''.join(random.choices(string.digits, k=12))
            if not User.objects.filter(unique_id=unique_id).exclude(pk=instance.pk).exists():
                instance.unique_id = unique_id
                break


@receiver(user_logged_in, sender=User)
def ensure_unique_id_on_login(sender, request, user, **kwargs):
    if not user.unique_id:
        user.ensure_unique_id()


@receiver(post_save, sender=UserSettings)
@receiver(post_save, sender=UserProfileSettings)
def refresh_presence_visibility(sender, instance, created, update_fields=None, **kwargs):
    if created or update_fields is not None and 'show_online_status' not in update_fields:
        return
    from core.online_status import online_status
    online_status._send_online_event(instance.user_id, instance.user.username, online_status.is_online(instance.user_id))
