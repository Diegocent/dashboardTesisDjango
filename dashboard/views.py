import io
import base64
import matplotlib
matplotlib.use('Agg')  # Para usar matplotlib sin GUI
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import Extract
from .models import AsistenciaHumanitaria
from .utils.data_cleaner import data_cleaner  # Importar el limpiador
import numpy as np

# Configurar matplotlib para español
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 10

def _get_cleaned_dataframe():
    """
    Obtiene todos los datos de AsistenciaHumanitaria, los convierte a un DataFrame
    y aplica la limpieza completa usando DataCleaner.
    """
    queryset = AsistenciaHumanitaria.objects.all().values(
        'id', 'fecha', 'localidad', 'distrito', 'departamento', 'evento',
        'kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc', 'colchones',
        'frazadas', 'terciadas', 'puntales', 'carpas_plasticas'
    )
    
    if not queryset.exists():
        return pd.DataFrame() # Retorna un DataFrame vacío si no hay datos
    
    # Convertir queryset a lista de diccionarios y luego a DataFrame
    data_list = list(queryset)
    
    # Aplicar limpieza a cada registro
    cleaned_data_list = [data_cleaner.limpiar_registro_completo(record) for record in data_list]
    
    df = pd.DataFrame(cleaned_data_list)
    
    # Asegurar que la columna 'fecha' sea de tipo datetime
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    
    return df

def dashboard_view(request):
    """Vista principal del dashboard"""
    df_cleaned = _get_cleaned_dataframe()
    
    # Estadísticas generales
    total_registros = df_cleaned.shape[0]
    total_departamentos = df_cleaned['departamento'].nunique() if not df_cleaned.empty else 0
    total_localidades = df_cleaned['localidad'].nunique() if not df_cleaned.empty else 0
    
    # Obtener datos para gráficos
    grafico_ayudas_por_ano = generar_grafico_ayudas_por_ano(df_cleaned)
    grafico_departamentos = generar_grafico_por_departamento(df_cleaned)
    grafico_eventos = generar_grafico_por_evento(df_cleaned)
    grafico_tendencia_mensual = generar_grafico_tendencia_mensual(df_cleaned)
    
    # Datos para tablas (usamos el ORM para paginación, pero limpiamos al vuelo)
    ultimos_registros_raw = AsistenciaHumanitaria.objects.order_by('-fecha')[:10]
    
    ultimos_registros_cleaned = []
    for r in ultimos_registros_raw:
        # Create a dictionary from the model instance for cleaning
        record_dict = {field.name: getattr(r, field.name) for field in r._meta.fields}
        cleaned_record = data_cleaner.limpiar_registro_completo(record_dict)
        
        # Calculate total_ayudas from cleaned numeric fields
        cleaned_record['total_ayudas'] = sum(cleaned_record.get(field, 0) for field in data_cleaner.aid_fields)
        ultimos_registros_cleaned.append(cleaned_record)

    context = {
        'total_registros': total_registros,
        'total_departamentos': total_departamentos,
        'total_localidades': total_localidades,
        'grafico_ayudas_por_ano': grafico_ayudas_por_ano,
        'grafico_departamentos': grafico_departamentos,
        'grafico_eventos': grafico_eventos,
        'grafico_tendencia_mensual': grafico_tendencia_mensual,
        'ultimos_registros': ultimos_registros_cleaned, # Usamos los registros limpios
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def generar_grafico_ayudas_por_ano(df_cleaned):
    """Genera gráfico de distribución de ayudas por año - USANDO DATAFRAME LIMPIO"""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para mostrar ayudas por año")
    
    df = df_cleaned.copy() # Trabajar con una copia
    
    # Extraer año de la fecha limpia
    df['AÑO'] = df['fecha'].dt.year
    
    # Columnas de ayudas (ya limpias y numéricas por _get_cleaned_dataframe)
    ayudas = data_cleaner.aid_fields
    
    # Agrupar por año y sumar ayudas
    df_grouped = df.groupby('AÑO')[ayudas].sum()
    
    # Configuración del gráfico
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Crear gráfico de barras apiladas
    df_grouped.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        colormap='viridis'
    )
    
    # Personalización
    plt.title('Distribución de Ayudas por Año', pad=20, fontsize=14)
    plt.ylabel('Cantidad distribuida', fontsize=12)
    plt.xlabel('Año', fontsize=12)
    plt.legend(
        title='Tipo de Ayuda',
        bbox_to_anchor=(1.05, 1),
        frameon=True
    )
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Convertir a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    
    return graphic

def generar_grafico_por_departamento(df_cleaned):
    """Genera gráfico de ayudas por departamento - USANDO DATAFRAME LIMPIO"""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles por departamento")
    
    df = df_cleaned.copy() # Trabajar con una copia
    
    # Columnas de ayudas
    ayudas = data_cleaner.aid_fields
    
    # Agrupar por departamento (ya limpio) y sumar ayudas
    df_grouped = df.groupby('departamento')[ayudas].sum().reset_index()
    
    # Calcular totales para cada tipo de ayuda
    df_grouped['total_kit_b'] = df_grouped['kit_b']
    df_grouped['total_kit_a'] = df_grouped['kit_a']
    df_grouped['total_chapas'] = df_grouped['chapa_fibrocemento'] + df_grouped['chapa_zinc']
    df_grouped['total_otros'] = df_grouped['colchones'] + df_grouped['frazadas'] + df_grouped['terciadas'] + df_grouped['puntales'] + df_grouped['carpas_plasticas']
    
    # Ordenar por total de kit_b (o cualquier otra métrica relevante)
    df_grouped = df_grouped.sort_values('total_kit_b', ascending=False)

    # Crear gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(df_grouped))
    width = 0.2
    
    ax.bar([i - width*1.5 for i in x], df_grouped['total_kit_b'], width, label='Kit B', alpha=0.8)
    ax.bar([i - width*0.5 for i in x], df_grouped['total_kit_a'], width, label='Kit A', alpha=0.8)
    ax.bar([i + width*0.5 for i in x], df_grouped['total_chapas'], width, label='Chapas', alpha=0.8)
    ax.bar([i + width*1.5 for i in x], df_grouped['total_otros'], width, label='Otros', alpha=0.8)
    
    ax.set_xlabel('Departamento')
    ax.set_ylabel('Cantidad')
    ax.set_title('Distribución de Ayudas por Departamento')
    ax.set_xticks(x)
    ax.set_xticklabels(df_grouped['departamento'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Convertir a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')

def generar_grafico_por_evento(df_cleaned):
    """Genera gráfico circular de eventos - USANDO DATAFRAME LIMPIO"""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles por evento")
    
    df = df_cleaned.copy() # Trabajar con una copia
    
    # Agrupar por evento (ya limpio) y contar
    df_grouped = df.groupby('evento').size().reset_index(name='total')
    df_grouped = df_grouped.sort_values('total', ascending=False).head(8) # Top 8 eventos
    
    eventos = df_grouped['evento'].tolist()
    cantidades = df_grouped['total'].tolist()
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(eventos)))
    wedges, texts, autotexts = ax.pie(cantidades, labels=eventos, autopct='%1.1f%%', 
                                      colors=colors, startangle=90)
    
    ax.set_title('Distribución por Tipo de Evento', fontsize=14, pad=20)
    
    # Mejorar legibilidad
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.tight_layout()
    
    # Convertir a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')

def generar_grafico_tendencia_mensual(df_cleaned):
    """Genera gráfico de tendencia mensual - MEJORADO CON LIMPIEZA"""
    datos = AsistenciaHumanitaria.objects.extra(
        select={'mes': "EXTRACT(month FROM fecha)", 'ano': "EXTRACT(year FROM fecha)"}
    ).values('mes', 'ano').annotate(
        total_registros=Count('id')
    ).order_by('ano', 'mes')
    
    if not datos:
        return crear_grafico_sin_datos("No hay datos disponibles para tendencia mensual")
    
    df = pd.DataFrame(list(datos))
    
    # APLICAR LIMPIEZA DE DATOS (como en tu ejemplo)
    df = df.dropna(subset=['ano', 'mes'])
    
    # Convertir a enteros y crear fecha
    df['ano'] = df['ano'].astype(int)
    df['mes'] = df['mes'].astype(int)
    
    df['fecha'] = pd.to_datetime({
        'year': df['ano'],
        'month': df['mes'],
        'day': 1
    })
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['fecha'], df['total_registros'], marker='o', linewidth=2, markersize=6)
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Número de Registros')
    ax.set_title('Tendencia Mensual de Asistencias')
    ax.grid(True, alpha=0.3)
    
    # Formatear fechas en el eje x
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Convertir a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')

def datos_tabla_view(request):
    """API para obtener datos de la tabla con paginación"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    registros_raw = AsistenciaHumanitaria.objects.all().order_by('-fecha')
    total = registros_raw.count()
    
    data = []
    for registro in registros_raw[start:end]:
        # Create a dictionary from the model instance for cleaning
        record_dict = {field.name: getattr(registro, field.name) for field in registro._meta.fields}
        cleaned_record = data_cleaner.limpiar_registro_completo(record_dict)
        
        # Calculate total_ayudas from cleaned numeric fields
        total_ayudas_cleaned = sum(cleaned_record.get(field, 0) for field in data_cleaner.aid_fields)

        data.append({
            'fecha': cleaned_record['fecha'].strftime('%Y-%m-%d') if cleaned_record['fecha'] else None,
            'localidad': cleaned_record['localidad'],
            'distrito': cleaned_record['distrito'],
            'departamento': cleaned_record['departamento'],
            'evento': cleaned_record['evento'],
            'kit_a': cleaned_record['kit_a'],
            'kit_b': cleaned_record['kit_b'],
            'total_ayudas': total_ayudas_cleaned,
        })
    
    return JsonResponse({
        'data': data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

def crear_grafico_sin_datos(mensaje):
    """Crea un gráfico que muestra un mensaje cuando no hay datos"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.text(0.5, 0.5, mensaje, 
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=16,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Convertir a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')

def analisis_geografico_view(request):
    """Vista para análisis geográfico"""
    df_cleaned = _get_cleaned_dataframe()

    if df_cleaned.empty:
        context = {
            'datos_departamentos': [],
            'datos_distritos': [],
            'active_section': 'geografico'
        }
        return render(request, 'dashboard/geografico.html', context)

    # Estadísticas por departamento
    datos_departamentos = df_cleaned.groupby('departamento').agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()
    
    datos_departamentos['total_ayudas'] = datos_departamentos[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)
    
    datos_departamentos = datos_departamentos.sort_values('total_ayudas', ascending=False).to_dict('records')

    # Estadísticas por distrito
    datos_distritos = df_cleaned.groupby(['departamento', 'distrito']).agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()

    datos_distritos['total_ayudas'] = datos_distritos[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)
    
    datos_distritos = datos_distritos.sort_values(['departamento', 'total_ayudas'], ascending=[True, False]).to_dict('records')

    context = {
        'datos_departamentos': datos_departamentos,
        'datos_distritos': datos_distritos,
        'active_section': 'geografico'
    }
    
    return render(request, 'dashboard/geografico.html', context)

def analisis_temporal_view(request):
    """Vista para análisis temporal"""
    df_cleaned = _get_cleaned_dataframe()

    if df_cleaned.empty:
        context = {
            'datos_anuales': [],
            'datos_mensuales': [],
            'active_section': 'temporal'
        }
        return render(request, 'dashboard/temporal.html', context)

    # Asegurar que la columna 'fecha' sea de tipo datetime y no tenga nulos
    df = df_cleaned.dropna(subset=['fecha']).copy()
    
    # Datos por año
    df['ano'] = df['fecha'].dt.year
    datos_anuales = df.groupby('ano').agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()

    datos_anuales['total_ayudas'] = datos_anuales[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)
    
    datos_anuales['promedio_mensual'] = datos_anuales['total_registros'] / 12 # Aproximado
    datos_anuales = datos_anuales.sort_values('ano').to_dict('records')

    # Datos por mes
    df['mes'] = df['fecha'].dt.month
    datos_mensuales = df.groupby(['ano', 'mes']).agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()

    datos_mensuales['total_ayudas'] = datos_mensuales[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)
    
    datos_mensuales = datos_mensuales.sort_values(['ano', 'mes']).to_dict('records')

    context = {
        'datos_anuales': datos_anuales,
        'datos_mensuales': datos_mensuales,
        'active_section': 'temporal'
    }
    
    return render(request, 'dashboard/temporal.html', context)

def analisis_eventos_view(request):
    """Vista para análisis por eventos"""
    df_cleaned = _get_cleaned_dataframe()

    if df_cleaned.empty:
        context = {
            'datos_eventos': [],
            'eventos_departamento': [],
            'active_section': 'eventos'
        }
        return render(request, 'dashboard/eventos.html', context)

    # Datos por tipo de evento
    datos_eventos = df_cleaned.groupby('evento').agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()

    datos_eventos['total_ayudas'] = datos_eventos[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)
    
    datos_eventos = datos_eventos.sort_values('total_registros', ascending=False).to_dict('records')

    # Eventos por departamento
    eventos_departamento = df_cleaned.groupby(['departamento', 'evento']).agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()

    eventos_departamento['total_ayudas'] = eventos_departamento[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)
    
    eventos_departamento = eventos_departamento.sort_values(['departamento', 'total_registros'], ascending=[True, False]).to_dict('records')

    context = {
        'datos_eventos': datos_eventos,
        'eventos_departamento': eventos_departamento,
        'active_section': 'eventos'
    }
    
    return render(request, 'dashboard/eventos.html', context)

def datos_mapa_view(request):
    """API para obtener datos del mapa por departamento - USANDO DATAFRAME LIMPIO"""
    df_cleaned = _get_cleaned_dataframe()

    if df_cleaned.empty:
        return JsonResponse({'departamentos': []})

    # Agrupar por departamento (ya limpio) y calcular métricas
    datos_agrupados = df_cleaned.groupby('departamento').agg(
        total_registros=('id', 'count'),
        total_kit_a=('kit_a', 'sum'),
        total_kit_b=('kit_b', 'sum'),
        total_chapa_fibrocemento=('chapa_fibrocemento', 'sum'),
        total_chapa_zinc=('chapa_zinc', 'sum'),
        total_colchones=('colchones', 'sum'),
        total_frazadas=('frazadas', 'sum'),
        total_terciadas=('terciadas', 'sum'),
        total_puntales=('puntales', 'sum'),
        total_carpas_plasticas=('carpas_plasticas', 'sum'),
    ).reset_index()

    datos_agrupados['total_ayudas'] = datos_agrupados[[
        'total_kit_a', 'total_kit_b', 'total_chapa_fibrocemento', 'total_chapa_zinc',
        'total_colchones', 'total_frazadas', 'total_terciadas', 'total_puntales',
        'total_carpas_plasticas'
    ]].sum(axis=1)

    # Coordenadas aproximadas de los departamentos de Paraguay
    coordenadas_departamentos = {
        'CENTRAL': {'lat': -25.2637, 'lng': -57.5759, 'zoom': 10},
        'ALTO PARANÁ': {'lat': -25.5163, 'lng': -54.6436, 'zoom': 9},
        'ITAPÚA': {'lat': -26.8753, 'lng': -55.9178, 'zoom': 9},
        'CAAGUAZÚ': {'lat': -25.4669, 'lng': -56.0175, 'zoom': 9},
        'SAN PEDRO': {'lat': -24.0669, 'lng': -57.0789, 'zoom': 9},
        'CORDILLERA': {'lat': -25.3219, 'lng': -56.8467, 'zoom': 9},
        'GUAIRÁ': {'lat': -25.7833, 'lng': -56.4500, 'zoom': 9},
        'CAAZAPÁ': {'lat': -26.1978, 'lng': -56.3711, 'zoom': 9},
        'MISIONES': {'lat': -26.8833, 'lng': -57.0833, 'zoom': 9},
        'PARAGUARÍ': {'lat': -25.6319, 'lng': -57.1456, 'zoom': 9},
        'ALTO PARAGUAY': {'lat': -20.3167, 'lng': -58.1833, 'zoom': 8},
        'PDTE. HAYES': {'lat': -23.3500, 'lng': -59.0500, 'zoom': 8},
        'BOQUERON': {'lat': -22.6833, 'lng': -60.4167, 'zoom': 8},
        'AMAMBAY': {'lat': -22.5667, 'lng': -56.0333, 'zoom': 9},
        'CANINDEYÚ': {'lat': -24.1167, 'lng': -55.1667, 'zoom': 9},
        'CONCEPCIÓN': {'lat': -23.4167, 'lng': -57.4333, 'zoom': 9},
        'ÑEEMBUCÚ': {'lat': -26.9167, 'lng': -58.2833, 'zoom': 9},
        'SIN ESPECIFICAR': {'lat': -23.442503, 'lng': -58.443832, 'zoom': 6}, # Default para no especificado
        'VARIOS DEPARTAMENTOS': {'lat': -23.442503, 'lng': -58.443832, 'zoom': 6}, # Default para varios
        'CORONEL OVIEDO': {'lat': -25.4469, 'lng': -56.4469, 'zoom': 10},
        'ITÁ': {'lat': -25.4900, 'lng': -57.3500, 'zoom': 10},
        'ITAUGUÁ': {'lat': -25.3900, 'lng': -57.3700, 'zoom': 10},
        'VILLARRICA': {'lat': -25.7833, 'lng': -56.4333, 'zoom': 10},
        'ASUNCIÓN': {'lat': -25.2637, 'lng': -57.5759, 'zoom': 11},
    }

    resultado = []
    for index, item in datos_agrupados.iterrows():
        departamento = item['departamento']
        coords = coordenadas_departamentos.get(departamento, {'lat': -23.442503, 'lng': -58.443832, 'zoom': 6}) # Default Paraguay
        
        resultado.append({
            'departamento': departamento,
            'lat': coords['lat'],
            'lng': coords['lng'],
            'zoom': coords['zoom'],
            'total_registros': item['total_registros'],
            'total_ayudas': item['total_ayudas'],
            'total_kit_a': item['total_kit_a'],
            'total_kit_b': item['total_kit_b']
        })

    return JsonResponse({'departamentos': resultado})
