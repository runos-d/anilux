from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0011_mentions_only_drop_chatinvite"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="message",
            index=models.Index(
                fields=["private_chat", "created_at"],
                name="social_msg_priv_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="messagereadstatus",
            index=models.Index(
                fields=["user", "message"],
                name="social_reads_user_msg_idx",
            ),
        ),
    ]
