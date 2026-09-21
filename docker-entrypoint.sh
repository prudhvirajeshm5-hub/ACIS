#!/bin/sh
# Runs once per deploy, before gunicorn starts. Every command here is
# idempotent (see the docstrings in seed_roles.py / seed_masters.py), so
# it's safe to run on every boot rather than wiring a separate Render
# pre-deploy step (which is a paid-plan-only feature).
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding roles..."
python manage.py seed_roles

echo "Seeding master data..."
python manage.py seed_masters

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 3
