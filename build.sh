#!/bin/bash
set -o errexit

# Forzar Python 3.11 aunque Render quiera usar otra versión
PYTHON_VERSION="3.11"
echo "===== ¡OBLIGANDO a usar Python $PYTHON_VERSION! ====="

# Instalar dependencias
python$PYTHON_VERSION -m pip install --upgrade pip setuptools wheel
python$PYTHON_VERSION -m pip install -r requirements.txt

# Comandos Django
python$PYTHON_VERSION manage.py makemigrations dashboard
python$PYTHON_VERSION manage.py migrate --fake-initial
python$PYTHON_VERSION manage.py collectstatic --noinput