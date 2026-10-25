from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.users.infrastructure.models.users import UserLibrary
from apps.anime.application.recommendations import invalidate_user
from apps.anime.infrastructure.models.anime import Anime, Franchise
from django.db import transaction


@receiver(post_save, sender=UserLibrary)
@receiver(post_delete, sender=UserLibrary)
def library_changed(sender, instance, **kwargs):
    from apps.users.infrastructure.models.users import User
    origin = kwargs.get('origin')
    if isinstance(origin, User) or getattr(origin, 'model', None) is User:
        return
    invalidate_user(instance.user_id)


@receiver(post_save, sender=Anime)
@receiver(post_delete, sender=Anime)
@receiver(post_save, sender=Franchise)
@receiver(post_delete, sender=Franchise)
def catalog_changed(sender, instance, **kwargs):
    def invalidate():
        from django.core.cache import cache
        from django.utils import timezone
        from apps.anime.application.recommendations import invalidate_catalog
        try:
            cache.delete('recommendations:candidates:v1')
            cache.set('catalog:revision', timezone.now().timestamp(), None)
            if cache.add('catalog:rebuild-debounce', 1, 10):
                invalidate_catalog()
        except Exception:
            invalidate_catalog()
    transaction.on_commit(invalidate, robust=True)
