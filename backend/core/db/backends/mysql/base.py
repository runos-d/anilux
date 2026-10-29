from django.db.backends.mysql.base import DatabaseWrapper as DjangoMySQLWrapper
from django.utils.asyncio import async_unsafe

from core.mysql_tls import CachedTLSConnection


class DatabaseWrapper(DjangoMySQLWrapper):
    @async_unsafe
    def connect(self):
        from core.telemetry import current_ws_operation, ws_phase
        operation = current_ws_operation.get()
        if operation:
            with ws_phase(operation, 'connection'):
                return super().connect()
        return super().connect()

    @async_unsafe
    def get_new_connection(self, conn_params):
        connection = CachedTLSConnection(**conn_params)
        # Keep the encoder compatibility adjustment from Django's MySQL backend.
        if connection.encoders.get(bytes) is bytes:
            connection.encoders.pop(bytes)
        return connection
