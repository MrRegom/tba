"""
Repository Pattern para el módulo de compras.

Separa la lógica de acceso a datos de la lógica de negocio,
siguiendo el principio de Inversión de Dependencias (SOLID).
"""
from typing import Optional
from decimal import Decimal
from django.db.models import QuerySet, Q, Sum
from django.contrib.auth.models import User
from .models import (
    Proveedor, EstadoOrdenCompra, OrdenCompra,
    DetalleOrdenCompra, DetalleOrdenCompraArticulo
)
from apps.bodega.models import Bodega, Articulo
from apps.activos.models import Activo


# ==================== PROVEEDOR REPOSITORY ====================

class ProveedorRepository:
    """Repository para gestionar acceso a datos de Proveedor."""

    @staticmethod
    def get_all() -> QuerySet[Proveedor]:
        """Retorna todos los proveedores no eliminados."""
        return Proveedor.objects.filter(eliminado=False).order_by('razon_social')

    @staticmethod
    def get_active() -> QuerySet[Proveedor]:
        """Retorna solo proveedores activos y no eliminados."""
        return Proveedor.objects.filter(
            activo=True, eliminado=False
        ).order_by('razon_social')

    @staticmethod
    def get_by_id(proveedor_id: int) -> Optional[Proveedor]:
        """Obtiene un proveedor por su ID."""
        try:
            return Proveedor.objects.get(id=proveedor_id, eliminado=False)
        except Proveedor.DoesNotExist:
            return None

    @staticmethod
    def get_by_rut(rut: str) -> Optional[Proveedor]:
        """Obtiene un proveedor por su RUT."""
        try:
            return Proveedor.objects.get(rut=rut, eliminado=False)
        except Proveedor.DoesNotExist:
            return None

    @staticmethod
    def search(query: str) -> QuerySet[Proveedor]:
        """Búsqueda de proveedores por RUT, razón social o nombre fantasía."""
        return Proveedor.objects.filter(
            Q(rut__icontains=query) |
            Q(razon_social__icontains=query) |
            Q(nombre_fantasia__icontains=query),
            eliminado=False
        ).order_by('razon_social')

    @staticmethod
    def exists_by_rut(rut: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe un proveedor con el RUT dado."""
        queryset = Proveedor.objects.filter(rut=rut)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()


# ==================== ESTADO ORDEN COMPRA REPOSITORY ====================

class EstadoOrdenCompraRepository:
    """Repository para gestionar estados de órdenes de compra."""

    @staticmethod
    def get_all() -> QuerySet[EstadoOrdenCompra]:
        """Retorna todos los estados activos."""
        return EstadoOrdenCompra.objects.filter(activo=True).order_by('codigo')

    @staticmethod
    def get_by_id(estado_id: int) -> Optional[EstadoOrdenCompra]:
        """Obtiene un estado por su ID."""
        try:
            return EstadoOrdenCompra.objects.get(id=estado_id, activo=True)
        except EstadoOrdenCompra.DoesNotExist:
            return None

    @staticmethod
    def get_by_codigo(codigo: str) -> Optional[EstadoOrdenCompra]:
        """Obtiene un estado por su código."""
        try:
            return EstadoOrdenCompra.objects.get(codigo=codigo, activo=True)
        except EstadoOrdenCompra.DoesNotExist:
            return None

    @staticmethod
    def get_inicial() -> Optional[EstadoOrdenCompra]:
        """Obtiene el estado inicial para nuevas órdenes de compra (PENDIENTE)."""
        try:
            return EstadoOrdenCompra.objects.get(
                codigo='PENDIENTE',
                activo=True
            )
        except EstadoOrdenCompra.DoesNotExist:
            # Fallback: retornar el primer estado activo si no existe PENDIENTE
            return EstadoOrdenCompra.objects.filter(
                activo=True
            ).order_by('codigo').first()


# ==================== ORDEN COMPRA REPOSITORY ====================

class OrdenCompraRepository:
    """Repository para gestionar órdenes de compra."""

    @staticmethod
    def get_all() -> QuerySet[OrdenCompra]:
        """Retorna todas las órdenes con relaciones optimizadas."""
        return OrdenCompra.objects.select_related(
            'proveedor', 'bodega_destino', 'estado', 'solicitante', 'aprobador'
        ).order_by('-fecha_orden', '-numero')

    @staticmethod
    def get_by_id(orden_id: int) -> Optional[OrdenCompra]:
        """Obtiene una orden por su ID."""
        try:
            return OrdenCompra.objects.select_related(
                'proveedor', 'bodega_destino', 'estado', 'solicitante', 'aprobador'
            ).get(id=orden_id)
        except OrdenCompra.DoesNotExist:
            return None

    @staticmethod
    def get_by_numero(numero: str) -> Optional[OrdenCompra]:
        """Obtiene una orden por su número."""
        try:
            return OrdenCompra.objects.select_related(
                'proveedor', 'bodega_destino', 'estado', 'solicitante', 'aprobador'
            ).get(numero=numero)
        except OrdenCompra.DoesNotExist:
            return None

    @staticmethod
    def filter_by_proveedor(proveedor: Proveedor) -> QuerySet[OrdenCompra]:
        """Retorna órdenes de un proveedor específico."""
        return OrdenCompra.objects.filter(
            proveedor=proveedor
        ).select_related(
            'bodega_destino', 'estado', 'solicitante'
        ).order_by('-fecha_orden')

    @staticmethod
    def filter_by_estado(estado: EstadoOrdenCompra) -> QuerySet[OrdenCompra]:
        """Retorna órdenes en un estado específico."""
        return OrdenCompra.objects.filter(
            estado=estado
        ).select_related(
            'proveedor', 'bodega_destino', 'solicitante'
        ).order_by('-fecha_orden')

    @staticmethod
    def filter_by_solicitante(solicitante: User) -> QuerySet[OrdenCompra]:
        """Retorna órdenes solicitadas por un usuario."""
        return OrdenCompra.objects.filter(
            solicitante=solicitante
        ).select_related(
            'proveedor', 'bodega_destino', 'estado'
        ).order_by('-fecha_orden')

    @staticmethod
    def exists_by_numero(numero: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe una orden con el número dado."""
        queryset = OrdenCompra.objects.filter(numero=numero)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    @staticmethod
    def search(query: str) -> QuerySet[OrdenCompra]:
        """Búsqueda de órdenes por número o proveedor."""
        return OrdenCompra.objects.filter(
            Q(numero__icontains=query) |
            Q(proveedor__razon_social__icontains=query)
        ).select_related(
            'proveedor', 'bodega_destino', 'estado', 'solicitante'
        ).order_by('-fecha_orden')


# ==================== DETALLE ORDEN COMPRA REPOSITORIES ====================

class DetalleOrdenCompraRepository:
    """Repository para detalles de órdenes de compra (Activos)."""

    @staticmethod
    def filter_by_orden(orden: OrdenCompra) -> QuerySet[DetalleOrdenCompra]:
        """Retorna detalles de una orden específica."""
        return DetalleOrdenCompra.objects.filter(
            orden_compra=orden,
            eliminado=False
        ).select_related('activo').order_by('id')

    @staticmethod
    def get_by_id(detalle_id: int) -> Optional[DetalleOrdenCompra]:
        """Obtiene un detalle por su ID."""
        try:
            return DetalleOrdenCompra.objects.select_related(
                'orden_compra', 'activo'
            ).get(id=detalle_id, eliminado=False)
        except DetalleOrdenCompra.DoesNotExist:
            return None


class DetalleOrdenCompraArticuloRepository:
    """Repository para detalles de órdenes de compra (Artículos)."""

    @staticmethod
    def filter_by_orden(orden: OrdenCompra) -> QuerySet[DetalleOrdenCompraArticulo]:
        """Retorna detalles de una orden específica."""
        return DetalleOrdenCompraArticulo.objects.filter(
            orden_compra=orden,
            eliminado=False
        ).select_related('articulo').order_by('id')

    @staticmethod
    def get_by_id(detalle_id: int) -> Optional[DetalleOrdenCompraArticulo]:
        """Obtiene un detalle por su ID."""
        try:
            return DetalleOrdenCompraArticulo.objects.select_related(
                'orden_compra', 'articulo'
            ).get(id=detalle_id, eliminado=False)
        except DetalleOrdenCompraArticulo.DoesNotExist:
            return None
