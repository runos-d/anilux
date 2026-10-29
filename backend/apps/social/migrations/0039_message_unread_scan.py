from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('social', '0038_post_feed_sort_index')]

    operations = [migrations.AddIndex(
        model_name='message',
        index=models.Index(fields=['conversation', 'is_deleted', 'seq', 'sender', 'created_at'],
                           name='message_unread_scan'),
    )]
