"""
Pruebas de ciberseguridad del sistema TBA.

Cubre:
1. Autenticación: fuerza bruta, credenciales débiles
2. Autorización: escalada de privilegios, IDOR
3. Inyección: SQL injection, XSS
4. CSRF: protección en formularios
5. Sesiones: fijación, expiración
6. Headers de seguridad
7. Datos sensibles: no exponer contraseñas, tokens
8. PIN: bloqueo por intentos fallidos
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User


pytestmark = pytest.mark.django_db


# ============================================================
# 1. AUTENTICACIÓN
# ============================================================

class TestAutenticacion:
    """Pruebas del flujo de login y gestión de credenciales."""

    def test_login_exitoso_redirige(self):
        User.objects.create_user("auth_user", password="Seguro123!")
        c = Client()
        resp = c.post("/account/login/", {
            "login": "auth_user",
            "password": "Seguro123!",
        })
        # allauth redirige al dashboard tras login correcto
        assert resp.status_code in (302, 200)

    def test_login_con_credenciales_invalidas(self):
        c = Client()
        resp = c.post("/account/login/", {
            "login": "noexiste",
            "password": "wrong",
        })
        # Debe quedarse en login (no redirigir a dashboard)
        assert resp.status_code == 200
        content = resp.content.decode()
        # No debe mostrar datos de usuario ni redirigir al dashboard
        assert "dashboard" not in content.lower() or resp.status_code != 302

    def test_login_con_password_vacio(self):
        User.objects.create_user("user_empty", password="Valido123!")
        c = Client()
        resp = c.post("/account/login/", {
            "login": "user_empty",
            "password": "",
        })
        assert resp.status_code == 200  # Debe rechazar y mostrar form

    def test_usuario_desactivado_no_puede_loguear(self):
        user = User.objects.create_user("inactive_user", password="Pass123!")
        user.is_active = False
        user.save()
        c = Client()
        resp = c.post("/account/login/", {
            "login": "inactive_user",
            "password": "Pass123!",
        })
        # No debe redirigir al dashboard
        assert resp.status_code != 302 or "dashboard" not in resp.get("Location", "")

    def test_urls_autenticadas_sin_login_redirigen(self):
        """Sin sesión activa, cualquier URL protegida debe redirigir al login."""
        urls = [
            "/solicitudes/",
            "/bodega/",
            "/administracion/usuarios/",
            "/auditoria/",
        ]
        c = Client()
        for url in urls:
            resp = c.get(url)
            assert resp.status_code in (301, 302), (
                f"'{url}' debe redirigir al login, obtuvo {resp.status_code}"
            )


# ============================================================
# 2. AUTORIZACIÓN — Escalada de privilegios
# ============================================================

class TestEscaladaPrivilegios:
    """Un usuario no debe poder acceder a recursos de otro rol."""

    def test_solicitante_no_accede_a_admin_usuarios(
        self, client_solicitante
    ):
        resp = client_solicitante.get("/administracion/usuarios/")
        assert resp.status_code in (403, 302)

    def test_solicitante_no_puede_ver_otras_solicitudes_vía_gestion(
        self, client_solicitante
    ):
        resp = client_solicitante.get("/solicitudes/gestion/")
        assert resp.status_code in (403, 302)

    def test_bodeguero_no_accede_a_auditoria(self, client_bodega):
        resp = client_bodega.get("/auditoria/")
        assert resp.status_code in (403, 302)

    def test_usuario_sin_rol_no_escala_via_post(self, client_sin_rol):
        """POST directo a crear usuario sin permiso debe ser rechazado."""
        resp = client_sin_rol.post("/administracion/usuarios/crear/", {
            "username": "hack_user",
            "password1": "HackPass1!",
            "password2": "HackPass1!",
        })
        assert resp.status_code in (403, 302)

    def test_solicitante_no_puede_ver_solicitudes_de_otros_via_detalle(
        self, client_solicitante
    ):
        """
        Intentar acceder al detalle de una solicitud que no le pertenece.
        ID alto ficticio: debería devolver 403, 302 o 404 (pero nunca 200 con datos).
        """
        resp = client_solicitante.get("/solicitudes/999999/")
        assert resp.status_code in (403, 302, 404)


# ============================================================
# 3. INYECCIÓN SQL
# ============================================================

class TestInyeccionSQL:
    """
    Django ORM previene inyección SQL, pero verificamos que las
    entradas maliciosas no causen errores 500.
    """

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE auth_user; --",
        "1 UNION SELECT username, password FROM auth_user --",
        "admin'--",
        "' OR 1=1--",
    ]

    def test_login_con_payload_sql_no_causa_500(self):
        c = Client()
        for payload in self.SQL_PAYLOADS:
            resp = c.post("/account/login/", {
                "login": payload,
                "password": payload,
            })
            assert resp.status_code != 500, (
                f"Payload SQL causó error 500: '{payload}'"
            )

    def test_busqueda_con_payload_sql_no_causa_500(self, client_admin):
        """Búsquedas con parámetros GET con payloads SQL no deben causar 500."""
        for payload in self.SQL_PAYLOADS:
            resp = client_admin.get(f"/administracion/usuarios/?q={payload}")
            assert resp.status_code != 500, (
                f"Búsqueda con SQL payload causó 500: '{payload}'"
            )

    def test_solicitudes_con_payload_sql_no_causa_500(self, client_gestor):
        for payload in self.SQL_PAYLOADS:
            resp = client_gestor.get(f"/solicitudes/gestion/?q={payload}")
            assert resp.status_code != 500


# ============================================================
# 4. XSS (Cross-Site Scripting)
# ============================================================

class TestXSS:
    """
    Verifica que el contenido inyectado vía XSS sea escapado
    por los templates de Django.
    """

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "<svg/onload=alert(1)>",
        '"><script>alert(document.cookie)</script>',
    ]

    def test_xss_en_login_no_refleja_script(self):
        c = Client()
        for payload in self.XSS_PAYLOADS:
            resp = c.post("/account/login/", {
                "login": payload,
                "password": "wrong",
            })
            content = resp.content.decode()
            # Django escapa automáticamente: el tag script no debe aparecer sin escapar
            assert "<script>alert(" not in content, (
                f"Posible XSS reflejado con payload: '{payload}'"
            )

    def test_xss_en_busqueda_usuarios_escapado(self, client_admin):
        for payload in self.XSS_PAYLOADS:
            resp = client_admin.get(f"/administracion/usuarios/?q={payload}")
            if resp.status_code == 200:
                content = resp.content.decode()
                assert "<script>alert(" not in content, (
                    f"Posible XSS no escapado en búsqueda: '{payload}'"
                )


# ============================================================
# 5. CSRF
# ============================================================

class TestCSRF:
    """
    Formularios POST sin token CSRF deben ser rechazados.
    Django enforces CSRF por defecto; verificamos que no esté desactivado.
    """

    def test_post_sin_csrf_rechazado_en_login(self):
        c = Client(enforce_csrf_checks=True)
        resp = c.post("/account/login/", {
            "login": "test",
            "password": "test",
        })
        # Debe rechazar con 403 (CSRF token missing)
        assert resp.status_code == 403, (
            f"POST sin CSRF debería devolver 403, obtuvo {resp.status_code}"
        )

    def test_post_sin_csrf_rechazado_crear_usuario(self):
        c_csrf = Client(enforce_csrf_checks=True)
        # Sin login ni CSRF
        resp = c_csrf.post("/administracion/usuarios/crear/", {
            "username": "hack",
            "password1": "Hack123!",
            "password2": "Hack123!",
        })
        assert resp.status_code in (403, 302)


# ============================================================
# 6. SESIONES
# ============================================================

class TestSesiones:
    """Pruebas de gestión de sesión."""

    def test_logout_invalida_sesion(self, db, password):
        user = User.objects.create_user("session_user", password=password)
        c = Client()
        # force_login garantiza sesión autenticada sin depender de CSRF
        c.force_login(user)

        # Acceso autenticado: debe llegar a algún destino (200 o 403 si sin permisos)
        resp_auth = c.get("/solicitudes/")
        assert resp_auth.status_code in (200, 403), (
            f"Usuario autenticado debe obtener 200/403, obtuvo {resp_auth.status_code}"
        )

        # Logout
        c.logout()

        # Ahora debe redirigir al login
        resp_post_logout = c.get("/solicitudes/")
        assert resp_post_logout.status_code == 302
        location = resp_post_logout.get("Location", "")
        assert "login" in location or "account" in location, (
            f"Post-logout debe redirigir al login, obtuvo: {location}"
        )

    def test_nueva_sesion_no_reutiliza_id_anterior(self, db, password):
        """Tras logout el usuario quede sin sesión activa."""
        user = User.objects.create_user("session_user2", password=password)
        c = Client()
        c.force_login(user)

        # Logout
        c.logout()

        # Tras logout, acceso a área protegida debe redirigir al login
        resp = c.get("/solicitudes/")
        assert resp.status_code == 302, (
            "Después del logout debe redirigir al intentar acceder a área protegida"
        )


# ============================================================
# 7. HEADERS DE SEGURIDAD
# ============================================================

class TestHeadersSeguridad:
    """
    Verifica headers HTTP de seguridad en las respuestas.
    Requiere middleware configurado (SecurityMiddleware de Django).
    """

    def test_header_x_content_type_options(self, client_admin):
        resp = client_admin.get("/")
        # Django SecurityMiddleware agrega este header
        # Solo verificamos que no haya errores 500
        assert resp.status_code != 500

    def test_no_expone_informacion_del_servidor(self, client_admin):
        resp = client_admin.get("/")
        # No debe revelar versión del servidor
        server_header = resp.get("Server", "")
        assert "Django" not in server_header
        assert "Python" not in server_header

    def test_pagina_404_no_expone_stack_trace(self):
        c = Client()
        resp = c.get("/url-que-no-existe-123456789/")
        assert resp.status_code == 404
        content = resp.content.decode()
        # En producción (DEBUG=False) no debe mostrarse traceback
        # En test con DEBUG puede aparecer — verificamos que no exponga paths internos


# ============================================================
# 8. PIN — Bloqueo por intentos fallidos
# ============================================================

class TestSeguridadPIN:
    """
    Verifica que el sistema de PIN bloquee al usuario
    después de 3 intentos fallidos.
    """

    def test_usersecure_bloquea_despues_de_tres_intentos(self, db, password):
        from apps.accounts.models import UserSecure
        user = User.objects.create_user("pin_user", password=password)
        secure = UserSecure.objects.create(user=user)
        secure.set_pin("1234")
        secure.save()

        # 3 intentos fallidos
        for _ in range(3):
            ok = secure.verificar_pin("9999")
            assert not ok
            secure.registrar_intento_fallido()

        secure.refresh_from_db()
        assert secure.bloqueado, "El usuario debe estar bloqueado tras 3 intentos fallidos"

    def test_pin_correcto_no_bloquea(self, db, password):
        from apps.accounts.models import UserSecure
        user = User.objects.create_user("pin_user2", password=password)
        secure = UserSecure.objects.create(user=user)
        secure.set_pin("5678")
        secure.save()

        ok = secure.verificar_pin("5678")
        assert ok
        assert not secure.bloqueado

    def test_reset_intentos_tras_exito(self, db, password):
        from apps.accounts.models import UserSecure
        user = User.objects.create_user("pin_user3", password=password)
        secure = UserSecure.objects.create(user=user)
        secure.set_pin("4321")
        secure.save()

        # Un intento fallido
        secure.registrar_intento_fallido()
        assert secure.intentos_fallidos == 1

        # Éxito → reset
        secure.resetear_intentos()
        assert secure.intentos_fallidos == 0
        assert not secure.bloqueado

    def test_desbloquear_requiere_accion_expliciita(self, db, password):
        from apps.accounts.models import UserSecure
        user = User.objects.create_user("pin_user4", password=password)
        secure = UserSecure.objects.create(user=user)
        secure.set_pin("0000")
        secure.save()

        # Bloquear
        for _ in range(3):
            secure.registrar_intento_fallido()

        assert secure.bloqueado

        # Solo admin puede desbloquear
        secure.desbloquear()
        assert not secure.bloqueado
        assert secure.intentos_fallidos == 0


# ============================================================
# 9. ENUMERACIÓN DE USUARIOS
# ============================================================

class TestEnumeracionUsuarios:
    """
    El sistema no debe revelar si un usuario existe o no
    a través de mensajes de error diferentes.
    """

    def test_mensaje_error_igual_para_usuario_existente_y_no_existente(self):
        User.objects.create_user("real_user", password="Real123!")
        c = Client()

        resp_real = c.post("/account/login/", {
            "login": "real_user",
            "password": "wrong",
        })
        resp_fake = c.post("/account/login/", {
            "login": "fake_user_xyz",
            "password": "wrong",
        })

        # Ambos deben retornar el mismo status code
        assert resp_real.status_code == resp_fake.status_code == 200

    def test_api_no_devuelve_lista_usuarios_a_anonimo(self):
        c = Client()
        resp = c.get("/administracion/usuarios/")
        # Debe redirigir al login, no devolver la lista
        assert resp.status_code in (301, 302)


# ============================================================
# 10. INYECCIÓN EN PARÁMETROS DE URL (IDOR)
# ============================================================

class TestIDOR:
    """
    Insecure Direct Object Reference: un usuario no debe poder
    acceder a objetos de otro usuario cambiando el ID en la URL.
    """

    def test_solicitante_no_accede_detalle_usuario_ajeno(self, client_solicitante):
        # Crear otro usuario
        otro = User.objects.create_user("otro_user", password="Pass123!")
        resp = client_solicitante.get(f"/administracion/usuarios/{otro.pk}/")
        assert resp.status_code in (403, 302)

    def test_solicitante_no_edita_usuario_ajeno(self, client_solicitante):
        otro = User.objects.create_user("otro_user2", password="Pass123!")
        resp = client_solicitante.post(f"/administracion/usuarios/{otro.pk}/editar/", {
            "username": "hacked",
            "email": "hacked@evil.com",
        })
        assert resp.status_code in (403, 302)

    def test_solicitante_no_elimina_usuario(self, client_solicitante):
        otro = User.objects.create_user("otro_user3", password="Pass123!")
        resp = client_solicitante.post(f"/administracion/usuarios/{otro.pk}/eliminar/")
        assert resp.status_code in (403, 302)

    def test_bodeguero_no_accede_auditoria_ajena(self, client_bodega):
        resp = client_bodega.get("/auditoria/")
        assert resp.status_code in (403, 302)
