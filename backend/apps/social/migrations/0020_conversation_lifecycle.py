from django.db import migrations, models
import django.db.models.deletion


def link_folders(apps, schema_editor):
    Item = apps.get_model('social', 'ChatFolderChat')
    Conversation = apps.get_model('social', 'Conversation')
    for item in Item.objects.all().iterator(chunk_size=500):
        field = 'private_chat' if item.chat_type == 'private' else 'group_chat'
        chat_model = apps.get_model('social', 'PrivateChat' if field == 'private_chat' else 'GroupChat')
        chat = chat_model.objects.filter(public_id=item.chat_id).first() or chat_model.objects.filter(pk=item.chat_id).first()
        if chat:
            conv = Conversation.objects.get(**{field + '_id': chat.pk})
            Item.objects.filter(pk=item.pk).update(conversation_id=conv.pk, chat_id=chat.public_id)


class Migration(migrations.Migration):
    dependencies = [('social', '0019_conversation_core')]
    operations = [
        migrations.AlterField(model_name='chatevent', name='conversation', field=models.ForeignKey(
            null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='social.conversation')),
        migrations.AddField(model_name='chatfolderchat', name='conversation', field=models.ForeignKey(
            blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='folder_items', to='social.conversation')),
        migrations.AddField(model_name='chatfolder', name='include_channels', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='chatfolder', name='include_muted', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='chatfolder', name='match_all', field=models.BooleanField(default=False)),
        migrations.RunPython(link_folders, migrations.RunPython.noop),
    ]
