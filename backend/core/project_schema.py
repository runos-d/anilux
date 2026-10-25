from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader


def project_schema_status():
    loader = MigrationLoader(connection)
    pending = [f'{app}.{name}' for app, name in loader.graph.leaf_nodes()
               if (app, name) not in loader.applied_migrations]
    missing_tables, missing_columns, missing_indexes = [], {}, {}
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
        checked = set()
        for model in apps.get_models(include_auto_created=True):
            table = model._meta.db_table
            if not model._meta.managed or model._meta.proxy or table in checked:
                continue
            checked.add(table)
            if table not in tables:
                missing_tables.append(table)
                continue
            columns = {column.name for column in connection.introspection.get_table_description(cursor, table)}
            absent = sorted({field.column for field in model._meta.local_fields} - columns)
            if absent:
                missing_columns[table] = absent
            if model._meta.indexes:
                actual = connection.introspection.get_constraints(cursor, table)
                for index in model._meta.indexes:
                    fields = [model._meta.get_field(field.lstrip('-')).column for field in index.fields]
                    if fields and not any(value.get('index') and value['columns'] == fields for value in actual.values()):
                        missing_indexes.setdefault(table, []).append(index.name)
    return {'ready': not (pending or missing_tables or missing_columns or missing_indexes),
            'pending_migrations': pending, 'missing_tables': missing_tables,
            'missing_columns': missing_columns, 'missing_indexes': missing_indexes}
