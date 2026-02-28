from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    path('', views.dashboard_auditoria, name='dashboard'),
    path('registros/', views.lista_registros, name='lista_registros'),
    path('registros/<int:pk>/', views.detalle_registro, name='detalle_registro'),
    path('sesiones/', views.lista_sesiones, name='lista_sesiones'),
    path('logs-sistema/', views.lista_logs_sistema, name='lista_logs_sistema'),
    path('pin/', views.lista_auditoria_pin, name='lista_auditoria_pin'),
]
