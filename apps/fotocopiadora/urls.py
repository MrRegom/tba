from django.urls import path

from . import views

app_name = 'fotocopiadora'

urlpatterns = [
    path('', views.MenuFotocopiadoraView.as_view(), name='menu_fotocopiadora'),
    path('trabajos/', views.TrabajoFotocopiaListView.as_view(), name='lista_trabajos'),
    path('trabajos/crear/', views.TrabajoFotocopiaCreateView.as_view(), name='crear_trabajo'),
    path('trabajos/<int:pk>/', views.TrabajoFotocopiaDetailView.as_view(), name='detalle_trabajo'),
    path('trabajos/<int:pk>/editar/', views.TrabajoFotocopiaUpdateView.as_view(), name='editar_trabajo'),
    path('trabajos/<int:pk>/eliminar/', views.TrabajoFotocopiaDeleteView.as_view(), name='eliminar_trabajo'),

    path('equipos/', views.EquipoListView.as_view(), name='lista_equipos'),
    path('equipos/crear/', views.EquipoCreateView.as_view(), name='crear_equipo'),
    path('equipos/<int:pk>/editar/', views.EquipoUpdateView.as_view(), name='editar_equipo'),
    path('equipos/<int:pk>/eliminar/', views.EquipoDeleteView.as_view(), name='eliminar_equipo'),
]
