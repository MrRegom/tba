from django.urls import path

from . import views

app_name = 'fotocopiadora'

urlpatterns = [
    path('', views.MenuFotocopiadoraView.as_view(), name='menu_fotocopiadora'),
    path('solicitudes/mias/', views.MyPrintRequestListView.as_view(), name='mis_solicitudes_impresion'),
    path('solicitudes/aprobacion/', views.ApprovalQueueListView.as_view(), name='bandeja_aprobacion_impresion'),
    path('solicitudes/operacion/', views.OperatorQueueListView.as_view(), name='bandeja_operativa_impresion'),
    path('solicitudes/todas/', views.WorkflowAdminListView.as_view(), name='lista_solicitudes_impresion'),
    path('solicitudes/crear/', views.PrintRequestCreateView.as_view(), name='crear_solicitud_impresion'),
    path('solicitudes/<int:pk>/', views.PrintRequestDetailView.as_view(), name='detalle_solicitud_impresion'),
    path('solicitudes/<int:pk>/editar/', views.PrintRequestUpdateView.as_view(), name='editar_solicitud_impresion'),
    path('solicitudes/<int:pk>/transicion/', views.PrintRequestTransitionView.as_view(), name='transicion_solicitud_impresion'),
    path('memberships/', views.MembershipListView.as_view(), name='lista_memberships'),
    path('memberships/crear/', views.MembershipCreateView.as_view(), name='crear_membership'),
    path('memberships/<int:pk>/editar/', views.MembershipUpdateView.as_view(), name='editar_membership'),
    path('memberships/<int:pk>/eliminar/', views.MembershipDeleteView.as_view(), name='eliminar_membership'),

    # Legacy retirado de la operación oficial
    path('trabajos/', views.LegacyWorkflowRetiredView.as_view(), name='lista_trabajos'),
    path('trabajos/crear/', views.LegacyWorkflowRetiredView.as_view(), name='crear_trabajo'),
    path('trabajos/<int:pk>/', views.LegacyWorkflowRetiredView.as_view(), name='detalle_trabajo'),
    path('trabajos/<int:pk>/editar/', views.LegacyWorkflowRetiredView.as_view(), name='editar_trabajo'),
    path('trabajos/<int:pk>/eliminar/', views.LegacyWorkflowRetiredView.as_view(), name='eliminar_trabajo'),

    path('equipos/', views.EquipoListView.as_view(), name='lista_equipos'),
    path('equipos/crear/', views.EquipoCreateView.as_view(), name='crear_equipo'),
    path('equipos/<int:pk>/editar/', views.EquipoUpdateView.as_view(), name='editar_equipo'),
    path('equipos/<int:pk>/eliminar/', views.EquipoDeleteView.as_view(), name='eliminar_equipo'),
]
