from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('anime', '0007_recommendationsnapshot_catalog_revision_and_more')]
    operations = [migrations.AddField(model_name='anime', name='franchise_checked_at',
                                     field=models.DateTimeField(blank=True, null=True, db_index=True))]
