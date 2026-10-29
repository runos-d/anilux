"""Independent low-rate lab observer. Never execute Django probes in an API quota."""
import io
import json
import os
from pathlib import Path
import socket
import time
import django
import requests
django.setup()
from django.core.management import call_command
from django.db import close_old_connections

target = Path('/tmp/scalability-observer.json')
while True:
    sample = {'captured_at_unix': time.time()}
    try:
        close_old_connections()
        output = io.StringIO()
        call_command('scalability_snapshot', stdout=output)
        sample['database_outbox'] = json.loads(output.getvalue())
        try:
            response = requests.get('http://rabbitmq:15672/api/queues/lab',
                                    auth=('lab', 'disposable-lab'), timeout=2)
            response.raise_for_status()
            sample['broker_queues'] = [{key: queue.get(key) for key in (
                'name', 'messages_ready', 'messages_unacknowledged')} for queue in response.json()]
        except requests.RequestException:
            sample['rabbitmq_management_available'] = False
        addresses = sorted({row[4][0] for row in socket.getaddrinfo('api', 8000, family=socket.AF_INET)})[:16]
        sample['api_metrics'] = {}
        for address in addresses:
            response = requests.get(f'http://{address}:8000/internal/metrics',
                headers={'Authorization': 'Bearer disposable-lab-metrics'}, timeout=2)
            response.raise_for_status()
            sample['api_metrics'][address] = response.text
    except Exception:
        sample['probe_unavailable'] = True
    finally:
        close_old_connections()
    scratch = target.with_suffix('.new')
    scratch.write_text(json.dumps(sample))
    os.replace(scratch, target)
    time.sleep(5)
