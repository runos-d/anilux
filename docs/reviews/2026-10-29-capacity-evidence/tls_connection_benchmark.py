"""Connection-only A/B on the disposable database; no user data or credentials printed."""
import json
import time

import django

django.setup()
from django.db import connection
from pymysql.connections import Connection
from core.mysql_tls import CachedTLSConnection, reset_default_context

assert connection.settings_dict['HOST'] == 'audit-mysql'
assert connection.settings_dict['NAME'] == 'chat_test'
params = connection.get_connection_params()
results = []
for driver in (Connection, CachedTLSConnection):
    reset_default_context()
    timings = []
    cpu_start = time.process_time()
    for _ in range(20):
        start = time.perf_counter()
        client = driver(**params)
        try:
            with client.cursor() as cursor:
                cursor.execute('SELECT 1')
                assert cursor.fetchone() == (1,)
            policy = {
                'tls': bool(client.ssl),
                'tls_required': getattr(client, '_ssl_required', None),
                'verify_mode': int(client.ctx.verify_mode) if client.ssl else None,
                'check_hostname': client.ctx.check_hostname if client.ssl else None,
            }
        finally:
            client.close()
        timings.append((time.perf_counter() - start) * 1000)
    results.append(dict(driver=driver.__name__, milliseconds=timings,
                        cpu_ms=(time.process_time() - cpu_start) * 1000, **policy))
print(json.dumps(results))
