"""
Modelos de Auditoría para el sistema TBA.

Siguiendo mejores prácticas, toda la información de auditoría 
(quién, cuándo, qué) se almacena en tablas separadas.
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditoriaAccion(models.TextChoices):
    """Tipos de acciones auditables."""
    CREAR = 'CREAR', 'Crear'
    ACTUALIZAR = 'ACTUALIZAR', 'Actualizar'
    ELIMINAR = 'ELIMINAR', 'Eliminar'
    ACTIVAR = 'ACTIVAR', 'Activar'
    DESACTIVAR = 'DESACTIVAR', 'Desactivar'
    RESTAURAR = 'RESTAURAR', 'Restaurar'
    OTRO = 'OTRO', 'Otro'


class RegistroAuditoria(models.Model):
    """
    Tabla de auditoría genérica que registra todas las acciones en el sistema.
    
    Utiliza GenericForeignKey para poder auditar cualquier modelo sin necesidad
    de campos FK en cada modelo individual.
    
    Campos principales:
    - content_type + object_id: Referencia genérica al objeto auditado
    - accion: Tipo de acción realizada (crear, actualizar, eliminar, etc.)
    - usuario: Usuario que realizó la acción
    - timestamp: Momento exacto de la acción
    - datos_anteriores: Estado del objeto antes del cambio (JSON)
    - datos_nuevos: Estado del objeto después del cambio (JSON)
    - ip_address: Dirección IP desde donde se realizó la acción
    - user_agent: Navegador/cliente utilizado
    """
    
    # Referencia genérica al objeto auditado
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de Contenido",
        help_text="Tipo de modelo auditado"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="ID del Objeto",
        help_text="ID del registro auditado"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Información de la acción
    accion = models.CharField(
        max_length=20,
        choices=AuditoriaAccion.choices,
        verbose_name="Acción",
        help_text="Tipo de acción realizada",
        db_index=True
    )
    
    # Usuario que realizó la acción
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acciones_auditoria',
        verbose_name="Usuario",
        help_text="Usuario que realizó la acción",
        db_index=True
    )
    
    # Timestamp de la acción
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora",
        help_text="Momento en que se realizó la acción",
        db_index=True
    )
    
    # Datos del cambio
    datos_anteriores = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Datos Anteriores",
        help_text="Estado del objeto antes del cambio (formato JSON)"
    )
    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Datos Nuevos",
        help_text="Estado del objeto después del cambio (formato JSON)"
    )
    
    # Información adicional de contexto
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP",
        help_text="Dirección IP desde donde se realizó la acción"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent",
        help_text="Información del navegador/cliente utilizado"
    )
    
    # Descripción adicional opcional
    descripcion = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción adicional de la acción"
    )
    
    class Meta:
        db_table = 'auditoria_registro'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['accion', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_accion_display()} - {self.content_type} #{self.object_id} por {self.usuario} ({self.timestamp})"
    
    @classmethod
    def registrar(cls, objeto, accion, usuario=None, request=None, datos_anteriores=None, datos_nuevos=None, descripcion=None):
        """
        Método helper para registrar una acción de auditoría.
        
        Args:
            objeto: El objeto sobre el cual se realizó la acción
            accion: Tipo de acción (usar AuditoriaAccion.*)
            usuario: Usuario que realizó la acción (opcional si se pasa request)
            request: Request HTTP (para extraer IP y user agent)
            datos_anteriores: Estado anterior del objeto (dict)
            datos_nuevos: Estado nuevo del objeto (dict)
            descripcion: Descripción adicional
        
        Returns:
            RegistroAuditoria: El registro de auditoría creado
        """
        # Extraer datos del request si existe
        ip_address = None
        user_agent = None
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if not usuario:
                usuario = request.user if request.user.is_authenticated else None
        
        # Crear el registro de auditoría
        return cls.objects.create(
            content_object=objeto,
            accion=accion,
            usuario=usuario,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            ip_address=ip_address,
            user_agent=user_agent,
            descripcion=descripcion
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Obtiene la IP real del cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditoriaSesion(models.Model):
    """
    Tabla para auditar sesiones de usuario (login, logout, intentos fallidos).
    
    Proporciona trazabilidad completa de accesos al sistema.
    """
    
    class TipoEvento(models.TextChoices):
        LOGIN_EXITOSO = 'LOGIN_EXITOSO', 'Login Exitoso'
        LOGIN_FALLIDO = 'LOGIN_FALLIDO', 'Login Fallido'
        LOGOUT = 'LOGOUT', 'Logout'
        CAMBIO_PASSWORD = 'CAMBIO_PASSWORD', 'Cambio de Contraseña'
        RESETEO_PASSWORD = 'RESETEO_PASSWORD', 'Reseteo de Contraseña'
        SESION_EXPIRADA = 'SESION_EXPIRADA', 'Sesión Expirada'
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sesiones_auditoria',
        verbose_name="Usuario",
        help_text="Usuario asociado al evento de sesión"
    )
    
    username = models.CharField(
        max_length=150,
        verbose_name="Nombre de Usuario",
        help_text="Username usado en el intento (guardado incluso si falla)",
        db_index=True
    )
    
    evento = models.CharField(
        max_length=20,
        choices=TipoEvento.choices,
        verbose_name="Tipo de Evento",
        help_text="Tipo de evento de sesión",
        db_index=True
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora",
        help_text="Momento del evento",
        db_index=True
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP",
        help_text="Dirección IP del cliente"
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent",
        help_text="Información del navegador/cliente"
    )
    
    exitoso = models.BooleanField(
        default=True,
        verbose_name="Exitoso",
        help_text="Indica si el evento fue exitoso"
    )
    
    razon_fallo = models.TextField(
        null=True,
        blank=True,
        verbose_name="Razón de Fallo",
        help_text="Motivo del fallo si no fue exitoso"
    )
    
    class Meta:
        db_table = 'auditoria_sesion'
        verbose_name = 'Auditoría de Sesión'
        verbose_name_plural = 'Auditorías de Sesiones'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['username', '-timestamp']),
            models.Index(fields=['evento', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_evento_display()} - {self.username} ({self.timestamp})"
