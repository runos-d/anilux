import json
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q



class SettingsCache:
    TIMEOUT = 300  

    @staticmethod
    def _key(user_id: int, chat_type: str, chat_id: int) -> str:
        return f"chat_settings:{user_id}:{chat_type}:{chat_id}"

    @staticmethod
    def _wallpaper_key(user_id: int, chat_type: str, chat_id: int) -> str:
        return f"chat_wallpaper:{user_id}:{chat_type}:{chat_id}"

    @staticmethod
    def _theme_key(user_id: int, chat_type: str, chat_id: int) -> str:
        return f"chat_theme:{user_id}:{chat_type}:{chat_id}"

    @classmethod
    def get_chat_settings(cls, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        key = cls._key(user_id, chat_type, chat_id)
        return cache.get(key)

    @classmethod
    def set_chat_settings(cls, user_id: int, chat_type: str, chat_id: int, data: Dict):
        key = cls._key(user_id, chat_type, chat_id)
        cache.set(key, data, timeout=cls.TIMEOUT)

    @classmethod
    def invalidate(cls, user_id: int, chat_type: str, chat_id: int):
        cache.delete(cls._key(user_id, chat_type, chat_id))
        cache.delete(cls._wallpaper_key(user_id, chat_type, chat_id))
        cache.delete(cls._theme_key(user_id, chat_type, chat_id))

    @classmethod
    def invalidate_all_for_chat(cls, chat_type: str, chat_id: int):
        pattern = f"chat_settings:*:{chat_type}:{chat_id}"
        try:
            from django.core.cache import cache as django_cache
            if hasattr(django_cache, 'delete_pattern'):
                django_cache.delete_pattern(pattern)
        except Exception:
            pass

    @classmethod
    def get_wallpaper(cls, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        key = cls._wallpaper_key(user_id, chat_type, chat_id)
        return cache.get(key)

    @classmethod
    def set_wallpaper(cls, user_id: int, chat_type: str, chat_id: int, data: Dict):
        cache.delete(cls._key(user_id, chat_type, chat_id))
        key = cls._wallpaper_key(user_id, chat_type, chat_id)
        cache.set(key, data, timeout=cls.TIMEOUT)

    @classmethod
    def get_theme(cls, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        key = cls._theme_key(user_id, chat_type, chat_id)
        return cache.get(key)

    @classmethod
    def set_theme(cls, user_id: int, chat_type: str, chat_id: int, data: Dict):
        cache.delete(cls._key(user_id, chat_type, chat_id))
        key = cls._theme_key(user_id, chat_type, chat_id)
        cache.set(key, data, timeout=cls.TIMEOUT)



class ChatSettingsService:
    PRESET_WALLPAPERS = [
        {'id': 'solid_dark', 'name': 'Тёмный', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#0f0f1a', 'wallpaper_color2': ''},
        {'id': 'solid_navy', 'name': 'Тёмно-синий', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#1a1a2e', 'wallpaper_color2': ''},
        {'id': 'solid_gray', 'name': 'Тёмно-серый', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#1c1c1c', 'wallpaper_color2': ''},
        {'id': 'solid_indigo', 'name': 'Индиго', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#1e1b4b', 'wallpaper_color2': ''},
        {'id': 'solid_black', 'name': 'Чёрный', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#000000', 'wallpaper_color2': ''},
        {'id': 'solid_white', 'name': 'Белый', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#f8f9fa', 'wallpaper_color2': ''},
        {'id': 'grad_blue_purple', 'name': 'Синий → Фиолетовый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#1a1a2e', 'wallpaper_color2': '#16213e',
         'gradient_angle': 135},
        {'id': 'grad_pink_orange', 'name': 'Розовый → Оранжевый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#831843', 'wallpaper_color2': '#9a3412',
         'gradient_angle': 135},
        {'id': 'grad_green_teal', 'name': 'Зелёный → Бирюзовый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#14532d', 'wallpaper_color2': '#134e4a',
         'gradient_angle': 135},
        {'id': 'grad_violet_pink', 'name': 'Фиолетовый → Розовый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#4c1d95', 'wallpaper_color2': '#831843',
         'gradient_angle': 135},
        {'id': 'grad_midnight', 'name': 'Полночь', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#0a0a1a', 'wallpaper_color2': '#1a1a3e',
         'gradient_angle': 180},
        {'id': 'grad_ocean', 'name': 'Океан', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#0c4a6e', 'wallpaper_color2': '#164e63',
         'gradient_angle': 135},
        {'id': 'pattern_dots', 'name': 'Точки', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#0f0f1a',
         'pattern_type': 'dots', 'pattern_color': '#3b82f6', 'pattern_opacity': 15},
        {'id': 'pattern_grid', 'name': 'Сетка', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#1a1a2e',
         'pattern_type': 'grid', 'pattern_color': '#6366f1', 'pattern_opacity': 10},
        {'id': 'pattern_waves', 'name': 'Волны', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#0f172a',
         'pattern_type': 'waves', 'pattern_color': '#0ea5e9', 'pattern_opacity': 20},
        {'id': 'pattern_hex', 'name': 'Шестиугольники', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#1e1b4b',
         'pattern_type': 'hexagon', 'pattern_color': '#8b5cf6', 'pattern_opacity': 15},
    ]

    PRESET_THEMES = [
        {
            'id': 'default_dark',
            'name': 'Тёмная (по умолчанию)',
            'theme': 'dark',
            'message_color_mine': '#3b82f6',
            'message_color_other': '#1e1e32',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#e2e8f0',
            'background_color': '#0f0f1a',
            'header_color': '#1a1a2e',
            'input_color': '#1e1e32',
            'accent_color': '#3b82f6',
        },
        {
            'id': 'anime_purple',
            'name': 'Аниме Фиолет',
            'theme': 'custom',
            'message_color_mine': '#8b5cf6',
            'message_color_other': '#2d1b69',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#ddd6fe',
            'background_color': '#1e1b4b',
            'header_color': '#2e2065',
            'input_color': '#312e81',
            'accent_color': '#8b5cf6',
        },
        {
            'id': 'sakura',
            'name': 'Сакура',
            'theme': 'custom',
            'message_color_mine': '#ec4899',
            'message_color_other': '#4a1942',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#fce7f3',
            'background_color': '#2d0a2e',
            'header_color': '#3b1040',
            'input_color': '#4a1942',
            'accent_color': '#ec4899',
        },
        {
            'id': 'ocean',
            'name': 'Океан',
            'theme': 'custom',
            'message_color_mine': '#0ea5e9',
            'message_color_other': '#0c2e4a',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#e0f2fe',
            'background_color': '#071826',
            'header_color': '#0c2e4a',
            'input_color': '#0f3a5c',
            'accent_color': '#0ea5e9',
        },
        {
            'id': 'forest',
            'name': 'Лес',
            'theme': 'custom',
            'message_color_mine': '#10b981',
            'message_color_other': '#0a2e1e',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#d1fae5',
            'background_color': '#071a0f',
            'header_color': '#0a2e1e',
            'input_color': '#0d3824',
            'accent_color': '#10b981',
        },
        {
            'id': 'light',
            'name': 'Светлая',
            'theme': 'light',
            'message_color_mine': '#3b82f6',
            'message_color_other': '#f1f5f9',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#1e293b',
            'background_color': '#f8fafc',
            'header_color': '#ffffff',
            'input_color': '#f1f5f9',
            'accent_color': '#3b82f6',
        },
    ]

    @classmethod
    def get_wallpaper_for_chat(cls, user, chat_type: str, chat_id: int) -> Optional[Dict]:
        cached = SettingsCache.get_wallpaper(user.id, chat_type, chat_id)
        if cached:
            return cached

        from ..models import ChatWallpaper

        if chat_type == 'group':
            wp = ChatWallpaper.objects.filter(user=user, chat_id=chat_id).first()
        else:
            wp = ChatWallpaper.objects.filter(user=user, private_chat_id=chat_id).first()

        if not wp:
            return None

        data = cls._wallpaper_to_dict(wp)
        SettingsCache.set_wallpaper(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def set_wallpaper_for_chat(cls, user, chat_type: str, chat_id: int, wallpaper_data: Dict) -> Dict:
        from ..models import ChatWallpaper

        defaults = {
            'wallpaper_type': wallpaper_data.get('wallpaper_type', 'solid'),
            'wallpaper_color': wallpaper_data.get('wallpaper_color', '#0f0f1a'),
            'wallpaper_color2': wallpaper_data.get('wallpaper_color2', ''),
            'wallpaper_intensity': wallpaper_data.get('wallpaper_intensity', 100),
            'wallpaper_blur': wallpaper_data.get('wallpaper_blur', 0),
            'wallpaper_motion': wallpaper_data.get('wallpaper_motion', 'none'),
            'gradient_angle': wallpaper_data.get('gradient_angle', 135),
            'pattern_type': wallpaper_data.get('pattern_type', ''),
            'pattern_color': wallpaper_data.get('pattern_color', ''),
            'pattern_opacity': wallpaper_data.get('pattern_opacity', 20),
        }

        if chat_type == 'group':
            wp, _ = ChatWallpaper.objects.update_or_create(
                user=user,
                chat_id=chat_id,
                defaults=defaults
            )
        else:
            wp, _ = ChatWallpaper.objects.update_or_create(
                user=user,
                private_chat_id=chat_id,
                defaults=defaults
            )

        data = cls._wallpaper_to_dict(wp)
        SettingsCache.set_wallpaper(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def reset_wallpaper(cls, user, chat_type: str, chat_id: int):
        from ..models import ChatWallpaper
        if chat_type == 'group':
            ChatWallpaper.objects.filter(user=user, chat_id=chat_id).delete()
        else:
            ChatWallpaper.objects.filter(user=user, private_chat_id=chat_id).delete()
        SettingsCache.invalidate(user.id, chat_type, chat_id)

    @classmethod
    def apply_preset_wallpaper(cls, user, chat_type: str, chat_id: int, preset_id: str) -> Optional[Dict]:
        preset = next((p for p in cls.PRESET_WALLPAPERS if p['id'] == preset_id), None)
        if not preset:
            return None
        return cls.set_wallpaper_for_chat(user, chat_type, chat_id, preset)

    @classmethod
    def get_theme_for_chat(cls, user, chat_type: str, chat_id: int) -> Optional[Dict]:
        cached = SettingsCache.get_theme(user.id, chat_type, chat_id)
        if cached:
            return cached

        from ..models import ChatTheme

        if chat_type == 'group':
            theme = ChatTheme.objects.filter(user=user, chat_id=chat_id).first()
        else:
            theme = ChatTheme.objects.filter(user=user, private_chat_id=chat_id).first()

        if not theme:
            return cls._default_theme()

        data = cls._theme_to_dict(theme)
        SettingsCache.set_theme(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def set_theme_for_chat(cls, user, chat_type: str, chat_id: int, theme_data: Dict) -> Dict:
        from ..models import ChatTheme

        fields = [
            'theme', 'message_color_mine', 'message_color_other',
            'message_text_color_mine', 'message_text_color_other',
            'bubble_style', 'bubble_border_radius', 'bubble_shadow',
            'font_family', 'font_size', 'font_size_px', 'font_weight', 'line_height',
            'time_format', 'time_color',
            'background_color', 'header_color', 'input_color',
            'input_text_color', 'accent_color', 'link_color',
            'message_animation', 'reaction_animation', 'typing_animation',
            'emoji_set', 'emoji_size',
            'show_avatars', 'show_usernames', 'compact_mode',
            'show_read_status', 'show_typing_indicator', 'message_grouping',
            'custom_css', 'anime_card_border_radius', 'playlist_card_border_radius',
        ]
        defaults = {k: v for k, v in theme_data.items() if k in fields}

        if chat_type == 'group':
            theme, _ = ChatTheme.objects.update_or_create(
                user=user, chat_id=chat_id, private_chat=None,
                defaults=defaults
            )
        else:
            theme, _ = ChatTheme.objects.update_or_create(
                user=user, chat=None, private_chat_id=chat_id,
                defaults=defaults
            )

        data = cls._theme_to_dict(theme)
        SettingsCache.set_theme(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def apply_preset_theme(cls, user, chat_type: str, chat_id: int, preset_id: str) -> Optional[Dict]:
        preset = next((p for p in cls.PRESET_THEMES if p['id'] == preset_id), None)
        if not preset:
            return None
        theme_data = {k: v for k, v in preset.items() if k != 'id' and k != 'name'}
        return cls.set_theme_for_chat(user, chat_type, chat_id, theme_data)

    @classmethod
    def get_all_settings_for_chat(cls, user, chat_type: str, chat_id: int) -> Dict:
        cached = SettingsCache.get_chat_settings(user.id, chat_type, chat_id)
        if cached:
            return cached

        wallpaper = cls.get_wallpaper_for_chat(user, chat_type, chat_id)
        theme = cls.get_theme_for_chat(user, chat_type, chat_id)

        data = {
            'wallpaper': wallpaper,
            'theme': theme or cls._default_theme(),
            'css_vars': cls._build_css_vars(wallpaper, theme),
        }

        SettingsCache.set_chat_settings(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def _wallpaper_to_dict(cls, wp) -> Dict:
        from django.conf import settings as django_settings
        data = {
            'id': wp.id,
            'wallpaper_type': wp.wallpaper_type,
            'wallpaper_color': wp.wallpaper_color,
            'wallpaper_color2': wp.wallpaper_color2,
            'wallpaper_intensity': wp.wallpaper_intensity,
            'wallpaper_blur': wp.wallpaper_blur,
            'wallpaper_motion': wp.wallpaper_motion,
            'gradient_angle': wp.gradient_angle,
            'pattern_type': wp.pattern_type,
            'pattern_color': wp.pattern_color,
            'pattern_opacity': wp.pattern_opacity,
            'css': wp.to_css(),
        }
        if wp.wallpaper_image:
            data['wallpaper_image_url'] = wp.wallpaper_image.url
        return data

    @classmethod
    def _theme_to_dict(cls, theme) -> Dict:
        data = {
            'id': theme.id,
            'theme': theme.theme,
            'message_color_mine': theme.message_color_mine,
            'message_color_other': theme.message_color_other,
            'message_text_color_mine': theme.message_text_color_mine,
            'message_text_color_other': theme.message_text_color_other,
            'bubble_style': theme.bubble_style,
            'bubble_border_radius': theme.bubble_border_radius,
            'bubble_shadow': theme.bubble_shadow,
            'anime_card_border_radius': theme.anime_card_border_radius,
            'playlist_card_border_radius': theme.playlist_card_border_radius,
            'font_family': theme.font_family,
            'font_size': theme.font_size,
            'font_size_px': theme.font_size_px,
            'font_weight': theme.font_weight,
            'line_height': theme.line_height,
            'time_format': theme.time_format,
            'time_color': theme.time_color,
            'background_color': theme.background_color,
            'header_color': theme.header_color,
            'input_color': theme.input_color,
            'input_text_color': theme.input_text_color,
            'accent_color': theme.accent_color,
            'link_color': theme.link_color,
            'message_animation': theme.message_animation,
            'reaction_animation': theme.reaction_animation,
            'typing_animation': theme.typing_animation,
            'emoji_set': theme.emoji_set,
            'emoji_size': theme.emoji_size,
            'show_avatars': theme.show_avatars,
            'show_usernames': theme.show_usernames,
            'compact_mode': theme.compact_mode,
            'show_read_status': theme.show_read_status,
            'show_typing_indicator': theme.show_typing_indicator,
            'message_grouping': theme.message_grouping,
            'custom_css': theme.custom_css,
            'css_vars': theme.to_css_vars(),
        }
        return data

    @classmethod
    def _default_theme(cls) -> Dict:
        return {
            'theme': 'default',
            'message_color_mine': '#3b82f6',
            'message_color_other': '#1e1e32',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#e2e8f0',
            'bubble_style': 'modern',
            'bubble_border_radius': 18,
            'bubble_shadow': False,
            'anime_card_border_radius': 12,
            'playlist_card_border_radius': 12,
            'font_family': 'system',
            'font_size': 'medium',
            'font_size_px': 14,
            'font_weight': 400,
            'line_height': 1.5,
            'time_format': '24h',
            'time_color': 'rgba(255,255,255,0.5)',
            'background_color': '#0f0f1a',
            'header_color': '#1a1a2e',
            'input_color': '#1e1e32',
            'input_text_color': '#e2e8f0',
            'accent_color': '#3b82f6',
            'link_color': '#60a5fa',
            'message_animation': 'slide',
            'reaction_animation': 'bounce',
            'typing_animation': 'dots',
            'emoji_set': 'default',
            'emoji_size': 'medium',
            'show_avatars': True,
            'show_usernames': True,
            'compact_mode': False,
            'show_read_status': True,
            'show_typing_indicator': True,
            'message_grouping': True,
            'custom_css': '',
            'css_vars': {
                '--msg-mine-bg': '#3b82f6',
                '--msg-other-bg': '#1e1e32',
                '--msg-mine-text': '#ffffff',
                '--msg-other-text': '#e2e8f0',
                '--chat-bg': '#0f0f1a',
                '--chat-header-bg': '#1a1a2e',
                '--chat-input-bg': '#1e1e32',
                '--chat-accent': '#3b82f6',
                '--msg-font-size': '14px',
                '--msg-border-radius': '18px',
            },
        }

    @classmethod
    def _build_css_vars(cls, wallpaper: Optional[Dict], theme: Optional[Dict]) -> Dict:
        css_vars = {}
        if theme:
            css_vars.update(theme.get('css_vars', {}))
        if wallpaper:
            css_vars['--chat-wallpaper-css'] = wallpaper.get('css', '')
        return css_vars



from dataclasses import dataclass, field
from typing import List


@dataclass
class PermissionResult:
    allowed: bool
    reason: str = ""
    missing_permissions: List[str] = field(default_factory=list)


from .chat_services import PermissionChecker


class RateLimiter:
    def __init__(self, user_id: int, action_type: str):
        self.user_id = user_id
        self.action_type = action_type
        self.redis_key = f"rate_limit:{user_id}:{action_type}"

    def check(self, limit: int = 10, period: int = 60) -> bool:
        current = cache.get(self.redis_key, 0)
        if current >= limit:
            return False
        new_val = current + 1
        cache.set(self.redis_key, new_val, timeout=period)
        return True

    def get_remaining(self, limit: int = 10) -> int:
        current = cache.get(self.redis_key, 0)
        return max(0, limit - current)

    def reset(self):
        cache.delete(self.redis_key)



class NotificationService:
    @staticmethod
    def send_to_chat(chat, event_type: str, data: Dict, exclude_users=None):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        exclude_ids = [u.id for u in (exclude_users or [])]
        for member in chat.members.all():
            if member.user_id in exclude_ids:
                continue
            try:
                async_to_sync(channel_layer.group_send)(
                    f"user_{member.user_id}",
                    {'type': 'chat_message', 'event': event_type, 'data': data}
                )
            except Exception:
                pass

    @staticmethod
    def send_to_user(user_id: int, event_type: str, data: Dict):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        try:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {'type': 'chat_message', 'event': event_type, 'data': data}
            )
        except Exception:
            pass



class AntiSpamService:
    def __init__(self, chat):
        self.chat = chat

    def check_message(self, message) -> Dict:
        violations = []
        from ..models import Message

        text = getattr(message, 'text', '') or ''
        user = getattr(message, 'sender', None)
        if not user:
            return {'clean': True, 'violations': []}

        recent = Message.objects.filter(
            sender=user, chat=self.chat,
            created_at__gte=timezone.now() - timezone.timedelta(seconds=5)
        ).count()
        if recent >= 5:
            violations.append({'type': 'flood', 'action': 'mute', 'duration': 300})

        if 'http' in text:
            link_count = Message.objects.filter(
                sender=user, chat=self.chat,
                text__contains='http',
                created_at__gte=timezone.now() - timezone.timedelta(seconds=60)
            ).count()
            if link_count >= 3:
                violations.append({'type': 'links', 'action': 'restrict_links'})

        if len(text) > 10:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7:
                violations.append({'type': 'caps', 'action': 'delete'})

        from ..models import AntiSpamRule
        rules = AntiSpamRule.objects.filter(chat=self.chat, enabled=True)
        for rule in rules:
            if rule.rule_type == 'spam_keywords' and rule.keywords:
                text_lower = text.lower()
                for kw in rule.keywords:
                    if kw.lower() in text_lower:
                        violations.append({'type': 'keyword', 'keyword': kw, 'action': rule.action})
                        break

        return {'clean': len(violations) == 0, 'violations': violations}



from .chat_services import ChatAnalytics


class SettingsExport:
    def export_user_settings(self, user) -> Dict:
        from .settings_transfer import export_settings
        return export_settings(user)

    def import_user_settings(self, user, data: Dict) -> Dict:
        from .settings_transfer import import_settings
        return import_settings(user, data)



class SettingsVersioning:
    @staticmethod
    def get_version(user_id: int) -> int:
        return cache.get(f"settings_version:{user_id}", 1)

    @staticmethod
    def increment_version(user_id: int):
        try:
            cache.incr(f"settings_version:{user_id}")
        except Exception:
            cache.set(f"settings_version:{user_id}", 2, timeout=86400)

    @staticmethod
    def sync_needed(user_id: int, client_version: int) -> bool:
        return SettingsVersioning.get_version(user_id) != client_version
