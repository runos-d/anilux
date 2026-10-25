from django.db import migrations, models
import django.db.models.deletion


def normalize(apps, schema_editor):
    alias = schema_editor.connection.alias
    Private = apps.get_model('social', 'PrivateChat')
    Message = apps.get_model('social', 'Message')
    Topic = apps.get_model('social', 'ChatTopic')
    Group = apps.get_model('social', 'GroupChat')
    pairs = set()
    for chat in Private.objects.using(alias).all().iterator(chunk_size=500):
        pair = tuple(sorted((chat.user1_id, chat.user2_id)))
        if pair[0] == pair[1] or pair in pairs:
            raise RuntimeError('Duplicate/self private pairs require manual review; no chat was removed.')
        pairs.add(pair)
    for chat in Private.objects.using(alias).filter(user1_id__gt=models.F('user2_id')).iterator(chunk_size=500):
        updates = {'user1_id': chat.user2_id, 'user2_id': chat.user1_id}
        for field in Private._meta.fields:
            if field.name.startswith('user1_'):
                counterpart = field.name.replace('user1_', 'user2_', 1)
                updates[field.name], updates[counterpart] = getattr(chat, counterpart), getattr(chat, field.name)
        Private.objects.using(alias).filter(pk=chat.pk).update(**updates)
    for chat in Group.objects.using(alias).all().iterator(chunk_size=500):
        topics = list(Topic.objects.using(alias).filter(chat_id=chat.pk).order_by('pk'))
        by_id = {t.pk: t.pk for t in topics}
        by_anime = {t.anime_id: t.pk for t in topics if t.anime_id}
        general = next((t.pk for t in topics if t.anime_id is None), None)
        if chat.discussion_type == 'franchise' and general is None:
            general = Topic.objects.using(alias).create(chat_id=chat.pk, title=chat.name, slug='general', order=0).pk
        raw_values = list(Message.objects.using(alias).filter(chat_id=chat.pk).values_list('topic_id', flat=True).distinct())
        for raw in raw_values:
            resolved = by_id.get(raw) or by_anime.get(raw) or (general if chat.discussion_type == 'franchise' else None)
            if resolved != raw:
                Message.objects.using(alias).filter(chat_id=chat.pk, topic_id=raw).update(legacy_topic_id=raw, topic_id=resolved)
    Message.objects.using(alias).filter(private_chat__isnull=False).exclude(topic_id=None).update(
        legacy_topic_id=models.F('topic_id'), topic_id=None)


class Migration(migrations.Migration):
    dependencies = [('social', '0022_chat_folder_rules')]
    operations = [
        migrations.AddField(model_name='message', name='legacy_topic_id', field=models.IntegerField(null=True, blank=True, editable=False)),
        migrations.RunPython(normalize, migrations.RunPython.noop),
        migrations.AddConstraint(model_name='privatechat', constraint=models.CheckConstraint(
            condition=models.Q(user1__lt=models.F('user2')), name='private_chat_ordered_pair')),
        migrations.RenameField(model_name='message', old_name='topic_id', new_name='topic'),
        migrations.AlterField(model_name='message', name='topic', field=models.ForeignKey(
            null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='social.chattopic')),
    ]
