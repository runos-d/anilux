# Generated migration for missing GroupChat FKs
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('anime', '0001_initial'),
        ('social', '0002_add_privatechat_fks'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupchat',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_group_chats', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupchat',
            name='anime',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chats', to='anime.anime'),
        ),
    ]