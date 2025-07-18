#!/bin/bash
set -o errexit

# Activar el entorno virtual que Render crea automáticamente
source /opt/render/project/src/.venv/bin/activate

# Instalar dependencias
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Comandos Django
python manage.py makemigrations dashboard
python manage.py migrate --fake-initial
python manage.py collectstatic --noinput