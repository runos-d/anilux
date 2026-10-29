from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import connection
from django.db.utils import ConnectionHandler
from django.http import JsonResponse


def liveness(request):
    return JsonResponse({'status': 'ok'}, headers={'Cache-Control': 'no-store'})


def readiness(request):
    states = {}
    for name, check in [('database', check_database), ('cache', check_cache), ('channels', check_channels)]:
        try:
            check()
            states[name] = 'ok'
        except Exception:
            states[name] = 'unavailable'
    ready = all(value == 'ok' for value in states.values())
    return JsonResponse({'status': 'ready' if ready else 'unavailable', 'dependencies': states},
                        status=200 if ready else 503, headers={'Cache-Control': 'no-store'})


def check_database():
    options = dict(connection.settings_dict.get('OPTIONS', {}))
    if connection.vendor == 'mysql':
        options.update(connect_timeout=1, read_timeout=1, write_timeout=1)
    probe = ConnectionHandler({'default': {**connection.settings_dict, 'OPTIONS': options, 'CONN_MAX_AGE': 0}})['default']
    try:
        with probe.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    finally:
        probe.close()


def check_cache():
    cache.set('health:probe', True, 10)
    if cache.get('health:probe') is not True:
        raise RuntimeError('Cache check failed')


def check_channels():
    async_to_sync(get_channel_layer().group_send)('health_readiness', {'type': 'health.probe'})
