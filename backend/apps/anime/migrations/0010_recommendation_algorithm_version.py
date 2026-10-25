from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('anime', '0009_calendarrelease')]
    operations = [migrations.AddField(
        model_name='recommendationsnapshot', name='algorithm_version',
        field=models.PositiveIntegerField(default=0))]
