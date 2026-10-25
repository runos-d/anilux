from rest_framework import serializers

from .models import Idea


class IdeaSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    is_voted = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Idea
        fields = [
            "id",
            "title",
            "description",
            "kind",
            "status",
            "priority",
            "admin_note",
            "votes_count",
            "author",
            "author_name",
            "author_avatar",
            "is_voted",
            "is_owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "admin_note",
            "status",
            "priority",
            "votes_count",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        return obj.author.display_name or obj.author.nickname or obj.author.username

    def get_author_avatar(self, obj):
        if not obj.author.avatar:
            return None
        request = self.context.get("request")
        url = obj.author.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_is_voted(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        voted_ids = self.context.get("voted_ids")
        if voted_ids is not None:
            return obj.id in voted_ids
        return obj.votes.filter(user=user).exists()

    def get_is_owner(self, obj):
        user = self.context["request"].user
        return user.is_authenticated and obj.author_id == user.id

    def validate_title(self, value):
        value = " ".join(value.split())
        if len(value) < 5:
            raise serializers.ValidationError("Опишите идею чуть подробнее.")
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 15:
            raise serializers.ValidationError("Описание должно содержать не менее 15 символов.")
        return value


class IdeaAdminSerializer(IdeaSerializer):
    class Meta(IdeaSerializer.Meta):
        read_only_fields = [
            "id",
            "author",
            "votes_count",
            "created_at",
            "updated_at",
        ]
