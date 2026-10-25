from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0010_add_achievement_icon_svg"),
    ]

    operations = [
        migrations.AddField(
            model_name="privatechatsettings",
            name="mentions_only",
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name="ChatInvite",
        ),
    ]
