"""Bound admission before Django creates threads or authenticates sockets."""
import threading


class BoundedApplication:
    def __init__(self, application, http_limit=64, socket_limit=2048, handshake_limit=64):
        self.application = application
        self.limits = {'http': http_limit, 'websocket': socket_limit}
        self.active = {'http': 0, 'websocket': 0}
        self.lock = threading.Lock()
        self.handshake_limit = handshake_limit
        self.pending_handshakes = 0

    async def __call__(self, scope, receive, send):
        kind = scope['type']
        if kind not in self.limits:
            return await self.application(scope, receive, send)
        with self.lock:
            admitted = self.active[kind] < self.limits[kind] and (
                kind != 'websocket' or self.pending_handshakes < self.handshake_limit
            )
            if admitted:
                self.active[kind] += 1
                if kind == 'websocket':
                    self.pending_handshakes += 1
        if not admitted:
            if kind == 'websocket':
                await send({'type': 'websocket.close', 'code': 1013})
            else:
                await send({'type': 'http.response.start', 'status': 503, 'headers': [
                    (b'content-type', b'application/json'), (b'retry-after', b'1'), (b'cache-control', b'no-store')]})
                await send({'type': 'http.response.body', 'body': b'{"detail":"Server busy. Retry shortly."}'})
            return
        handshake_pending = kind == 'websocket'
        def finish_handshake():
            nonlocal handshake_pending
            if handshake_pending:
                with self.lock:
                    self.pending_handshakes -= 1
                handshake_pending = False
        async def guarded_send(message):
            if message['type'] in ('websocket.accept', 'websocket.close'):
                finish_handshake()
            await send(message)
        try:
            return await self.application(scope, receive, guarded_send if kind == 'websocket' else send)
        finally:
            finish_handshake()
            with self.lock:
                self.active[kind] -= 1
