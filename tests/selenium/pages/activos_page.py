"""Page Objects para el modulo de Activos."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class ActivosPage(BasePage):

    def open(self):
        return self.go("/activos/")

    def open_crear(self):
        return self.go("/activos/crear/")

    def open_detalle(self, pk):
        return self.go(f"/activos/{pk}/")

    def lista_cargada(self):
        src = self.driver.page_source
        return "activo" in src.lower() or "table" in src


class MovimientosActivosPage(BasePage):

    def open(self):
        return self.go("/activos/movimientos/")

    def lista_cargada(self):
        return "movimiento" in self.driver.page_source.lower() or "table" in self.driver.page_source
