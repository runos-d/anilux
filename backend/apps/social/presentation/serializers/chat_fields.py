from rest_framework import serializers
from apps.social.infrastructure.models.social import PrivateChat, GroupChat


class PublicChatField(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        from apps.social.application.conversations import resolve_chat
        kind = 'private' if self.queryset.model is PrivateChat else 'group'
        return resolve_chat(data, self.context['request'].user, kind)

    def to_representation(self, value):
        return value.public_id


class ChatModelSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for name in ('chat', 'group_chat', 'private_chat'):
            field = fields.get(name)
            if isinstance(field, serializers.PrimaryKeyRelatedField):
                model = PrivateChat if name == 'private_chat' or self.Meta.model._meta.get_field(name).related_model is PrivateChat else GroupChat
                fields[name] = PublicChatField(queryset=None if field.read_only else model.objects.all(),
                    read_only=field.read_only, required=field.required, allow_null=field.allow_null)
        return fields
