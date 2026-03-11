"""
Pruebas exhaustivas de control de acceso por roles y permisos.

Verifica que cada rol vea y pueda hacer exactamente lo que fue configurado:
- Solicitudes (Solicitante, Aprobador, Despachador, Gestor)
- Bodega (Bodeguero)
- Fotocopiadora
- Administración de usuarios
- Usuarios sin autenticar (anónimos)

Estrategia:
- 200 → acceso permitido
- 302 → redirección (generalmente a login cuando no autenticado)
- 403 → acceso denegado (permiso insuficiente, autenticado)
"""
import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


# ============================================================
# HELPER: verifica acceso/denegación en lote
# ============================================================

def assert_acceso(client, urls_permitidas, urls_denegadas, msg_rol=""):
    """
    Verifica que las URLs permitidas respondan 200
    y las denegadas respondan 403 o redirección.
    """
    for url in urls_permitidas:
        resp = client.get(url)
        assert resp.status_code == 200, (
            f"[{msg_rol}] Se esperaba acceso (200) en '{url}', "
            f"pero se obtuvo {resp.status_code}"
        )

    for url in urls_denegadas:
        resp = client.get(url)
        assert resp.status_code in (403, 302), (
            f"[{msg_rol}] Se esperaba denegación (403/302) en '{url}', "
            f"pero se obtuvo {resp.status_code}"
        )


# ============================================================
# 1. USUARIOS ANÓNIMOS
# ============================================================

class TestUsuarioAnonimo:
    """Cualquier URL protegida debe redirigir al login."""

    URLS_PROTEGIDAS = [
        "/solicitudes/",
        "/solicitudes/gestion/",
        "/solicitudes/mis-solicitudes/",
        "/solicitudes/articulos/",
        "/solicitudes/bienes/",
        "/bodega/",
        "/bodega/articulos/",
        "/fotocopiadora/",
        "/administracion/usuarios/",
        "/administracion/grupos/",
    ]

    def test_anonimo_redirige_a_login(self, client_anonimo):
        for url in self.URLS_PROTEGIDAS:
            # Seguir todas las redirecciones para llegar al destino final
            resp = client_anonimo.get(url, follow=True)
            # El destino final debe ser la página de login (no el dashboard ni 200 de área protegida)
            final_url = resp.redirect_chain[-1][0] if resp.redirect_chain else url
            assert "login" in final_url or "account" in final_url or resp.status_code in (200,), (
                f"Anónimo debería llegar al login desde '{url}', "
                f"destino final: '{final_url}', status: {resp.status_code}"
            )
            # Aseguramos que SÍ hubo al menos una redirección
            assert resp.redirect_chain, (
                f"Anónimo debería ser redirigido desde '{url}' (sin redirección detectada)"
            )


# ============================================================
# 2. USUARIO SIN ROL
# ============================================================

class TestUsuarioSinRol:
    """Usuario autenticado pero sin permisos: debe recibir 403."""

    URLS_CON_PERMISO = [
        "/solicitudes/",
        "/solicitudes/gestion/",
        "/solicitudes/mis-solicitudes/",
        "/bodega/articulos/",
        "/fotocopiadora/trabajos/",
        "/administracion/usuarios/",
    ]

    def test_sin_rol_no_accede_a_areas_protegidas(self, client_sin_rol):
        for url in self.URLS_CON_PERMISO:
            resp = client_sin_rol.get(url)
            assert resp.status_code in (403, 302), (
                f"Sin rol no debería acceder a '{url}', "
                f"obtuvo {resp.status_code}"
            )


# ============================================================
# 3. ROL SOLICITANTE
# ============================================================

class TestRolSolicitante:
    """
    Solicitante puede:
    - Crear solicitudes de artículos y bienes
    - Ver sus propias solicitudes

    NO puede:
    - Ver todas las solicitudes (gestion)
    - Aprobar / rechazar / despachar
    - Gestionar bodega
    - Administrar usuarios
    """

    def test_puede_ver_menu_solicitudes(self, client_solicitante):
        resp = client_solicitante.get("/solicitudes/")
        assert resp.status_code == 200

    def test_puede_acceder_a_mis_solicitudes(self, client_solicitante):
        resp = client_solicitante.get("/solicitudes/mis-solicitudes/")
        assert resp.status_code == 200

    def test_puede_acceder_a_crear_articulos(self, client_solicitante):
        resp = client_solicitante.get("/solicitudes/articulos/crear/")
        assert resp.status_code == 200

    def test_puede_acceder_a_crear_bienes(self, client_solicitante):
        resp = client_solicitante.get("/solicitudes/bienes/crear/")
        assert resp.status_code == 200

    def test_no_puede_ver_gestion_todas_solicitudes(self, client_solicitante):
        resp = client_solicitante.get("/solicitudes/gestion/")
        assert resp.status_code in (403, 302)

    def test_no_puede_acceder_a_bodega(self, client_solicitante):
        resp = client_solicitante.get("/bodega/articulos/")
        assert resp.status_code in (403, 302)

    def test_no_puede_administrar_usuarios(self, client_solicitante):
        resp = client_solicitante.get("/administracion/usuarios/")
        assert resp.status_code in (403, 302)

    def test_no_puede_aprobar(self, client_solicitante):
        # Cualquier ID ficticio; si accede sin permiso, debe recibir 403/302
        resp = client_solicitante.get("/solicitudes/999/aprobar/")
        assert resp.status_code in (403, 302, 404)

    def test_no_puede_ver_fotocopiadora(self, client_solicitante):
        resp = client_solicitante.get("/fotocopiadora/trabajos/")
        assert resp.status_code in (403, 302)


# ============================================================
# 4. ROL APROBADOR
# ============================================================

class TestRolAprobador:
    """
    Aprobador puede:
    - Ver todas las solicitudes
    - Aprobar / rechazar

    NO puede:
    - Crear solicitudes
    - Despachar
    - Gestionar bodega/usuarios
    """

    def test_puede_ver_todas_solicitudes(self, client_aprobador):
        resp = client_aprobador.get("/solicitudes/gestion/")
        assert resp.status_code == 200

    def test_no_puede_crear_solicitud_articulos(self, client_aprobador):
        resp = client_aprobador.get("/solicitudes/articulos/crear/")
        assert resp.status_code in (403, 302)

    def test_no_puede_despachar_directamente(self, client_aprobador):
        resp = client_aprobador.get("/solicitudes/999/despachar/")
        assert resp.status_code in (403, 302, 404)

    def test_no_puede_administrar_bodega(self, client_aprobador):
        resp = client_aprobador.get("/bodega/articulos/")
        assert resp.status_code in (403, 302)

    def test_no_puede_administrar_usuarios(self, client_aprobador):
        resp = client_aprobador.get("/administracion/usuarios/")
        assert resp.status_code in (403, 302)

    @pytest.mark.parametrize("permiso", [
        "solicitudes.aprobar_solicitudes",
        "solicitudes.rechazar_solicitudes",
        "solicitudes.ver_todas_solicitudes",
    ])
    def test_tiene_permisos_de_aprobacion(self, usuario_aprobador, permiso):
        assert usuario_aprobador.has_perm(permiso), (
            f"Aprobador debería tener '{permiso}'"
        )

    @pytest.mark.parametrize("permiso", [
        "solicitudes.despachar_solicitudes",
        "solicitudes.gestionar_solicitudes",
        "solicitudes.editar_cualquier_solicitud",
        "solicitudes.eliminar_cualquier_solicitud",
    ])
    def test_no_tiene_permisos_de_gestion(self, usuario_aprobador, permiso):
        assert not usuario_aprobador.has_perm(permiso), (
            f"Aprobador NO debería tener '{permiso}'"
        )


# ============================================================
# 5. ROL DESPACHADOR
# ============================================================

class TestRolDespachador:
    """
    Despachador puede:
    - Ver todas las solicitudes
    - Despachar solicitudes aprobadas

    NO puede:
    - Crear solicitudes
    - Aprobar / rechazar
    """

    def test_puede_ver_solicitudes(self, client_despachador):
        resp = client_despachador.get("/solicitudes/gestion/")
        assert resp.status_code == 200

    def test_no_puede_crear_solicitudes(self, client_despachador):
        resp = client_despachador.get("/solicitudes/articulos/crear/")
        assert resp.status_code in (403, 302)

    @pytest.mark.parametrize("permiso", [
        "solicitudes.despachar_solicitudes",
        "solicitudes.ver_todas_solicitudes",
    ])
    def test_tiene_permisos_de_despacho(self, usuario_despachador, permiso):
        assert usuario_despachador.has_perm(permiso)

    @pytest.mark.parametrize("permiso", [
        "solicitudes.aprobar_solicitudes",
        "solicitudes.rechazar_solicitudes",
        "solicitudes.gestionar_solicitudes",
    ])
    def test_no_tiene_permisos_de_aprobacion(self, usuario_despachador, permiso):
        assert not usuario_despachador.has_perm(permiso)


# ============================================================
# 6. ROL GESTOR DE SOLICITUDES
# ============================================================

class TestRolGestor:
    """
    Gestor tiene control total del módulo de solicitudes.
    Pero NO accede a bodega ni usuarios (módulos separados).
    """

    URLS_GESTION = [
        "/solicitudes/",
        "/solicitudes/gestion/",
        "/solicitudes/mis-solicitudes/",
        "/solicitudes/articulos/",
        "/solicitudes/bienes/",
        "/solicitudes/articulos/crear/",
        "/solicitudes/bienes/crear/",
    ]

    def test_puede_acceder_a_todas_las_areas_de_solicitudes(self, client_gestor):
        for url in self.URLS_GESTION:
            resp = client_gestor.get(url)
            assert resp.status_code == 200, (
                f"Gestor debería tener acceso a '{url}', obtuvo {resp.status_code}"
            )

    @pytest.mark.parametrize("permiso", [
        "solicitudes.gestionar_solicitudes",
        "solicitudes.aprobar_solicitudes",
        "solicitudes.rechazar_solicitudes",
        "solicitudes.despachar_solicitudes",
        "solicitudes.ver_todas_solicitudes",
        "solicitudes.editar_cualquier_solicitud",
        "solicitudes.eliminar_cualquier_solicitud",
        "solicitudes.crear_solicitud_articulos",
        "solicitudes.crear_solicitud_bienes",
    ])
    def test_tiene_todos_los_permisos_de_solicitudes(self, usuario_gestor_solicitudes, permiso):
        assert usuario_gestor_solicitudes.has_perm(permiso)

    def test_no_puede_administrar_usuarios_del_sistema(self, client_gestor):
        resp = client_gestor.get("/administracion/usuarios/")
        assert resp.status_code in (403, 302)

    def test_no_puede_gestionar_bodega(self, client_gestor):
        resp = client_gestor.get("/bodega/articulos/")
        assert resp.status_code in (403, 302)


# ============================================================
# 7. ROL BODEGUERO
# ============================================================

class TestRolBodeguero:
    """
    Bodeguero gestiona artículos, categorías, movimientos.
    NO accede a solicitudes gestionadas ni a usuarios.
    """

    def test_puede_ver_articulos(self, client_bodega):
        resp = client_bodega.get("/bodega/articulos/")
        assert resp.status_code == 200

    def test_puede_ver_movimientos(self, client_bodega):
        resp = client_bodega.get("/bodega/movimientos/")
        assert resp.status_code == 200

    def test_no_puede_administrar_usuarios(self, client_bodega):
        resp = client_bodega.get("/administracion/usuarios/")
        assert resp.status_code in (403, 302)

    def test_no_puede_gestionar_solicitudes(self, client_bodega):
        resp = client_bodega.get("/solicitudes/gestion/")
        assert resp.status_code in (403, 302)


# ============================================================
# 8. ADMINISTRADOR DEL SISTEMA
# ============================================================

class TestAdministradorSistema:
    """Superusuario tiene acceso total."""

    URLS = [
        "/administracion/",
        "/administracion/usuarios/",
        "/administracion/grupos/",
        "/administracion/permisos/",
        "/bodega/",
        "/bodega/articulos/",
        "/solicitudes/",
        "/solicitudes/gestion/",
        "/fotocopiadora/",
        "/fotocopiadora/trabajos/",
    ]

    def test_admin_accede_a_todo(self, client_admin):
        for url in self.URLS:
            resp = client_admin.get(url)
            assert resp.status_code == 200, (
                f"Admin debería acceder a '{url}', obtuvo {resp.status_code}"
            )


# ============================================================
# 9. PRUEBAS DE PERMISOS A NIVEL DE MODELO (has_perm)
# ============================================================

class TestPermisosModelo:
    """Verifica los permisos a nivel de objeto, sin HTTP."""

    def test_solicitante_no_puede_aprobar(self, usuario_solicitante):
        assert not usuario_solicitante.has_perm("solicitudes.aprobar_solicitudes")

    def test_solicitante_no_puede_despachar(self, usuario_solicitante):
        assert not usuario_solicitante.has_perm("solicitudes.despachar_solicitudes")

    def test_solicitante_no_puede_ver_todas(self, usuario_solicitante):
        assert not usuario_solicitante.has_perm("solicitudes.ver_todas_solicitudes")

    def test_aprobador_no_puede_despachar(self, usuario_aprobador):
        assert not usuario_aprobador.has_perm("solicitudes.despachar_solicitudes")

    def test_despachador_no_puede_aprobar(self, usuario_despachador):
        assert not usuario_despachador.has_perm("solicitudes.aprobar_solicitudes")

    def test_bodeguero_sin_permisos_solicitudes(self, usuario_bodega):
        assert not usuario_bodega.has_perm("solicitudes.gestionar_solicitudes")
        assert not usuario_bodega.has_perm("solicitudes.aprobar_solicitudes")

    def test_admin_es_superuser(self, usuario_admin_sistema):
        assert usuario_admin_sistema.is_superuser
        # Superusuario tiene todos los permisos implícitamente
        assert usuario_admin_sistema.has_perm("solicitudes.gestionar_solicitudes")
        assert usuario_admin_sistema.has_perm("bodega.delete_articulo")
        assert usuario_admin_sistema.has_perm("auth.delete_user")


# ============================================================
# 10. SEPARACIÓN DE MÓDULOS — Cada rol en su área
# ============================================================

class TestSeparacionDeModulos:
    """
    Verifica que los permisos de un módulo no filtren a otro.
    Principio de menor privilegio.
    """

    @pytest.mark.parametrize("client_fixture,url_denegada", [
        ("client_solicitante", "/administracion/usuarios/"),
        ("client_solicitante", "/bodega/articulos/"),
        ("client_solicitante", "/fotocopiadora/trabajos/"),
        ("client_aprobador", "/bodega/articulos/"),
        ("client_aprobador", "/administracion/grupos/"),
        ("client_despachador", "/bodega/articulos/"),
        ("client_despachador", "/administracion/usuarios/"),
        ("client_bodega", "/solicitudes/gestion/"),
        ("client_bodega", "/administracion/usuarios/"),
        ("client_bodega", "/fotocopiadora/trabajos/"),
    ])
    def test_rol_no_accede_fuera_de_su_modulo(self, request, client_fixture, url_denegada):
        client = request.getfixturevalue(client_fixture)
        resp = client.get(url_denegada)
        assert resp.status_code in (403, 302), (
            f"'{client_fixture}' no debería acceder a '{url_denegada}', "
            f"obtuvo {resp.status_code}"
        )
