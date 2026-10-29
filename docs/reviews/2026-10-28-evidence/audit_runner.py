from django.test.runner import DiscoverRunner
from django.apps import apps
from django.db import connection
class AuditRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        if connection.vendor != 'sqlite' or connection.settings_dict['NAME'] != ':memory:':
            raise RuntimeError('Diagnostic runner requires an in-memory SQLite database')
        import config.urls
        with connection.schema_editor() as editor:
            seen = set()
            for model in apps.get_models():
                if not model._meta.proxy and model._meta.db_table not in seen:
                    editor.create_model(model)
                    seen.add(model._meta.db_table)
        return None
    def teardown_databases(self, old_config, **kwargs): pass


