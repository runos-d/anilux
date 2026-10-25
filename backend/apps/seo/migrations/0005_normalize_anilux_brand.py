from django.db import migrations, models


def normalize_public_brand(apps, schema_editor):
    SiteSeoSettings = apps.get_model('seo', 'SiteSeoSettings')
    SiteSeoSettings.objects.filter(
        site_name__in=['anilux', 'AniSphere', 'Anisphere'],
    ).update(site_name='AniLux')


class Migration(migrations.Migration):
    dependencies = [
        ('seo', '0004_rebrand_site_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteseosettings',
            name='site_name',
            field=models.CharField(default='AniLux', max_length=100),
        ),
        migrations.RunPython(normalize_public_brand, migrations.RunPython.noop),
    ]
