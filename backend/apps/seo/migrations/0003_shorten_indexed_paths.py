from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('seo', '0002_seohub_fingerprint')]

    operations = [
        migrations.AlterField(
            model_name='seoalias',
            name='path',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='seohub',
            name='path',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='seooverride',
            name='path',
            field=models.CharField(
                help_text='Канонический путь без query и завершающего слэша, например /anime/year/2025',
                max_length=255,
                unique=True,
            ),
        ),
    ]
