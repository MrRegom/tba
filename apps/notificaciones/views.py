from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notificacion


@login_required
def api_notificaciones(request):
    """Devuelve las últimas 20 notificaciones del usuario con el conteo de no leídas."""
    qs = Notificacion.objects.filter(
        destinatario=request.user
    ).order_by('-fecha_creacion')[:20]

    no_leidas = Notificacion.objects.filter(
        destinatario=request.user, leida=False
    ).count()

    items = [
        {
            'id':      n.id,
            'tipo':    n.tipo,
            'titulo':  n.titulo,
            'mensaje': n.mensaje,
            'url':     n.url,
            'leida':   n.leida,
            'icono':   n.icono_css,
            'fecha':   n.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        }
        for n in qs
    ]

    return JsonResponse({'no_leidas': no_leidas, 'notificaciones': items})


@require_POST
@login_required
def marcar_leida(request, pk):
    """Marca una notificación como leída."""
    updated = Notificacion.objects.filter(
        pk=pk, destinatario=request.user
    ).update(leida=True, fecha_lectura=timezone.now())
    return JsonResponse({'success': bool(updated)})


@require_POST
@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones del usuario como leídas."""
    Notificacion.objects.filter(
        destinatario=request.user, leida=False
    ).update(leida=True, fecha_lectura=timezone.now())
    return JsonResponse({'success': True})
