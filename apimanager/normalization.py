"""Validation and normalization of optional API data."""
from datetime import datetime, time

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .clients.exceptions import KinopoiskAPIError
from .constants import EMPTY_NAME_URL


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_list(value):
    return value if isinstance(value, list) else []


def records(value):
    return [item for item in as_list(value) if isinstance(item, dict)]


def text(value, default=''):
    return value.strip() if isinstance(value, str) and value.strip() else default


def integer(value, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if minimum <= number <= 2_147_483_647 else None


def parse_rating(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return None
    return number if 0 < number <= 10 else None


def api_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    try:
        result = parse_datetime(value)
        if result is None:
            day = parse_date(value)
            result = datetime.combine(day, time.min) if day else None
    except (ValueError, OverflowError):
        return None
    if result is not None:
        if settings.USE_TZ and timezone.is_naive(result):
            result = timezone.make_aware(result, timezone.get_default_timezone())
        elif not settings.USE_TZ and timezone.is_aware(result):
            result = timezone.make_naive(result, timezone.get_default_timezone())
    return result


def known(value, previous, field, default=None):
    if value is None:
        return getattr(previous, field) if previous is not None else default
    return value


def detail_data(data, identifier):
    if not isinstance(data, dict) or integer(data.get('id'), 1) != identifier:
        raise KinopoiskAPIError('Ответ API не содержит ID запрошенной карточки.')
    return data


def documents(data, required=False):
    docs = data.get('docs')
    if docs is None and not required:
        return []
    if not isinstance(docs, list):
        raise KinopoiskAPIError('Ответ API не содержит корректный список docs.')
    if required and any(not isinstance(item, dict) for item in docs):
        raise KinopoiskAPIError('В ответе API есть некорректная связанная запись.')
    return records(docs)


def parse_tmdb_id(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    try:
        tmdb_id = int(value)
    except (TypeError, ValueError):
        return None
    return tmdb_id if 0 < tmdb_id <= 2_147_483_647 else None


def photo_url_handler(photo_url):
    photo_url = text(photo_url)
    if not photo_url:
        return EMPTY_NAME_URL
    return photo_url[6:] if photo_url.startswith('https:') else photo_url
