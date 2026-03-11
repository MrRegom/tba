"""
Pruebas de flujo del módulo de Compras.

Cubre:
1. Creación de órdenes de compra
2. Cambio de estados de la orden
3. Recepciones de artículos (vinculada a OC)
4. Recepciones sin OC
5. Vistas HTTP por rol
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from apps.compras.models import OrdenCompra, DetalleOrdenCompra, DetalleOrdenCompraArticulo
from apps.compras.services import OrdenCompraService

from tests.factories_globales import *  # noqa: F403


pytestmark = pytest.mark.django_db


# ============================================================
# HELPER
# ============================================================

def crear_orden_compra(
    proveedor, bodega, estado, solicitante
) -> OrdenCompra:
    return OrdenCompra.objects.create(
        numero=f"OC-TEST-{OrdenCompra.objects.count() + 1:04d}",
        fecha_orden=date.today(),
        fecha_entrega_esperada=date.today() + timedelta(days=7),
        proveedor=proveedor,
        bodega_destino=bodega,
        estado=estado,
        solicitante=solicitante,
        subtotal=Decimal("10000.00"),
        impuesto=Decimal("1900.00"),
        descuento=Decimal("0.00"),
        total=Decimal("11900.00"),
        observaciones="OC de prueba de integración",
        activo=True,
        eliminado=False,
    )


# ============================================================
# 1. CREACIÓN DE ORDEN DE COMPRA
# ============================================================

class TestCreacionOrdenCompra:

    def test_crear_orden_compra_estado_pendiente(
        self, proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero
    ):
        oc = crear_orden_compra(
            proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero
        )
        assert oc.pk is not None
        assert oc.estado.codigo == "PENDIENTE"
        assert oc.proveedor == proveedor_test
        assert oc.total == Decimal("11900.00")

    def test_numero_orden_es_unico(
        self, proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero
    ):
        oc1 = crear_orden_compra(proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero)
        oc2 = crear_orden_compra(proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero)
        assert oc1.numero != oc2.numero

    def test_totales_calculados_correctamente(
        self, proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero
    ):
        oc = crear_orden_compra(proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero)
        # total = subtotal + impuesto - descuento = 10000 + 1900 - 0 = 11900
        assert oc.total == oc.subtotal + oc.impuesto - oc.descuento


# ============================================================
# 2. CAMBIO DE ESTADOS DE ORDEN DE COMPRA
# ============================================================

class TestEstadosOrdenCompra:

    def test_orden_puede_cambiar_a_aprobada(
        self, proveedor_test, bodega_test,
        estado_orden_pendiente, estado_orden_aprobada, u_bodeguero, u_admin
    ):
        oc = crear_orden_compra(proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero)
        service = OrdenCompraService()
        oc = service.cambiar_estado(
            orden=oc,
            nuevo_estado=estado_orden_aprobada,
            usuario=u_admin,
        )
        oc.refresh_from_db()
        assert oc.estado.codigo == "APROBADA"

    def test_orden_puede_cambiar_a_recibida(
        self, proveedor_test, bodega_test,
        estado_orden_aprobada, estado_orden_recibida, u_bodeguero, u_admin
    ):
        oc = crear_orden_compra(proveedor_test, bodega_test, estado_orden_aprobada, u_bodeguero)
        service = OrdenCompraService()
        oc = service.cambiar_estado(
            orden=oc,
            nuevo_estado=estado_orden_recibida,
            usuario=u_admin,
        )
        oc.refresh_from_db()
        assert oc.estado.codigo == "RECIBIDA"

    def test_flujo_completo_orden_compra(
        self, proveedor_test, bodega_test,
        estado_orden_pendiente, estado_orden_aprobada, estado_orden_recibida,
        u_bodeguero, u_admin
    ):
        """
        PENDIENTE → APROBADA → RECIBIDA
        """
        oc = crear_orden_compra(proveedor_test, bodega_test, estado_orden_pendiente, u_bodeguero)
        service = OrdenCompraService()

        oc = service.cambiar_estado(oc, estado_orden_aprobada, u_admin)
        assert oc.estado.codigo == "APROBADA"

        oc = service.cambiar_estado(oc, estado_orden_recibida, u_admin)
        assert oc.estado.codigo == "RECIBIDA"


# ============================================================
# 3. RECEPCIÓN DE ARTÍCULOS
# ============================================================

class TestRecepcionArticulos:

    def test_crear_recepcion_articulo_con_orden(
        self, proveedor_test, bodega_test,
        estado_orden_aprobada, estado_recepcion_inicial,
        tipo_recepcion_con_orden, u_bodeguero
    ):
        from apps.bodega.models import RecepcionArticulo

        oc = crear_orden_compra(proveedor_test, bodega_test, estado_orden_aprobada, u_bodeguero)

        recepcion = RecepcionArticulo.objects.create(
            numero="RART-TEST-001",
            bodega=bodega_test,
            estado=estado_recepcion_inicial,
            recibido_por=u_bodeguero,
            orden_compra=oc,
            tipo=tipo_recepcion_con_orden,
            documento_referencia="GUIA-TEST-12345",
            observaciones="Recepción de prueba",
            activo=True,
            eliminado=False,
        )

        assert recepcion.pk is not None
        assert recepcion.estado.codigo == "BORRADOR"
        assert recepcion.orden_compra == oc

    def test_crear_recepcion_sin_orden(
        self, bodega_test, estado_recepcion_inicial,
        tipo_recepcion_sin_orden, u_bodeguero
    ):
        from apps.bodega.models import RecepcionArticulo

        recepcion = RecepcionArticulo.objects.create(
            numero="RART-TEST-002",
            bodega=bodega_test,
            estado=estado_recepcion_inicial,
            recibido_por=u_bodeguero,
            tipo=tipo_recepcion_sin_orden,
            documento_referencia="GUIA-DIRECTA-001",
            observaciones="Recepción directa sin orden",
            activo=True,
            eliminado=False,
        )

        assert recepcion.pk is not None
        assert recepcion.orden_compra is None

    def test_recepcion_y_aumento_de_stock(
        self, proveedor_test, bodega_test,
        estado_orden_aprobada, estado_recepcion_inicial, estado_recepcion_completada,
        tipo_recepcion_con_orden, tipo_mov_recepcion,
        articulo_test, u_bodeguero, operacion_entrada
    ):
        """
        Al recepcionar artículos, el stock debe aumentar.
        """
        from apps.bodega.models import RecepcionArticulo, DetalleRecepcionArticulo
        from apps.bodega.services import MovimientoService

        stock_antes = articulo_test.stock_actual
        oc = crear_orden_compra(proveedor_test, bodega_test, estado_orden_aprobada, u_bodeguero)

        recepcion = RecepcionArticulo.objects.create(
            numero="RART-TEST-003",
            bodega=bodega_test,
            estado=estado_recepcion_inicial,
            recibido_por=u_bodeguero,
            orden_compra=oc,
            tipo=tipo_recepcion_con_orden,
            activo=True, eliminado=False,
        )

        DetalleRecepcionArticulo.objects.create(
            recepcion=recepcion,
            articulo=articulo_test,
            cantidad=30,
            eliminado=False,
        )

        # Registrar entrada de stock manualmente (simula confirmación de recepción)
        service = MovimientoService()
        service.registrar_entrada(
            articulo=articulo_test,
            tipo=tipo_mov_recepcion,
            cantidad=Decimal("30.00"),
            usuario=u_bodeguero,
            motivo=f"Recepción {recepcion.numero}",
        )

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == stock_antes + Decimal("30.00")


# ============================================================
# 4. VISTAS HTTP — COMPRAS
# ============================================================

class TestVistasHTTPCompras:

    def test_admin_accede_a_lista_ordenes(self, client_admin):
        resp = client_admin.get("/compras/ordenes/")
        assert resp.status_code == 200

    def test_admin_accede_a_crear_orden(self, client_admin):
        resp = client_admin.get("/compras/ordenes/crear/")
        assert resp.status_code == 200

    def test_sin_permiso_no_accede_a_compras(self, client_sin_rol):
        resp = client_sin_rol.get("/compras/ordenes/")
        assert resp.status_code in (403, 302)

    def test_solicitante_no_accede_a_compras(self, client_solicitante):
        resp = client_solicitante.get("/compras/ordenes/")
        assert resp.status_code in (403, 302)

    def test_admin_accede_a_proveedores(self, client_admin):
        resp = client_admin.get("/compras/proveedores/")
        assert resp.status_code == 200

    def test_admin_accede_a_recepciones_articulos(self, client_admin):
        resp = client_admin.get("/bodega/recepciones-articulos/")
        assert resp.status_code == 200
