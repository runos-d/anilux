from django.db import models
from django.conf import settings


class News(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Обычная"),
        ("important", "Важная"),
        ("hot", "Горячая"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="news_posts",
        verbose_name="Автор",
    )
    title = models.CharField(max_length=500, verbose_name="Заголовок")
    summary = models.CharField(max_length=1000, blank=True, verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Содержимое")
    cover_url = models.URLField(blank=True, verbose_name="URL обложки")
    cover_file = models.ImageField(
        upload_to="news/covers/", null=True, blank=True, verbose_name="Файл обложки"
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="low", verbose_name="Приоритет"
    )
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплено")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "social_news"
        ordering = ["-is_pinned", "-created_at"]
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

    def __str__(self):
        return self.title