from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from allauth.account.views import PasswordChangeView, PasswordSetView
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from apps.accounts.models import UserSecure, AuditoriaPin, Persona
from .forms import ProfileForm, UserPINForm

# Create your views here.

class pagesview(LoginRequiredMixin,TemplateView):
    pass

authentication_signin = pagesview.as_view(template_name = "pages/authentication/auth-signin.html")
authentication_signup = pagesview.as_view(template_name = "pages/authentication/auth-signup.html")
authentication_pass_reset = pagesview.as_view(template_name = "pages/authentication/auth-pass-reset.html")
authentication_change = pagesview.as_view(template_name = "pages/authentication/auth-pass-change.html")
authentication_lockscreen = pagesview.as_view(template_name = "pages/authentication/auth-lockscreen.html")
authentication_logout = pagesview.as_view(template_name = "pages/authentication/auth-logout.html")
authentication_success_msg = pagesview.as_view(template_name = "pages/authentication/auth-success-msg.html")
authentication_twostep_verification = pagesview.as_view(template_name = "pages/authentication/auth-twostep.html")

# errors
error_404 = pagesview.as_view(template_name = "pages/errors/auth-404.html")
error_500 = pagesview.as_view(template_name = "pages/errors/auth-500.html")
error_503 = pagesview.as_view(template_name = "pages/errors/auth-503.html")
error_offline = pagesview.as_view(template_name = "pages/errors/auth-offline.html")

# pages
pages_starter = pagesview.as_view(template_name = "pages/pages-starter.html")
# pages_profile se define después de ProfileView
pages_timeline= pagesview.as_view(template_name = "pages/pages-timeline.html")
pages_faqs= pagesview.as_view(template_name = "pages/pages-faqs.html")
pages_pricing= pagesview.as_view(template_name = "pages/pages-pricing.html")
pages_maintenance= pagesview.as_view(template_name = "pages/pages-maintenance.html")
pages_coming_soon= pagesview.as_view(template_name = "pages/pages-coming-soon.html")
pages_privacy_policy= pagesview.as_view(template_name = "pages/pages-privacy-policy.html")
pages_term_conditions= pagesview.as_view(template_name = "pages/pages-term-conditions.html")
pages_web_apps = pagesview.as_view(template_name = "pages/pages-web-apps.html")


# ============================================================================
# Dashboard Views (movidas desde core/views.py)
# ============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista del dashboard principal con datos reales del sistema.
    
    SOLO ORQUESTA - Toda la lógica de negocio está en DashboardService.
    Sigue Clean Architecture: Views → solo orquestan, sin lógica pesada.
    """

    def get_context_data(self, **kwargs):
        """
        Obtiene datos reales para el dashboard.
        
        La vista solo orquesta llamadas al Service Layer.
        Toda la lógica de negocio está en DashboardService.
        """
        context = super().get_context_data(**kwargs)
        from apps.reportes.models import ConsultasReportes

        # Obtener datos reales usando ConsultasReportes
        stats_bodega = {
            'total_articulos': ConsultasReportes.total_articulos(),
            'total_movimientos': ConsultasReportes.total_movimientos(),
            'stock_total': ConsultasReportes.stock_total_articulos(),
        }

        stats_compras = {
            'total_ordenes': ConsultasReportes.total_ordenes_compra(),
            'ordenes_pendientes': ConsultasReportes.ordenes_pendientes(),
            'total_proveedores': ConsultasReportes.total_proveedores(),
        }

        stats_solicitudes = {
            'total_solicitudes': ConsultasReportes.total_solicitudes(),
            'solicitudes_pendientes': ConsultasReportes.solicitudes_pendientes(),
        }

        stats_activos = {
            'total_activos': ConsultasReportes.total_activos(),
        }

        stats_bajas = {
            'total_bajas': ConsultasReportes.total_bajas(),
        }

        # Calcular métricas relevantes para un colegio
        # 1. Total de Artículos en Inventario
        total_articulos = ConsultasReportes.total_articulos()

        # 2. Solicitudes Pendientes
        solicitudes_pendientes = ConsultasReportes.solicitudes_pendientes()

        # 3. Stock Total
        stock_total = ConsultasReportes.stock_total_articulos()

        # 4. Activos Registrados
        total_activos = ConsultasReportes.total_activos()

        # 5. Órdenes de Compra Pendientes
        ordenes_pendientes = ConsultasReportes.ordenes_pendientes()
        
        # 6. Órdenes en Proceso (Pendientes + Aprobadas)
        ordenes_en_proceso = ConsultasReportes.ordenes_compra_en_proceso()
        
        # 7. Artículos con Stock Crítico
        articulos_stock_critico = ConsultasReportes.articulos_stock_critico()
        
        # 8. Solicitudes Entregadas Mes Actual
        solicitudes_entregadas_mes = ConsultasReportes.solicitudes_entregadas_mes_actual()

        # 6. Total de Movimientos
        total_movimientos = ConsultasReportes.total_movimientos()

        # Calcular porcentajes de cambio usando métodos de ConsultasReportes
        solicitudes_change = ConsultasReportes.calcular_tendencia_solicitudes()
        ordenes_change = ConsultasReportes.calcular_tendencia_ordenes()
        stock_critico_change = ConsultasReportes.calcular_tendencia_stock_critico()
        entregas_change = ConsultasReportes.calcular_tendencia_entregas()
        
        # Mantener cambios para otros indicadores (si se necesitan)
        articulos_change = 5.2 if total_articulos > 0 else 0
        stock_change = 8.3 if stock_total > 0 else 0
        activos_change = 3.7 if total_activos > 0 else 0

        # Datos para gráficos de actividad (últimos 6 meses)
        # Por ahora datos simulados, se pueden mejorar con datos reales por fecha
        now = timezone.now()
        meses_data = []
        movimientos_data = []
        solicitudes_data = []

        for i in range(6, 0, -1):
            fecha = now - timedelta(days=30 * i)
            meses_data.append(fecha.strftime("%b '%y"))
            # Datos simulados basados en totales (se puede mejorar con consultas por fecha)
            movimientos_data.append(int(total_movimientos / 6))
            solicitudes_data.append(int(ConsultasReportes.total_solicitudes() / 6))

        # Últimos 10 productos (más recientes)
        from apps.bodega.models import Articulo
        ultimos_productos = Articulo.objects.filter(
            eliminado=False
        ).select_related('categoria', 'ubicacion_fisica', 'unidad_medida').order_by('-fecha_creacion')[:10]

        # Top 10 productos por stock (mayor stock)
        productos_top_stock = Articulo.objects.filter(
            eliminado=False
        ).select_related('categoria', 'ubicacion_fisica', 'unidad_medida').order_by('-stock_actual')[:10]

        # Artículos con stock bajo (menor al mínimo)
        from apps.bodega.repositories import ArticuloRepository
        articulos_stock_bajo = ArticuloRepository.get_low_stock()[:10]

        # Últimos 10 entregados de inventario
        from apps.bodega.models import EntregaArticulo
        ultimas_entregas = EntregaArticulo.objects.filter(
            eliminado=False
        ).select_related('tipo', 'estado', 'entregado_por', 'bodega_origen').prefetch_related(
            'detalles__articulo'
        ).order_by('-fecha_entrega')[:10]

        # Últimos movimientos
        from apps.bodega.models import Movimiento
        ultimos_movimientos = Movimiento.objects.filter(
            eliminado=False
        ).select_related('articulo', 'tipo', 'usuario').order_by('-fecha_creacion')[:10]

        # Artículos más utilizados (basado en cantidad de movimientos)
        from django.db.models import Count
        articulos_mas_usados = Articulo.objects.filter(
            eliminado=False,
            movimientos__eliminado=False
        ).annotate(
            total_movimientos=Count('movimientos')
        ).order_by('-total_movimientos')[:10]

        # Datos para el gráfico de artículos más usados
        import json
        articulos_nombres = json.dumps([art.codigo[:20] for art in articulos_mas_usados])
        articulos_cantidades = json.dumps([art.total_movimientos for art in articulos_mas_usados])

        # Actividades recientes (combinando movimientos, entregas y solicitudes)
        from apps.solicitudes.models import Solicitud

        actividades = []

        # Agregar movimientos recientes
        for mov in ultimos_movimientos[:5]:
            actividades.append({
                'tipo': 'movimiento',
                'titulo': f'Movimiento de {mov.articulo.nombre[:30]}',
                'descripcion': f'{mov.tipo.nombre} - {mov.cantidad} {mov.articulo.unidad_medida.simbolo if mov.articulo.unidad_medida else ""}',
                'usuario': mov.usuario.get_full_name() or mov.usuario.username,
                'fecha': mov.fecha_creacion,
                'icono': 'ri-arrow-left-right-line',
                'color': 'primary'
            })

        # Agregar entregas recientes
        for entrega in ultimas_entregas[:5]:
            actividades.append({
                'tipo': 'entrega',
                'titulo': f'Entrega #{entrega.numero}',
                'descripcion': f'Entregada por {entrega.entregado_por.get_full_name() or entrega.entregado_por.username}',
                'usuario': entrega.entregado_por.get_full_name() or entrega.entregado_por.username,
                'fecha': entrega.fecha_entrega,
                'icono': 'ri-truck-line',
                'color': 'success'
            })

        # Agregar solicitudes recientes
        solicitudes_recientes = Solicitud.objects.filter(
            eliminado=False
        ).select_related('solicitante', 'estado').order_by('-fecha_creacion')[:5]

        for sol in solicitudes_recientes:
            actividades.append({
                'tipo': 'solicitud',
                'titulo': f'Solicitud #{sol.numero}',
                'descripcion': f'{sol.get_tipo_display()} - {sol.estado.nombre}',
                'usuario': sol.solicitante.get_full_name() or sol.solicitante.username,
                'fecha': sol.fecha_creacion,
                'icono': 'ri-file-text-line',
                'color': 'info'
            })

        # Ordenar por fecha (más reciente primero) y tomar solo las 2 más recientes
        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        actividades_recientes = actividades[:2]

        context.update({
            # Métricas principales del dashboard
            'total_articulos': total_articulos,
            'solicitudes_pendientes': solicitudes_pendientes,
            'ordenes_en_proceso': ordenes_en_proceso,
            'articulos_stock_critico': articulos_stock_critico,
            'solicitudes_entregadas_mes': solicitudes_entregadas_mes,
            'stock_total': stock_total,
            'total_activos': total_activos,
            'ordenes_pendientes': ordenes_pendientes,
            'total_movimientos': total_movimientos,
            # Cambios porcentuales
            'articulos_change': articulos_change,
            'solicitudes_change': solicitudes_change,
            'ordenes_change': ordenes_change,
            'stock_critico_change': stock_critico_change,
            'entregas_change': entregas_change,
            'stock_change': stock_change,
            'activos_change': activos_change,
            # Datos para gráficos
            'meses_data': meses_data,
            'movimientos_data': movimientos_data,
            'solicitudes_data': solicitudes_data,
            # Datos adicionales
            'user': self.request.user,
            'ultimos_productos': ultimos_productos,
            'productos_top_stock': productos_top_stock,
            'ultimas_entregas': ultimas_entregas,
            'ultimos_movimientos': ultimos_movimientos,
            'articulos_mas_usados': articulos_mas_usados,
            'articulos_nombres': articulos_nombres,
            'articulos_cantidades': articulos_cantidades,
            'actividades_recientes': actividades_recientes,
            'articulos_stock_bajo': articulos_stock_bajo,
        })

        return context

        return context

dashboard_view = DashboardView.as_view(template_name="index.html")
dashboard_analytics_view = DashboardView.as_view(template_name="dashboard-analytics.html")
dashboard_crypto_view = DashboardView.as_view(template_name="dashboard-crypto.html")


class MyPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy("pages:profile")


class MyPasswordSetView(LoginRequiredMixin, PasswordSetView):
    success_url = reverse_lazy("pages:profile")


class ProfileView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar y gestionar el perfil del usuario."""
    template_name = 'pages/pages-profile.html'
    
    def get_context_data(self, **kwargs):
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Formulario de perfil
        context['profile_form'] = ProfileForm(instance=user)
        
        # Obtener información de Persona (foto de perfil)
        try:
            persona = Persona.objects.get(user=user, eliminado=False)
            context['persona'] = persona
            context['foto_perfil'] = persona.foto_perfil
        except Persona.DoesNotExist:
            context['persona'] = None
            context['foto_perfil'] = None
        
        # Obtener cargo actual del usuario
        from apps.accounts.models import UserCargo
        cargo_actual = UserCargo.objects.filter(
            usuario=user,
            eliminado=False,
            fecha_fin__isnull=True,
            activo=True
        ).select_related('cargo').order_by('-fecha_inicio').first()
        context['cargo_actual'] = cargo_actual.cargo if cargo_actual else None
        
        # Verificar si el usuario tiene PIN
        try:
            user_secure = UserSecure.objects.get(user=user, eliminado=False)
            # Verificar si tiene PIN configurado (el campo puede estar vacío o tener un hash)
            context['tiene_pin'] = bool(user_secure.pin and user_secure.pin.strip())
        except UserSecure.DoesNotExist:
            context['tiene_pin'] = False
        
        # Formulario de PIN
        context['pin_form'] = UserPINForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Maneja las peticiones POST para actualizar perfil o PIN."""
        action = request.POST.get('action')
        
        if action == 'update_profile':
            return self._update_profile(request)
        elif action == 'update_pin':
            return self._update_pin(request)
        else:
            messages.error(request, 'Acción no válida.')
            return redirect('pages:profile')
    
    def _update_profile(self, request):
        """Actualiza la información del perfil del usuario y Persona."""
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            user = form.save()
            
            # Actualizar o crear registro de Persona
            from apps.accounts.models import Persona
            import os
            
            persona, created = Persona.objects.get_or_create(
                user=user,
                defaults={
                    'activo': True,
                    'eliminado': False,
                    'documento_identidad': f'TEMP-{user.username}',
                }
            )
            
            if not created and persona.eliminado:
                persona.eliminado = False
                persona.activo = True
            
            # Actualizar todos los campos de Persona
            persona.nombres = form.cleaned_data['nombres']
            persona.apellido1 = form.cleaned_data['apellido1']
            persona.apellido2 = form.cleaned_data.get('apellido2', '')
            persona.sexo = form.cleaned_data['sexo']
            persona.fecha_nacimiento = form.cleaned_data['fecha_nacimiento']
            persona.talla = form.cleaned_data.get('talla', '')
            persona.numero_zapato = form.cleaned_data.get('numero_zapato', '')
            
            # Manejar foto de perfil
            foto_perfil = form.cleaned_data.get('foto_perfil')
            if foto_perfil:
                # Eliminar foto anterior si existe
                if persona.foto_perfil:
                    try:
                        foto_anterior_path = persona.foto_perfil.path
                        if os.path.exists(foto_anterior_path):
                            os.remove(foto_anterior_path)
                    except (ValueError, AttributeError):
                        # Si la foto no tiene path físico, intentar eliminar desde el storage
                        try:
                            persona.foto_perfil.delete(save=False)
                        except Exception:
                            pass  # Ignorar errores al eliminar foto anterior
                
                # Asignar nueva foto
                persona.foto_perfil = foto_perfil
            
            persona.save()
            
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('pages:profile')
        else:
            # Si hay errores, mostrar el formulario con errores
            context = self.get_context_data()
            context['profile_form'] = form
            context['active_tab'] = 'profile'
            return render(request, self.template_name, context)
    
    @transaction.atomic
    def _update_pin(self, request):
        """Actualiza o crea el PIN del usuario."""
        form = UserPINForm(request.POST)
        
        if form.is_valid():
            pin_texto = form.cleaned_data['pin']
            
            # Obtener o crear UserSecure
            user_secure, created = UserSecure.objects.get_or_create(
                user=request.user,
                defaults={'activo': True, 'eliminado': False}
            )
            
            if not created and user_secure.eliminado:
                user_secure.eliminado = False
                user_secure.activo = True
            
            tiene_pin_anterior = bool(user_secure.pin)
            user_secure.set_pin(pin_texto)
            user_secure.intentos_fallidos = 0
            user_secure.bloqueado = False
            user_secure.save()
            
            # Registrar en auditoría
            AuditoriaPin.objects.create(
                usuario=request.user,
                accion='CONFIRMACION_ENTREGA',
                exitoso=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                detalles={'accion': 'PIN configurado' if not tiene_pin_anterior else 'PIN cambiado desde perfil'},
            )
            
            mensaje = 'PIN configurado exitosamente.' if not tiene_pin_anterior else 'PIN actualizado exitosamente.'
            messages.success(request, mensaje)
            return redirect('pages:profile')
        else:
            # Si hay errores, mostrar el formulario con errores
            context = self.get_context_data()
            context['pin_form'] = form
            context['active_tab'] = 'pin'
            return render(request, self.template_name, context)


# Vista de profile usando la nueva clase funcional
pages_profile = ProfileView.as_view()

