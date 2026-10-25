# Generated manually for the ideas board.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Idea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("description", models.TextField(max_length=5000)),
                ("kind", models.CharField(choices=[("idea", "Идея"), ("bug", "Ошибка"), ("improvement", "Улучшение")], default="idea", max_length=20)),
                ("status", models.CharField(choices=[("pending", "Ожидает"), ("planned", "Запланировано"), ("in_progress", "В процессе"), ("review", "На проверке"), ("done", "Готово"), ("declined", "Отклонено")], default="pending", max_length=20)),
                ("priority", models.CharField(choices=[("low", "Низкий"), ("normal", "Обычный"), ("high", "Высокий"), ("critical", "Критический")], default="normal", max_length=20)),
                ("admin_note", models.TextField(blank=True, max_length=2000)),
                ("votes_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ideas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="IdeaVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("idea", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="ideas.idea")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="idea_votes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name="idea",
            index=models.Index(fields=["status", "-created_at"], name="ideas_status_created_idx"),
        ),
        migrations.AddIndex(
            model_name="idea",
            index=models.Index(fields=["kind", "-created_at"], name="ideas_kind_created_idx"),
        ),
        migrations.AddConstraint(
            model_name="ideavote",
            constraint=models.UniqueConstraint(fields=("idea", "user"), name="unique_idea_vote"),
        ),
    ]
