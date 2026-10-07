"""PoiskKino requests, endpoints and related-record pagination."""
import logging

import requests
from django.conf import settings
from requests.exceptions import RequestException

from .exceptions import KinopoiskAPIError
from ..constants import PAGES_LIMIT_REQUEST
from ..normalization import detail_data, documents, integer

logger = logging.getLogger(__name__)


def request(url, params=None):
    if not settings.POISKKINO_API_KEY:
        raise KinopoiskAPIError("Не настроен ключ API ПоискКино.")

    try:
        with requests.Session() as session:
            session.trust_env = settings.POISKKINO_TRUST_ENV

            response = session.get(
                url,
                headers={
                    "accept": "application/json",
                    "X-API-KEY": settings.POISKKINO_API_KEY,
                },
                params=params,
                timeout=(5, 15),
            )
            response.raise_for_status()
            data = response.json()

    except requests.exceptions.Timeout as exc:
        logger.warning("ПоискКино: превышено время ожидания")
        raise KinopoiskAPIError(
            "ПоискКино не ответил вовремя. Попробуйте позже."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        logger.warning("ПоискКино: HTTP %s", status)
        raise KinopoiskAPIError(
            f"ПоискКино вернул ошибку HTTP {status}."
        ) from exc

    except RequestException as exc:
        logger.warning("ПоискКино: ошибка соединения")
        raise KinopoiskAPIError(
            "Не удалось соединиться с ПоискКино."
        ) from exc

    except ValueError as exc:
        logger.warning("ПоискКино: некорректный JSON")
        raise KinopoiskAPIError(
            "ПоискКино вернул некорректный ответ."
        ) from exc

    if not isinstance(data, dict):
        raise KinopoiskAPIError(
            "ПоискКино вернул ответ неожиданного формата."
        )

    return data


def fetch_documents(url, params):
    result = []
    page = 1
    while True:
        data = request(url, {**params, 'page': page})
        docs = documents(data, required=True)
        pages = integer(data.get('pages'))
        if pages is None:
            if docs or data.get('pages') is not None:
                raise KinopoiskAPIError('Ответ API не содержит корректное число страниц.')
            pages = 1
        if pages == 0 and docs:
            raise KinopoiskAPIError('Число страниц API не соответствует связанным записям.')
        result.extend(docs)
        if page >= pages:
            return result
        page += 1


def search_films(query, page=1):
    return request('https://api.poiskkino.dev/v1.5/movie/search',
                   {'page': page, 'limit': PAGES_LIMIT_REQUEST, 'query': query})


def search_persons(query, page=1):
    return request('https://api.poiskkino.dev/v1.4/person/search',
                   {'page': page, 'limit': PAGES_LIMIT_REQUEST, 'query': query})


def get_film(identifier):
    return detail_data(request(f'https://api.poiskkino.dev/v1.4/movie/{identifier}'), identifier)


def get_person(identifier):
    return detail_data(request(f'https://api.poiskkino.dev/v1.4/person/{identifier}'), identifier)


def get_seasons(identifier):
    return fetch_documents('https://api.poiskkino.dev/v1.4/season',
                           {'movieId': identifier, 'limit': 250})


def get_awards(identifier):
    return fetch_documents('https://api.poiskkino.dev/v1.4/person/awards',
                           {'personId': identifier, 'limit': 100, 'winning': 'true'})
