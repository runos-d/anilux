from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('social', '0034_post_post_read_scan')]
    operations = [migrations.AddField(model_name='postmedia', name='processing_progress',
                                     field=models.PositiveSmallIntegerField(default=0))]
