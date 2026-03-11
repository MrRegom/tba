"""
Fixtures de Selenium para la suite de pruebas UI.

Usa el fixture live_server de pytest-django para arrancar un servidor
real en un puerto libre, sin depender de un servidor externo.

Login via inyeccion de cookie de sesion Django (sin formulario allauth).

Ejecutar:
    pytest tests/selenium/ -m selenium --tb=short
    SELENIUM_HEADLESS=false pytest tests/selenium/ -m selenium -v
"""
import os
import pytest
from decimal import Decimal
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from django.contrib.auth.models import User, Permission
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY

from apps.solicitudes.models import EstadoSolicitud, TipoSolicitud, Departamento, Area
from apps.bodega.models import Bodega, Categoria, UnidadMedida, Articulo
from apps.bodega.models import Operacion, TipoMovimiento
from apps.compras.models import EstadoOrdenCompra, Proveedor, OrdenCompra
from apps.activos.models import (
    CategoriaActivo,
    EstadoActivo,
    Ubicacion,
    Proveniencia,
    Marca as MarcaActivo,
    TipoMovimientoActivo,
    Activo,
)
from apps.bajas_inventario.models import MotivoBaja

from .observation import VisualObserver


def _build_options(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-gpu")
    return opts


@pytest.fixture(scope="function")
def driver():
    headless = os.environ.get("SELENIUM_HEADLESS", "true").lower() == "true"
    opts = _build_options(headless=headless)
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        d = webdriver.Chrome(service=service, options=opts)
    except Exception:
        d = webdriver.Chrome(options=opts)
    d.implicitly_wait(8)
    yield d
    d.quit()


def inject_session(driver, live_server, user):
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    driver.get(live_server.url)
    driver.add_cookie({
        "name": "sessionid",
        "value": session.session_key,
        "secure": False,
        "path": "/",
    })
    return session.session_key


def selenium_login_form(driver, base_url, username, password):
    driver.get(f"{base_url}/account/login/")
    driver.find_element("name", "login").send_keys(username)
    driver.find_element("name", "password").send_keys(password)
    driver.find_element("css selector", "button[type='submit']").click()


def selenium_login(driver, username, password):
    selenium_login_form(driver, "http://127.0.0.1:8000", username, password)


def switch_user(driver, live_server, user):
    driver.delete_all_cookies()
    inject_session(driver, live_server, user)
    driver._base_url = live_server.url
    return driver


def _add_perms(user, perms_list):
    for p in perms_list:
        app, codename = p.split(".", 1)
        try:
            perm = Permission.objects.get(codename=codename, content_type__app_label=app)
            user.user_permissions.add(perm)
        except Permission.DoesNotExist:
            pass


def _add_all_app_perms(user, app_label):
    perms = Permission.objects.filter(content_type__app_label=app_label)
    user.user_permissions.add(*perms)


@pytest.fixture
def sel_admin(db):
    user, _ = User.objects.get_or_create(
        username="sel_admin",
        defaults={"email": "sel_admin@test.cl", "is_staff": True, "is_superuser": True}
    )
    user.set_password("Test1234!")
    user.save()
    return user


@pytest.fixture
def sel_solicitante(db):
    user, created = User.objects.get_or_create(
        username="sel_solicitante",
        defaults={"email": "sel_sol@test.cl", "first_name": "Juan", "last_name": "Perez"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_perms(user, [
        "solicitudes.view_solicitud",
        "solicitudes.add_solicitud",
        "solicitudes.ver_mis_solicitudes",
        "solicitudes.crear_solicitud_articulos",
        "solicitudes.ver_solicitudes_articulos",
        "solicitudes.view_estadosolicitud",
        "solicitudes.view_tiposolicitud",
    ])
    return user


@pytest.fixture
def sel_aprobador(db):
    user, created = User.objects.get_or_create(
        username="sel_aprobador",
        defaults={"email": "sel_apro@test.cl", "first_name": "Maria", "last_name": "Gonzalez"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_perms(user, [
        "solicitudes.view_solicitud",
        "solicitudes.gestionar_solicitudes",
        "solicitudes.ver_todas_solicitudes",
        "solicitudes.aprobar_solicitudes",
        "solicitudes.rechazar_solicitudes",
        "solicitudes.view_estadosolicitud",
    ])
    return user


@pytest.fixture
def sel_despachador(db):
    user, created = User.objects.get_or_create(
        username="sel_despachador",
        defaults={"email": "sel_des@test.cl", "first_name": "Pedro", "last_name": "Lopez"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_perms(user, [
        "solicitudes.view_solicitud",
        "solicitudes.gestionar_solicitudes",
        "solicitudes.ver_todas_solicitudes",
        "solicitudes.despachar_solicitudes",
        "solicitudes.view_estadosolicitud",
    ])
    return user


@pytest.fixture
def sel_bodeguero(db):
    user, created = User.objects.get_or_create(
        username="sel_bodeguero",
        defaults={"email": "sel_bod@test.cl", "first_name": "Carlos", "last_name": "Soto"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_all_app_perms(user, "bodega")
    return user


@pytest.fixture
def sel_comprador(db):
    user, created = User.objects.get_or_create(
        username="sel_comprador",
        defaults={"email": "sel_comp@test.cl", "first_name": "Claudia", "last_name": "Compra"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_all_app_perms(user, "compras")
    return user


@pytest.fixture
def sel_activos_operador(db):
    user, created = User.objects.get_or_create(
        username="sel_activos",
        defaults={"email": "sel_activos@test.cl", "first_name": "Ana", "last_name": "Activos"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_all_app_perms(user, "activos")
    return user


@pytest.fixture
def sel_bajas_operador(db):
    user, created = User.objects.get_or_create(
        username="sel_bajas",
        defaults={"email": "sel_bajas@test.cl", "first_name": "Bea", "last_name": "Bajas"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_all_app_perms(user, "bajas_inventario")
    return user


@pytest.fixture
def sel_admin_usuarios(db):
    user, created = User.objects.get_or_create(
        username="sel_admin_usuarios",
        defaults={"email": "sel_admin_users@test.cl", "first_name": "Alba", "last_name": "Admin"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_all_app_perms(user, "auth")
    _add_all_app_perms(user, "accounts")
    return user


@pytest.fixture
def sel_sin_rol(db):
    user, created = User.objects.get_or_create(
        username="sel_sin_rol",
        defaults={"email": "sel_norole@test.cl"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    return user


@pytest.fixture
def browser_admin(driver, live_server, sel_admin):
    inject_session(driver, live_server, sel_admin)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_solicitante(driver, live_server, sel_solicitante):
    inject_session(driver, live_server, sel_solicitante)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_aprobador(driver, live_server, sel_aprobador):
    inject_session(driver, live_server, sel_aprobador)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_despachador(driver, live_server, sel_despachador):
    inject_session(driver, live_server, sel_despachador)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_bodeguero(driver, live_server, sel_bodeguero):
    inject_session(driver, live_server, sel_bodeguero)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_comprador(driver, live_server, sel_comprador):
    inject_session(driver, live_server, sel_comprador)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_activos(driver, live_server, sel_activos_operador):
    inject_session(driver, live_server, sel_activos_operador)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_bajas(driver, live_server, sel_bajas_operador):
    inject_session(driver, live_server, sel_bajas_operador)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_admin_usuarios(driver, live_server, sel_admin_usuarios):
    inject_session(driver, live_server, sel_admin_usuarios)
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def browser_anonimo(driver, live_server):
    driver._base_url = live_server.url
    return driver


@pytest.fixture
def ui_observer(request, driver):
    enabled = os.environ.get("SELENIUM_OBSERVE", "true").lower() == "true"
    return VisualObserver(driver=driver, test_name=request.node.name, enabled=enabled)


@pytest.fixture
def solicitudes_ui_catalogo(db, sel_solicitante, sel_aprobador, sel_despachador):
    estado_pendiente, _ = EstadoSolicitud.objects.get_or_create(
        codigo="PENDIENTE",
        defaults={
            "nombre": "Pendiente",
            "es_inicial": True,
            "es_final": False,
            "requiere_accion": True,
            "color": "#ffc107",
            "activo": True,
            "eliminado": False,
        },
    )
    EstadoSolicitud.objects.get_or_create(
        codigo="APROBADA",
        defaults={
            "nombre": "Aprobada",
            "es_inicial": False,
            "es_final": False,
            "requiere_accion": True,
            "color": "#198754",
            "activo": True,
            "eliminado": False,
        },
    )
    EstadoSolicitud.objects.get_or_create(
        codigo="RECHAZAR",
        defaults={
            "nombre": "Rechazada",
            "es_inicial": False,
            "es_final": True,
            "requiere_accion": False,
            "color": "#dc3545",
            "activo": True,
            "eliminado": False,
        },
    )
    EstadoSolicitud.objects.get_or_create(
        codigo="DESPACHAR",
        defaults={
            "nombre": "Para despachar",
            "es_inicial": False,
            "es_final": False,
            "requiere_accion": True,
            "color": "#0dcaf0",
            "activo": True,
            "eliminado": False,
        },
    )
    EstadoSolicitud.objects.get_or_create(
        codigo="CANCELADA",
        defaults={
            "nombre": "Cancelada",
            "es_inicial": False,
            "es_final": True,
            "requiere_accion": False,
            "color": "#6c757d",
            "activo": True,
            "eliminado": False,
        },
    )
    EstadoSolicitud.objects.get_or_create(
        codigo="COMPRAR",
        defaults={
            "nombre": "En compras",
            "es_inicial": False,
            "es_final": False,
            "requiere_accion": True,
            "color": "#6610f2",
            "activo": True,
            "eliminado": False,
        },
    )
    tipo_solicitud, _ = TipoSolicitud.objects.get_or_create(
        codigo="ARTICULO",
        defaults={
            "nombre": "Solicitud de Articulos",
            "descripcion": "Catalogo base para pruebas UI",
            "requiere_aprobacion": True,
            "activo": True,
            "eliminado": False,
        },
    )
    departamento, _ = Departamento.objects.get_or_create(
        codigo="DEP-SEL",
        defaults={
            "nombre": "Departamento Selenium",
            "activo": True,
            "eliminado": False,
        },
    )
    area, _ = Area.objects.get_or_create(
        codigo="AREA-SEL",
        defaults={
            "nombre": "Area Selenium",
            "departamento": departamento,
            "activo": True,
            "eliminado": False,
        },
    )
    bodega, _ = Bodega.objects.get_or_create(
        codigo="BOD01",
        defaults={
            "nombre": "Bodega Central",
            "descripcion": "Bodega para Selenium",
            "responsable": sel_despachador,
            "activo": True,
            "eliminado": False,
        },
    )
    categoria, _ = Categoria.objects.get_or_create(
        codigo="CAT-SEL",
        defaults={"nombre": "Categoria Selenium", "activo": True, "eliminado": False},
    )
    unidad, _ = UnidadMedida.objects.get_or_create(
        codigo="UND-SEL",
        defaults={"nombre": "Unidad Selenium", "simbolo": "un", "activo": True, "eliminado": False},
    )
    articulo, _ = Articulo.objects.get_or_create(
        codigo="ART-SEL-001",
        defaults={
            "nombre": "Lapiz Selenium",
            "descripcion": "Articulo para pruebas visuales",
            "categoria": categoria,
            "unidad_medida": unidad,
            "ubicacion_fisica": bodega,
            "stock_actual": 80,
            "stock_minimo": 5,
            "stock_maximo": 500,
            "activo": True,
            "eliminado": False,
        },
    )
    return {
        "estado_pendiente": estado_pendiente,
        "tipo_solicitud": tipo_solicitud,
        "departamento": departamento,
        "area": area,
        "bodega": bodega,
        "articulo": articulo,
        "solicitante": sel_solicitante,
        "aprobador": sel_aprobador,
        "despachador": sel_despachador,
    }


@pytest.fixture
def erp_ui_catalogo(
    db,
    sel_admin,
    sel_bodeguero,
    sel_comprador,
    sel_activos_operador,
    sel_bajas_operador,
    sel_admin_usuarios,
):
    bodega, _ = Bodega.objects.get_or_create(
        codigo="BOD01",
        defaults={
            "nombre": "Bodega Central",
            "descripcion": "Bodega comun para pruebas UI",
            "responsable": sel_admin,
            "activo": True,
            "eliminado": False,
        },
    )
    categoria_bodega, _ = Categoria.objects.get_or_create(
        codigo="CAT-ERP",
        defaults={"nombre": "Categoria ERP", "activo": True, "eliminado": False},
    )
    unidad, _ = UnidadMedida.objects.get_or_create(
        codigo="UND",
        defaults={"nombre": "Unidad", "simbolo": "un", "activo": True, "eliminado": False},
    )
    operacion_entrada, _ = Operacion.objects.get_or_create(
        codigo="ENTRADA",
        defaults={"nombre": "Entrada", "tipo": "ENTRADA", "activo": True},
    )
    operacion_salida, _ = Operacion.objects.get_or_create(
        codigo="SALIDA",
        defaults={"nombre": "Salida", "tipo": "SALIDA", "activo": True},
    )
    tipo_mov_bodega, _ = TipoMovimiento.objects.get_or_create(
        codigo="AJUSTE",
        defaults={"nombre": "Ajuste", "descripcion": "Movimiento de prueba", "activo": True},
    )
    articulo_base, _ = Articulo.objects.get_or_create(
        codigo="ART-ERP-001",
        defaults={
            "nombre": "Cuaderno ERP",
            "descripcion": "Articulo base para pruebas UI",
            "categoria": categoria_bodega,
            "unidad_medida": unidad,
            "ubicacion_fisica": bodega,
            "stock_actual": Decimal("10"),
            "stock_minimo": Decimal("2"),
            "stock_maximo": Decimal("50"),
            "punto_reorden": Decimal("5"),
            "activo": True,
            "eliminado": False,
        },
    )

    estado_oc_pendiente, _ = EstadoOrdenCompra.objects.get_or_create(
        codigo="PENDIENTE",
        defaults={"nombre": "Pendiente", "color": "#ffc107", "activo": True, "eliminado": False},
    )
    proveedor_base, _ = Proveedor.objects.get_or_create(
        rut="76.000.000-1",
        defaults={
            "razon_social": "Proveedor ERP Base",
            "direccion": "Calle Base 123",
            "ciudad": "Santiago",
            "telefono": "+56911111111",
            "email": "proveedor.base@test.cl",
            "activo": True,
            "eliminado": False,
        },
    )
    orden_base, _ = OrdenCompra.objects.get_or_create(
        numero="OC-ERP-001",
        defaults={
            "fecha_orden": date.today(),
            "fecha_entrega_esperada": date.today() + timedelta(days=5),
            "proveedor": proveedor_base,
            "bodega_destino": bodega,
            "estado": estado_oc_pendiente,
            "solicitante": sel_admin,
            "subtotal": Decimal("0"),
            "impuesto": Decimal("0"),
            "descuento": Decimal("0"),
            "total": Decimal("0"),
            "activo": True,
            "eliminado": False,
        },
    )

    categoria_activo, _ = CategoriaActivo.objects.get_or_create(
        codigo="CAT-ACT-ERP",
        defaults={
            "nombre": "Categoria Activo ERP",
            "sigla": "ERP",
            "descripcion": "Categoria base para pruebas",
            "activo": True,
            "eliminado": False,
        },
    )
    estado_activo, _ = EstadoActivo.objects.get_or_create(
        codigo="DISP",
        defaults={
            "nombre": "Disponible",
            "descripcion": "Estado base",
            "color": "#198754",
            "es_inicial": True,
            "permite_movimiento": True,
            "activo": True,
            "eliminado": False,
        },
    )
    estado_baja, _ = EstadoActivo.objects.get_or_create(
        codigo="BAJA",
        defaults={
            "nombre": "Baja",
            "descripcion": "Estado final",
            "color": "#dc3545",
            "es_inicial": False,
            "permite_movimiento": False,
            "activo": True,
            "eliminado": False,
        },
    )
    ubicacion, _ = Ubicacion.objects.get_or_create(
        codigo="UBI-ERP",
        defaults={"nombre": "Ubicacion ERP", "descripcion": "Ubicacion base", "activo": True, "eliminado": False},
    )
    proveniencia, _ = Proveniencia.objects.get_or_create(
        codigo="COMPRA",
        defaults={"nombre": "Compra", "descripcion": "Origen base", "activo": True, "eliminado": False},
    )
    marca_activo, _ = MarcaActivo.objects.get_or_create(
        codigo="MAR-ERP",
        defaults={"nombre": "Marca ERP", "descripcion": "Marca base", "activo": True, "eliminado": False},
    )
    tipo_mov_activo, _ = TipoMovimientoActivo.objects.get_or_create(
        codigo="TRASLADO",
        defaults={"nombre": "Traslado", "descripcion": "Movimiento base", "activo": True, "eliminado": False},
    )
    activo_base, _ = Activo.objects.get_or_create(
        codigo="ERP01437-001",
        defaults={
            "nombre": "Notebook ERP Base",
            "descripcion": "Activo base para pruebas UI",
            "categoria": categoria_activo,
            "estado": estado_activo,
            "marca": marca_activo,
            "numero_serie": "SERIE-ERP-001",
            "precio_unitario": Decimal("250000"),
            "activo": True,
            "eliminado": False,
        },
    )

    motivo_baja, _ = MotivoBaja.objects.get_or_create(
        codigo="OBS",
        defaults={"nombre": "Obsolescencia", "descripcion": "Motivo base", "activo": True, "eliminado": False},
    )

    return {
        "admin": sel_admin,
        "bodeguero": sel_bodeguero,
        "comprador": sel_comprador,
        "activos_operador": sel_activos_operador,
        "bajas_operador": sel_bajas_operador,
        "admin_usuarios": sel_admin_usuarios,
        "bodega": bodega,
        "categoria_bodega": categoria_bodega,
        "unidad": unidad,
        "operacion_entrada": operacion_entrada,
        "operacion_salida": operacion_salida,
        "tipo_mov_bodega": tipo_mov_bodega,
        "articulo_base": articulo_base,
        "estado_oc_pendiente": estado_oc_pendiente,
        "proveedor_base": proveedor_base,
        "orden_base": orden_base,
        "categoria_activo": categoria_activo,
        "estado_activo": estado_activo,
        "estado_baja": estado_baja,
        "ubicacion": ubicacion,
        "proveniencia": proveniencia,
        "marca_activo": marca_activo,
        "tipo_mov_activo": tipo_mov_activo,
        "activo_base": activo_base,
        "motivo_baja": motivo_baja,
    }


# Legacy
@pytest.fixture(scope="function")
def selenium_usuario_solicitante(db):
    user, created = User.objects.get_or_create(
        username="sel_solicitante_leg",
        defaults={"email": "sl@test.cl"}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    _add_perms(user, [
        "solicitudes.view_solicitud",
        "solicitudes.add_solicitud",
        "solicitudes.ver_mis_solicitudes",
        "solicitudes.crear_solicitud_articulos",
        "solicitudes.ver_solicitudes_articulos",
        "solicitudes.view_estadosolicitud",
        "solicitudes.view_tiposolicitud",
    ])
    return user


@pytest.fixture(scope="function")
def selenium_usuario_admin(db):
    user, created = User.objects.get_or_create(
        username="sel_admin_leg",
        defaults={"email": "sa@test.cl", "is_staff": True, "is_superuser": True}
    )
    if created:
        user.set_password("Test1234!")
        user.save()
    return user
