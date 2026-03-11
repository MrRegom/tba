"""
Pruebas UI de autenticacion con Selenium.

Usa live_server de pytest-django. No requiere servidor externo.
"""
import pytest
from django.contrib.auth.models import User
from .conftest import inject_session, selenium_login_form
from .pages.login_page import LoginPage
from .pages.dashboard_page import DashboardPage

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


class TestLoginFormUI:
    """Pruebas del formulario de login."""

    def test_login_exitoso_redirige_al_dashboard(self, driver, live_server, db):
        User.objects.create_user("ui_user1", password="Test1234!")
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        page.login("ui_user1", "Test1234!")
        dashboard = DashboardPage(driver, base_url=live_server.url)
        assert dashboard.is_authenticated(), (
            f"Login exitoso debe redirigir al dashboard, URL actual: {driver.current_url}"
        )

    def test_credenciales_invalidas_no_redirigen(self, driver, live_server, db):
        User.objects.create_user("ui_user2", password="Test1234!")
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        page.login("ui_user2", "WRONGPASS")
        assert page.is_login_page(), "Credenciales invalidas deben mantenerse en login"

    def test_campos_vacios_no_autentican(self, driver, live_server, db):
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        page.login("", "")
        assert page.is_login_page(), "Campos vacios no deben autenticar"

    def test_xss_en_campo_login_no_ejecuta_script(self, driver, live_server, db):
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        page.login("<script>alert('xss')</script>", "wrong")
        assert page.no_alert_present(), "XSS ejecutado: alerta JS detectada"

    def test_formulario_tiene_csrf_token(self, driver, live_server, db):
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        assert "csrfmiddlewaretoken" in page.page_source(), "Falta token CSRF en formulario"

    def test_campo_password_es_tipo_password(self, driver, live_server, db):
        page = LoginPage(driver, base_url=live_server.url)
        page.open()
        el = driver.find_element("name", "password")
        assert el.get_attribute("type") == "password"

    def test_logout_invalida_sesion(self, driver, live_server, db):
        user = User.objects.create_user("ui_logout_user", password="Test1234!")
        inject_session(driver, live_server, user)
        driver.get(f"{live_server.url}/solicitudes/")
        assert "login" not in driver.current_url, "Deberia estar autenticado antes del logout"

        driver.delete_all_cookies()
        driver.get(f"{live_server.url}/solicitudes/")
        url = driver.current_url
        assert "login" in url or "account" in url, "Sin sesion debe redirigir al login"

    def test_multiples_intentos_fallidos_no_causan_500(self, driver, live_server, db):
        User.objects.create_user("brute_target", password="Real123!")
        page = LoginPage(driver, base_url=live_server.url)
        for i in range(5):
            page.open()
            page.login("brute_target", f"wrong{i}")
            assert "500" not in driver.title, f"Error 500 en intento {i+1}"


class TestSesionSeguridad:
    """Pruebas de seguridad de sesion."""

    def test_inyeccion_de_sesion_funciona(self, driver, live_server, db):
        user = User.objects.create_user("inj_user", password="Test1234!")
        inject_session(driver, live_server, user)
        driver.get(f"{live_server.url}/solicitudes/")
        assert "login" not in driver.current_url

    def test_sin_sesion_redirige_a_login(self, driver, live_server, db):
        driver.get(f"{live_server.url}/solicitudes/")
        url = driver.current_url
        assert "login" in url or "account" in url

    def test_url_login_usa_path_estandar(self, driver, live_server, db):
        driver.get(f"{live_server.url}/account/login/")
        assert "/account/login" in driver.current_url
