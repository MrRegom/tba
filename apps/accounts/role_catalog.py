"""
Catálogo oficial de roles funcionales del sistema.

Se usa para:
- bootstrap de grupos
- vistas de asignación
- documentación funcional
"""

OFFICIAL_ROLE_CATALOG = {
    'Superadministrador': {
        'category': 'Administracion',
        'description': 'Control total técnico y funcional del sistema.',
        'scope': 'Global',
        'can_approve': True,
    },
    'Administrador Institucional': {
        'category': 'Administracion',
        'description': 'Administra usuarios, perfiles de acceso y configuración institucional.',
        'scope': 'Global',
        'can_approve': False,
    },
    'Solicitante': {
        'category': 'Solicitudes',
        'description': 'Crea y consulta sus propias solicitudes y requerimientos.',
        'scope': 'Propio',
        'can_approve': False,
    },
    'Aprobador / Jefatura': {
        'category': 'Solicitudes',
        'description': 'Aprueba o rechaza solicitudes del área o departamento asignado.',
        'scope': 'Area o departamento',
        'can_approve': True,
    },
    'Encargado de Bodega': {
        'category': 'Operacion',
        'description': 'Gestiona artículos, stock, recepciones y entregas de la bodega asignada.',
        'scope': 'Bodega',
        'can_approve': False,
    },
    'Operario de Bodega': {
        'category': 'Operacion',
        'description': 'Opera entregas de artículos y consulta movimientos sin acceder a gestores de artículos.',
        'scope': 'Bodega',
        'can_approve': False,
    },
    'Gestor de Compras': {
        'category': 'Operacion',
        'description': 'Gestiona proveedores y órdenes de compra del módulo de compras.',
        'scope': 'Modulo o alcance asignado',
        'can_approve': False,
    },
    'Aprobador de Compras': {
        'category': 'Operacion',
        'description': 'Aprueba, rechaza o anula órdenes de compra según política institucional.',
        'scope': 'Modulo o alcance asignado',
        'can_approve': True,
    },
    'Gestor de Activos Fijos': {
        'category': 'Operacion',
        'description': 'Administra bienes, altas, movimientos y control patrimonial.',
        'scope': 'Inventario patrimonial',
        'can_approve': False,
    },
    'Auditor / Consulta': {
        'category': 'Control',
        'description': 'Acceso de solo lectura para auditoría, revisión y exportación controlada.',
        'scope': 'Lectura global o restringida',
        'can_approve': False,
    },
    'Operador de Fotocopiadora': {
        'category': 'Operacion',
        'description': 'Opera solicitudes y equipos del módulo de fotocopiadora.',
        'scope': 'Modulo',
        'can_approve': False,
    },
    'Encargado de Bajas': {
        'category': 'Control',
        'description': 'Gestiona expedientes y ejecución operativa de bajas de inventario.',
        'scope': 'Modulo o alcance asignado',
        'can_approve': False,
    },
}


def get_official_role_names():
    return list(OFFICIAL_ROLE_CATALOG.keys())
