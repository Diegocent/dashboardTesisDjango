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
from .utils.data_cleaner import DataCleaner # Importar DataCleaner
import numpy as np
import time
import calendar
import locale # Importar el módulo locale

try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_PY.UTF-8') # Intenta con Paraguay
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '') # Fallback a la configuración por defecto del sistema
        print("Advertencia: No se pudo establecer el locale 'es_ES.UTF-8' o 'es_PY.UTF-8'. Los nombres de los meses pueden no estar en español.")

# Configurar matplotlib para español
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 10

# Inicializar el limpiador de datos
cleaner = DataCleaner()

# --- Mecanismo de Caché en Memoria ---
_cache = {
    'cleaned_df': None,
    'last_df_update': 0,
    'graphs': {} # Para almacenar gráficos codificados en base64
}
CACHE_TIMEOUT_SECONDS = 300 # Cachear datos y gráficos por 5 minutos (ajustar según necesidad)

def _get_cleaned_dataframe():
    """
    Obtiene todos los datos de AsistenciaHumanitaria, los convierte a un DataFrame
    y aplica la limpieza completa usando DataCleaner. Implementa caching.
    """
    current_time = time.time()
    # Si el DataFrame está en caché y no ha expirado, lo retornamos
    if _cache['cleaned_df'] is not None and (current_time - _cache['last_df_update']) < CACHE_TIMEOUT_SECONDS:
        return _cache['cleaned_df']

    # Si no está en caché o ha expirado, lo generamos
    queryset = AsistenciaHumanitaria.objects.all().values(
        'id', 'fecha', 'localidad', 'distrito', 'departamento', 'evento',
        'kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc', 'colchones',
        'frazadas', 'terciadas', 'puntales', 'carpas_plasticas'
    )
        
    if not queryset.exists():
        df = pd.DataFrame() # Retorna un DataFrame vacío si no hay datos
    else:
        df = pd.DataFrame(list(queryset))  
        # Asegurar que la columna 'fecha' sea de tipo datetime y manejar nulos
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        # Aplicar operaciones de limpieza directamente a las columnas del DataFrame
        # Limpiar campos numéricos
        for field in cleaner.aid_fields:
            df[field] = df[field].apply(cleaner.limpiar_numero)
        # Limpiar campos de texto
        df['departamento'] = df['departamento'].apply(cleaner.limpiar_departamento)
        df['evento'] = df['evento'].apply(cleaner.limpiar_texto).apply(cleaner.limpiar_evento)
        df['localidad'] = df['localidad'].apply(cleaner.limpiar_texto)
        df['distrito'] = df['distrito'].apply(cleaner.limpiar_texto)
        # Aplicar post-procesamiento de eventos (requiere campos de ayuda ya limpios)
        df['evento'] = df.apply(cleaner.post_process_eventos_with_aids, axis=1)
    
    # Almacenar el DataFrame limpio en caché
    _cache['cleaned_df'] = df
    _cache['last_df_update'] = current_time
    _cache['graphs'] = {} # Limpiar la caché de gráficos cuando los datos se refrescan
    return df

def _get_cached_graph(graph_name, df_cleaned, graph_generation_func):
    """Función auxiliar para obtener o generar un gráfico con caching."""
    current_time = time.time()
    # Si el gráfico está en caché y no ha expirado (basado en la última actualización del DF), lo retornamos
    if graph_name in _cache['graphs'] and (current_time - _cache['last_df_update']) < CACHE_TIMEOUT_SECONDS:
        return _cache['graphs'][graph_name]
        
    # Si no está en caché o ha expirado, lo generamos
    graphic = graph_generation_func(df_cleaned)
    _cache['graphs'][graph_name] = graphic
    return graphic

def dashboard_view(request):
    """Vista principal del dashboard"""
    df_cleaned = _get_cleaned_dataframe()
        
    # Estadísticas generales
    total_registros = df_cleaned.shape[0]
    total_departamentos = df_cleaned['departamento'].nunique() if not df_cleaned.empty else 0
    total_localidades = df_cleaned['localidad'].nunique() if not df_cleaned.empty else 0
        
    # Obtener datos para gráficos usando la función de ayuda con caché
    grafico_ayudas_por_ano = _get_cached_graph('ayudas_por_ano', df_cleaned, generar_grafico_ayudas_por_ano)
    grafico_departamentos = _get_cached_graph('departamentos', df_cleaned, generar_grafico_por_departamento)
    grafico_eventos = _get_cached_graph('eventos', df_cleaned, generar_grafico_por_evento)
    grafico_tendencia_mensual = _get_cached_graph('tendencia_mensual', df_cleaned, generar_grafico_tendencia_mensual)

    # Datos para tablas (usamos el ORM para paginación, pero limpiamos al vuelo)
    ultimos_registros_raw = AsistenciaHumanitaria.objects.order_by('-fecha')[:10]
        
    ultimos_registros_cleaned = []
    for r in ultimos_registros_raw:
        # Crear un diccionario a partir de la instancia del modelo para la limpieza
        record_dict = {field.name: getattr(r, field.name) for field in r._meta.fields}
        cleaned_record = cleaner.limpiar_registro_completo(record_dict)
            
        # Calcular total_ayudas a partir de los campos numéricos limpios
        cleaned_record['total_ayudas'] = sum(cleaned_record.get(field, 0) for field in cleaner.aid_fields)
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
        
    datos_departamentos['total_ayudas'] = datos_departamentos[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
        
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
    datos_distritos['total_ayudas'] = datos_distritos[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
        
    datos_distritos = datos_distritos.sort_values(['departamento', 'total_ayudas'], ascending=[True, False]).to_dict('records')
    #para los graficos
    grafico_departamentos = _get_cached_graph('departamentos', df_cleaned, generar_grafico_por_departamento)
    grafico_total_ayudas_departamento = _get_cached_graph('total_ayudas_departamento', df_cleaned, generar_grafico_total_ayudas_departamento)
    grafico_top_localidades = _get_cached_graph('top_localidades', df_cleaned, generar_grafico_top_localidades)
    grafico_evolucion_ayudas_top_departamentos = _get_cached_graph('evolucion_ayudas_top_departamentos', df_cleaned, generar_grafico_evolucion_ayudas_top_departamentos)
    grafico_heatmap_departamento_anio = _get_cached_graph('heatmap_departamento_anio', df_cleaned, generar_grafico_heatmap_departamento_anio)


    context = {
        'datos_departamentos': datos_departamentos,
        'datos_distritos': datos_distritos,
        'active_section': 'geografico',
        'grafico_departamentos': grafico_departamentos,
        'grafico_total_ayudas_departamento': grafico_total_ayudas_departamento,
        'grafico_top_localidades': grafico_top_localidades,
        'grafico_evolucion_ayudas_top_departamentos': grafico_evolucion_ayudas_top_departamentos,
        'grafico_heatmap_departamento_anio': grafico_heatmap_departamento_anio
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
    #Para los graficos
    grafico_ayudas_mensual = _get_cached_graph('ayudas_mensual', df_cleaned, generar_grafico_ayudas_mensual)
    grafico_ayudas_por_ano = _get_cached_graph('ayudas_por_ano', df_cleaned, generar_grafico_ayudas_por_ano)
    grafico_distribucion_anual_ayuda_principal = _get_cached_graph('distribucion_anual_ayuda_principal', df_cleaned, generar_grafico_distribucion_anual_ayuda_principal)
    grafico_tendencia_mensual = _get_cached_graph('tendencia_mensual', df_cleaned, generar_grafico_tendencia_mensual)


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
    datos_anuales['total_ayudas'] = datos_anuales[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
        
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
    datos_mensuales['total_ayudas'] = datos_mensuales[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
        
    datos_mensuales = datos_mensuales.sort_values(['ano', 'mes']).to_dict('records')
    # Añadir el nombre del mes
    for mes_data in datos_mensuales: # Cambiado 'mes' a 'mes_data' para evitar conflicto con la columna 'mes'
        mes_data['mes_nombre'] = calendar.month_name[mes_data['mes']].capitalize()
    context = {
        'datos_anuales': datos_anuales,
        'datos_mensuales': datos_mensuales,
        'active_section': 'temporal',
        'grafico_ayudas_mensual': grafico_ayudas_mensual,
        'grafico_ayudas_por_ano': grafico_ayudas_por_ano,
        'grafico_distribucion_anual_ayuda_principal': grafico_distribucion_anual_ayuda_principal,
        'grafico_tendencia_mensual': grafico_tendencia_mensual
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
    datos_eventos['total_ayudas'] = datos_eventos[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
        
    datos_eventos = datos_eventos.sort_values('total_registros', ascending=False).to_dict('records')

    #para los graficos
    grafico_eventos = _get_cached_graph('eventos', df_cleaned, generar_grafico_por_evento)
    grafico_eventos_mayor_ayuda = _get_cached_graph('eventos_mayor_ayuda', df_cleaned, generar_grafico_eventos_mayor_ayuda)
    grafico_composicion_ayudas_por_evento = _get_cached_graph('composicion_ayudas_por_evento', df_cleaned, generar_grafico_composicion_ayudas_por_evento)
    grafico_top_eventos_frecuentes_seaborn = _get_cached_graph('top_eventos_frecuentes_seaborn', df_cleaned, generar_grafico_top_eventos_frecuentes_seaborn)
    grafico_comparacion_eventos_por_anio = _get_cached_graph('comparacion_eventos_por_anio', df_cleaned, generar_grafico_comparacion_eventos_por_anio)
    grafico_heatmap_eventos_por_anio = _get_cached_graph('heatmap_eventos_por_anio', df_cleaned, generar_grafico_heatmap_eventos_por_anio)
    grafico_eventos_comunes_total_anio = _get_cached_graph('eventos_comunes_total_anio', df_cleaned, generar_grafico_eventos_comunes_total_anio)
    grafico_tendencia_mensual_eventos_alternativo = _get_cached_graph('tendencia_mensual_eventos_alternativo', df_cleaned, generar_grafico_tendencia_mensual_eventos_alternativo)

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
    eventos_departamento['total_ayudas'] = eventos_departamento[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
        
    eventos_departamento = eventos_departamento.sort_values(['departamento', 'total_registros'], ascending=[True, False]).to_dict('records')
    context = {
        'datos_eventos': datos_eventos,
        'eventos_departamento': eventos_departamento,
        'active_section': 'eventos',
        'grafico_eventos': grafico_eventos,
        'grafico_eventos_mayor_ayuda': grafico_eventos_mayor_ayuda,
        'grafico_composicion_ayudas_por_evento': grafico_composicion_ayudas_por_evento,
        'grafico_top_eventos_frecuentes_seaborn': grafico_top_eventos_frecuentes_seaborn,
        'grafico_comparacion_eventos_por_anio': grafico_comparacion_eventos_por_anio,
        'grafico_heatmap_eventos_por_anio': grafico_heatmap_eventos_por_anio,
        'grafico_eventos_comunes_total_anio': grafico_eventos_comunes_total_anio,
        'grafico_tendencia_mensual_eventos_alternativo': grafico_tendencia_mensual_eventos_alternativo,

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
    datos_agrupados['total_ayudas'] = datos_agrupados[[f'total_{field}' for field in cleaner.aid_fields]].sum(axis=1)
    # Coordenadas aproximadas de los departamentos de Paraguay
    coordenadas_departamentos = {
        'CAPITAL': {'lat': -25.2967, 'lng': -57.6359, 'zoom': 12}, # Asunción con posición más centrada y zoom más cercano
        'CENTRAL': {'lat': -25.3637, 'lng': -57.4259, 'zoom': 10}, # Central desplazado al este
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
            'total_kits': item['total_kit_a'] + item['total_kit_b'],
            'total_chapa_fibrocemento': item['total_chapa_fibrocemento'],
            'total_chapa_zinc': item['total_chapa_zinc'],
        })
    return JsonResponse({'departamentos': resultado})

def generar_grafico_ayudas_por_ano(df_cleaned):
    """Genera gráfico de distribución de ayudas por año - USANDO DATAFRAME LIMPIO"""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para mostrar ayudas por año")
        
    df = df_cleaned.copy() # Trabajar con una copia
        
    # Extraer año de la fecha limpia
    df['AÑO'] = df['fecha'].dt.year
        
    # Columnas de ayudas (ya limpias y numéricas por _get_cleaned_dataframe)
    ayudas = [col for col in cleaner.aid_fields if col in df.columns] # Asegurarse de que las columnas existan
        
    # Agrupar por año y sumar ayudas
    df_grouped = df.groupby('AÑO')[ayudas].sum()
    if df_grouped.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por año para mostrar ayudas.")
        
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
    plt.title('Distribución de Asistencias por Año', pad=20, fontsize=14)
    plt.ylabel('Cantidad distribuida', fontsize=12)
    plt.xlabel('Año', fontsize=12)
    plt.legend(
        title='Tipo de Asistencia',
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
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]
        
    # Agrupar por departamento (ya limpio) y sumar ayudas
    df_grouped = df.groupby('departamento')[ayudas].sum().reset_index()
    if df_grouped.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por departamento.")
        
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
    ax.set_title('Distribución de Asistencias por Departamento')
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
    if df_grouped.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por evento.")
    
    # Calcular porcentajes
    df_grouped['percentage'] = (df_grouped['total'] / df_grouped['total'].sum()) * 100

    # Definir un umbral para agrupar eventos pequeños
    threshold_percent = 3.0 # Por ejemplo, agrupar eventos con menos del 3%
    
    # Separar eventos grandes y pequeños
    df_large_events = df_grouped[df_grouped['percentage'] >= threshold_percent]
    df_small_events = df_grouped[df_grouped['percentage'] < threshold_percent]
    
    eventos = df_large_events['evento'].tolist()
    cantidades = df_large_events['total'].tolist()

    # Si hay eventos pequeños, sumarlos en una categoría "Otros"
    if not df_small_events.empty:
        otros_total = df_small_events['total'].sum()
        eventos.append('OTROS')
        cantidades.append(otros_total)
    
    # Ordenar para asegurar que los "Otros" no siempre estén al final si no es el más pequeño
    # Opcional: puedes ordenar por cantidad si quieres los más grandes primero
    # combined_data = sorted(zip(eventos, cantidades), key=lambda x: x[1], reverse=True)
    # eventos = [item[0] for item in combined_data]
    # cantidades = [item[1] for item in combined_data]

    fig, ax = plt.subplots(figsize=(10, 10)) # Aumentar el tamaño para mejor legibilidad
            
    colors = plt.cm.Set3(np.linspace(0, 1, len(eventos)))
    
    # Función para autopct que puede ajustar el formato o esconder si es muy pequeño
    def autopct_format(pct):
        return ('%1.1f%%' % pct) if pct > 1 else '' # Solo mostrar porcentaje si es mayor a 1%

    wedges, texts, autotexts = ax.pie(cantidades, labels=eventos, autopct=autopct_format, 
                                      colors=colors, startangle=90, 
                                      pctdistance=0.85, labeldistance=1.05) # Ajustar distancias
            
    ax.set_title('Distribución de asistencias por Tipo de Evento', fontsize=16, pad=20) # Aumentar tamaño del título
            
    # Mejorar legibilidad de los porcentajes
    for autotext in autotexts:
        autotext.set_color('black') # Cambiar a negro para mejor contraste
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10) # Reducir tamaño de fuente si es necesario

    # Ajustar la posición de las etiquetas de texto (nombres de eventos)
    for text in texts:
        text.set_fontsize(11) # Ajustar tamaño de fuente de las etiquetas
        text.set_color('black') # Asegurar que las etiquetas sean visibles

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
    """Genera gráfico de tendencia mensual - USANDO DATAFRAME LIMPIO"""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para tendencia mensual")
        
    df = df_cleaned.copy() # Trabajar con una copia
        
    # Asegurar que la columna 'fecha' sea de tipo datetime y no tenga nulos
    df = df.dropna(subset=['fecha'])
        
    # Si después de eliminar NaNs, el DataFrame se vuelve vacío, retornar gráfico sin datos
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para tendencia mensual")
    # Extraer mes y año de la fecha limpia
    df['mes'] = df['fecha'].dt.month
    df['ano'] = df['fecha'].dt.year
        
    # Agrupar por año y mes y contar registros
    df_grouped = df.groupby(['ano', 'mes']).size().reset_index(name='total_registros')
    if df_grouped.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por mes/año para tendencia mensual.")
        
    # Si df_grouped está vacío después de agrupar
    if df_grouped.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por mes/año para tendencia mensual")
    # CORRECCIÓN: Usar un diccionario con las claves 'year', 'month', 'day'
    df_grouped['fecha_plot'] = pd.to_datetime({
        'year': df_grouped['ano'],
        'month': df_grouped['mes'],
        'day': 1 # Se requiere un día para ensamblar la fecha
    })
        
    fig, ax = plt.subplots(figsize=(12, 6))
        
    ax.plot(df_grouped['fecha_plot'], df_grouped['total_registros'], marker='o', linewidth=2, markersize=6)
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

# --- Nuevas funciones de gráficos ---

import logging
logger = logging.getLogger(__name__)

def generar_grafico_ayudas_mensual(df_cleaned):
    """Genera gráfico de distribución mensual de ayudas humanitarias (barras apiladas)."""

    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la distribución mensual de ayudas.")

    df = df_cleaned.copy()

    df = df.dropna(subset=['fecha'])

    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos.")

    df['MES'] = df['fecha'].dt.month

    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    plot_data = df.groupby('MES')[ayudas].sum()

    if plot_data.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por mes para la distribución mensual de ayudas.")

    fig, ax = plt.subplots(figsize=(12, 6))

    plot_data.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        colormap='viridis',
        edgecolor='black',
        width=0.8
    )

    plt.title('Distribución Mensual de Asistencias', fontsize=14, pad=20)
    plt.ylabel('Total de Unidades Distribuidas', fontsize=12)
    plt.xlabel('Mes', fontsize=12)

    meses_abreviados = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    ax.set_xticks(range(len(meses_abreviados)))
    ax.set_xticklabels(meses_abreviados, rotation=0)

    totals = plot_data.sum(axis=1)

    for i, total in enumerate(totals):
        if total > 0:
            ax.text(
                i,
                total + (0.05 * totals.max() if totals.max() > 0 else 0.05),
                f'{int(total):,}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold'
            )

    plt.legend(
        title='Tipos de Asistencia',
        bbox_to_anchor=(1.05, 1),
        frameon=True,
        framealpha=1
    )

    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    # print(f">>> Gráfico mensual generado correctamente.{image_png}", file=sys.stderr)
    return base64.b64encode(image_png).decode('utf-8')



def generar_grafico_total_ayudas_departamento(df_cleaned):
    """Genera gráfico de total de ayudas por departamento."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para el total de ayudas por departamento.")
    
    df = df_cleaned.copy()
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    # Sumar todas las ayudas por departamento
    df_grouped = df.groupby('departamento')[ayudas].sum().sum(axis=1).sort_values(ascending=False)
    if df_grouped.empty:
        return crear_grafico_sin_datos("No hay datos agrupados para el total de ayudas por departamento.")

    fig, ax = plt.subplots(figsize=(20, 10))
    df_grouped.plot(
        kind='bar',
        color='skyblue',
        edgecolor='black',
        ax=ax
    )

    plt.title('Totales por Departamento', fontsize=16, pad=20)
    plt.ylabel('Cantidad total de unidades distribuidas', fontsize=12, labelpad=15)
    plt.xlabel('Departamento', fontsize=12, labelpad=15)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    for p in ax.patches:
        if p.get_height() > 0: # Solo añadir etiqueta si hay valor
            ax.annotate(f"{int(p.get_height()):,}",
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center',
                        xytext=(0, 10),
                        textcoords='offset points',
                        fontsize=9)

    plt.figtext(0.5, 0.01,
                "Nota: Los valores representan la suma total de unidades físicas distribuidas (kits, chapas, colchones, etc.)",
                ha="center", fontsize=10, bbox={"facecolor":"white", "alpha":0.8, "pad":5})

    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_top_localidades(df_cleaned):
    """Genera gráfico de top 5 localidades con más eventos de asistencia."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para las top localidades.")
    
    df = df_cleaned.copy()
    df = df[df['localidad'] != 'SIN ESPECIFICAR']
    top_localidades = df['localidad'].value_counts().head(5)
    if top_localidades.empty:
        return crear_grafico_sin_datos("No hay datos de localidades para determinar las top localidades.")

    fig, ax = plt.subplots(figsize=(10, 5))
    top_localidades.plot(kind='barh', ax=ax)
    plt.title('Localidades con más Eventos Registrados')
    plt.xlabel('Número de Eventos')
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_correlacion_ayudas(df_cleaned):
    """Genera gráfico de correlación entre tipos de ayuda (heatmap)."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la correlación de ayudas.")
    
    df = df_cleaned.copy()
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    corr_matrix = df[ayudas].corr()
    if corr_matrix.empty:
        return crear_grafico_sin_datos("No hay datos suficientes para calcular la matriz de correlación.")

    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

    fig, ax = plt.subplots(figsize=(10, 8)) # Ajustado el tamaño para un solo gráfico
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap='coolwarm',
                center=0, linewidths=0.5, ax=ax)
    plt.title('Correlación entre Tipos de Asistencia', pad=15)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_distribucion_anual_ayuda_principal(df_cleaned):
    """Genera gráfico de distribución anual de la ayuda principal."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la distribución anual de ayuda principal.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para la distribución anual de ayuda principal.")

    df['AÑO'] = df['fecha'].dt.year
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    total_ayudas_por_tipo = df[ayudas].sum().sort_values(ascending=False)
    if total_ayudas_por_tipo.empty:
        return crear_grafico_sin_datos("No hay tipos de asistencia para determinar la ayuda principal.")
    
    ayuda_principal = total_ayudas_por_tipo.idxmax()

    # No es necesario un check de empty aquí si ya se hizo en total_ayudas_por_tipo.empty

    fig, ax = plt.subplots(figsize=(10, 6)) # Ajustado el tamaño para un solo gráfico
    df.groupby('AÑO')[ayuda_principal].sum().plot(
        kind='line', marker='o', color='skyblue', linewidth=2.5, ax=ax) # Usar un color específico

    plt.title(f'Distribución Anual de {ayuda_principal}')
    plt.ylabel('Unidades distribuidas')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_evolucion_ayudas_top_departamentos(df_cleaned):
    """Genera gráfico de evolución de ayudas en los 5 departamentos más asistidos."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la evolución de ayudas por departamento.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para la evolución de ayudas por departamento.")

    df['AÑO'] = df['fecha'].dt.year
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    # Preparar datos
    top_deptos = df['departamento'].value_counts().nlargest(5).index
    df_top = df[df['departamento'].isin(top_deptos)]
    
    if df_top.empty:
        return crear_grafico_sin_datos("No hay datos para los top 5 departamentos.")

    pivot_data = df_top.groupby(['AÑO', 'departamento'])[ayudas].sum().sum(axis=1).unstack()
    if pivot_data.empty:
        return crear_grafico_sin_datos("No hay datos pivotados para la evolución de ayudas por departamento.")

    fig, ax = plt.subplots(figsize=(18, 8))

    markers = ['o', 's', 'D', '^', 'v', 'p', '*']
    for i, depto in enumerate(pivot_data.columns):
        ax.plot(pivot_data.index, pivot_data[depto],
                marker=markers[i % len(markers)],
                markersize=8,
                linewidth=2.5,
                label=depto)

    plt.title('Departamentos con más Asistencias por año', fontsize=15)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Total de Unidades Distribuidas', fontsize=12)
    plt.legend(title='Departamento', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)

    for depto in pivot_data.columns:
        # Asegurarse de que haya datos para el departamento
        if not pivot_data[depto].empty:
            max_val = pivot_data[depto].max()
            year_max = pivot_data[depto].idxmax()
            if pd.notna(max_val) and pd.notna(year_max):
                ax.annotate(f"{int(max_val):,}",
                            xy=(year_max, max_val),
                            xytext=(0, 10),
                            textcoords='offset points',
                            ha='center',
                            fontsize=9,
                            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_heatmap_departamento_anio(df_cleaned):
    """Genera un heatmap de distribución de ayudas por departamento y año."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para el heatmap de departamento por año.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para el heatmap de departamento por año.")

    df['AÑO'] = df['fecha'].dt.year
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    heatmap_data = df.groupby(['departamento', 'AÑO'])[ayudas].sum().sum(axis=1).unstack().fillna(0)
    if heatmap_data.empty:
        return crear_grafico_sin_datos("No hay datos para el heatmap de departamento por año.")

    fig, ax = plt.subplots(figsize=(15, 8))
    sns.heatmap(heatmap_data, annot=True, fmt=",.0f", cmap="YlOrRd",
                linewidths=0.5, linecolor='gray', ax=ax)
    plt.title('Distribución de Asistencias por Departamento y Año', pad=15)
    plt.xlabel('Año')
    plt.ylabel('Departamento')
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_eventos_mayor_ayuda(df_cleaned):
    """Genera gráfico de eventos con mayor distribución de ayuda."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para eventos con mayor ayuda.")
    
    df = df_cleaned.copy()
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    evento_ayudas = df.groupby('evento')[ayudas].sum().sum(axis=1).nlargest(5)
    if evento_ayudas.empty:
        return crear_grafico_sin_datos("No hay datos de eventos para determinar los eventos con mayor ayuda.")

    fig, ax = plt.subplots(figsize=(10, 6)) # Ajustado el tamaño para un solo gráfico
    colors = plt.cm.Paired.colors # Usar Paired para consistencia
    ax = evento_ayudas.plot(kind='barh', color=colors, ax=ax)

    for i, v in enumerate(evento_ayudas):
        if v > 0: # Solo añadir etiqueta si hay valor
            ax.text(v + 0.01 * evento_ayudas.max(), i, f"{int(v):,}", color='black', va='center')

    plt.title('Eventos con Mayor Unidades Distribuidas', pad=15)
    plt.xlabel('Total de Unidades Distribuidas')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_composicion_ayudas_por_evento(df_cleaned):
    """Genera gráfico de composición de ayudas por tipo de evento (normalizado)."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la composición de ayudas por evento.")
    
    df = df_cleaned.copy()
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    top_5_eventos = df['evento'].value_counts().nlargest(5).index
    df_top_events = df[df['evento'].isin(top_5_eventos)]

    if df_top_events.empty:
        return crear_grafico_sin_datos("No hay datos suficientes para la composición de ayudas por evento.")

    event_aid_composition = df_top_events.groupby('evento')[ayudas].sum()
    
    # Manejar el caso donde la suma de ayudas por evento es cero para evitar división por cero
    sum_axis_1 = event_aid_composition.sum(axis=1)
    event_aid_composition_norm = event_aid_composition.div(sum_axis_1.replace(0, np.nan), axis=0).fillna(0)
    if event_aid_composition_norm.empty:
        return crear_grafico_sin_datos("No hay datos normalizados para la composición de ayudas por evento.")

    fig, ax = plt.subplots(figsize=(15, 8))
    if not event_aid_composition_norm.empty:
        event_aid_composition_norm.plot(
            kind='bar',
            stacked=True,
            colormap='viridis',
            ax=ax
        )
        plt.title('Composición de Ayudas por Tipo de Evento (Normalizado por Evento)', pad=15)
        plt.ylabel('Proporción de Ayuda')
        plt.xlabel('Tipo de Evento')
        plt.legend(title='Tipo de Ayuda', bbox_to_anchor=(1.05, 1))
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.6)
    else:
        ax.text(0.5, 0.5, 'No hay datos suficientes', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Datos insuficientes')
        ax.axis('off') # Ocultar ejes si no hay datos

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_top_eventos_frecuentes_seaborn(df_cleaned):
    """Genera gráfico de top 10 tipos de evento más frecuentes (Seaborn barplot)."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para los top eventos frecuentes (Seaborn).")
    
    df = df_cleaned.copy()
    event_counts = df['evento'].value_counts().nlargest(5)
    if event_counts.empty:
        return crear_grafico_sin_datos("No hay datos de eventos para determinar los top eventos frecuentes (Seaborn).")

    fig, ax = plt.subplots(figsize=(10, 6)) # Ajustado el tamaño para un solo gráfico
    sns.barplot(x=event_counts.values,
                y=event_counts.index,
                palette="rocket",
                dodge=False,
                ax=ax)
    
    plt.title('Eventos por mayor distribución.', pad=15, fontsize=14)
    plt.xlabel('Número de Ocurrencias', fontsize=12)
    plt.ylabel('')
    plt.grid(axis='x', linestyle='--', alpha=0.3)

    for i, v in enumerate(event_counts):
        if v > 0: # Solo añadir etiqueta si hay valor
            ax.text(v + 0.02 * event_counts.max(), i, f"{int(v):,}",
                    color='black', va='center', fontsize=10)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_comparacion_eventos_por_anio(df_cleaned):
    """Genera gráfico de comparación de eventos por año (barras agrupadas)."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la comparación de eventos por año.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para la comparación de eventos por año.")

    df['AÑO'] = df['fecha'].dt.year
    ayudas = [col for col in cleaner.aid_fields if col in df.columns]

    # Asegurarse de que las columnas de ayuda sean numéricas
    for field in ayudas:
        df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)

    eventos_por_anio = df.groupby('AÑO')['evento'].value_counts().unstack().fillna(0)
    
    if eventos_por_anio.empty:
        return crear_grafico_sin_datos("No hay datos de eventos por año para comparar.")

    top_anios = eventos_por_anio.sum(axis=1).nlargest(6).index
    top_eventos = eventos_por_anio.sum().nlargest(5).index
    datos_grafico = eventos_por_anio.loc[top_anios, top_eventos]
    if datos_grafico.empty:
        return crear_grafico_sin_datos("No hay datos suficientes para la comparación de eventos por año.")

    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(datos_grafico.index))
    width = 0.15
    n = len(datos_grafico.columns)

    for i, evento in enumerate(datos_grafico.columns):
        pos = x + width * i - width * (n - 1) / 2
        ax.bar(pos, datos_grafico[evento],
               width=width,
               label=evento,
               edgecolor='black')

    plt.title('Comparación de eventos por año', fontsize=14, pad=20)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Número de eventos', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(datos_grafico.index)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend(title='Tipos de Evento', bbox_to_anchor=(1.05, 1), frameon=True)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_heatmap_eventos_por_anio(df_cleaned):
    """Genera un mapa de calor de eventos más comunes por año."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para el heatmap de eventos por año.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para el heatmap de eventos por año.")

    df['AÑO'] = df['fecha'].dt.year
    eventos_por_anio = df.groupby('AÑO')['evento'].value_counts().unstack().fillna(0)

    if eventos_por_anio.empty:
        return crear_grafico_sin_datos("No hay datos de eventos por año para el heatmap.")

    top_anios = eventos_por_anio.sum(axis=1).nlargest(6).index
    top_eventos = eventos_por_anio.sum().nlargest(6).index
    datos_grafico = eventos_por_anio.loc[top_anios, top_eventos]
    if datos_grafico.empty:
        return crear_grafico_sin_datos("No hay datos suficientes para el heatmap de eventos por año.")

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(datos_grafico, annot=True, fmt='.0f', cmap='YlOrRd', linewidths=0.5, ax=ax)
    plt.title('Mapa de calor: Eventos más comunes por año', fontsize=14, pad=20)
    plt.xlabel('Tipos de Evento', fontsize=12)
    plt.ylabel('Año', fontsize=12)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_eventos_comunes_total_anio(df_cleaned):
    """Genera un gráfico de embudo para los eventos más comunes (total por año)."""
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para el embudo de eventos por año.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para el embudo de eventos por año.")

    df['AÑO'] = df['fecha'].dt.year
    eventos_por_anio = df.groupby('AÑO')['evento'].value_counts().unstack().fillna(0)

    if eventos_por_anio.empty:
        return crear_grafico_sin_datos("No hay datos de eventos por año para el embudo.")

    top_anios = eventos_por_anio.sum(axis=1).nlargest(5).index
    top_eventos_anio = eventos_por_anio.sum().nlargest(5).index
    datos_anio = eventos_por_anio.loc[top_anios, top_eventos_anio].sum().sort_values(ascending=False)
    if datos_anio.empty:
        return crear_grafico_sin_datos("No hay datos suficientes para el embudo de eventos por año.")

    fig, ax = plt.subplots(figsize=(10, 6))
    embudo = ax.barh(range(len(datos_anio)), datos_anio.values,
                     color=plt.cm.viridis_r(np.linspace(0.2, 0.8, len(datos_anio))))

    plt.title('Eventos más Comunes (Total por Año)', fontsize=14, pad=20)
    plt.xlabel('Número total de eventos', fontsize=12)
    plt.ylabel('Tipo de Evento', fontsize=12)
    ax.set_yticks(range(len(datos_anio)))
    ax.set_yticklabels(datos_anio.index)
    plt.grid(axis='x', linestyle='--', alpha=0.6)

    for i, bar in enumerate(embudo):
        width = bar.get_width()
        if width > 0: # Solo añadir etiqueta si hay valor
            ax.text(width + 0.02 * datos_anio.max(), i, f"{int(width)}",
                    va='center', fontsize=10)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')

def generar_grafico_tendencia_mensual_eventos_alternativo(df_cleaned):
    """
    Genera un gráfico de línea para la tendencia mensual de eventos,
    como alternativa al gráfico de cascada.
    """
    if df_cleaned.empty:
        return crear_grafico_sin_datos("No hay datos disponibles para la tendencia mensual de eventos.")
    
    df = df_cleaned.copy()
    df = df.dropna(subset=['fecha'])
    if df.empty:
        return crear_grafico_sin_datos("No hay datos de fecha válidos para la tendencia mensual de eventos.")

    df['MES'] = df['fecha'].dt.month
    df['AÑO'] = df['fecha'].dt.year

    # Agrupar por año y mes y contar eventos
    eventos_por_mes_anio = df.groupby(['AÑO', 'MES']).size().reset_index(name='total_eventos')
    if eventos_por_mes_anio.empty:
        return crear_grafico_sin_datos("No hay datos agrupados por mes/año para la tendencia de eventos.")

    # Crear una columna de fecha para el eje X
    eventos_por_mes_anio['fecha_plot'] = pd.to_datetime(eventos_por_mes_anio['AÑO'].astype(str) + '-' + eventos_por_mes_anio['MES'].astype(str) + '-01')
    
    eventos_por_mes_anio = eventos_por_mes_anio.sort_values('fecha_plot')

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(eventos_por_mes_anio['fecha_plot'], eventos_por_mes_anio['total_eventos'],
            marker='o', linestyle='-', color='teal', linewidth=2)

    plt.title('Número de Eventos Mensual', fontsize=14, pad=20)
    plt.xlabel('Fecha', fontsize=12)
    plt.ylabel('Número de Eventos', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)

    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3)) # Mostrar cada 3 meses
    plt.xticks(rotation=45, ha='right')

    # Añadir etiquetas de valor en los puntos
    for x, y in zip(eventos_por_mes_anio['fecha_plot'], eventos_por_mes_anio['total_eventos']):
        if y > 0: # Solo añadir etiqueta si hay valor
            ax.text(x, y + 0.02 * eventos_por_mes_anio['total_eventos'].max(), f"{int(y)}",
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')


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
        cleaned_record = cleaner.limpiar_registro_completo(record_dict)
            
        # Calculate total_ayudas from cleaned numeric fields
        total_ayudas_cleaned = sum(cleaned_record.get(field, 0) for field in cleaner.aid_fields)
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
