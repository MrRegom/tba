"""Page Object base para todas las paginas del sistema TBA."""
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Pausa visual entre acciones. Controlar con: SELENIUM_PAUSE=2 pytest ...
_PAUSE = float(os.environ.get("SELENIUM_PAUSE", "0"))


class BasePage:

    def __init__(self, driver, base_url="", timeout=10):
        self.driver = driver
        self.base_url = base_url or getattr(driver, "_base_url", "http://127.0.0.1:8000")
        self.wait = WebDriverWait(driver, timeout)

    def _pause(self):
        if _PAUSE > 0:
            time.sleep(_PAUSE)

    def go(self, path):
        self._pause()
        self.driver.get(f"{self.base_url}{path}")
        return self

    def find(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all(self, locator):
        return self.wait.until(lambda d: d.find_elements(*locator))

    def click(self, locator):
        self._pause()
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.click_element(element)

    def click_element(self, element: WebElement):
        self._pause()
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self.wait.until(lambda d: element.is_displayed() and element.is_enabled())
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def type_text(self, locator, text):
        self._pause()
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def set_value(self, locator, text):
        self._pause()
        element = self.find(locator)
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            element,
            text,
        )

    def scroll_into_view(self, locator):
        element = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self._pause()
        return element

    def get_text(self, locator):
        return self.find(locator).text

    def get_value(self, locator):
        return self.find(locator).get_attribute("value")

    def is_visible(self, locator):
        try:
            self.wait.until(EC.visibility_of_element_located(locator))
            return True
        except Exception:
            return False

    def current_url(self):
        return self.driver.current_url

    def page_source(self):
        return self.driver.page_source

    def title(self):
        return self.driver.title

    def has_text(self, text):
        return text in self.driver.page_source

    def no_server_error(self):
        """Retorna True si la pagina no tiene error 500/403."""
        src = self.driver.page_source
        title = self.driver.title
        return "500" not in title and "403" not in title and "Server Error" not in src

    def is_redirected_to_login(self):
        url = self.driver.current_url
        return "login" in url or "account" in url

    def screenshot(self, name):
        os.makedirs("tests/selenium/screenshots", exist_ok=True)
        self.driver.save_screenshot(f"tests/selenium/screenshots/{name}.png")

    def select_option(self, locator, value):
        from selenium.webdriver.support.ui import Select
        el = self.find(locator)
        Select(el).select_by_value(value)

    def select_option_by_text(self, locator, text):
        from selenium.webdriver.support.ui import Select
        el = self.find(locator)
        Select(el).select_by_visible_text(text)

    def wait_for_url_contains(self, fragment, timeout=10):
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains(fragment)
        )

    def wait_for_element_count_at_least(self, locator, minimum=1, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(*locator)) >= minimum
        )

    def wait_for_text(self, text, timeout=10):
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{text}')]"))
        )

    def wait_until(self, condition, timeout=10):
        return WebDriverWait(self.driver, timeout).until(condition)

    def element_contains_text(self, locator, text):
        return text in self.find(locator).text

    def no_alert_present(self):
        """Retorna True si no hay alertas JS activas."""
        try:
            self.driver.switch_to.alert.dismiss()
            return False
        except Exception:
            return True
