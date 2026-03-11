"""
Pruebas de flujo del módulo de Activos / Inventario.

Cubre:
1. Registro de activos
2. Movimientos de activos (traslados)
3. Estados de activos
4. Vistas HTTP por rol
"""
import pytest
from decimal import Decimal

from apps.activos.models import Activo, MovimientoActivo

from tests.factories_globales import *  # noqa: F403


pytestmark = pytest.mark.django_db


# ============================================================
# 1. REGISTRO DE ACTIVOS
# ============================================================

class TestRegistroActivos:

    def test_activo_se_crea_correctamente(
        self, activo_test, estado_activo_disponible, categoria_activo
    ):
        assert activo_test.pk is not None
        assert activo_test.estado == estado_activo_disponible
        assert activo_test.categoria == categoria_activo
        assert activo_test.activo is True
        assert activo_test.eliminado is False

    def test_activo_genera_codigo_barras_automatico(
        self, activo_test
    ):
        """El modelo auto-genera codigo_barras si no se provee."""
        assert activo_test.codigo_barras is not None
        assert len(activo_test.codigo_barras) > 0

    def test_activo_codigo_es_unico(
        self, categoria_activo, estado_activo_disponible
    ):
        a1 = Activo.objects.create(
            codigo="ACT-UNICO-001",
            nombre="Activo Único 1",
            categoria=categoria_activo,
            estado=estado_activo_disponible,
            activo=True, eliminado=False,
        )
        with pytest.raises(Exception):
            Activo.objects.create(
                codigo="ACT-UNICO-001",  # Mismo código → error único
                nombre="Activo Único Duplicado",
                categoria=categoria_activo,
                estado=estado_activo_disponible,
                activo=True, eliminado=False,
            )

    def test_activo_soft_delete(self, activo_test):
        """Soft delete: no elimina físicamente, marca eliminado=True."""
        activo_test.eliminado = True
        activo_test.activo = False
        activo_test.save()

        activo_test.refresh_from_db()
        assert activo_test.eliminado is True
        assert activo_test.activo is False

        # Aún existe en la DB
        assert Activo.objects.filter(pk=activo_test.pk).exists()


# ============================================================
# 2. ESTADOS DE ACTIVOS
# ============================================================

class TestEstadosActivos:

    def test_activo_disponible_tiene_estado_inicial(
        self, activo_test, estado_activo_disponible
    ):
        assert activo_test.estado == estado_activo_disponible
        assert activo_test.estado.es_inicial is True

    def test_activo_puede_cambiar_a_estado_baja(
        self, activo_test, estado_activo_baja
    ):
        activo_test.estado = estado_activo_baja
        activo_test.save()
        activo_test.refresh_from_db()
        assert activo_test.estado.codigo == "BJA"
        assert activo_test.estado.permite_movimiento is False

    def test_activo_en_baja_no_permite_movimiento(
        self, activo_test, estado_activo_baja
    ):
        activo_test.estado = estado_activo_baja
        activo_test.save()
        assert activo_test.estado.permite_movimiento is False


# ============================================================
# 3. MOVIMIENTOS DE ACTIVOS
# ============================================================

class TestMovimientosActivos:

    def test_crear_movimiento_activo(
        self, activo_test, ubicacion_test, tipo_movimiento_activo_traslado, u_bodeguero
    ):
        from apps.activos.models import Ubicacion

        ub_destino, _ = Ubicacion.objects.get_or_create(
            codigo="UB-DESTINO",
            defaults={"nombre": "Destino Test", "activo": True, "eliminado": False}
        )

        mov = MovimientoActivo.objects.create(
            activo=activo_test,
            tipo_movimiento=tipo_movimiento_activo_traslado,
            ubicacion_destino=ub_destino,
            responsable=u_bodeguero,
            usuario_registro=u_bodeguero,
            observaciones="Traslado de prueba",
            eliminado=False,
        )

        assert mov.pk is not None
        assert mov.activo == activo_test
        assert mov.usuario_registro == u_bodeguero

    def test_historial_movimientos_articulo(
        self, activo_test, ubicacion_test, tipo_movimiento_activo_traslado, u_bodeguero
    ):
        from apps.activos.models import Ubicacion

        ub2, _ = Ubicacion.objects.get_or_create(
            codigo="UB-DEST2",
            defaults={"nombre": "Destino 2", "activo": True, "eliminado": False}
        )

        MovimientoActivo.objects.create(
            activo=activo_test,
            tipo_movimiento=tipo_movimiento_activo_traslado,
            ubicacion_destino=ub2,
            usuario_registro=u_bodeguero,
            observaciones="Primer traslado",
            eliminado=False,
        )

        movs = MovimientoActivo.objects.filter(activo=activo_test)
        assert movs.count() >= 1


# ============================================================
# 4. VISTAS HTTP — ACTIVOS
# ============================================================

class TestVistasHTTPActivos:

    def test_admin_ve_lista_activos(self, client_admin):
        resp = client_admin.get("/activos/")
        assert resp.status_code == 200

    def test_admin_puede_crear_activo(self, client_admin):
        resp = client_admin.get("/activos/crear/")
        assert resp.status_code == 200

    def test_sin_permiso_no_accede_a_activos(self, client_sin_rol):
        resp = client_sin_rol.get("/activos/")
        assert resp.status_code in (403, 302)

    def test_admin_ve_detalle_activo(self, client_admin, activo_test):
        resp = client_admin.get(f"/activos/{activo_test.pk}/")
        assert resp.status_code == 200

    def test_admin_ve_movimientos_activos(self, client_admin):
        resp = client_admin.get("/activos/movimientos/")
        assert resp.status_code == 200

    def test_solicitante_no_accede_activos(self, client_solicitante):
        resp = client_solicitante.get("/activos/")
        assert resp.status_code in (403, 302)
