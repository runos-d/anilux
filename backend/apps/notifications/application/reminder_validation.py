from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from rest_framework.exceptions import ValidationError


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValidationError({'timezone_name': 'Укажите корректный часовой пояс IANA'})
    return value
