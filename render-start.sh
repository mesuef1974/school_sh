#!/bin/bash

# Exit on error
set -o errexit

echo "==> Running Migrations..."
python manage.py migrate --noinput

echo "==> Creating Superuser..."
python manage.py initadmin

echo "==> Collecting Static Files..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn..."
export DJANGO_SETTINGS_MODULE=config.settings.prod
exec gunicorn config.wsgi:application --bind 0.0.0.0:10000