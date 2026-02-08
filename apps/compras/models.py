from decimal import Decimal
from typing import Any

from django.contrib.auth.models import User
from django.core.validators import EmailValidator, MinValueValidator
from django.db import models

from apps.activos.models import Activo
from apps.bodega.models import Articulo, Bodega
from core.models import BaseModel


class Proveedor(BaseModel):
    """
    Modelo para gestionar proveedores del sistema de compras.

    Almacena información completa de proveedores incluyendo datos de contacto
    y condiciones comerciales.
    """

    rut = models.CharField(max_length=12, unique=True, verbose_name='RUT')
    razon_social = models.CharField(max_length=255, verbose_name='Razón Social')

    # Contacto
    direccion = models.CharField(max_length=255, verbose_name='Dirección')
    comuna = models.CharField(max_length=100, blank=True, null=True, verbose_name='Comuna')
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ciudad')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    email = models.EmailField(
        validators=[EmailValidator()],
        blank=True,
        null=True,
        verbose_name='Correo Electrónico'
    )
    sitio_web = models.URLField(blank=True, null=True, verbose_name='Sitio Web')

    class Meta:
        db_table = 'tba_compras_proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['razon_social']

    def __str__(self) -> str:
        return f"{self.rut} - {self.razon_social}"


class EstadoOrdenCompra(BaseModel):
    """
    Catálogo de estados de órdenes de compra.

    Define los diferentes estados que puede tener una orden de compra
    durante su ciclo de vida (ej: PENDIENTE, APROBADA, RECIBIDA).
    """

    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Color (Hex)'
    )

    class Meta:
        db_table = 'tba_compras_conf_estado_orden'
        verbose_name = 'Estado de Orden de Compra'
        verbose_name_plural = 'Estados de Órdenes de Compra'
        ordering = ['codigo']

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class OrdenCompra(BaseModel):
    """
    Modelo para gestionar órdenes de compra.

    Representa una orden de compra emitida a un proveedor, incluyendo
    información de fechas, montos, estado y relaciones con solicitudes.
    """

    numero = models.CharField(max_length=20, unique=True, verbose_name='Número de Orden')
    fecha_orden = models.DateField(verbose_name='Fecha de Orden')
    fecha_entrega_esperada = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha Entrega Esperada'
    )
    fecha_entrega_real = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha Entrega Real'
    )

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='ordenes_compra',
        verbose_name='Proveedor'
    )
    bodega_destino = models.ForeignKey(
        Bodega,
        on_delete=models.PROTECT,
        related_name='ordenes_compra',
        verbose_name='Bodega Destino'
    )
    estado = models.ForeignKey(
        EstadoOrdenCompra,
        on_delete=models.PROTECT,
        related_name='ordenes_compra',
        verbose_name='Estado'
    )
    solicitante = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ordenes_solicitadas',
        verbose_name='Solicitante'
    )
    aprobador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ordenes_aprobadas',
        verbose_name='Aprobador',
        blank=True,
        null=True
    )

    # Relación con solicitudes aprobadas
    solicitudes = models.ManyToManyField(
        'solicitudes.Solicitud',
        related_name='ordenes_compra',
        blank=True,
        verbose_name='Solicitudes Asociadas',
        help_text='Solicitudes aprobadas que originan esta orden de compra'
    )

    # Montos
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Subtotal'
    )
    impuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Impuesto (IVA)'
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Descuento'
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Total'
    )

    # Observaciones
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'tba_compras_orden'
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-fecha_orden', '-numero']
        permissions = [
            ('aprobar_ordencompra', 'Puede aprobar órdenes de compra'),
            ('rechazar_ordencompra', 'Puede rechazar órdenes de compra'),
            ('cerrar_ordencompra', 'Puede cerrar órdenes de compra'),
            ('anular_ordencompra', 'Puede anular órdenes de compra'),
            ('ver_todas_ordenescompra', 'Puede ver todas las órdenes de compra'),
            ('ver_reportes_compras', 'Puede ver reportes de compras'),
        ]

    def __str__(self) -> str:
        return f"OC-{self.numero} - {self.proveedor.razon_social}"


class DetalleOrdenCompra(BaseModel):
    """
    Modelo para el detalle de activos en una orden de compra.

    Representa cada línea de activos incluidos en una orden de compra,
    con información de cantidad, precios y seguimiento de recepción.
    """

    orden_compra = models.ForeignKey(
        OrdenCompra,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Orden de Compra'
    )
    activo = models.ForeignKey(
        Activo,
        on_delete=models.PROTECT,
        related_name='detalles_compra',
        verbose_name='Activo'
    )
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Precio Unitario'
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Descuento'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Subtotal'
    )
    cantidad_recibida = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Recibida'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'tba_compras_orden_detalle'
        verbose_name = 'Detalle de Orden de Compra'
        verbose_name_plural = 'Detalles de Órdenes de Compra'
        ordering = ['orden_compra', 'id']

    def __str__(self) -> str:
        return f"{self.orden_compra.numero} - {self.activo.codigo} ({self.cantidad})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Calcula el subtotal automáticamente antes de guardar."""
        precio = self.precio_unitario or Decimal('0')
        descuento = self.descuento or Decimal('0')
        self.subtotal = (Decimal(self.cantidad) * precio) - descuento
        super().save(*args, **kwargs)


class DetalleOrdenCompraArticulo(BaseModel):
    """
    Modelo para el detalle de artículos de bodega en una orden de compra.

    Representa cada línea de artículos de bodega incluidos en una orden de compra,
    con información de cantidad, precios y seguimiento de recepción.
    """

    orden_compra = models.ForeignKey(
        OrdenCompra,
        on_delete=models.CASCADE,
        related_name='detalles_articulos',
        verbose_name='Orden de Compra'
    )
    articulo = models.ForeignKey(
        Articulo,
        on_delete=models.PROTECT,
        related_name='detalles_compra',
        verbose_name='Artículo'
    )
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Precio Unitario'
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Descuento'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Subtotal'
    )
    cantidad_recibida = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Recibida'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'tba_compras_orden_detalle_articulo'
        verbose_name = 'Detalle Orden - Artículo'
        verbose_name_plural = 'Detalles Orden - Artículos'
        ordering = ['orden_compra', 'id']

    def __str__(self) -> str:
        return f"{self.orden_compra.numero} - {self.articulo.codigo} ({self.cantidad})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Calcula el subtotal automáticamente antes de guardar."""
        precio = self.precio_unitario or Decimal('0')
        descuento = self.descuento or Decimal('0')
        self.subtotal = (Decimal(self.cantidad) * precio) - descuento
        super().save(*args, **kwargs)
