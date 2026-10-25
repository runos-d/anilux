from django.conf import settings
from django.db import models


class Idea(models.Model):
    class Kind(models.TextChoices):
        IDEA = "idea", "Идея"
        BUG = "bug", "Ошибка"
        IMPROVEMENT = "improvement", "Улучшение"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        PLANNED = "planned", "Запланировано"
        IN_PROGRESS = "in_progress", "В процессе"
        REVIEW = "review", "На проверке"
        DONE = "done", "Готово"
        DECLINED = "declined", "Отклонено"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        NORMAL = "normal", "Обычный"
        HIGH = "high", "Высокий"
        CRITICAL = "critical", "Критический"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ideas",
    )
    title = models.CharField(max_length=140)
    description = models.TextField(max_length=5000)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.IDEA)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    admin_note = models.TextField(max_length=2000, blank=True)
    votes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="ideas_status_created_idx"),
            models.Index(fields=["kind", "-created_at"], name="ideas_kind_created_idx"),
        ]

    def __str__(self):
        return self.title


class IdeaVote(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="idea_votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["idea", "user"], name="unique_idea_vote"),
        ]
