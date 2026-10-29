from pathlib import Path
import unittest
from unittest.mock import patch

import replica_probe


class ReplicaProbeSafetyTests(unittest.TestCase):
    def test_foreign_or_ambiguous_containers_are_rejected(self):
        with patch.object(replica_probe, 'command', return_value=b'id1 id2'):
            with self.assertRaisesRegex(RuntimeError, 'exactly one isolated'):
                replica_probe.container('lab-mysql')
        with patch.object(replica_probe, 'command', side_effect=[b'id1', b'{"com.docker.compose.project":"working"}']):
            with self.assertRaisesRegex(RuntimeError, 'identity mismatch'):
                replica_probe.container('lab-mysql')

    def test_nonempty_replica_refused_before_any_dump_or_mutation(self):
        with patch.object(replica_probe, 'mysql', side_effect=['scalability_lab\t101\t1', 'scalability_lab\t102', '5']) as sql, \
                patch.object(replica_probe.subprocess, 'run') as process:
            with self.assertRaisesRegex(RuntimeError, 'not empty'):
                replica_probe.bootstrap('source', 'replica', Path('unused'))
            self.assertEqual(sql.call_count, 3)
            self.assertTrue(all(call.args[1].startswith('SELECT') for call in sql.call_args_list))
            process.assert_not_called()

    def test_checkpoint_accepts_only_expected_lab_binlog(self):
        self.assertIsNotNone(replica_probe.COORDINATES.search(
            b"-- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='lab-bin.000001', SOURCE_LOG_POS=157;"))
        self.assertIsNone(replica_probe.COORDINATES.search(
            b"-- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='working-bin.000001', SOURCE_LOG_POS=157;"))

    def test_recovery_checks_source_and_replica_before_any_mutation(self):
        for answers in (['working\t1\t1'], ['scalability_lab\t101\t1', 'working\t102'],
                        ['scalability_lab\t101\t1', 'scalability_lab\t102', 'foreign-source']):
            with patch.object(replica_probe, 'mysql', side_effect=answers) as sql:
                with self.assertRaises(RuntimeError):
                    replica_probe.recover('source', 'replica')
                self.assertTrue(all(call.args[1].startswith('SELECT') for call in sql.call_args_list))


if __name__ == '__main__':
    unittest.main()
