"""Pruebas visuales detalladas para el modulo de activos."""
from __future__ import annotations

import pytest

from apps.activos.models import Activo, MovimientoActivo

from .conftest import switch_user
from .helpers import fill_input, replace_input_value, select_by_text_or_first, submit_last_form


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestActivosVisual:
    def test_activo_se_crea_y_genera_codigo(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["activos_operador"])
        driver.get(f"{live_server.url}/activos/crear/")
        ui_observer.note("Formulario crear activo", "Se valida alta individual y generacion automatica de codigo.")

        fill_input(driver, "nombre", "Activo Visual Selenium")
        fill_input(driver, "descripcion", "Activo creado para flujo visual.")
        select_by_text_or_first(driver, "categoria", erp_ui_catalogo["categoria_activo"].nombre)
        select_by_text_or_first(driver, "estado", erp_ui_catalogo["estado_activo"].nombre)
        select_by_text_or_first(driver, "marca", erp_ui_catalogo["marca_activo"].nombre)
        fill_input(driver, "numero_serie", "SERIE-VISUAL-001")
        replace_input_value(driver, "precio_unitario", "349990")
        submit_last_form(driver)
        ui_observer.note("Activo creado", "Se espera persistencia correcta y codigo autogenerado.")
        activo = Activo.objects.filter(nombre="Activo Visual Selenium").order_by("-id").first()
        assert activo is not None
        assert activo.codigo
        assert activo.codigo.startswith(erp_ui_catalogo["categoria_activo"].sigla)

    def test_movimiento_activo_requiere_estado_y_se_registra(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["activos_operador"])
        driver.get(f"{live_server.url}/activos/movimientos/registrar/")
        ui_observer.note("Formulario movimiento de activo", "Se valida estado obligatorio y registro final.")

        driver.execute_script(
            """
            document.getElementById('activos_seleccionados').value = arguments[0];
            document.getElementById('seccion-detalles-movimiento').style.display = 'block';
            document.getElementById('card-activos-seleccionados').style.display = 'block';
            document.getElementById('contador-seleccionados').textContent = '1';
            document.getElementById('btn-registrar-movimiento').disabled = false;
            """,
            str(erp_ui_catalogo["activo_base"].id),
        )
        fill_input(driver, "observaciones", "Movimiento sin estado para error")
        driver.execute_script("document.getElementById('form-movimiento').submit();")
        ui_observer.note("Error por estado faltante", "La regla de negocio exige nuevo estado.")
        assert "nuevo estado es obligatorio" in driver.page_source.lower()

        driver.get(f"{live_server.url}/activos/movimientos/registrar/")
        driver.execute_script(
            """
            document.getElementById('activos_seleccionados').value = arguments[0];
            document.getElementById('seccion-detalles-movimiento').style.display = 'block';
            document.getElementById('card-activos-seleccionados').style.display = 'block';
            document.getElementById('contador-seleccionados').textContent = '1';
            document.getElementById('btn-registrar-movimiento').disabled = false;
            """,
            str(erp_ui_catalogo["activo_base"].id),
        )
        select_by_text_or_first(driver, "estado_nuevo", erp_ui_catalogo["estado_activo"].nombre)
        select_by_text_or_first(driver, "ubicacion_destino", erp_ui_catalogo["ubicacion"].nombre)
        select_by_text_or_first(driver, "responsable", erp_ui_catalogo["activos_operador"].username)
        select_by_text_or_first(driver, "proveniencia", erp_ui_catalogo["proveniencia"].nombre)
        fill_input(driver, "observaciones", "Movimiento activo visual")
        driver.execute_script("document.getElementById('form-movimiento').submit();")
        ui_observer.note("Movimiento registrado", "Debe quedar trazabilidad del activo en la tabla de movimientos.")
        movimiento = MovimientoActivo.objects.filter(observaciones="Movimiento activo visual").order_by("-id").first()
        assert movimiento is not None
        assert movimiento.activo == erp_ui_catalogo["activo_base"]
