from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0002_complaint_assigned_to_complaint_complainant_and_more'),
    ]
    operations = [
        # N1 dedupe
        migrations.AddField(
            model_name='notification',
            name='dedupe_key',
            field=models.CharField(max_length=255, blank=True, db_index=True, default=''),
        ),
        # N7 timezone per user
        migrations.AddField(
            model_name='notificationsetting',
            name='timezone',
            field=models.CharField(max_length=50, blank=True, default='UTC'),
        ),
        # N6 push subscriptions
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Bootstrap with an indexable column on MySQL. 0005 expands
                # this to TEXT and moves uniqueness to a full endpoint hash.
                ('endpoint', models.CharField(max_length=191, unique=True)),
                ('p256dh', models.TextField(blank=True)),
                ('auth', models.TextField(blank=True)),
                ('user_agent', models.CharField(max_length=255, blank=True)),
                ('device_name', models.CharField(max_length=255, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_active', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_subscriptions', to='users.User')),
            ],
            options={
                'ordering': ['-last_active'],
                'indexes': [models.Index(fields=['user', 'is_active'], name='push_user_active_idx'), models.Index(fields=['endpoint'], name='push_endpoint_idx')],
            },
        ),
        # N8 episode subscription (reminder-btn series tracker)
        migrations.CreateModel(
            name='EpisodeSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episode_subs', to='users.User')),
                ('anime', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episode_subs', to='anime.Anime')),
                ('is_active', models.BooleanField(default=True)),
                ('is_paused', models.BooleanField(default=False)),
                ('paused_until', models.DateTimeField(null=True, blank=True)),
                ('last_notified_episode', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': (('user', 'anime'),),
                'indexes': [models.Index(fields=['user', 'is_active'], name='ep_sub_user_active_idx'), models.Index(fields=['anime', 'is_active'], name='ep_sub_anime_active_idx')],
            },
        ),
    ]
