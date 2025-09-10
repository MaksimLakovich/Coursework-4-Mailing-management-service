# Базовый образ Python
FROM python:3.12-slim


# Классический паттерн установки netcat и системные зависимости:
# 1) apt-get update → обновляет список пакетов (как apt update в Ubuntu).
# 2) apt-get install -y ... → устанавливает системные пакеты (-y == отвечать "ДА" на всё):
# netcat-traditional - в образе python:3.12-slim нет утилиты nc (netcat), а без нее не сработает entrypoint.sh,
# поэтому устанавливаю netcat в образ
# build-essential - компилятор C (для установки некоторых пакетов).
# libpq-dev - заголовки и библиотеки PostgreSQL (нужны psycopg2)
# libjpeg-dev - для pillow (работа с изображениями)
# zlib1g-dev - для pillow (PNG/JPEG и т.п.)
# 3) rm -rf /var/lib/apt/lists/* → чистим кэш apt, иначе образ будет на сотни МБ тяжелее.
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /mailing_service_project

# Копируем pyproject.toml и poetry.lock (чтобы зависимости кэшировались)
COPY pyproject.toml poetry.lock* /mailing_service_project/

# Устанавливаем Poetry и зависимости проекта
# 1) pip install --upgrade pip → в slim-образах Python стоит старый pip, а Poetry под капотом использует pip.
#    Если pip старый → могут ломаться зависимости.
# 2) pip install poetry → ставим менеджер зависимостей Poetry.
# 3) poetry config virtualenvs.create false → отключаем виртуальные окружения (venv),
#    потому что в Docker у нас и так изоляция (каждый контейнер = отдельное окружение).
# 4) poetry install --no-root --only main → ставим только основные зависимости (без dev-зависимостей).
#    Пример: ставим Django, DRF, Celery, psycopg2, но НЕ ставим pytest, flake8, black и т.п.
#    Если убрать флаг "--only main" то будет ставиться все и контейнер будет чуть-чуть тяжелее.
RUN pip install --upgrade pip && pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root


# Копируем всё содержимое проекта в контейнер
COPY . /mailing_service_project

# Открываем порт для приложения
EXPOSE 8000

## Команда по умолчанию (запуск Django-сервера разработки)
## Эту строку в Dockerfile можно убрать , так как запуск сервера описан в docker-compose.yaml
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
