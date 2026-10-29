import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Create bounded synthetic rooms and an ID-only room fixture in the disposable lab'

    def add_arguments(self, parser):
        parser.add_argument('--room-size', type=int, default=60)

    def handle(self, **options):
        if connection.settings_dict['HOST'] != 'lab-mysql' or connection.settings_dict['NAME'] != 'scalability_lab':
            raise CommandError('Only lab-mysql/scalability_lab is allowed')
        if not 2 <= options['room_size'] <= 10000:
            raise CommandError('room-size must be 2..10000')
        target = Path('/lab-data/load-rooms.json')
        if target.exists():
            raise CommandError('Room fixture already exists; refusing to overwrite it')
        from apps.users.models import User
        from apps.social.infrastructure.models.social import GroupChat, ChatMember
        from apps.social.application.conversations import get_conversation
        rows = {}
        users = list(User.objects.filter(username__startswith='load-user-').order_by('pk')[:10000])
        if not users:
            raise CommandError('Seed synthetic users first')
        with transaction.atomic():
            for offset in range(0, len(users), options['room_size']):
                members = users[offset:offset+options['room_size']]
                room = GroupChat.objects.create(name=f'Synthetic load room {offset}', created_by=members[0],
                    max_members=max(200, options['room_size']))
                ChatMember.objects.bulk_create([ChatMember(chat=room, user=user) for user in members])
                get_conversation(room)
                rows.update({str(user.pk): room.public_id for user in members})
            with os.fdopen(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
                json.dump({'identity': 'scalability-disposable-lab', 'rooms': rows,
                           'room_size': options['room_size']}, output)
        self.stdout.write(json.dumps({'users': len(users), 'room_size': options['room_size']}))
