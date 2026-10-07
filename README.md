# Cinema

Учебный Django-проект для поиска фильмов и людей, объединения данных из внешних источников и просмотра карточек.

Сейчас доступны поиск, карточки фильмов и людей, рейтинги, актёры и режиссёры, работы и награды, трейлеры, изображения, сезоны и эпизоды. Основной источник — ПоискКино; TMDB дополняет карточки рейтингом и изображениями по числовому `externalId.tmdb`. Прогноз рейтинга с помощью модели машинного обучения — следующий этап разработки.

## Технологии

- Python 3.12 / 3.13.
- Django 5.1.7, SQLite.
- Requests, python-dotenv.
- Django templates, JavaScript, jQuery, Slick и Fancybox.

Версии Python-зависимостей закреплены в `requirements.txt`.

## Структура

Корень репозитория — папка рядом с `manage.py`.

| Путь | Назначение |
| --- | --- |
| `cinema/` | Настройки Django, общие URL, WSGI/ASGI и тестовые настройки |
| `apimanager/clients/` | Запросы к внешним API и обработка ошибок источников |
| `apimanager/services/` | Загрузка и сохранение фильмов, людей, сезонов и эпизодов |
| `apimanager/normalization.py` | Проверка и обработка необязательных полей API |
| `apimanager/constants.py` | Общие значения для поиска и отображения |
| `apimanager/models.py` | Модели каталога |
| `apimanager/views.py` | HTTP-запросы, контекст страниц, HTML и JSON |
| `apimanager/migrations/` | История изменений схемы базы |
| `apimanager/templates/apimanager/` | Шаблоны страниц |
| `apimanager/static/` | Исходные CSS, JavaScript и библиотеки интерфейса |
| `apimanager/test_*.py` | Автоматические тесты |

## Первый запуск в Windows PowerShell

В новой копии репозитория, из папки с `manage.py`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Если установлена только версия Python 3.12, используйте `py -3.12` при создании окружения.

Сгенерируйте ключ Django и впишите полученное значение в `DJANGO_SECRET_KEY` файла `.env`:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Заполните в `.env` ключ ПоискКино и токен TMDB. Затем:

```powershell
python manage.py migrate
python manage.py check
python manage.py runserver
```

Сайт: http://127.0.0.1:8000/.

Для первого запуска в Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

После заполнения `.env` используются те же команды `migrate`, `check` и `runserver`.

## Переменные окружения

| Переменная | Назначение |
| --- | --- |
| `DJANGO_SECRET_KEY` | Ключ Django; необходим для загрузки рабочих настроек |
| `POISKKINO_API_KEY` | Ключ основного источника ПоискКино |
| `TMDB_API_TOKEN` | Bearer-токен дополнительного источника TMDB |
| `IMDB_API_KEY` | Ключ существующего вспомогательного клиента IMDb; текущий рейтинг IMDb приходит из ПоискКино |
| `POISKKINO_TRUST_ENV` | Использовать ли настройки прокси окружения для ПоискКино: `true` или `false` |
| `TMDB_TRUST_ENV` | Использовать ли настройки прокси окружения для TMDB: `true` или `false` |

Настройки прокси задаются отдельно для каждого источника. Доступность API также зависит от маршрутизации VPN на компьютере.

`.env` загружается относительно папки с `manage.py`. Переменные окружения имеют приоритет над `.env`; после изменения значений перезапустите сервер.

В Git хранится только `.env.example` с пустыми значениями. Рабочая база создаётся миграциями и тоже не включается в репозиторий. Миграции и исходные файлы `apimanager/static/` включаются в Git.

