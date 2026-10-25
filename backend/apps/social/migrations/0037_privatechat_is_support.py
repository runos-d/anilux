from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0036_alter_messageattachment_content_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="privatechat",
            name="is_support",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
