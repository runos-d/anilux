"""Reuse only the disposable, fully migrated audit schema."""
from django.test.runner import DiscoverRunner
from django.db import connection


class MigratedAuditRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        config = connection.settings_dict
        if connection.vendor != 'mysql' or config['HOST'] != 'audit-mysql' or config['NAME'] != 'chat_test':
            raise RuntimeError('Runner requires the disposable audit-mysql/chat_test schema')
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise RuntimeError('Run all migrations before starting MySQL verification')
        # Load probes intentionally seed this same disposable schema. Unit tests
        # require the clean database normally supplied by DiscoverRunner.
        from django.core.management import call_command
        call_command('flush', interactive=False, verbosity=0)
        return None

    def teardown_databases(self, old_config, **kwargs):
        pass
