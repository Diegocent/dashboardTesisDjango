# Usamos una imagen ligera con Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiamos los archivos necesarios
COPY requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código al contenedor
COPY . .

# Exponer puerto (Django por defecto usa 8000)
EXPOSE 8000

# Comando para iniciar el servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]