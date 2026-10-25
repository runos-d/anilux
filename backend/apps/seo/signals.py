from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from apps.anime.infrastructure.models.anime import Anime, Franchise
from .models import SEO_PATH_MAX_LENGTH, SeoAlias


@receiver(pre_save, sender=Anime)
@receiver(pre_save, sender=Franchise)
def remember_slug(sender, instance, **kwargs):
    if instance.pk:
        instance._seo_old_slug = sender.objects.filter(pk=instance.pk).values_list('slug', flat=True).first()


@receiver(post_save, sender=Anime)
@receiver(post_save, sender=Franchise)
def record_alias(sender, instance, **kwargs):
    from .service import anime_path
    old = getattr(instance, '_seo_old_slug', None)
    if old and old != instance.slug:
        paths = [f'/anime/{old}', f'/anime/{instance.pk}-{old}'] if sender is Anime else [f'/franchise/{old}', f'/anime/franchise/{old}']
        for path in paths:
            if len(path) <= SEO_PATH_MAX_LENGTH:
                SeoAlias.objects.update_or_create(path=path, defaults={'kind': 'anime' if sender is Anime else 'franchise', 'object_id': str(instance.pk)})


def schedule_hubs():
    from django.core.cache import cache
    def queue():
        try:
            if cache.add('seo:hub-refresh-pending', True, 30):
                from .tasks import refresh_hubs
                refresh_hubs.apply_async(countdown=5)
        except Exception:
            import logging
            logging.getLogger(__name__).warning('SEO hub refresh deferred; run refresh_seo or await periodic retry')
    transaction.on_commit(queue, robust=True)


@receiver(post_save)
@receiver(post_delete)
def changed(sender, instance, **kwargs):
    if sender._meta.label_lower in {'anime.anime', 'anime.franchise', 'anime.genre', 'anime.catalogvisibility',
                                   'anime.cataloghiderule', 'seo.seocollection', 'seo.siteseosettings', 'seo.seooverride'}:
        schedule_hubs()
