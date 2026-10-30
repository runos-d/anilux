import unittest
from unittest.mock import patch
from engine_stats import collect, engine_get


class EngineStatsTests(unittest.TestCase):
    def test_rejects_nonlocal_engine_and_nonlab_container(self):
        with self.assertRaises(ValueError):
            engine_get('tcp://example.test:2375', '/version')
        with patch('engine_stats.engine_get', return_value={'Config': {'Labels': {}}}) as get:
            with self.assertRaises(ValueError):
                collect('unix:///test', ['a'*12])
            self.assertEqual(get.call_count, 1)

    def test_only_api_counters_exported_and_private_config_omitted(self):
        info = {'Name': '/api-1', 'Config': {'Env': ['SECRET=private'], 'Labels': {
            'com.docker.compose.project': 'animecore-scalability-lab', 'com.docker.compose.service': 'api'}}}
        stats = {'cpu_stats': {'cpu_usage': {'total_usage': 99},
            'throttling_data': {'periods': 10, 'throttled_periods': 3, 'throttled_time': 777}},
            'memory_stats': {'usage': 100}, 'pids_stats': {'current': 4}}
        with patch('engine_stats.engine_get', side_effect=[info, stats]):
            row, = collect('unix:///test', ['a'*12])
        self.assertEqual(row['throttling']['throttled_time'], 777)
        self.assertNotIn('private', str(row))
        self.assertNotIn('Config', row)
