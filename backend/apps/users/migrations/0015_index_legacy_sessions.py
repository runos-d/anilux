from django.db import migrations
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone


def index_sessions(apps, schema_editor):
    Session = apps.get_model('sessions', 'Session')
    ActiveSession = apps.get_model('users', 'ActiveSession')
    User = apps.get_model('users', 'User')
    db = schema_editor.connection.alias
    store = SessionStore()
    batch = []
    for session in Session.objects.using(db).filter(expire_date__gt=timezone.now()).iterator(chunk_size=500):
        owner = store.decode(session.session_data).get('_auth_user_id')
        if owner and str(owner).isdigit():
            batch.append((session.session_key, int(owner)))
        if len(batch) >= 500:
            save_batch(ActiveSession, User, db, batch)
            batch = []
    save_batch(ActiveSession, User, db, batch)


def save_batch(ActiveSession, User, db, batch):
    valid = set(User.objects.using(db).filter(pk__in=[owner for _, owner in batch]).values_list('pk', flat=True))
    ActiveSession.objects.using(db).bulk_create([
        ActiveSession(session_key=key, user_id=owner, ip_address='127.0.0.1', user_agent='')
        for key, owner in batch if owner in valid
    ], ignore_conflicts=True, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [('users', '0014_token_version_profile_storage'), ('sessions', '0001_initial')]
    operations = [migrations.RunPython(index_sessions, migrations.RunPython.noop)]
