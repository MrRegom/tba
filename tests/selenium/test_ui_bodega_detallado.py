"""Pruebas visuales detalladas para el modulo de bodega."""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from apps.bodega.models import Articulo, Movimiento

from .conftest import switch_user
from .helpers import (
    fill_input,
    force_select_value,
    replace_input_value,
    select_by_text_or_first,
    submit_last_form,
)


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestBodegaVisual:
    def test_articulo_formulario_y_creacion_exitosa(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["bodeguero"])
        driver.get(f"{live_server.url}/bodega/articulos/crear/")
        ui_observer.note("Formulario crear articulo", "Se revisa la estructura del formulario y luego un alta valida.")

        page_text = driver.page_source.lower()
        assert "art" in page_text
        assert driver.find_elements(By.NAME, "nombre")
        assert driver.find_elements(By.NAME, "categoria")
        assert driver.find_elements(By.NAME, "unidad_medida")
        assert driver.find_elements(By.NAME, "ubicacion_fisica")
        assert driver.find_elements(By.NAME, "stock_minimo")
        assert driver.find_elements(By.NAME, "stock_maximo")
        assert driver.find_elements(By.NAME, "punto_reorden")

        fill_input(driver, "nombre", "Articulo Visual Bodega")
        fill_input(driver, "descripcion", "Creado desde Selenium para validar reglas.")
        select_by_text_or_first(driver, "categoria", erp_ui_catalogo["categoria_bodega"].nombre)
        select_by_text_or_first(driver, "unidad_medida", erp_ui_catalogo["unidad"].nombre)
        select_by_text_or_first(driver, "ubicacion_fisica", erp_ui_catalogo["bodega"].nombre)
        replace_input_value(driver, "stock_minimo", "5")
        replace_input_value(driver, "stock_maximo", "20")
        replace_input_value(driver, "punto_reorden", "8")
        submit_last_form(driver)
        ui_observer.note("Articulo creado", "Se espera persistencia correcta con parametros validos.")
        articulo = Articulo.objects.filter(nombre="Articulo Visual Bodega").order_by("-id").first()
        assert articulo is not None
        assert articulo.stock_minimo == 5

    def test_movimiento_muestra_campos_clave_del_formulario(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["bodeguero"])
        driver.get(f"{live_server.url}/bodega/movimientos/crear/")
        ui_observer.note("Formulario movimiento", "Se valida que la UI exponga articulo, tipo, operacion, cantidad y motivo.")

        page_text = driver.page_source.lower()
        assert "registrar movimiento" in page_text
        assert driver.find_elements(By.NAME, "articulo")
        assert driver.find_elements(By.NAME, "tipo")
        assert driver.find_elements(By.NAME, "operacion")
        assert driver.find_elements(By.NAME, "cantidad")
        assert driver.find_elements(By.NAME, "motivo")

    def test_movimiento_bloquea_salida_con_stock_insuficiente(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["bodeguero"])
        driver.get(f"{live_server.url}/bodega/movimientos/crear/")
        ui_observer.note("Salida invalida", "Se intenta registrar una salida por sobre el stock disponible.")

        cantidad_inicial = Movimiento.objects.count()
        force_select_value(driver, "articulo", erp_ui_catalogo["articulo_base"].id, erp_ui_catalogo["articulo_base"].codigo)
        force_select_value(driver, "tipo", erp_ui_catalogo["tipo_mov_bodega"].id, erp_ui_catalogo["tipo_mov_bodega"].nombre)
        force_select_value(driver, "operacion", erp_ui_catalogo["operacion_salida"].id, erp_ui_catalogo["operacion_salida"].nombre)
        fill_input(driver, "cantidad", "999")
        fill_input(driver, "motivo", "Intento de salida superior al stock")
        submit_last_form(driver)
        ui_observer.note("Stock insuficiente", "La vista debe advertir que la salida excede el disponible.")
        assert Movimiento.objects.count() == cantidad_inicial
        page_text = driver.page_source.lower()
        assert "registrar movimiento" in page_text
        assert "cantidad" in page_text
