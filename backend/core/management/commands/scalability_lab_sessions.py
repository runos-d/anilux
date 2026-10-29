"""Provision server-bound synthetic sessions without printing credentials."""
import json
import os
from datetime import timedelta
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone


class Command(BaseCommand):
    help = 'Write synthetic lab sessions to its private volume, never stdout'

    def handle(self, **options):
        if connection.settings_dict['HOST'] != 'lab-mysql' or connection.settings_dict['NAME'] != 'scalability_lab':
            raise CommandError('Only lab-mysql/scalability_lab is allowed')
        from apps.users.infrastructure.models.users import User, ActiveSession
        from rest_framework_simplejwt.tokens import AccessToken
        target = Path('/lab-data/load-users.json')
        if target.exists():
            raise CommandError('Session fixture already exists; refusing to overwrite it')
        rows = []
        with transaction.atomic():
            for user in User.objects.filter(username__startswith='load-user-').order_by('pk')[:10000]:
                session = SessionStore()
                session['_auth_user_id'] = str(user.pk)
                session['_auth_user_hash'] = user.get_session_auth_hash()
                session.set_expiry(12 * 3600)
                session.create()
                active, _ = ActiveSession.objects.get_or_create(user=user, session_key=session.session_key,
                    defaults={'ip_address': '127.0.0.1', 'user_agent': 'disposable-scalability-lab'})
                token = AccessToken.for_user(user)
                token.set_exp(lifetime=timedelta(hours=12))
                token['sid'], token['ver'] = str(active.pk), user.token_version
                rows.append({'user_id': user.pk, 'access': str(token)})
            if not rows:
                raise CommandError('Seed synthetic lab users first')
            # Exclusive creation avoids clobbering a fixture used by another run.
            with os.fdopen(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
                json.dump({'identity': 'scalability-disposable-lab', 'users': rows}, output)
        self.stdout.write(json.dumps({'synthetic_sessions': len(rows), 'credentials_printed': False}))
