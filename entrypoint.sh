#!/bin/sh
set -e
echo "⏳ Жду Postgres..."
while ! nc -z -v db 5432; do
  sleep 1
done

echo "🚀 Делаю миграции..."
python manage.py migrate --noinput

echo "📦 Собираю статику..."
python manage.py collectstatic --noinput

echo "✅ Запускаю Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
