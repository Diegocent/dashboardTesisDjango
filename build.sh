#!/bin/bash
set -o errexit

# Forzar Python 3.11 explícitamente
PYTHON_VERSION="3.11"

# Instalar dependencias básicas primero
python$PYTHON_VERSION -m pip install --upgrade "pip<23.3" "setuptools<66" "wheel"
python$PYTHON_VERSION -m pip install -r requirements.txt

# Comandos Django
python$PYTHON_VERSION manage.py makemigrations dashboard
python$PYTHON_VERSION manage.py migrate --fake-initial
python$PYTHON_VERSION manage.py collectstatic --noinput
