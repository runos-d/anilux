import unittest
from unittest.mock import Mock, patch
from django.db.utils import OperationalError, ProgrammingError
from docker_entrypoint import wait_for_database


class DatabaseStartupTests(unittest.TestCase):
    def test_recovery_retries_then_continues(self):
        connection = Mock()
        connection.ensure_connection.side_effect = [OperationalError('starting'), None]
        with patch('docker_entrypoint.time.sleep') as sleep:
            wait_for_database(connection, timeout=30)
        self.assertEqual(connection.ensure_connection.call_count, 2)
        connection.close.assert_called_once()
        sleep.assert_called_once()

    def test_timeout_is_bounded_and_does_not_expose_credentials(self):
        connection = Mock()
        connection.ensure_connection.side_effect = OperationalError('private password')
        with patch('docker_entrypoint.time.monotonic', side_effect=[0, 31]):
            with self.assertRaisesRegex(SystemExit, 'DB_STARTUP_TIMEOUT') as error:
                wait_for_database(connection, timeout=30)
        self.assertNotIn('private password', str(error.exception))

    def test_schema_errors_are_not_retried(self):
        connection = Mock()
        connection.ensure_connection.side_effect = ProgrammingError('invalid schema')
        with self.assertRaises(ProgrammingError):
            wait_for_database(connection, timeout=30)


if __name__ == '__main__':
    unittest.main()
