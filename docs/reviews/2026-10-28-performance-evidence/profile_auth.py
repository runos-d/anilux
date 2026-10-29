import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','load_settings')
import django
django.setup()
import cProfile,pstats,io,time,json
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from apps.users.infrastructure.models.users import ActiveSession
row=ActiveSession.objects.select_related('user').first()
token=AccessToken.for_user(row.user);token['sid']=str(row.pk);token['ver']=row.user.token_version
client=APIClient();header={'HTTP_AUTHORIZATION':'Bearer '+str(token)}
client.get('/api/anime/?page_size=20',**header)
profile=cProfile.Profile();times=[]
with CaptureQueriesContext(connection) as queries:
 profile.enable()
 for i in range(10):
  start=time.perf_counter();response=client.get('/api/anime/?page_size=20',**header);times.append(round((time.perf_counter()-start)*1000,2))
 profile.disable()
print('PROFILE_JSON='+json.dumps({'ms':times,'sql':len(queries),'status':response.status_code}))
output=io.StringIO();pstats.Stats(profile,stream=output).sort_stats('cumtime').print_stats(25);print(output.getvalue())
