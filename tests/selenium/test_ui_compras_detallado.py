"""Pruebas visuales detalladas para el modulo de compras."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.compras.models import OrdenCompra, Proveedor

from .conftest import switch_user
from .helpers import fill_input, set_input_value, select_by_text_or_first, submit_last_form


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestComprasVisual:
    def test_proveedor_crea_y_bloquea_rut_duplicado(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["comprador"])
        driver.get(f"{live_server.url}/compras/proveedores/crear/")
        ui_observer.note("Formulario proveedor", "Se crea proveedor y luego se prueba RUT duplicado.")

        fill_input(driver, "rut", "76.555.555-5")
        fill_input(driver, "razon_social", "Proveedor Visual Selenium")
        fill_input(driver, "direccion", "Avenida Proveedor 123")
        fill_input(driver, "ciudad", "Santiago")
        fill_input(driver, "telefono", "+56912345678")
        fill_input(driver, "email", "proveedor.visual@test.cl")
        submit_last_form(driver)
        ui_observer.note("Proveedor creado", "Debe quedar persistido con su RUT y razon social.")
        proveedor = Proveedor.objects.filter(rut="76.555.555-5").first()
        assert proveedor is not None

        driver.get(f"{live_server.url}/compras/proveedores/crear/")
        fill_input(driver, "rut", "76.555.555-5")
        fill_input(driver, "razon_social", "Proveedor Duplicado")
        fill_input(driver, "direccion", "Otra direccion 999")
        submit_last_form(driver)
        ui_observer.note("RUT duplicado", "La UI debe mostrar validacion por unicidad.")
        assert "ya existe un proveedor con el rut" in driver.page_source.lower()

    def test_orden_compra_valida_fecha_y_se_crea(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["comprador"])
        driver.get(f"{live_server.url}/compras/ordenes/crear/")
        ui_observer.note("Formulario orden de compra", "Se prueba fecha invalida y luego creacion valida.")

        set_input_value(driver, "fecha_entrega_esperada", (date.today() - timedelta(days=1)).isoformat())
        select_by_text_or_first(driver, "proveedor", erp_ui_catalogo["proveedor_base"].razon_social)
        select_by_text_or_first(driver, "bodega_destino", erp_ui_catalogo["bodega"].nombre)
        fill_input(driver, "observaciones", "Orden con fecha invalida")
        submit_last_form(driver)
        ui_observer.note("Fecha de entrega invalida", "La fecha esperada no puede ser anterior a la fecha de orden.")
        assert "fecha de entrega esperada no puede ser anterior" in driver.page_source.lower()

        driver.get(f"{live_server.url}/compras/ordenes/crear/")
        set_input_value(driver, "fecha_entrega_esperada", (date.today() + timedelta(days=7)).isoformat())
        select_by_text_or_first(driver, "proveedor", erp_ui_catalogo["proveedor_base"].razon_social)
        select_by_text_or_first(driver, "bodega_destino", erp_ui_catalogo["bodega"].nombre)
        fill_input(driver, "observaciones", "Orden creada visualmente")
        submit_last_form(driver)
        ui_observer.note("Orden creada", "Debe crearse una orden con datos minimos validos.")
        orden = OrdenCompra.objects.filter(observaciones="Orden creada visualmente").order_by("-id").first()
        assert orden is not None
        assert orden.proveedor == erp_ui_catalogo["proveedor_base"]
