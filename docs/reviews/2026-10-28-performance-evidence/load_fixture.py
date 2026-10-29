import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'load_settings')
import django
django.setup()
from django.conf import settings
assert settings.DATABASES['default']['HOST'] == 'audit-mysql' and settings.DATABASES['default']['NAME'] == 'chat_test'
from apps.anime.models import Anime
if not Anime.objects.exists():
    import backend_probe
import json
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from django.conf import settings
from apps.users.infrastructure.models.users import User
from apps.users.application.token_sessions import issue_refresh
from apps.anime.models import BackgroundJob, Anime
from apps.anime.presentation.views.prepared_downloads import job_file

import secrets
from datetime import timedelta
from django.utils import timezone
from django.contrib.sessions.models import Session
from apps.users.infrastructure.models.users import ActiveSession
from rest_framework_simplejwt.tokens import AccessToken
users = list(User.objects.order_by('pk')[:100])
sessions = []
for user in users:
    key = secrets.token_hex(16)
    sessions.append(Session(session_key=key, expire_date=timezone.now()+timedelta(hours=24), session_data=SessionStore().encode({
        '_auth_user_id': str(user.pk), '_auth_user_hash': user.get_session_auth_hash(),
        '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend',
    })))
Session.objects.bulk_create(sessions)
ActiveSession.objects.bulk_create([ActiveSession(user=user,session_key=session.session_key,ip_address='127.0.0.1',user_agent='isolated-load') for user,session in zip(users,sessions)])
selectors = dict(ActiveSession.objects.filter(session_key__in=[s.session_key for s in sessions]).values_list('session_key','pk'))
tokens=[]
for user, session in zip(users, sessions):
    access=AccessToken.for_user(user); access['sid']=str(selectors[session.session_key]); access['ver']=user.token_version
    tokens.append({'user_id':user.pk,'access':str(access)})
job, _ = BackgroundJob.objects.update_or_create(key='load-range-fixture', defaults={'kind':'download','status':'ready',
    'payload':{'anime_id':Anime.objects.first().pk,'format':'mp4','episode':1},'result':{'bytes':10}})
job_file(job).parent.mkdir(parents=True, exist_ok=True)
job_file(job).write_bytes(b'0123456789')
print('TOKENS=' + json.dumps({'tokens': tokens, 'download': f'/api/anime/{job.payload["anime_id"]}/stream/?job_id={job.pk}'}), flush=True)
