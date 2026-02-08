from django.contrib import admin
from .models import (
    Proveedor, EstadoOrdenCompra, OrdenCompra, DetalleOrdenCompra, DetalleOrdenCompraArticulo
)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """Administrador del modelo Proveedor."""

    list_display = ['rut', 'razon_social', 'telefono', 'email', 'ciudad', 'activo']
    list_filter = ['activo', 'ciudad']
    search_fields = ['rut', 'razon_social', 'email']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    fieldsets = (
        ('Información Básica', {
            'fields': ('rut', 'razon_social')
        }),
        ('Contacto', {
            'fields': ('direccion', 'comuna', 'ciudad', 'telefono', 'email', 'sitio_web')
        }),
        ('Estado', {
            'fields': ('activo', 'eliminado')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EstadoOrdenCompra)
class EstadoOrdenCompraAdmin(admin.ModelAdmin):
    """Administrador del catálogo de estados de órdenes de compra."""

    list_display = ['codigo', 'nombre', 'color', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    fieldsets = (
        ('Información', {
            'fields': ('codigo', 'nombre', 'descripcion', 'color')
        }),
        ('Estado', {
            'fields': ('activo', 'eliminado')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


class DetalleOrdenCompraInline(admin.TabularInline):
    """Inline para detalles de activos en orden de compra."""

    model = DetalleOrdenCompra
    extra = 1
    readonly_fields = ['subtotal']
    fields = ['activo', 'cantidad', 'precio_unitario', 'descuento', 'subtotal', 'cantidad_recibida']


class DetalleOrdenCompraArticuloInline(admin.TabularInline):
    """Inline para detalles de artículos en orden de compra."""

    model = DetalleOrdenCompraArticulo
    extra = 1
    readonly_fields = ['subtotal']
    fields = ['articulo', 'cantidad', 'precio_unitario', 'descuento', 'subtotal', 'cantidad_recibida']


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    """Administrador del modelo Orden de Compra."""

    list_display = ['numero', 'fecha_orden', 'proveedor', 'estado', 'total', 'solicitante']
    list_filter = ['estado', 'fecha_orden', 'bodega_destino']
    search_fields = ['numero', 'proveedor__razon_social']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'subtotal', 'impuesto', 'total']
    inlines = [DetalleOrdenCompraArticuloInline, DetalleOrdenCompraInline]
    fieldsets = (
        ('Información General', {
            'fields': ('numero', 'fecha_orden', 'fecha_entrega_esperada', 'fecha_entrega_real')
        }),
        ('Proveedor y Destino', {
            'fields': ('proveedor', 'bodega_destino')
        }),
        ('Estado y Responsables', {
            'fields': ('estado', 'solicitante', 'aprobador')
        }),
        ('Montos', {
            'fields': ('subtotal', 'impuesto', 'descuento', 'total')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
