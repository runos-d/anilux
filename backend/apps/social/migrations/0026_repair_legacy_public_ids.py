import copy
import secrets

from django.db import migrations, models, transaction
from django.core.exceptions import FieldDoesNotExist


def repair_public_ids(apps, schema_editor):
    connection = schema_editor.connection
    alias = connection.alias
    tables = set(connection.introspection.table_names())
    repairs = []
    for model in apps.get_app_config('social').get_models():
        try:
            field = model._meta.get_field('public_id')
        except FieldDoesNotExist:
            continue
        if field.null or not field.unique or model._meta.db_table not in tables:
            continue
        with connection.cursor() as cursor:
            columns = {column.name: column for column in connection.introspection.get_table_description(cursor, model._meta.db_table)}
            constraints = connection.introspection.get_constraints(cursor, model._meta.db_table)
        if field.column not in columns:
            raise RuntimeError(f'{model._meta.db_table}.{field.column} is missing; repair migration 0024 first.')
        old = copy.copy(field)
        old.null = columns[field.column].null_ok
        old._unique = any(value['unique'] and value['columns'] == [field.column] for value in constraints.values())
        # Validate every table before changing any row. Never replace an ID
        # that may already be used in URLs, bookmarks or external references.
        duplicates = model.objects.using(alias).exclude(public_id=None).order_by().values('public_id').annotate(total=models.Count('pk')).filter(total__gt=1)
        if duplicates.exists():
            raise RuntimeError(f'{model._meta.db_table} has duplicate public IDs; no ID was replaced.')
        if old.null or not old.unique:
            repairs.append((model, old, field))

    for model, old, field in repairs:
        used = set(model.objects.using(alias).exclude(public_id=None).values_list('public_id', flat=True))
        with transaction.atomic(using=alias):
            while rows := list(model.objects.using(alias).filter(public_id=None).only('pk', 'public_id').order_by('pk')[:500]):
                for row in rows:
                    candidate = 10000000 + secrets.randbelow(90000000)
                    while candidate in used:
                        candidate = 10000000 + secrets.randbelow(90000000)
                    used.add(candidate)
                    row.public_id = candidate
                model.objects.using(alias).bulk_update(rows, ['public_id'], batch_size=500)
        # Introspection makes this operation resumable after non-atomic MySQL
        # DDL failures, including when the column was already corrected.
        schema_editor.alter_field(model, old, field)


class Migration(migrations.Migration):
    dependencies = [('social', '0025_chat_privacy_and_backups')]
    operations = [migrations.RunPython(repair_public_ids, migrations.RunPython.noop, atomic=False)]
