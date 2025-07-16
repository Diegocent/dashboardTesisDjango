"""
Script de verificación de conexión a base de datos
Ejecutar con: python manage.py shell < scripts/setup_database.py
"""

from dashboard.models import AsistenciaHumanitaria
from django.db import connection

def verificar_conexion():
    """Verifica la conexión y muestra estadísticas de datos existentes"""
    try:
        # Verificar conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        print("✅ Conexión a base de datos exitosa")
        
        # Mostrar estadísticas de datos existentes
        total_registros = AsistenciaHumanitaria.objects.count()
        print(f"📊 Total de registros encontrados: {total_registros}")
        
        if total_registros > 0:
            # Mostrar rango de fechas
            primer_registro = AsistenciaHumanitaria.objects.order_by('fecha').first()
            ultimo_registro = AsistenciaHumanitaria.objects.order_by('-fecha').first()
            
            print(f"📅 Rango de fechas: {primer_registro.fecha} a {ultimo_registro.fecha}")
            
            # Mostrar departamentos únicos
            departamentos = AsistenciaHumanitaria.objects.values_list('departamento', flat=True).distinct()
            print(f"🏛️ Departamentos: {list(departamentos)}")
            
            # Mostrar eventos únicos
            eventos = AsistenciaHumanitaria.objects.values_list('evento', flat=True).distinct()
            print(f"⚡ Tipos de eventos: {list(eventos)}")
            
            print("\n🎉 Tu base de datos está lista para usar con el dashboard!")
        else:
            print("⚠️ No se encontraron registros en la tabla asistencia_humanitaria")
            print("   Asegúrate de que tu tabla tenga datos antes de usar el dashboard")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("   Verifica la configuración de la base de datos en settings.py")

# Ejecutar verificación
verificar_conexion()
