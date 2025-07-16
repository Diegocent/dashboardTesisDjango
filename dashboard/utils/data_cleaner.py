import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self):
        self.aid_fields = [
            'kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc',
            'colchones', 'frazadas', 'terciadas', 'puntales', 'carpas_plasticas'
        ]

        # Diccionario de estandarización de departamentos para nombres individuales
        self.estandarizacion_dept = {
            'ÑEEMBUCU': 'ÑEEMBUCÚ', 'ÑEEMBUCÙ': 'ÑEEMBUCÚ', 'ÑEMBUCU': 'ÑEEMBUCÚ',
            'ALTO PARANA': 'ALTO PARANÁ', 'ALTO PARANÀ': 'ALTO PARANÁ', 'ALTO PNÀ': 'ALTO PARANÁ', 'ALTO PNÁ': 'ALTO PARANÁ', 'ALTO PY': 'ALTO PARANÁ',
            'BOQUERÒN': 'BOQUERON', 'BOQUERÓN': 'BOQUERON','CAAGUAZU-GUAIRA':'CAAGUAZÚ',
            'CAAGUAZU': 'CAAGUAZÚ', 'CAAGUAZÙ': 'CAAGUAZÚ',
            'CAAZAPA': 'CAAZAPÁ', 'CAAZAPÀ': 'CAAZAPÁ',
            'CANINDEYU': 'CANINDEYÚ', 'CANINDEYÙ': 'CANINDEYÚ',
            'CENT/CORDILL': 'CENTRAL', 'CENTR-CORD': 'CENTRAL', 'CENTRAL-CORDILLERA': 'CENTRAL', 'CENTRAL/CAP': 'CENTRAL', 'CENTRAL/CAPITAL': 'CENTRAL', 'CENTRAL/COR': 'CENTRAL', 'CENTRAL/CORD': 'CENTRAL', 'CENTRAL/CORD.': 'CENTRAL', 'CENTRAL/CORDILLER': 'CENTRAL', 'CENTRAL/CORDILLERA': 'CENTRAL', 'CENTRAL/PARAG.': 'CENTRAL', 'central': 'CENTRAL',
            'CONCEPCION': 'CONCEPCIÓN', 'CONCEPCIÒN': 'CONCEPCIÓN',
            'COORDILLERA': 'CORDILLERA', 'CORD./CENTRAL': 'CORDILLERA', 'CORD/S.PEDRO': 'CORDILLERA', 'CORDILLERA ARROYOS Y EST.': 'CORDILLERA', 'CORDILLERACAACUPÈ': 'CORDILLERA',
            'GUAIRA': 'GUAIRÁ', 'GUAIRÀ': 'GUAIRÁ', 'GUIARA': 'GUAIRÁ',
            'ITAPUA': 'ITAPÚA', 'ITAPÙA': 'ITAPÚA',
            'MISIONES YABEBYRY': 'MISIONES',
            'PARAGUARI': 'PARAGUARÍ', 'PARAGUARI PARAGUARI': 'PARAGUARÍ', 'PARAGUARÌ': 'PARAGUARÍ',
            'PDTE HAYES': 'PDTE. HAYES', 'PDTE HAYES S.PIRI-4 DE MAYO': 'PDTE. HAYES', 'PDTE HYES': 'PDTE. HAYES', 'PTE HAYES': 'PDTE. HAYES', 'PTE. HAYES': 'PDTE. HAYES', 'Pdte Hayes': 'PDTE. HAYES', 'Pdte. Hayes': 'PDTE. HAYES', 'PDTE.HAYES': 'PDTE. HAYES',
            'S.PEDRO/CAN.': 'SAN PEDRO', 'SAN PEDRO-CAAGUAZU': 'SAN PEDRO', 'SAN PEDRO/ AMAMBAY': 'SAN PEDRO', 'SAN PEDRO/ CANINDEYU': 'SAN PEDRO',
            'CORONEL OVIEDO': 'CORONEL OVIEDO', 'ITA': 'ITÁ', 'ITAUGUA': 'ITAUGUÁ', 'VILLARICA': 'VILLARRICA', 'ASUNCION': 'CAPITAL', 'ASUNCIÓN': 'CAPITAL', 'CAACUPÈ': 'CAACUPÉ'
        }

        self.estandarizacion_eventos = {
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

    def limpiar_numero(self, value):
        """Intenta convertir un valor a entero, si falla retorna 0."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def limpiar_texto(self, text):
        """Limpia y estandariza cadenas de texto."""
        if pd.isna(text) or text is None or str(text).strip() == '':
            return 'Sin Especificar'
        return str(text).strip().title()

    def limpiar_departamento(self, departamento_str):
        """Limpia y estandariza nombres de departamentos."""
        if pd.isna(departamento_str) or departamento_str is None or str(departamento_str).strip() == '':
            departamento_str = 'SIN_DEPARTAMENTO'

        departamento_str = str(departamento_str).strip().upper()

        # Reclasificar SIN_DEPARTAMENTO, VARIOS DEPARTAMENTOS, INDI a CENTRAL
        if departamento_str in ['SIN_DEPARTAMENTO', 'VARIOS DEPARTAMENTOS', 'INDI']:
            return 'CENTRAL'
        
        # Unificar departamentos compuestos (ej. "CANINDEYU - CAAGUAZU" -> "CANINDEYU")
        # Prioriza el primer departamento si hay un separador
        separators = [' - ', ' / ', ', ', ' Y '] # Orden de prioridad para los separadores
        for sep in separators:
            if sep in departamento_str:
                departamento_str = departamento_str.split(sep)[0].strip()
                break # Solo aplica la primera división encontrada

        # Aplicar estandarización específica para nombres individuales
        return self.estandarizacion_dept.get(departamento_str, departamento_str)

    def limpiar_evento(self, evento_str):
        """Limpia y estandariza nombres de eventos."""
        if pd.isna(evento_str) or evento_str is None or str(evento_str).strip() == '':
            return 'SIN_EVENTO'
        
        evento_str = str(evento_str).strip().upper()
        
        # Extraer solo la parte antes del guión (-) si existe
        evento_str = evento_str.split('-')[0].strip()
        
        return self.estandarizacion_eventos.get(evento_str, evento_str)

    def post_process_eventos_with_aids(self, row):
        """
        Ajusta el evento basado en la presencia de ayudas,
        especialmente para 'SIN EVENTO'.
        """
        evento = row['evento']
        
        if evento == 'SIN EVENTO':
            # Sumar todas las ayudas para la fila actual
            total_aids = sum(row.get(field, 0) for field in self.aid_fields)
            
            if total_aids > 0:
                # Lógica específica para reasignar eventos basados en ayudas
                if row.get('chapa_fibrocemento', 0) > 0:
                    return 'INUNDACION'
                elif row.get('chapa_zinc', 0) > 0:
                    return 'TEMPORAL'
                else:
                    return 'ASISTENCIA' # Si hay ayudas pero no chapas específicas
            else:
                # Si es 'SIN EVENTO' y no hay ayudas, se mantiene 'SIN EVENTO'
                pass
        return evento

    def limpiar_registro_completo(self, record_dict):
        """
        Limpia un diccionario de registro completo usando las funciones de limpieza.
        Retorna un nuevo diccionario con los datos limpios.
        """
        cleaned_record = record_dict.copy()

        # Limpiar campos numéricos
        for field in self.aid_fields:
            cleaned_record[field] = self.limpiar_numero(record_dict.get(field))

        # Limpiar campos de texto
        cleaned_record['departamento'] = self.limpiar_departamento(record_dict.get('departamento'))
        cleaned_record['evento'] = self.limpiar_evento(record_dict.get('evento'))
        cleaned_record['localidad'] = self.limpiar_texto(record_dict.get('localidad'))
        cleaned_record['distrito'] = self.limpiar_texto(record_dict.get('distrito'))

        # Asegurar que la fecha sea un objeto datetime
        fecha_raw = record_dict.get('fecha')
        if pd.isna(fecha_raw) or fecha_raw is None:
            cleaned_record['fecha'] = None
        else:
            try:
                cleaned_record['fecha'] = pd.to_datetime(fecha_raw)
            except ValueError:
                cleaned_record['fecha'] = None

        # Aplicar post-procesamiento de eventos
        cleaned_record['evento'] = self.post_process_eventos_with_aids(cleaned_record)

        return cleaned_record
