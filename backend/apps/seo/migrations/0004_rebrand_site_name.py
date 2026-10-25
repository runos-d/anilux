from django.db import migrations, models


def rebrand_default_site_name(apps, schema_editor):
    SiteSeoSettings = apps.get_model('seo', 'SiteSeoSettings')
    SiteSeoSettings.objects.filter(
        site_name__in=['Каталог аниме', 'AniSphere', 'Anisphere'],
    ).update(site_name='anilux')


class Migration(migrations.Migration):
    dependencies = [
        ('seo', '0003_shorten_indexed_paths'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteseosettings',
            name='site_name',
            field=models.CharField(default='anilux', max_length=100),
        ),
        migrations.RunPython(rebrand_default_site_name, migrations.RunPython.noop),
    ]
