from django.db import models

class AsistenciaHumanitaria(models.Model):
    fecha = models.DateField()
    localidad = models.TextField()
    distrito = models.TextField()
    departamento = models.TextField()
    evento = models.TextField()
    kit_b = models.IntegerField(default=0)
    kit_a = models.IntegerField(default=0)
    chapa_fibrocemento = models.IntegerField(default=0)
    chapa_zinc = models.IntegerField(default=0)
    colchones = models.IntegerField(default=0)
    frazadas = models.IntegerField(default=0)
    terciadas = models.IntegerField(default=0)
    puntales = models.IntegerField(default=0)
    carpas_plasticas = models.IntegerField(default=0)

    class Meta:
        db_table = 'asistencia_humanitaria'
        verbose_name = 'Asistencia Humanitaria'
        verbose_name_plural = 'Asistencias Humanitarias'

    def __str__(self):
        return f"{self.localidad} - {self.fecha}"

    @property
    def total_ayudas(self):
        """Calcula el total de todas las ayudas"""
        return (self.kit_b + self.kit_a + self.chapa_fibrocemento + 
                self.chapa_zinc + self.colchones + self.frazadas + 
                self.terciadas + self.puntales + self.carpas_plasticas)

    @classmethod
    def obtener_estadisticas_generales(cls):
        """Obtiene estadísticas generales de la base de datos"""
        from django.db.models import Sum, Count, Min, Max
        
        stats = cls.objects.aggregate(
            total_registros=Count('id'),
            fecha_inicio=Min('fecha'),
            fecha_fin=Max('fecha'),
            total_kit_a=Sum('kit_a'),
            total_kit_b=Sum('kit_b'),
            total_ayudas=Sum('kit_a') + Sum('kit_b') + Sum('chapa_fibrocemento') + 
                         Sum('chapa_zinc') + Sum('colchones') + Sum('frazadas') + 
                         Sum('terciadas') + Sum('puntales') + Sum('carpas_plasticas')
        )
        
        return stats

    @classmethod
    def verificar_datos_disponibles(cls):
        """Verifica si hay datos disponibles en la base"""
        return cls.objects.exists()
