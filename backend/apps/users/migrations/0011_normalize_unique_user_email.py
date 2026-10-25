from django.db import migrations, models
from django.db.models.functions import Lower


def normalize_existing_emails(apps, schema_editor):
    User = apps.get_model("users", "User")
    duplicates = list(
        User.objects.exclude(email__isnull=True)
        .exclude(email="")
        .annotate(normalized=Lower("email"))
        .values("normalized")
        .annotate(total=models.Count("id"))
        .filter(total__gt=1)
        .values_list("normalized", flat=True)[:20]
    )
    if duplicates:
        raise RuntimeError(
            "Cannot enforce unique user emails; resolve case-insensitive duplicates first: "
            + ", ".join(duplicates)
        )

    User.objects.filter(email="").update(email=None)
    for user in User.objects.exclude(email__isnull=True).iterator(chunk_size=500):
        normalized = user.email.strip().lower()
        User.objects.filter(pk=user.pk).update(email=normalized or None)


class Migration(migrations.Migration):
    dependencies = [("users", "0010_transactional_email_delivery")]

    operations = [
        migrations.RunPython(normalize_existing_emails, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                blank=True,
                max_length=254,
                null=True,
                unique=True,
                verbose_name="email address",
            ),
        ),
    ]
