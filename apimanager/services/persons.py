"""Person search and atomic biography, work and award updates."""
import re

from django.db import transaction

from ..clients import kinopoisk
from ..models import Award, Movie, Person
from ..normalization import api_date, as_dict, documents, integer, known, photo_url_handler, parse_rating, records, text
from .persistence import get_award_defaults, get_movie_defaults, get_person_defaults


def search_persons(query, page=1):
    data = {}
    all_actors = []
    if query:
        data = kinopoisk.search_persons(query, page)
        for item in documents(data):
            identifier = integer(item.get('id'), 1)
            if identifier is None:
                continue
            all_actors.append(Person(
                kinopoisk_id=identifier,
                name=text(item.get('name')) or text(item.get('enName'), 'Нет имени'),
                name_en=text(item.get('enName'), 'Нет имени на английском языке'),
                photo_url=photo_url_handler(item.get('photo')),
                gender=text(item.get('sex'), 'Нет данных'),
                birthday_date=api_date(item.get('birthday')),
                death_date=api_date(item.get('death')),
                age=integer(item.get('age')),
                growth=integer(item.get('growth')),
            ))
    return all_actors, data


def load_person(id, refresh=False):
    previous = Person.objects.filter(kinopoisk_id=id).first()
    if previous is not None and not refresh:
        return previous
    data = kinopoisk.get_person(id)

    raw_movies = data.get('movies')
    movies = records(raw_movies)
    professions = sorted({text(movie.get('enProfession')) for movie in movies
                          if text(movie.get('enProfession'))})
    profession = ', '.join(professions) or 'Нет данных'
    if not isinstance(raw_movies, list) and previous:
        profession = previous.profession or 'Нет данных'
    raw_facts = data.get('facts')
    biography = ' '.join(text(item.get('value')) for item in records(raw_facts)
                         if text(item.get('value'))) or 'Нет данных'
    biography = re.sub('<.*?>', '', biography)
    if not isinstance(raw_facts, list) and previous:
        biography = previous.biography or 'Нет данных'

    movie_objects = []
    for movie in movies:
        identifier = integer(movie.get('id'), 1)
        if identifier is None:
            continue
        movie_objects.append(Movie(
            kinopoisk_id=identifier,
            name=text(movie.get('name'), 'Нет названия'),
            name_lang1=text(movie.get('alternativeName'), 'Нет названия на английском'),
            plot=text(movie.get('description'), 'Роль не указана'),
            short_description=text(movie.get('enProfession'), 'Профессия не указана'),
            kinopoisk_rating=parse_rating(movie.get('rating')),
        ))

    award_objects = []
    for item in kinopoisk.get_awards(id):
        nomination = as_dict(item.get('nomination'))
        award = as_dict(nomination.get('award'))
        movie = as_dict(item.get('movie'))
        award_objects.append(Award(
            award_name=text(award.get('title'), 'Нет данных'),
            year=integer(award.get('year'), 1),
            nomination_name=text(nomination.get('title'), 'Нет данных'),
            film_name=text(movie.get('name'), 'Нет данных'),
            film_kinopoisk_id=integer(movie.get('id'), 1),
            person_kinopoisk_id=id,
        ))

    places = [text(item.get('value')) for item in records(data.get('birthPlace'))
              if text(item.get('value'))]
    country = places[-1] if places else 'Нет данных'
    if not isinstance(data.get('birthPlace'), list) and previous:
        country = previous.country or 'Нет данных'
    birthday = api_date(data.get('birthday'))
    death = api_date(data.get('death'))
    person = Person(
        kinopoisk_id=id,
        name=text(data.get('name')) or text(data.get('enName')) or text(known(None, previous, 'name'), 'Нет данных'),
        name_en=text(known(data.get('enName'), previous, 'name_en'), 'Нет имени на английском языке'),
        country=country,
        photo_url=photo_url_handler(known(data.get('photo'), previous, 'photo_url')),
        birthday_date=birthday or (previous.birthday_date if previous else None),
        death_date=death or (previous.death_date if previous else None),
        gender=text(known(data.get('sex'), previous, 'gender'), 'Нет данных'),
        profession=profession, biography=biography,
        age=integer(known(data.get('age'), previous, 'age')),
        growth=integer(known(data.get('growth'), previous, 'growth')),
    )
    with transaction.atomic():
        movies_db = [Movie.objects.update_or_create(
            kinopoisk_id=movie.kinopoisk_id, defaults=get_movie_defaults(movie))[0] for movie in movie_objects]
        awards_db = [Award.objects.update_or_create(
            person_kinopoisk_id=id, award_name=award.award_name, year=award.year,
            nomination_name=award.nomination_name, defaults=get_award_defaults(award))[0] for award in award_objects]
        person, _ = Person.objects.update_or_create(kinopoisk_id=id, defaults=get_person_defaults(person))
        person.awards.set(awards_db)
        if isinstance(raw_movies, list):
            person.movies.set(movies_db)
    return person
