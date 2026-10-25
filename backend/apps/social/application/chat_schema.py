from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader


CHAT_MODELS = ('Conversation', 'ChatEvent', 'ConversationUserState', 'Message',
    'PrivateChat', 'GroupChat', 'ChatMember', 'ChatRole', 'ChatTopic', 'ChatFolder',
    'ChatFolderChat', 'ChatBackup', 'ChatJoinRequest', 'ChatInviteLink',
    'PrivateChatSettings', 'GroupChatSettings', 'GroupMemberSettings',
    'ChatWallpaper', 'ChatTheme', 'ScheduledMessage', 'Attachment',
    'MessageAttachment', 'MessageReaction', 'MessagePin', 'MessageReadStatus',
    'ChatAdminLog', 'ChatTypingStatus', 'ChatSettings', 'PrivateChatUserSettings',
    'Reaction', 'ChatBan', 'ChatRestriction', 'ChatSlowMode', 'ChatTag',
    'ChatTagAssignment', 'AntiSpamRule', 'UserGlobalChatStyle')


def chat_schema_status():
    loader = MigrationLoader(connection)
    pending = [name for app, name in loader.graph.leaf_nodes('social')
        if (app, name) not in loader.applied_migrations]
    tables = set(connection.introspection.table_names())
    missing_tables, missing_columns, invalid_public_ids = [], {}, {}
    with connection.cursor() as cursor:
        for name in CHAT_MODELS:
            model = apps.get_model('social', name)
            table = model._meta.db_table
            if table not in tables:
                missing_tables.append(table)
                continue
            columns = {column.name: column for column in connection.introspection.get_table_description(cursor, table)}
            absent = sorted({field.column for field in model._meta.local_fields} - columns.keys())
            if absent:
                missing_columns[table] = absent
            if 'public_id' in columns:
                constraints = connection.introspection.get_constraints(cursor, table)
                unique = any(value['unique'] and value['columns'] == ['public_id'] for value in constraints.values())
                if columns['public_id'].null_ok or not unique:
                    invalid_public_ids[table] = {'nullable': columns['public_id'].null_ok, 'unique': unique}
    return {'ready': not (pending or missing_tables or missing_columns or invalid_public_ids),
        'pending_migrations': pending, 'missing_tables': missing_tables, 'missing_columns': missing_columns,
        'invalid_public_ids': invalid_public_ids}
