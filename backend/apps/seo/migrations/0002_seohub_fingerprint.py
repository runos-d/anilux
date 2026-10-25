from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('seo', '0001_initial')]
    operations = [migrations.AddField(model_name='seohub', name='fingerprint', field=models.CharField(max_length=64, blank=True))]
