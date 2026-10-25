from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('playlists', '0005_refine_topics_and_cover_mode')]

    operations = [
        migrations.AddIndex(
            model_name='playlist',
            index=models.Index(fields=['visibility', '-created_at'], name='pl_vis_created_idx'),
        ),
        migrations.AddIndex(
            model_name='playlist',
            index=models.Index(fields=['visibility', '-updated_at'], name='pl_vis_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='playlist',
            index=models.Index(fields=['user', '-created_at'], name='pl_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='playlistitem',
            index=models.Index(fields=['playlist', 'position', 'added_at'], name='pl_item_order_idx'),
        ),
    ]
