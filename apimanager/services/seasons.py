"""Season and episode updates within the caller's film transaction."""
from ..clients.exceptions import KinopoiskAPIError
from ..models import Season
from ..normalization import as_dict, integer, known, photo_url_handler, text


def save_seasons(identifier, docs, series_length):
    seasons = []
    previous_seasons = {season.number: season for season in Season.objects.filter(kinopoisk_id=identifier)}
    for data in docs:
        number = integer(data.get('number'))
        if number is None:
            raise KinopoiskAPIError('В ответе API отсутствует номер сезона.')
        previous = previous_seasons.get(number)
        season, _ = Season.objects.update_or_create(
            kinopoisk_id=identifier, number=number,
            defaults={'name': text(known(data.get('name'), previous, 'name'), f'Сезон {number}')},
        )
        raw_episodes = data.get('episodes')
        if isinstance(raw_episodes, list):
            previous_episodes = {episode.number: episode for episode in season.episodes.all()}
            episodes = []
            for episode in raw_episodes:
                if not isinstance(episode, dict):
                    raise KinopoiskAPIError('Некорректная запись эпизода в ответе API.')
                number = integer(episode.get('number'))
                if number is None:
                    raise KinopoiskAPIError('В ответе API отсутствует номер эпизода.')
                previous = previous_episodes.get(number)
                still = as_dict(episode.get('still'))
                current, _ = season.episodes.update_or_create(
                    number=number,
                    defaults={
                        'kinopoisk_id': identifier,
                        'name': text(known(episode.get('name'), previous, 'name'), f'Эпизод {number}'),
                        'name_en': text(known(episode.get('enName'), previous, 'name_en'), f'Episode {number}'),
                        'description': text(known(episode.get('description'), previous, 'description')),
                        'description_en': text(known(episode.get('enDescription'), previous, 'description_en')),
                        'runtime': integer(known(episode.get('seriesLength'), previous, 'runtime')) or series_length,
                        'poster_url': photo_url_handler(known(still.get('previewUrl') or still.get('url'), previous, 'poster_url')),
                    },
                )
                episodes.append(current)
            season.episodes.set(episodes)
        seasons.append(season)
    return sorted(seasons, key=lambda season: season.number)
