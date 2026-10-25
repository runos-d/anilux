from django.db import migrations, models
import django.db.models.deletion


def validate_legacy(apps, schema_editor):
    Message = apps.get_model('social', 'Message')
    invalid = Message.objects.using(schema_editor.connection.alias).filter(
        models.Q(chat__isnull=True, private_chat__isnull=True) |
        models.Q(chat__isnull=False, private_chat__isnull=False)).count()
    if invalid:
        raise RuntimeError(f'{invalid} messages have invalid chat links; run audit_chats and repair before any schema change.')


def backfill(apps, schema_editor):
    Conversation = apps.get_model('social', 'Conversation')
    Message = apps.get_model('social', 'Message')
    alias = schema_editor.connection.alias
    invalid = Message.objects.using(alias).filter(
        models.Q(chat__isnull=True, private_chat__isnull=True) |
        models.Q(chat__isnull=False, private_chat__isnull=False)).count()
    if invalid:
        raise RuntimeError(f'{invalid} messages have invalid chat links; repair them before migration. No messages were removed.')
    for model_name, field, message_field in [('PrivateChat', 'private_chat', 'private_chat'), ('GroupChat', 'group_chat', 'chat')]:
        Model = apps.get_model('social', model_name)
        for chat_id in Model.objects.using(alias).values_list('pk', flat=True).iterator(chunk_size=500):
            conversation, _ = Conversation.objects.using(alias).get_or_create(**{field + '_id': chat_id})
            seq = 0
            batch = []
            keys = set()
            messages = Message.objects.using(alias).filter(**{message_field + '_id': chat_id}).order_by('created_at', 'pk')
            for message in messages.iterator(chunk_size=500):
                seq += 1
                message.conversation_id, message.seq = conversation.pk, seq
                key = (message.sender_id, message.client_message_id)
                # Preserve pre-migration duplicates; they were separate messages.
                if not message.client_message_id or key in keys:
                    message.client_message_id = None
                keys.add(key)
                batch.append(message)
                if len(batch) == 500:
                    Message.objects.using(alias).bulk_update(batch, ['conversation', 'seq', 'client_message_id'])
                    batch = []
            if batch:
                Message.objects.using(alias).bulk_update(batch, ['conversation', 'seq', 'client_message_id'])
            Conversation.objects.using(alias).filter(pk=conversation.pk).update(next_message_seq=seq)


def consolidate_reactions(apps, schema_editor):
    Legacy = apps.get_model('social', 'Reaction')
    Reaction = apps.get_model('social', 'MessageReaction')
    Message = apps.get_model('social', 'Message')
    alias = schema_editor.connection.alias
    pending = []
    # Legacy installations may lack the unused public_id column even when
    # migration 0017 was recorded. Read only the columns needed for transfer;
    # migration 0024 repairs the absent public IDs afterwards.
    for row in Legacy.objects.using(alias).only('message_id', 'user_id', 'emoji').iterator(chunk_size=500):
        pending.append(Reaction(message_id=row.message_id, user_id=row.user_id, emoji=row.emoji))
        if len(pending) == 500:
            Reaction.objects.using(alias).bulk_create(pending, ignore_conflicts=True)
            pending = []
    if pending:
        Reaction.objects.using(alias).bulk_create(pending, ignore_conflicts=True)
    # Keep legacy rows for rollback/reference; the canonical projection uses the merged table.
    ids = Reaction.objects.using(alias).order_by().values_list('message_id', flat=True).distinct()
    for message_id in ids.iterator(chunk_size=500):
        reactions = {}
        for emoji, user_id in Reaction.objects.using(alias).filter(message_id=message_id).values_list('emoji', 'user_id'):
            reactions.setdefault(emoji, []).append(user_id)
        Message.objects.using(alias).filter(pk=message_id).update(reactions=reactions)



class Migration(migrations.Migration):
    dependencies = [('social', '0018_posthashtag_public_id')]
    operations = [
        migrations.RunPython(validate_legacy, migrations.RunPython.noop),
        migrations.CreateModel(name='Conversation', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('next_message_seq', models.PositiveBigIntegerField(default=0)),
            ('event_seq', models.PositiveBigIntegerField(default=0)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('private_chat', models.OneToOneField(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='conversation', to='social.privatechat')),
            ('group_chat', models.OneToOneField(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='conversation', to='social.groupchat')),
        ], options={'constraints': [models.CheckConstraint(condition=models.Q(private_chat__isnull=False, group_chat__isnull=True) | models.Q(private_chat__isnull=True, group_chat__isnull=False), name='conversation_exactly_one_chat')]}),
        migrations.CreateModel(name='ChatEvent', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('sequence', models.PositiveBigIntegerField()),
            ('kind', models.CharField(max_length=40)),
            ('payload', models.JSONField(default=dict)),
            ('recipients', models.JSONField(default=list)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('delivered_at', models.DateTimeField(null=True, blank=True)),
            ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='social.conversation')),
        ], options={'ordering': ['sequence'], 'constraints': [models.UniqueConstraint(fields=['conversation', 'sequence'], name='chat_event_sequence_unique')], 'indexes': [models.Index(fields=['delivered_at', 'id'], name='chat_event_pending_idx')]}),
        migrations.CreateModel(name='ConversationUserState', fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ('hidden', models.BooleanField(default=False)),
            ('cleared_through_seq', models.PositiveBigIntegerField(default=0)),
            ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_states', to='social.conversation')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
        ], options={'constraints': [models.UniqueConstraint(fields=['conversation', 'user'], name='conversation_user_unique')]}),
        migrations.AddField(model_name='message', name='conversation', field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='social.conversation')),
        migrations.AddField(model_name='message', name='version', field=models.PositiveIntegerField(default=1)),
        migrations.AddField(model_name='message', name='command_fingerprint', field=models.CharField(max_length=64, blank=True, default='')),
        migrations.AlterField(model_name='message', name='client_message_id', field=models.CharField(max_length=36, null=True, blank=True, default=None)),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(model_name='messagereaction', name='emoji', field=models.CharField(max_length=50)),
        migrations.RunPython(consolidate_reactions, migrations.RunPython.noop),
        migrations.AlterModelOptions(name='message', options={'ordering': ['seq', 'id']}),
        migrations.AddConstraint(model_name='message', constraint=models.CheckConstraint(condition=models.Q(chat__isnull=False, private_chat__isnull=True) | models.Q(chat__isnull=True, private_chat__isnull=False), name='message_exactly_one_chat')),
        migrations.AddConstraint(model_name='message', constraint=models.UniqueConstraint(fields=['conversation', 'seq'], name='message_conversation_seq_unique')),
        migrations.AddConstraint(model_name='message', constraint=models.UniqueConstraint(fields=['conversation', 'sender', 'client_message_id'], name='message_command_unique')),
        migrations.AlterUniqueTogether(name='chatfolderchat', unique_together={('folder', 'chat_type', 'chat_id')}),
    ]
