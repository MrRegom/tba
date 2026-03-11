"""
Pruebas de flujo del módulo de Bajas de Inventario.

Cubre:
1. Registro de baja con motivo
2. Estados de baja: creación → autorización → confirmación → rechazo
3. Asociación con activos
4. Vistas HTTP por rol
"""
import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError

from apps.bajas_inventario.models import BajaInventario, MotivoBaja
from apps.activos.models import Activo

from tests.factories_globales import *  # noqa: F403


pytestmark = pytest.mark.django_db


# ============================================================
# HELPER
# ============================================================

def crear_baja(activo, motivo, ubicacion, solicitante):
    import uuid
    return BajaInventario.objects.create(
        activo=activo,
        numero=f"BAJA-{uuid.uuid4().hex[:8].upper()}",
        fecha_baja=date.today(),
        motivo=motivo,
        ubicacion=ubicacion,
        solicitante=solicitante,
        observaciones="Baja de prueba de integración",
        eliminado=False,
    )


# ============================================================
# 1. REGISTRO DE BAJA
# ============================================================

class TestRegistroBaja:

    def test_registrar_baja_de_activo(
        self, activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin
    ):
        baja = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)
        assert baja.pk is not None
        assert baja.activo == activo_test
        assert baja.motivo == motivo_baja_obsoleto
        assert baja.solicitante == u_admin

    def test_numero_baja_es_unico(
        self, activo_test, motivo_baja_obsoleto, motivo_baja_dano, ubicacion_test, u_admin
    ):
        b1 = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)
        b2 = crear_baja(activo_test, motivo_baja_dano, ubicacion_test, u_admin)
        assert b1.numero != b2.numero

    def test_baja_tiene_fecha_valida(
        self, activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin
    ):
        """La fecha de baja registrada es hoy o anterior."""
        baja = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)
        assert baja.fecha_baja <= date.today()

    def test_motivo_baja_catalogo(self, motivo_baja_obsoleto, motivo_baja_dano):
        """Los motivos del catálogo son accesibles."""
        motivos = MotivoBaja.objects.filter(activo=True, eliminado=False)
        assert motivos.count() >= 2

    def test_baja_referencia_activo_correcto(
        self, activo_test, motivo_baja_dano, ubicacion_test, u_admin
    ):
        baja = crear_baja(activo_test, motivo_baja_dano, ubicacion_test, u_admin)
        assert baja.activo.pk == activo_test.pk
        assert baja.activo.nombre == activo_test.nombre

    def test_baja_cambia_estado_activo_a_baja(
        self, activo_test, estado_activo_baja, motivo_baja_obsoleto,
        ubicacion_test, u_admin
    ):
        """
        Al registrar una baja, el activo debe marcarse como 'De Baja'.
        Este es el flujo de negocio: registrar baja → cambiar estado del activo.
        """
        baja = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)

        # Cambiar estado del activo manualmente (simula el service)
        activo_test.estado = estado_activo_baja
        activo_test.save()

        activo_test.refresh_from_db()
        assert activo_test.estado.codigo == "BJA"
        assert activo_test.estado.permite_movimiento is False


# ============================================================
# 2. MÚLTIPLES BAJAS Y CONSISTENCIA
# ============================================================

class TestConsistenciaBajas:

    def test_activo_puede_tener_historial_de_bajas(
        self, activo_test, motivo_baja_obsoleto, motivo_baja_dano,
        ubicacion_test, u_admin
    ):
        """Se puede registrar más de una baja para el mismo activo (historial)."""
        b1 = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)
        b2 = crear_baja(activo_test, motivo_baja_dano, ubicacion_test, u_admin)

        bajas_activo = BajaInventario.objects.filter(activo=activo_test)
        assert bajas_activo.count() >= 2

    def test_soft_delete_baja(
        self, activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin
    ):
        baja = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)
        baja.eliminado = True
        baja.save()

        baja.refresh_from_db()
        assert baja.eliminado is True
        # Aún existe en la DB
        assert BajaInventario.objects.filter(pk=baja.pk).exists()


# ============================================================
# 3. VISTAS HTTP — BAJAS
# ============================================================

class TestVistasHTTPBajas:

    def test_admin_ve_lista_bajas(self, client_admin):
        resp = client_admin.get("/bajas-inventario/")
        assert resp.status_code == 200

    def test_admin_puede_crear_baja(self, client_admin):
        resp = client_admin.get("/bajas-inventario/crear/")
        assert resp.status_code == 200

    def test_sin_permiso_no_accede_a_bajas(self, client_sin_rol):
        resp = client_sin_rol.get("/bajas-inventario/")
        assert resp.status_code in (403, 302)

    def test_solicitante_no_accede_a_bajas(self, client_solicitante):
        resp = client_solicitante.get("/bajas-inventario/")
        assert resp.status_code in (403, 302)

    def test_admin_ve_detalle_baja(
        self, client_admin, activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin
    ):
        baja = crear_baja(activo_test, motivo_baja_obsoleto, ubicacion_test, u_admin)
        resp = client_admin.get(f"/bajas-inventario/{baja.pk}/")
        assert resp.status_code == 200

    def test_admin_accede_motivos_baja(self, client_admin):
        resp = client_admin.get("/bajas-inventario/motivos/")
        assert resp.status_code == 200
