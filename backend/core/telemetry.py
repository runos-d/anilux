"""Bounded, process-local operational metrics. Never collect paths or user data.

Scrape every ASGI process separately; counters are intentionally not Redis writes
on every request. The endpoint is opt-in and must stay on the private network.
"""
import asyncio
import hmac
import json
import logging
import re
import secrets
import threading
import time
from collections import defaultdict
from contextvars import ContextVar

logger = logging.getLogger('core.telemetry')
BUCKETS = (.01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10, 30)
DOMAINS = frozenset(('anime', 'users', 'social', 'playlists', 'notifications',
                     'seo', 'admin', 'studios', 'dubs', 'ideas', 'native'))
TRACEPARENT = re.compile(r'^00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$')
current_domain = ContextVar('operational_domain', default='other')


def domain_for(path):
    parts = path.split('/', 3)
    if len(parts) > 2 and parts[1] == 'api':
        return parts[2] if parts[2] in DOMAINS else 'api_other'
    if path.startswith('/health/'):
        return 'health'
    return 'other'


class Registry:
    def __init__(self):
        self.lock = threading.Lock()
        self.http = defaultdict(lambda: [0, 0., [0] * len(BUCKETS), 0])
        self.active = {'http': 0, 'websocket': 0}
        self.frames = defaultdict(int)
        self.sql = defaultdict(lambda: [0, 0., 0])
        self.ws_batches = defaultdict(lambda: [0, 0., 0, 0])

    def observe_batch(self, operation, records, seconds, pending):
        operation = operation if operation in ('session', 'projection', 'chat_acl') else 'other'
        with self.lock:
            row = self.ws_batches[operation]
            row[0] += 1
            row[1] += seconds
            row[2] += records
            row[3] = max(row[3], pending)

    def observe(self, domain, status, duration, size):
        # Only these finite labels may enter the registry, even from callers.
        domain = domain if domain in DOMAINS | {'health', 'api_other'} else 'other'
        status = status // 100 if 100 <= status < 600 else 5
        with self.lock:
            row = self.http[(domain, status)]
            row[0] += 1
            row[1] += duration
            row[3] += size
            for i, bound in enumerate(BUCKETS):
                row[2][i] += duration <= bound

    def render(self):
        lines = ['# TYPE site_http_duration_seconds histogram']
        with self.lock:
            for (domain, status), (count, total, buckets, size) in sorted(self.http.items()):
                labels = f'domain="{domain}",status_class="{status}xx"'
                for bound, value in zip(BUCKETS, buckets):
                    lines.append(f'site_http_duration_seconds_bucket{{{labels},le="{bound}"}} {value}')
                lines.extend((f'site_http_duration_seconds_bucket{{{labels},le="+Inf"}} {count}',
                              f'site_http_duration_seconds_count{{{labels}}} {count}',
                              f'site_http_duration_seconds_sum{{{labels}}} {total}',
                              f'site_http_response_bytes_total{{{labels}}} {size}'))
            for kind, count in self.active.items():
                lines.append(f'site_connections_active{{protocol="{kind}"}} {count}')
            for kind, count in sorted(self.frames.items()):
                lines.append(f'site_ws_frames_total{{direction="{kind}"}} {count}')
            for domain, (count, duration, errors) in sorted(self.sql.items()):
                lines.extend((f'site_sql_queries_total{{domain="{domain}"}} {count}',
                              f'site_sql_duration_seconds_total{{domain="{domain}"}} {duration}',
                              f'site_sql_errors_total{{domain="{domain}"}} {errors}'))
            for operation, (count, duration, records, peak) in sorted(self.ws_batches.items()):
                labels = f'operation="{operation}"'
                lines.extend((f'site_ws_batches_total{{{labels}}} {count}',
                              f'site_ws_batch_validation_seconds_total{{{labels}}} {duration}',
                              f'site_ws_batch_records_total{{{labels}}} {records}',
                              f'site_ws_batch_pending_peak{{{labels}}} {peak}'))
        return ('\n'.join(lines) + '\n').encode()


process_registry = Registry()


def sql_timing(execute, sql, params, many, context):
    start, failed = time.monotonic(), False
    try:
        return execute(sql, params, many, context)
    except Exception:
        failed = True
        raise
    finally:
        # Query text and params can contain private content: never retain them.
        domain = current_domain.get()
        with process_registry.lock:
            row = process_registry.sql[domain]
            row[0] += 1
            row[1] += time.monotonic() - start
            row[2] += failed


def instrument_connection(sender, connection, **kwargs):
    # Django reopens the same object; wrappers survive close().
    if sql_timing not in connection.execute_wrappers:
        connection.execute_wrappers.append(sql_timing)


class OperationalTelemetry:
    def __init__(self, application, *, enabled=False, token='', sample_rate=0., registry=None):
        self.application = application
        self.enabled = enabled
        self.token = token.encode('utf-8')
        self.sample_rate = max(0., min(1., sample_rate))
        self.registry = registry or Registry()

    async def __call__(self, scope, receive, send):
        kind = scope['type']
        if not self.enabled or kind not in ('http', 'websocket'):
            return await self.application(scope, receive, send)
        if kind == 'http' and scope.get('path') == '/internal/metrics':
            supplied = next((v for k, v in scope.get('headers', []) if k == b'authorization'), b'')
            allowed = bool(self.token) and hmac.compare_digest(supplied, b'Bearer ' + self.token)
            body = self.registry.render() if allowed else b''
            await send({'type': 'http.response.start', 'status': 200 if allowed else 404,
                        'headers': [(b'content-type', b'text/plain; version=0.0.4'),
                                    (b'cache-control', b'no-store')]})
            await send({'type': 'http.response.body', 'body': body})
            return
        start, status, size = time.monotonic(), 500, 0
        headers = dict(scope.get('headers', []))
        parent = TRACEPARENT.fullmatch(headers.get(b'traceparent', b'').decode('ascii', errors='ignore'))
        trace_id = parent.group(1) if parent and int(parent.group(1), 16) and int(parent.group(2), 16) else secrets.token_hex(16)
        # Remote sampling flags never force logging; no credentials or URL in logs.
        sampled = secrets.randbelow(1_000_000) < self.sample_rate * 1_000_000
        domain = domain_for(scope.get('path', ''))
        domain_token = current_domain.set(domain)
        with self.registry.lock:
            self.registry.active[kind] += 1

        async def counted_receive():
            message = await receive()
            if message['type'] == 'websocket.receive':
                with self.registry.lock:
                    self.registry.frames['received'] += 1
            return message

        async def counted_send(message):
            nonlocal status, size
            if message['type'] == 'http.response.start':
                status = message['status']
                message = {**message, 'headers': [*message.get('headers', []),
                                                  (b'x-trace-id', trace_id.encode())]}
            elif message['type'] == 'http.response.body':
                size += len(message.get('body', b''))
            elif message['type'] == 'websocket.send':
                with self.registry.lock:
                    self.registry.frames['sent'] += 1
            await send(message)

        outcome = 'complete'
        try:
            return await self.application(scope, counted_receive, counted_send)
        except asyncio.CancelledError:
            outcome = 'cancelled'
            raise
        except Exception:
            outcome = 'error'
            raise
        finally:
            duration = time.monotonic() - start
            with self.registry.lock:
                self.registry.active[kind] -= 1
            if kind == 'http':
                self.registry.observe(domain, status, duration, size)
            if sampled:
                logger.info(json.dumps({'event': 'transport.completed', 'trace_id': trace_id,
                                       'protocol': kind, 'domain': domain, 'status': status if kind == 'http' else None,
                                       'duration_seconds': round(duration, 6), 'response_bytes': size,
                                       'outcome': outcome}, separators=(',', ':')))
            current_domain.reset(domain_token)
