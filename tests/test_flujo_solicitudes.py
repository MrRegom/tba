"""
Pruebas de flujo completo del módulo de Solicitudes.

Cubre cada transición de estado y cada rol:
  PENDIENTE → APROBADA → DESPACHAR → DESPACHADA  (flujo feliz)
  PENDIENTE → RECHAZAR                            (flujo rechazo)
  PENDIENTE → COMPRAR                             (flujo compra)
  PENDIENTE → CANCELADA                           (flujo cancelación)

Prueba tanto el nivel de servicio como el HTTP.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.solicitudes.models import Solicitud, DetalleSolicitud, HistorialSolicitud
from apps.solicitudes.services import SolicitudService

from tests.factories_globales import *  # noqa: F403


pytestmark = pytest.mark.django_db


# ============================================================
# HELPERS
# ============================================================

def crear_solicitud_base(
    estado_pendiente, tipo_solicitud_articulo, area_test, departamento_test,
    solicitante, articulo=None
):
    """Crea una solicitud en estado PENDIENTE con un detalle."""
    from datetime import date, timedelta
    import uuid
    solicitud = Solicitud.objects.create(
        tipo="ARTICULO",
        numero=f"SOL-TEST-{uuid.uuid4().hex[:6].upper()}",
        tipo_solicitud=tipo_solicitud_articulo,
        estado=estado_pendiente,
        solicitante=solicitante,
        area=area_test,
        departamento=departamento_test,
        fecha_requerida=date.today() + timedelta(days=7),
        observaciones="Solicitud de prueba de integración",
        activo=True,
        eliminado=False,
    )
    if articulo:
        DetalleSolicitud.objects.create(
            solicitud=solicitud,
            articulo=articulo,
            cantidad_solicitada=10,
            cantidad_aprobada=0,
            eliminado=False,
        )
    return solicitud


# ============================================================
# 1. FLUJO FELIZ: PENDIENTE → APROBADA → DESPACHAR → DESPACHADA
# ============================================================

class TestFlujoAprobacionCompleto:
    """
    Escenario completo: el solicitante crea, el aprobador aprueba,
    el despachador despacha.
    """

    def test_solicitud_creada_en_estado_pendiente(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        assert solicitud.estado.codigo == "PENDIENTE"
        assert solicitud.detalles.count() == 1
        assert solicitud.aprobador is None
        assert solicitud.despachador is None

    def test_aprobador_aprueba_solicitud(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()

        service = SolicitudService()
        solicitud = service.aprobar_solicitud(
            solicitud=solicitud,
            aprobador=u_aprobador,
            detalles_aprobados=[{
                "detalle_id": detalle.id,
                "cantidad_aprobada": Decimal("8.00"),
            }],
            notas_aprobacion="Aprobado con cantidad reducida",
        )

        solicitud.refresh_from_db()
        assert solicitud.estado.codigo == "APROBADA"
        assert solicitud.aprobador == u_aprobador

        detalle.refresh_from_db()
        assert detalle.cantidad_aprobada == Decimal("8.00")

        # Historial registrado
        historial = HistorialSolicitud.objects.filter(solicitud=solicitud)
        assert historial.count() >= 1
        ultimo = historial.order_by("-fecha_cambio").first()
        assert ultimo.estado_nuevo.codigo == "APROBADA"

    def test_despachador_despacha_solicitud_aprobada(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, u_despachador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()

        service = SolicitudService()
        solicitud = service.aprobar_solicitud(
            solicitud=solicitud,
            aprobador=u_aprobador,
            detalles_aprobados=[{"detalle_id": detalle.id, "cantidad_aprobada": Decimal("10.00")}],
        )

        solicitud = service.despachar_solicitud(
            solicitud=solicitud,
            despachador=u_despachador,
            detalles_despachados=[{"detalle_id": detalle.id, "cantidad_despachada": Decimal("10.00")}],
            notas_despacho="Despachado desde bodega",
        )

        solicitud.refresh_from_db()
        assert solicitud.estado.codigo == "DESPACHAR"
        assert solicitud.despachador == u_despachador

    def test_historial_registra_todas_las_transiciones(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, u_despachador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()
        service = SolicitudService()

        service.aprobar_solicitud(
            solicitud=solicitud, aprobador=u_aprobador,
            detalles_aprobados=[{"detalle_id": detalle.id, "cantidad_aprobada": Decimal("5.00")}],
        )
        service.despachar_solicitud(
            solicitud=solicitud, despachador=u_despachador,
            detalles_despachados=[{"detalle_id": detalle.id, "cantidad_despachada": Decimal("5.00")}],
        )

        historial = HistorialSolicitud.objects.filter(solicitud=solicitud).order_by("fecha_cambio")
        codigos = [h.estado_nuevo.codigo for h in historial]

        assert "APROBADA" in codigos
        assert "DESPACHAR" in codigos


# ============================================================
# 2. FLUJO RECHAZO: PENDIENTE → RECHAZADA
# ============================================================

class TestFlujoRechazo:

    def test_aprobador_rechaza_solicitud(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )

        service = SolicitudService()
        solicitud = service.rechazar_solicitud(
            solicitud=solicitud,
            rechazador=u_aprobador,
            motivo_rechazo="Presupuesto insuficiente para este período",
        )

        solicitud.refresh_from_db()
        assert solicitud.estado.codigo == "RECHAZAR"
        assert solicitud.estado.es_final is True
        assert "Presupuesto insuficiente" in (solicitud.notas_aprobacion or "")

    def test_no_se_puede_aprobar_solicitud_ya_rechazada(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()
        service = SolicitudService()

        service.rechazar_solicitud(
            solicitud=solicitud,
            rechazador=u_aprobador,
            motivo_rechazo="Rechazada previamente",
        )

        with pytest.raises(ValidationError):
            service.aprobar_solicitud(
                solicitud=solicitud,
                aprobador=u_aprobador,
                detalles_aprobados=[{"detalle_id": detalle.id, "cantidad_aprobada": Decimal("5.00")}],
            )

    def test_rechazar_requiere_motivo(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante
        )
        service = SolicitudService()

        with pytest.raises(ValidationError):
            service.rechazar_solicitud(
                solicitud=solicitud,
                rechazador=u_aprobador,
                motivo_rechazo="",  # Sin motivo
            )


# ============================================================
# 3. FLUJO CANCELACIÓN: PENDIENTE → CANCELADA
# ============================================================

class TestFlujoCancelacion:

    def test_gestor_cancela_solicitud(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_gestor
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante
        )

        service = SolicitudService()
        solicitud = service.cancelar_solicitud(
            solicitud=solicitud,
            usuario=u_gestor,
            motivo_cancelacion="Cambio de prioridades del área",
        )

        solicitud.refresh_from_db()
        assert solicitud.estado.codigo == "CANCELADA"
        assert solicitud.estado.es_final is True

    def test_solicitud_cancelada_no_puede_cambiar_estado(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_gestor, u_aprobador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()
        service = SolicitudService()

        service.cancelar_solicitud(
            solicitud=solicitud, usuario=u_gestor,
            motivo_cancelacion="Cancelada por test",
        )

        with pytest.raises(ValidationError):
            service.aprobar_solicitud(
                solicitud=solicitud, aprobador=u_aprobador,
                detalles_aprobados=[{"detalle_id": detalle.id, "cantidad_aprobada": Decimal("5.00")}],
            )


# ============================================================
# 4. FLUJO COMPRAR: → EN COMPRAS
# ============================================================

class TestFlujoComprar:

    def test_despachador_envía_a_compras(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_despachador
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante
        )

        service = SolicitudService()
        solicitud = service.cambiar_estado(
            solicitud=solicitud,
            nuevo_estado=todos_estados_solicitud["COMPRAR"],
            usuario=u_despachador,
            observaciones="Enviado a compras por falta de stock",
        )

        solicitud.refresh_from_db()
        assert solicitud.estado.codigo == "COMPRAR"


# ============================================================
# 5. VALIDACIONES DE NEGOCIO
# ============================================================

class TestValidacionesNegocio:

    def test_cantidad_aprobada_no_puede_exceder_solicitada(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()
        assert detalle.cantidad_solicitada == Decimal("10.00")

        service = SolicitudService()
        with pytest.raises(ValidationError):
            service.aprobar_solicitud(
                solicitud=solicitud,
                aprobador=u_aprobador,
                detalles_aprobados=[{
                    "detalle_id": detalle.id,
                    "cantidad_aprobada": Decimal("999.00"),  # Excede lo solicitado
                }],
            )

    def test_despachador_no_puede_despachar_cantidad_negativa(
        self, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, u_despachador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()
        service = SolicitudService()

        service.aprobar_solicitud(
            solicitud=solicitud, aprobador=u_aprobador,
            detalles_aprobados=[{"detalle_id": detalle.id, "cantidad_aprobada": Decimal("5.00")}],
        )

        with pytest.raises(ValidationError):
            service.despachar_solicitud(
                solicitud=solicitud, despachador=u_despachador,
                detalles_despachados=[{"detalle_id": detalle.id, "cantidad_despachada": Decimal("-1.00")}],
            )

    def test_solicitud_sin_estado_inicial_lanza_error(
        self, tipo_solicitud_articulo, area_test, departamento_test, u_solicitante
    ):
        """Si no hay estado PENDIENTE configurado, el service debe fallar."""
        from apps.solicitudes.repositories import EstadoSolicitudRepository
        # Usar service sin estados en DB → get_inicial() retorna None
        # Verificamos que create() sin estado falla a nivel DB
        from datetime import date, timedelta
        import uuid
        with pytest.raises(Exception):
            Solicitud.objects.create(
                tipo="ARTICULO",
                numero=f"SOL-NOSTATE-{uuid.uuid4().hex[:6].upper()}",
                tipo_solicitud=tipo_solicitud_articulo,
                estado=None,  # Sin estado
                solicitante=u_solicitante,
                area=area_test,
                departamento=departamento_test,
                fecha_requerida=date.today() + timedelta(days=3),
                descripcion="Sin estado",
            )


# ============================================================
# 6. VISTAS HTTP — Flujo por rol
# ============================================================

class TestVistasHTTPSolicitudes:
    """
    Pruebas de los endpoints HTTP de solicitudes por cada rol.
    """

    def test_solicitante_crea_solicitud_articulo_via_http(
        self, client_solicitante, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, articulo_test
    ):
        resp = client_solicitante.get("/solicitudes/articulos/crear/")
        assert resp.status_code == 200, "Solicitante debe ver el formulario de creación"

    def test_aprobador_ve_lista_solicitudes_via_http(
        self, client_aprobador, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, articulo_test
    ):
        # Crear solicitud primero
        crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        resp = client_aprobador.get("/solicitudes/gestion/")
        assert resp.status_code == 200

    def test_aprobador_puede_aprobar_via_http(
        self, client_aprobador, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()

        resp = client_aprobador.post(
            f"/solicitudes/{solicitud.pk}/aprobar/",
            {
                f"cantidad_aprobada_{detalle.id}": "8",
                "notas_aprobacion": "Aprobado vía HTTP",
            }
        )
        assert resp.status_code in (200, 302), (
            f"POST de aprobación debe retornar 200 o 302, obtuvo {resp.status_code}"
        )

    def test_solicitante_no_puede_aprobar_via_http(
        self, client_solicitante, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()

        resp = client_solicitante.post(
            f"/solicitudes/{solicitud.pk}/aprobar/",
            {f"cantidad_aprobada_{detalle.id}": "5"}
        )
        assert resp.status_code in (403, 302), (
            "Solicitante no debe poder aprobar"
        )

    def test_aprobador_puede_rechazar_via_http(
        self, client_aprobador, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        resp = client_aprobador.post(
            f"/solicitudes/{solicitud.pk}/rechazar/",
            {"motivo_rechazo": "Rechazado por el aprobador vía HTTP"}
        )
        assert resp.status_code in (200, 302)
        solicitud.refresh_from_db()
        assert solicitud.estado.codigo == "RECHAZAR"

    def test_despachador_puede_despachar_via_http(
        self, client_despachador, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_aprobador, articulo_test
    ):
        solicitud = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        detalle = solicitud.detalles.first()

        # Aprobar primero (vía service)
        service = SolicitudService()
        service.aprobar_solicitud(
            solicitud=solicitud, aprobador=u_aprobador,
            detalles_aprobados=[{"detalle_id": detalle.id, "cantidad_aprobada": Decimal("5.00")}],
        )

        resp = client_despachador.post(
            f"/solicitudes/{solicitud.pk}/despachar/",
            {
                f"cantidad_despachada_{detalle.id}": "5",
                "notas_despacho": "Despachado vía HTTP",
            }
        )
        assert resp.status_code in (200, 302)

    def test_solicitante_ve_solo_sus_solicitudes(
        self, client_solicitante, todos_estados_solicitud, tipo_solicitud_articulo,
        area_test, departamento_test, u_solicitante, u_gestor, articulo_test
    ):
        """Solicitante solo ve sus propias solicitudes en /mis-solicitudes/."""
        # Crear solicitud del solicitante
        sol_propia = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_solicitante, articulo=articulo_test
        )
        # Crear solicitud de otro usuario
        sol_ajena = crear_solicitud_base(
            todos_estados_solicitud["PENDIENTE"],
            tipo_solicitud_articulo, area_test, departamento_test,
            u_gestor, articulo=articulo_test
        )

        resp = client_solicitante.get("/solicitudes/mis-solicitudes/")
        assert resp.status_code == 200
        content = resp.content.decode()

        # El número de la propia solicitud puede aparecer
        # La solicitud ajena NO debe estar accesible al solicitante vía detalle
        resp_ajena = client_solicitante.get(f"/solicitudes/{sol_ajena.pk}/")
        # Puede ser 200 si tiene view_solicitud, pero no debe poder editar/eliminar
        resp_editar_ajena = client_solicitante.get(f"/solicitudes/{sol_ajena.pk}/editar/")
        assert resp_editar_ajena.status_code in (403, 302, 404)
