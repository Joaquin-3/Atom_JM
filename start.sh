#!/usr/bin/env bash

# Migraciones
DJANGO_SETTINGS_MODULE=AtomProject.settings python manage.py migrate

# Crear superusuario si no existe
DJANGO_SETTINGS_MODULE=AtomProject.settings python -c "import django; django.setup(); from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','', 'admin')"

# Static files (por si cambian)
python manage.py collectstatic --noinput

# Iniciar servidor
gunicorn AtomProject.wsgi:application --bind 0.0.0.0:$PORT
