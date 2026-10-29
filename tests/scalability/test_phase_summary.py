import json
from pathlib import Path
import tempfile
import unittest

from summarize_phases import summarize


class PhaseSummaryTests(unittest.TestCase):
    def fixture(self, reset=False):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        (folder/'result.json').write_text(json.dumps({'load_started_at_unix': 10, 'load_finished_at_unix': 30}))
        samples = []
        for stamp, count in ((1, 500), (11, 10), (29, 9 if reset else 30), (40, 900)):
            body = '\n'.join(f'site_ws_phase_seconds_{kind}{{operation="projection",phase="work"{label}}} {value}'
                for kind, label, value in (('count', '', count), ('sum', '', count*.01),
                    ('bucket', ',le="0.025"', count), ('bucket', ',le="+Inf"', count)))
            samples.append({'observer': {'captured_at_unix': stamp, 'api_metrics': {'api1': body, 'api2': body}}})
        (folder/'resources.jsonl').write_text('\n'.join(json.dumps(s) for s in samples))
        return folder

    def test_only_load_window_deltas_are_aggregated(self):
        result = summarize(self.fixture())
        self.assertEqual(result['sampled_seconds'], 18)
        self.assertEqual(result['api_replicas'], 2)
        self.assertEqual(result['phases'][0]['observations'], 40)
        self.assertAlmostEqual(result['phases'][0]['mean_ms'], 10)
        self.assertEqual(result['phases'][0]['p99_bucket_upper_ms'], 25)

    def test_counter_reset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Counter reset'):
            summarize(self.fixture(reset=True))


if __name__ == '__main__':
    unittest.main()
