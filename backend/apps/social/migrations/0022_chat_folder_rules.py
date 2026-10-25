from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('social', '0021_chat_cascade_and_join_invite')]
    operations = [
        migrations.AddField(model_name='chatfolder', name='rules', field=models.JSONField(default=dict, blank=True)),
        migrations.AlterField(model_name='message', name='conversation', field=models.ForeignKey(
            on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='social.conversation')),
    ]
