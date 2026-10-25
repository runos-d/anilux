from datetime import date


def premiere_date(record):
    material = record.get('material_data') or {}
    for value in (material.get('aired_at'), record.get('aired_at')):
        if isinstance(value, str):
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                pass
    return None


def valid_year(value):
    if isinstance(value, bool):
        return None
    try:
        year = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return year if 1900 <= year <= 2100 else None


def release_year(record):
    material = record.get('material_data') or {}
    exact = premiere_date(record)
    if exact:
        return valid_year(exact.year)
    for value in (record.get('year'), material.get('anime_year'), material.get('year')):
        year = valid_year(value)
        if year is not None:
            return year
    return None
