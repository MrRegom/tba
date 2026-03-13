"""
Bootstrap de roles oficiales y permisos sugeridos para el ERP escolar.

Este comando no reemplaza la lógica de ámbito: solo configura roles funcionales
base usando Groups + Permissions.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from apps.accounts.role_catalog import get_official_role_names

ROLE_DEFINITIONS = {
    'Superadministrador': {
        'description': 'Control total del sistema, incluyendo seguridad y auditoría.',
        'permissions': ['*'],
    },
    'Administrador Institucional': {
        'description': 'Administra usuarios, perfiles de acceso, catálogos organizacionales y consulta global.',
        'permissions': [
            'auth.view_user', 'auth.add_user', 'auth.change_user',
            'auth.view_group',
            'accounts.manage_access_profiles',
            'accounts.view_all_auditoria',
            'accounts.export_sensitive_reports',
            'solicitudes.view_solicitud',
            'compras.view_ordencompra',
            'bodega.view_articulo',
            'activos.view_activo',
        ],
    },
    'Solicitante': {
        'description': 'Crea y consulta sus propias solicitudes.',
        'permissions': [
            'solicitudes.view_solicitud',
            'solicitudes.add_solicitud',
            'solicitudes.ver_solicitudes_articulos',
            'solicitudes.crear_solicitud_articulos',
            'solicitudes.ver_solicitudes_bienes',
            'solicitudes.crear_solicitud_bienes',
            'solicitudes.ver_mis_solicitudes',
            'solicitudes.editar_mis_solicitudes',
            'solicitudes.eliminar_mis_solicitudes',
            'fotocopiadora.view_trabajofotocopia',
            'fotocopiadora.add_trabajofotocopia',
        ],
    },
    'Aprobador / Jefatura': {
        'description': 'Aprueba o rechaza solicitudes dentro de su dependencia.',
        'permissions': [
            'solicitudes.view_solicitud',
            'solicitudes.aprobar_solicitudes',
            'solicitudes.rechazar_solicitudes',
            'solicitudes.view_historialsolicitud',
        ],
    },
    'Encargado de Bodega': {
        'description': 'Gestiona artículos, stock, entregas y recepciones de su bodega.',
        'permissions': [
            'bodega.view_articulo', 'bodega.add_articulo', 'bodega.change_articulo',
            'bodega.view_categoria', 'bodega.add_categoria', 'bodega.change_categoria',
            'bodega.view_marca', 'bodega.add_marca', 'bodega.change_marca',
            'bodega.view_unidadmedida', 'bodega.add_unidadmedida', 'bodega.change_unidadmedida',
            'bodega.view_movimiento', 'bodega.add_movimiento',
            'bodega.registrar_entrada', 'bodega.registrar_salida', 'bodega.ajustar_stock',
            'bodega.ver_historial_movimientos', 'bodega.ver_reportes_inventario',
            'bodega.view_entregaarticulo', 'bodega.add_entregaarticulo',
            'bodega.view_recepcionarticulo', 'bodega.add_recepcionarticulo', 'bodega.change_recepcionarticulo',
            'compras.view_ordencompra',
        ],
    },
    'Operario de Bodega': {
        'description': 'Opera entregas de artículos y revisa movimientos de su bodega, sin acceso a gestores.',
        'permissions': [
            'bodega.view_entregaarticulo',
            'bodega.add_entregaarticulo',
            'bodega.view_movimiento',
            'bodega.add_movimiento',
            'bodega.registrar_salida',
            'bodega.ver_historial_movimientos',
        ],
    },
    'Gestor de Compras': {
        'description': 'Gestiona proveedores, órdenes de compra y seguimiento operativo del módulo.',
        'permissions': [
            'compras.view_proveedor', 'compras.add_proveedor', 'compras.change_proveedor',
            'compras.view_ordencompra', 'compras.add_ordencompra', 'compras.change_ordencompra',
            'compras.view_estadoordencompra',
            'compras.ver_todas_ordenescompra',
            'compras.ver_reportes_compras',
            'solicitudes.view_solicitud',
        ],
    },
    'Aprobador de Compras': {
        'description': 'Aprueba o rechaza órdenes de compra sin operar inventario.',
        'permissions': [
            'compras.view_ordencompra',
            'compras.aprobar_ordencompra',
            'compras.rechazar_ordencompra',
            'compras.cerrar_ordencompra',
            'compras.anular_ordencompra',
            'compras.ver_todas_ordenescompra',
            'compras.ver_reportes_compras',
        ],
    },
    'Gestor de Activos Fijos': {
        'description': 'Gestiona bienes/activos, movimientos y asignaciones del inventario patrimonial.',
        'permissions': [
            'activos.view_activo', 'activos.add_activo', 'activos.change_activo',
            'activos.view_movimientoactivo', 'activos.add_movimientoactivo',
            'activos.view_categoriaactivo', 'activos.add_categoriaactivo', 'activos.change_categoriaactivo',
            'activos.view_estadoactivo', 'activos.view_ubicacion',
            'activos.gestionar_inventario', 'activos.ajustar_inventario',
            'activos.ver_reportes_inventario', 'activos.exportar_activos',
            'compras.view_ordencompra',
        ],
    },
    'Auditor / Consulta': {
        'description': 'Solo lectura, exportación y acceso controlado a auditoría.',
        'permissions': [
            'accounts.view_all_auditoria',
            'accounts.export_sensitive_reports',
            'solicitudes.view_solicitud',
            'compras.view_ordencompra',
            'bodega.view_articulo',
            'bodega.ver_historial_movimientos',
            'activos.view_activo',
            'activos.view_movimientoactivo',
        ],
    },
    'Operador de Fotocopiadora': {
        'description': 'Opera solicitudes y equipos de fotocopiadora.',
        'permissions': [
            'fotocopiadora.view_trabajofotocopia',
            'fotocopiadora.add_trabajofotocopia',
            'fotocopiadora.change_trabajofotocopia',
            'fotocopiadora.view_fotocopiadoraequipo',
            'fotocopiadora.gestionar_equipos_fotocopiadora',
        ],
    },
    'Encargado de Bajas': {
        'description': 'Gestiona expedientes y ejecución operativa de bajas.',
        'permissions': [
            'bajas_inventario.view_bajainventario',
            'bajas_inventario.add_bajainventario',
            'bajas_inventario.change_bajainventario',
            'bajas_inventario.registrar_baja',
            'bajas_inventario.aprobar_baja',
            'bajas_inventario.ver_reportes_bajas',
            'activos.view_activo',
            'bodega.view_articulo',
        ],
    },
}


class Command(BaseCommand):
    help = 'Crea y actualiza los roles oficiales de autorización del sistema.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Limpia permisos antes de reasignarlos.')

    def handle(self, *args, **options):
        reset = options['reset']
        all_permissions = Permission.objects.select_related('content_type').all()
        official_names = set(get_official_role_names())

        for role_name, config in ROLE_DEFINITIONS.items():
            if role_name not in official_names:
                self.stdout.write(self.style.WARNING(
                    f'Rol no declarado en catálogo oficial: {role_name}'
                ))
            group, _ = Group.objects.get_or_create(name=role_name)
            if reset:
                group.permissions.clear()

            permission_codes = config['permissions']
            if permission_codes == ['*']:
                group.permissions.set(all_permissions)
            else:
                permissions = []
                for perm_code in permission_codes:
                    app_label, codename = perm_code.split('.', 1)
                    permission = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=codename,
                    ).first()
                    if permission:
                        permissions.append(permission)
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Permiso no encontrado para {role_name}: {perm_code}'
                        ))
                group.permissions.set(permissions)

            self.stdout.write(self.style.SUCCESS(f'Rol actualizado: {role_name}'))
