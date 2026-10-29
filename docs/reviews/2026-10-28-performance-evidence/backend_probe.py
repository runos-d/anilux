"""Run only in disposable performance_settings Docker database after migrate."""
import os
print('stage: django setup', flush=True)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'performance_settings')
import django
django.setup()
import json
import time
import statistics
from unittest.mock import patch
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.anime.models import Anime, Franchise
from apps.users.infrastructure.models.users import User, PrivacySettings

disposable_mysql = settings.DATABASES['default'].get('HOST') == 'audit-mysql' and settings.DATABASES['default']['NAME'] == 'chat_test'
memory_sqlite = connection.vendor == 'sqlite' and settings.DATABASES['default']['NAME'] == ':memory:'
assert disposable_mysql or memory_sqlite
import config.urls  # register late models before probing
print('stage: create isolated schema', flush=True)
if memory_sqlite:
    from audit_runner import AuditRunner
    AuditRunner().setup_databases()

if not Anime.objects.exists():
    print('stage: seed 10000 anime', flush=True)
    Franchise.objects.bulk_create([Franchise(name=f'Франшиза {i}', slug=f'franchise-{i}') for i in range(30)])
    franchises = list(Franchise.objects.values_list('pk', flat=True))
    Anime.objects.bulk_create([Anime(title_ru=f'Тест каталога {i}', slug=f'test-{i}',
        shikimori_id=i + 1, is_available=True, has_cyrillic=True, year=2024,
        score=8, kind='tv', episodes=12, status='released',
        franchise_id=franchises[i // 10] if i < 300 else None,
        poster_url='https://example.test/poster.jpg') for i in range(10000)], batch_size=500)
    User.objects.bulk_create([User(username=f'probe-{i}',email=f'probe-{i}@example.test',password='!') for i in range(101)])
    users = list(User.objects.all())
    PrivacySettings.objects.bulk_create([PrivacySettings(user=user, who_can_see_profile_photo='contacts') for user in users], ignore_conflicts=True)
user = User.objects.first()
client = APIClient()
client.raise_request_exception = False
measurements = []

def measure(label, path, runs=1):
    print('stage: measure '+path, flush=True)
    timings, counts, statuses, sizes = [], [], [], []
    for _ in range(runs):
        start = time.perf_counter()
        with CaptureQueriesContext(connection) as queries:
            response = client.get(path)
            if hasattr(response, 'render'):
                response.render()
        timings.append(round((time.perf_counter()-start)*1000,2))
        counts.append(len(queries))
        statuses.append(response.status_code)
        sizes.append(len(response.content))
    measurements.append({'label':label,'path':path,'ms':timings,'sql':counts,'status':statuses,'bytes':sizes})
    print('MEASURE='+json.dumps(measurements[-1],ensure_ascii=False),flush=True)

cache.clear()
with patch('apps.anime.presentation.views.anime_views.legacy_anime_slug', return_value='never-match') as slug:
    measure('unknown anime slug', '/api/anime/not-an-anime/')
    measurements[-1]['python_slug_calls'] = slug.call_count
with patch('apps.anime.presentation.views.anime_views.anime_service.search_by_shikimori_id', return_value=None) as provider:
    measure('detail with missing screenshots', f'/api/anime/{Anime.objects.first().pk}/', 3)
    measurements[-1]['provider_calls'] = provider.call_count
for path in ['/api/anime/?page_size=20','/api/anime/?page_size=500','/api/anime/franchises/?page_size=20',
             '/api/anime/franchises/?page_size=0','/api/anime/franchises/?page=-1','/api/anime/franchises/?page_size=abc']:
    measure('catalog or franchises',path,2)
client.force_authenticate(user)
measure('contact-only avatars search', '/api/users/search/?search=probe')
with patch('core.online_status.online_status.get_online_users', return_value=[{'user_id':pk} for pk in User.objects.values_list('pk',flat=True)]):
    measure('online projection', '/api/users/online/')

if disposable_mysql:
    from core.online_status import online_status
    redis = online_status._get_client()
    pipeline = redis.pipeline()
    for i in range(1000):
        pipeline.setex(f'user_online:{i}',120,json.dumps({'user_id':i,'username':f'probe-{i}'}))
        pipeline.zadd('presence:index:v1', {f'user_online:{i}': time.time()+120})
    pipeline.execute()
    before = redis.info('commandstats')
    start=time.perf_counter(); online_status.get_online_users(); elapsed=round((time.perf_counter()-start)*1000,2)
    after = redis.info('commandstats')
    measurements.append({'label':'online Redis 1000','ms':elapsed,'commands':{k:after[k]['calls']-before.get(k,{}).get('calls',0) for k in after if after[k]['calls']-before.get(k,{}).get('calls',0)>0}})
print('AUDIT_JSON='+json.dumps(measurements,ensure_ascii=False),flush=True)
