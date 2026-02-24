"""
Signals que generan notificaciones automáticas según eventos del sistema.

Eventos cubiertos:
  Solicitudes:
    - Nueva solicitud creada  → notifica a usuarios con 'aprobar_solicitudes'
    - Solicitud aprobada      → notifica al solicitante
    - Solicitud rechazada     → notifica al solicitante
    - Solicitud despachada    → notifica al solicitante

  Bajas de Inventario:
    - Nueva baja registrada   → notifica a usuarios con 'aprobar_baja'

  Órdenes de Compra:
    - Nueva orden creada      → notifica a usuarios con 'aprobar_ordencompra'
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


# ── Solicitudes ───────────────────────────────────────────────────────────────

def _conectar_solicitudes():
    try:
        from apps.solicitudes.models import Solicitud, HistorialSolicitud
    except ImportError:
        return

    @receiver(post_save, sender=Solicitud, weak=False,
              dispatch_uid='notif_solicitud_creada')
    def notif_solicitud_creada(sender, instance, created, **kwargs):
        if not created:
            return
        from .models import Notificacion
        try:
            url = reverse('solicitudes:detalle_solicitud', args=[instance.pk])
        except Exception:
            url = ''
        Notificacion.notificar_a_usuarios_con_permiso(
            codename='aprobar_solicitudes',
            tipo='SOLICITUD',
            titulo='Nueva solicitud pendiente de aprobación',
            mensaje=f'Se registró la solicitud {instance.numero}.',
            url=url,
        )

    @receiver(post_save, sender=HistorialSolicitud, weak=False,
              dispatch_uid='notif_solicitud_historial')
    def notif_solicitud_historial(sender, instance, created, **kwargs):
        if not created:
            return
        from .models import Notificacion
        estado = instance.estado_nuevo.nombre if instance.estado_nuevo else ''
        es_final = getattr(instance.estado_nuevo, 'es_final', False)
        try:
            url = reverse('solicitudes:detalle_solicitud', args=[instance.solicitud.pk])
        except Exception:
            url = ''

        if es_final:
            Notificacion.crear(
                destinatario=instance.solicitud.solicitante,
                tipo='SOLICITUD',
                titulo=f'Solicitud {instance.solicitud.numero} — {estado}',
                mensaje=instance.observaciones or f'Su solicitud cambió al estado {estado}.',
                url=url,
            )


_conectar_solicitudes()


# ── Bajas de Inventario ───────────────────────────────────────────────────────

def _conectar_bajas():
    try:
        from apps.bajas_inventario.models import BajaInventario
    except ImportError:
        return

    @receiver(post_save, sender=BajaInventario, weak=False,
              dispatch_uid='notif_baja_creada')
    def notif_baja_creada(sender, instance, created, **kwargs):
        if not created:
            return
        from .models import Notificacion
        try:
            url = reverse('bajas_inventario:detalle_baja', args=[instance.pk])
        except Exception:
            url = ''
        Notificacion.notificar_a_usuarios_con_permiso(
            codename='aprobar_baja',
            tipo='BAJA',
            titulo='Nueva baja de inventario registrada',
            mensaje=f'Se registró la baja {instance.numero} por {instance.motivo.nombre}.',
            url=url,
        )


_conectar_bajas()


# ── Órdenes de Compra ─────────────────────────────────────────────────────────

def _conectar_compras():
    try:
        from apps.compras.models import OrdenCompra
    except ImportError:
        return

    @receiver(post_save, sender=OrdenCompra, weak=False,
              dispatch_uid='notif_orden_creada')
    def notif_orden_creada(sender, instance, created, **kwargs):
        if not created:
            return
        from .models import Notificacion
        try:
            url = reverse('compras:detalle_orden', args=[instance.pk])
        except Exception:
            url = ''
        Notificacion.notificar_a_usuarios_con_permiso(
            codename='aprobar_ordencompra',
            tipo='COMPRA',
            titulo='Nueva orden de compra pendiente',
            mensaje=f'Se registró la orden {instance.numero} por {instance.solicitante.get_full_name() or instance.solicitante.username}.',
            url=url,
        )


_conectar_compras()
