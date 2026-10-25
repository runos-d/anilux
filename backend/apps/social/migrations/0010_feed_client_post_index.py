from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('social', '0006_add_client_post_id')]
    operations = [
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['client_post_id', 'status'], name='social_post_client_status'),
        ),
    ]
