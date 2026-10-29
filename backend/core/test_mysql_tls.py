from concurrent.futures import ThreadPoolExecutor
import os
import ssl
from unittest.mock import patch
from unittest import skipUnless

from django.test import SimpleTestCase
from pymysql.connections import Connection
from core.mysql_tls import CachedTLSConnection, reset_default_context


@skipUnless(Connection(defer_connect=True).ssl, 'This driver has no default TLS context to reuse')
class DefaultTLSContextTests(SimpleTestCase):
    def setUp(self):
        reset_default_context()

    def test_shared_default_context_keeps_driver_tls_negotiation_and_verification(self):
        original = Connection(defer_connect=True)
        first, second = CachedTLSConnection(defer_connect=True), CachedTLSConnection(defer_connect=True)
        self.assertTrue(first.ssl)
        self.assertIs(first.ctx, second.ctx)
        self.assertIsNot(first.ctx, original.ctx)
        self.assertEqual(first._ssl_required, original._ssl_required)
        for attr in ('check_hostname','verify_mode','verify_flags','options','minimum_version','maximum_version'):
            self.assertEqual(getattr(first.ctx, attr), getattr(original.ctx, attr))

    def test_parallel_connections_build_the_default_context_only_once(self):
        original = Connection._create_ssl_ctx
        calls = []
        def build(connection, options):
            calls.append(1)
            return original(connection, options)
        with patch.object(Connection, '_create_ssl_ctx', build), ThreadPoolExecutor(max_workers=8) as executor:
            contexts = list(executor.map(lambda _: CachedTLSConnection(defer_connect=True).ctx, range(40)))
        self.assertEqual(len(calls), 1)
        self.assertEqual(len({id(context) for context in contexts}), 1)

    def test_explicit_context_or_tls_configuration_is_not_cached(self):
        explicit = ssl.create_default_context()
        self.assertIs(CachedTLSConnection(ssl=explicit,defer_connect=True).ctx, explicit)
        first = CachedTLSConnection(ssl={'check_hostname':False},defer_connect=True)
        second = CachedTLSConnection(ssl={'check_hostname':False},defer_connect=True)
        self.assertIsNot(first.ctx, second.ctx)
        self.assertTrue(first._ssl_required)

    def test_disabled_tls_and_cache_opt_out_keep_the_driver_behavior(self):
        self.assertFalse(CachedTLSConnection(ssl_disabled=True,defer_connect=True).ssl)
        with patch.dict(os.environ, {'DB_TLS_CONTEXT_CACHE':'false'}):
            first, second = CachedTLSConnection(defer_connect=True), CachedTLSConnection(defer_connect=True)
        self.assertIsNot(first.ctx, second.ctx)

    def test_a_child_process_does_not_reuse_the_parent_context(self):
        parent = CachedTLSConnection(defer_connect=True).ctx
        with patch('core.mysql_tls.os.getpid', return_value=os.getpid()+1):
            child = CachedTLSConnection(defer_connect=True).ctx
        self.assertIsNot(parent, child)
