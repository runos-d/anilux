from django.db import migrations,models
class Migration(migrations.Migration):
    dependencies=[("social","0005_antispamrule_chat_attachment_message_bookmark_post_and_more")]
    operations=[migrations.AddField(model_name="post",name="client_post_id",field=models.CharField(blank=True,db_index=True,default="",max_length=36),preserve_default=False)]
