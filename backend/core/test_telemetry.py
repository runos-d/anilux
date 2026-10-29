import asyncio
import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
from django.test import override_settings

from core.telemetry import OperationalTelemetry, Registry


class TelemetryTests(IsolatedAsyncioTestCase):
    async def request(self, app, path='/api/users/123/secret?q=token', headers=(), kind='http'):
        sent = []
        async def receive():
            return {'type': 'http.request'}
        await app({'type': kind, 'path': path, 'headers': headers}, receive, self.append_to(sent))
        return sent

    @staticmethod
    def append_to(sent):
        async def send(message):
            sent.append(message)
        return send

    async def test_histogram_bounded_labels_trace_and_private_endpoint(self):
        async def application(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 201})
            await send({'type': 'http.response.body', 'body': b'ok'})
        app = OperationalTelemetry(application, enabled=True, token='private')
        for i in range(50):
            await self.request(app, f'/api/unknown{i}/user{i}')
        sent = await self.request(app, headers=[(b'traceparent', b'00-' + b'a'*32 + b'-' + b'b'*16 + b'-01')])
        self.assertIn((b'x-trace-id', b'a'*32), sent[0]['headers'])
        self.assertEqual(len(app.registry.http), 2)
        self.assertEqual((await self.request(app, '/internal/metrics'))[0]['status'], 404)
        exported = await self.request(app, '/internal/metrics', [(b'authorization', b'Bearer private')])
        self.assertEqual(exported[0]['status'], 200)
        self.assertIn(b'site_http_duration_seconds_count{domain="users",status_class="2xx"} 1', exported[1]['body'])
        self.assertNotIn(b'user49', exported[1]['body'])
        self.assertEqual(app.registry.active['http'], 0)

    async def test_disabled_token_empty_logs_do_not_expose_request(self):
        async def application(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 200})
        app = OperationalTelemetry(application, enabled=True, sample_rate=1)
        with patch('core.telemetry.logger.info') as log:
            await self.request(app, headers=[(b'authorization', b'Bearer secret')])
            entry = json.loads(log.call_args.args[0])
            self.assertEqual(entry['domain'], 'users')
            self.assertNotIn('secret', log.call_args.args[0])
        self.assertEqual((await self.request(app, '/internal/metrics', [(b'authorization', b'Bearer ')]))[0]['status'], 404)
        disabled = OperationalTelemetry(application)
        self.assertEqual((await self.request(disabled))[0], {'type': 'http.response.start', 'status': 200})

    async def test_cancel_cleanup_and_frame_counts(self):
        async def cancelled(scope, receive, send):
            raise asyncio.CancelledError
        app = OperationalTelemetry(cancelled, enabled=True)
        with self.assertRaises(asyncio.CancelledError):
            await self.request(app)
        self.assertEqual(app.registry.active['http'], 0)
        async def socket(scope, receive, send):
            await receive()
            await send({'type': 'websocket.send', 'text': 'private'})
        app = OperationalTelemetry(socket, enabled=True)
        async def receive():
            return {'type': 'websocket.receive', 'text': 'private'}
        await app({'type': 'websocket', 'path': '/ws/'}, receive, self.append_to([]))
        self.assertEqual(dict(app.registry.frames), {'received': 1, 'sent': 1})
        self.assertEqual(app.registry.active['websocket'], 0)

    def test_untrusted_registry_labels_are_collapsed(self):
        registry = Registry()
        for i in range(1000):
            registry.observe(str(i), i + 600, .1, 2)
        self.assertEqual(len(registry.http), 1)
        for i in range(1000):
            registry.observe_ws_phase(str(i), str(i), .02)
        self.assertEqual(len(registry.ws_phases), 1)

    @override_settings(OPERATIONAL_METRICS_ENABLED=True)
    async def test_database_phase_context_cleans_up_after_failure(self):
        from core.telemetry import measured_database_call, current_ws_operation
        registry = Registry()
        def failed():
            self.assertEqual(current_ws_operation.get(), 'projection')
            raise RuntimeError('private content')
        with patch('core.telemetry.process_registry', registry):
            with self.assertRaises(RuntimeError):
                await measured_database_call(failed, 'projection')
        self.assertIsNone(current_ws_operation.get())
        self.assertEqual(registry.ws_phases[('projection', 'work')][0], 1)
        self.assertEqual(registry.ws_phases[('projection', 'executor_wait')][0], 1)
        self.assertNotIn(b'private', registry.render())

    @override_settings(OPERATIONAL_METRICS_ENABLED=True)
    def test_publication_metadata_is_optional_bounded_and_payload_free(self):
        import time
        from core.telemetry import observe_publication
        registry = Registry()
        with patch('core.telemetry.process_registry', registry):
            for stamp in (None, 'private', time.time() + 60, time.time() - 7200):
                observe_publication({'_published_at': stamp}, 'room')
            observe_publication({'_published_at': time.time() - .1}, 'room')
        self.assertEqual(registry.ws_phases[('room', 'publication_to_handler')][0], 1)

    def test_sql_wrapper_is_attached_once_and_never_retains_private_sql(self):
        from types import SimpleNamespace
        from core.telemetry import instrument_connection, sql_timing, process_registry
        connection = SimpleNamespace(execute_wrappers=[])
        instrument_connection(None, connection)
        instrument_connection(None, connection)
        self.assertEqual(connection.execute_wrappers, [sql_timing])
        self.assertEqual(sql_timing(lambda *args: 7, 'private sql', ['private text'], False, {}), 7)
        with self.assertRaises(RuntimeError):
            sql_timing(lambda *args: (_ for _ in ()).throw(RuntimeError()), 'private sql', [], False, {})
        self.assertNotIn(b'private', process_registry.render())
