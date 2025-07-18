#!/bin/bash

set -o errexit

# Fuerza la versión de Python especificada en runtime.txt
PYTHON_VERSION=$(cat runtime.txt | cut -d '-' -f 2)
echo "Usando Python $PYTHON_VERSION"

# Instalar dependencias con la versión correcta
python$PYTHON_VERSION -m pip install --upgrade pip setuptools wheel
python$PYTHON_VERSION -m pip install -r requirements.txt

# Comandos Django
python$PYTHON_VERSION manage.py makemigrations dashboard
python$PYTHON_VERSION manage.py migrate --fake-initial
python$PYTHON_VERSION manage.py collectstatic --noinput

# Nota: Render ignora el runserver, usa el comando de inicio de Render