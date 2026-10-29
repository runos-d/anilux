from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from pathlib import Path
import random
from apps.users.infrastructure.models.users import (
    FavoriteEpisode,
    FavoriteTheme,
    User,
    UserFavorite,
    UserSession,
    UserSettings,
    UserProfileSettings,
    TwoFactorAuth,
    ActiveSession,
    NotificationSettings,
    PrivacySettings,
    UserTheme,
    ChatBackground,
    UserActivitySummary,
    EmailLog,
    MessageNotification,
    UserLibrary,
    SupportTicket,
    SupportMessage,
)


class PrivacyListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        from apps.users.application.privacy import prepare_privacy
        rows = data.all() if hasattr(data, 'all') else data
        return super().to_representation(prepare_privacy(
            rows, getattr(self.context.get('request'), 'user', None), self.child.fields,
        ))


class PrivacyProjectionMixin:
    def to_representation(self, instance):
        from apps.users.application.privacy import project_user
        return project_user(super().to_representation(instance), instance, getattr(self.context.get("request"), "user", None))


class UserSimpleSerializer(PrivacyProjectionMixin, serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        list_serializer_class = PrivacyListSerializer
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "display_name",
            "avatar_url",
            "is_online",
            "last_login",
            "level",
            "bio",
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        def_ava_dir = Path(settings.MEDIA_ROOT) / "def_avatars"
        if def_ava_dir.exists():
            jpg_files = list(def_ava_dir.glob("*.jpg")) + list(def_ava_dir.glob("*.jpeg"))
            if jpg_files:
                selected_index = obj.id % len(jpg_files)
                selected_file = jpg_files[selected_index]
                return f"/data/media/def_avatars/{selected_file.name}"
        return None

    def get_display_name(self, obj):
        return obj.display_name or obj.nickname or obj.username


class UserSerializer(PrivacyProjectionMixin, serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    display_name_computed = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    nickname_color = serializers.SerializerMethodField()
    nickname_gradient_start = serializers.SerializerMethodField()
    nickname_gradient_end = serializers.SerializerMethodField()
    nickname_glow_enabled = serializers.SerializerMethodField()
    nickname_glow_color = serializers.SerializerMethodField()
    nickname_glow_intensity = serializers.SerializerMethodField()

    class Meta:
        list_serializer_class = PrivacyListSerializer
        model = User
        fields = [
            "id",
            "unique_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "display_name_computed",
            "nickname",
            "phone_number",
            "avatar",
            "avatar_url",
            "cover_image",
            "cover_image_url",
            "cover_position_x",
            "cover_position_y",
            "bio",
            "favorite_genres",
            "website",
            "vk_profile",
            "telegram",
            "github",
            "discord",
            "twitter",
            "social_links",
            "email_verified",
            "phone_verified",
            "two_factor_enabled",
            "is_online",
            "last_login",
            "created_at",
            "updated_at",
            "level",
            "experience",
            "mana",
            "badges",
            "posts_count",
            "comments_count",
            "likes_received",
            "playlists_count",
            "followers_count",
            "following_count",
            "is_staff",
            "is_admin",
            "is_premium",
            "nickname_color",
            "nickname_gradient_start",
            "nickname_gradient_end",
            "nickname_glow_enabled",
            "nickname_glow_color",
            "nickname_glow_intensity",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "created_at",
            "updated_at",
            "level",
            "experience",
            "mana",
            "badges",
            "posts_count",
            "comments_count",
            "likes_received",
            "playlists_count",
            "is_staff", "email", "phone_number", "email_verified", "phone_verified", "two_factor_enabled",
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        def_ava_dir = Path(settings.MEDIA_ROOT) / "def_avatars"
        if def_ava_dir.exists():
            jpg_files = list(def_ava_dir.glob("*.jpg")) + list(def_ava_dir.glob("*.jpeg"))
            if jpg_files:
                selected_index = obj.id % len(jpg_files)
                selected_file = jpg_files[selected_index]
                return f"/data/media/def_avatars/{selected_file.name}"
        return None

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_display_name_computed(self, obj):
        return obj.display_name or obj.nickname or obj.username

    def get_is_admin(self, obj):
        return obj.is_staff or obj.is_superuser

    def get_is_premium(self, obj):
        try:
            return obj.subscription.is_premium
        except Exception:
            return False

    def get_social_links(self, obj):
        try:
            profile = obj.profile_settings
            return getattr(profile, "social_links", []) or []
        except Exception:
            return []

    def get_nickname_color(self, obj):
        try:
            return obj.profile_settings.nickname_color or None
        except Exception:
            return None

    def get_nickname_gradient_start(self, obj):
        try:
            return obj.profile_settings.nickname_gradient_start or None
        except Exception:
            return None

    def get_nickname_gradient_end(self, obj):
        try:
            return obj.profile_settings.nickname_gradient_end or None
        except Exception:
            return None

    def get_nickname_glow_enabled(self, obj):
        try:
            return obj.profile_settings.nickname_glow_enabled or False
        except Exception:
            return False

    def get_nickname_glow_color(self, obj):
        try:
            return obj.profile_settings.nickname_glow_color or None
        except Exception:
            return None

    def get_nickname_glow_intensity(self, obj):
        try:
            return obj.profile_settings.nickname_glow_intensity or 1
        except Exception:
            return 1


class PublicUserSerializer(PrivacyProjectionMixin, serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    display_name_computed = serializers.SerializerMethodField()

    class Meta:
        list_serializer_class = PrivacyListSerializer
        model = User
        fields = [
            "id", "username", "nickname", "display_name",
            "display_name_computed",
            "avatar", "avatar_url","cover_image", "cover_image_url",
            "bio", "is_online", "posts_count", "comments_count",
            "likes_received", "playlists_count", "level", "experience",
            "created_at",
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_display_name_computed(self, obj):
        return obj.display_name or obj.nickname or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают")

        email = data.get("email", "").strip().lower()
        if not email:
            raise serializers.ValidationError({"email": "Email обязателен"})
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "Этот email уже используется"})
        data["email"] = email

        from django.contrib.auth.password_validation import validate_password
        validate_password(data["password"])

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        if not user.nickname:
            user.nickname = user.username
        if not user.display_name:
            user.display_name = user.username

        def_ava_dir = Path(settings.MEDIA_ROOT) / "def_avatars"
        if def_ava_dir.exists():
            jpg_files = list(def_ava_dir.glob("*.jpg")) + list(def_ava_dir.glob("*.jpeg"))
            if jpg_files:
                selected_avatar = random.choice(jpg_files)
                from django.core.files import File
                with open(selected_avatar, 'rb') as f:
                    user.avatar.save(f"def_{selected_avatar.name}", File(f), save=False)

        user.save(update_fields=["nickname", "display_name", "avatar"])
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data["email"].strip().lower()
        user_record = User.objects.filter(email__iexact=email).only("username").first()
        user = authenticate(
            username=user_record.username if user_record else "",
            password=data["password"],
        )
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")
        data["user"] = user
        return data


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    action = serializers.ChoiceField(choices=["send", "verify"])
    code = serializers.CharField(required=False, min_length=6, max_length=6)


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    action = serializers.ChoiceField(choices=["send", "verify"])
    code = serializers.CharField(required=False, min_length=8, max_length=8)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "display_name",
            "nickname",
            "avatar",
            "cover_image",
            "cover_image_url",
            "cover_position_x",
            "cover_position_y",
            "bio",
            "favorite_genres",
            "website",
            "vk_profile",
            "telegram",
            "github",
            "discord",
            "twitter",
        ]

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def validate_nickname(self, value):
        if (
            value
            and User.objects.filter(nickname=value)
            .exclude(id=self.instance.id if self.instance else None)
            .exists()
        ):
            raise serializers.ValidationError("Этот nickname уже занят")
        return value

    def validate_cover_image(self, value):
        if value:
            if hasattr(value, "size") and value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "Размер файла не должен превышать 10MB"
                )
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            "id",
            "session_key",
            "device_info",
            "ip_address",
            "location",
            "last_activity",
            "created_at",
            "is_current",
        ]
        read_only_fields = ["id", "session_key", "created_at"]

    def get_is_current(self, obj):
        from django.utils import timezone

        return (timezone.now() - obj.last_activity).seconds < 300


class UserSettingsSerializer(serializers.ModelSerializer):
    def validate_theme(self, value):
        valid_themes = ["light", "dark", "auto"]
        if value not in valid_themes:
            raise serializers.ValidationError(
                f"Недопустимая тема. Допустимые значения: {', '.join(valid_themes)}"
            )
        return value

    def validate_ui_style(self, value):
        valid_styles = ["modern", "classic", "minimal", "dark"]
        if value not in valid_styles:
            raise serializers.ValidationError(
                f"Недопустимый стиль интерфейса. Допустимые значения: {', '.join(valid_styles)}"
            )
        return value

    def validate_text_size(self, value):
        valid_sizes = ["small", "medium", "large"]
        if value not in valid_sizes:
            raise serializers.ValidationError(
                f"Недопустимый размер текста. Допустимые значения: {', '.join(valid_sizes)}"
            )
        return value

    def validate_selected_interests(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("selected_interests должен быть списком")

        if len(value) > 20:
            raise serializers.ValidationError("Максимум 20 интересов")

        if not all(isinstance(interest, str) for interest in value):
            raise serializers.ValidationError("Все интересы должны быть строками")

        for interest in value:
            if len(interest) > 50:
                raise serializers.ValidationError(
                    "Длина каждого интереса не должна превышать 50 символов"
                )

        return value

    class Meta:
        model = UserSettings
        fields = [
            "theme",
            "ui_style",
            "text_size",
            "push_notifications",
            "email_notifications",
            "message_notifications",
            "contest_notifications",
            "show_in_search",
            "show_online_status",
            "show_stats",
            "personalized_recommendations",
            "selected_interests",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class NicknameCheckSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=30)

    def validate_nickname(self, value):
        if not value.replace("_", "").replace("-", "").isalnum():
            raise serializers.ValidationError(
                "Nickname может содержать только буквы, цифры, подчеркивания и дефисы"
            )

        available = not User.objects.filter(nickname=value).exists()
        if not available:
            raise serializers.ValidationError("Этот nickname уже занят")

        return value


class TwoFactorSetupSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["enable", "disable", "verify"])
    code = serializers.CharField(required=False, min_length=6, max_length=6)


class UserProfileSettingsSerializer(serializers.ModelSerializer):
    user_display_name = serializers.CharField(
        source="user.display_name", read_only=True
    )
    user_nickname = serializers.CharField(source="user.nickname", read_only=True)
    user_avatar = serializers.ImageField(source="user.avatar", read_only=True)
    user_bio = serializers.CharField(source="user.bio", read_only=True)
    user_favorite_genres = serializers.JSONField(
        source="user.favorite_genres", read_only=True
    )
    user_website = serializers.URLField(source="user.website", read_only=True)
    user_vk_profile = serializers.CharField(source="user.vk_profile", read_only=True)
    user_telegram = serializers.CharField(source="user.telegram", read_only=True)
    user_phone_number = serializers.CharField(
        source="user.phone_number", read_only=True
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfileSettings
        fields = ["id", "user", "updated_at", "user_display_name", "user_nickname", "user_avatar", "user_bio", "user_favorite_genres", "user_website", "user_vk_profile", "user_telegram", "user_phone_number", "user_email"]
        read_only_fields = ["user", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["notification_sound"] = instance.notification_sound
        data["vibration"] = instance.vibration
        data["preview_content"] = instance.preview_content
        return data

    def validate_theme(self, value):
        valid_themes = ["light", "dark", "system", "blue", "green", "red", "yellow", "banana", "sea", "lilac", "emerald", "peach", "blueberry", "rozovaya", "polnochnaya", "custom"]
        if value not in valid_themes:
            raise serializers.ValidationError(
                f"Недопустимая тема. Допустимые значения: {', '.join(valid_themes)}"
            )
        return value

    def validate_accent_color(self, value):
        import re

        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError(
                "Недопустимый формат цвета. Используйте формат #RRGGBB"
            )
        return value

    def validate_language(self, value):
        valid_languages = ["ru", "en", "uk", "be", "kk"]
        if value not in valid_languages:
            raise serializers.ValidationError(
                f"Недопустимый язык. Допустимые значения: {', '.join(valid_languages)}"
            )
        return value

    def validate_timezone(self, value):
        try:
            import pytz

            pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError:
            raise serializers.ValidationError(f"Недопустимый часовой пояс: {value}")
        return value


class NotificationSettingsSerializer(serializers.ModelSerializer):
    enabled = serializers.BooleanField(required=False)
    sound_enabled = serializers.BooleanField(required=False)
    vibration_enabled = serializers.BooleanField(required=False)
    preview_enabled = serializers.BooleanField(required=False)

    push_sound_enabled = serializers.BooleanField(required=False, source="push_sound")
    push_vibration_enabled = serializers.BooleanField(
        required=False, source="push_vibration"
    )
    push_preview_enabled = serializers.BooleanField(
        required=False, source="push_preview"
    )

    class Meta:
        model = NotificationSettings
        fields = ["id", "user", "updated_at", "message_notifications", "group_notifications", "call_notifications", "mention_notifications", "reaction_notifications", "push_enabled", "push_sound", "push_vibration", "push_preview", "email_enabled", "email_frequency", "mute_until", "do_not_disturb_start", "do_not_disturb_end", "override_chat_settings", "enabled", "sound_enabled", "vibration_enabled", "preview_enabled", "push_sound_enabled", "push_vibration_enabled", "push_preview_enabled"]
        read_only_fields = ["user", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["enabled"] = True
        data["sound_enabled"] = True
        data["vibration_enabled"] = (
            instance.push_vibration if hasattr(instance, "push_vibration") else True
        )
        data["preview_enabled"] = (
            instance.push_preview if hasattr(instance, "push_preview") else True
        )
        data["push_sound_enabled"] = (
            instance.push_sound if hasattr(instance, "push_sound") else True
        )
        data["push_vibration_enabled"] = (
            instance.push_vibration if hasattr(instance, "push_vibration") else True
        )
        data["push_preview_enabled"] = (
            instance.push_preview if hasattr(instance, "push_preview") else True
        )
        data["do_not_disturb_enabled"] = (
            instance.do_not_disturb_start is not None
            and instance.do_not_disturb_end is not None
        )
        return data

    def validate_email_frequency(self, value):
        valid_frequencies = ["immediately", "hourly", "daily", "weekly"]
        if value not in valid_frequencies:
            raise serializers.ValidationError(
                f"Недопустимая частота. Допустимые значения: {', '.join(valid_frequencies)}"
            )
        return value

    def validate(self, data):
        do_not_disturb_start = data.get(
            "do_not_disturb_start",
            self.instance.do_not_disturb_start if self.instance else None,
        )
        do_not_disturb_end = data.get(
            "do_not_disturb_end",
            self.instance.do_not_disturb_end if self.instance else None,
        )

        if do_not_disturb_start and do_not_disturb_end:
            if do_not_disturb_start >= do_not_disturb_end:
                raise serializers.ValidationError(
                    "Время начала должно быть раньше времени окончания"
                )

        return data


class PrivacySettingsSerializer(serializers.ModelSerializer):
    blocked_users_list = serializers.SerializerMethodField()

    show_online_status = serializers.BooleanField(required=False)
    show_last_seen = serializers.BooleanField(required=False)
    show_typing_status = serializers.BooleanField(required=False)
    allow_calls = serializers.BooleanField(required=False)
    allow_group_invites = serializers.BooleanField(required=False)

    class Meta:
        model = PrivacySettings
        fields = ["id", "user", "who_can_see_phone", "who_can_see_email", "who_can_see_last_seen", "who_can_see_profile_photo", "blocked_users", "allow_message_forwarding", "who_can_call", "who_can_add_to_groups", "blocked_users_list", "show_online_status", "show_last_seen", "show_typing_status", "allow_calls", "allow_group_invites", "analytics_consent_state", "analytics_consent_version", "analytics_consent_updated_at", "analytics_consent_source"]
        read_only_fields = ["user"]

    def to_representation(self, instance):
        from django.conf import settings

        data = super().to_representation(instance)
        if instance.analytics_consent_version != settings.ANALYTICS_CONSENT_POLICY_VERSION:
            data["analytics_consent_state"] = "unknown"
            data["analytics_consent_version"] = settings.ANALYTICS_CONSENT_POLICY_VERSION
            data["analytics_consent_updated_at"] = None
        try:
            profile_settings = instance.user.profile_settings
            data["show_online_status"] = profile_settings.show_online_status
            data["show_last_seen"] = profile_settings.show_last_seen
            data["show_typing_status"] = profile_settings.show_typing_status
            data["allow_calls"] = profile_settings.allow_calls
            data["allow_group_invites"] = profile_settings.allow_group_invites
        except:
            data["show_online_status"] = True
            data["show_last_seen"] = True
            data["show_typing_status"] = True
            data["allow_calls"] = True
            data["allow_group_invites"] = True
        return data

    def validate(self, attrs):
        from django.conf import settings

        state = attrs.get("analytics_consent_state")
        version = attrs.get("analytics_consent_version")
        if state in ("granted", "denied") and version != settings.ANALYTICS_CONSENT_POLICY_VERSION:
            raise serializers.ValidationError({
                "analytics_consent_version": "Версия политики согласия устарела."
            })
        source = attrs.get("analytics_consent_source")
        if source and source not in ("banner", "settings", "server", "policy_upgrade"):
            raise serializers.ValidationError({"analytics_consent_source": "Недопустимый источник."})
        return attrs

    def update(self, instance, validated_data):
        from django.db import transaction
        from django.utils import timezone
        from apps.users.infrastructure.models.users import UserProfileSettings

        profile_fields = {
            key: validated_data.pop(key)
            for key in ("show_online_status", "show_last_seen", "show_typing_status", "allow_calls", "allow_group_invites")
            if key in validated_data
        }
        if "analytics_consent_state" in validated_data:
            validated_data["analytics_consent_updated_at"] = timezone.now()
        with transaction.atomic():
            result = super().update(instance, validated_data)
            if profile_fields:
                profile, _ = UserProfileSettings.objects.get_or_create(user=instance.user)
                for key, value in profile_fields.items():
                    setattr(profile, key, value)
                profile.save(update_fields=list(profile_fields))
        return result

    def get_blocked_users_list(self, obj):
        return UserSimpleSerializer(obj.blocked_users.all(), many=True).data

    def validate_who_can_see_phone(self, value):
        valid_values = ["everyone", "contacts", "nobody"]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Недопустимое значение. Допустимые: {', '.join(valid_values)}"
            )
        return value

    def validate_who_can_see_email(self, value):
        valid_values = ["everyone", "contacts", "nobody"]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Недопустимое значение. Допустимые: {', '.join(valid_values)}"
            )
        return value

    def validate_who_can_see_last_seen(self, value):
        valid_values = ["everyone", "contacts", "nobody"]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Недопустимое значение. Допустимые: {', '.join(valid_values)}"
            )
        return value

    def validate_who_can_see_profile_photo(self, value):
        valid_values = ["everyone", "contacts", "nobody"]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Недопустимое значение. Допустимые: {', '.join(valid_values)}"
            )
        return value

    def validate_who_can_call(self, value):
        valid_values = ["everyone", "contacts", "nobody"]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Недопустимое значение. Допустимые: {', '.join(valid_values)}"
            )
        return value

    def validate_who_can_add_to_groups(self, value):
        valid_values = ["everyone", "contacts", "nobody"]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Недопустимое значение. Допустимые: {', '.join(valid_values)}"
            )
        return value


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    has_backup_codes = serializers.SerializerMethodField()
    backup_codes_count = serializers.SerializerMethodField()

    class Meta:
        model = TwoFactorAuth
        fields = ["id", "user", "is_enabled", "phone_number", "email_enabled", "require_on_new_device", "remember_device_days", "created_at", "last_used", "qr_code_url", "has_backup_codes", "backup_codes_count"]
        read_only_fields = ["user", "secret_key", "created_at", "last_used"]
        extra_kwargs = {"backup_codes": {"write_only": True}}

    def get_qr_code_url(self, obj):
        if obj.secret_key:
            return f"/api/auth/2fa/qr/{obj.user.id}/"
        return None

    def get_has_backup_codes(self, obj):
        return len(obj.backup_codes) > 0

    def get_backup_codes_count(self, obj):
        return len(obj.backup_codes)


class TwoFactorSettingsSerializer(serializers.Serializer):
    require_on_new_device = serializers.BooleanField(required=False)
    remember_device_days = serializers.IntegerField(
        required=False, min_value=1, max_value=365
    )
    email_enabled = serializers.BooleanField(required=False)
    phone_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20
    )

    def validate_phone_number(self, value):
        if value:
            user = self.context["request"].user
            if not user.phone_verified:
                raise serializers.ValidationError(
                    "Необходимо подтвердить номер телефона для использования SMS 2FA"
                )
        return value


class ActiveSessionSerializer(serializers.ModelSerializer):
    session_key = serializers.CharField(source="pk", read_only=True)
    ip_address = serializers.CharField(read_only=True)
    device_name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    is_current_device = serializers.SerializerMethodField()

    def get_is_current_device(self, obj):
        from apps.users.application.token_sessions import current_session_key
        request = self.context.get("request")
        return bool(request and current_session_key(request) == obj.session_key)

    class Meta:
        model = ActiveSession
        fields = "__all__"
        read_only_fields = ["user", "created_at", "last_activity"]

    def get_device_name(self, obj):
        device = obj.device_info.get("device", "Неизвестное устройство")
        browser = obj.device_info.get("browser", "Неизвестный браузер")
        return f"{device} ({browser})"

    def get_location(self, obj):
        if obj.country and obj.city:
            return f"{obj.city}, {obj.country}"
        return "Неизвестно"


class UserThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTheme
        fields = ["id", "user", "name", "is_active", "primary_color", "secondary_color", "background_color", "card_background", "hover_background", "text_color", "secondary_text_color", "border_color", "message_bubble_radius", "show_message_time", "compact_mode", "chat_background", "chat_background_opacity", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class ChatBackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatBackground
        fields = ["id", "user", "name", "image", "thumbnail", "is_default", "opacity", "created_at"]
        read_only_fields = ["user", "created_at"]


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = ["id", "user", "subject", "sent_at"]
        read_only_fields = ["user", "sent_at"]


class MessageNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageNotification
        fields = ["id", "user", "message", "notified_via", "notified_at"]
        read_only_fields = ["user", "notified_at"]


class UserActivitySummarySerializer(serializers.ModelSerializer):
    weekly_report = serializers.SerializerMethodField()

    class Meta:
        model = UserActivitySummary
        fields = ["id", "user", "messages_sent", "messages_received", "media_sent", "calls_made", "time_spent", "favorite_chat_type", "most_active_hour", "average_response_time", "primary_device", "last_used_device", "last_updated", "collected_since", "weekly_report"]
        read_only_fields = ["user", "last_updated", "collected_since"]

    def get_weekly_report(self, obj):
        return obj.get_weekly_report()


class UserFavoriteSerializer(serializers.ModelSerializer):
    anime_title_ru = serializers.CharField(source="anime.title_ru", read_only=True)
    anime_title_en = serializers.CharField(source="anime.title_en", read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_episodes = serializers.IntegerField(source="anime.episodes", read_only=True)
    anime_kind = serializers.CharField(source="anime.kind", read_only=True)
    anime_year = serializers.IntegerField(source="anime.year", read_only=True)

    class Meta:
        model = UserFavorite
        fields = [
            "id",
            "anime",
            "anime_title_ru",
            "anime_title_en",
            "anime_poster",
            "anime_episodes",
            "anime_kind",
            "anime_year",
            "added_at",
        ]
        read_only_fields = ["id", "user", "added_at"]

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, "url"):
            return obj.anime.poster.url
        if obj.anime.poster_url:
            return obj.anime.poster_url
        return None


class FavoriteThemeSerializer(serializers.ModelSerializer):
    anime_title_ru = serializers.CharField(source="anime.title_ru", read_only=True)
    anime_title_en = serializers.CharField(source="anime.title_en", read_only=True)
    anime_slug = serializers.CharField(source="anime.slug", read_only=True)
    theme_type_display = serializers.CharField(
        source="get_theme_type_display", read_only=True
    )

    class Meta:
        model = FavoriteTheme
        fields = [
            "id",
            "anime",
            "anime_slug",
            "anime_title_ru",
            "anime_title_en",
            "theme_type",
            "theme_type_display",
            "episode",
            "season",
            "title",
            "start_time",
            "end_time",
            "added_at",
        ]
        read_only_fields = ["id", "user", "added_at"]


class FavoriteEpisodeSerializer(serializers.ModelSerializer):
    anime_title_ru = serializers.CharField(source="anime.title_ru", read_only=True)
    anime_title_en = serializers.CharField(source="anime.title_en", read_only=True)
    anime_poster = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteEpisode
        fields = [
            "id",
            "anime",
            "anime_title_ru",
            "anime_title_en",
            "anime_poster",
            "episode",
            "season",
            "note",
            "added_at",
        ]
        read_only_fields = ["id", "user", "added_at"]

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, "url"):
            return obj.anime.poster.url
        if obj.anime.poster_url:
            return obj.anime.poster_url
        return None


class UserLibrarySerializer(serializers.ModelSerializer):
    anime_title_ru = serializers.CharField(source="anime.title_ru", read_only=True)
    anime_title_en = serializers.CharField(source="anime.title_en", read_only=True)
    anime_slug = serializers.CharField(source="anime.slug", read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_episodes_count = serializers.SerializerMethodField()
    anime_status = serializers.CharField(source="anime.status", read_only=True)
    anime_kind = serializers.CharField(source="anime.kind", read_only=True)
    anime_year = serializers.IntegerField(source="anime.year", read_only=True)
    anime_score = serializers.FloatField(source="anime.score", read_only=True)
    anime_genres = serializers.JSONField(source="anime.genres", read_only=True)
    anime_status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    progress_percentage = serializers.SerializerMethodField()
    episodes_watched = serializers.SerializerMethodField()

    class Meta:
        model = UserLibrary
        fields = [
            "id",
            "user",
            "anime",
            "anime_title_ru",
            "anime_title_en",
            "anime_slug",
            "anime_poster",
            "anime_episodes_count",
            "anime_status",
            "anime_kind",
            "anime_year",
            "anime_score",
            "anime_genres",
            "status",
            "anime_status_display",
            "current_season",
            "current_episode",
            "episodes_watched",
            "rating",
            "added_at",
            "started_at",
            "completed_at",
            "updated_at",
            "notes",
            "is_favorite",
            "rewatch_count",
            "progress_percentage",
        ]
        read_only_fields = ["id", "user", "added_at", "updated_at"]

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, "url"):
            return obj.anime.poster.url
        if obj.anime.poster_url:
            return obj.anime.poster_url
        return None

    def get_anime_episodes_count(self, obj):
        return obj.anime.progress_total or obj.anime.episodes or 0

    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()

    def get_episodes_watched(self, obj):
        return obj.effective_episodes_watched


class UserLibraryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLibrary
        fields = [
            "anime",
            "status",
            "rating",
            "notes",
            "is_favorite",
            "current_season",
            "current_episode",
            "episodes_watched",
        ]
        extra_kwargs = {
            "status": {"required": False},
            "current_season": {"required": False},
            "current_episode": {"required": False},
            "episodes_watched": {"required": False},
        }

    def create(self, validated_data):
        user = self.context["request"].user
        anime = validated_data["anime"]
        episodes_watched = validated_data.pop("episodes_watched", None)

        library_item, created = UserLibrary.objects.get_or_create(
            user=user, anime=anime, defaults=validated_data
        )

        if "status" in validated_data:
            library_item.user_set_status = True

        if not created:
            for key, value in validated_data.items():
                if key != "anime":
                    setattr(library_item, key, value)
            library_item.save()
        elif "status" in validated_data:
            library_item.save(update_fields=["user_set_status", "updated_at"])

        if episodes_watched is not None:
            from apps.users.application.library_episodes import set_watched_progress
            set_watched_progress(
                user, anime, episodes_watched,
                season=library_item.current_season or 1,
            )
            library_item.refresh_from_db()

        return library_item


class UserLibraryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLibrary
        fields = [
            "status",
            "current_season",
            "current_episode",
            "episodes_watched",
            "rating",
            "notes",
            "is_favorite",
        ]

    def update(self, instance, validated_data):
        episodes_watched = validated_data.pop("episodes_watched", None)

        if "status" in validated_data:
            instance.status = validated_data["status"]
            instance.user_set_status = True
            if instance.status == "started" and not instance.started_at:
                instance.started_at = timezone.now()
            if instance.status == "completed" and not instance.completed_at:
                instance.completed_at = timezone.now()

        for attr, value in validated_data.items():
            if attr != "status":
                setattr(instance, attr, value)

        instance.save()
        if episodes_watched is not None:
            from apps.users.application.library_episodes import set_watched_progress
            set_watched_progress(
                instance.user, instance.anime, episodes_watched,
                season=instance.current_season or 1,
            )
            instance.refresh_from_db()
        return instance


class UserLibraryProgressSerializer(serializers.Serializer):
    episode = serializers.IntegerField(min_value=0)

    def validate_episode(self, value):
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать минимум 8 символов"
            )

        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)

        if not has_letter:
            raise serializers.ValidationError(
                "Пароль должен содержать минимум одну букву"
            )
        if not has_digit:
            raise serializers.ValidationError(
                "Пароль должен содержать минимум одну цифру"
            )

        user = self.context["request"].user
        if user.username.lower() in value.lower():
            raise serializers.ValidationError("Пароль не должен содержать ваш логин")
        if user.email and user.email.split("@")[0].lower() in value.lower():
            raise serializers.ValidationError(
                "Пароль не должен содержать часть вашего email"
            )

        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Пароли не совпадают"}
            )

        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "Новый пароль должен отличаться от текущего"}
            )

        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()

        from apps.users.infrastructure.models.users import SecurityLog

        SecurityLog.objects.create(
            user=user,
            action="password_changed",
            ip_address=self.get_client_ip(self.context["request"]),
            user_agent=self.context["request"].META.get("HTTP_USER_AGENT", ""),
        )

        from core.redis_events import publish_password_changed

        publish_password_changed(user.id)

        self.terminate_other_sessions(user)

        return user

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def terminate_other_sessions(self, user):
        from django.contrib.sessions.models import Session
        from django.contrib.sessions.middleware import get_current_session_key

        current_key = get_current_session_key()

        user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        sessions_to_delete = []

        for session in user_sessions:
            session_data = session.get_decoded()
            if (
                "_auth_user_id" in session_data
                and str(user.id) == session_data["_auth_user_id"]
                and session.session_key != current_key
            ):
                sessions_to_delete.append(session.session_key)

        Session.objects.filter(session_key__in=sessions_to_delete).delete()

        from apps.users.infrastructure.models.users import ActiveSession

        ActiveSession.objects.filter(session_key__in=sessions_to_delete).delete()




class SupportMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_avatar = serializers.SerializerMethodField()
    is_from_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = SupportMessage
        fields = [
            "id",
            "ticket",
            "sender",
            "sender_username",
            "sender_avatar",
            "message",
            "is_from_admin",
            "attachments",
            "created_at",
            "is_read",
        ]
        read_only_fields = ["id", "ticket", "sender", "created_at", "is_read"]

    def get_sender_avatar(self, obj):
        if obj.sender.avatar:
            return obj.sender.avatar.url
        return None


class SupportTicketSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    messages = SupportMessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "user",
            "user_username",
            "user_avatar",
            "subject",
            "description",
            "category",
            "status",
            "priority",
            "assigned_to",
            "chat_id",
            "messages",
            "unread_count",
            "last_message",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "chat_id"]

    def get_user_avatar(self, obj):
        if obj.user.avatar:
            return obj.user.avatar.url
        return None

    def get_unread_count(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user:
            return 0
        if user.is_staff or user.is_superuser:
            return obj.messages.filter(is_read=False).exclude(sender=user).count()
        return obj.messages.filter(is_read=False, sender=user).count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return SupportMessageSerializer(last_msg).data
        return None


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ["subject", "description", "category", "priority"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "display_name",
            "nickname",
            "bio",
            "website",
            "vk_profile",
            "telegram",
            "github",
            "discord",
            "twitter",
            "favorite_genres",
            "avatar",
            "cover_image",
            "cover_image_url",
            "cover_position_x",
            "cover_position_y",
        ]

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def validate_nickname(self, value):
        if value and User.objects.filter(nickname=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Этот nickname уже занят")
        return value


class UserNotificationSettingsSerializer(serializers.Serializer):
    notify_likes = serializers.BooleanField(required=False)
    notify_comments = serializers.BooleanField(required=False)
    notify_mentions = serializers.BooleanField(required=False)
    email_digest = serializers.ChoiceField(choices=["never", "daily", "weekly"], required=False)


class SupportTicketListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "user",
            "user_username",
            "subject",
            "category",
            "status",
            "priority",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                "message": last_msg.message[:100] + "..."
                if len(last_msg.message) > 100
                else last_msg.message,
                "sender_username": last_msg.sender.username,
                "is_from_admin": last_msg.is_from_admin,
                "created_at": last_msg.created_at,
            }
        return None

    def get_unread_count(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user:
            return 0
        if user.is_staff or user.is_superuser:
            return obj.messages.filter(is_read=False).exclude(sender=user).count()
        return obj.messages.filter(is_read=False, sender=user).count()
