"""
Comando Django para limpiar y estandarizar datos de asistencia humanitaria
Ejecutar con: python manage.py limpiar_datos
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from dashboard.models import AsistenciaHumanitaria
import pandas as pd
from datetime import datetime
from dashboard.utils.data_cleaner import DataCleaner # Importar DataCleaner

class Command(BaseCommand):
    help = 'Limpia y estandariza los datos de asistencia humanitaria'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta sin guardar cambios (solo muestra lo que haría)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada del proceso',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpieza de datos...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️ Modo DRY-RUN: No se guardarán cambios')
            )
        
        # Inicializar el limpiador de datos
        cleaner = DataCleaner()
        
        # Obtener todos los registros
        registros = AsistenciaHumanitaria.objects.all()
        total_registros = registros.count()
        
        self.stdout.write(f"📊 Total de registros a procesar: {total_registros}")
        
        # Convertir a DataFrame para facilitar la limpieza
        data = []
        for registro in registros:
            data.append({
                'id': registro.id,
                'fecha': registro.fecha,
                'departamento': registro.departamento,
                'distrito': registro.distrito,
                'localidad': registro.localidad,
                'evento': registro.evento,
                'kit_b': registro.kit_b,
                'kit_a': registro.kit_a,
                'chapa_fibrocemento': registro.chapa_fibrocemento,
                'chapa_zinc': registro.chapa_zinc,
                'colchones': registro.colchones,
                'frazadas': registro.frazadas,
                'terciadas': registro.terciadas,
                'puntales': registro.puntales,
                'carpas_plasticas': registro.carpas_plasticas,
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            self.stdout.write(
                self.style.ERROR('❌ No hay datos para procesar')
            )
            return
        
        # 1. LIMPIEZA DE FECHAS
        self.stdout.write("📅 Procesando fechas...")
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['AÑO'] = df['fecha'].dt.year
        df['MES'] = df['fecha'].dt.month
        df['DIA_SEMANA'] = df['fecha'].dt.day_name()
        
        # 2. LIMPIEZA DE VALORES NULOS EN AYUDAS
        self.stdout.write("🔢 Limpiando valores numéricos...")
        for col in cleaner.aid_fields:
            df[col] = df[col].apply(cleaner.limpiar_numero)
        
        # 3. LIMPIEZA DE DEPARTAMENTOS
        self.stdout.write("🗺️ Estandarizando departamentos...")
        df['departamento'] = df['departamento'].apply(cleaner.limpiar_departamento)
        
        # 4. LIMPIEZA DE EVENTOS
        self.stdout.write("⚡ Estandarizando eventos...")
        df['evento'] = df['evento'].apply(cleaner.limpiar_evento)
        
        # Post-procesamiento de eventos (usando la función del cleaner)
        df['evento'] = df.apply(cleaner.post_process_eventos_with_aids, axis=1)

        # Eliminar registros SIN EVENTO que no tienen ayudas (opcional para el comando)
        cond_sin_evento = df['evento'].str.upper().str.strip().eq('SIN EVENTO')
        registros_a_eliminar = df[cond_sin_evento & (df[cleaner.aid_fields].sum(axis=1) == 0)]
        if not dry_run and not registros_a_eliminar.empty:
            self.stdout.write(
                self.style.WARNING(f"🗑️ Eliminando {len(registros_a_eliminar)} registros 'SIN EVENTO' y sin ayudas...")
            )
            AsistenciaHumanitaria.objects.filter(id__in=registros_a_eliminar['id']).delete()
            df = df[~df['id'].isin(registros_a_eliminar['id'])] # Actualizar DataFrame local
            total_registros = df.shape[0] # Actualizar total de registros
            self.stdout.write(f"📊 Total de registros restantes: {total_registros}")

        # 5. LIMPIEZA DE LOCALIDADES Y DISTRITOS
        self.stdout.write("🏘️ Limpiando localidades y distritos...")
        df['localidad'] = df['localidad'].apply(cleaner.limpiar_texto)
        df['distrito'] = df['distrito'].apply(cleaner.limpiar_texto)
        
        # 6. MOSTRAR ESTADÍSTICAS DE LIMPIEZA
        if verbose:
            self.stdout.write("\n📊 ESTADÍSTICAS DE LIMPIEZA:")
            self.stdout.write(f"Departamentos únicos: {df['departamento'].nunique()}")
            self.stdout.write(f"Eventos únicos: {df['evento'].nunique()}")
            self.stdout.write(f"Registros con fechas válidas: {df['fecha'].notna().sum()}")
            
            self.stdout.write("\n🗺️ DEPARTAMENTOS ENCONTRADOS:")
            for dept in sorted(df['departamento'].unique()):
                count = df[df['departamento'] == dept].shape[0]
                self.stdout.write(f"  • {dept}: {count} registros")
            
            self.stdout.write("\n⚡ EVENTOS ENCONTRADOS:")
            for evento in sorted(df['evento'].unique()):
                count = df[df['evento'] == evento].shape[0]
                self.stdout.write(f"  • {evento}: {count} registros")
        
        # 7. GUARDAR CAMBIOS EN LA BASE DE DATOS
        if not dry_run:
            self.stdout.write("💾 Guardando cambios en la base de datos...")
            
            with transaction.atomic():
                registros_actualizados = 0
                
                for index, row in df.iterrows():
                    try:
                        # Solo actualizamos si el registro no fue eliminado
                        if row['id'] in AsistenciaHumanitaria.objects.values_list('id', flat=True):
                            registro = AsistenciaHumanitaria.objects.get(id=row['id'])
                            
                            # Actualizar campos
                            registro.departamento = row['departamento']
                            registro.distrito = row['distrito']
                            registro.localidad = row['localidad']
                            registro.evento = row['evento']
                            for field in cleaner.aid_fields:
                                setattr(registro, field, int(row[field]))
                            
                            registro.save()
                            registros_actualizados += 1
                            
                            if registros_actualizados % 100 == 0:
                                self.stdout.write(f"  Procesados: {registros_actualizados}/{total_registros}")
                        
                    except AsistenciaHumanitaria.DoesNotExist:
                        # Si el registro fue eliminado, simplemente lo saltamos
                        pass
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error procesando registro {row['id']}: {e}")
                        )
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Limpieza completada: {registros_actualizados} registros actualizados")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ Modo DRY-RUN: No se guardaron cambios")
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Proceso de limpieza finalizado')
        )
