from django.db import migrations


def ensure_subscription(apps, schema_editor):
    model = apps.get_model('users', 'Subscription')
    if model._meta.db_table not in schema_editor.connection.introspection.table_names():
        schema_editor.create_model(model)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('users', '0007_alter_userprofilesettings_theme')]
    operations = [migrations.RunPython(ensure_subscription, migrations.RunPython.noop, atomic=False)]
