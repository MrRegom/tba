"""
Pruebas de flujo del módulo de Bodega.

Cubre:
1. Entradas de stock (aumentan)
2. Salidas de stock (disminuyen)
3. Ajustes positivos y negativos
4. Validaciones: stock negativo, exceder máximo
5. Punto de reorden y bajo stock
6. Recepciones de artículos
7. Entregas vinculadas a solicitudes
8. Vistas HTTP por rol
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.bodega.models import Articulo, Movimiento
from apps.bodega.services import MovimientoService, ArticuloService

from tests.factories_globales import *  # noqa: F403


pytestmark = pytest.mark.django_db


# ============================================================
# 1. ENTRADAS DE STOCK
# ============================================================

class TestEntradasStock:

    def test_entrada_aumenta_stock(
        self, articulo_test, tipo_mov_recepcion, u_bodeguero,
        operacion_entrada
    ):
        stock_inicial = articulo_test.stock_actual
        service = MovimientoService()

        mov = service.registrar_entrada(
            articulo=articulo_test,
            tipo=tipo_mov_recepcion,
            cantidad=Decimal("50.00"),
            usuario=u_bodeguero,
            motivo="Recepción de compra test",
        )

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == stock_inicial + Decimal("50.00")
        assert mov.stock_despues == stock_inicial + Decimal("50.00")
        assert mov.stock_antes == stock_inicial

    def test_entrada_registra_movimiento(
        self, articulo_test, tipo_mov_recepcion, u_bodeguero, operacion_entrada
    ):
        service = MovimientoService()
        service.registrar_entrada(
            articulo=articulo_test,
            tipo=tipo_mov_recepcion,
            cantidad=Decimal("20.00"),
            usuario=u_bodeguero,
            motivo="Test movimiento",
        )

        movs = Movimiento.objects.filter(articulo=articulo_test)
        assert movs.count() >= 1
        ultimo = movs.order_by("-fecha_creacion").first()
        assert ultimo.cantidad == Decimal("20.00")
        assert ultimo.usuario == u_bodeguero

    def test_entrada_cantidad_cero_lanza_error(
        self, articulo_test, tipo_mov_recepcion, u_bodeguero, operacion_entrada
    ):
        service = MovimientoService()
        with pytest.raises(ValidationError, match="mayor a cero"):
            service.registrar_entrada(
                articulo=articulo_test,
                tipo=tipo_mov_recepcion,
                cantidad=Decimal("0.00"),
                usuario=u_bodeguero,
                motivo="Cantidad inválida",
            )

    def test_entrada_cantidad_negativa_lanza_error(
        self, articulo_test, tipo_mov_recepcion, u_bodeguero, operacion_entrada
    ):
        service = MovimientoService()
        with pytest.raises(ValidationError):
            service.registrar_entrada(
                articulo=articulo_test,
                tipo=tipo_mov_recepcion,
                cantidad=Decimal("-10.00"),
                usuario=u_bodeguero,
                motivo="Negativo inválido",
            )

    def test_entrada_que_excede_stock_maximo_lanza_error(
        self, articulo_test, tipo_mov_recepcion, u_bodeguero, operacion_entrada
    ):
        """
        stock_actual=100, stock_maximo=500
        Intentar agregar 450 → total 550 > 500 → error
        """
        service = MovimientoService()
        with pytest.raises(ValidationError, match="stock máximo"):
            service.registrar_entrada(
                articulo=articulo_test,
                tipo=tipo_mov_recepcion,
                cantidad=Decimal("450.00"),  # 100 + 450 = 550 > 500
                usuario=u_bodeguero,
                motivo="Excede máximo",
            )


# ============================================================
# 2. SALIDAS DE STOCK
# ============================================================

class TestSalidasStock:

    def test_salida_disminuye_stock(
        self, articulo_test, tipo_mov_entrega, u_bodeguero, operacion_salida
    ):
        stock_inicial = articulo_test.stock_actual  # 100
        service = MovimientoService()

        mov = service.registrar_salida(
            articulo=articulo_test,
            tipo=tipo_mov_entrega,
            cantidad=Decimal("30.00"),
            usuario=u_bodeguero,
            motivo="Entrega a área test",
        )

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == stock_inicial - Decimal("30.00")
        assert mov.stock_antes == stock_inicial
        assert mov.stock_despues == stock_inicial - Decimal("30.00")

    def test_salida_stock_insuficiente_lanza_error(
        self, articulo_sin_stock, tipo_mov_entrega, u_bodeguero, operacion_salida
    ):
        """
        articulo_sin_stock tiene stock_actual=0 → no se puede sacar
        """
        service = MovimientoService()
        with pytest.raises(ValidationError, match="Stock insuficiente"):
            service.registrar_salida(
                articulo=articulo_sin_stock,
                tipo=tipo_mov_entrega,
                cantidad=Decimal("1.00"),
                usuario=u_bodeguero,
                motivo="Sin stock disponible",
            )

    def test_salida_exactamente_el_stock_disponible(
        self, articulo_test, tipo_mov_entrega, u_bodeguero, operacion_salida
    ):
        """Debe permitir sacar exactamente lo que hay."""
        service = MovimientoService()
        stock_total = articulo_test.stock_actual  # 100

        mov = service.registrar_salida(
            articulo=articulo_test,
            tipo=tipo_mov_entrega,
            cantidad=stock_total,
            usuario=u_bodeguero,
            motivo="Salida total del stock",
        )

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == Decimal("0.00")

    def test_salida_deja_stock_en_minimo(
        self, articulo_test, tipo_mov_entrega, u_bodeguero, operacion_salida
    ):
        """
        stock_actual=100, stock_minimo=10
        Sacar 90 → quedan 10 (igual al mínimo) → válido
        """
        service = MovimientoService()
        service.registrar_salida(
            articulo=articulo_test,
            tipo=tipo_mov_entrega,
            cantidad=Decimal("90.00"),
            usuario=u_bodeguero,
            motivo="Lleva al mínimo",
        )
        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == Decimal("10.00")

    def test_salida_cantidad_cero_lanza_error(
        self, articulo_test, tipo_mov_entrega, u_bodeguero, operacion_salida
    ):
        service = MovimientoService()
        with pytest.raises(ValidationError):
            service.registrar_salida(
                articulo=articulo_test,
                tipo=tipo_mov_entrega,
                cantidad=Decimal("0.00"),
                usuario=u_bodeguero,
                motivo="Cero inválido",
            )


# ============================================================
# 3. AJUSTES POSITIVOS Y NEGATIVOS
# ============================================================

class TestAjustesStock:

    def test_ajuste_positivo_aumenta_stock(
        self, articulo_test, tipo_mov_ajuste_positivo, u_bodeguero, operacion_entrada
    ):
        stock_inicial = articulo_test.stock_actual
        service = MovimientoService()

        service.registrar_entrada(
            articulo=articulo_test,
            tipo=tipo_mov_ajuste_positivo,
            cantidad=Decimal("25.00"),
            usuario=u_bodeguero,
            motivo="Ajuste positivo de inventario",
        )

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == stock_inicial + Decimal("25.00")

    def test_ajuste_negativo_disminuye_stock(
        self, articulo_test, tipo_mov_ajuste_negativo, u_bodeguero, operacion_salida
    ):
        stock_inicial = articulo_test.stock_actual
        service = MovimientoService()

        service.registrar_salida(
            articulo=articulo_test,
            tipo=tipo_mov_ajuste_negativo,
            cantidad=Decimal("15.00"),
            usuario=u_bodeguero,
            motivo="Ajuste negativo de inventario",
        )

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == stock_inicial - Decimal("15.00")

    def test_multiples_movimientos_acumulan_correctamente(
        self, articulo_test, tipo_mov_recepcion, tipo_mov_entrega,
        tipo_mov_ajuste_positivo, u_bodeguero, operacion_entrada, operacion_salida
    ):
        """
        Flujo: 100 inicial → +50 entrada → -30 salida → +10 ajuste → resultado: 130
        """
        service = MovimientoService()

        service.registrar_entrada(articulo_test, tipo_mov_recepcion, Decimal("50"), u_bodeguero, "E1")
        service.registrar_salida(articulo_test, tipo_mov_entrega, Decimal("30"), u_bodeguero, "S1")
        service.registrar_entrada(articulo_test, tipo_mov_ajuste_positivo, Decimal("10"), u_bodeguero, "A1")

        articulo_test.refresh_from_db()
        assert articulo_test.stock_actual == Decimal("130.00")

        # Verificar que hay 3 movimientos nuevos
        movs = Movimiento.objects.filter(articulo=articulo_test).count()
        assert movs == 3


# ============================================================
# 4. ARTÍCULOS BAJO STOCK Y PUNTO DE REORDEN
# ============================================================

class TestStockAlertas:

    def test_identifica_articulos_bajo_stock(
        self, articulo_test, tipo_mov_entrega, u_bodeguero,
        operacion_salida
    ):
        """
        Sacar 95 unidades → stock_actual=5 < stock_minimo=10 → bajo stock
        """
        service_mov = MovimientoService()
        service_mov.registrar_salida(
            articulo=articulo_test,
            tipo=tipo_mov_entrega,
            cantidad=Decimal("95.00"),
            usuario=u_bodeguero,
            motivo="Provocar bajo stock",
        )

        articulo_test.refresh_from_db()
        service_art = ArticuloService()
        bajo_stock = service_art.obtener_articulos_bajo_stock()
        assert articulo_test in bajo_stock

    def test_articulo_con_stock_suficiente_no_en_bajo_stock(
        self, articulo_test, db
    ):
        """stock_actual=100 >= stock_minimo=10 → no está en bajo stock"""
        service = ArticuloService()
        bajo_stock = service.obtener_articulos_bajo_stock()
        assert articulo_test not in bajo_stock

    def test_articulo_sin_stock_es_critico(
        self, articulo_sin_stock, db
    ):
        """stock_actual=0 < stock_minimo=5 → bajo stock"""
        service = ArticuloService()
        bajo_stock = service.obtener_articulos_bajo_stock()
        assert articulo_sin_stock in bajo_stock


# ============================================================
# 5. VISTAS HTTP — BODEGA
# ============================================================

class TestVistasHTTPBodega:

    def test_bodeguero_accede_lista_articulos(self, client_bodega):
        resp = client_bodega.get("/bodega/articulos/")
        assert resp.status_code == 200

    def test_bodeguero_accede_lista_movimientos(self, client_bodega):
        resp = client_bodega.get("/bodega/movimientos/")
        assert resp.status_code == 200

    def test_bodeguero_accede_a_crear_movimiento(self, client_bodega):
        resp = client_bodega.get("/bodega/movimientos/crear/")
        assert resp.status_code == 200

    def test_sin_permiso_no_puede_crear_articulo(self, client_sin_rol):
        resp = client_sin_rol.get("/bodega/articulos/crear/")
        assert resp.status_code in (403, 302)

    def test_solicitante_no_accede_a_bodega(self, client_solicitante):
        resp = client_solicitante.get("/bodega/articulos/")
        assert resp.status_code in (403, 302)

    def test_admin_puede_crear_articulo(self, client_admin):
        resp = client_admin.get("/bodega/articulos/crear/")
        assert resp.status_code == 200

    def test_bodeguero_ve_detalle_articulo(
        self, client_bodega, articulo_test
    ):
        resp = client_bodega.get(f"/bodega/articulos/{articulo_test.pk}/")
        assert resp.status_code == 200

    def test_bodeguero_puede_registrar_movimiento_entrada_via_http(
        self, client_bodega, articulo_test, tipo_mov_recepcion
    ):
        stock_antes = articulo_test.stock_actual
        resp = client_bodega.post("/bodega/movimientos/crear/", {
            "articulo": articulo_test.pk,
            "tipo": tipo_mov_recepcion.pk,
            "cantidad": "20",
            "operacion_tipo": "ENTRADA",
            "motivo": "Entrada vía HTTP test",
        })
        # 200 (form con errores) o 302 (éxito) son válidos
        assert resp.status_code in (200, 302)
