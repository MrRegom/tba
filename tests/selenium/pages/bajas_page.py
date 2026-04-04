"""Page Objects para el modulo de Bajas de Inventario."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class BajasPage(BasePage):

    def open(self):
        return self.go("/bajas-inventario/")

    def open_crear(self):
        return self.go("/bajas-inventario/crear/")

    def open_detalle(self, pk):
        return self.go(f"/bajas-inventario/{pk}/")

    def open_motivos(self):
        return self.go("/bajas-inventario/motivos/")

    def lista_cargada(self):
        src = self.driver.page_source
        return "baja" in src.lower() or "table" in src
