# Generated migration for missing Message FKs
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social', '0003_add_groupchat_fks'),
        ('anime', '0001_initial'),
        ('playlists', '0001_initial'),
        ('reactor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group_messages', to='social.groupchat'),
        ),
        migrations.AddField(
            model_name='message',
            name='private_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='private_messages', to='social.privatechat'),
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='shared_post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shared_in_messages', to='social.post'),
        ),
        migrations.AddField(
            model_name='message',
            name='shared_anime',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shared_in_messages', to='anime.anime'),
        ),
        migrations.AddField(
            model_name='message',
            name='shared_playlist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shared_in_messages', to='playlists.playlist'),
        ),
        migrations.AddField(
            model_name='message',
            name='shared_shorts',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shared_in_messages', to='reactor.reactorpost'),
        ),
        migrations.AddField(
            model_name='message',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_messages', to=settings.AUTH_USER_MODEL),
        ),
    ]