import os
import subprocess
import sys
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class ScalabilityConfigTests(SimpleTestCase):
    def test_dedicated_cache_credentials_and_channel_url_are_independent(self):
        script = '''
from config import settings as s
from redis import Redis
assert s.CACHES['default']['LOCATION'] == 'redis://:cache-password@cache-isolated:6379/4'
assert 'PASSWORD' not in s.CACHES['default']['OPTIONS']
assert s.CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS']['max_connections'] == 256
assert s.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]['address'] == 'redis://channel-isolated:6379/2'
assert Redis.from_url(s.CACHES['default']['LOCATION']).connection_pool.connection_kwargs['password'] == 'cache-password'
'''
        environment = {**os.environ, 'ENV_FILE': '/dev/null',
            'CACHE_REDIS_URL': 'redis://:cache-password@cache-isolated:6379/4',
            'CHANNEL_REDIS_URL': 'redis://channel-isolated:6379/2',
            'REDIS_PASSWORD': 'different-realtime-password', 'CACHE_REDIS_MAX_CONNECTIONS': '9999'}
        result = subprocess.run([sys.executable, '-c', script], env=environment, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_lab_config_refuses_other_database_before_importing_environment(self):
        environment = {**os.environ, 'DB_HOST': 'not-lab', 'DB_NAME': 'not-lab'}
        result = subprocess.run([sys.executable, '-c', 'import config.settings_scalability_lab'],
                                env=environment, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'lab-mysql/scalability_lab', result.stderr)


class LabSeedGuardTests(SimpleTestCase):
    def test_seed_refuses_test_schema_without_touching_any_rows(self):
        # Django's no-database SimpleTestCase gate also proves no query happens
        # before the host/name guard rejects the test database.
        from django.db import connection
        with patch.dict(connection.settings_dict, NAME='test_scalability_lab'), self.assertRaises(CommandError):
            call_command('seed_scalability_lab', users=120, anime=3000, posts=10000)
