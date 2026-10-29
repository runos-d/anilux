"""Apply safe dead-letter policy only to the disposable RabbitMQ vhost."""
import json
import subprocess

container = 'animecore-scalability-lab-rabbitmq-1'
state = json.loads(subprocess.check_output(['docker', 'inspect', container]))[0]
labels = state['Config']['Labels']
if labels.get('com.docker.compose.project') != 'animecore-scalability-lab' or labels.get('com.docker.compose.service') != 'rabbitmq':
    raise RuntimeError('Refusing a non-lab broker')
pattern = '^(celery|events|notifications|recommendations|maintenance|reports|post_media|media_downloads|catalog_imports|native_builds)$'
policy = {'dead-letter-strategy': 'at-least-once', 'overflow': 'reject-publish'}
subprocess.run(['docker', 'exec', container, 'rabbitmqctl', 'set_policy', '--vhost', 'lab',
                '--apply-to', 'quorum_queues', '--priority', '10', 'task-dead-letters', pattern,
                json.dumps(policy)], check=True, capture_output=True)
print(json.dumps({'lab_policy_applied': True, 'dead_letter_strategy': 'at-least-once'}))
