import hashlib
import json

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Return counts/hashes of immutable chat data for migration verification.'

    def add_arguments(self, parser):
        parser.add_argument('--exclude-public-ids', action='store_true', help='Compare contents while filling previously NULL public IDs.')

    def handle(self, **options):
        selections = {
            'messages': ('social_message', 'id,chat_id,private_chat_id,sender_id,text,created_at,reply_to_id,media'),
            'private_chats': ('social_privatechat', 'id,public_id,LEAST(user1_id,user2_id),GREATEST(user1_id,user2_id),created_at'),
            'group_chats': ('social_groupchat', 'id,public_id,name,created_by_id,created_at'),
            'attachments': ('social_attachment', 'id,message_id,file,file_name,uploaded_at'),
        }
        if options['exclude_public_ids']:
            selections = {name: (table, fields.replace('public_id,', '')) for name, (table, fields) in selections.items()}
        result = {}
        with connection.cursor() as cursor:
            for name, (table, fields) in selections.items():
                cursor.execute(f'SELECT {fields} FROM {table} ORDER BY id')
                digest, count = hashlib.sha256(), 0
                while rows := cursor.fetchmany(1000):
                    for row in rows:
                        digest.update(json.dumps(row, default=str, ensure_ascii=False).encode('utf8') + b'\n')
                        count += 1
                result[name] = {'count': count, 'sha256': digest.hexdigest()}
        self.stdout.write(json.dumps(result, indent=2))
