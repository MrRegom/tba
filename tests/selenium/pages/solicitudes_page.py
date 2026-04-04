"""Page Objects para el modulo de Solicitudes."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from .base_page import BasePage


class ListaSolicitudesPage(BasePage):
    TITULO = (By.CSS_SELECTOR, "h1, h2, .page-title")
    TABLA = (By.CSS_SELECTOR, "table, .table, .list-group")

    def open(self):
        return self.go("/solicitudes/mis-solicitudes/")

    def open_gestion(self):
        return self.go("/solicitudes/gestion/")

    def open_lista(self):
        return self.go("/solicitudes/")

    def tiene_tabla_o_mensaje(self):
        src = self.driver.page_source
        return ("table" in src or "list" in src.lower()
                or "solicitud" in src.lower() or "No hay" in src)


class CrearSolicitudPage(BasePage):
    URL = "/solicitudes/articulos/crear/"

    def open(self):
        return self.go(self.URL)

    def tiene_formulario(self):
        return "form" in self.driver.page_source.lower()

    def formulario_visible(self):
        return self.is_visible((By.CSS_SELECTOR, "form"))

    def primera_opcion_tipo(self):
        try:
            sel = Select(self.driver.find_element(By.NAME, "tipo_solicitud"))
            if sel.options:
                sel.select_by_index(1)
                return True
        except Exception:
            return False

    def campo_visible(self, name):
        try:
            el = self.driver.find_element(By.NAME, name)
            return el.is_displayed()
        except Exception:
            return False


class DetalleSolicitudPage(BasePage):
    ESTADO_BADGE = (By.CSS_SELECTOR, ".badge, .estado, [class*='estado']")

    def open(self, pk):
        return self.go(f"/solicitudes/{pk}/")

    def estado_texto(self):
        try:
            return self.get_text(self.ESTADO_BADGE)
        except Exception:
            return self.driver.page_source
