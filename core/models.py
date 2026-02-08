from django.db import models
from django.conf import settings

# Create your models here.


class BaseModel(models.Model):
    """
    Modelo base para auditoría - todos los modelos heredan de esta clase
    """
    activo = models.BooleanField(default=True, verbose_name="Activo", help_text="Estado activo/inactivo del registro")
    eliminado = models.BooleanField(default=False, verbose_name="Eliminado", help_text="Estado eliminado/no eliminado del registro")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación", help_text="Fecha y hora de creación del registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización", help_text="Fecha y hora de última actualización")
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_creados',
        verbose_name="Usuario de Creación",
        help_text="Usuario que creó el registro"
    )
    usuario_actualizacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_actualizados',
        verbose_name="Usuario de Actualización",
        help_text="Usuario que actualizó el registro por última vez"
    )

    class Meta:
        abstract = True

