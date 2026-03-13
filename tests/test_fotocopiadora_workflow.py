import datetime

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django.utils import timezone

from apps.fotocopiadora.models import (
    PrintMembershipRole,
    PrintRequest,
    PrintRequestItem,
    PrintRequestStatus,
    PrintRoleMembership,
)
from apps.solicitudes.models import Area, Departamento


def grant_permissions(user, *codes):
    for code in codes:
        app_label, codename = code.split('.', 1)
        permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        user.user_permissions.add(permission)


@pytest.mark.django_db
def test_professor_can_create_draft_request_and_only_view_own_requests(client):
    user = User.objects.create_user(username='profesor', password='x')
    other = User.objects.create_user(username='otro-profesor', password='x')
    departamento = Departamento.objects.create(codigo='DEP-FOT-1', nombre='Lenguaje')
    area = Area.objects.create(codigo='AR-FOT-1', nombre='Lenguaje Media', departamento=departamento)
    grant_permissions(
        user,
        'fotocopiadora.view_printrequest',
        'fotocopiadora.add_printrequest',
        'fotocopiadora.change_printrequest',
        'fotocopiadora.submit_printrequest',
        'fotocopiadora.cancel_own_printrequest',
    )

    PrintRequest.objects.create(
        numero='PR-OTRA',
        title='Solicitud ajena',
        request_type='PRINT',
        required_at=timezone.now() + datetime.timedelta(days=2),
        requester=other,
        departamento=departamento,
        area=area,
    )

    client.force_login(user)
    response = client.post(
        reverse('fotocopiadora:crear_solicitud_impresion'),
        data={
            'title': 'Guía 7B',
            'description': 'Material de apoyo',
            'request_type': 'PHOTOCOPY',
            'priority': 'NORMAL',
            'required_at': (timezone.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'departamento': departamento.pk,
            'area': area.pk,
            'items-TOTAL_FORMS': 1,
            'items-INITIAL_FORMS': 0,
            'items-MIN_NUM_FORMS': 0,
            'items-MAX_NUM_FORMS': 1000,
            'items-0-document_title': 'Guía unidad 1',
            'items-0-page_size': 'A4',
            'items-0-print_side': 'SINGLE',
            'items-0-color_mode': 'BW',
            'items-0-copy_count_requested': 35,
            'items-0-original_page_count': 2,
            'items-0-stapled': '',
            'items-0-collated': '',
            'items-0-notes': '',
        },
    )

    assert response.status_code == 302

    created = PrintRequest.objects.get(title='Guía 7B')
    assert created.requester == user
    assert created.status == PrintRequestStatus.DRAFT
    assert created.items.count() == 1

    list_response = client.get(reverse('fotocopiadora:mis_solicitudes_impresion'))

    assert list_response.status_code == 200
    page = list_response.content.decode('utf-8')
    assert 'Guía 7B' in page
    assert 'Solicitud ajena' not in page


@pytest.mark.django_db
def test_approver_can_approve_request_in_scope(client):
    professor = User.objects.create_user(username='profesor-2', password='x')
    approver = User.objects.create_user(username='jefatura-fot', password='x')
    departamento = Departamento.objects.create(codigo='DEP-FOT-2', nombre='Matemática')
    area = Area.objects.create(codigo='AR-FOT-2', nombre='Matemática Básica', departamento=departamento)

    grant_permissions(
        approver,
        'fotocopiadora.view_printrequest',
        'fotocopiadora.view_department_printrequest',
        'fotocopiadora.approve_printrequest',
        'fotocopiadora.reject_printrequest',
        'fotocopiadora.partial_approve_printrequest',
    )
    PrintRoleMembership.objects.create(user=approver, role=PrintMembershipRole.APPROVER, departamento=departamento)

    request_obj = PrintRequest.objects.create(
        numero='PR-APR-1',
        title='Prueba parcial',
        request_type='PHOTOCOPY',
        status=PrintRequestStatus.PENDING_APPROVAL,
        required_at=timezone.now() + datetime.timedelta(days=1),
        requester=professor,
        departamento=departamento,
        area=area,
        submitted_at=timezone.now(),
    )
    item = PrintRequestItem.objects.create(
        request=request_obj,
        line_number=1,
        document_title='Prueba parcial 8A',
        page_size='A4',
        print_side='DOUBLE',
        color_mode='BW',
        copy_count_requested=40,
        original_page_count=3,
    )

    client.force_login(approver)
    response = client.post(
        reverse('fotocopiadora:transicion_solicitud_impresion', args=[request_obj.pk]),
        data={
            'action': 'APPROVE',
            f'item_{item.pk}_approved': 32,
            'comment': 'Se ajusta a la dotación autorizada.',
        },
    )

    assert response.status_code == 302
    request_obj.refresh_from_db()
    item.refresh_from_db()

    assert request_obj.status == PrintRequestStatus.APPROVED
    assert request_obj.approver == approver
    assert request_obj.is_partial_approval is True
    assert item.copy_count_approved == 32
    assert request_obj.status_history.filter(action='APPROVE').exists()


@pytest.mark.django_db
def test_operator_can_complete_operational_flow(client):
    professor = User.objects.create_user(username='profesor-3', password='x')
    approver = User.objects.create_user(username='jefatura-3', password='x')
    operator = User.objects.create_user(username='operadora', password='x')
    departamento = Departamento.objects.create(codigo='DEP-FOT-3', nombre='Ciencias')

    grant_permissions(
        operator,
        'fotocopiadora.view_printrequest',
        'fotocopiadora.view_operational_queue_printrequest',
        'fotocopiadora.operate_printrequest',
        'fotocopiadora.mark_ready_printrequest',
        'fotocopiadora.deliver_printrequest',
        'fotocopiadora.close_printrequest',
    )

    request_obj = PrintRequest.objects.create(
        numero='PR-OP-1',
        title='Laboratorio',
        request_type='PRINT',
        status=PrintRequestStatus.APPROVED,
        required_at=timezone.now() + datetime.timedelta(days=1),
        requester=professor,
        approver=approver,
        departamento=departamento,
        approved_at=timezone.now(),
    )
    PrintRequestItem.objects.create(
        request=request_obj,
        line_number=1,
        document_title='Guía laboratorio',
        page_size='A4',
        print_side='SINGLE',
        color_mode='BW',
        copy_count_requested=20,
        copy_count_approved=20,
        original_page_count=4,
    )

    client.force_login(operator)
    for action in ['START', 'READY', 'DELIVER', 'CLOSE']:
        response = client.post(
            reverse('fotocopiadora:transicion_solicitud_impresion', args=[request_obj.pk]),
            data={'action': action, 'comment': f'Paso {action.lower()}'},
        )
        assert response.status_code == 302

    request_obj.refresh_from_db()
    assert request_obj.status == PrintRequestStatus.CLOSED
    assert request_obj.status_history.count() == 4


@pytest.mark.django_db
def test_approver_cannot_view_or_approve_request_outside_scope(client):
    professor = User.objects.create_user(username='profesor-4', password='x')
    approver = User.objects.create_user(username='jefatura-fuera', password='x')
    departamento_ok = Departamento.objects.create(codigo='DEP-FOT-4', nombre='Historia')
    departamento_other = Departamento.objects.create(codigo='DEP-FOT-5', nombre='Música')

    grant_permissions(
        approver,
        'fotocopiadora.view_printrequest',
        'fotocopiadora.view_department_printrequest',
        'fotocopiadora.approve_printrequest',
    )
    PrintRoleMembership.objects.create(user=approver, role=PrintMembershipRole.APPROVER, departamento=departamento_other)

    request_obj = PrintRequest.objects.create(
        numero='PR-OUT-1',
        title='Solicitud fuera de alcance',
        request_type='PHOTOCOPY',
        status=PrintRequestStatus.PENDING_APPROVAL,
        required_at=timezone.now() + datetime.timedelta(days=1),
        requester=professor,
        departamento=departamento_ok,
        submitted_at=timezone.now(),
    )
    PrintRequestItem.objects.create(
        request=request_obj,
        line_number=1,
        document_title='Apunte',
        page_size='A4',
        print_side='SINGLE',
        color_mode='BW',
        copy_count_requested=10,
        original_page_count=1,
    )

    client.force_login(approver)

    detail_response = client.get(reverse('fotocopiadora:detalle_solicitud_impresion', args=[request_obj.pk]))
    assert detail_response.status_code == 403

    transition_response = client.post(
        reverse('fotocopiadora:transicion_solicitud_impresion', args=[request_obj.pk]),
        data={'action': 'APPROVE', 'comment': 'No debería aprobar'},
    )
    assert transition_response.status_code == 403

    request_obj.refresh_from_db()
    assert request_obj.status == PrintRequestStatus.PENDING_APPROVAL
