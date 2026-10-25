from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofilesettings",
            name="sakura_enabled",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="userprofilesettings",
            name="new_year_enabled",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="userprofilesettings",
            name="halloween_enabled",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="userprofilesettings",
            name="love_day_enabled",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name="userprofilesettings",
            name="accent_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
        migrations.AlterField(
            model_name="userprofilesettings",
            name="custom_background",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="fontsettings",
            name="font_weight",
            field=models.CharField(default="normal", max_length=10),
        ),
        migrations.AlterField(
            model_name="fontsettings",
            name="font_family",
            field=models.CharField(default="Inter", max_length=50),
        ),
    ]
