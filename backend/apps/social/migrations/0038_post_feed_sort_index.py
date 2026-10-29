from django.db import migrations, models
from django.db.models.functions import Coalesce


class Migration(migrations.Migration):
    dependencies = [('social', '0037_privatechat_is_support')]
    operations = [
        migrations.AddField(model_name='post', name='feed_sort_at', field=models.GeneratedField(
            expression=Coalesce('published_at', 'created_at'), output_field=models.DateTimeField(), db_persist=True)),
        migrations.AddIndex(model_name='post', index=models.Index(
            fields=['is_deleted', 'feed_sort_at', 'id', 'status', 'visibility', 'author', 'group', 'post_type', 'is_pinned'],
            name='post_feed_date_scan')),
    ]
