from django.db import migrations, models
import django.db.models.deletion
from apps.social.infrastructure.models.chat_cascade import chat_cascade


class Migration(migrations.Migration):
    dependencies = [('social', '0020_conversation_lifecycle')]
    operations = [
        migrations.AlterField(model_name='conversation', name='private_chat', field=models.OneToOneField(
            null=True, blank=True, on_delete=chat_cascade, related_name='conversation', to='social.privatechat')),
        migrations.AlterField(model_name='conversation', name='group_chat', field=models.OneToOneField(
            null=True, blank=True, on_delete=chat_cascade, related_name='conversation', to='social.groupchat')),
        migrations.AlterField(model_name='message', name='chat', field=models.ForeignKey(
            null=True, blank=True, on_delete=chat_cascade, related_name='group_messages', to='social.groupchat')),
        migrations.AlterField(model_name='message', name='private_chat', field=models.ForeignKey(
            null=True, blank=True, on_delete=chat_cascade, related_name='private_messages', to='social.privatechat')),
        migrations.AddField(model_name='chatjoinrequest', name='invite', field=models.ForeignKey(
            null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
            related_name='join_requests', to='social.chatinvitelink')),
    ]
