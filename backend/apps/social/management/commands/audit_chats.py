import json
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Audit legacy chat integrity before the conversation migration'

    def handle(self, **options):
        checks = {
            'messages': 'SELECT COUNT(*) FROM social_message',
            'invalid_message_links': 'SELECT COUNT(*) FROM social_message WHERE (chat_id IS NULL AND private_chat_id IS NULL) OR (chat_id IS NOT NULL AND private_chat_id IS NOT NULL)',
            'self_chats': 'SELECT COUNT(*) FROM social_privatechat WHERE user1_id=user2_id',
            'reversed_private_pairs': 'SELECT COUNT(*) FROM social_privatechat WHERE user1_id>user2_id',
            'duplicate_private_pairs': 'SELECT COUNT(*) FROM (SELECT LEAST(user1_id,user2_id), GREATEST(user1_id,user2_id) FROM social_privatechat GROUP BY LEAST(user1_id,user2_id), GREATEST(user1_id,user2_id) HAVING COUNT(*)>1) duplicates',
            'duplicate_franchise_discussions': "SELECT COUNT(*) FROM (SELECT franchise_id FROM social_groupchat WHERE discussion_type='franchise' AND franchise_id IS NOT NULL GROUP BY franchise_id HAVING COUNT(*)>1) duplicates",
            'orphan_topic_ids': 'SELECT COUNT(*) FROM social_message m LEFT JOIN social_chattopic t ON m.topic_id=t.id AND m.chat_id=t.chat_id WHERE m.topic_id IS NOT NULL AND t.id IS NULL',
            'unmigrated_folder_items': 'SELECT COUNT(*) FROM social_chatfolderchat',
        }
        result = {}
        with connection.cursor() as cursor:
            for name, sql in checks.items():
                cursor.execute(sql)
                result[name] = cursor.fetchone()[0]
        self.stdout.write(json.dumps(result, indent=2))
