"""Lab-only outbox publish/retry probe. Phase flags support a stopped broker."""
import argparse
import json
import os
import time
import uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_scalability_lab')
import django
django.setup()
from django.conf import settings
from apps.social.application import conversations
from apps.social.application.tasks_chat import deliver_chat_event, retry_chat_outbox
from apps.social.infrastructure.models.social import GroupChat, ChatMember
from apps.social.infrastructure.models.conversation import ChatEvent
from apps.users.models import User
from core.scalability_tasks import lab_retry_probe

if settings.DATABASES['default']['HOST'] != 'lab-mysql' or settings.DATABASES['default']['NAME'] != 'scalability_lab':
    raise RuntimeError('Refusing a non-lab schema')
parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=('produce', 'recover', 'retry'))
parser.add_argument('--event-id', type=int)
args = parser.parse_args()
if args.phase == 'retry':
    result = lab_retry_probe.delay().get(timeout=45)
    assert result == {'retried': 1, 'completed': True}, result
    print(json.dumps({'countdown_retry': result, 'broker_scheme': settings.CELERY_BROKER_URL.split(':')[0]}))
elif args.phase == 'produce':
    users = list(User.objects.filter(username__startswith='load-user-').order_by('pk')[:2])
    if len(users) != 2:
        raise RuntimeError('Seed two synthetic users first')
    room = GroupChat.objects.create(name='Synthetic broker probe', created_by=users[0])
    ChatMember.objects.bulk_create([ChatMember(chat=room, user=user) for user in users])
    message, _ = conversations.send_message(room, users[0], {'text': 'Synthetic durable command',
        'client_message_id': str(uuid.uuid4())})
    event = ChatEvent.objects.get(conversation_id=message.conversation_id, kind='new_message',
                                 payload__message__id=message.pk)
    print(json.dumps({'event_id': event.pk, 'message_saved': True,
                      'pending_at_observation': event.delivered_at is None}))
else:
    if not args.event_id:
        parser.error('--event-id is required for recover')
    retry_chat_outbox()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        event = ChatEvent.objects.get(pk=args.event_id)
        if event.delivered_at:
            break
        time.sleep(.1)
    assert event.delivered_at, 'Outbox did not recover'
    deliver_chat_event.delay(event.pk).get(timeout=15)
    print(json.dumps({'event_id': event.pk, 'outbox_published': True, 'duplicate_task_completed': True,
                      'client_delivery_verified': False}))
