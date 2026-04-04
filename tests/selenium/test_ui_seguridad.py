"""
Pruebas de seguridad UI con Selenium.

Cubre: XSS, CSRF visible, IDOR, enumeracion de URLs, headers.
"""
import urllib.parse
import pytest
from .pages.base_page import BasePage
from .pages.login_page import LoginPage

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestXSSEnUI:

    def test_xss_en_busqueda_admin_no_ejecuta_script(self, browser_admin):
        d = browser_admin
        xss = "<script>alert('xss_test')</script>"
        payload = urllib.parse.quote(xss)
        d.get(f"{d._base_url}/administracion/usuarios/?q={payload}")
        page = BasePage(d, base_url=d._base_url)
        assert page.no_alert_present(), "XSS ejecutado en busqueda de usuarios"

    def test_xss_en_parametro_url_escapado(self, browser_admin):
        d = browser_admin
        d.get(f"{d._base_url}/administracion/usuarios/?q=<b>test</b>")
        src = d.page_source
        assert "<b>test</b>" not in src, "HTML no escapado detectado en la respuesta"

    def test_xss_en_login_campo_usuario(self, driver, live_server, db):
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        page.login("<img src=x onerror=alert(1)>", "pass")
        assert page.no_alert_present(), "XSS ejecutado en campo de usuario del login"

    def test_xss_en_busqueda_articulos(self, browser_admin):
        d = browser_admin
        xss = urllib.parse.quote("<script>alert(2)</script>")
        d.get(f"{d._base_url}/bodega/articulos/?q={xss}")
        page = BasePage(d, base_url=d._base_url)
        assert page.no_alert_present(), "XSS ejecutado en busqueda de articulos"

    def test_xss_en_busqueda_activos(self, browser_admin):
        d = browser_admin
        xss = urllib.parse.quote("<script>alert(3)</script>")
        d.get(f"{d._base_url}/activos/?q={xss}")
        page = BasePage(d, base_url=d._base_url)
        assert page.no_alert_present()


class TestIDOR:
    """Insecure Direct Object Reference: un rol no debe ver objetos de otro."""

    def test_solicitante_no_accede_a_detalle_de_baja_arbitraria(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/bajas-inventario/9999/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url or "404" in src

    def test_solicitante_no_accede_a_detalle_orden_compra(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/compras/ordenes/9999/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url or "404" in src

    def test_solicitante_no_accede_a_detalle_activo_arbitrario(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/activos/9999/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url or "404" in src


class TestCSRFEnFormularios:

    def test_formularios_tienen_csrf(self, browser_admin):
        d = browser_admin
        rutas_con_form = [
            "/solicitudes/articulos/crear/",
            "/bodega/articulos/crear/",
            "/compras/ordenes/crear/",
            "/activos/crear/",
            "/bajas-inventario/crear/",
            "/administracion/usuarios/crear/",
        ]
        for ruta in rutas_con_form:
            d.get(f"{d._base_url}{ruta}")
            src = d.page_source
            if "form" in src.lower() and "403" not in d.title:
                assert "csrfmiddlewaretoken" in src, (
                    f"Falta CSRF token en formulario de {ruta}"
                )


class TestEnumeracionURLs:
    """Rutas administrativas no deben revelar informacion a usuarios sin permisos."""

    def test_rutas_admin_denegadas_a_solicitante(self, browser_solicitante):
        d = browser_solicitante
        rutas_admin = [
            "/administracion/usuarios/",
            "/administracion/usuarios/crear/",
            "/administracion/permisos/",
        ]
        for ruta in rutas_admin:
            d.get(f"{d._base_url}{ruta}")
            url = d.current_url
            src = d.page_source
            denegado = "403" in src or "login" in url or "account" in url or "404" in d.title
            assert denegado, f"Solicitante no debe acceder a {ruta}"

    def test_api_interna_denegada_a_anonimo(self, browser_anonimo):
        d = browser_anonimo
        rutas = ["/administracion/", "/bodega/", "/activos/", "/compras/"]
        for ruta in rutas:
            d.get(f"{d._base_url}{ruta}")
            url = d.current_url
            assert "login" in url or "account" in url, (
                f"Anonimo no debe ver {ruta}"
            )


class TestRenderizadoSinErrores:
    """Todas las paginas principales deben renderizar sin error 500."""

    @pytest.mark.parametrize("ruta", [
        "/solicitudes/",
        "/solicitudes/mis-solicitudes/",
        "/solicitudes/articulos/crear/",
        "/bodega/articulos/",
        "/bodega/movimientos/",
        "/bodega/recepciones-articulos/",
        "/compras/ordenes/",
        "/compras/proveedores/",
        "/activos/",
        "/activos/movimientos/",
        "/bajas-inventario/",
        "/bajas-inventario/motivos/",
        "/administracion/usuarios/",
    ])
    def test_pagina_sin_error_500(self, browser_admin, ruta):
        browser_admin.get(f"{browser_admin._base_url}{ruta}")
        assert "500" not in browser_admin.title, f"Error 500 en {ruta}"
        assert "Server Error" not in browser_admin.page_source, f"Server Error en {ruta}"
