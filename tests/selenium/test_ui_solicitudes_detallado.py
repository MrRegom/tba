"""Pruebas visuales detalladas del modulo de solicitudes."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from selenium.webdriver.common.by import By

from apps.solicitudes.models import Solicitud

from .conftest import switch_user
from .pages.solicitudes_workflow_page import SolicitudWorkflowPage


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.selenium]


def _future_date(days: int = 7) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def _past_date(days: int = 1) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


class TestSolicitudesVisualValidation:
    def test_creacion_muestra_validaciones_cliente_y_servidor(
        self,
        driver,
        live_server,
        ui_observer,
        solicitudes_ui_catalogo,
    ):
        switch_user(driver, live_server, solicitudes_ui_catalogo["solicitante"])
        page = SolicitudWorkflowPage(driver, base_url=live_server.url)
        page.open_create()
        ui_observer.note(
            "Formulario inicial",
            "Se verifica la presencia de campos clave y el estado vacio antes de agregar articulos.",
        )

        assert page.is_visible(page.FORM)
        assert page.is_visible(page.TIPO_SOLICITUD)
        assert page.is_visible(page.FECHA_REQUERIDA)
        assert page.is_visible(page.MOTIVO)
        assert page.is_visible((By.ID, "sin-articulos"))

        tipo_texto = page.select_first_nonempty_option(page.TIPO_SOLICITUD)

        page.fill_header_form(
            tipo_solicitud=tipo_texto,
            fecha_requerida=_future_date(),
            departamento=solicitudes_ui_catalogo["departamento"].nombre,
            area=solicitudes_ui_catalogo["area"].nombre,
            bodega=solicitudes_ui_catalogo["bodega"].nombre,
            motivo="Validacion visual de campos requeridos",
        )
        page.submit()
        ui_observer.note(
            "Advertencia por detalle faltante",
            "El frontend debe bloquear el envio cuando no se agrega ningun articulo.",
        )
        assert "debe agregar al menos un art" in driver.page_source.lower()

        page.add_articulo(
            solicitudes_ui_catalogo["articulo"].nombre,
            "0",
            "Cantidad invalida para forzar advertencia",
        )
        ui_observer.note(
            "Articulo agregado con cantidad invalida",
            "Se espera un bloqueo visual porque la cantidad no puede ser cero.",
        )
        page.submit()
        assert "cantidades deben ser mayores a cero" in driver.page_source.lower()

        page.open_create()
        tipo_texto = page.select_first_nonempty_option(page.TIPO_SOLICITUD)
        page.fill_header_form(
            tipo_solicitud=tipo_texto,
            fecha_requerida=_past_date(),
            departamento=solicitudes_ui_catalogo["departamento"].nombre,
            area=solicitudes_ui_catalogo["area"].nombre,
            bodega=solicitudes_ui_catalogo["bodega"].nombre,
            motivo="Validacion de fecha pasada",
            observaciones="Debe mostrar error de negocio",
        )
        page.add_articulo(
            solicitudes_ui_catalogo["articulo"].nombre,
            "2",
            "Cantidad correcta para llegar al backend",
        )
        page.submit()
        ui_observer.note(
            "Error de negocio en backend",
            "La fecha requerida en el pasado debe dejar feedback claro en el formulario.",
        )
        combined_feedback = f"{page.latest_alert_text()} {page.invalid_feedback_text()} {driver.page_source}"
        assert "fecha requerida no puede ser anterior a hoy" in combined_feedback.lower()

    def test_aprobacion_y_rechazo_muestran_errores_por_campo(
        self,
        driver,
        live_server,
        ui_observer,
        solicitudes_ui_catalogo,
    ):
        switch_user(driver, live_server, solicitudes_ui_catalogo["solicitante"])
        page = SolicitudWorkflowPage(driver, base_url=live_server.url)
        page.open_create()
        tipo_texto = page.select_first_nonempty_option(page.TIPO_SOLICITUD)
        page.fill_header_form(
            tipo_solicitud=tipo_texto,
            fecha_requerida=_future_date(),
            departamento=solicitudes_ui_catalogo["departamento"].nombre,
            area=solicitudes_ui_catalogo["area"].nombre,
            bodega=solicitudes_ui_catalogo["bodega"].nombre,
            motivo="Solicitud base para probar formularios de aprobacion y rechazo",
        )
        page.add_articulo(solicitudes_ui_catalogo["articulo"].nombre, "4", "Linea base")
        page.submit()
        solicitud = Solicitud.objects.filter(solicitante=solicitudes_ui_catalogo["solicitante"]).latest("id")
        detalle = solicitud.detalles.first()
        ui_observer.note(
            "Solicitud base creada",
            f"Se usara la solicitud {solicitud.numero} para verificar errores de aprobacion y rechazo.",
        )

        switch_user(driver, live_server, solicitudes_ui_catalogo["aprobador"])
        page.open_approve(solicitud.id)
        page.set_numeric_field(page.approval_input(detalle.id), "99")
        ui_observer.note(
            "Cantidad aprobada sobre el maximo",
            "La validacion cliente debe advertir que no se puede aprobar mas de lo solicitado.",
        )
        page.submit()
        assert "no puede exceder" in driver.page_source.lower()

        page.open_reject(solicitud.id)
        page.submit()
        ui_observer.note(
            "Motivo de rechazo obligatorio",
            "El campo de rechazo debe informar claramente que es requerido.",
        )
        motivo = driver.find_element(By.NAME, "motivo_rechazo")
        validation_message = driver.execute_script("return arguments[0].validationMessage;", motivo)
        assert motivo.get_attribute("required")
        assert validation_message


class TestSolicitudesVisualWorkflow:
    def test_flujo_visual_desde_creacion_hasta_despacho(
        self,
        driver,
        live_server,
        ui_observer,
        solicitudes_ui_catalogo,
    ):
        page = SolicitudWorkflowPage(driver, base_url=live_server.url)

        switch_user(driver, live_server, solicitudes_ui_catalogo["solicitante"])
        page.open_create()
        tipo_texto = page.select_first_nonempty_option(page.TIPO_SOLICITUD)
        page.fill_header_form(
            tipo_solicitud=tipo_texto,
            fecha_requerida=_future_date(),
            departamento=solicitudes_ui_catalogo["departamento"].nombre,
            area=solicitudes_ui_catalogo["area"].nombre,
            bodega=solicitudes_ui_catalogo["bodega"].nombre,
            motivo="Flujo completo visible de solicitudes",
            observaciones="Creada por Selenium para revision visual",
        )
        page.add_articulo(
            solicitudes_ui_catalogo["articulo"].nombre,
            "3",
            "Linea incluida en flujo completo",
        )
        ui_observer.note(
            "Antes de crear la solicitud",
            "Se completan datos generales, estructura organizacional y detalle del articulo.",
        )
        page.submit()
        solicitud = Solicitud.objects.filter(solicitante=solicitudes_ui_catalogo["solicitante"]).latest("id")
        detalle = solicitud.detalles.first()
        page.wait_for_redirect_to_detail(solicitud.id)
        ui_observer.note(
            "Solicitud creada",
            f"Se espera estado Pendiente y visibilidad del historial de creacion para {solicitud.numero}.",
        )
        assert "Pendiente" in driver.page_source
        assert page.history_contains("Solicitud creada por")

        switch_user(driver, live_server, solicitudes_ui_catalogo["aprobador"])
        page.open_approve(solicitud.id)
        page.set_numeric_field(page.approval_input(detalle.id), "2")
        page.set_textarea("notas_aprobacion", "Se aprueba parcialmente para observar el cambio de estado.")
        ui_observer.note(
            "Formulario de aprobacion",
            "Se reduce la cantidad aprobada para validar regla de negocio y trazabilidad.",
        )
        page.submit()
        page.wait_for_redirect_to_detail(solicitud.id)
        ui_observer.note(
            "Solicitud aprobada",
            "La pagina de detalle debe mostrar aprobador, notas y el nuevo estado aprobado.",
        )
        assert "Aprobada" in driver.page_source
        assert "aprueba parcialmente" in driver.page_source.lower()

        switch_user(driver, live_server, solicitudes_ui_catalogo["despachador"])
        page.open_dispatch(solicitud.id)
        page.set_numeric_field(page.dispatch_input(detalle.id), "2")
        page.set_textarea("notas_despacho", "Se despacha cantidad aprobada para cierre operativo visible.")
        ui_observer.note(
            "Formulario de despacho",
            "Se despacha exactamente la cantidad aprobada para cerrar el flujo operativo.",
        )
        page.submit()
        page.wait_for_redirect_to_detail(solicitud.id)
        ui_observer.note(
            "Solicitud lista para despacho",
            "El detalle debe quedar con despachador asignado, historial actualizado y estado para despachar.",
        )
        response_text = driver.page_source
        assert "Para despachar" in response_text
        assert "Despachado por" in response_text
        assert "Movido a Para Despachar" in response_text
