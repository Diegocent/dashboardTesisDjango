import pandas as pd # type: ignore
import numpy as np # type: ignore
import re
from datetime import datetime

class DataCleaner:
    def __init__(self):
        self.aid_fields = [
            'kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc',
            'colchones', 'frazadas', 'terciadas', 'puntales', 'carpas_plasticas'
        ]
        self.evento_patterns = [
            (r'ASISTENCIAS.*INUNDACION', 'INUNDACION'),
            (r'ASISTENCIAS.*SEQUIA', 'SEQUIA'),
            (r'COORDINACION.*REHABILITACION', 'INUNDACION'),
            (r'TRABAJOS.*FAMILIAS AFECTADAS', 'INUNDACION'),
            (r'EVENTO CLIMATICO', 'TEMPORAL'),
            (r'OPERATIVO', 'OPERATIVO JAHO\'I'),
        ]

        # Mapeo de distritos a sus departamentos correspondientes
        self.distrito_a_departamento = {
            'ASUNCIÓN': 'CAPITAL',
            'LIMPIO': 'CENTRAL',
            'MARIANO ROQUE ALONSO': 'CENTRAL',
            'ÑEMBY': 'CENTRAL',
            'SAN LORENZO': 'CENTRAL',
            'LAMBARÉ': 'CENTRAL',
            'FERNANDO DE LA MORA': 'CENTRAL',
            'VILLA ELISA': 'CENTRAL',
            'SAN ANTONIO': 'CENTRAL',
            'LUQUE': 'CENTRAL',
            'CAPIATÁ': 'CENTRAL',
            'ITAUGUÁ': 'CENTRAL',
            'J. AUGUSTO SALDÍVAR': 'CENTRAL',
            'VILLETA': 'CENTRAL',
            'GUARAMBARÉ': 'CENTRAL',
            'YPACARAÍ': 'CENTRAL',
            'YPANÉ': 'CENTRAL',
            'ITÁ': 'CENTRAL',
            'SANTA ROSA': 'MISIONES',
            'SAN JUAN BAUTISTA': 'MISIONES',
            'VILLARRICA': 'GUAIRÁ',
            'CORONEL OVIEDO': 'CAAGUAZÚ',
            'CAACUPÉ': 'CORDILLERA',
            'VILLARICA': 'GUAIRÁ',
            'ITA': 'CENTRAL',
        }

        # Diccionario de estandarización de departamentos
        self.estandarizacion_dept = {
            # Ñeembucú
            'ÑEEMBUCU': 'ÑEEMBUCÚ',
            'ÑEEMBUCÙ': 'ÑEEMBUCÚ',
            'ÑEMBUCU': 'ÑEEMBUCÚ',
            'ÑEEMBUCU': 'ÑEEMBUCÚ',
            'Ñeembucu': 'ÑEEMBUCÚ',

            # Alto Paraná
            'ALTO PARANA': 'ALTO PARANÁ',
            'ALTO PARANÀ': 'ALTO PARANÁ',
            'ALTO PNÀ': 'ALTO PARANÁ',
            'ALTO PNÁ': 'ALTO PARANÁ',
            'ALTO PY': 'ALTO PARANÁ',
            'Alto Parana': 'ALTO PARANÁ',

            # Boquerón
            'BOQUERÒN': 'BOQUERON',
            'BOQUERÓN': 'BOQUERON',
            'Boqueron': 'BOQUERON',

            # Caaguazú
            'CAAGUAZU': 'CAAGUAZÚ',
            'CAAGUAZÙ': 'CAAGUAZÚ',
            'Caaguazu': 'CAAGUAZÚ',
            'Caaguazú': 'CAAGUAZÚ',
            'CAAG-CANIND': 'CAAGUAZÚ',
            'CAAG/CANIN': 'CAAGUAZÚ',
            'CAAG/CANIND.': 'CAAGUAZÚ',
            'CAAGUAZU- ALTO PARANA': 'CAAGUAZÚ',
            'CAAGUAZU/MISIONES': 'CAAGUAZÚ',
            'Caaguazu - Canindeyu': 'CAAGUAZÚ',
            'Caaguazu y Canindeyu': 'CAAGUAZÚ',
            'Caaguazu, Canindeyu y San Pedro': 'CAAGUAZÚ',
            'Caaguazu, San Pedro y Canindeyu': 'CAAGUAZÚ',
            'Caaguazu-Guaira y San Pedro': 'CAAGUAZÚ',
            'CAAGUAZU-GUAIRA': 'CAAGUAZÚ',
            'CAAGUAZU - CANINDEYU': 'CAAGUAZÚ',
            'CAAGUAZU Y CANINDEYU': 'CAAGUAZÚ',
            'CAAGUAZU, CANINDEYU Y SAN PEDRO': 'CAAGUAZÚ',
            'CAAGUAZU, SAN PEDRO Y CANINDEYU': 'CAAGUAZÚ',
            'CAAGUAZU-GUAIRA Y SAN PEDRO': 'CAAGUAZÚ',


            # Caazapá
            'CAAZAPA': 'CAAZAPÁ',
            'CAAZAPÀ': 'CAAZAPÁ',
            'Caazapa': 'CAAZAPÁ',
            'Caazapa - Guaira': 'CAAZAPÁ',
            'CAAZAPA - GUAIRA': 'CAAZAPÁ',

            # Canindeyú
            'CANINDEYU': 'CANINDEYÚ',
            'CANINDEYÙ': 'CANINDEYÚ',
            'Canindeyu': 'CANINDEYÚ',
            'Canindeyu - Caaguazu': 'CANINDEYÚ',
            'Canindeyu y San Pedro': 'CANINDEYÚ',
            'CANINDEYU - CAAGUAZU': 'CANINDEYÚ',
            'CANINDEYU Y SAN PEDRO': 'CANINDEYÚ',

            # Central
            'CENT/CORDILL': 'CENTRAL',
            'CENTR-CORD': 'CENTRAL',
            'CENTRAL': 'CENTRAL',
            'CENTRAL-CORDILLERA': 'CENTRAL',
            'CENTRAL/CAP': 'CENTRAL',
            'CENTRAL/CAPITAL': 'CENTRAL',
            'CENTRAL/COR': 'CENTRAL',
            'CENTRAL/CORD': 'CENTRAL',
            'CENTRAL/CORD.': 'CENTRAL',
            'CENTRAL/CORDILLER': 'CENTRAL',
            'CENTRAL/CORDILLERA': 'CENTRAL',
            'CENTRAL/PARAG.': 'CENTRAL',
            'central': 'CENTRAL',

            # Concepción
            'CONCEPCION': 'CONCEPCIÓN',
            'CONCEPCIÒN': 'CONCEPCIÓN',
            'Concepcion': 'CONCEPCIÓN',

            # Cordillera
            'COORDILLERA': 'CORDILLERA',
            'CORD./CENTRAL': 'CORDILLERA',
            'CORD/S.PEDRO': 'CORDILLERA',
            'CORDILLERA': 'CORDILLERA',
            'CORDILLERA ARROYOS Y EST.': 'CORDILLERA',
            'CORDILLERA Y SAN PEDRO': 'CORDILLERA',
            'CORDILLERACAACUPÈ': 'CORDILLERA',
            'Cordillera': 'CORDILLERA',
            'CORDILLERA ARROYOS': 'CORDILLERA',

            # Guairá
            'GUAIRA': 'GUAIRÁ',
            'GUAIRÀ': 'GUAIRÁ',
            'GUIARA': 'GUAIRÁ',
            'Guaira': 'GUAIRÁ',
            'Guaira - Caazapa': 'GUAIRÁ',
            'GUAIRA - CAAZAPA': 'GUAIRÁ',

            # Itapúa
            'ITAPUA': 'ITAPÚA',
            'ITAPUA- CAAGUAZU': 'ITAPÚA',
            'ITAPÙA': 'ITAPÚA',
            'Itapua': 'ITAPÚA',

            # Misiones
            'MISIONES YABEBYRY': 'MISIONES',
            'Misiones': 'MISIONES',

            # Paraguarí
            'PARAGUARI': 'PARAGUARÍ',
            'PARAGUARI PARAGUARI': 'PARAGUARÍ',
            'PARAGUARÌ': 'PARAGUARÍ',
            'Paraguari': 'PARAGUARÍ',
            'Paraguari -  Guaira': 'PARAGUARÍ',
            'PARAGUARI - GUAIRA': 'PARAGUARÍ',

            # Presidente Hayes
            'PDTE HAYES': 'PDTE. HAYES',
            'PDTE HAYES S.PIRI-4 DE MAYO': 'PDTE. HAYES',
            'PDTE HYES': 'PDTE. HAYES',
            'PDTE. HAYES': 'PDTE. HAYES',
            'PTE HAYES': 'PDTE. HAYES',
            'PTE. HAYES': 'PDTE. HAYES',
            'Pdte Hayes': 'PDTE. HAYES',
            'Pdte. Hayes': 'PDTE. HAYES',
            'PDTE.HAYES': 'PDTE. HAYES',

            # San Pedro
            'S.PEDRO/CAN.': 'SAN PEDRO',
            'SAN PEDRO': 'SAN PEDRO',
            'SAN PEDRO-CAAGUAZU': 'SAN PEDRO',
            'SAN PEDRO/ AMAMBAY': 'SAN PEDRO',
            'SAN PEDRO/ CANINDEYU': 'SAN PEDRO',
            'San Pedro': 'SAN PEDRO',
            'San Pedro - Canindeyu': 'SAN PEDRO',
            'SAN PEDRO - CANINDEYU': 'SAN PEDRO',

            # Varios departamentos
            'VARIOS DEP.': 'VARIOS DEPARTAMENTOS',
            'VARIOS DPTOS.': 'VARIOS DEPARTAMENTOS',
            'VARIOS DPTS.': 'VARIOS DEPARTAMENTOS',
            'varios': 'VARIOS DEPARTAMENTOS',
            'REGION ORIENTAL/ OCCIDENTAL': 'VARIOS DEPARTAMENTOS',
            'VARIOS': 'VARIOS DEPARTAMENTOS',

            # Otros
            'ASOC MUSICO': 'VARIOS DEPARTAMENTOS',
            'CNEL OVIEDO': 'CORONEL OVIEDO',  # Coronel Oviedo pertenece a Caaguazú
            'ITA': 'ITA',  # Itá pertenece a Central
            'ITAUGUA': 'ITAUGUÁ',  # Itauguá pertenece a Central
            'VILLARICA': 'VILLARICA',  # Villarrica pertenece a Guairá
            'ASUNCION': 'ASUNCIÓN',
            'ASUNCIÓN': 'ASUNCIÓN',
            'CAACUPÈ': 'CAACUPÉ',  # Caacupé pertenece a Cordillera
            'CAACUPÉ': 'CAACUPÉ',
            
            # Departamentos estándar para completar
            'ALTO PARAGUAY': 'ALTO PARAGUAY',
            'AMAMBAY': 'AMAMBAY',
            'CAPITAL': 'CAPITAL'
        }

        # Diccionario de estandarización de eventos actualizado según requerimientos
        self.estandarizacion_eventos = {
            # COVID y variantes
            'ALB.COVID': 'COVID', 'ALBER.COVID': 'COVID', 'ALBERG.COVID': 'COVID',
            'COVI 19 OLL.': 'COVID', 'COVID 19': 'COVID', 'COVI': 'COVID',
            'VAC.ARATIRI': 'COVID', 'VACUNATORIO SND': 'COVID',
            'APOY.INST.COVID 19': 'COVID', 'APOYO INSTITUCIONAL COVID': 'COVID',
            'ÑANGARECO': 'COVID', 'ÑANGAREKO': 'COVID',

            # INCENDIO
            'INC.FORESTAL': 'INCENDIO', 'INCCENDIO': 'INCENDIO', 'INCEND': 'INCENDIO',
            'INCEND. DOMIC.': 'INCENDIO', 'INCENDIO DOMICILIARIO': 'INCENDIO',
            'DERRUMBE': 'INCENDIO', 'INCENDIO FORESTAL': 'INCENDIO',

            # TEMPORAL
            'EVENTO CLIMATICO': 'TEMPORAL', 'TEMPORAL CENTRAL': 'TEMPORAL',
            'EVENTO CLIMATICO TEMPORAL': 'TEMPORAL', 'MUNICIPALIDAD': 'TEMPORAL',

            # SEQUIA
            'SEQ. E INUND.': 'SEQUIA', 'SEQ./INUND.': 'SEQUIA', 'SEQUIA-INUND.': 'SEQUIA',

            # EXTREMA VULNERABILIDAD
            'COMISION VECINAL': 'EXTREMA VULNERABILIDAD',
            'AYUDA SOLIDARIA': 'EXTREMA VULNERABILIDAD',

            # C.I.D.H.
            'C I D H': 'C.I.D.H.',
            'C.H.D.H': 'C.I.D.H.',
            'C.I.D.H': 'C.I.D.H.',
            'C.I.D.H.': 'C.I.D.H.',
            'C.ID.H': 'C.I.D.H.',
            'CIDH': 'C.I.D.H.',

            # OPERATIVO JAHO'I
            'OPERATIVO ÑEÑUA': "OPERATIVO JAHO'I",
            'OPERATIVO ESPECIAL': "OPERATIVO JAHO'I",
            'OP INVIERNO': "OPERATIVO JAHO'I", 'OP. INVIERNO': "OPERATIVO JAHO'I",
            'OP. ÑEÑUA': "OPERATIVO JAHO'I", 'OP.INVIERNO': "OPERATIVO JAHO'I",
            'OP.ÑEÑUA': "OPERATIVO JAHO'I", 'OPER. ÑEÑUA': "OPERATIVO JAHO'I",
            'OPER.INVIERN': "OPERATIVO JAHO'I", 'OPER.INVIERNO': "OPERATIVO JAHO'I",
            'OPERATIVO INV.': "OPERATIVO JAHO'I",

            # INUNDACION
            'INUNDAC.': 'INUNDACION', 'INUNDAIÓN S.': 'INUNDACION',
            'INUNDACION SUBITA': 'INUNDACION', 'INUNDACION " DECLARACION DE EMERGENCIA"': 'INUNDACION',
            'LNUNDACION': 'INUNDACION', 'INUNDACIÓN': 'INUNDACION',

            # OLLA POPULAR
            'OLLA P': 'OLLA POPULAR', 'OLLA P.': 'OLLA POPULAR', 'OLLA POP': 'OLLA POPULAR',
            'OLLA POP.': 'OLLA POPULAR', 'OLLA POPILAR': 'OLLA POPULAR',
            'OLLA POPOLAR': 'OLLA POPULAR', 'OLLA POPUL': 'OLLA POPULAR',
            'OLLAP.': 'OLLA POPULAR', 'OLLA POPULAR COVID': 'OLLA POPULAR',

            # OTROS
            'INERAM': 'OTROS', 'INERAM(MINGA)': 'OTROS', 'MINGA': 'OTROS',
            'INDERT': 'OTROS', 'INDI MBYA GUARANI': 'OTROS',
            'NIÑEZ': 'OTROS', 'DGRR 027/22': 'OTROS', 'DGRR 028/22': 'OTROS',
            'DONAC': 'OTROS', 'DONAC.': 'OTROS', 'DONACIÒN': 'OTROS',
            'EDAN': 'OTROS', 'EVALUACION DE DAÑOS': 'OTROS',
            'TRABAJO COMUNITARIO': 'OTROS', 'ASISTENCIA INSTITUCIONAL': 'OTROS',
            'APOYO LOGISTICO': 'OTROS', 'APOYO INSTITUCIONAL': 'OTROS',
            'APOY.LOG': 'OTROS', 'APOY LOG': 'OTROS',
            'APOYO LOG.': 'OTROS', 'OTROS "TEMPORAL"': 'OTROS',
            'APOYO LOGISTICO INDI': 'OTROS',

            # PREPOSICIONAMIENTO (se eliminarán después)
            'PREP.': 'PREPOSICIONAMIENTO', 'PREPOS': 'PREPOSICIONAMIENTO',
            'PREPOS.': 'PREPOSICIONAMIENTO', 'PREPOSIC.': 'PREPOSICIONAMIENTO',
            'PREPOSICION.': 'PREPOSICIONAMIENTO', 'PRE POSICIONAMIENTO': 'PREPOSICIONAMIENTO',
            'P/ STOCK DEL COE': 'PREPOSICIONAMIENTO', 'REP.DE MATERIAL': 'PREPOSICIONAMIENTO',
            'REPOSIC.MATER': 'PREPOSICIONAMIENTO', 'REPOSIC.MATER.': 'PREPOSICIONAMIENTO',
            'PROVISION DE MATERIALES': 'PREPOSICIONAMIENTO', 'REABASTECIMIENTO': 'PREPOSICIONAMIENTO',
            'REPARACION': 'PREPOSICIONAMIENTO', 'REPARACION DE BAÑADERA': 'PREPOSICIONAMIENTO',
            'REPARACION DE OBRAS': 'PREPOSICIONAMIENTO', 'PRESTAMO': 'PREPOSICIONAMIENTO',
            'REPOSICION': 'PREPOSICIONAMIENTO', 'REPOSICION DE MATERIALES': 'PREPOSICIONAMIENTO',
            'TRASLADO INTERNO': 'PREPOSICIONAMIENTO', 'PREPOSICIONAMIENTO': 'PREPOSICIONAMIENTO',

            # SIN EVENTO
            'SIN_EVENTO': 'SIN EVENTO', 'DEVOLVIO': 'SIN EVENTO', 'REFUGIO SEN': 'SIN EVENTO',
        }

    def limpiar_numero(self, value):
        """Intenta convertir un valor a entero, si falla retorna 0."""
        try:
            return int(float(value)) if value not in [None, '', np.nan] else 0
        except (ValueError, TypeError):
            return 0

    def limpiar_texto(self, text):
        """Limpia y estandariza cadenas de texto."""
        if pd.isna(text) or text is None or str(text).strip() == '':
            return 'SIN ESPECIFICAR'
        return str(text).strip().title()

    def limpiar_evento(self, evento_str):
        """Versión mejorada con manejo de patrones según nuevos requerimientos"""
        if pd.isna(evento_str) or evento_str is None or str(evento_str).strip() == '':
            return 'SIN EVENTO'
        
        evento_str = str(evento_str).strip().upper()
        
        # 1. Verificación exacta primero (más eficiente)
        if evento_str in self.estandarizacion_eventos:
            estandarizado = self.estandarizacion_eventos[evento_str]
            # Eliminamos cualquier cosa que sea preposicionamiento
            if estandarizado == 'PREPOSICIONAMIENTO':
                return None  # Indicador para eliminar el registro
            return estandarizado
        
        # 2. Búsqueda de patrones en textos largos
        for pattern, replacement in self.evento_patterns:
            if re.search(pattern, evento_str, re.IGNORECASE):
                return replacement
                
        # 3. Búsqueda de palabras clave simples
        keywords = {
            'INSTITUCIONAL': 'OTROS',
            'LOGISTICO': 'OTROS',
            'LOGÍSTICO': 'OTROS',
            'LOGISTICA': 'OTROS',
            'LOGÍSTICA': 'OTROS',
            'INUNDACION': 'INUNDACION',
            'SEQUIA': 'SEQUIA',
            'LLUVIA': 'INUNDACION',
            'TEMPORAL': 'TEMPORAL',
            'VIENTO': 'TEMPORAL',
            'INCENDIO': 'INCENDIO',
            'COVID': 'COVID',
            'JAHO\'I': "OPERATIVO JAHO'I",
            'ÑEÑUA': "OPERATIVO JAHO'I",
        }
        
        for kw, replacement in keywords.items():
            if kw in evento_str:
                return replacement
                
        # 4. Si no coincide con nada, devolver OTROS
        return 'SIN EVENTO'

    def post_process_eventos_with_aids(self, row):
        """Ajusta el evento basado en la presencia de ayudas según nuevos requerimientos."""
        evento = row['evento']
        
        # Si es preposicionamiento, lo eliminamos
        if evento == 'PREPOSICIONAMIENTO':
            return None

        # Si no tiene evento, aplicamos las nuevas reglas
        if evento == 'SIN EVENTO':
            # Verificamos si es Boqueron, Alto Paraguay o PDTE. HAYES -> SEQUIA
            departamento = row.get('departamento', '').upper()
            if departamento in ['BOQUERON', 'ALTO PARAGUAY', 'PDTE. HAYES']:
                return 'SEQUIA'
            
            # Verificamos si tiene kits -> EXTREMA VULNERABILIDAD
            if (row.get('kit_a', 0) > 0 or row.get('kit_b', 0) > 0):
                return 'EXTREMA VULNERABILIDAD'
            
            # Verificamos si tiene viveres <10 con materiales -> INCENDIO
            # Asumimos que 'viveres' es otro campo de ayuda (si no existe, deberías agregarlo)
            viveres = row.get('viveres', 0)
            materiales = sum(row.get(field, 0) for field in ['chapa_fibrocemento', 'chapa_zinc', 
                                                           'colchones', 'frazadas', 'terciadas', 
                                                           'puntales', 'carpas_plasticas'])
            if viveres > 0 and viveres < 10 and materiales > 0:
                return 'INCENDIO'
            
            # Verificamos si tiene viveres y es de 2020 o 2021 -> OLLA POPULAR
            fecha = row.get('fecha')
            if fecha and viveres > 0:
                try:
                    year = fecha.year if isinstance(fecha, (pd.Timestamp, datetime)) else pd.to_datetime(fecha).year
                    if year in [2020, 2021] and viveres < 10:
                        return 'OLLA POPULAR'
                except:
                    pass
            
            # Verificamos si es CAPITAL y solo tiene viveres -> INUNDACION
            if departamento == 'CAPITAL' and viveres > 0 and materiales == 0:
                return 'INUNDACION'
            
            # Si no cumple ninguna regla, dejamos SIN EVENTO
            return 'EXTREMA VULNERABILIDAD'
        
        return evento

    def corregir_distrito_como_departamento(self, departamento, distrito):
        """Corrige casos donde un distrito aparece como departamento."""
        dep_upper = str(departamento).strip().upper()
        dist_upper = str(distrito).strip().upper()
        
        if (not dist_upper or dist_upper == 'SIN ESPECIFICAR') and dep_upper in self.distrito_a_departamento:
            return (self.distrito_a_departamento[dep_upper], dep_upper)
        
        elif dep_upper in self.distrito_a_departamento:
            if not dist_upper or dist_upper == 'SIN ESPECIFICAR':
                return (self.distrito_a_departamento[dep_upper], dep_upper)
        
        return (dep_upper, dist_upper)

    def limpiar_departamento(self, departamento_str, distrito_str=None):
        """Limpia y estandariza nombres de departamentos."""
        # Manejo de valores nulos
        if pd.isna(departamento_str) or departamento_str is None or str(departamento_str).strip() == '':
            departamento_str = 'SIN_DEPARTAMENTO'
        if distrito_str is None:
            distrito_str = ''

        depto_raw = str(departamento_str).strip()

        # 1. Primero: estandarizar usando el diccionario
        depto_upper = depto_raw.upper()
        if depto_upper in self.estandarizacion_dept:
            depto_std = self.estandarizacion_dept[depto_upper]
        else:
            depto_std = depto_raw

        # 2. Verificar si es un caso especial (VARIOS, SIN_DEPARTAMENTO, etc.)
        # Nota: ahora usamos el valor estandarizado
        if depto_std in ['VARIOS DEPARTAMENTOS', 'INDI', 'VARIOS']:
            return 'CENTRAL'

        if depto_std == 'SIN_DEPARTAMENTO':
            return 'CENTRAL'

        # 3. Corregir si el departamento es en realidad un distrito
        depto_std, distrito_str = self.corregir_distrito_como_departamento(depto_std, distrito_str)

        # 4. Separadores: quedarnos con la primera parte
        separators = [' - ', ' / ', ', ', ' Y ']
        for sep in separators:
            if sep in depto_std:
                partes = depto_std.split(sep)
                primera = partes[0].strip()
                depto_std = primera
                break

        # 5. Buscar en el diccionario de nuevo, por si acaso
        if depto_std.upper() in self.estandarizacion_dept:
            depto_final = self.estandarizacion_dept[depto_std.upper()]
        else:
            depto_final = depto_std

        return depto_final

    def limpiar_registro_completo(self, record_dict):
        """Limpia un registro completo."""
        cleaned_record = record_dict.copy()

        # Limpiar campos numéricos
        for field in self.aid_fields:
            cleaned_record[field] = self.limpiar_numero(record_dict.get(field))

        # Limpiar distrito primero
        cleaned_record['distrito'] = self.limpiar_texto(record_dict.get('distrito'))
        
        # Limpiar departamento
        departamento_raw = record_dict.get('departamento')
        distrito_raw = cleaned_record['distrito']
        
        cleaned_record['departamento'] = self.limpiar_departamento(departamento_raw, distrito_raw)
        
        # Si el distrito está vacío pero el departamento es un distrito conocido
        if (not cleaned_record['distrito'] or cleaned_record['distrito'] == 'SIN ESPECIFICAR'):
            dep_upper = str(departamento_raw).strip().upper() if departamento_raw else ''
            if dep_upper in self.distrito_a_departamento:
                cleaned_record['distrito'] = str(departamento_raw).strip().title()
        
        # Resto de la limpieza
        cleaned_record['evento'] = self.limpiar_evento(record_dict.get('evento'))
        cleaned_record['localidad'] = self.limpiar_texto(record_dict.get('localidad'))

        # Manejo de fechas
        fecha_raw = record_dict.get('fecha')
        if pd.isna(fecha_raw) or fecha_raw is None:
            cleaned_record['fecha'] = None
        else:
            try:
                cleaned_record['fecha'] = pd.to_datetime(fecha_raw)
            except ValueError:
                cleaned_record['fecha'] = None

        cleaned_record['evento'] = self.post_process_eventos_with_aids(cleaned_record)

        return cleaned_record