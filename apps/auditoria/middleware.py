"""
Middleware para auditoría automática.

Este middleware captura automáticamente las señales de Django y registra
las acciones de creación, actualización y eliminación de modelos.
"""
from django.utils.deprecation import MiddlewareMixin
from django.db.models.signals import post_save, post_delete
from threading import local

# Thread-local storage para el request actual
_thread_locals = local()


def get_current_request():
    """Obtiene el request actual del thread local."""
    return getattr(_thread_locals, 'request', None)


class AuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware que almacena el request actual en thread-local storage.
    
    Esto permite que las señales de los modelos accedan al request
    para obtener el usuario, IP y user agent sin necesidad de
    pasar el request explícitamente.
    """
    
    def process_request(self, request):
        """Almacena el request en thread-local."""
        _thread_locals.request = request
        return None
    
    def process_response(self, request, response):
        """Limpia el thread-local después de procesar el request."""
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response
    
    def process_exception(self, request, exception):
        """Limpia el thread-local en caso de excepción."""
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return None


def registrar_auditoria_automatica(sender, instance, created, **kwargs):
    """
    Handler de señal que registra automáticamente creaciones y actualizaciones.
    
    Se conecta automáticamente a todos los modelos que hereden de BaseModel.
    """
    from apps.auditoria.models import RegistroAuditoria, AuditoriaAccion
    
    # Ignorar modelos de auditoría para evitar recursión
    if sender.__name__ in ['RegistroAuditoria', 'AuditoriaSesion']:
        return
    
    # Ignorar modelos de Django internos
    if sender._meta.app_label in ['admin', 'auth', 'contenttypes', 'sessions']:
        return
    
    request = get_current_request()
    accion = AuditoriaAccion.CREAR if created else AuditoriaAccion.ACTUALIZAR
    
    # Obtener el estado actual del objeto
    datos_nuevos = {}
    for field in instance._meta.fields:
        if not field.name.startswith('_'):
            try:
                valor = getattr(instance, field.name)
                # Convertir a string para serialización JSON
                if hasattr(valor, 'pk'):
                    datos_nuevos[field.name] = f"{valor.__class__.__name__}:{valor.pk}"
                else:
                    datos_nuevos[field.name] = str(valor) if valor is not None else None
            except:
                pass
    
    #  Registrar en la auditoría
    try:
        RegistroAuditoria.registrar(
            objeto=instance,
            accion=accion,
            request=request,
            datos_nuevos=datos_nuevos,
            descripcion=f"{'Creación' if created else 'Actualización'} de {sender.__name__}"
        )
    except Exception as e:
        # No fallar la operación principal si falla la auditoría
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al registrar auditoría: {e}")


def registrar_eliminacion_automatica(sender, instance, **kwargs):
    """
    Handler de señal que registra automáticamente eliminaciones.
    
    Se conecta automáticamente a todos los modelos que hereden de BaseModel.
    """
    from apps.auditoria.models import RegistroAuditoria, AuditoriaAccion
    
    # Ignorar modelos de auditoría
    if sender.__name__ in ['RegistroAuditoria', 'AuditoriaSesion']:
        return
    
    # Ignorar modelos de Django internos
    if sender._meta.app_label in ['admin', 'auth', 'contenttypes', 'sessions']:
        return
    
    request = get_current_request()
    
    # Obtener el estado del objeto antes de eliminar
    datos_anteriores = {}
    for field in instance._meta.fields:
        if not field.name.startswith('_'):
            try:
                valor = getattr(instance, field.name)
                if hasattr(valor, 'pk'):
                    datos_anteriores[field.name] = f"{valor.__class__.__name__}:{valor.pk}"
                else:
                    datos_anteriores[field.name] = str(valor) if valor is not None else None
            except:
                pass
    
    # Registrar en la auditoría
    try:
        RegistroAuditoria.registrar(
            objeto=instance,
            accion=AuditoriaAccion.ELIMINAR,
            request=request,
            datos_anteriores=datos_anteriores,
            descripcion=f"Eliminación de {sender.__name__}"
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al registrar auditoría de eliminación: {e}")


def activar_auditoria_automatica():
    """
    Activa la auditoría automática conectando las señales.
    
    Debe ser llamado en apps.py de la app auditoria.
    """
    from django.apps import apps
    from core.models import BaseModel
    
    # Conectar señales para todos los modelos que hereden de BaseModel
    for model in apps.get_models():
        if issubclass(model, BaseModel) and model is not BaseModel:
            post_save.connect(registrar_auditoria_automatica, sender=model, weak=False)
            post_delete.connect(registrar_eliminacion_automatica, sender=model, weak=False)
