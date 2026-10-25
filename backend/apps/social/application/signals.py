from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import Post, Follow


@receiver(post_save, sender=Post)
def on_post_created(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.status != 'published' or instance.is_deleted:
        return
    from apps.social.application.post_commands import record_event
    record_event(instance, 'new_post')


def create_level_up_post(user, new_level):
    from apps.social.application.services import SystemPostService
    
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
    from apps.social.application.services import SystemPostService
    
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
    from apps.social.application.services import SystemPostService
    return SystemPostService.create_contest_win_post(
        user=user,
        contest_title=contest_title,
        place=place
    )
