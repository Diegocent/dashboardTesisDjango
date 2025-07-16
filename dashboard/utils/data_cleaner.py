"""
Utilidades para limpieza de datos en tiempo real
"""

import pandas as pd
import re
from typing import Dict, Any, Optional

class DataCleaner:
    """Clase para limpiar datos de asistencia humanitaria"""
    
    def __init__(self):
        self.departamentos_estandarizacion = {
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
        
        self.eventos_estandarizacion = {
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
        
        self.aid_fields = [
            'kit_b', 'kit_a', 'chapa_fibrocemento', 'chapa_zinc',
            'colchones', 'frazadas', 'terciadas', 'puntales', 'carpas_plasticas'
        ]
    
    def limpiar_departamento(self, departamento: str) -> str:
        """Limpia y estandariza nombre de departamento"""
        if not departamento or pd.isna(departamento):
            return 'SIN ESPECIFICAR'
        
        dept_limpio = str(departamento).strip().upper()
        return self.departamentos_estandarizacion.get(dept_limpio, dept_limpio)
    
    def limpiar_evento(self, evento: str) -> str:
        """Limpia y estandariza tipo de evento (pre-procesamiento)"""
        if not evento or pd.isna(evento):
            return 'SIN EVENTO'
        
        # Extraer parte antes del guión
        evento_limpio = str(evento).split('-')[0].strip().upper()
        return self.eventos_estandarizacion.get(evento_limpio, evento_limpio)
    
    def limpiar_texto(self, texto: str) -> str:
        """Limpia texto general"""
        if not texto or pd.isna(texto):
            return 'Sin Especificar'
        
        return str(texto).strip().title()
    
    def limpiar_numero(self, numero: Any) -> int:
        """Convierte y limpia valores numéricos"""
        try:
            if pd.isna(numero) or numero == '' or numero is None:
                return 0
            return int(float(numero))
        except (ValueError, TypeError):
            return 0
    
    def post_process_eventos_with_aids(self, record: Dict[str, Any]) -> str:
        """
        Aplica lógica adicional para eventos 'SIN EVENTO' basada en la presencia de ayudas.
        Debe ser llamada DESPUÉS de que los campos numéricos de ayuda estén limpios.
        """
        evento = record.get('evento', 'SIN EVENTO')
        
        # Solo aplicar si el evento es 'SIN EVENTO' (case-insensitive)
        if evento.upper().strip() == 'SIN EVENTO':
            chapa_fibrocemento = record.get('chapa_fibrocemento', 0)
            chapa_zinc = record.get('chapa_zinc', 0)
            
            # Calcular el total de ayudas para este registro
            total_ayudas = sum(record.get(field, 0) for field in self.aid_fields)
            
            if chapa_fibrocemento > 0:
                return 'INUNDACION'
            elif chapa_zinc > 0:
                return 'TEMPORAL'
            elif total_ayudas > 0:
                return 'ASISTENCIA'
            else:
                # Si es 'SIN EVENTO' y no tiene ayudas, se mantiene como 'SIN EVENTO'
                # (para las vistas, no se elimina el registro)
                return 'SIN EVENTO'
        return evento

    def limpiar_registro_completo(self, registro_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia un registro completo"""
        registro_limpio = registro_dict.copy()
        
        # Limpiar números primero, ya que la lógica de eventos depende de ellos
        for campo in self.aid_fields:
            if campo in registro_limpio:
                registro_limpio[campo] = self.limpiar_numero(
                    registro_limpio[campo]
                )
        
        # Limpiar evento (pre-procesamiento)
        if 'evento' in registro_limpio:
            registro_limpio['evento'] = self.limpiar_evento(
                registro_limpio['evento']
            )
        
        # Aplicar post-procesamiento de eventos basado en ayudas
        if 'evento' in registro_limpio:
            registro_limpio['evento'] = self.post_process_eventos_with_aids(
                registro_limpio
            )
        
        # Limpiar departamento
        if 'departamento' in registro_limpio:
            registro_limpio['departamento'] = self.limpiar_departamento(
                registro_limpio['departamento']
            )
        
        # Limpiar textos
        for campo in ['distrito', 'localidad']:
            if campo in registro_limpio:
                registro_limpio[campo] = self.limpiar_texto(
                    registro_limpio[campo]
                )
        
        return registro_limpio

# Instancia global del limpiador
data_cleaner = DataCleaner()
