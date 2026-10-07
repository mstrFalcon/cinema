"""HTTP input, page contexts and user-facing responses."""
import logging
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render

from .clients.exceptions import KinopoiskAPIError
from .constants import LANGUAGES, PAGES_LIMIT_HTML_SELECTOR
from .models import Season
from .normalization import integer
from .services import films, persons

logger = logging.getLogger(__name__)


def handle_kinopoisk_errors(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except KinopoiskAPIError as exc:
            logger.warning('Ошибка загрузки данных в %s: %s', view.__name__, exc)
            context = {
                'api_error': True,
                'error_title': 'Не удалось открыть карточку',
                'error_message': (
                    'Сейчас не получается получить данные. '
                    'Повторите запрос немного позже.'
                ),
                'retry_url': request.get_full_path(),
            }

            if view.__name__ == 'get_films':
                template = 'apimanager/film.html'
                context.update(
                    error_title='Не удалось загрузить результаты',
                    all_films=[],
                    page_start=-1,
                    page_end=-1,
                    page_range=[],
                )
            elif view.__name__ == 'get_persons':
                template = 'apimanager/person.html'
                context.update(
                    error_title='Не удалось загрузить результаты',
                    all_actors=[],
                    page_start=-1,
                    page_end=-1,
                    page_range=[],
                )
            else:
                template = 'apimanager/service_unavailable.html'
                context['search_view'] = (
                    'get_persons' if view.__name__ == 'person_detail'
                    else 'get_films'
                )

            response = render(request, template, context, status=503)
            response['Cache-Control'] = 'no-store'
            return response

    return wrapper


def _pagination(data, requested_page, has_results):
    context = {'page_start': -1, 'page_end': -1, 'page_range': [],
               'page_current': requested_page}
    pages = integer(data.get('pages'), 1)
    if pages is None or not has_results:
        return context
    current = min(integer(data.get('page'), 1) or requested_page, pages)
    start = max(1, min(current - PAGES_LIMIT_HTML_SELECTOR // 2,
                       pages - PAGES_LIMIT_HTML_SELECTOR + 1))
    end = min(pages, start + PAGES_LIMIT_HTML_SELECTOR - 1)
    context.update(page_start=start, page_end=end, page_current=current,
                   page_range=range(start, end + 1))
    return context


def _film_context(film):
    return {
        'film': film,
        'actors': list(film.actors.all()),
        'directors': list(film.directors.all()),
        'lang_film_name_dict': [
            (language, getattr(film, f'name_lang{position}', '') or '')
            for position, language in enumerate(LANGUAGES, 1)
        ],
        'screenshots': list(film.screenshots.all()),
        'trailers': list(film.trailers.all()),
        'seasons': list(film.seasons.order_by('number')),
    }


def _person_context(person):
    return {'actor': person, 'movies_list': list(person.movies.all()),
            'awards_list': list(person.awards.all())}


def get_episodes(request, season_id):
    try:
        season = Season.objects.get(id=season_id)
        episodes = season.episodes.all().order_by('number')
        data = {
            'episodes': [
                {
                    'id': ep.id,
                    'name': ep.name,
                    'name_en': ep.name_en,
                    'description': ep.description,
                    'description_en': ep.description_en,
                    'runtime': ep.runtime,
                    'poster_url': ep.poster_url or '',
                    'number': ep.number,
                } for ep in episodes
            ]
        }
        return JsonResponse(data)
    except Season.DoesNotExist:
        return JsonResponse({'error': 'Сезон не найден'}, status=404)


@handle_kinopoisk_errors
def get_films(request, page=1):
    query = request.GET.get('name', '').strip()
    page = integer(request.GET.get('page', page), 1) or 1
    all_films, data = films.search_films(query, page)
    context = {'all_films': all_films, 'search_performed': bool(query)}
    context.update(_pagination(data, page, bool(all_films)))
    return render(request, 'apimanager/film.html', context)


@handle_kinopoisk_errors
def film_detail(request, id):
    film = films.load_film(id, refresh='refresh' in request.GET)
    return render(request, 'apimanager/film_detail.html', _film_context(film))


@handle_kinopoisk_errors
def get_persons(request, page=1):
    query = request.GET.get('name', '').strip()
    page = integer(request.GET.get('page', page), 1) or 1
    all_actors, data = persons.search_persons(query, page)
    context = {'all_actors': all_actors, 'search_performed': bool(query)}
    context.update(_pagination(data, page, bool(all_actors)))
    return render(request, 'apimanager/person.html', context)


@handle_kinopoisk_errors
def person_detail(request, id):
    person = persons.load_person(id, refresh='refresh' in request.GET)
    return render(request, 'apimanager/person_detail.html', _person_context(person))
