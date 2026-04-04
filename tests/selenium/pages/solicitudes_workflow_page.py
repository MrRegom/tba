"""Page Objects detallados para flujos visuales de solicitudes."""
from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from .base_page import BasePage


class SolicitudWorkflowPage(BasePage):
    FORM = (By.ID, "formSolicitud")
    TIPO_SOLICITUD = (By.NAME, "tipo_solicitud")
    FECHA_REQUERIDA = (By.NAME, "fecha_requerida")
    DEPARTAMENTO = (By.NAME, "departamento")
    AREA = (By.NAME, "area")
    BODEGA = (By.NAME, "bodega_origen")
    MOTIVO = (By.NAME, "motivo")
    OBSERVACIONES = (By.NAME, "observaciones")
    BTN_AGREGAR_ARTICULO = (By.ID, "btn-agregar-articulo")
    MODAL_ARTICULOS = (By.ID, "modalSeleccionItem")
    BUSCADOR_ARTICULOS = (By.ID, "buscar-item")
    BTN_GUARDAR = (By.XPATH, "//form[@id='formSolicitud']//button[@type='submit']")
    ALERTS = (By.CSS_SELECTOR, ".alert")
    BADGES = (By.CSS_SELECTOR, ".badge")
    HISTORIAL_TABLA = (By.CSS_SELECTOR, ".table tbody tr")

    def open_create(self):
        return self.go("/solicitudes/articulos/crear/")

    def open_detail(self, solicitud_id: int, origen: str = "admin"):
        return self.go(f"/solicitudes/{solicitud_id}/?origen={origen}")

    def open_approve(self, solicitud_id: int):
        return self.go(f"/solicitudes/{solicitud_id}/aprobar/")

    def open_reject(self, solicitud_id: int):
        return self.go(f"/solicitudes/{solicitud_id}/rechazar/")

    def open_dispatch(self, solicitud_id: int):
        return self.go(f"/solicitudes/{solicitud_id}/despachar/")

    def select_option_by_text_safe(self, locator, text):
        select = Select(self.find(locator))
        select.select_by_visible_text(text)

    def select_first_nonempty_option(self, locator):
        select = Select(self.find(locator))
        for option in select.options:
            if option.get_attribute("value"):
                select.select_by_value(option.get_attribute("value"))
                return option.text.strip()
        raise AssertionError(f"No hay opciones disponibles para {locator}")

    def _select_text_or_first(self, locator, value):
        if value:
            try:
                self.select_option_by_text_safe(locator, value)
                return value
            except Exception:
                pass
        return self.select_first_nonempty_option(locator)

    def fill_header_form(self, *, tipo_solicitud=None, fecha_requerida, departamento=None, area=None, bodega=None, motivo, observaciones=""):
        self._select_text_or_first(self.TIPO_SOLICITUD, tipo_solicitud)
        self.set_value(self.FECHA_REQUERIDA, fecha_requerida)
        self._select_text_or_first(self.DEPARTAMENTO, departamento)
        self._select_text_or_first(self.AREA, area)
        self._select_text_or_first(self.BODEGA, bodega)
        self.type_text(self.MOTIVO, motivo)
        if observaciones:
            self.type_text(self.OBSERVACIONES, observaciones)

    def add_articulo(self, nombre_articulo: str, cantidad: str, observaciones: str = ""):
        self.click(self.BTN_AGREGAR_ARTICULO)
        self.find_visible(self.MODAL_ARTICULOS)
        self.type_text(self.BUSCADOR_ARTICULOS, nombre_articulo)
        row_button = (
            By.XPATH,
            f"//tbody[@id='tbody-lista-items']//tr[contains(., '{nombre_articulo}')]//button[contains(@class,'btn-seleccionar-item')]",
        )
        self.click(row_button)
        qty_locator = (
            By.CSS_SELECTOR,
            "input[name^='detalles'][name$='[cantidad_solicitada]']",
        )
        self.wait_for_element_count_at_least(qty_locator, minimum=1)
        qty_inputs = self.driver.find_elements(*qty_locator)
        qty_input = qty_inputs[-1]
        self.click_element(qty_input)
        qty_input.send_keys(Keys.CONTROL, "a")
        qty_input.send_keys(str(cantidad))
        if observaciones:
            obs_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name^='detalles'][name$='[observaciones]']")
            obs_input = obs_inputs[-1]
            self.click_element(obs_input)
            obs_input.send_keys(observaciones)

    def submit(self):
        buttons = self.driver.find_elements(By.XPATH, "//form//button[@type='submit']")
        visible_buttons = [button for button in buttons if button.is_displayed()]
        target = visible_buttons[-1] if visible_buttons else self.find(self.BTN_GUARDAR)
        self.click_element(target)

    def latest_alert_text(self):
        alerts = self.driver.find_elements(*self.ALERTS)
        return alerts[0].text if alerts else ""

    def invalid_feedback_text(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".invalid-feedback, .text-danger, .validation-error")
        return " | ".join(el.text for el in elements if el.text.strip())

    def current_status_text(self):
        badges = self.driver.find_elements(*self.BADGES)
        texts = [badge.text.strip() for badge in badges if badge.text.strip()]
        return " | ".join(texts)

    def history_contains(self, text: str) -> bool:
        return text in self.driver.page_source

    def approval_input(self, detalle_id: int):
        return (By.ID, f"id_cantidad_aprobada_{detalle_id}")

    def dispatch_input(self, detalle_id: int):
        return (By.ID, f"id_cantidad_despachada_{detalle_id}")

    def set_numeric_field(self, locator, value: str):
        element = self.find(locator)
        self.click_element(element)
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(str(value))

    def set_textarea(self, name: str, value: str):
        self.type_text((By.NAME, name), value)

    def wait_for_redirect_to_detail(self, solicitud_id: int):
        self.wait_until(EC.url_contains(f"/solicitudes/{solicitud_id}/"), timeout=10)

    def extract_created_solicitud_id(self) -> int:
        current_url = self.driver.current_url.rstrip("/")
        return int(current_url.split("/")[-1].split("?")[0])
