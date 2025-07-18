import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self):
        self.aid_fields = [
            'kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc',
            'colchones', 'frazadas', 'terciadas', 'puntales', 'carpas_plasticas'
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
            'ITA': 'CENTRAL',
            'VILLARICA': 'GUAIRÁ',
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
        self.estandarizacion_eventos = {
            # COVID y variantes
            'ALB.COVID': 'COVID', 'ALBER.COVID': 'COVID', 'ALBERG.COVID': 'COVID',
            'COVI 19 OLL.': 'COVID', 'COVID 19': 'COVID', 'COVI': 'COVID',
            'VAC.ARATIRI': 'COVID', 'VACUNATORIO SND': 'COVID',
            'APOY.INST.COVID 19': 'COVID', 'APOYO INSTITUCIONAL COVID': 'COVID',

            # Apoyo institucional
            'APOY INST': 'APOYO INSTITUCIONAL', 'APOYO INST.': 'APOYO INSTITUCIONAL',
            'APOYO INSTIT.': 'APOYO INSTITUCIONAL', 'APOYO INT.': 'APOYO INSTITUCIONAL',
            'APOYO INTITUCIONAL': 'APOYO INSTITUCIONAL', 'APOYO INSITUCIONAL': 'APOYO INSTITUCIONAL',
            'APOY. INST.': 'APOYO INSTITUCIONAL', 'APOY.INST,': 'APOYO INSTITUCIONAL',
            'APOY.INSTITUC.': 'APOYO INSTITUCIONAL', 'APOY.INSTITUCIONAL': 'APOYO INSTITUCIONAL',
            'APAYO INSTITUCIONAL': 'APOYO INSTITUCIONAL', 'APOYO INSRITUCIOMAL': 'APOYO INSTITUCIONAL',
            'APOYO INSTITUCIOINAL': 'APOYO INSTITUCIONAL', 'APOYO INSTITUCIONAAL': 'APOYO INSTITUCIONAL',
            'APOYO INSTIYUCIONAL': 'APOYO INSTITUCIONAL', 'APYO INSTITUCIONAL': 'APOYO INSTITUCIONAL',
            'APOYO INSTITUCIONAL INDI': 'INDI',

            # Apoyo logístico
            'APOY.LOG': 'APOYO LOGISTICO', 'APOY LOG': 'APOYO LOGISTICO',
            'APOYO LOG.': 'APOYO LOGISTICO', 'APOYO LOGISTICO "TEMPORAL"': 'TEMPORAL',
            'APOYO LOGISTICO INDI': 'INDI',

            # Asistencia
            'ASIST.': 'ASISTENCIA', 'ASISTANCIA': 'ASISTENCIA', 'ASISTECIA': 'ASISTENCIA',
            'ASIASTENCIA': 'ASISTENCIA', 'ASISTENCIAS': 'ASISTENCIA',
            'AS.DE LA CORTE': 'ASISTENCIA INSTITUCIONAL',
            'ASISTENCIA DE LA CORTE': 'ASISTENCIA INSTITUCIONAL',
            'ASISTENCIA SECRETARIA DE REPATRIADOS': 'ASISTENCIA INSTITUCIONAL',
            'ASISTENCIA TEMPORAL': 'ASISTENCIA TEMPORAL',
            'ASISTENCIA COMUNIDAD INDIGENA': 'INDI',
            'ASISTENCIA A COMUNIDADES INDIGENAS': 'INDI',
            'ASISTENCIA COMUNITARIA': 'ASISTENCIA',
            'ASISTENCIA SOCIAL': 'ASISTENCIA',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LA ULTIMA INUNDACION': 'INUNDACION',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS INUNDACION Y SEQUIA': 'INUNDACION',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS SEQUIA.': 'SEQUIA',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS INUNDACION Y SEQUIA': 'INUNDACION',
            '	ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS INUNDACION.': 'INUNDACION',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS INUNDACIONES Y SEQUIAS': 'INUNDACION',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS INUNDACIONES.': 'INUNDACION',
            'ASISTENCIAS EN EL MARCO DE LOS TRABAJOS DE COORDINACION PARA LA REHABILITACION DE LOS MEDIOS DE VIDAS DE LAS FAMILIAS AFECTADAS POR LAS ULTIMAS SEQUIA.': 'SEQUIA',

            # Incidentes
            'INC.FORESTAL': 'INCENDIO', 'INCCENDIO': 'INCENDIO', 'INCEND': 'INCENDIO',
            'INCEND. DOMIC.': 'INCENDIO', 'INCENDIO DOMICILIARIO': 'INCENDIO',
            'DERRUMBE': 'DERRUMBE',

            # Inundaciones
            'INUNDAC.': 'INUNDACION', 'INUNDAIÓN S.': 'INUNDACION',
            'INUNDACION SUBITA': 'INUNDACION', 'INUNDACION " DECLARACION DE EMERGENCIA"': 'INUNDACION',
            'LNUNDACION': 'INUNDACION', 'SEQ. E INUND.': 'INUNDACION',
            'SEQ./INUND.': 'INUNDACION', 'SEQUIA-INUND.': 'SEQUIA',

            # Ollas populares
            'OLLA P': 'OLLA POPULAR', 'OLLA P.': 'OLLA POPULAR', 'OLLA POP': 'OLLA POPULAR',
            'OLLA POP.': 'OLLA POPULAR', 'OLLA POPILAR': 'OLLA POPULAR',
            'OLLA POPOLAR': 'OLLA POPULAR', 'OLLA POPUL': 'OLLA POPULAR',
            'OLLAP.': 'OLLA POPULAR', 'OLLA POPULAR COVID': 'OLLA POPULAR COVID',

            # Operativos
            'OP INVIERNO': 'OPERATIVO INVIERNO', 'OP. INVIERNO': 'OPERATIVO INVIERNO',
            'OP. ÑEÑUA': 'OPERATIVO ÑEÑUA', 'OP.INVIERNO': 'OPERATIVO INVIERNO',
            'OP.ÑEÑUA': 'OPERATIVO ÑEÑUA', 'OPER. ÑEÑUA': 'OPERATIVO ÑEÑUA',
            'OPER.INVIERN': 'OPERATIVO INVIERNO', 'OPER.INVIERNO': 'OPERATIVO INVIERNO',
            'OPERATIVO INV.': 'OPERATIVO INVIERNO', 'OPERATIVO CAACUPE': 'OPERATIVO ESPECIAL',
            'OPERATIVO RETORNO': 'OPERATIVO ESPECIAL',

            # Preposicionamiento
            'PREP.': 'PREPOSICIONAMIENTO', 'PREPOS': 'PREPOSICIONAMIENTO',
            'PREPOS.': 'PREPOSICIONAMIENTO', 'PREPOSIC.': 'PREPOSICIONAMIENTO',
            'PREPOSICION.': 'PREPOSICIONAMIENTO', 'PRE POSICIONAMIENTO': 'PREPOSICIONAMIENTO',
            'P/ STOCK DEL COE': 'PREPOSICIONAMIENTO',

            # Reposición de materiales
            'REP.DE MATERIAL': 'ASISTENCIA',
            'REPOSIC.MATER': 'ASISTENCIA',
            'REPOSIC.MATER.': 'ASISTENCIA',
            'PROVISION DE MATERIALES': 'ASISTENCIA',
            'REABASTECIMIENTO': 'ASISTENCIA',

            # Reparaciones
            'REPARACION': 'ASISTENCIA', 'REPARACION DE BAÑADERA': 'ASISTENCIA',
            'REPARACION DE OBRAS': 'ASISTENCIA',

            # Eventos institucionales
            'INDERT': 'ASISTENCIA', 'INDI MBYA GUARANI': 'INDI',
            'MUNICIPALIDAD': 'ASISTENCIA', 'NIÑEZ': 'ASISTENCIA',
            'DGRR 027/22': 'ASISTENCIA', 'DGRR 028/22': 'ASISTENCIA',

            # Otros eventos
            'DONAC': 'ASISTENCIA', 'DONAC.': 'ASISTENCIA', 'DONACIÒN': 'ASISTENCIA',
            'EDAN': 'EVALUACION DE DAÑOS', 'EVALUACION DE DAÑOS': 'EVALUACION DE DAÑOS',
            'MINGA': 'ASISTENCIA', 'INERAM(MINGA)': 'ASISTENCIA',
            'EVENTO CLIMATICO TEMPORAL': 'TEMPORAL', 'TEMPORAL CENTRAL': 'TEMPORAL',
            'ÑANGARECO': 'ASISTENCIA', 'ÑANGAREKO': 'ASISTENCIA',
            'AYUDA SOLIDARIA':'ASISTENCIA',
            'SIN_EVENTO': 'SIN EVENTO', 'DEVOLVIO': 'DEVOLUCION', 'REFUGIO SEN': 'ALBERGUE',
            'TRASLADO INTERNO': 'ASISTENCIA',
            'C I D H':'ASISTENCIA',
            'C.H.D.H':'ASISTENCIA',
            'C.I.D.H':'ASISTENCIA',
            'C.I.D.H.':'ASISTENCIA',
            'C.ID.H':'ASISTENCIA',
            'CIDH':'ASISTENCIA',
            'COMISION VECINAL':'ASISTENCIA',
            'ASISTENCIA INSTITUCIONAL':'ASISTENCIA',
            'ASISTENCIA TEMPORAL':'TEMPORAL',
            'APOYO LOGISTICO':'ASISTENCIA',
            'APOYO INSTITUCIONAL':'ASISTENCIA',
            'INCENDIO FORESTAL': 'INCENDIO',
            'PRESTAMO':'ASISTENCIA',
            'REPOSICION': 'ASISTENCIA',
            'TRABAJO COMUNITARIO': 'ASISTENCIA',
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
        """Limpia y estandariza nombres de eventos."""
        if pd.isna(evento_str) or evento_str is None or str(evento_str).strip() == '':
            return 'SIN EVENTO'
        
        evento_str = str(evento_str).strip().upper()
        evento_str = evento_str.split('-')[0].strip()
        return self.estandarizacion_eventos.get(evento_str, evento_str)

    def post_process_eventos_with_aids(self, row):
        """Ajusta el evento basado en la presencia de ayudas."""
        evento = row['evento']
        
        if evento == 'SIN EVENTO':
            total_aids = sum(row.get(field, 0) for field in self.aid_fields)
            
            if total_aids > 0:
                if row.get('chapa_fibrocemento', 0) > 0:
                    return 'INUNDACION'
                elif row.get('chapa_zinc', 0) > 0:
                    return 'TEMPORAL'
                else:
                    return 'ASISTENCIA'
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
        if pd.isna(departamento_str) or departamento_str is None or str(departamento_str).strip() == '':
            departamento_str = 'SIN_DEPARTAMENTO'
        
        if distrito_str is None:
            distrito_str = ''

        departamento_str, distrito_str = self.corregir_distrito_como_departamento(departamento_str, distrito_str)

        if departamento_str in ['SIN_DEPARTAMENTO', 'VARIOS DEPARTAMENTOS', 'INDI', 'VARIOS']:
            return 'CENTRAL'
        
        separators = [' - ', ' / ', ', ', ' Y ']
        for sep in separators:
            if sep in departamento_str:
                departamento_str = departamento_str.split(sep)[0].strip()
                break

        return self.estandarizacion_dept.get(departamento_str, departamento_str)

    def limpiar_registro_completo(self, record_dict):
        """Limpia un registro completo."""
        cleaned_record = record_dict.copy()

        for field in self.aid_fields:
            cleaned_record[field] = self.limpiar_numero(record_dict.get(field))

        cleaned_record['distrito'] = self.limpiar_texto(record_dict.get('distrito'))
        cleaned_record['departamento'] = self.limpiar_departamento(
            record_dict.get('departamento'),
            cleaned_record['distrito']
        )
        
        if (not cleaned_record['distrito'] or cleaned_record['distrito'] == 'SIN ESPECIFICAR') and str(record_dict.get('departamento', '')).strip().upper() in self.distrito_a_departamento:
            cleaned_record['distrito'] = str(record_dict.get('departamento')).strip().title()

        cleaned_record['evento'] = self.limpiar_evento(record_dict.get('evento'))
        cleaned_record['localidad'] = self.limpiar_texto(record_dict.get('localidad'))

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