"""Page Objects para el modulo de Bodega."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class ArticulosPage(BasePage):

    def open(self):
        return self.go("/bodega/articulos/")

    def open_crear(self):
        return self.go("/bodega/articulos/crear/")

    def open_detalle(self, pk):
        return self.go(f"/bodega/articulos/{pk}/")

    def lista_cargada(self):
        src = self.driver.page_source
        return "articulo" in src.lower() or "table" in src or "list" in src.lower()


class MovimientosPage(BasePage):

    def open(self):
        return self.go("/bodega/movimientos/")

    def open_crear(self):
        return self.go("/bodega/movimientos/crear/")

    def formulario_visible(self):
        return self.is_visible((By.CSS_SELECTOR, "form"))


class RecepcionesPage(BasePage):

    def open(self):
        return self.go("/bodega/recepciones-articulos/")

    def open_crear(self):
        return self.go("/bodega/recepciones-articulos/crear/")

    def lista_cargada(self):
        src = self.driver.page_source
        return "recepcion" in src.lower() or "table" in src
