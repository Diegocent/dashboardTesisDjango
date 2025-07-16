from django.contrib import admin
from .models import AsistenciaHumanitaria

@admin.register(AsistenciaHumanitaria)
class AsistenciaHumanitariaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'localidad', 'distrito', 'departamento', 'evento', 'total_ayudas']
    list_filter = ['departamento', 'distrito', 'evento', 'fecha']
    search_fields = ['localidad', 'distrito', 'departamento', 'evento']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información General', {
            'fields': ('fecha', 'localidad', 'distrito', 'departamento', 'evento')
        }),
        ('Kits de Ayuda', {
            'fields': ('kit_a', 'kit_b')
        }),
        ('Materiales de Construcción', {
            'fields': ('chapa_fibrocemento', 'chapa_zinc', 'terciadas', 'puntales')
        }),
        ('Otros Suministros', {
            'fields': ('colchones', 'frazadas', 'carpas_plasticas')
        }),
    )
