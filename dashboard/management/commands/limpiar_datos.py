"""
Comando Django para limpiar y estandarizar datos de asistencia humanitaria
Ejecutar con: python manage.py limpiar_datos
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from dashboard.models import AsistenciaHumanitaria
import pandas as pd
from datetime import datetime

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
        dry_run = options['dry-run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpieza de datos...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️ Modo DRY-RUN: No se guardarán cambios')
            )
        
        # Obtener todos los registros
        registros = AsistenciaHumanitaria.objects.all()
        total_registros = registros.count()
        
        self.stdout.write(f"📊 Total de registros a procesar: {total_registros}")
        
        # Convertir a DataFrame para facilitar la limpieza
        data = []
        for registro in registros:
            data.append({
                'id': registro.id,
                'FECHA': registro.fecha,
                'DEPARTAMENTO': registro.departamento,
                'DISTRITO': registro.distrito,
                'LOCALIDAD': registro.localidad,
                'EVENTO': registro.evento,
                'KIT_B': registro.kit_b,
                'KIT_A': registro.kit_a,
                'CHAPA_FIBROCEMENTO': registro.chapa_fibrocemento,
                'CHAPA_ZINC': registro.chapa_zinc,
                'COLCHONES': registro.colchones,
                'FRAZADAS': registro.frazadas,
                'TERCIADAS': registro.terciadas,
                'PUNTALES': registro.puntales,
                'CARPAS_PLASTICAS': registro.carpas_plasticas,
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            self.stdout.write(
                self.style.ERROR('❌ No hay datos para procesar')
            )
            return
        
        # 1. LIMPIEZA DE FECHAS
        self.stdout.write("📅 Procesando fechas...")
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
        df['AÑO'] = df['FECHA'].dt.year
        df['MES'] = df['FECHA'].dt.month
        df['DIA_SEMANA'] = df['FECHA'].dt.day_name()
        
        # 2. LIMPIEZA DE VALORES NULOS EN AYUDAS
        self.stdout.write("🔢 Limpiando valores numéricos...")
        ayudas_cols = ['KIT_B', 'KIT_A', 'CHAPA_FIBROCEMENTO', 'CHAPA_ZINC',
                       'COLCHONES', 'FRAZADAS', 'TERCIADAS', 'PUNTALES', 'CARPAS_PLASTICAS']
        
        # Convertir a numérico y reemplazar NaN por 0
        for col in ayudas_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 3. LIMPIEZA DE DEPARTAMENTOS
        self.stdout.write("🗺️ Estandarizando departamentos...")
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str).str.strip().str.upper()
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].replace(['NAN', 'NONE', ''], 'SIN_DEPARTAMENTO')
        
        # Diccionario de estandarización de departamentos
        estandarizacion_dept = {
            'ÑEEMBUCU': 'ÑEEMBUCÚ', 'ÑEEMBUCÙ': 'ÑEEMBUCÚ', 'ÑEMBUCU': 'ÑEEMBUCÚ',
            'ALTO PARANA': 'ALTO PARANÁ', 'ALTO PARANÀ': 'ALTO PARANÁ', 'ALTO PNÀ': 'ALTO PARANÁ', 'ALTO PNÁ': 'ALTO PARANÁ', 'ALTO PY': 'ALTO PARANÁ',
            'BOQUERÒN': 'BOQUERON', 'BOQUERÓN': 'BOQUERON',
            'CAAGUAZU': 'CAAGUAZÚ', 'CAAGUAZÙ': 'CAAGUAZÚ', 'CAAG-CANIND': 'CAAGUAZÚ', 'CAAG/CANIN': 'CAAGUAZÚ', 'CAAG/CANIND.': 'CAAGUAZÚ', 'CAAGUAZU- ALTO PARANA': 'CAAGUAZÚ', 'CAAGUAZU/MISIONES': 'CAAGUAZÚ', 'CAAGUAZU - Canindeyu': 'CAAGUAZÚ', 'CAAGUAZU y Canindeyu': 'CAAGUAZÚ', 'CAAGUAZU, Canindeyu y San Pedro': 'CAAGUAZÚ', 'CAAGUAZU, San Pedro y Canindeyu': 'CAAGUAZÚ', 'CAAGUAZU-Guaira y San Pedro': 'CAAGUAZÚ',
            'CAAZAPA': 'CAAZAPÁ', 'CAAZAPÀ': 'CAAZAPÁ', 'CAAZAPA - Guaira': 'CAAZAPÁ',
            'CANINDEYU': 'CANINDEYÚ', 'CANINDEYÙ': 'CANINDEYÚ', 'Canindeyu - Caaguazu': 'CANINDEYÚ', 'Canindeyu y San Pedro': 'CANINDEYÚ',
            'CENT/CORDILL': 'CENTRAL', 'CENTR-CORD': 'CENTRAL', 'CENTRAL-CORDILLERA': 'CENTRAL', 'CENTRAL/CAP': 'CENTRAL', 'CENTRAL/CAPITAL': 'CENTRAL', 'CENTRAL/COR': 'CENTRAL', 'CENTRAL/CORD': 'CENTRAL', 'CENTRAL/CORD.': 'CENTRAL', 'CENTRAL/CORDILLER': 'CENTRAL', 'CENTRAL/CORDILLERA': 'CENTRAL', 'CENTRAL/PARAG.': 'CENTRAL', 'central': 'CENTRAL',
            'CONCEPCION': 'CONCEPCIÓN', 'CONCEPCIÒN': 'CONCEPCIÓN',
            'COORDILLERA': 'CORDILLERA', 'CORD./CENTRAL': 'CORDILLERA', 'CORD/S.PEDRO': 'CORDILLERA', 'CORDILLERA ARROYOS Y EST.': 'CORDILLERA', 'CORDILLERA Y SAN PEDRO': 'CORDILLERA', 'CORDILLERACAACUPÈ': 'CORDILLERA',
            'GUAIRA': 'GUAIRÁ', 'GUAIRÀ': 'GUAIRÁ', 'GUIARA': 'GUAIRÁ', 'Guaira - Caazapa': 'GUAIRÁ',
            'ITAPUA': 'ITAPÚA', 'ITAPUA- CAAGUAZU': 'ITAPÚA', 'ITAPÙA': 'ITAPÚA',
            'MISIONES YABEBYRY': 'MISIONES',
            'PARAGUARI': 'PARAGUARÍ', 'PARAGUARI PARAGUARI': 'PARAGUARÍ', 'PARAGUARÌ': 'PARAGUARÍ', 'Paraguari - Guaira': 'PARAGUARÍ',
            'PDTE HAYES': 'PDTE. HAYES', 'PDTE HAYES S.PIRI-4 DE MAYO': 'PDTE. HAYES', 'PDTE HYES': 'PDTE. HAYES', 'PTE HAYES': 'PDTE. HAYES', 'PTE. HAYES': 'PDTE. HAYES', 'Pdte Hayes': 'PDTE. HAYES', 'Pdte. Hayes': 'PDTE. HAYES', 'PDTE.HAYES': 'PDTE. HAYES',
            'S.PEDRO/CAN.': 'SAN PEDRO', 'SAN PEDRO-CAAGUAZU': 'SAN PEDRO', 'SAN PEDRO/ AMAMBAY': 'SAN PEDRO', 'SAN PEDRO/ CANINDEYU': 'SAN PEDRO', 'San Pedro - Canindeyu': 'SAN PEDRO',
            'VARIOS DEP.': 'VARIOS DEPARTAMENTOS', 'VARIOS DPTOS.': 'VARIOS DEPARTAMENTOS', 'VARIOS DPTS.': 'VARIOS DEPARTAMENTOS', 'varios': 'VARIOS DEPARTAMENTOS', 'REGION ORIENTAL/ OCCIDENTAL': 'VARIOS DEPARTAMENTOS',
            'ASOC MUSICO': 'VARIOS DEPARTAMENTOS', 'CNEL OVIEDO': 'CORONEL OVIEDO', 'ITA': 'ITÁ', 'ITAUGUA': 'ITAUGUÁ', 'VILLARICA': 'VILLARRICA', 'ASUNCION': 'ASUNCIÓN', 'CAACUPÈ': 'CAACUPÉ'
        }
        
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].replace(estandarizacion_dept)
        
        # 4. LIMPIEZA DE EVENTOS
        self.stdout.write("⚡ Estandarizando eventos...")
        df['EVENTO'] = df['EVENTO'].astype(str).str.strip().str.upper()
        df['EVENTO'] = df['EVENTO'].replace(['NAN', 'NONE', ''], 'SIN_EVENTO')
        
        # Extraer solo la parte antes del guión (-)
        df['EVENTO'] = df['EVENTO'].str.split('-').str[0].str.strip()
        
        # Diccionario de estandarización de eventos
        estandarizacion_eventos = {
            'ALB.COVID': 'COVID', 'ALBER.COVID': 'COVID', 'ALBERG.COVID': 'COVID', 'COVI 19 OLL.': 'COVID', 'COVID 19': 'COVID', 'COVI': 'COVID',
            'APOY INST': 'APOYO INSTITUCIONAL', 'APOYO INST.': 'APOYO INSTITUCIONAL', 'APOYO INSTIT.': 'APOYO INSTITUCIONAL', 'APOYO INT.': 'APOYO INSTITUCIONAL', 'APOYO INTITUCIONAL': 'APOYO INSTITUCIONAL', 'APOYO INSITUCIONAL': 'APOYO INSTITUCIONAL', 'APOY. INST.': 'APOYO INSTITUCIONAL', 'APOY.INST,': 'APOYO INSTITUCIONAL', 'APOY.INST.COVID 19': 'COVID', 'APOY.INSTITUC.': 'APOYO INSTITUCIONAL', 'APOY.INSTITUCIONAL': 'APOYO INSTITUCIONAL', 'APAYO INSTITUCIONAL': 'APOYO INSTITUCIONAL', 'APOYO INSRITUCIOMAL': 'APOYO INSTITUCIONAL', 'APOYO INSTITUCIOINAL': 'APOYO INSTITUCIONAL', 'APOYO INSTITUCIONAAL': 'APOYO INSTITUCIONAL', 'APOYO INSTIYUCIONAL': 'APOYO INSTITUCIONAL', 'APYO INSTITUCIONAL': 'APOYO INSTITUCIONAL', 'APOYO INSTITUCIONAL INDI': 'INDI', 'APOYO INSTITUCIONAL COVID': 'COVID',
            'APOY.LOG': 'APOYO LOGISTICO', 'APOY LOG': 'APOYO LOGISTICO', 'APOYO LOG.': 'APOYO LOGISTICO', 'APOYO LOGISTICO "TEMPORAL"': 'TEMPORAL', 'APOYO LOGISTICO INDI': 'INDI',
            'ASIST.': 'ASISTENCIA', 'ASISTANCIA': 'ASISTENCIA', 'ASISTECIA': 'ASISTENCIA', 'ASIASTENCIA': 'ASISTENCIA', 'ASISTENCIAS': 'ASISTENCIA', 'AS.DE LA CORTE': 'ASISTENCIA INSTITUCIONAL', 'ASISTENCIA DE LA CORTE': 'ASISTENCIA INSTITUCIONAL', 'ASISTENCIA SECRETARIA DE REPATRIADOS': 'ASISTENCIA INSTITUCIONAL', 'ASISTENCIA TEMPORAL': 'ASISTENCIA TEMPORAL', 'ASISTENCIA COMUNIDAD INDIGENA': 'INDI', 'ASISTENCIA A COMUNIDADES INDIGENAS': 'INDI',
            'INC.FORESTAL': 'INCENDIO', 'INCCENDIO': 'INCENDIO', 'INCEND': 'INCENDIO', 'INCEND. DOMIC.': 'INCENDIO', 'INCENDIO DOMICILIARIO': 'INCENDIO', 'DERRUMBE': 'DERRUMBE',
            'INUNDAC.': 'INUNDACION', 'INUNDAIÓN S.': 'INUNDACION', 'INUNDACION SUBITA': 'INUNDACION', 'INUNDACION " DECLARACION DE EMERGENCIA"': 'INUNDACION', 'LNUNDACION': 'INUNDACION', 'SEQ. E INUND.': 'INUNDACION', 'SEQ./INUND.': 'INUNDACION',
            'SEQUIA-INUND.': 'SEQUIA',
            'OLLA P': 'OLLA POPULAR', 'OLLA P.': 'OLLA POPULAR', 'OLLA POP': 'OLLA POPULAR', 'OLLA POP.': 'OLLA POPULAR', 'OLLA POPILAR': 'OLLA POPULAR', 'OLLA POPOLAR': 'OLLA POPULAR', 'OLLA POPUL': 'OLLA POPULAR', 'OLLAP.': 'OLLA POPULAR', 'OLLA POPULAR COVID': 'OLLA POPULAR COVID',
            'OP INVIERNO': 'OPERATIVO INVIERNO', 'OP. INVIERNO': 'OPERATIVO INVIERNO', 'OP. ÑEÑUA': 'OPERATIVO ÑEÑUA', 'OP.INVIERNO': 'OPERATIVO INVIERNO', 'OP.ÑEÑUA': 'OPERATIVO ÑEÑUA', 'OPER. ÑEÑUA': 'OPERATIVO ÑEÑUA', 'OPER.INVIERN': 'OPERATIVO INVIERNO', 'OPER.INVIERNO': 'OPERATIVO INVIERNO', 'OPERATIVO INV.': 'OPERATIVO INVIERNO', 'OPERATIVO CAACUPE': 'OPERATIVO ESPECIAL', 'OPERATIVO RETORNO': 'OPERATIVO ESPECIAL',
            'PREP.': 'PREPOSICIONAMIENTO', 'PREPOS': 'PREPOSICIONAMIENTO', 'PREPOS.': 'PREPOSICIONAMIENTO', 'PREPOSIC.': 'PREPOSICIONAMIENTO', 'PREPOSICION.': 'PREPOSICIONAMIENTO', 'PRE POSICIONAMIENTO': 'PREPOSICIONAMIENTO', 'P/ STOCK DEL COE': 'PREPOSICIONAMIENTO',
            'REP.DE MATERIAL': 'REPOSICION DE MATERIALES', 'REPOSIC.MATER': 'REPOSICION DE MATERIALES', 'REPOSIC.MATER.': 'REPOSICION DE MATERIALES', 'PROVISION DE MATERIALES': 'REPOSICION DE MATERIALES', 'REABASTECIMIENTO': 'REPOSICION DE MATERIALES',
            'REPARACION': 'REPARACION', 'REPARACION DE BAÑADERA': 'REPARACION', 'REPARACION DE OBRAS': 'REPARACION',
            'INDERT': 'EVENTO INSTITUCIONAL', 'INDI MBYA GUARANI': 'INDI', 'MUNICIPALIDAD': 'EVENTO INSTITUCIONAL', 'NIÑEZ': 'ASISTENCIA', 'VAC.ARATIRI': 'COVID', 'VACUNATORIO SND': 'COVID', 'DGRR 027/22': 'EVENTO INSTITUCIONAL', 'DGRR 028/22': 'EVENTO INSTITUCIONAL',
            'DONAC': 'DONACION', 'DONAC.': 'DONACION', 'DONACIÒN': 'DONACION', 'EDAN': 'EVALUACION DE DAÑOS', 'EVALUACION DE DAÑOS': 'EVALUACION DE DAÑOS', 'MINGA': 'TRABAJO COMUNITARIO', 'INERAM(MINGA)': 'TRABAJO COMUNITARIO', 'EVENTO CLIMATICO TEMPORAL': 'TEMPORAL', 'TEMPORAL CENTRAL': 'TEMPORAL', 'ÑANGARECO': 'AYUDA SOLIDARIA', 'ÑANGAREKO': 'AYUDA SOLIDARIA', 'SIN_EVENTO': 'SIN EVENTO', 'DEVOLVIO': 'DEVOLUCION', 'PRESTAMO': 'PRESTAMO', 'REFUGIO SEN': 'ALBERGUE', 'TRASLADO INTERNO': 'TRASLADO', 'ASISTENCIA COMUNITARIA':'ASISTENCIA', 'ASISTENCIA SOCIAL':'ASISTENCIA'
        }
        
        df['EVENTO'] = df['EVENTO'].replace(estandarizacion_eventos)
        
        # Lógica adicional para 'SIN EVENTO'
        cond_sin_evento = df['EVENTO'].str.upper().str.strip().eq('SIN EVENTO')
        
        df.loc[cond_sin_evento & (df['CHAPA_FIBROCEMENTO'] > 0), 'EVENTO'] = 'INUNDACION'
        df.loc[cond_sin_evento & (df['CHAPA_ZINC'] > 0), 'EVENTO'] = 'TEMPORAL'
        df.loc[cond_sin_evento & (df[ayudas_cols].sum(axis=1) > 0), 'EVENTO'] = 'ASISTENCIA'
        
        # Eliminar registros SIN EVENTO que no tienen ayudas (opcional para el comando)
        registros_a_eliminar = df[cond_sin_evento & (df[ayudas_cols].sum(axis=1) == 0)]
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
        df['LOCALIDAD'] = df['LOCALIDAD'].astype(str).str.strip().str.title()
        df['DISTRITO'] = df['DISTRITO'].astype(str).str.strip().str.title()
        
        # Reemplazar valores vacíos
        df['LOCALIDAD'] = df['LOCALIDAD'].replace(['Nan', 'None', ''], 'Sin Especificar')
        df['DISTRITO'] = df['DISTRITO'].replace(['Nan', 'None', ''], 'Sin Especificar')
        
        # 6. MOSTRAR ESTADÍSTICAS DE LIMPIEZA
        if verbose:
            self.stdout.write("\n📊 ESTADÍSTICAS DE LIMPIEZA:")
            self.stdout.write(f"Departamentos únicos: {df['DEPARTAMENTO'].nunique()}")
            self.stdout.write(f"Eventos únicos: {df['EVENTO'].nunique()}")
            self.stdout.write(f"Registros con fechas válidas: {df['FECHA'].notna().sum()}")
            
            self.stdout.write("\n🗺️ DEPARTAMENTOS ENCONTRADOS:")
            for dept in sorted(df['DEPARTAMENTO'].unique()):
                count = df[df['DEPARTAMENTO'] == dept].shape[0]
                self.stdout.write(f"  • {dept}: {count} registros")
            
            self.stdout.write("\n⚡ EVENTOS ENCONTRADOS:")
            for evento in sorted(df['EVENTO'].unique()):
                count = df[df['EVENTO'] == evento].shape[0]
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
                            registro.departamento = row['DEPARTAMENTO']
                            registro.distrito = row['DISTRITO']
                            registro.localidad = row['LOCALIDAD']
                            registro.evento = row['EVENTO']
                            registro.kit_b = int(row['KIT_B'])
                            registro.kit_a = int(row['KIT_A'])
                            registro.chapa_fibrocemento = int(row['CHAPA_FIBROCEMENTO'])
                            registro.chapa_zinc = int(row['CHAPA_ZINC'])
                            registro.colchones = int(row['COLCHONES'])
                            registro.frazadas = int(row['FRAZADAS'])
                            registro.terciadas = int(row['TERCIADAS'])
                            registro.puntales = int(row['PUNTALES'])
                            registro.carpas_plasticas = int(row['CARPAS_PLASTICAS'])
                            
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
