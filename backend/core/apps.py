from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.conf import settings
        if settings.OPERATIONAL_METRICS_ENABLED:
            from django.db.backends.signals import connection_created
            from core.telemetry import instrument_connection
            connection_created.connect(instrument_connection, weak=False,
                                       dispatch_uid='core.operational_sql_timing')
