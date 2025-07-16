from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('geografico/', views.analisis_geografico_view, name='geografico'),
    path('temporal/', views.analisis_temporal_view, name='temporal'),
    path('eventos/', views.analisis_eventos_view, name='eventos'),
    path('api/datos-tabla/', views.datos_tabla_view, name='datos_tabla'),
    path('api/datos-mapa/', views.datos_mapa_view, name='datos_mapa'),
]
