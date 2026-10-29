import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import get_resolver

from core.scalability_surface import describe_routes, describe_task


class Command(BaseCommand):
    help = 'Export bounded static HTTP/WS/task inventory; never execute handlers or contact a broker'
    requires_system_checks = []

    def handle(self, **options):
        from config.celery import app
        from apps.social.application.routing import websocket_urlpatterns

        app.loader.import_default_modules()
        tasks = sorted((name, task) for name, task in app.tasks.items() if not name.startswith('celery.'))
        if len(tasks) > 10000:
            raise CommandError('Task inventory exceeds its bounded output limit')
        try:
            http = describe_routes(get_resolver().url_patterns)
            websocket = describe_routes(websocket_urlpatterns)
        except ValueError as error:
            raise CommandError(str(error)) from None
        scheduled = sorted({entry['task'] for entry in app.conf.beat_schedule.values()})
        registered = {name for name, _ in tasks}
        result = {'schema_version': 1, 'urlconf': settings.ROOT_URLCONF,
            'runtime_policies_evaluated': False, 'capacity_certified': False,
            'http': http, 'websocket': websocket,
            'tasks': [describe_task(name, task) for name, task in tasks],
            'scheduled_task_names': scheduled,
            'unregistered_scheduled_task_names': sorted(set(scheduled) - registered),
            'notes': ['Static inventory depends on enabled feature flags and URL configuration.',
                      'Methods are declarations; function handlers may inspect methods at runtime.',
                      'Task queue options explicitly passed by a caller override this static map.',
                      'No session, ACL, payload, broker URL or environment values are exported.']}
        self.stdout.write(json.dumps(result, indent=2))
