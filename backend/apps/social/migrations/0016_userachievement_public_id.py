# Fix missing public_id in UserAchievement (UUIDv8Model requires it)
from django.db import migrations, models

def generate_public_id():
    import secrets
    return secrets.randbelow(90000000) + 10000000

class Migration(migrations.Migration):
    dependencies = [
        ('social', '0015_merge_20261008_2002'),
    ]
    operations = [
        migrations.AddField(
            model_name='userachievement',
            name='public_id',
            field=models.PositiveBigIntegerField(
                blank=True, db_index=True, null=True, unique=True,
                default=generate_public_id,
            ),
            preserve_default=False,
        ),
    ]
