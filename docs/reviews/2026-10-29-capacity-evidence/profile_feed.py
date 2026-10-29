"""Read-only timing on the disposable 60,000-post fixture; never prints SQL/tokens."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capacity_settings')
import django
django.setup()
from django.conf import settings
assert settings.DATABASES['default']['HOST'] == 'audit-mysql' and settings.DATABASES['default']['NAME'] == 'chat_test'
import config.urls
import json,time
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient
from apps.users.infrastructure.models.users import User
client = APIClient()
client.force_authenticate(User.objects.filter(username__startswith='capacity-load-').order_by('pk').first())
results=[]
for path in ['/api/social/feed/?page_size=20','/api/social/feed/?page_size=20&include_count=false',
             '/api/social/feed/weighted/?page_size=20&include_count=false']:
 client.get(path)
 timings=[]
 for _ in range(5):
  start=time.perf_counter()
  with CaptureQueriesContext(connection) as queries:response=client.get(path)
  assert response.status_code==200
  timings.append((time.perf_counter()-start)*1000)
 results.append({'path':path,'milliseconds':timings,'queries':len(queries),
  'sql_ms':sum(float(q['time']) for q in queries.captured_queries)*1000,
  'slowest_sql_ms':sorted((float(q['time'])*1000 for q in queries.captured_queries),reverse=True)[:8]})
print(json.dumps({'posts':60000,'results':results}))
