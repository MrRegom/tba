"""Pruebas visuales detalladas para administracion de usuarios y roles."""
from __future__ import annotations

import pytest

from django.contrib.auth.models import Group

from .conftest import switch_user
from .helpers import fill_input, submit_last_form


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestAdministracionVisual:
    def test_menu_administracion_muestra_accesos_principales(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["admin_usuarios"])
        driver.get(f"{live_server.url}/administracion/")
        ui_observer.note("Menu administracion", "Se revisan accesos visibles a usuarios, grupos y permisos.")

        page_text = driver.page_source.lower()
        assert "administr" in page_text
        assert "usuarios" in page_text
        assert "grupos" in page_text or "roles" in page_text

    def test_crear_grupo_se_registra_desde_administracion(
        self, driver, live_server, ui_observer, erp_ui_catalogo
    ):
        switch_user(driver, live_server, erp_ui_catalogo["admin_usuarios"])
        driver.get(f"{live_server.url}/administracion/grupos/crear/")
        ui_observer.note("Formulario crear grupo", "Se valida gestion base de roles.")

        fill_input(driver, "name", "Rol Visual Selenium")
        submit_last_form(driver)
        ui_observer.note("Grupo creado", "Debe persistir el rol para futuras asignaciones.")
        assert Group.objects.filter(name="Rol Visual Selenium").exists()
