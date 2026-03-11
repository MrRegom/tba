"""
Factories globales compartidas entre todos los tests de flujos.

Provee datos de catálogo (estados, tipos, categorías) que se reutilizan
en múltiples módulos del sistema.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth.models import User

from apps.solicitudes.models import (
    EstadoSolicitud, TipoSolicitud, Solicitud, DetalleSolicitud, Area, Departamento
)
from apps.bodega.models import (
    Bodega, Categoria, UnidadMedida, Articulo, Operacion, TipoMovimiento,
    EstadoRecepcion, TipoRecepcion, EstadoEntrega, TipoEntrega
)
from apps.activos.models import (
    CategoriaActivo, EstadoActivo, Activo, Ubicacion, Marca, TipoMovimientoActivo
)
from apps.compras.models import EstadoOrdenCompra, Proveedor, OrdenCompra
from apps.bajas_inventario.models import MotivoBaja, BajaInventario


# ============================================================
# USUARIOS
# ============================================================

@pytest.fixture
def u_solicitante(db):
    return User.objects.create_user("f_solicitante", password="Pass1!", first_name="Juan", last_name="Pérez")

@pytest.fixture
def u_aprobador(db):
    return User.objects.create_user("f_aprobador", password="Pass1!", first_name="María", last_name="González")

@pytest.fixture
def u_despachador(db):
    return User.objects.create_user("f_despachador", password="Pass1!", first_name="Pedro", last_name="López")

@pytest.fixture
def u_gestor(db):
    return User.objects.create_user("f_gestor", password="Pass1!", first_name="Ana", last_name="Martínez")

@pytest.fixture
def u_bodeguero(db):
    return User.objects.create_user("f_bodeguero", password="Pass1!", first_name="Carlos", last_name="Soto")

@pytest.fixture
def u_admin(db):
    return User.objects.create_superuser("f_admin", password="Pass1!", email="admin@f.cl")


# ============================================================
# CATÁLOGOS DE SOLICITUDES
# ============================================================

@pytest.fixture
def estado_pendiente(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="PENDIENTE",
        defaults={"nombre": "Pendiente", "es_inicial": True, "es_final": False,
                  "requiere_accion": True, "activo": True}
    )
    return estado

@pytest.fixture
def estado_aprobada(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="APROBADA",
        defaults={"nombre": "Aprobada", "es_inicial": False, "es_final": False,
                  "requiere_accion": False, "activo": True}
    )
    return estado

@pytest.fixture
def estado_rechazada(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="RECHAZAR",
        defaults={"nombre": "Rechazada", "es_inicial": False, "es_final": True,
                  "requiere_accion": False, "activo": True}
    )
    return estado

@pytest.fixture
def estado_despachar(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="DESPACHAR",
        defaults={"nombre": "Para despachar", "es_inicial": False, "es_final": False,
                  "requiere_accion": True, "activo": True}
    )
    return estado

@pytest.fixture
def estado_despachada(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="DESPACHADA",
        defaults={"nombre": "Recepción Conforme", "es_inicial": False, "es_final": True,
                  "requiere_accion": False, "activo": True}
    )
    return estado

@pytest.fixture
def estado_cancelada(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="CANCELADA",
        defaults={"nombre": "Cancelada", "es_inicial": False, "es_final": True,
                  "requiere_accion": False, "activo": True}
    )
    return estado

@pytest.fixture
def estado_comprar(db):
    estado, _ = EstadoSolicitud.objects.get_or_create(
        codigo="COMPRAR",
        defaults={"nombre": "En Compras", "es_inicial": False, "es_final": False,
                  "requiere_accion": True, "activo": True}
    )
    return estado

@pytest.fixture
def todos_estados_solicitud(
    estado_pendiente, estado_aprobada, estado_rechazada,
    estado_despachar, estado_despachada, estado_cancelada, estado_comprar
):
    """Crea todos los estados de solicitud de una vez."""
    return {
        "PENDIENTE": estado_pendiente,
        "APROBADA": estado_aprobada,
        "RECHAZAR": estado_rechazada,
        "DESPACHAR": estado_despachar,
        "DESPACHADA": estado_despachada,
        "CANCELADA": estado_cancelada,
        "COMPRAR": estado_comprar,
    }

@pytest.fixture
def tipo_solicitud_articulo(db):
    tipo, _ = TipoSolicitud.objects.get_or_create(
        codigo="ARTICULO",
        defaults={"nombre": "Solicitud de Artículos", "activo": True}
    )
    return tipo

@pytest.fixture
def tipo_solicitud_bien(db):
    tipo, _ = TipoSolicitud.objects.get_or_create(
        codigo="BIEN",
        defaults={"nombre": "Solicitud de Bienes", "activo": True}
    )
    return tipo

@pytest.fixture
def departamento_test(db):
    depto, _ = Departamento.objects.get_or_create(
        codigo="DEPTO-TEST",
        defaults={"nombre": "Depto de Test", "activo": True}
    )
    return depto

@pytest.fixture
def area_test(db, departamento_test):
    area, _ = Area.objects.get_or_create(
        codigo="TEST",
        defaults={"nombre": "Área de Test", "departamento": departamento_test, "activo": True}
    )
    return area


# ============================================================
# CATÁLOGOS DE BODEGA
# ============================================================

@pytest.fixture
def bodega_test(db, u_bodeguero):
    bodega, _ = Bodega.objects.get_or_create(
        codigo="BOD-TEST",
        defaults={
            "nombre": "Bodega Test",
            "descripcion": "Bodega para pruebas",
            "responsable": u_bodeguero,
            "activo": True,
            "eliminado": False,
        }
    )
    return bodega

@pytest.fixture
def categoria_bodega(db):
    cat, _ = Categoria.objects.get_or_create(
        codigo="CAT-TEST",
        defaults={"nombre": "Materiales Test", "activo": True, "eliminado": False}
    )
    return cat

@pytest.fixture
def unidad_medida_unidad(db):
    um, _ = UnidadMedida.objects.get_or_create(
        codigo="UND",
        defaults={"nombre": "Unidad", "simbolo": "und", "activo": True, "eliminado": False}
    )
    return um

@pytest.fixture
def operacion_entrada(db):
    op, _ = Operacion.objects.get_or_create(
        codigo="ENTRADA",
        defaults={"nombre": "Entrada", "tipo": "ENTRADA", "activo": True}
    )
    return op

@pytest.fixture
def operacion_salida(db):
    op, _ = Operacion.objects.get_or_create(
        codigo="SALIDA",
        defaults={"nombre": "Salida", "tipo": "SALIDA", "activo": True}
    )
    return op

@pytest.fixture
def tipo_mov_recepcion(db):
    tm, _ = TipoMovimiento.objects.get_or_create(
        codigo="RECEPCION",
        defaults={"nombre": "Recepción de Compra", "activo": True}
    )
    return tm

@pytest.fixture
def tipo_mov_ajuste_positivo(db):
    tm, _ = TipoMovimiento.objects.get_or_create(
        codigo="AJUSTE_POSITIVO",
        defaults={"nombre": "Ajuste Positivo", "activo": True}
    )
    return tm

@pytest.fixture
def tipo_mov_ajuste_negativo(db):
    tm, _ = TipoMovimiento.objects.get_or_create(
        codigo="AJUSTE_NEGATIVO",
        defaults={"nombre": "Ajuste Negativo", "activo": True}
    )
    return tm

@pytest.fixture
def tipo_mov_entrega(db):
    tm, _ = TipoMovimiento.objects.get_or_create(
        codigo="ENTREGA",
        defaults={"nombre": "Entrega", "activo": True}
    )
    return tm

@pytest.fixture
def articulo_test(db, categoria_bodega, unidad_medida_unidad, bodega_test):
    art, _ = Articulo.objects.get_or_create(
        codigo="ART-TEST-001",
        defaults={
            "nombre": "Lápiz HB Test",
            "descripcion": "Lápiz para pruebas",
            "categoria": categoria_bodega,
            "unidad_medida": unidad_medida_unidad,
            "ubicacion_fisica": bodega_test,
            "stock_actual": Decimal("100.00"),
            "stock_minimo": Decimal("10.00"),
            "stock_maximo": Decimal("500.00"),
            "activo": True,
            "eliminado": False,
        }
    )
    return art

@pytest.fixture
def articulo_sin_stock(db, categoria_bodega, unidad_medida_unidad, bodega_test):
    art, _ = Articulo.objects.get_or_create(
        codigo="ART-TEST-002",
        defaults={
            "nombre": "Papel Carta Test",
            "categoria": categoria_bodega,
            "unidad_medida": unidad_medida_unidad,
            "ubicacion_fisica": bodega_test,
            "stock_actual": Decimal("0.00"),
            "stock_minimo": Decimal("5.00"),
            "stock_maximo": Decimal("100.00"),
            "activo": True,
            "eliminado": False,
        }
    )
    return art

@pytest.fixture
def estado_recepcion_inicial(db):
    est, _ = EstadoRecepcion.objects.get_or_create(
        codigo="BORRADOR",
        defaults={"nombre": "Borrador"}
    )
    return est

@pytest.fixture
def estado_recepcion_completada(db):
    est, _ = EstadoRecepcion.objects.get_or_create(
        codigo="COMPLETADA",
        defaults={"nombre": "Completada"}
    )
    return est

@pytest.fixture
def tipo_recepcion_con_orden(db):
    tr, _ = TipoRecepcion.objects.get_or_create(
        codigo="CON_ORDEN",
        defaults={"nombre": "Con Orden de Compra", "requiere_orden": True, "activo": True}
    )
    return tr

@pytest.fixture
def tipo_recepcion_sin_orden(db):
    tr, _ = TipoRecepcion.objects.get_or_create(
        codigo="SIN_ORDEN",
        defaults={"nombre": "Sin Orden", "requiere_orden": False, "activo": True}
    )
    return tr


# ============================================================
# CATÁLOGOS DE ACTIVOS
# ============================================================

@pytest.fixture
def ubicacion_test(db):
    ub, _ = Ubicacion.objects.get_or_create(
        codigo="UB-TEST",
        defaults={"nombre": "Sala Test", "activo": True, "eliminado": False}
    )
    return ub

@pytest.fixture
def categoria_activo(db):
    cat, _ = CategoriaActivo.objects.get_or_create(
        codigo="INFO-TEST",
        defaults={"nombre": "Informática Test", "activo": True, "eliminado": False}
    )
    return cat

@pytest.fixture
def estado_activo_disponible(db):
    est, _ = EstadoActivo.objects.get_or_create(
        codigo="DISP",
        defaults={
            "nombre": "Disponible",
            "es_inicial": True,
            "permite_movimiento": True,
            "activo": True,
            "eliminado": False,
        }
    )
    return est

@pytest.fixture
def estado_activo_baja(db):
    est, _ = EstadoActivo.objects.get_or_create(
        codigo="BJA",
        defaults={
            "nombre": "De Baja",
            "es_inicial": False,
            "permite_movimiento": False,
            "activo": True,
            "eliminado": False,
        }
    )
    return est

@pytest.fixture
def marca_test(db):
    marca, _ = Marca.objects.get_or_create(
        codigo="MARCA-TEST",
        defaults={"nombre": "Marca Test", "activo": True, "eliminado": False}
    )
    return marca

@pytest.fixture
def tipo_movimiento_activo_traslado(db):
    tm, _ = TipoMovimientoActivo.objects.get_or_create(
        codigo="TRASLADO",
        defaults={"nombre": "Traslado", "activo": True, "eliminado": False}
    )
    return tm

@pytest.fixture
def activo_test(db, categoria_activo, estado_activo_disponible, ubicacion_test):
    activo, _ = Activo.objects.get_or_create(
        codigo="ACT-TEST-001",
        defaults={
            "nombre": "Notebook Test",
            "descripcion": "Notebook para pruebas",
            "categoria": categoria_activo,
            "estado": estado_activo_disponible,
            "numero_serie": "SN-TEST-001",
            "activo": True,
            "eliminado": False,
        }
    )
    return activo


# ============================================================
# CATÁLOGOS DE COMPRAS
# ============================================================

@pytest.fixture
def estado_orden_pendiente(db):
    est, _ = EstadoOrdenCompra.objects.get_or_create(
        codigo="PENDIENTE",
        defaults={"nombre": "Pendiente", "activo": True}
    )
    return est

@pytest.fixture
def estado_orden_aprobada(db):
    est, _ = EstadoOrdenCompra.objects.get_or_create(
        codigo="APROBADA",
        defaults={"nombre": "Aprobada", "activo": True}
    )
    return est

@pytest.fixture
def estado_orden_recibida(db):
    est, _ = EstadoOrdenCompra.objects.get_or_create(
        codigo="RECIBIDA",
        defaults={"nombre": "Recibida", "activo": True}
    )
    return est

@pytest.fixture
def proveedor_test(db):
    prov, _ = Proveedor.objects.get_or_create(
        rut="76.123.456-7",
        defaults={
            "razon_social": "Proveedor Test S.A.",
            "activo": True,
            "eliminado": False,
        }
    )
    return prov


# ============================================================
# CATÁLOGOS DE BAJAS
# ============================================================

@pytest.fixture
def motivo_baja_obsoleto(db):
    motivo, _ = MotivoBaja.objects.get_or_create(
        codigo="OBSO",
        defaults={"nombre": "Obsolescencia", "activo": True, "eliminado": False}
    )
    return motivo

@pytest.fixture
def motivo_baja_dano(db):
    motivo, _ = MotivoBaja.objects.get_or_create(
        codigo="DANO",
        defaults={"nombre": "Daño Irreparable", "activo": True, "eliminado": False}
    )
    return motivo
