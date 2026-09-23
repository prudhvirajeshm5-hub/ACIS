#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding roles..."
python manage.py seed_roles

echo "Seeding master data..."
python manage.py seed_masters

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Ensuring superuser exists..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ['DJANGO_SUPERUSER_USERNAME']
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ['DJANGO_SUPERUSER_PASSWORD']
user, created = User.objects.get_or_create(username=username, defaults={'email': email})
user.email = email or user.email
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()
print('Superuser created' if created else 'Superuser updated')
"
fi

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 3
