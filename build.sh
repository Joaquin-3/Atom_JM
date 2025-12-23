#!/usr/bin/env bash
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Preparar archivos estáticos
python manage.py collectstatic --noinput
