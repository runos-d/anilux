import os
import sys
import time
import logging


def wait_for_database(connection=None, timeout=None):
    from django.db import connection as default_connection
    from django.db.utils import OperationalError, InterfaceError
    connection = default_connection if connection is None else connection
    timeout = float(os.environ.get('DB_STARTUP_TIMEOUT', '600')) if timeout is None else timeout
    deadline = time.monotonic() + timeout
    announced = False
    while True:
        try:
            connection.ensure_connection()
            return
        except (OperationalError, InterfaceError):
            connection.close()
            if time.monotonic() >= deadline:
                raise SystemExit('Database did not become available before DB_STARTUP_TIMEOUT; check MySQL logs.') from None
            if not announced:
                logging.getLogger(__name__).warning('Waiting for the database to finish starting before checking schema...')
                announced = True
            time.sleep(min(2, max(0, deadline - time.monotonic())))


def check_schema():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    wait_for_database()
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'check_chat_schema', '--verbosity', '0'])
    execute_from_command_line(['manage.py', 'check_project_schema', '--verbosity', '0'])


def main(argv=None):
    command = list(sys.argv[1:] if argv is None else argv)
    if not command:
        raise SystemExit('No container command specified')
    if os.path.basename(command[0]) in ('daphne', 'celery'):
        check_schema()
    if os.path.basename(command[0]) == 'daphne' and os.environ.get('NATIVE_AUTO_BUILD_ON_START', 'true').lower() in ('true', '1', 'yes'):
        try:
            from apps.native_apps.releases import schedule_build
            schedule_build()
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Native app build could not be scheduled')
    os.execvp(command[0], command)


if __name__ == '__main__':
    main()
