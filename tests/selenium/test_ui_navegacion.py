"""
Pruebas UI de navegacion y renderizado correcto por modulo.

Verifica que cada pagina carga sin errores 500, muestra el contenido
esperado y que los elementos de navegacion son correctos por rol.
"""
import pytest
from .pages.solicitudes_page import ListaSolicitudesPage, CrearSolicitudPage
from .pages.bodega_page import ArticulosPage, MovimientosPage, RecepcionesPage
from .pages.compras_page import OrdenesCompraPage, ProveedoresPage
from .pages.activos_page import ActivosPage, MovimientosActivosPage
from .pages.bajas_page import BajasPage

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestNavegacionAdmin:
    """Admin navega por todos los modulos sin errores."""

    def test_lista_solicitudes_carga(self, browser_admin):
        page = ListaSolicitudesPage(browser_admin, base_url=browser_admin._base_url)
        page.open_lista()
        assert page.no_server_error()

    def test_crear_solicitud_carga(self, browser_admin):
        page = CrearSolicitudPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()
        assert page.tiene_formulario()

    def test_lista_articulos_carga(self, browser_admin):
        page = ArticulosPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_crear_articulo_carga(self, browser_admin):
        page = ArticulosPage(browser_admin, base_url=browser_admin._base_url)
        page.open_crear()
        assert page.no_server_error()

    def test_movimientos_bodega_carga(self, browser_admin):
        page = MovimientosPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_recepciones_articulos_carga(self, browser_admin):
        page = RecepcionesPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_ordenes_compra_carga(self, browser_admin):
        page = OrdenesCompraPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_crear_orden_compra_carga(self, browser_admin):
        page = OrdenesCompraPage(browser_admin, base_url=browser_admin._base_url)
        page.open_crear()
        assert page.no_server_error()

    def test_proveedores_carga(self, browser_admin):
        page = ProveedoresPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_activos_lista_carga(self, browser_admin):
        page = ActivosPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_crear_activo_carga(self, browser_admin):
        page = ActivosPage(browser_admin, base_url=browser_admin._base_url)
        page.open_crear()
        assert page.no_server_error()

    def test_movimientos_activos_carga(self, browser_admin):
        page = MovimientosActivosPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_bajas_lista_carga(self, browser_admin):
        page = BajasPage(browser_admin, base_url=browser_admin._base_url)
        page.open()
        assert page.no_server_error()

    def test_crear_baja_carga(self, browser_admin):
        page = BajasPage(browser_admin, base_url=browser_admin._base_url)
        page.open_crear()
        assert page.no_server_error()

    def test_motivos_baja_carga(self, browser_admin):
        page = BajasPage(browser_admin, base_url=browser_admin._base_url)
        page.open_motivos()
        assert page.no_server_error()


class TestNavegacionSolicitante:

    def test_mis_solicitudes_carga(self, browser_solicitante):
        page = ListaSolicitudesPage(browser_solicitante, base_url=browser_solicitante._base_url)
        page.open()
        assert page.no_server_error()

    def test_crear_solicitud_carga(self, browser_solicitante):
        page = CrearSolicitudPage(browser_solicitante, base_url=browser_solicitante._base_url)
        page.open()
        assert page.no_server_error()
        assert page.tiene_formulario()

    def test_articulos_bodega_denegado(self, browser_solicitante):
        page = ArticulosPage(browser_solicitante, base_url=browser_solicitante._base_url)
        page.open()
        src = page.page_source()
        url = page.current_url()
        assert "403" in src or "login" in url or "account" in url

    def test_ordenes_compra_denegado(self, browser_solicitante):
        page = OrdenesCompraPage(browser_solicitante, base_url=browser_solicitante._base_url)
        page.open()
        src = page.page_source()
        url = page.current_url()
        assert "403" in src or "login" in url or "account" in url


class TestNavegacionBodeguero:

    def test_articulos_carga(self, browser_bodeguero):
        page = ArticulosPage(browser_bodeguero, base_url=browser_bodeguero._base_url)
        page.open()
        assert page.no_server_error()

    def test_movimientos_carga(self, browser_bodeguero):
        page = MovimientosPage(browser_bodeguero, base_url=browser_bodeguero._base_url)
        page.open()
        assert page.no_server_error()

    def test_recepciones_carga(self, browser_bodeguero):
        page = RecepcionesPage(browser_bodeguero, base_url=browser_bodeguero._base_url)
        page.open()
        assert page.no_server_error()

    def test_solicitudes_denegado(self, browser_bodeguero):
        page = ListaSolicitudesPage(browser_bodeguero, base_url=browser_bodeguero._base_url)
        page.open_gestion()
        src = page.page_source()
        url = page.current_url()
        assert "403" in src or "login" in url or "account" in url
