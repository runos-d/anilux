import base64
import json
import io
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, APIException, ParseError
from rest_framework.parsers import JSONParser

from apps.social.infrastructure.models.social import ChatFolder, ChatFolderChat, ChatMember
from apps.social.infrastructure.models.social_chat import PrivateChatSettings, GroupMemberSettings, ChatWallpaper, ChatTheme, UserGlobalChatStyle
from apps.users.infrastructure.models.users import User
from . import conversations as service


EXCLUDED = {'id', 'public_id', 'created_at', 'updated_at', 'blocked_at', 'folder_id',
            'is_preset', 'preset_name', 'preset_category', 'is_system'}
SECTIONS = {'private_chats': PrivateChatSettings, 'group_chats': GroupMemberSettings,
            'wallpapers': ChatWallpaper, 'themes': ChatTheme, 'global_style': UserGlobalChatStyle,
            'folders': ChatFolder}


class SettingsImportParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        limit = getattr(settings, 'CHAT_SETTINGS_IMPORT_MAX_BYTES', 32 * 1024 * 1024)
        content = stream.read(limit + 1)
        if len(content) > limit:
            raise ParseError('Файл настроек превышает допустимый размер')
        return super().parse(io.BytesIO(content), media_type, parser_context)


def fields_for(model):
    return [f.name for f in model._meta.fields if f.name not in EXCLUDED and not f.is_relation and not isinstance(f, models.FileField)]


def values_for(obj):
    return json.loads(json.dumps({key: getattr(obj, key) for key in fields_for(type(obj))}, cls=DjangoJSONEncoder))


def reference(chat):
    return {'type': service.chat_kind(chat), 'id': chat.public_id} if chat else None


def export_settings(user):
    total_bytes = 0
    data = {'version': '3.0', 'exported_at': service.timezone.now().isoformat(), **{section: [] for section in SECTIONS}}
    queries = {
        'private_chats': PrivateChatSettings.objects.filter(user=user).select_related('chat'),
        'group_chats': GroupMemberSettings.objects.filter(membership__user=user).select_related('membership__chat'),
        'wallpapers': ChatWallpaper.objects.filter(user=user).select_related('chat', 'private_chat'),
        'themes': ChatTheme.objects.filter(user=user).select_related('chat', 'private_chat'),
        'global_style': UserGlobalChatStyle.objects.filter(user=user),
        'folders': ChatFolder.objects.filter(user=user, is_system=False).prefetch_related('chats__conversation__group_chat', 'chats__conversation__private_chat'),
    }
    folders = dict(ChatFolder.objects.filter(user=user).values_list('pk', 'name'))
    for section, query in queries.items():
        for obj in query.order_by('pk'):
            chat = obj.membership.chat if section == 'group_chats' else getattr(obj, 'chat', None) or getattr(obj, 'private_chat', None)
            if chat:
                try:
                    service.check_access(chat, user)
                except APIException:
                    continue
            row = {'chat': reference(chat), 'settings': values_for(obj)}
            if section == 'private_chats':
                row['folder_name'] = folders.get(obj.folder_id)
            if section == 'folders':
                row['chats'] = []
                for item in obj.chats.all():
                    if not item.conversation:
                        continue
                    try:
                        service.check_access(item.conversation.chat, user)
                        row['chats'].append(reference(item.conversation.chat))
                    except APIException:
                        continue
            images = {}
            for field in obj._meta.fields:
                if isinstance(field, models.FileField):
                    file = getattr(obj, field.name)
                    if file:
                        total_bytes += file.size
                        if total_bytes > 20 * 1024 * 1024:
                            raise ValidationError('Изображения настроек превышают 20 МБ')
                        if file.size > 5 * 1024 * 1024:
                            raise ValidationError('Изображение настроек превышает 5 МБ')
                        with file.open('rb') as source:
                            images[field.name] = {'name': PurePosixPath(file.name).name, 'content': base64.b64encode(source.read()).decode()}
                    else:
                        images[field.name] = None
            if images:
                row['images'] = images
            data[section].append(row)
    return data


def payload(model, data):
    if not isinstance(data, dict) or set(data) - set(fields_for(model)):
        raise ValidationError('Неизвестные поля персональных настроек')
    meta = type('Meta', (), {'model': model, 'fields': fields_for(model), 'validators': []})
    serializer = type('SettingsPayload', (serializers.ModelSerializer,), {'Meta': meta})(data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@transaction.atomic
def import_settings(user, data):
    from .chat_settings_service import SettingsCache, SettingsVersioning
    from apps.social.infrastructure.models.conversation import ConversationUserState
    if not isinstance(data, dict) or data.get('version') != '3.0' or set(data) - {'version', 'exported_at', *SECTIONS}:
        raise ValidationError('Ожидается экспорт настроек версии 3.0')
    User.objects.select_for_update().get(pk=user.pk)
    prepared, total_bytes, seen = [], 0, set()
    for section, model in SECTIONS.items():
        entries = data.get(section, [])
        if not isinstance(entries, list) or len(entries) > 2000:
            raise ValidationError('Превышен лимит настроек')
        for row in entries:
            if not isinstance(row, dict) or set(row) - {'chat', 'settings', 'images', 'folder_name', 'chats'}:
                raise ValidationError('Неверная запись настроек')
            ref = row.get('chat')
            chat = None
            if ref is not None:
                if not isinstance(ref, dict) or set(ref) != {'type', 'id'} or ref['type'] not in ('private', 'group') or type(ref['id']) is not int:
                    raise ValidationError('Неверная ссылка на чат')
                chat = service.resolve_chat(ref['id'], user, ref['type'])
            if section in ('private_chats', 'group_chats') and (not chat or service.chat_kind(chat) != ('private' if section == 'private_chats' else 'group')):
                raise ValidationError('Неверный тип чата')
            if section in ('global_style', 'folders') and chat:
                raise ValidationError('Глобальные настройки не относятся к чату')
            values = payload(model, row.get('settings'))
            key = (section, service.chat_kind(chat) if chat else None, chat.pk if chat else values.get('name'))
            if key in seen:
                raise ValidationError('Повторная запись настроек')
            seen.add(key)
            if section == 'folders' and not values.get('name'):
                raise ValidationError('Имя папки обязательно')
            if section == 'folders' and ChatFolder.objects.filter(user=user, name=values['name'], is_system=True).exists():
                raise ValidationError('Нельзя перезаписать системную папку')
            images = row.get('images', {})
            file_fields = {f.name for f in model._meta.fields if isinstance(f, models.FileField)}
            if not isinstance(images, dict) or set(images) - file_fields:
                raise ValidationError('Недопустимое изображение')
            parsed_images = {}
            for name, image in images.items():
                if image is None:
                    parsed_images[name] = None
                    continue
                try:
                    if not isinstance(image, dict) or set(image) != {'name', 'content'} or len(image['content']) > 7 * 1024 * 1024:
                        raise ValueError()
                    image_bytes = base64.b64decode(image['content'], validate=True)
                    total_bytes += len(image_bytes)
                    if total_bytes > 20 * 1024 * 1024 or len(image_bytes) > 5 * 1024 * 1024 or PurePosixPath(image['name']).name != image['name'] or '\\' in image['name']:
                        raise ValueError()
                    from PIL import Image
                    import io
                    Image.open(io.BytesIO(image_bytes)).verify()
                    parsed_images[name] = ContentFile(image_bytes, name=image['name'])
                except (ValueError, TypeError, KeyError, OSError) as exc:
                    raise ValidationError('Повреждённое изображение настроек') from exc
            folder_chats = []
            if section == 'folders':
                if not isinstance(row.get('chats', []), list) or len(row.get('chats', [])) > 2000:
                    raise ValidationError('Неверный список папки')
                for item in row.get('chats', []):
                    if not isinstance(item, dict) or set(item) != {'id', 'type'} or item['type'] not in ('private', 'group') or type(item['id']) is not int:
                        raise ValidationError('Неверная ссылка папки')
                    folder_chats.append(service.resolve_chat(item['id'], user, item['type']))
            prepared.append((section, model, chat, values, parsed_images, row.get('folder_name'), folder_chats))
    parents = { (service.chat_kind(chat), chat.pk): chat for _, _, chat, _, _, _, refs in prepared for chat in ([chat] if chat else []) + refs }
    for key in sorted(parents):
        chat = parents[key]
        type(chat).objects.select_for_update().get(pk=chat.pk)
        service.check_access(chat, user)
    imported, saved_files = {key: 0 for key in SECTIONS}, []
    try:
        prepared.sort(key=lambda row: row[0] != 'folders')
        for section, model, chat, values, images, folder_name, folder_chats in prepared:
            if section == 'group_chats':
                lookup = {'membership': ChatMember.objects.get(chat=chat, user=user)}
            else:
                lookup = {'user': user}
                if section == 'private_chats':
                    lookup['chat'] = chat
                elif section in ('wallpapers', 'themes'):
                    lookup.update(chat=chat if chat and service.chat_kind(chat) == 'group' else None,
                                  private_chat=chat if chat and service.chat_kind(chat) == 'private' else None)
                elif section == 'folders':
                    lookup.update(name=values['name'], is_system=False)
            obj = model.objects.filter(**lookup).first() or model(**lookup)
            for key, value in values.items():
                setattr(obj, key, value)
            if section == 'private_chats':
                folder = ChatFolder.objects.filter(user=user, name=folder_name).first() if folder_name else None
                if folder_name and not folder:
                    raise ValidationError('Папка персональных настроек отсутствует')
                obj.folder_id = folder.pk if folder else None
            for key, value in images.items():
                if value:
                    file = getattr(obj, key)
                    file.save(value.name, value, save=False)
                    saved_files.append((file.storage, file.name))
                else:
                    setattr(obj, key, '')
            obj.save()
            if section == 'folders':
                obj.chats.all().delete()
                for parent in folder_chats:
                    ChatFolderChat.objects.get_or_create(folder=obj, chat_id=parent.public_id, chat_type=service.chat_kind(parent), defaults={'conversation': service.get_conversation(parent)})
            elif section == 'private_chats' and 'is_hidden' in values:
                ConversationUserState.objects.update_or_create(conversation=service.get_conversation(chat), user=user, defaults={'hidden': obj.is_hidden})
            if chat:
                transaction.on_commit(lambda parent=chat: SettingsCache.invalidate(user.pk, service.chat_kind(parent), parent.pk))
            imported[section] += 1
        transaction.on_commit(lambda: SettingsVersioning.increment_version(user.pk))
        return {'success': True, 'imported': imported}
    except Exception:
        for storage, name in saved_files:
            storage.delete(name)
        raise
