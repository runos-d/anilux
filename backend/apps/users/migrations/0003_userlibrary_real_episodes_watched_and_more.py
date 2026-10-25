from django.db import migrations, models


def _column_exists(schema_editor, table, column):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table)
    return any(col.name == column for col in description)


def add_userlibrary_columns_if_missing(apps, schema_editor):
    UserLibrary = apps.get_model("users", "UserLibrary")
    table = UserLibrary._meta.db_table
    columns = (
        ("real_episodes_watched", models.IntegerField(default=0)),
        ("user_set_status", models.BooleanField(default=False)),
    )
    for name, field in columns:
        if _column_exists(schema_editor, table, name):
            continue
        field.set_attributes_from_name(name)
        schema_editor.add_field(UserLibrary, field)


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_appearance_settings'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_userlibrary_columns_if_missing,
                    migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='userlibrary',
                    name='real_episodes_watched',
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name='userlibrary',
                    name='user_set_status',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
        migrations.AlterField(
            model_name='userprofilesettings',
            name='theme',
            field=models.CharField(
                choices=[
                    ('light', 'Светлая'),
                    ('dark', 'Тёмная'),
                    ('system', 'Как в системе'),
                    ('blue', 'Синяя'),
                    ('green', 'Зелёная'),
                    ('red', 'Красная'),
                    ('yellow', 'Жёлтая'),
                    ('banana', 'Банановая'),
                    ('sea', 'Морская'),
                    ('lilac', 'Сиренёвая'),
                    ('emerald', 'Изумрудная'),
                    ('peach', 'Персиковая'),
                    ('blueberry', 'Черничная'),
                    ('custom', 'Своя тема'),
                ],
                default='dark',
                max_length=20,
            ),
        ),
    ]
