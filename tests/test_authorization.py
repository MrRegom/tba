import datetime

import pytest
from django.contrib.auth.models import Permission, User

from apps.accounts.models import AccessScope
from apps.bodega.models import Articulo, Bodega, Categoria, UnidadMedida
from apps.solicitudes.models import Area, Departamento, EstadoSolicitud, Solicitud, TipoSolicitud
from core.authz import scope_articulos_for_user, scope_solicitudes_for_user


@pytest.mark.django_db
def test_user_access_profile_is_created_automatically():
    user = User.objects.create_user(username='perfil-auto', password='x')

    assert hasattr(user, 'access_profile')
    assert user.access_profile.scope_level == AccessScope.OWN


@pytest.mark.django_db
def test_scope_solicitudes_for_department_user():
    user = User.objects.create_user(username='jefatura', password='x')
    other = User.objects.create_user(username='otro', password='x')
    responsable = User.objects.create_user(username='bodega', password='x')

    permission = Permission.objects.get(codename='view_solicitud', content_type__app_label='solicitudes')
    user.user_permissions.add(permission)

    departamento_ok = Departamento.objects.create(codigo='DEP-1', nombre='Direccion')
    departamento_other = Departamento.objects.create(codigo='DEP-2', nombre='UTP')
    area_ok = Area.objects.create(codigo='AR-1', nombre='Direccion', departamento=departamento_ok)
    tipo = TipoSolicitud.objects.create(codigo='TIP-1', nombre='Normal')
    estado = EstadoSolicitud.objects.create(codigo='PEN', nombre='Pendiente', es_inicial=True)
    bodega = Bodega.objects.create(codigo='BOD-1', nombre='Central', responsable=responsable)

    visible = Solicitud.objects.create(
        tipo='ARTICULO',
        numero='SOL-001',
        fecha_requerida=datetime.date.today(),
        tipo_solicitud=tipo,
        estado=estado,
        solicitante=other,
        departamento=departamento_ok,
        area=area_ok,
        bodega_origen=bodega,
        motivo='Materiales',
    )
    hidden = Solicitud.objects.create(
        tipo='ARTICULO',
        numero='SOL-002',
        fecha_requerida=datetime.date.today(),
        tipo_solicitud=tipo,
        estado=estado,
        solicitante=other,
        departamento=departamento_other,
        bodega_origen=bodega,
        motivo='Otros materiales',
    )

    user.access_profile.scope_level = AccessScope.DEPARTAMENTO
    user.access_profile.departamento = departamento_ok
    user.access_profile.save()

    result = scope_solicitudes_for_user(Solicitud.objects.all(), user)

    assert list(result) == [visible]
    assert hidden not in result


@pytest.mark.django_db
def test_scope_articulos_with_view_permission_returns_full_catalog():
    user = User.objects.create_user(username='gestor-bodega', password='x')
    responsable = User.objects.create_user(username='encargado', password='x')
    permission = Permission.objects.get(codename='view_articulo', content_type__app_label='bodega')
    user.user_permissions.add(permission)

    unidad = UnidadMedida.objects.create(codigo='UNI', nombre='Unidad', simbolo='un')
    categoria = Categoria.objects.create(codigo='CAT-1', nombre='Papeleria')
    bodega_1 = Bodega.objects.create(codigo='BOD-1', nombre='Central', responsable=responsable)
    bodega_2 = Bodega.objects.create(codigo='BOD-2', nombre='Secundaria', responsable=responsable)

    visible = Articulo.objects.create(
        codigo='ART-1',
        nombre='Cuaderno',
        categoria=categoria,
        unidad_medida=unidad,
        ubicacion_fisica=bodega_1,
    )
    hidden = Articulo.objects.create(
        codigo='ART-2',
        nombre='Lapiz',
        categoria=categoria,
        unidad_medida=unidad,
        ubicacion_fisica=bodega_2,
    )

    result = scope_articulos_for_user(Articulo.objects.all(), user)

    assert set(result) == {visible, hidden}


@pytest.mark.django_db
def test_scope_articulos_without_view_permission_returns_none():
    user = User.objects.create_user(username='operario-sin-catalogo', password='x')
    responsable = User.objects.create_user(username='encargado-2', password='x')
    unidad = UnidadMedida.objects.create(codigo='UN2', nombre='Unidad 2', simbolo='u2')
    categoria = Categoria.objects.create(codigo='CAT-2', nombre='Aseo')
    bodega = Bodega.objects.create(codigo='BOD-R', nombre='Responsable', responsable=responsable)

    Articulo.objects.create(
        codigo='ART-R',
        nombre='Escoba',
        categoria=categoria,
        unidad_medida=unidad,
        ubicacion_fisica=bodega,
    )

    result = scope_articulos_for_user(Articulo.objects.all(), user)

    assert result.count() == 0
