"""Page Object para el dashboard / pagina principal."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class DashboardPage(BasePage):

    def is_authenticated(self):
        url = self.driver.current_url
        return "login" not in url and "account" not in url

    def visible_links(self):
        return [a.get_attribute("href") for a in self.driver.find_elements(By.TAG_NAME, "a")]

    def has_link_to(self, path):
        return any(path in (href or "") for href in self.visible_links())

    def navigate(self, path):
        return self.go(path)
