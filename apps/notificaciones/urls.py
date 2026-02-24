from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('api/',                  views.api_notificaciones,  name='api'),
    path('api/<int:pk>/leer/',    views.marcar_leida,        name='marcar_leida'),
    path('api/leer-todas/',       views.marcar_todas_leidas, name='marcar_todas_leidas'),
]
