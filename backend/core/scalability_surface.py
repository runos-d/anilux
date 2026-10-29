"""Describe static handlers and routing without invoking requests, tasks or ACLs."""
from fnmatch import fnmatchcase

from django.urls import URLPattern, URLResolver

from core.task_topology import ROUTES


def qualified_name(value):
    return f'{value.__module__}.{value.__qualname__}'


def describe_routes(patterns, *, prefix='', namespaces=(), limit=10000):
    rows = []

    def visit(items, path, scope):
        for item in items:
            template = path + str(item.pattern)
            if isinstance(item, URLResolver):
                visit(item.url_patterns, template, (*scope, item.namespace) if item.namespace else scope)
            elif isinstance(item, URLPattern):
                callback = item.callback
                view = getattr(callback, 'cls', None) or getattr(callback, 'view_class', None)
                actions = getattr(callback, 'actions', None)
                # These are declarations, not a promise about runtime dispatch or permission.
                methods = sorted(actions) if actions else sorted(getattr(view, 'http_method_names', ()))
                rows.append({'pattern': template,
                    'name': ':'.join((*scope, item.name)) if item.name else None,
                    'handler': qualified_name(view or callback),
                    'declared_methods': [method.upper() for method in methods]})
                if len(rows) > limit:
                    raise ValueError('Route inventory exceeds its bounded output limit')

    visit(patterns, prefix, namespaces)
    return rows


def describe_task(name, task):
    declared = getattr(task, 'queue', None)
    declared = getattr(declared, 'name', declared)
    matched = next(((pattern, queue) for pattern, queue in ROUTES.items()
                    if fnmatchcase(name, pattern)), (None, 'celery'))
    return {'name': name, 'declared_queue': declared,
            'legacy_queue': declared or 'celery',
            'isolated_queue': declared or matched[1],
            'isolated_route_pattern': matched[0],
            'acks_late_declared': bool(task.acks_late)}
