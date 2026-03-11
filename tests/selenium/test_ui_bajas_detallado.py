"""Pruebas visuales detalladas para el modulo de bajas."""
from __future__ import annotations

import pytest

from apps.bajas_inventario.models import MotivoBaja

from .conftest import switch_user


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestBajasVisual:
    def test_menu_bajas_muestra_accesos_y_estadisticas(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["bajas_operador"])
        driver.get(f"{live_server.url}/bajas-inventario/")
        ui_observer.note("Menu de bajas", "Se revisa el acceso principal y la presencia de estadisticas del modulo.")
        page_text = driver.page_source
        assert "Bajas de Inventario" in page_text
        assert "Motivos" in page_text or "motivos" in page_text

    def test_listado_motivos_muestra_catalogo_existente(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        MotivoBaja.objects.get_or_create(
            codigo="VIS-BAJA",
            defaults={"nombre": "Motivo Visual", "descripcion": "Motivo para listado", "activo": True, "eliminado": False},
        )
        switch_user(driver, live_server, erp_ui_catalogo["bajas_operador"])
        driver.get(f"{live_server.url}/bajas-inventario/motivos/")
        ui_observer.note("Listado de motivos", "Se verifica que el catalogo de motivos sea visible y navegable.")
        page_text = driver.page_source
        assert "Motivo Visual" in page_text
        assert "VIS-BAJA" in page_text
