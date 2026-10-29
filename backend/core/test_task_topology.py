from django.test import SimpleTestCase
from celery import Celery
from celery.exceptions import QueueNotFound
from celery import Task
from unittest.mock import patch
from core.bounded_tasks import BoundedPublishTask
from core.task_topology import worker_topology, QUEUES


class TaskTopologyTests(SimpleTestCase):
    def test_legacy_profile_preserves_existing_worker_routes_and_ack_policy(self):
        self.assertEqual(worker_topology(), {})

    def test_quorum_requires_explicit_rabbitmq_and_isolated_workers(self):
        for profile, url in (('legacy', 'amqp://lab'), ('isolated', 'redis://lab')):
            with self.assertRaises(ValueError):
                worker_topology(profile, quorum=True, broker_url=url)

    def test_celery_resolves_critical_domains_and_fixed_queue_set(self):
        app = Celery('routing-test', broker='memory://', set_as_current=False)
        app.conf.update(**worker_topology('isolated'))
        for name, queue in (
            ('apps.social.application.tasks_chat.deliver_chat_event', 'events'),
            ('social.retry_post_events', 'events'),
            ('notifications.process_episode_events', 'notifications'),
            ('anime.refresh_recommendations', 'recommendations'),
            ('users.build_data_export', 'reports'),
            ('anime.sync_franchises', 'catalog_imports'),
            ('social.process_post_media', 'post_media'),
        ):
            self.assertEqual(app.amqp.router.route({}, name)['queue'].name, queue)
        self.assertEqual(set(app.amqp.queues), set(QUEUES))
        with self.assertRaises(QueueNotFound):
            app.amqp.router.route({'queue': 'unexpected_unbounded_queue'}, 'anything')
        app.close()

    def test_quorum_queues_have_confirm_overflow_dead_letter_and_bounded_length(self):
        config = worker_topology('isolated', quorum=True, broker_url='amqp://lab', max_length=500)
        self.assertEqual(config['broker_transport_options'], {'confirm_publish': True, 'read_timeout': 2, 'write_timeout': 2})
        self.assertTrue(config['worker_detect_quorum_queues'])
        self.assertNotIn('task_acks_late', config)  # unreviewed tasks retain their ACK behavior
        for queue in config['task_queues']:
            self.assertEqual(queue.queue_arguments['x-queue-type'], 'quorum')
            self.assertEqual(queue.queue_arguments['x-overflow'], 'reject-publish')
            self.assertLessEqual(queue.queue_arguments['x-max-length'], 10000)

    def test_publish_and_confirm_deadlines_are_bounded_without_changing_legacy(self):
        app = Celery('bounded-publish', broker='memory://', task_cls=BoundedPublishTask, set_as_current=False)
        @app.task
        def sample():
            pass
        with patch.object(Task, 'apply_async', return_value='queued') as publish:
            sample.apply_async()
            self.assertNotIn('timeout', publish.call_args.kwargs)
            app.conf.site_bounded_publish = True
            sample.apply_async(timeout=100, confirm_timeout=.25)
            self.assertEqual(publish.call_args.kwargs['timeout'], 2.)
            self.assertEqual(publish.call_args.kwargs['confirm_timeout'], .25)
        app.close()
