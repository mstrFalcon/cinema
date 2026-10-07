"""Fields used when updating existing catalog records."""
from ..models import Award, Film, Person, PersonCard


def get_award_defaults(award: Award):
    return {
        'award_name': award.award_name,
        'year': award.year,
        'nomination_name': award.nomination_name,
        'film_name': award.film_name,
        'film_kinopoisk_id': award.film_kinopoisk_id,
        'person_kinopoisk_id': award.person_kinopoisk_id,
    }


def get_person_defaults(person: Person):
    return {
        'name': person.name,
        'name_en': person.name_en,
        'country': person.country,
        'photo_url': person.photo_url,
        'birthday_date': person.birthday_date,
        'death_date': person.death_date,
        'gender': person.gender,
        'profession': person.profession,
        'biography': person.biography,
        'age': person.age,
        'growth': person.growth,
        'kinopoisk_id':person.kinopoisk_id,
    }


def get_film_defaults(film: Film):
    return {
        'name': film.name,
        'name_lang1': film.name_lang1,
        'name_lang2': film.name_lang2,
        'name_lang3': film.name_lang3,
        'name_lang4': film.name_lang4,
        'name_lang5': film.name_lang5,
        'countries':  film.countries,
        'genre': film.genre,
        'kinopoisk_id': film.kinopoisk_id,
        'imdb_id': film.imdb_id,
        'tmdb_id': film.tmdb_id,
        'kinopoisk_rating': film.kinopoisk_rating,
        'imdb_rating': film.imdb_rating,
        'tmdb_rating': film.tmdb_rating,
        'plot': film.plot,
        'short_description': film.short_description,
        'runtime': film.runtime,
        'date': film.date,
        'age_rating': film.age_rating,
        'poster_url': film.poster_url,
        'is_series': film.is_series,
    }


def get_movie_defaults(film: Film):
    return {
        'name': film.name,
        'name_lang1': film.name_lang1,
        'plot': film.plot,
        'short_description': film.short_description,
        'kinopoisk_rating': film.kinopoisk_rating,
        'kinopoisk_id': film.kinopoisk_id,
    }


def get_personcard_defaults(person: PersonCard):
    return {
        'name': person.name,
        'name_en': person.name_en,
        'photo_url': person.photo_url,
        'profession': person.profession,
        'role': person.role,
        'kinopoisk_id': person.kinopoisk_id,
    }
