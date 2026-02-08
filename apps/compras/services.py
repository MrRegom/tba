"""
Service Layer para el módulo de compras.

Contiene la lógica de negocio siguiendo el principio de
Single Responsibility (SOLID). Las operaciones críticas
usan transacciones atómicas para garantizar consistencia.
"""
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from core.utils import validar_rut, format_rut, generar_codigo_unico
from .models import (
    Proveedor, EstadoOrdenCompra, OrdenCompra,
    DetalleOrdenCompra, DetalleOrdenCompraArticulo
)
from .repositories import (
    ProveedorRepository, EstadoOrdenCompraRepository, OrdenCompraRepository,
    DetalleOrdenCompraRepository, DetalleOrdenCompraArticuloRepository
)
from apps.bodega.models import Bodega, Articulo
from apps.bodega.repositories import ArticuloRepository, BodegaRepository
from apps.activos.models import Activo
from apps.activos.repositories import ActivoRepository


# ==================== PROVEEDOR SERVICE ====================

class ProveedorService:
    """Service para lógica de negocio de Proveedores."""

    def __init__(self):
        self.proveedor_repo = ProveedorRepository()

    @transaction.atomic
    def crear_proveedor(
        self,
        rut: str,
        razon_social: str,
        direccion: str,
        **kwargs: Any
    ) -> Proveedor:
        """
        Crea un nuevo proveedor con validaciones.

        Args:
            rut: RUT del proveedor
            razon_social: Razón social
            direccion: Dirección
            **kwargs: Campos opcionales

        Returns:
            Proveedor: Proveedor creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar RUT
        if not validar_rut(rut):
            raise ValidationError({'rut': 'RUT inválido'})

        # Verificar RUT único
        if self.proveedor_repo.exists_by_rut(rut):
            raise ValidationError({'rut': 'Ya existe un proveedor con este RUT'})

        # Formatear RUT
        rut_formateado = format_rut(rut)

        # Crear proveedor
        proveedor = Proveedor.objects.create(
            rut=rut_formateado,
            razon_social=razon_social.strip(),
            direccion=direccion.strip(),
            nombre_fantasia=kwargs.get('nombre_fantasia', ''),
            giro=kwargs.get('giro', ''),
            comuna=kwargs.get('comuna', ''),
            ciudad=kwargs.get('ciudad', ''),
            telefono=kwargs.get('telefono', ''),
            email=kwargs.get('email', ''),
            sitio_web=kwargs.get('sitio_web', ''),
            condicion_pago=kwargs.get('condicion_pago', 'Contado'),
            dias_credito=kwargs.get('dias_credito', 0),
            activo=True
        )

        return proveedor

    @transaction.atomic
    def actualizar_proveedor(
        self,
        proveedor: Proveedor,
        **campos: Any
    ) -> Proveedor:
        """
        Actualiza un proveedor existente.

        Args:
            proveedor: Proveedor a actualizar
            **campos: Campos a actualizar

        Returns:
            Proveedor: Proveedor actualizado

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Si se actualiza el RUT, validar
        if 'rut' in campos:
            nuevo_rut = campos['rut']
            if not validar_rut(nuevo_rut):
                raise ValidationError({'rut': 'RUT inválido'})

            # Verificar que no exista otro con ese RUT
            if self.proveedor_repo.exists_by_rut(nuevo_rut, exclude_id=proveedor.id):
                raise ValidationError({'rut': 'Ya existe otro proveedor con este RUT'})

            campos['rut'] = format_rut(nuevo_rut)

        # Actualizar campos
        for campo, valor in campos.items():
            setattr(proveedor, campo, valor)

        proveedor.save()
        return proveedor

    @transaction.atomic
    def eliminar_proveedor(self, proveedor: Proveedor) -> None:
        """
        Elimina (soft delete) un proveedor.

        Args:
            proveedor: Proveedor a eliminar

        Raises:
            ValidationError: Si el proveedor tiene órdenes asociadas
        """
        # Verificar que no tenga órdenes de compra
        orden_repo = OrdenCompraRepository()
        ordenes = orden_repo.filter_by_proveedor(proveedor)

        if ordenes.exists():
            raise ValidationError(
                'No se puede eliminar el proveedor porque tiene órdenes de compra asociadas'
            )

        # Soft delete
        proveedor.eliminado = True
        proveedor.activo = False
        proveedor.save()


# ==================== ORDEN COMPRA SERVICE ====================

class OrdenCompraService:
    """Service para lógica de negocio de Órdenes de Compra."""

    def __init__(self):
        self.orden_repo = OrdenCompraRepository()
        self.estado_repo = EstadoOrdenCompraRepository()
        self.proveedor_repo = ProveedorRepository()
        self.bodega_repo = BodegaRepository()

    def calcular_totales(
        self,
        subtotal: Decimal,
        tasa_impuesto: Decimal = Decimal('0.19'),  # 19% IVA Chile
        descuento: Decimal = Decimal('0')
    ) -> Dict[str, Decimal]:
        """
        Calcula los totales de una orden de compra.

        Args:
            subtotal: Subtotal sin impuestos
            tasa_impuesto: Tasa de impuesto (default: 19%)
            descuento: Descuento aplicado

        Returns:
            Dict con 'subtotal', 'impuesto', 'descuento', 'total'
        """
        impuesto = (subtotal - descuento) * tasa_impuesto
        total = subtotal - descuento + impuesto

        return {
            'subtotal': subtotal,
            'impuesto': impuesto,
            'descuento': descuento,
            'total': total
        }

    @transaction.atomic
    def crear_orden_compra(
        self,
        proveedor: Proveedor,
        bodega_destino: Bodega,
        solicitante: User,
        fecha_orden: date,
        numero: Optional[str] = None,
        **kwargs: Any
    ) -> OrdenCompra:
        """
        Crea una nueva orden de compra.

        Args:
            proveedor: Proveedor
            bodega_destino: Bodega de destino
            solicitante: Usuario solicitante
            fecha_orden: Fecha de la orden
            numero: Número de orden (opcional, se genera automático)
            **kwargs: Campos opcionales

        Returns:
            OrdenCompra: Orden creada

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar proveedor activo
        if not proveedor.activo:
            raise ValidationError({'proveedor': 'El proveedor no está activo'})

        # Generar número si no se proporciona
        if not numero:
            numero = generar_codigo_unico('OC', OrdenCompra, 'numero', longitud=8)
        else:
            # Verificar que el número no exista
            if self.orden_repo.exists_by_numero(numero):
                raise ValidationError({'numero': 'Ya existe una orden con este número'})

        # Obtener estado inicial
        estado_inicial = self.estado_repo.get_inicial()
        if not estado_inicial:
            raise ValidationError('No se ha configurado un estado inicial para órdenes de compra')

        # Crear orden
        orden = OrdenCompra.objects.create(
            numero=numero,
            fecha_orden=fecha_orden,
            proveedor=proveedor,
            bodega_destino=bodega_destino,
            estado=estado_inicial,
            solicitante=solicitante,
            aprobador=kwargs.get('aprobador'),
            fecha_entrega_esperada=kwargs.get('fecha_entrega_esperada'),
            subtotal=Decimal('0'),
            impuesto=Decimal('0'),
            descuento=kwargs.get('descuento', Decimal('0')),
            total=Decimal('0'),
            observaciones=kwargs.get('observaciones', ''),
            notas_internas=kwargs.get('notas_internas', '')
        )

        return orden

    @transaction.atomic
    def cambiar_estado(
        self,
        orden: OrdenCompra,
        nuevo_estado: EstadoOrdenCompra,
        usuario: User
    ) -> OrdenCompra:
        """
        Cambia el estado de una orden de compra.

        Args:
            orden: Orden a actualizar
            nuevo_estado: Nuevo estado
            usuario: Usuario que realiza el cambio

        Returns:
            OrdenCompra: Orden actualizada

        Raises:
            ValidationError: Si el cambio no es válido
        """
        # Validar que el estado actual permita edición
        # Estados finales: RECIBIDA, CANCELADA, CERRADA
        estados_finales = ['RECIBIDA', 'CANCELADA', 'CERRADA']
        if orden.estado.codigo in estados_finales:
            raise ValidationError(f'No se puede cambiar el estado de una orden en estado {orden.estado.nombre}')

        # Actualizar estado
        orden.estado = nuevo_estado
        orden.save()

        return orden

    @transaction.atomic
    def recalcular_totales(self, orden: OrdenCompra) -> OrdenCompra:
        """
        Recalcula los totales de una orden basándose en sus detalles.

        Args:
            orden: Orden de compra

        Returns:
            OrdenCompra: Orden actualizada
        """
        # Sumar subtotales de detalles de activos
        detalle_repo = DetalleOrdenCompraRepository()
        detalles_activos = detalle_repo.filter_by_orden(orden)
        subtotal_activos = sum(d.subtotal for d in detalles_activos)

        # Sumar subtotales de detalles de artículos
        detalle_articulo_repo = DetalleOrdenCompraArticuloRepository()
        detalles_articulos = detalle_articulo_repo.filter_by_orden(orden)
        subtotal_articulos = sum(d.subtotal for d in detalles_articulos)

        # Subtotal total
        subtotal_total = subtotal_activos + subtotal_articulos

        # Calcular totales
        totales = self.calcular_totales(subtotal_total, descuento=orden.descuento)

        # Actualizar orden
        orden.subtotal = totales['subtotal']
        orden.impuesto = totales['impuesto']
        orden.total = totales['total']
        orden.save()

        return orden
