"""Audit-only entrypoint; never imported by the application deployment."""
import json
import resource
import threading
import time
from asgiref.sync import sync_to_async
from config.asgi import application as base
from apps.users.application import token_sessions
import requests

def disabled_http(*args, **kwargs):
    raise RuntimeError('External HTTP disabled in isolated audit app')
requests.sessions.Session.request = disabled_http

lock = threading.Lock()
validations = 0
original_validate = token_sessions.validate_token_session
def validate(*args, **kwargs):
    global validations
    with lock:
        validations += 1
    return original_validate(*args, **kwargs)
token_sessions.validate_token_session = validate


async def application(scope, receive, send):
    if scope['type'] != 'http' or not scope['path'].startswith('/__audit_'):
        return await base(scope, receive, send)
    if scope['path'] == '/__audit_identity':
        data = {'audit': 'animecore-fix-verification'}
    elif scope['path'] == '/__audit_metrics':
        data = {'session_validations': validations, 'max_rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                'threads': threading.active_count(), 'cpu_seconds': time.process_time()}
    elif scope['path'] == '/__audit_event':
        body = b''
        while True:
            message = await receive()
            body += message.get('body', b'')
            if len(body) > 2048:
                raise ValueError('Audit body limit')
            if not message.get('more_body'):
                break
        data = json.loads(body)
        from core.redis_events import event_publisher
        await sync_to_async(event_publisher.publish_event, thread_sensitive=False)(
            'audit_probe', {'sequence': data['sequence']}, target_users=[data['target']])
        data = {'ok': True}
    else:
        data = {'unknown': True}
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': json.dumps(data).encode()})
