"""
Vistas de Auditoría — solo accesibles por administradores (is_staff o is_superuser).
Muestra cuatro secciones:
  1. Registro de Auditoría   → operaciones CRUD sobre modelos del sistema
  2. Auditoría de Sesiones   → login / logout / intentos fallidos
  3. Logs del Sistema        → acciones registradas con registrar_log_auditoria
  4. Auditoría de PIN        → uso del PIN de confirmación de entregas
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from .models import RegistroAuditoria, AuditoriaSesion
from apps.accounts.models import AuthLogs, AuditoriaPin

# ── Decorador administrador ───────────────────────────────────────────────────

def es_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

admin_required = user_passes_test(es_admin, login_url='account_login')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _paginar(qs, request, key='page', per_page=20):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(request.GET.get(key, 1))


def _rango_fechas(request):
    """Devuelve (fecha_desde, fecha_hasta) desde los GET params, o None."""
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    return desde or None, hasta or None


# ── Vista principal (dashboard de auditoría) ──────────────────────────────────

@login_required
@admin_required
def dashboard_auditoria(request):
    """Resumen estadístico de los últimos 30 días."""
    hace_30 = timezone.now() - timedelta(days=30)

    stats = {
        'total_registros': RegistroAuditoria.objects.count(),
        'registros_30d': RegistroAuditoria.objects.filter(timestamp__gte=hace_30).count(),
        'sesiones_30d': AuditoriaSesion.objects.filter(timestamp__gte=hace_30).count(),
        'logins_fallidos_30d': AuditoriaSesion.objects.filter(
            timestamp__gte=hace_30,
            evento=AuditoriaSesion.TipoEvento.LOGIN_FALLIDO
        ).count(),
        'logs_sistema_30d': AuthLogs.objects.filter(fecha_creacion__gte=hace_30).count(),
        'pin_fallidos_30d': AuditoriaPin.objects.filter(
            fecha_creacion__gte=hace_30, exitoso=False
        ).count(),
    }

    # Últimas 10 acciones de cada tipo para la vista rápida
    ultimos_registros = (
        RegistroAuditoria.objects
        .select_related('usuario', 'content_type')
        .order_by('-timestamp')[:10]
    )
    ultimas_sesiones = (
        AuditoriaSesion.objects
        .select_related('usuario')
        .order_by('-timestamp')[:10]
    )

    # Acciones más frecuentes (top 5)
    top_acciones = (
        RegistroAuditoria.objects
        .filter(timestamp__gte=hace_30)
        .values('accion')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    return render(request, 'auditoria/dashboard.html', {
        'titulo': 'Auditoría del Sistema',
        'stats': stats,
        'ultimos_registros': ultimos_registros,
        'ultimas_sesiones': ultimas_sesiones,
        'top_acciones': top_acciones,
    })


# ── Registro de Auditoría (CRUD en modelos) ───────────────────────────────────

@login_required
@admin_required
def lista_registros(request):
    """Lista paginada + filtros de RegistroAuditoria."""
    from django.contrib.contenttypes.models import ContentType

    qs = RegistroAuditoria.objects.select_related('usuario', 'content_type').order_by('-timestamp')

    # Filtros
    q = request.GET.get('q', '').strip()
    accion = request.GET.get('accion', '').strip()
    modulo = request.GET.get('modulo', '').strip()
    usuario_id = request.GET.get('usuario_id', '').strip()
    desde, hasta = _rango_fechas(request)

    if q:
        qs = qs.filter(
            Q(usuario__username__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(ip_address__icontains=q)
        )
    if accion:
        qs = qs.filter(accion=accion)
    if modulo:
        qs = qs.filter(content_type__app_label=modulo)
    if usuario_id:
        qs = qs.filter(usuario_id=usuario_id)
    if desde:
        qs = qs.filter(timestamp__date__gte=desde)
    if hasta:
        qs = qs.filter(timestamp__date__lte=hasta)

    from django.contrib.auth.models import User
    page_obj = _paginar(qs, request)
    modulos = ContentType.objects.values_list('app_label', flat=True).distinct().order_by('app_label')
    usuarios = User.objects.filter(is_active=True).order_by('username')

    return render(request, 'auditoria/registros.html', {
        'titulo': 'Registro de Auditoría',
        'page_obj': page_obj,
        'modulos': modulos,
        'usuarios': usuarios,
        'acciones': RegistroAuditoria._meta.get_field('accion').choices,
        'filtros': {
            'q': q, 'accion': accion, 'modulo': modulo,
            'usuario_id': usuario_id, 'desde': desde or '', 'hasta': hasta or '',
        },
    })


@login_required
@admin_required
def detalle_registro(request, pk):
    """Detalle completo de un RegistroAuditoria con diff JSON."""
    from django.shortcuts import get_object_or_404
    registro = get_object_or_404(
        RegistroAuditoria.objects.select_related('usuario', 'content_type'), pk=pk
    )
    return render(request, 'auditoria/detalle_registro.html', {
        'titulo': f'Detalle Auditoría #{pk}',
        'registro': registro,
    })


# ── Auditoría de Sesiones ─────────────────────────────────────────────────────

@login_required
@admin_required
def lista_sesiones(request):
    """Lista paginada + filtros de AuditoriaSesion."""
    from django.contrib.auth.models import User

    qs = AuditoriaSesion.objects.select_related('usuario').order_by('-timestamp')

    q = request.GET.get('q', '').strip()
    evento = request.GET.get('evento', '').strip()
    exitoso = request.GET.get('exitoso', '').strip()
    desde, hasta = _rango_fechas(request)

    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(ip_address__icontains=q) |
            Q(usuario__first_name__icontains=q) |
            Q(usuario__last_name__icontains=q)
        )
    if evento:
        qs = qs.filter(evento=evento)
    if exitoso in ('true', 'false'):
        qs = qs.filter(exitoso=(exitoso == 'true'))
    if desde:
        qs = qs.filter(timestamp__date__gte=desde)
    if hasta:
        qs = qs.filter(timestamp__date__lte=hasta)

    return render(request, 'auditoria/sesiones.html', {
        'titulo': 'Auditoría de Sesiones',
        'page_obj': _paginar(qs, request),
        'eventos': AuditoriaSesion.TipoEvento.choices,
        'filtros': {
            'q': q, 'evento': evento, 'exitoso': exitoso,
            'desde': desde or '', 'hasta': hasta or '',
        },
    })


# ── Logs del Sistema (AuthLogs) ───────────────────────────────────────────────

@login_required
@admin_required
def lista_logs_sistema(request):
    """Lista paginada + filtros de AuthLogs."""
    from django.contrib.auth.models import User
    from apps.accounts.models import AuthLogAccion

    qs = AuthLogs.objects.select_related('usuario', 'accion').order_by('-fecha_creacion')

    q = request.GET.get('q', '').strip()
    accion_id = request.GET.get('accion_id', '').strip()
    usuario_id = request.GET.get('usuario_id', '').strip()
    desde, hasta = _rango_fechas(request)

    if q:
        qs = qs.filter(
            Q(usuario__username__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(ip_usuario__icontains=q)
        )
    if accion_id:
        qs = qs.filter(accion_id=accion_id)
    if usuario_id:
        qs = qs.filter(usuario_id=usuario_id)
    if desde:
        qs = qs.filter(fecha_creacion__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_creacion__date__lte=hasta)

    acciones = AuthLogAccion.objects.filter(activo=True).order_by('glosa')
    usuarios = User.objects.filter(is_active=True).order_by('username')

    return render(request, 'auditoria/logs_sistema.html', {
        'titulo': 'Logs del Sistema',
        'page_obj': _paginar(qs, request),
        'acciones': acciones,
        'usuarios': usuarios,
        'filtros': {
            'q': q, 'accion_id': accion_id, 'usuario_id': usuario_id,
            'desde': desde or '', 'hasta': hasta or '',
        },
    })


# ── Auditoría de PIN ──────────────────────────────────────────────────────────

@login_required
@admin_required
def lista_auditoria_pin(request):
    """Lista paginada + filtros de AuditoriaPin."""
    from django.contrib.auth.models import User

    qs = AuditoriaPin.objects.select_related('usuario').order_by('-fecha_creacion')

    q = request.GET.get('q', '').strip()
    accion = request.GET.get('accion', '').strip()
    exitoso = request.GET.get('exitoso', '').strip()
    desde, hasta = _rango_fechas(request)

    if q:
        qs = qs.filter(
            Q(usuario__username__icontains=q) |
            Q(ip_address__icontains=q) |
            Q(usuario__first_name__icontains=q) |
            Q(usuario__last_name__icontains=q)
        )
    if accion:
        qs = qs.filter(accion=accion)
    if exitoso in ('true', 'false'):
        qs = qs.filter(exitoso=(exitoso == 'true'))
    if desde:
        qs = qs.filter(fecha_creacion__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_creacion__date__lte=hasta)

    usuarios = User.objects.filter(is_active=True).order_by('username')

    return render(request, 'auditoria/pin.html', {
        'titulo': 'Auditoría de PIN',
        'page_obj': _paginar(qs, request),
        'acciones_pin': AuditoriaPin.ACCION_CHOICES,
        'usuarios': usuarios,
        'filtros': {
            'q': q, 'accion': accion, 'exitoso': exitoso,
            'desde': desde or '', 'hasta': hasta or '',
        },
    })
