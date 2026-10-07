"""Optional TMDB enrichment using its numeric movie or TV identifier."""
import logging

import requests
from django.conf import settings
from requests.exceptions import RequestException

from ..normalization import parse_tmdb_id

logger = logging.getLogger(__name__)


def request(url, params=None):
    if not settings.TMDB_API_TOKEN:
        logger.warning('TMDB: не настроен TMDB_API_TOKEN')
        return {}

    try:
        with requests.Session() as session:
            session.trust_env = getattr(settings, 'TMDB_TRUST_ENV', True)
            response = session.get(
                url,
                headers={
                    'accept': 'application/json',
                    'Authorization': f'Bearer {settings.TMDB_API_TOKEN}',
                },
                params=params,
                timeout=(5, 10),
            )
            response.raise_for_status()
            data = response.json()
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 'unknown'
        logger.warning('TMDB: HTTP %s', status)
        return {}
    except requests.exceptions.Timeout:
        logger.warning('TMDB: превышено время ожидания ответа')
        return {}
    except (RequestException, ValueError) as exc:
        logger.warning('TMDB: ошибка запроса (%s)', type(exc).__name__)
        return {}

    if not isinstance(data, dict) or data.get('success') is False:
        logger.warning('TMDB: неожиданный формат ответа или ошибка API')
        return {}
    return data


def get_data(tmdb_id, is_series):
    tmdb_id = parse_tmdb_id(tmdb_id)
    if tmdb_id is None:
        return None
    media_type = 'tv' if is_series else 'movie'
    return request(
        f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}',
        {'append_to_response': 'images'},
    ) or None
