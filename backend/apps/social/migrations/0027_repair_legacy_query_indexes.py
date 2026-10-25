from django.db import migrations


def repair_indexes(apps, schema_editor):
    required = {'Post': {'social_post_created_3ab9d6_idx'},
                'Message': {'social_mess_chat_id_14946a_idx', 'social_mess_private_541ee8_idx'}}
    for name, names in required.items():
        model = apps.get_model('social', name)
        with schema_editor.connection.cursor() as cursor:
            existing = schema_editor.connection.introspection.get_constraints(cursor, model._meta.db_table)
        for index in model._meta.indexes:
            if index.name not in names:
                continue
            columns = [model._meta.get_field(field.lstrip('-')).column for field in index.fields]
            if not any(value.get('index') and value['columns'] == columns for value in existing.values()):
                schema_editor.add_index(model, index)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('social', '0026_repair_legacy_public_ids')]
    operations = [migrations.RunPython(repair_indexes, migrations.RunPython.noop, atomic=False)]
