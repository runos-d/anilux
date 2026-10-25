# Generated migration for missing PrivateChat FKs
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatechat',
            name='user1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='private_chats_as_user1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='privatechat',
            name='user2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='private_chats_as_user2', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='privatechat',
            unique_together={('user1', 'user2')},
        ),
        migrations.AddIndex(
            model_name='privatechat',
            index=models.Index(fields=['user1', 'last_message_at'], name='social_priv_user1_i_572f69_idx'),
        ),
        migrations.AddIndex(
            model_name='privatechat',
            index=models.Index(fields=['user2', 'last_message_at'], name='social_priv_user2_i_d61c4d_idx'),
        ),
        migrations.AddIndex(
            model_name='privatechat',
            index=models.Index(fields=['user1', 'user1_pinned'], name='social_priv_user1_i_d69881_idx'),
        ),
        migrations.AddIndex(
            model_name='privatechat',
            index=models.Index(fields=['user2', 'user2_pinned'], name='social_priv_user2_i_9fcb4a_idx'),
        ),
    ]