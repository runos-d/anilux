from hashlib import sha256

from django.db import migrations, models


def hash_endpoints(apps, schema_editor):
    subscriptions = apps.get_model('notifications', 'PushSubscription')
    alias = schema_editor.connection.alias
    for subscription in subscriptions.objects.using(alias).only('pk', 'endpoint').iterator(chunk_size=500):
        subscriptions.objects.using(alias).filter(pk=subscription.pk).update(
            endpoint_hash=sha256(subscription.endpoint.encode('utf-8')).hexdigest(),
        )


class Migration(migrations.Migration):
    dependencies = [('notifications', '0004_rename_ep_sub_user_active_idx_notificatio_user_id_f43898_idx_and_more')]
    operations = [
        migrations.AddField(
            model_name='pushsubscription', name='endpoint_hash',
            field=models.CharField(max_length=64, unique=True, null=True, editable=False),
        ),
        migrations.RunPython(hash_endpoints, migrations.RunPython.noop),
        migrations.RemoveIndex(model_name='pushsubscription', name='notificatio_endpoin_498a4c_idx'),
        migrations.AlterField(model_name='pushsubscription', name='endpoint', field=models.TextField()),
        migrations.AlterField(
            model_name='pushsubscription', name='endpoint_hash',
            field=models.CharField(max_length=64, unique=True, editable=False),
        ),
    ]
