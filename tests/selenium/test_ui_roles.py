"""
Pruebas UI de control de acceso por roles con Selenium.

Verifica que cada rol vea solo lo que le corresponde.
Usa live_server + inyeccion de sesion (sin formulario allauth).
"""
import pytest
from django.contrib.auth.models import User
from .conftest import inject_session
from .pages.dashboard_page import DashboardPage

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]

BASE_RUTAS_PROTEGIDAS = [
    "/solicitudes/",
    "/bodega/articulos/",
    "/activos/",
    "/compras/ordenes/",
    "/bajas-inventario/",
    "/administracion/usuarios/",
]


class TestAccesoAnonimo:

    def test_anonimo_redirigido_al_intentar_rutas_protegidas(self, browser_anonimo):
        d = browser_anonimo
        for ruta in BASE_RUTAS_PROTEGIDAS:
            d.get(f"{d._base_url}{ruta}")
            url = d.current_url
            assert "login" in url or "account" in url, (
                f"Anonimo debe ser redirigido al acceder a {ruta}, URL actual: {url}"
            )


class TestRolSolicitante:

    def test_solicitante_accede_a_mis_solicitudes(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/solicitudes/mis-solicitudes/")
        assert "403" not in d.title
        assert "login" not in d.current_url

    def test_solicitante_puede_ver_formulario_crear_solicitud(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/solicitudes/articulos/crear/")
        assert "403" not in d.title
        assert "login" not in d.current_url

    def test_solicitante_bloqueado_en_gestion_solicitudes(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/solicitudes/gestion/")
        url = d.current_url
        src = d.page_source
        denegado = ("403" in src or "login" in url or "account" in url
                    or "Permiso" in src or "permiso" in src)
        assert denegado, "Solicitante no debe acceder a gestion de solicitudes"

    def test_solicitante_bloqueado_en_bodega(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/bodega/articulos/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url, (
            "Solicitante no debe ver bodega"
        )

    def test_solicitante_bloqueado_en_administracion(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/administracion/usuarios/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url

    def test_solicitante_bloqueado_en_compras(self, browser_solicitante):
        d = browser_solicitante
        d.get(f"{d._base_url}/compras/ordenes/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url


class TestRolAprobador:

    def test_aprobador_ve_lista_solicitudes(self, browser_aprobador):
        d = browser_aprobador
        d.get(f"{d._base_url}/solicitudes/gestion/")
        assert "403" not in d.title
        assert "login" not in d.current_url

    def test_aprobador_bloqueado_en_administracion(self, browser_aprobador):
        d = browser_aprobador
        d.get(f"{d._base_url}/administracion/usuarios/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url

    def test_aprobador_bloqueado_en_bodega(self, browser_aprobador):
        d = browser_aprobador
        d.get(f"{d._base_url}/bodega/articulos/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url


class TestRolDespachador:

    def test_despachador_ve_lista_solicitudes(self, browser_despachador):
        d = browser_despachador
        d.get(f"{d._base_url}/solicitudes/gestion/")
        assert "403" not in d.title
        assert "login" not in d.current_url

    def test_despachador_bloqueado_en_administracion(self, browser_despachador):
        d = browser_despachador
        d.get(f"{d._base_url}/administracion/usuarios/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url


class TestRolBodeguero:

    def test_bodeguero_ve_articulos(self, browser_bodeguero):
        d = browser_bodeguero
        d.get(f"{d._base_url}/bodega/articulos/")
        assert "403" not in d.title
        assert "login" not in d.current_url

    def test_bodeguero_ve_movimientos(self, browser_bodeguero):
        d = browser_bodeguero
        d.get(f"{d._base_url}/bodega/movimientos/")
        assert "403" not in d.title
        assert "500" not in d.title

    def test_bodeguero_ve_recepciones(self, browser_bodeguero):
        d = browser_bodeguero
        d.get(f"{d._base_url}/bodega/recepciones-articulos/")
        assert "403" not in d.title
        assert "500" not in d.title

    def test_bodeguero_bloqueado_en_administracion(self, browser_bodeguero):
        d = browser_bodeguero
        d.get(f"{d._base_url}/administracion/usuarios/")
        url = d.current_url
        src = d.page_source
        assert "403" in src or "login" in url or "account" in url


class TestRolAdmin:

    def test_admin_accede_a_todos_los_modulos(self, browser_admin):
        d = browser_admin
        rutas = [
            "/solicitudes/",
            "/bodega/articulos/",
            "/activos/",
            "/compras/ordenes/",
            "/bajas-inventario/",
            "/administracion/usuarios/",
        ]
        for ruta in rutas:
            d.get(f"{d._base_url}{ruta}")
            assert "403" not in d.title, f"Admin bloqueado en {ruta}"
            assert "500" not in d.title, f"Error 500 en {ruta}"
            assert "login" not in d.current_url, f"Admin redirigido al login en {ruta}"

    def test_admin_puede_crear_usuario(self, browser_admin):
        d = browser_admin
        d.get(f"{d._base_url}/administracion/usuarios/crear/")
        assert "403" not in d.title
        assert "login" not in d.current_url

    def test_admin_accede_a_bajas(self, browser_admin):
        d = browser_admin
        d.get(f"{d._base_url}/bajas-inventario/")
        assert "403" not in d.title

    def test_admin_accede_a_activos(self, browser_admin):
        d = browser_admin
        d.get(f"{d._base_url}/activos/")
        assert "403" not in d.title

    def test_admin_accede_a_compras(self, browser_admin):
        d = browser_admin
        d.get(f"{d._base_url}/compras/ordenes/")
        assert "403" not in d.title


class TestSinRol:

    def test_sin_rol_bloqueado_en_todo(self, browser_anonimo, live_server, sel_sin_rol):
        from .conftest import inject_session
        d = browser_anonimo
        inject_session(d, live_server, sel_sin_rol)
        rutas = [
            "/solicitudes/",
            "/bodega/articulos/",
            "/activos/",
            "/compras/ordenes/",
        ]
        for ruta in rutas:
            d.get(f"{d._base_url}{ruta}")
            url = d.current_url
            src = d.page_source
            denegado = "403" in src or "login" in url or "account" in url or "Permiso" in src
            assert denegado, f"Usuario sin rol no debe acceder a {ruta}"
