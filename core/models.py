from django.db import models, IntegrityError, transaction
from django.conf import settings

# Create your models here.


class AutoCodeMixin(models.Model):
    """
    Mixin para auto-generación de códigos secuenciales en el ``save()``.

    Cada modelo que lo herede debe declarar ``AUTO_CODE_PREFIX`` con un
    prefijo único de 3 letras mayúsculas.  El mixin genera automáticamente el
    código al crear instancias sin código asignado, usando un loop de reintento
    ante ``IntegrityError`` para tolerar inserciones concurrentes.

    Uso::

        class Ubicacion(AutoCodeMixin, BaseModel):
            AUTO_CODE_PREFIX = 'UBI'
            codigo = models.CharField(max_length=20, unique=True)
            ...

    El mixin DEBE ir **antes** de ``BaseModel`` en el MRO para que su
    ``save()`` se ejecute primero y llame correctamente a ``super().save()``.

    Atributos de clase configurables:

    * ``AUTO_CODE_PREFIX``     — prefijo de 3 letras (REQUERIDO, no debe repetirse entre modelos).
    * ``AUTO_CODE_FIELD``      — nombre del campo código (default: ``'codigo'``).
    * ``AUTO_CODE_LENGTH``     — cantidad de dígitos del correlativo (default: ``6``).
    * ``AUTO_CODE_MAX_RETRIES``— intentos máximos ante colisión (default: ``5``).
    """

    AUTO_CODE_PREFIX: str | None = None  # ej. 'UBI' — REQUERIDO
    AUTO_CODE_FIELD: str = "codigo"
    AUTO_CODE_LENGTH: int = 6
    AUTO_CODE_MAX_RETRIES: int = 5

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        campo = self.AUTO_CODE_FIELD
        valor_actual = getattr(self, campo, None)

        # Si el modelo no declaró prefijo o el código ya está establecido,
        # no intervenir — delegar directamente a la cadena MRO.
        if not self.AUTO_CODE_PREFIX or valor_actual:
            super().save(*args, **kwargs)
            return

        # El código está vacío: auto-generar con reintento ante colisión.
        from core.utils.business import generar_codigo_unico

        for attempt in range(self.AUTO_CODE_MAX_RETRIES):
            codigo = generar_codigo_unico(
                self.AUTO_CODE_PREFIX,
                self.__class__,
                campo,
                self.AUTO_CODE_LENGTH,
            )
            setattr(self, campo, codigo)
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return  # guardado exitoso
            except IntegrityError:
                if attempt == self.AUTO_CODE_MAX_RETRIES - 1:
                    # Agotamos los reintentos — propagar la excepción.
                    raise
                # Limpiar el código para que el próximo intento genere uno nuevo.
                setattr(self, campo, "")


class BaseModel(models.Model):
    """
    Modelo base para auditoría - todos los modelos heredan de esta clase.

    NOTA: Los campos usuario_creacion y usuario_actualizacion fueron eliminados.
    Ahora toda la auditoría se maneja automáticamente via apps.auditoria.
    El sistema registra quién, qué, cuándo, desde dónde (IP) y cómo (user agent)
    para cada creación, actualización y eliminación.
    """

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Estado activo/inactivo del registro",
    )
    eliminado = models.BooleanField(
        default=False,
        verbose_name="Eliminado",
        help_text="Estado eliminado/no eliminado del registro",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
        help_text="Fecha y hora de creación del registro",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización",
        help_text="Fecha y hora de última actualización",
    )

    class Meta:
        abstract = True
