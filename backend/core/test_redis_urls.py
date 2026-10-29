from unittest.mock import patch
from django.test import SimpleTestCase
from redis import Redis
from kombu import Connection
from config import settings as application_settings


class RedisCredentialTests(SimpleTestCase):
    def test_special_password_survives_cache_channel_and_broker_url_parsing(self):
        password = 'disposable:a@b/#?% word'
        with patch.object(application_settings, 'REDIS_PASSWORD', password), \
                patch.object(application_settings, 'REDIS_HOST', '10.80.0.10'):
            url = application_settings.redis_uri(3)
        options = Redis.from_url(url).connection_pool.connection_kwargs
        self.assertEqual(options['password'], password)
        self.assertEqual(options['db'], 3)
        self.assertEqual(Connection(url).password, password)

    def test_private_ipv6_is_a_valid_redis_uri(self):
        with patch.object(application_settings, 'REDIS_HOST', 'fd00::10'):
            options = Redis.from_url(application_settings.redis_uri(0)).connection_pool.connection_kwargs
        self.assertEqual(options['host'], 'fd00::10')
