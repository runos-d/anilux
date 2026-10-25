from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("anime", "0013_anime_franchise_manual_catalogvisibility_and_more"),
        ("notifications", "0008_complaint_moderation_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="reminder",
            name="franchise",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reminders",
                to="anime.franchise",
            ),
        ),
    ]
