"""Film search, optional enrichment and atomic catalog updates."""
from django.db import transaction

from ..clients import kinopoisk, tmdb
from ..constants import LANGUAGES
from ..models import Film, PersonCard, Screenshot, Trailer
from ..normalization import (
    api_date, as_dict, documents, integer, known, parse_tmdb_id,
    photo_url_handler, parse_rating, records, text,
)
from .persistence import get_film_defaults, get_personcard_defaults
from .seasons import save_seasons


def search_films(query, page=1):
    data = {}
    all_films = []
    if query:
        data = kinopoisk.search_films(query, page)
        for item in documents(data):
            identifier = integer(item.get('id'), 1)
            if identifier is None:
                continue
            external = as_dict(item.get('externalId'))
            rating = as_dict(item.get('rating'))
            all_films.append(Film(
                kinopoisk_id=identifier,
                name=text(item.get('name'), 'Нет названия'),
                name_lang1=text(item.get('alternativeName'), 'Нет названия на английском'),
                plot=text(item.get('description'), 'Описание не указано'),
                date=integer(item.get('year'), 1) or 'Дата выхода отсутствует',
                kinopoisk_rating=parse_rating(rating.get('kp')) or 'Нет данных',
                imdb_rating=parse_rating(rating.get('imdb')) or 'Нет данных',
                poster_url=photo_url_handler(as_dict(item.get('poster')).get('url')),
                imdb_id=text(external.get('imdb')) or None,
                tmdb_id=parse_tmdb_id(external.get('tmdb')),
                is_series=item.get('isSeries') is True,
            ))
    return all_films, data


def load_film(id, refresh=False):
    previous = Film.objects.filter(kinopoisk_id=id).first()
    if previous is not None and not refresh:
        return previous

    data = kinopoisk.get_film(id)
    external = as_dict(data.get('externalId'))
    ratings = as_dict(data.get('rating'))
    is_series = data.get('isSeries')
    if not isinstance(is_series, bool):
        is_series = previous.is_series if previous else False
    tmdb_id = parse_tmdb_id(external.get('tmdb'))
    if tmdb_id is None and previous and previous.is_series == is_series:
        tmdb_id = previous.tmdb_id

    names = {}
    for item in records(data.get('names')):
        language = text(item.get('language')).lower()
        name = text(item.get('name'))
        if language and name and (language not in names or item.get('type') is None):
            names[language] = name
    languages = [names.get(language.lower(), '') for language in LANGUAGES]
    languages[0] = languages[0] or text(data.get('alternativeName')) or names.get('us', '')
    if previous:
        for position in range(len(languages)):
            languages[position] = languages[position] or getattr(previous, f'name_lang{position + 1}') or ''

    countries = ', '.join(text(item.get('name')) for item in records(data.get('countries'))
                          if text(item.get('name')))
    genres = ', '.join(text(item.get('name')) for item in records(data.get('genres'))
                       if text(item.get('name')))
    if not isinstance(data.get('countries'), list):
        countries = previous.countries if previous else ''
    if not isinstance(data.get('genres'), list):
        genres = previous.genre if previous else ''
    date = api_date(as_dict(data.get('premiere')).get('world'))
    if date is None and previous:
        date = previous.date
    poster = as_dict(data.get('poster')).get('url')
    film = Film(
        kinopoisk_id=id,
        name=text(known(data.get('name'), previous, 'name'), 'Нет данных'),
        name_lang1=languages[0], name_lang2=languages[1], name_lang3=languages[2],
        name_lang4=languages[3], name_lang5=languages[4],
        countries=countries, genre=genres,
        imdb_id=text(known(external.get('imdb'), previous, 'imdb_id')) or None,
        tmdb_id=tmdb_id,
        kinopoisk_rating=parse_rating(known(ratings.get('kp'), previous, 'kinopoisk_rating')),
        imdb_rating=parse_rating(known(ratings.get('imdb'), previous, 'imdb_rating')),
        plot=text(known(data.get('description'), previous, 'plot'), 'Нет данных'),
        short_description=text(known(data.get('shortDescription'), previous, 'short_description'), 'Нет данных'),
        runtime=integer(known(data.get('movieLength'), previous, 'runtime')),
        date=date,
        age_rating=integer(known(data.get('ageRating'), previous, 'age_rating')),
        poster_url=photo_url_handler(known(poster, previous, 'poster_url')),
        is_series=is_series,
    )

    same_tmdb_object = previous is not None and previous.is_series == is_series and previous.tmdb_id in (None, tmdb_id)
    film.tmdb_rating = previous.tmdb_rating if same_tmdb_object else None
    screenshots = list(previous.screenshots.values_list('photo_url', flat=True)) if same_tmdb_object else []
    tmdb_data = tmdb.get_data(tmdb_id, is_series)
    if tmdb_data is not None:
        rating = tmdb_data.get('vote_average')
        votes = tmdb_data.get('vote_count')
        if type(votes) is int and votes == 0:
            film.tmdb_rating = None
        elif type(votes) is int and votes > 0 and type(rating) in (int, float) and 0 <= rating <= 10:
            film.tmdb_rating = float(rating)
        raw_images = as_dict(tmdb_data.get('images')).get('backdrops')
        if isinstance(raw_images, list):
            screenshots = [f'https://image.tmdb.org/t/p/original{item["file_path"]}'
                           for item in records(raw_images)
                           if isinstance(item.get('file_path'), str) and item['file_path'].startswith('/')][:12]

    raw_persons = data.get('persons')
    actors = []
    directors = []
    for item in records(raw_persons):
        identifier = integer(item.get('id'), 1)
        name = text(item.get('name')) or text(item.get('enName'))
        profession = item.get('enProfession')
        if identifier is None or not name or profession not in ('actor', 'director'):
            continue
        person = PersonCard(
            kinopoisk_id=identifier, name=name, name_en=text(item.get('enName')),
            photo_url=photo_url_handler(item.get('photo')),
            profession=text(item.get('profession'), 'Нет данных'),
            role=text(item.get('description'), 'Нет данных'),
        )
        if person.profession.endswith('ы'):
            person.profession = person.profession[:-1]
        (actors if profession == 'actor' else directors).append(person)

    raw_trailers = as_dict(data.get('videos')).get('trailers')
    trailers = [text(item.get('url')) for item in records(raw_trailers) if text(item.get('url'))]
    season_docs = kinopoisk.get_seasons(id) if is_series else []

    # Сеть завершена; карточка и все её связи сохраняются вместе.
    with transaction.atomic():
        seasons = save_seasons(id, season_docs, integer(data.get('seriesLength')) or 0)
        actors_db = [PersonCard.objects.update_or_create(
            kinopoisk_id=person.kinopoisk_id, defaults=get_personcard_defaults(person))[0] for person in actors]
        directors_db = [PersonCard.objects.update_or_create(
            kinopoisk_id=person.kinopoisk_id, defaults=get_personcard_defaults(person))[0] for person in directors]
        trailers_db = [Trailer.objects.update_or_create(kinopoisk_id=id, video_url=url)[0] for url in trailers]
        screenshots_db = [Screenshot.objects.update_or_create(kinopoisk_id=id, photo_url=url)[0] for url in screenshots]
        film, _ = Film.objects.update_or_create(kinopoisk_id=id, defaults=get_film_defaults(film))
        if isinstance(raw_persons, list):
            film.actors.set(actors_db)
            film.directors.set(directors_db)
        if isinstance(raw_trailers, list):
            film.trailers.set(trailers_db)
        film.screenshots.set(screenshots_db)
        film.seasons.set(seasons)

    return film
