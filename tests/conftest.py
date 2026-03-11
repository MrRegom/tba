"""
Fixtures globales para la suite de pruebas del sistema TBA.

Provee usuarios por rol, cliente autenticado y helpers de permisos.
"""
import pytest
from django.contrib.auth.models import User, Group, Permission
from django.test import Client


# ============================================================
# HELPERS
# ============================================================

def _crear_usuario(username, password="Test1234!", **kwargs):
    user = User.objects.create_user(username=username, password=password, **kwargs)
    return user


def _asignar_permisos(user, codenames: list[str]):
    """Asigna permisos por codename completo 'app.codename'."""
    for perm_str in codenames:
        app_label, codename = perm_str.split(".", 1)
        try:
            perm = Permission.objects.get(codename=codename, content_type__app_label=app_label)
            user.user_permissions.add(perm)
        except Permission.DoesNotExist:
            pass  # Permiso aún no creado (migraciones pendientes)
    user.save()


# ============================================================
# FIXTURES DE USUARIOS POR ROL
# ============================================================

@pytest.fixture
def password():
    return "Test1234!"


@pytest.fixture
def usuario_sin_rol(db, password):
    """Usuario autenticado sin ningún permiso ni grupo."""
    return _crear_usuario("sin_rol", password)


@pytest.fixture
def usuario_solicitante(db, password):
    """Usuario con rol Solicitante: solo crea y ve sus propias solicitudes."""
    user = _crear_usuario("solicitante", password, email="sol@test.cl")
    _asignar_permisos(user, [
        "solicitudes.view_solicitud",
        "solicitudes.add_solicitud",
        "solicitudes.ver_solicitudes_articulos",
        "solicitudes.crear_solicitud_articulos",
        "solicitudes.ver_solicitudes_bienes",
        "solicitudes.crear_solicitud_bienes",
        "solicitudes.ver_mis_solicitudes",
        "solicitudes.editar_mis_solicitudes",
        "solicitudes.eliminar_mis_solicitudes",
        "solicitudes.view_estadosolicitud",
        "solicitudes.view_tiposolicitud",
        "solicitudes.add_historialsolicitud",
        "solicitudes.view_historialsolicitud",
    ])
    return user


@pytest.fixture
def usuario_aprobador(db, password):
    """Usuario con rol Aprobador: puede aprobar/rechazar solicitudes."""
    user = _crear_usuario("aprobador", password, email="aprobador@test.cl")
    _asignar_permisos(user, [
        "solicitudes.view_solicitud",
        "solicitudes.ver_todas_solicitudes",
        "solicitudes.aprobar_solicitudes",
        "solicitudes.rechazar_solicitudes",
        "solicitudes.view_estadosolicitud",
        "solicitudes.view_tiposolicitud",
        "solicitudes.add_historialsolicitud",
        "solicitudes.view_historialsolicitud",
    ])
    return user


@pytest.fixture
def usuario_despachador(db, password):
    """Usuario con rol Despachador: solo puede despachar solicitudes aprobadas."""
    user = _crear_usuario("despachador", password, email="despacha@test.cl")
    _asignar_permisos(user, [
        "solicitudes.view_solicitud",
        "solicitudes.ver_todas_solicitudes",
        "solicitudes.despachar_solicitudes",
        "solicitudes.view_estadosolicitud",
        "solicitudes.view_tiposolicitud",
        "solicitudes.add_historialsolicitud",
        "solicitudes.view_historialsolicitud",
    ])
    return user


@pytest.fixture
def usuario_gestor_solicitudes(db, password):
    """Usuario con gestión completa del módulo de solicitudes."""
    user = _crear_usuario("gestor", password, email="gestor@test.cl")
    _asignar_permisos(user, [
        "solicitudes.view_solicitud",
        "solicitudes.add_solicitud",
        "solicitudes.change_solicitud",
        "solicitudes.delete_solicitud",
        "solicitudes.gestionar_solicitudes",
        "solicitudes.ver_todas_solicitudes",
        "solicitudes.aprobar_solicitudes",
        "solicitudes.rechazar_solicitudes",
        "solicitudes.despachar_solicitudes",
        "solicitudes.editar_cualquier_solicitud",
        "solicitudes.eliminar_cualquier_solicitud",
        "solicitudes.ver_solicitudes_articulos",
        "solicitudes.crear_solicitud_articulos",
        "solicitudes.ver_solicitudes_bienes",
        "solicitudes.crear_solicitud_bienes",
        "solicitudes.ver_mis_solicitudes",
        "solicitudes.editar_mis_solicitudes",
        "solicitudes.eliminar_mis_solicitudes",
        "solicitudes.view_estadosolicitud",
        "solicitudes.add_estadosolicitud",
        "solicitudes.change_estadosolicitud",
        "solicitudes.delete_estadosolicitud",
        "solicitudes.view_tiposolicitud",
        "solicitudes.add_tiposolicitud",
        "solicitudes.change_tiposolicitud",
        "solicitudes.delete_tiposolicitud",
        "solicitudes.view_historialsolicitud",
        "solicitudes.add_historialsolicitud",
        "solicitudes.change_historialsolicitud",
        "solicitudes.delete_historialsolicitud",
    ])
    return user


@pytest.fixture
def usuario_bodega(db, password):
    """Usuario con permisos del módulo de bodega."""
    user = _crear_usuario("bodeguero", password, email="bodega@test.cl")
    _asignar_permisos(user, [
        "bodega.view_articulo",
        "bodega.add_articulo",
        "bodega.change_articulo",
        "bodega.delete_articulo",
        "bodega.view_categoria",
        "bodega.view_unidadmedida",
        "bodega.view_movimiento",
        "bodega.add_movimiento",
        "bodega.view_entregaarticulo",
        "bodega.add_entregaarticulo",
    ])
    return user


@pytest.fixture
def usuario_fotocopiadora(db, password):
    """Usuario con permisos del módulo fotocopiadora."""
    user = _crear_usuario("foto_user", password, email="foto@test.cl")
    _asignar_permisos(user, [
        "fotocopiadora.view_trabajofotocopia",
        "fotocopiadora.add_trabajofotocopia",
        "fotocopiadora.change_trabajofotocopia",
    ])
    return user


@pytest.fixture
def usuario_admin_sistema(db, password):
    """Usuario administrador con todos los permisos."""
    user = User.objects.create_superuser(
        username="admin_sistema",
        password=password,
        email="admin@test.cl",
    )
    return user


# ============================================================
# CLIENTES HTTP AUTENTICADOS
# ============================================================

@pytest.fixture
def client_anonimo():
    return Client()


@pytest.fixture
def client_sin_rol(db, usuario_sin_rol, password):
    c = Client()
    c.login(username=usuario_sin_rol.username, password=password)
    return c


@pytest.fixture
def client_solicitante(db, usuario_solicitante, password):
    c = Client()
    c.login(username=usuario_solicitante.username, password=password)
    return c


@pytest.fixture
def client_aprobador(db, usuario_aprobador, password):
    c = Client()
    c.login(username=usuario_aprobador.username, password=password)
    return c


@pytest.fixture
def client_despachador(db, usuario_despachador, password):
    c = Client()
    c.login(username=usuario_despachador.username, password=password)
    return c


@pytest.fixture
def client_gestor(db, usuario_gestor_solicitudes, password):
    c = Client()
    c.login(username=usuario_gestor_solicitudes.username, password=password)
    return c


@pytest.fixture
def client_bodega(db, usuario_bodega, password):
    c = Client()
    c.login(username=usuario_bodega.username, password=password)
    return c


@pytest.fixture
def client_admin(db, usuario_admin_sistema, password):
    c = Client()
    c.login(username=usuario_admin_sistema.username, password=password)
    return c
