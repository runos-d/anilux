import hashlib
import json
import tempfile
import zipfile
from datetime import timedelta, datetime
from pathlib import PurePosixPath

from django.apps import apps
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files import File
from django.db import transaction, models
from django.utils import timezone
from django.conf import settings
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from . import conversations as service
from .chat_services import PermissionChecker
from apps.social.infrastructure.models.social import GroupChat, Message, ChatMember
from apps.social.infrastructure.models.social_chat import ChatBackup, ChatBan, MessagePin, MessageReaction, GroupChatSettings


SCOPES = {
    'GroupChat': 'pk', 'ChatRole': 'chat_id', 'ChatTopic': 'chat_id', 'ChatMember': 'chat_id',
    'ChatSlowMode': 'chat_id', 'ChatBan': 'chat_id', 'ChatRestriction': 'chat_id',
    'ChatInviteLink': 'chat_id', 'ChatJoinRequest': 'chat_id', 'Message': 'chat_id',
    'Attachment': 'message__chat_id', 'MessageAttachment': 'message__chat_id',
    'MessageReaction': 'message__chat_id', 'MessagePin': 'message__chat_id',
    'MessageReadStatus': 'message__chat_id', 'GroupMemberSettings': 'membership__chat_id',
    'ChatWallpaper': 'chat_id', 'ChatTheme': 'chat_id', 'AntiSpamRule': 'chat_id',
    'ChatAdminLog': 'chat_id', 'ScheduledMessage': 'chat_id',
}


class ExactTimestampEncoder(DjangoJSONEncoder):
    def default(self, obj):
        return obj.isoformat() if isinstance(obj, datetime) else super().default(obj)


def require_backup_access(chat, user, *, restore=False):
    service.check_access(chat, user)
    checker = PermissionChecker(user, chat)
    if restore:
        allowed = checker._is_owner() or user.is_staff
    else:
        allowed = checker.has_permission('can_manage_chat').allowed
    if not allowed:
        raise PermissionDenied('Недостаточно прав для резервной копии')


@transaction.atomic
def snapshot(chat, user):
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    require_backup_access(chat, user)
    if Message.objects.filter(chat=chat).count() > getattr(settings, 'CHAT_BACKUP_MAX_MESSAGES', 100000):
        raise ValidationError('Чат превышает лимит резервного копирования')
    records, files, manifest_bytes = [], {}, 0
    manifest_limit = getattr(settings, 'CHAT_BACKUP_MAX_MANIFEST_BYTES', 64 * 1024 * 1024)
    for name, scope in SCOPES.items():
        model = apps.get_model('social', name)
        objects = model.objects.filter(**{scope: chat.pk}).order_by('pk').iterator(chunk_size=500)
        for obj in objects:
            encoded = serializers.serialize('json', [obj], cls=ExactTimestampEncoder, ensure_ascii=False)
            manifest_bytes += len(encoded.encode('utf8'))
            if manifest_bytes > manifest_limit or len(records) >= 1000000:
                raise ValidationError('Манифест превышает лимит резервного копирования')
            records.extend(json.loads(encoded))
            for field in model._meta.fields:
                if isinstance(field, models.FileField):
                    file = getattr(obj, field.name)
                    if file:
                        private = field.storage.__class__.__name__ == 'ChatPrivateStorage'
                        key = ('private:' if private else 'public:') + file.name
                        files[key] = (file.name, file.storage, private)
    manifest = {'format': 'anilux-chat', 'version': 1, 'chat_id': chat.public_id,
                'created_at': timezone.now().isoformat(), 'records': records, 'files': {}}
    return manifest, files


def build_backup(backup_id):
    with transaction.atomic():
        backup = ChatBackup.objects.select_for_update().select_related('chat', 'created_by').get(pk=backup_id)
        if backup.status == 'completed' and backup.backup_file:
            return backup
        if backup.processing_started_at and backup.processing_started_at > timezone.now() - timedelta(minutes=6):
            return backup
        backup.processing_started_at, backup.status, backup.error_message = timezone.now(), 'creating', ''
        backup.save(update_fields=['processing_started_at', 'status', 'error_message'])
    saved_name = None
    try:
        manifest, files = snapshot(backup.chat, backup.created_by)
        limit = getattr(settings, 'CHAT_BACKUP_MAX_BYTES', 512 * 1024 * 1024)
        total = 0
        with tempfile.TemporaryFile() as temporary:
            with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for key, (name, storage, private) in files.items():
                    entry = 'files/' + hashlib.sha256(key.encode()).hexdigest()
                    digest, size = hashlib.sha256(), 0
                    with storage.open(name, 'rb') as source, archive.open(entry, 'w') as dest:
                        for chunk in iter(lambda: source.read(65536), b''):
                            total += len(chunk)
                            size += len(chunk)
                            if total > limit:
                                raise ValidationError('Файлы превышают лимит резервного копирования')
                            digest.update(chunk)
                            dest.write(chunk)
                    manifest['files'][key] = {'name': name, 'entry': entry, 'private': private, 'size': size, 'sha256': digest.hexdigest()}
                encoded_manifest = json.dumps(manifest, ensure_ascii=False).encode('utf8')
                if len(encoded_manifest) > getattr(settings, 'CHAT_BACKUP_MAX_MANIFEST_BYTES', 64 * 1024 * 1024):
                    raise ValidationError('Манифест превышает лимит резервного копирования')
                archive.writestr('manifest.json', encoded_manifest)
            temporary.seek(0)
            with transaction.atomic():
                row = ChatBackup.objects.select_for_update().get(pk=backup_id)
                if row.status == 'completed' and row.backup_file:
                    return row
                require_backup_access(row.chat, backup.created_by)
                row.backup_file.save(f'chat-{row.chat.public_id}-{row.pk}.zip', File(temporary), save=False)
                saved_name = row.backup_file.name
                row.file_size = row.backup_file.size
                row.messages_count = sum(r['model'] == 'social.message' for r in manifest['records'])
                row.members_count = sum(r['model'] == 'social.chatmember' for r in manifest['records'])
                row.status = 'completed'
                row.processing_started_at = None
                row.save()
                return row
    except Exception as exc:
        if saved_name:
            ChatBackup._meta.get_field('backup_file').storage.delete(saved_name)
        ChatBackup.objects.filter(pk=backup_id, status='creating').update(status='failed', processing_started_at=None, error_message=str(exc)[:2000])
        raise


def read_archive(backup):
    if backup.status != 'completed' or not backup.backup_file:
        raise ValidationError('Резервная копия ещё не готова')
    try:
        archive = zipfile.ZipFile(backup.backup_file.open('rb'))
        limit = getattr(settings, 'CHAT_BACKUP_MAX_BYTES', 512 * 1024 * 1024)
        entries = archive.infolist()
        manifest_limit = getattr(settings, 'CHAT_BACKUP_MAX_MANIFEST_BYTES', 64 * 1024 * 1024)
        if len({info.filename for info in entries}) != len(entries) or archive.getinfo('manifest.json').file_size > manifest_limit:
            raise ValueError('Дубликаты файлов или слишком большой манифест')
        if sum(info.file_size for info in entries) > limit + manifest_limit:
            raise ValueError('Превышен лимит архива')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('format') != 'anilux-chat' or manifest.get('version') != 1 or manifest.get('chat_id') != backup.chat.public_id:
            raise ValueError('Неподдерживаемый формат или другой чат')
        if not isinstance(manifest['records'], list) or not isinstance(manifest['files'], dict) or len(manifest['records']) > 1000000:
            raise ValueError('Неверный состав архива')
        allowed = {apps.get_model('social', name)._meta.label_lower for name in SCOPES}
        keys = [(r['model'], r['pk']) for r in manifest['records']]
        if len(keys) != len(set(keys)) or sum(r['model'] == 'social.groupchat' for r in manifest['records']) != 1:
            raise ValueError('Дубликат сущности или неверный корень')
        for record in manifest['records']:
            if record['model'] not in allowed or type(record['pk']) is not int or record['pk'] < 1:
                raise ValueError('Недопустимая сущность')
        for key, info in manifest['files'].items():
            name = info['name']
            if type(info['private']) is not bool or key != ('private:' if info['private'] else 'public:') + name or not name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or '\\' in name or info['entry'] != 'files/' + hashlib.sha256(key.encode()).hexdigest():
                raise ValueError('Недопустимое имя файла')
            with archive.open(info['entry']) as source:
                digest, size = hashlib.sha256(), 0
                for chunk in iter(lambda: source.read(65536), b''):
                    digest.update(chunk)
                    size += len(chunk)
            if size != info['size'] or digest.hexdigest() != info['sha256']:
                raise ValueError('Повреждён файл в архиве')
        return archive, manifest
    except (ValueError, TypeError, AttributeError, KeyError, zipfile.BadZipFile, FileNotFoundError) as exc:
        if 'archive' in locals():
            archive.close()
        backup.backup_file.close()
        raise ValidationError(f'Некорректная резервная копия: {exc}')


def validate_records(backup, manifest):
    for record in manifest['records']:
        model = apps.get_model(record['model'])
        expected = {field.name for field in model._meta.local_fields if field.serialize and not field.primary_key}
        if set(record.get('fields', {})) != expected:
            raise ValidationError(f'Неполный или неизвестный набор полей: {record["model"]}')
    try:
        rows = list(serializers.deserialize('json', json.dumps(manifest['records'])))
    except (serializers.base.DeserializationError, ValueError, TypeError) as exc:
        raise ValidationError(f'Неверные данные архива: {exc}')
    archived_members = [row.object for row in rows if isinstance(row.object, ChatMember)]
    current_members = {member.user_id: member for member in ChatMember.objects.filter(
        chat_id=backup.chat_id, user_id__in=[member.user_id for member in archived_members])}
    remapped = {}
    for member in archived_members:
        current = current_members.get(member.user_id)
        if current and current.pk != member.pk:
            if ChatMember.objects.filter(pk=member.pk).exclude(chat_id=backup.chat_id).exists():
                raise ValidationError('Архивный участник конфликтует с другим чатом')
            remapped[member.pk] = current
    if remapped:
        resolved = []
        for row in rows:
            if isinstance(row.object, ChatMember) and row.object.pk in remapped:
                row.object = remapped[row.object.pk]
            elif row.object._meta.model_name == 'groupmembersettings' and row.object.membership_id in remapped:
                continue
            resolved.append(row)
        rows = resolved
    owned = {apps.get_model('social', name)._meta.label_lower: set() for name in SCOPES}
    for row in rows:
        owned[row.object._meta.label_lower].add(row.object.pk)
    errors, external, referenced_files = [], {}, set()
    by_model = {}
    for row in rows:
        by_model.setdefault(type(row.object), []).append(row.object)
    existing_ids, scoped_ids = {}, {}
    for model, objects in by_model.items():
        scope = SCOPES[model.__name__]
        ids = [obj.pk for obj in objects]
        existing_ids[model] = set(model.objects.filter(pk__in=ids).values_list('pk', flat=True))
        scoped_ids[model] = set(model.objects.filter(pk__in=ids, **{scope: backup.chat_id}).values_list('pk', flat=True))
        unique_sets = list(model._meta.unique_together)
        unique_sets += [(field.name,) for field in model._meta.fields if field.unique and not field.primary_key]
        unique_sets += [constraint.fields for constraint in model._meta.constraints
                        if isinstance(constraint, models.UniqueConstraint) and constraint.fields and not constraint.condition]
        for names in unique_sets:
            fields = [model._meta.get_field(name) for name in names]
            incoming = {}
            for obj in objects:
                key = tuple(getattr(obj, f.attname) for f in fields)
                if None not in key and key in incoming and incoming[key] != obj.pk:
                    errors.append(f'{model._meta.label_lower}:{obj.pk}: повтор уникальных полей {list(names)}')
                incoming[key] = obj.pk
            candidates = model.objects.filter(**{scope: backup.chat_id})
            if len(fields) == 1 and fields[0].unique:
                candidates = model.objects.filter(**{fields[0].attname + '__in': [value[0] for value in incoming]})
            for values in candidates.values_list('pk', *[f.attname for f in fields]):
                key = values[1:]
                if None not in key and key in incoming and incoming[key] != values[0]:
                    errors.append(f'{model._meta.label_lower}:{incoming[key]}: конфликт уникальности {list(names)}')
    for row in rows:
        obj = row.object
        scope = SCOPES[obj.__class__.__name__]
        if obj.pk in existing_ids[type(obj)] and obj.pk not in scoped_ids[type(obj)]:
            errors.append(f'{obj._meta.label_lower}:{obj.pk}: конфликт другого чата')
        if hasattr(obj, 'chat_id') and obj.chat_id not in (None, backup.chat_id) or isinstance(obj, GroupChat) and obj.pk != backup.chat_id or getattr(obj, 'private_chat_id', None):
            errors.append(f'{obj._meta.label_lower}:{obj.pk}: другой чат')
        if isinstance(obj, Message) and (obj.private_chat_id or obj.reply_to_id and obj.reply_to_id not in owned.get('social.message', set())):
            errors.append(f'message:{obj.pk}: неверный родитель/ответ')
        for field in obj._meta.fields:
            if isinstance(field, models.FileField):
                file = getattr(obj, field.name)
                if file:
                    key = ('private:' if field.storage.__class__.__name__ == 'ChatPrivateStorage' else 'public:') + file.name
                    referenced_files.add(key)
                    if key not in manifest['files']:
                        errors.append(f'{obj._meta.label_lower}:{obj.pk}: отсутствует файл {field.name}')
            if isinstance(field, models.ForeignKey) and field.name != 'conversation':
                value = getattr(obj, field.attname)
                label = field.related_model._meta.label_lower
                if value and value not in owned.get(label, set()):
                    if label in owned and field.name != 'forwarded_from':
                        errors.append(f'{obj._meta.label_lower}:{obj.pk}: неверная внутренняя связь {field.name}')
                    else:
                        external.setdefault(label, set()).add(value)
    for label, ids in external.items():
        missing = ids - set(apps.get_model(label).objects.filter(pk__in=ids).values_list('pk', flat=True))
        if missing:
            errors.append(f'{label}: отсутствуют {sorted(missing)}')
    if referenced_files != set(manifest['files']):
        errors.append('Состав файлов не соответствует сущностям архива')
    from apps.social.infrastructure.chat_storage import chat_private_storage
    from django.core.files.storage import default_storage
    for info in manifest['files'].values():
        storage = chat_private_storage if info['private'] else default_storage
        if storage.exists(info['name']):
            with storage.open(info['name'], 'rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != info['sha256']:
                    errors.append(f'Конфликт содержимого файла: {info["name"]}')
    if errors:
        raise ValidationError({'dependencies': errors})
    return rows


@transaction.atomic
def restore_backup(backup_id, user, *, dry_run=False):
    original = ChatBackup.objects.filter(pk=backup_id).first()
    if original is None:
        raise NotFound('Резервная копия не найдена')
    chat = GroupChat.objects.select_for_update().get(pk=original.chat_id)
    require_backup_access(chat, user, restore=True)
    backup = ChatBackup.objects.select_for_update().select_related('chat').get(pk=backup_id)
    if backup.restored_at and not dry_run:
        return dict(backup.restore_result, already_restored=True)
    archive, manifest = read_archive(backup)
    new_files = []
    try:
        rows = validate_records(backup, manifest)
        result = {'success': True, 'dry_run': dry_run, 'messages_count': backup.messages_count,
                  'members_count': backup.members_count, 'security_policy': 'current_owner_and_bans_preserved',
                  'preserves_newer_rows': True, 'restored_schedules': 'cancelled'}
        if dry_run:
            return result
        from apps.social.infrastructure.chat_storage import chat_private_storage
        from django.core.files.storage import default_storage
        for key, info in manifest['files'].items():
            storage = chat_private_storage if info['private'] else default_storage
            if not storage.exists(info['name']):
                with archive.open(info['entry']) as source:
                    saved = storage.save(info['name'], File(source))
                new_files.append((storage, saved))
                if saved != info['name']:
                    raise ValidationError('Конфликт имени файла')
        conversation = service.get_conversation(chat, lock=True)
        banned = set(ChatBan.objects.filter(chat=chat).filter(models.Q(until_date__isnull=True) | models.Q(until_date__gt=timezone.now())).values_list('user_id', flat=True))
        touched = []
        grouped = {}
        for row in rows:
            grouped.setdefault(type(row.object), []).append(row.object)
        for model, objects in grouped.items():
            existing = model.objects.in_bulk([obj.pk for obj in objects])
            updates, inserts, originals = [], [], []
            for obj in objects:
                previous = existing.get(obj.pk)
                if isinstance(obj, GroupChat):
                    for field in obj._meta.fields:
                        if field.name not in ('id', 'public_id', 'created_by', 'created_at', 'members_count', 'last_message_at', 'code'):
                            setattr(chat, field.attname, getattr(obj, field.attname))
                    chat.save()
                    continue
                if model.__name__ == 'ScheduledMessage':
                    if previous:
                        continue
                    obj.status = 'cancelled'
                if isinstance(obj, Message):
                    obj.conversation_id = conversation.pk
                    obj.version = max(obj.version, previous.version if previous else 0) + 1
                    touched.append(obj.pk)
                if isinstance(obj, ChatMember):
                    obj.is_banned = obj.user_id in banned or (previous.is_banned if previous else obj.is_banned)
                    if obj.user_id == chat.created_by_id:
                        obj.is_admin = True
                if previous and (isinstance(obj, ChatBan) or model.__name__ == 'ChatRestriction'):
                    continue
                fields = [field for field in model._meta.fields if not field.primary_key]
                originals.append((obj, {f.attname: getattr(obj, f.attname) for f in fields}))
                (updates if previous else inserts).append(obj)
            if inserts:
                model.objects.bulk_create(inserts, batch_size=500)
            for obj, values in originals:
                for name, value in values.items():
                    setattr(obj, name, value)
            if updates or inserts:
                model.objects.bulk_update(updates + inserts, [f.name for f in fields], batch_size=500)
        highest = Message.objects.filter(chat=chat).aggregate(v=models.Max('seq'))['v'] or 0
        conversation.next_message_seq = max(conversation.next_message_seq, highest)
        conversation.save(update_fields=['next_message_seq'])
        reactions, pins = {}, {pin.message_id: pin for pin in MessagePin.objects.filter(message_id__in=touched)}
        for message_id, emoji, uid in MessageReaction.objects.filter(message_id__in=touched).values_list('message_id', 'emoji', 'user_id'):
            reactions.setdefault(message_id, {}).setdefault(emoji, []).append(uid)
        restored = list(Message.objects.filter(pk__in=touched))
        for message in restored:
            pin = pins.get(message.pk)
            message.reactions, message.is_pinned, message.pinned_by_id = reactions.get(message.pk, {}), bool(pin), pin.pinned_by_id if pin else None
        Message.objects.bulk_update(restored, ['reactions', 'is_pinned', 'pinned_by'], batch_size=500)
        chat.members_count = ChatMember.objects.filter(chat=chat).count()
        last = Message.objects.filter(chat=chat, is_deleted=False).order_by('-seq').first()
        chat.last_message_at = last.created_at if last else None
        chat.save(update_fields=['members_count', 'last_message_at'])
        GroupChatSettings.objects.update_or_create(chat=chat, defaults={'members_count': chat.members_count,
            'messages_count': Message.objects.filter(chat=chat, is_deleted=False).count(), 'last_message_at': chat.last_message_at})
        service.record_event(chat, 'chat_restored', {})
        backup.restored_at, backup.restore_result = timezone.now(), result
        backup.save(update_fields=['restored_at', 'restore_result'])
        return result
    except Exception:
        for storage, name in new_files:
            storage.delete(name)
        raise
    finally:
        archive.close()
        backup.backup_file.close()
