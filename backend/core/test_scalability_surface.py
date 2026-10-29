from types import SimpleNamespace

from django.test import SimpleTestCase
from django.urls import include, path
from django.views import View

from core.scalability_surface import describe_routes, describe_task


class SampleView(View):
    http_method_names = ['get', 'head']

    def get(self, request):
        raise AssertionError('Inventory must not execute views')


class SurfaceInventoryTests(SimpleTestCase):
    def test_nested_routes_preserve_templates_and_names_without_execution(self):
        patterns = [path('api/', include(([path('item/<int:pk>/', SampleView.as_view(), name='item')],
                                          'sample'), namespace='sample'))]
        rows = describe_routes(patterns)
        self.assertEqual(rows[0]['pattern'], 'api/item/<int:pk>/')
        self.assertEqual(rows[0]['name'], 'sample:item')
        self.assertEqual(rows[0]['declared_methods'], ['GET', 'HEAD'])
        self.assertEqual(len(rows), 1)
        with self.assertRaisesMessage(ValueError, 'bounded output'):
            describe_routes(patterns, limit=0)

    def test_declared_task_queue_takes_precedence_over_profile_route(self):
        task = SimpleNamespace(queue=None, acks_late=False)
        row = describe_task('notifications.example', task)
        self.assertEqual((row['legacy_queue'], row['isolated_queue']), ('celery', 'notifications'))
        task.queue = 'post_media'
        self.assertEqual(describe_task('notifications.example', task)['isolated_queue'], 'post_media')
        self.assertEqual(describe_task('unknown.example', SimpleNamespace(queue=None, acks_late=True))
                         ['isolated_queue'], 'celery')
