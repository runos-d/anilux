import io
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, SimpleTestCase

from .chat_schema import chat_schema_status
import docker_entrypoint


class ChatSchemaTests(TestCase):
    def test_migrated_database_is_ready(self):
        self.assertTrue(chat_schema_status()['ready'])
        call_command('check_chat_schema', stdout=io.StringIO())

    def test_missing_table_is_rejected_even_with_applied_migrations(self):
        tables = [name for name in connection.introspection.table_names() if name != 'social_chatevent']
        with patch.object(connection.introspection, 'table_names', return_value=tables):
            self.assertIn('social_chatevent', chat_schema_status()['missing_tables'])
            with self.assertRaisesMessage(CommandError, 'Chat schema is not ready'):
                call_command('check_chat_schema')

    def test_missing_message_column_is_rejected(self):
        describe = connection.introspection.get_table_description
        def without_version(cursor, table):
            columns = describe(cursor, table)
            return [column for column in columns if column.name != 'version'] if table == 'social_message' else columns
        with patch.object(connection.introspection, 'get_table_description', side_effect=without_version):
            self.assertEqual(['version'], chat_schema_status()['missing_columns']['social_message'])
            with self.assertRaises(CommandError):
                call_command('check_chat_schema')

    def test_pending_migration_is_rejected_with_existing_tables(self):
        with patch('apps.social.application.chat_schema.MigrationLoader') as loader:
            loader.return_value.graph.leaf_nodes.return_value = [('social', '0025_chat_privacy_and_backups')]
            loader.return_value.applied_migrations = set()
            self.assertEqual(['0025_chat_privacy_and_backups'], chat_schema_status()['pending_migrations'])

    def test_nullable_public_id_is_rejected_even_without_null_rows(self):
        describe = connection.introspection.get_table_description
        def nullable(cursor, table):
            columns = describe(cursor, table)
            return [column._replace(null_ok=True) if column.name == 'public_id' else column for column in columns] if table == 'social_privatechat' else columns
        with patch.object(connection.introspection, 'get_table_description', side_effect=nullable):
            self.assertTrue(chat_schema_status()['invalid_public_ids']['social_privatechat']['nullable'])
            with self.assertRaises(CommandError):
                call_command('check_chat_schema')

    def test_missing_public_id_unique_constraint_is_rejected(self):
        constraints = connection.introspection.get_constraints
        def without_public_unique(cursor, table):
            values = constraints(cursor, table)
            return {name: value for name, value in values.items() if value['columns'] != ['public_id']} if table == 'social_privatechat' else values
        with patch.object(connection.introspection, 'get_constraints', side_effect=without_public_unique):
            self.assertFalse(chat_schema_status()['invalid_public_ids']['social_privatechat']['unique'])
            with self.assertRaises(CommandError):
                call_command('check_chat_schema')


class ChatEntrypointTests(SimpleTestCase):
    def test_scaled_api_can_disable_automatic_native_build(self):
        import os
        with patch.dict(os.environ, {'NATIVE_AUTO_BUILD_ON_START': 'false'}), \
                patch.object(docker_entrypoint, 'check_schema'), \
                patch.object(docker_entrypoint.os, 'execvp') as execute, \
                patch('apps.native_apps.releases.schedule_build') as schedule:
            command = ['daphne', 'config.asgi:application']
            docker_entrypoint.main(command)
            execute.assert_called_once_with('daphne', command)
            schedule.assert_not_called()

    def test_daphne_and_celery_wait_for_schema_preflight(self):
        for command in [['daphne', 'config.asgi:application'], ['celery', '-A', 'config', 'worker'], ['celery', '-A', 'config', 'beat']]:
            with self.subTest(command=command), patch.object(docker_entrypoint, 'check_schema', side_effect=SystemExit(1)), patch.object(docker_entrypoint.os, 'execvp') as execute:
                with self.assertRaises(SystemExit):
                    docker_entrypoint.main(command)
                execute.assert_not_called()

    def test_ready_service_replaces_process_for_signal_delivery(self):
        with patch.object(docker_entrypoint, 'check_schema') as check, patch.object(docker_entrypoint.os, 'execvp') as execute:
            command = ['celery', '-A', 'config', 'worker']
            docker_entrypoint.main(command)
            check.assert_called_once()
            execute.assert_called_once_with('celery', command)

    def test_migration_command_is_allowed_before_schema_is_ready(self):
        with patch.object(docker_entrypoint, 'check_schema') as check, patch.object(docker_entrypoint.os, 'execvp') as execute:
            command = ['python', 'manage.py', 'migrate', '--noinput']
            docker_entrypoint.main(command)
            check.assert_not_called()
            execute.assert_called_once_with('python', command)
