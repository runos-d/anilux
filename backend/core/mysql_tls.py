"""Reuse immutable default PyMySQL TLS configuration, never DB connections.

PyMySQL 1.2's default PREFERRED mode builds an SSLContext (including loading
system trust roots) on every connection. ASGI deliberately uses CONN_MAX_AGE=0.
Sharing that unchanged context avoids this CPU cost while preserving the
driver's negotiation/verification rules. Explicit TLS options remain uncached,
so CA/client-certificate changes continue to take effect on the next connect.
"""
import os
import threading

from pymysql.connections import Connection

_context = None
_pid = os.getpid()
_lock = threading.Lock()


def reset_default_context():
    global _context, _pid, _lock
    _context = None
    _pid = os.getpid()
    _lock = threading.Lock()


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=reset_default_context)


class CachedTLSConnection(Connection):
    def _create_ssl_ctx(self, options):
        global _context
        enabled = os.environ.get('DB_TLS_CONTEXT_CACHE', 'true').lower() in ('true', '1', 'yes')
        if not enabled or not isinstance(options, dict) or options:
            return super()._create_ssl_ctx(options)
        if _pid != os.getpid():
            reset_default_context()
        with _lock:
            if _context is None:
                _context = super()._create_ssl_ctx(options)
            return _context
