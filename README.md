# 📊 Dashboard de Asistencia Humanitaria - Django

Dashboard interactivo para visualizar datos de asistencia humanitaria con gráficos generados usando matplotlib y pandas.

## 🚀 Instalación y Configuración

### 1. Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Acceso a base de datos PostgreSQL (Neon)

### 2. Clonar o descargar el proyecto

```bash
# Si tienes el proyecto en un repositorio
git clone <url-del-repositorio>
cd django-dashboard

# O simplemente descargar y extraer los archivos
```

### 3. Crear entorno virtual (Recomendado)

```bash
# Crear entorno virtual
python -m venv dashboard_env

# Si necesitas especificar la version de python utiliza de esta forma
# Ya que este proyecto depende de la version 3.11
py -3.11 -m venv dashboard_env

# Activar entorno virtual
# En Windows:
dashboard_env\\Scripts\\activate

# En macOS/Linux:
source dashboard_env/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar base de datos

El archivo `settings.py` ya está configurado para tu base de datos Neon. Si necesitas cambiar la configuración:

```python
# dashboard_project/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tu_nombre_bd',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_password',
        'HOST': 'tu_host',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

### 6. Ejecutar migraciones

```bash
# Crear migraciones para la app dashboard
python manage.py makemigrations dashboard

# Aplicar migraciones
python manage.py migrate
```

### 7. Crear superusuario (Opcional)

```bash
python manage.py createsuperuser
```

### 8. Ejecutar el servidor

```bash
python manage.py runserver
```

Visita: `http://127.0.0.1:8000/`

## 📁 Estructura del Proyecto

```
django-dashboard/
├── dashboard_project/          # Configuración principal de Django
│   ├── settings.py            # Configuración de la aplicación
│   ├── urls.py               # URLs principales
│   └── wsgi.py               # Configuración WSGI
├── dashboard/                 # Aplicación principal
│   ├── models.py             # Modelo de datos
│   ├── views.py              # Lógica de vistas y gráficos
│   ├── urls.py               # URLs de la aplicación
│   └── admin.py              # Configuración del admin
├── templates/                 # Plantillas HTML
│   ├── base.html             # Plantilla base
│   └── dashboard/
│       └── dashboard.html    # Plantilla del dashboard
├── scripts/                   # Scripts auxiliares
│   └── setup_database.py     # Script para datos de ejemplo
├── requirements.txt           # Dependencias del proyecto
└── manage.py                 # Comando principal de Django
```

## 📈 Cómo Agregar Tus Gráficos Personalizados

### Paso 1: Crear función para tu gráfico

Abre `dashboard/views.py` y agrega una nueva función:

```python
def tu_nuevo_grafico():
    """Descripción de tu gráfico"""

    # 1. Obtener datos de la base de datos
    queryset = AsistenciaHumanitaria.objects.all().values(
        'fecha__year', 'kit_b', 'kit_a', 'chapa_fibrocemento'
        # Agrega los campos que necesites
    )

    # 2. Convertir a DataFrame
    df = pd.DataFrame(list(queryset))

    if df.empty:
        return None

    # 3. TU CÓDIGO MATPLOTLIB AQUÍ
    # Ejemplo basado en tu código original:
    fig, ax = plt.subplots(figsize=(12, 6))

    # Tu lógica de gráfico
    df.groupby('fecha__year')['kit_b'].sum().plot(
        kind='bar',
        ax=ax,
        color='viridis'
    )

    # Personalización
    plt.title('Tu Título Aquí', pad=20, fontsize=14)
    plt.ylabel('Tu Label Y', fontsize=12)
    plt.xlabel('Tu Label X', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # 4. CONVERSIÓN A BASE64 (NO CAMBIAR)
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')
```

### Paso 2: Agregar al contexto

En la función `dashboard_view`, agrega tu gráfico:

```python
def dashboard_view(request):
    # ... código existente ...

    # Agregar tu nuevo gráfico
    tu_grafico = tu_nuevo_grafico()

    context = {
        # ... contexto existente ...
        'tu_grafico': tu_grafico,  # Agregar esta línea
    }

    return render(request, 'dashboard/dashboard.html', context)
```

### Paso 3: Mostrar en el template

En `templates/dashboard/dashboard.html`, agrega:

```html
<!-- Tu Nuevo Gráfico -->
{% if tu_grafico %}
<div class="col-lg-12 mb-4">
  <div class="card">
    <div class="card-header">
      <h5 class="card-title mb-0">
        <i class="fas fa-chart-bar me-2"></i>
        Título de Tu Gráfico
      </h5>
    </div>
    <div class="card-body">
      <div class="text-center">
        <img
          src="data:image/png;base64,{{ tu_grafico }}"
          class="img-fluid"
          alt="Tu Gráfico"
        />
      </div>
    </div>
  </div>
</div>
{% endif %}
```

## 🔧 Ejemplo Práctico: Adaptando tu código

Si tienes este código:

```python
# Tu código original
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))
df.groupby('AÑO')[ayudas].sum().plot(
    kind='bar',
    stacked=True,
    ax=ax,
    colormap='viridis')

plt.title('Distribución de Ayudas por Año', pad=20, fontsize=14)
plt.ylabel('Cantidad distribuida', fontsize=12)
plt.xlabel('Año', fontsize=12)
plt.legend(title='Tipo de Ayuda', bbox_to_anchor=(1.05, 1), frameon=True)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
```

**Adaptación para Django:**

```python
def mi_grafico_personalizado():
    # 1. Obtener datos de Django ORM
    queryset = AsistenciaHumanitaria.objects.all().values(
        'fecha__year', 'kit_b', 'kit_a', 'chapa_fibrocemento',
        'chapa_zinc', 'colchones', 'frazadas', 'terciadas',
        'puntales', 'carpas_plasticas'
    )

    df = pd.DataFrame(list(queryset))
    if df.empty:
        return None

    # 2. Preparar datos (igual que tu código)
    df.rename(columns={'fecha__year': 'AÑO'}, inplace=True)
    ayudas = ['kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc',
              'colchones', 'frazadas', 'terciadas', 'puntales', 'carpas_plasticas']

    # 3. TU CÓDIGO ORIGINAL (sin cambios)
    fig, ax = plt.subplots(figsize=(12, 6))
    df.groupby('AÑO')[ayudas].sum().plot(
        kind='bar',
        stacked=True,
        ax=ax,
        colormap='viridis')

    plt.title('Distribución de Ayudas por Año', pad=20, fontsize=14)
    plt.ylabel('Cantidad distribuida', fontsize=12)
    plt.xlabel('Año', fontsize=12)
    plt.legend(title='Tipo de Ayuda', bbox_to_anchor=(1.05, 1), frameon=True)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # 4. Conversión para web (reemplaza plt.show())
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')
```

## 🎨 Personalización del Dashboard

### Cambiar colores y estilos

Edita `templates/base.html` en la sección `<style>`:

```css
.sidebar {
  background: linear-gradient(135deg, #tu-color1 0%, #tu-color2 100%);
}

.stat-card {
  background: linear-gradient(135deg, #tu-color3 0%, #tu-color4 100%);
}
```

### Agregar nuevas estadísticas

En `dashboard_view` agrega:

```python
# Nueva estadística
total_kits = AsistenciaHumanitaria.objects.aggregate(
    total=Sum('kit_a') + Sum('kit_b')
)['total'] or 0

context = {
    # ... existente ...
    'total_kits': total_kits,
}
```

## 🔍 Comandos Útiles

```bash
# Ver logs del servidor
python manage.py runserver --verbosity=2

# Crear nueva migración después de cambios en models.py
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Abrir shell de Django para pruebas
python manage.py shell

# Recopilar archivos estáticos (para producción)
python manage.py collectstatic
```

## 🐛 Solución de Problemas

### Error de conexión a base de datos

- Verifica que las credenciales en `settings.py` sean correctas
- Asegúrate de que tu IP esté en la whitelist de Neon

### Error con matplotlib

```bash
# En sistemas Linux, puede necesitar:
sudo apt-get install python3-tk

# En macOS:
brew install python-tk
```

### Error "No module named 'dashboard'"

```bash
# Asegúrate de estar en el directorio correcto
cd django-dashboard
python manage.py runserver
```

### Gráficos no se muestran

- Verifica que la función retorne datos (no `None`)
- Revisa la consola del navegador para errores
- Asegúrate de que `plt.close()` esté al final de cada función de gráfico

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en la consola
2. Verifica que todos los paquetes estén instalados
3. Asegúrate de que la base de datos esté accesible
4. Comprueba que el modelo coincida con tu tabla

## 🚀 Próximos Pasos

- Agregar filtros por fecha y departamento
- Implementar exportación a Excel/PDF
- Crear API REST para los datos
- Agregar autenticación de usuarios
- Implementar cache para mejorar rendimiento

---

**¡Tu dashboard está listo para usar! 🎉**

```

Este README incluye todo lo que necesitas desde la instalación hasta cómo agregar tus gráficos personalizados. La sección más importante para ti será "Cómo Agregar Tus Gráficos Personalizados" donde explico exactamente cómo adaptar tu código de matplotlib existente al formato Django.
```
