"""Page Object para la pagina de login (allauth)."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    USERNAME = (By.NAME, "login")
    PASSWORD = (By.NAME, "password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def open(self):
        return self.go("/account/login/")

    def login(self, username, password):
        self.type_text(self.USERNAME, username)
        self.type_text(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def is_login_page(self):
        return "login" in self.driver.current_url or "account" in self.driver.current_url
