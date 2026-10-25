# Fix missing public_id in PostHashtag (UUIDv8Model requires it)
from django.db import migrations, models

def generate_public_id():
    import secrets
    return secrets.randbelow(90000000) + 10000000

class Migration(migrations.Migration):
    dependencies = [
        ('social', '0017_alter_message_options_and_more'),
    ]
    operations = [
        # 0017 already creates this column. Only its state options differ.
        migrations.AlterField(
            model_name='posthashtag',
            name='public_id',
            field=models.PositiveBigIntegerField(
                blank=True, db_index=True, null=True, unique=True,
            ),
            preserve_default=False,
        ),
    ]
