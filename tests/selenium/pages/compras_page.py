"""Page Objects para el modulo de Compras."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class OrdenesCompraPage(BasePage):

    def open(self):
        return self.go("/compras/ordenes/")

    def open_crear(self):
        return self.go("/compras/ordenes/crear/")

    def open_detalle(self, pk):
        return self.go(f"/compras/ordenes/{pk}/")

    def lista_cargada(self):
        src = self.driver.page_source
        return "orden" in src.lower() or "compra" in src.lower() or "table" in src


class ProveedoresPage(BasePage):

    def open(self):
        return self.go("/compras/proveedores/")

    def open_crear(self):
        return self.go("/compras/proveedores/crear/")

    def lista_cargada(self):
        return "proveedor" in self.driver.page_source.lower()
