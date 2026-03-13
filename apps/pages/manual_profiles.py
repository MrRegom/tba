"""
Perfiles del manual de usuario vinculados a roles reales del sistema.
"""

MANUAL_PROFILE_DEFINITIONS = {
    'solicitante': {
        'label': 'Solicitante',
        'description': 'Creación y seguimiento de solicitudes propias.',
        'roles': ['Solicitante'],
    },
    'aprobador': {
        'label': 'Aprobador / Jefatura',
        'description': 'Revisión y resolución de solicitudes de su ámbito.',
        'roles': ['Aprobador / Jefatura'],
    },
    'bodega': {
        'label': 'Encargado de Bodega',
        'description': 'Recepciones, entregas, stock y artículos.',
        'roles': ['Encargado de Bodega'],
    },
    'compras': {
        'label': 'Compras',
        'description': 'Órdenes de compra, proveedores y seguimiento.',
        'roles': ['Gestor de Compras', 'Aprobador de Compras'],
    },
    'inventario': {
        'label': 'Activos y Bajas',
        'description': 'Inventario patrimonial, movimientos y bajas.',
        'roles': ['Gestor de Activos Fijos', 'Encargado de Bajas'],
    },
    'fotocopiadora': {
        'label': 'Fotocopiadora',
        'description': 'Trabajos, equipos y control operativo.',
        'roles': ['Operador de Fotocopiadora'],
    },
    'auditoria': {
        'label': 'Auditor / Consulta',
        'description': 'Consulta, auditoría y revisión de trazabilidad.',
        'roles': ['Auditor / Consulta'],
    },
    'administracion': {
        'label': 'Administración',
        'description': 'Usuarios, perfiles de acceso, permisos y control global.',
        'roles': ['Administrador Institucional', 'Superadministrador'],
    },
}


def resolve_manual_profiles(group_names: list[str]) -> list[dict]:
    profiles = []
    for key, definition in MANUAL_PROFILE_DEFINITIONS.items():
        if any(role_name in group_names for role_name in definition['roles']):
            profiles.append({
                'key': key,
                'label': definition['label'],
                'description': definition['description'],
            })
    return profiles
