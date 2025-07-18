#!/bin/bash

set -o errexit

# Instalar dependencias
pip install -r requirements.txt

python manage.py makemigrations dashboard

# Ejecutar migraciones
python manage.py migrate --fake-initial

# Recopilar archivos estáticos
python manage.py collectstatic --noinput
# Iniciar el servidor de desarrollo
python manage.py runserver