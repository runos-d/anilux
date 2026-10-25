from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import models


SEO_PATH_MAX_LENGTH = 255


class SiteSeoSettings(models.Model):
    site_name = models.CharField(max_length=100, default='AniLux')
    public_origin = models.URLField(blank=True, help_text='Только HTTPS origin без пути. Пусто -текущий адрес и noindex.')
    indexing_enabled = models.BooleanField(default=False)
    templates = models.JSONField(default=dict, blank=True, help_text='Ключи home/catalog/collection/anime/franchise/profile/post/playlist; значения title, description, h1. Подстановки: {name}, {site}, {count}, {summary}, {page}.')
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        origin = urlsplit(self.public_origin)
        if self.public_origin and (origin.scheme != 'https' or not origin.hostname or origin.path not in ('', '/') or origin.query or origin.fragment or origin.username or origin.port):
            raise ValidationError({'public_origin': 'Укажите HTTPS origin без порта, пути, параметров и логина.'})
        from .service import validate_templates
        validate_templates(self.templates)

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.site_name


class SeoCollection(models.Model):
    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=180)
    filters = models.JSONField(default=dict, help_text='Разрешены year, genre (slug), season, kind, status. Сезон: winter/spring/summer/autumn вместе с year.')
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from .service import filter_query
        filter_query(self.filters, validate=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SeoOverride(models.Model):
    path = models.CharField(max_length=SEO_PATH_MAX_LENGTH, unique=True, help_text='Канонический путь без query и завершающего слэша, например /anime/year/2025')
    title = models.CharField(max_length=250, blank=True)
    description = models.CharField(max_length=500, blank=True)
    h1 = models.CharField(max_length=250, blank=True)
    text = models.TextField(blank=True, help_text='Обычный текст под карточками. Не меняет правила доступа и порог 5.')
    noindex = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.path.startswith('/') or self.path.startswith('//') or '?' in self.path or '#' in self.path or (self.path != '/' and self.path.endswith('/')):
            raise ValidationError({'path': 'Нужен канонический относительный путь.'})

    def __str__(self):
        return self.path


class SeoAlias(models.Model):
    path = models.CharField(max_length=SEO_PATH_MAX_LENGTH, unique=True)
    kind = models.CharField(max_length=20)
    object_id = models.CharField(max_length=40)


class SeoHub(models.Model):
    path = models.CharField(max_length=SEO_PATH_MAX_LENGTH, unique=True)
    lastmod = models.DateTimeField(null=True)
    fingerprint = models.CharField(max_length=64, blank=True)
