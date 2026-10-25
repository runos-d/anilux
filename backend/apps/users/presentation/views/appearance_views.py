import re

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.infrastructure.models.users import FontSettings, UserProfileSettings

THEMES = {"light", "dark", "system", "blue", "green", "red", "yellow", "banana", "sea", "lilac", "emerald", "peach", "blueberry", "rozovaya", "polnochnaya", "custom"}
BACKGROUNDS = {"default", "gradient", "stars", "mountains", "ocean"}
FONT_FAMILIES = {"Inter", "Roboto", "Open Sans", "Lato", "Montserrat", "anime", "system"}
FONT_WEIGHTS = {"normal", "bold"}
DENSITIES = {"compact", "comfortable", "spacious"}
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

CUSTOM_THEME_KEYS = {
    "bg",
    "containerBg",
    "sidebar",
    "topbar",
    "textPrimary",
    "textSecondary",
    "textTertiary",
    "btnDefault",
    "btnHover",
    "btnPress",
    "tabDefault",
    "tabHover",
    "tabActive",
    "accent",
}

BOOL_FIELDS = (
    "use_shared_background",
    "smooth_animations",
    "scroll_effects",
    "parallax_effect",
    "truncate_names",
    "compact_lists",
    "hide_avatars",
    "show_time_everywhere",
    "small_emojis",
    "high_contrast",
)

OVERLAY_FIELDS = (
    "sakura_enabled",
    "new_year_enabled",
    "halloween_enabled",
    "love_day_enabled",
)

FONT_DEFAULTS = {
    "font_family": "Inter",
    "font_size": 14,
    "line_height": 1.5,
    "font_weight": "normal",
}


def _is_bool(value):
    return isinstance(value, bool)


def _to_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _normalize_color_map(value, allowed_keys):
    if value is None:
        return {}, None
    if not isinstance(value, dict):
        return None, "Ожидается объект с парами ключ-значение"
    normalized = {}
    for key, item in value.items():
        if key not in allowed_keys:
            continue
        if item == "" or (isinstance(item, str) and HEX_COLOR_RE.match(item)):
            normalized[key] = item.lower()
        else:
            return None, f"По ключу {key} ожидается цвет вида #RRGGBB или пустое значение"
    return normalized, None


def _get_font_settings(user):
    return FontSettings.objects.filter(user=user).first()


def _theme_payload(profile, font):
    data = {
        "theme": profile.theme,
        "accent_color": profile.accent_color or "",
        "theme_accents": profile.theme_accents or {},
        "custom_theme": profile.custom_theme or {},
        "custom_background": profile.custom_background or "default",
    }
    for name in BOOL_FIELDS:
        data[name] = getattr(profile, name)
    for name in OVERLAY_FIELDS:
        data[name] = getattr(profile, name)

    data["font_family"] = font.font_family if font else FONT_DEFAULTS["font_family"]
    data["font_size"] = font.font_size if font else FONT_DEFAULTS["font_size"]
    data["line_spacing"] = font.line_height if font else FONT_DEFAULTS["line_height"]
    data["font_weight"] = font.font_weight if font else FONT_DEFAULTS["font_weight"]
    return data


class ThemeSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfileSettings.objects.filter(user=request.user).first()
        if profile is None:
            profile = UserProfileSettings(user=request.user)
        font = _get_font_settings(request.user)
        return Response(_theme_payload(profile, font))

    def put(self, request):
        data = request.data
        errors = {}
        profile_updates = {}
        font_updates = {}

        if "theme" in data:
            if data["theme"] in THEMES:
                profile_updates["theme"] = data["theme"]
            else:
                errors["theme"] = "Неизвестная тема"

        if "accent_color" in data:
            value = data["accent_color"] or ""
            if value == "" or (isinstance(value, str) and HEX_COLOR_RE.match(value)):
                profile_updates["accent_color"] = value.lower() if value else ""
            else:
                errors["accent_color"] = "Ожидается цвет вида #RRGGBB или пустое значение"

        if "theme_accents" in data:
            normalized, error = _normalize_color_map(data["theme_accents"], THEMES)
            if error:
                errors["theme_accents"] = error
            else:
                profile_updates["theme_accents"] = normalized

        if "custom_theme" in data:
            normalized, error = _normalize_color_map(data["custom_theme"], CUSTOM_THEME_KEYS)
            if error:
                errors["custom_theme"] = error
            else:
                profile_updates["custom_theme"] = normalized

        if "custom_background" in data:
            if data["custom_background"] in BACKGROUNDS:
                profile_updates["custom_background"] = data["custom_background"]
            else:
                errors["custom_background"] = "Неизвестный фон"

        for name in BOOL_FIELDS:
            if name in data:
                if _is_bool(data[name]):
                    profile_updates[name] = data[name]
                else:
                    errors[name] = "Ожидается true или false"

        for name in OVERLAY_FIELDS:
            if name in data:
                if data[name] is None or _is_bool(data[name]):
                    profile_updates[name] = data[name]
                else:
                    errors[name] = "Ожидается true, false или null"

        if "font_family" in data:
            if data["font_family"] in FONT_FAMILIES:
                font_updates["font_family"] = data["font_family"]
            else:
                errors["font_family"] = "Неизвестный шрифт"

        if "font_size" in data:
            value = _to_number(data["font_size"])
            if value is not None and 10 <= value <= 24:
                font_updates["font_size"] = int(round(value))
            else:
                errors["font_size"] = "Размер шрифта: от 10 до 24"

        if "line_spacing" in data:
            value = _to_number(data["line_spacing"])
            if value is not None and 1.0 <= value <= 2.2:
                font_updates["line_height"] = round(value, 2)
            else:
                errors["line_spacing"] = "Межстрочный интервал: от 1.0 до 2.2"

        if "font_weight" in data:
            if data["font_weight"] in FONT_WEIGHTS:
                font_updates["font_weight"] = data["font_weight"]
            else:
                errors["font_weight"] = "Ожидается normal или bold"

        if errors:
            detail = "; ".join(f"{name}: {text}" for name, text in errors.items())
            return Response({"errors": errors, "detail": detail}, status=400)

        profile, _ = UserProfileSettings.objects.get_or_create(user=request.user)
        for field, value in profile_updates.items():
            setattr(profile, field, value)
        if profile_updates:
            profile.save(update_fields=list(profile_updates.keys()))

        font = _get_font_settings(request.user)
        if font_updates:
            if font is None:
                font = FontSettings(user=request.user)
            for field, value in font_updates.items():
                setattr(font, field, value)
            font.save()

        return Response(_theme_payload(profile, font))

    patch = put
    post = put


class FontSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    FIELDS = (
        "font_family",
        "font_size",
        "interface_scale",
        "line_height",
        "density",
        "bold_headings",
        "increase_line_height",
        "monospace_code",
        "reduce_motion",
        "high_contrast_mode",
        "font_weight",
    )

    BOOL_FIELDS = (
        "bold_headings",
        "increase_line_height",
        "monospace_code",
        "reduce_motion",
        "high_contrast_mode",
    )

    def _payload(self, font):
        if font is None:
            font = FontSettings()
        return {name: getattr(font, name) for name in self.FIELDS}

    def get(self, request):
        return Response(self._payload(_get_font_settings(request.user)))

    def put(self, request):
        data = request.data
        errors = {}
        updates = {}

        if "font_family" in data:
            if data["font_family"] in FONT_FAMILIES:
                updates["font_family"] = data["font_family"]
            else:
                errors["font_family"] = "Неизвестный шрифт"

        for name, (lo, hi) in {
            "font_size": (10, 24),
            "interface_scale": (50, 200),
        }.items():
            if name in data:
                value = _to_number(data[name])
                if value is not None and lo <= value <= hi:
                    updates[name] = int(round(value))
                else:
                    errors[name] = f"Допустимо от {lo} до {hi}"

        if "line_height" in data:
            value = _to_number(data["line_height"])
            if value is not None and 0.8 <= value <= 2.5:
                updates["line_height"] = round(value, 2)
            else:
                errors["line_height"] = "Допустимо от 0.8 до 2.5"

        if "density" in data:
            if data["density"] in DENSITIES:
                updates["density"] = data["density"]
            else:
                errors["density"] = "Неизвестная плотность"

        if "font_weight" in data:
            if data["font_weight"] in FONT_WEIGHTS:
                updates["font_weight"] = data["font_weight"]
            else:
                errors["font_weight"] = "Ожидается normal или bold"

        for name in self.BOOL_FIELDS:
            if name in data:
                if _is_bool(data[name]):
                    updates[name] = data[name]
                else:
                    errors[name] = "Ожидается true или false"

        if errors:
            return Response({"errors": errors}, status=400)

        font = _get_font_settings(request.user)
        if font is None:
            font = FontSettings(user=request.user)
        for field, value in updates.items():
            setattr(font, field, value)
        font.save()
        return Response(self._payload(font))

    patch = put
    post = put
