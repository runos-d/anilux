from django.db import migrations, models
import apps.users.infrastructure.profile_storage


class Migration(migrations.Migration):
    dependencies = [('users', '0013_privacy_consent_exports_activity_summary')]
    operations = [
        migrations.AddField(model_name='user', name='token_version', field=models.PositiveIntegerField(default=0)),
        migrations.AlterField(model_name='user', name='avatar', field=models.ImageField(blank=True, null=True, upload_to='avatars/', storage=apps.users.infrastructure.profile_storage.ProfileStorage())),
        migrations.AlterField(model_name='userprofilesettings', name='avatar', field=models.ImageField(blank=True, null=True, upload_to='avatars/', storage=apps.users.infrastructure.profile_storage.ProfileStorage())),
    ]
