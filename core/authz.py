"""
Servicios de autorización y filtrado por ámbito.

Centraliza reglas de acceso para evitar que la seguridad quede repartida
entre templates, vistas y consultas duplicadas.
"""
from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.accounts.models import AccessScope


def _profile(user):
    return getattr(user, 'access_profile', None)


def _resolve_user_bodega_scope_id(user):
    """
    Resuelve la bodega operativa del usuario.

    Prioridad:
    1. Perfil de acceso explícito
    2. Bodega donde el usuario figura como responsable, si es única
    """
    profile = _profile(user)
    if profile and profile.scope_level == AccessScope.BODEGA and profile.bodega_id:
        return profile.bodega_id

    try:
        from apps.bodega.models import Bodega
    except Exception:
        return None

    bodegas_ids = list(
        Bodega.objects.filter(responsable=user, activo=True, eliminado=False).values_list('id', flat=True)[:2]
    )
    if len(bodegas_ids) == 1:
        return bodegas_ids[0]
    return None


def has_global_scope(user) -> bool:
    profile = _profile(user)
    return bool(user.is_superuser or (profile and profile.scope_level == AccessScope.GLOBAL))


def can_manage_authorization(user) -> bool:
    profile = _profile(user)
    return bool(
        user.is_superuser
        or user.has_perm('accounts.manage_access_profiles')
        or (profile and profile.puede_administrar_autorizacion)
    )


def can_view_solicitud(user, solicitud) -> bool:
    if not user.is_authenticated or not user.has_perm('solicitudes.view_solicitud'):
        return False
    if has_global_scope(user) or user.has_perm('solicitudes.ver_todas_solicitudes'):
        return True

    profile = _profile(user)
    if solicitud.solicitante_id == user.id:
        return True
    if not profile:
        return False
    if profile.scope_level == AccessScope.DEPARTAMENTO and profile.departamento_id:
        return solicitud.departamento_id == profile.departamento_id
    if profile.scope_level == AccessScope.AREA and profile.area_id:
        return solicitud.area_id == profile.area_id
    if profile.scope_level == AccessScope.OWN:
        return False
    return False


def scope_solicitudes_for_user(queryset: QuerySet, user) -> QuerySet:
    if not user.is_authenticated:
        return queryset.none()
    if has_global_scope(user) or user.has_perm('solicitudes.ver_todas_solicitudes'):
        return queryset

    profile = _profile(user)
    filters = Q(solicitante=user)
    if profile:
        if profile.scope_level == AccessScope.DEPARTAMENTO and profile.departamento_id:
            filters |= Q(departamento_id=profile.departamento_id)
        elif profile.scope_level == AccessScope.AREA and profile.area_id:
            filters |= Q(area_id=profile.area_id)
    return queryset.filter(filters).distinct()


def can_view_orden_compra(user, orden) -> bool:
    if not user.is_authenticated or not user.has_perm('compras.view_ordencompra'):
        return False
    if has_global_scope(user) or user.has_perm('compras.ver_todas_ordenescompra'):
        return True

    profile = _profile(user)
    if orden.solicitante_id == user.id or orden.aprobador_id == user.id:
        return True
    if profile and profile.scope_level == AccessScope.BODEGA and profile.bodega_id:
        return orden.bodega_destino_id == profile.bodega_id
    if profile and profile.scope_level == AccessScope.OWN:
        return False

    # Inferencia razonable: una orden es visible si nace de una solicitud visible.
    return orden.solicitudes.filter(pk__in=scope_solicitudes_for_user(orden.solicitudes.all(), user)).exists()


def scope_ordenes_compra_for_user(queryset: QuerySet, user) -> QuerySet:
    if not user.is_authenticated:
        return queryset.none()
    if has_global_scope(user) or user.has_perm('compras.ver_todas_ordenescompra'):
        return queryset

    profile = _profile(user)
    filters = Q(solicitante=user) | Q(aprobador=user) | Q(solicitudes__solicitante=user)
    if profile and profile.scope_level == AccessScope.BODEGA and profile.bodega_id:
        filters |= Q(bodega_destino_id=profile.bodega_id)
    if profile and profile.scope_level == AccessScope.DEPARTAMENTO and profile.departamento_id:
        filters |= Q(solicitudes__departamento_id=profile.departamento_id)
    if profile and profile.scope_level == AccessScope.AREA and profile.area_id:
        filters |= Q(solicitudes__area_id=profile.area_id)
    return queryset.filter(filters).distinct()


def can_view_articulo(user, articulo) -> bool:
    if not user.is_authenticated or not user.has_perm('bodega.view_articulo'):
        return False
    return True


def scope_articulos_for_user(queryset: QuerySet, user) -> QuerySet:
    if not user.is_authenticated:
        return queryset.none()
    if has_global_scope(user) or user.has_perm('bodega.view_articulo'):
        return queryset
    return queryset.none()


def can_view_activo(user, activo) -> bool:
    """
    Activos aún no tiene un alcance organizacional fuerte en su modelo.

    Mientras no exista FK directa a establecimiento/dependencia/ubicación operativa,
    se usa permiso del módulo como condición principal y se documenta esta limitación.
    """
    return bool(user.is_authenticated and user.has_perm('activos.view_activo'))


def scope_activos_for_user(queryset: QuerySet, user) -> QuerySet:
    if not user.is_authenticated or not user.has_perm('activos.view_activo'):
        return queryset.none()
    return queryset


def can_approve_purchase(user, orden) -> bool:
    profile = _profile(user)
    if not user.is_authenticated or not user.has_perm('compras.aprobar_ordencompra'):
        return False
    if not getattr(profile, 'puede_aprobar_propias', False) and orden.solicitante_id == user.id:
        return False
    return can_view_orden_compra(user, orden)
