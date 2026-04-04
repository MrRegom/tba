# Autorización ERP Escolar

## Objetivo

Definir una capa de autorización clara, mantenible y segura para el ERP escolar,
separando:

- lo que un usuario puede ver
- lo que puede crear
- lo que puede aprobar
- lo que puede editar
- lo que puede eliminar
- lo que puede auditar
- lo que puede administrar

## Principios

1. `Group` define el rol funcional.
2. `Permission` define la acción.
3. `UserAccessProfile` define el alcance de visualización y operación.
4. La seguridad no depende del frontend.
5. Las acciones de alto riesgo se separan de las acciones operativas.

## Componentes implementados

- `apps.accounts.models.UserAccessProfile`
- `core.authz`
- `core.mixins.ScopedObjectPermissionMixin`
- `manage.py setup_authorization_roles`

## Roles Oficiales

### Superadministrador

- Propósito: control total técnico y funcional.
- Alcance: global.
- Puede aprobar: sí.
- Puede ejecutar: sí.
- Restricción: uso excepcional.

### Administrador Institucional

- Propósito: administrar usuarios, perfiles de acceso y parametrización institucional.
- Módulos: accounts, reportes, consulta global.
- Puede aprobar: no como función operativa por defecto.
- Puede ejecutar: administración.
- Restricción: no debe operar stock ni aprobar compras del día a día.

### Solicitante

- Propósito: crear y consultar sus propias solicitudes.
- Módulos: solicitudes, fotocopiadora.
- Puede aprobar: no.
- Puede ejecutar: creación y edición de lo propio en estados permitidos.
- Alcance: propio.

### Aprobador / Jefatura

- Propósito: aprobar o rechazar solicitudes del área o departamento.
- Módulos: solicitudes.
- Puede aprobar: sí.
- Puede ejecutar: no stock, no compras, no administración.
- Alcance: departamento o área.

### Encargado de Bodega

- Propósito: operar la bodega asignada.
- Módulos: bodega, recepciones, entregas.
- Puede crear: artículos, categorías, marcas, unidades, movimientos.
- Puede aprobar: no compras.
- Puede ejecutar: entradas, salidas, ajustes y recepciones.
- Alcance: bodega.

### Gestor de Compras

- Propósito: gestionar proveedores y órdenes de compra.
- Módulos: compras.
- Puede crear: proveedores y órdenes.
- Puede aprobar: no, salvo rol adicional explícito.
- Puede ejecutar: gestión operativa del módulo.
- Alcance: global del módulo o por ámbito definido.

### Aprobador de Compras

- Propósito: aprobar, rechazar, anular o cerrar órdenes de compra.
- Módulos: compras.
- Puede aprobar: sí.
- Puede ejecutar: no stock.
- Alcance: definido por perfil.

### Gestor de Activos Fijos

- Propósito: administrar bienes y movimientos patrimoniales.
- Módulos: activos.
- Puede crear: bienes/activos.
- Puede aprobar: no bajas ni compras por defecto.
- Puede ejecutar: altas, movimientos, ajustes, exportación.
- Alcance: hoy depende del permiso del módulo; el modelo aún no tiene un scope patrimonial fuerte.

### Auditor / Consulta

- Propósito: revisión, consulta y exportación controlada.
- Módulos: auditoría, reportes, consulta transversal.
- Puede aprobar: no.
- Puede ejecutar: no.
- Alcance: global de lectura o restringido según perfil.

### Operador de Fotocopiadora

- Propósito: operar solicitudes de reprografía.
- Módulos: fotocopiadora.
- Puede aprobar: no.
- Puede ejecutar: sí, en su módulo.

### Encargado de Bajas

- Propósito: gestionar expedientes y ejecución de bajas.
- Módulos: bajas, activos, bodega.
- Puede aprobar: no por defecto.
- Puede ejecutar: sí.
- Restricción: no debe aprobar la misma baja que inicia.

## Matriz Resumida

| Rol | Ver | Crear | Editar | Eliminar | Aprobar | Auditar | Administrar |
|---|---|---|---|---|---|---|---|
| Superadministrador | Todo | Todo | Todo | Todo | Sí | Sí | Sí |
| Administrador Institucional | Global | Usuarios/perfiles/catálogos | Sí | Restringido | No | Consulta global | Sí |
| Solicitante | Propio | Solicitudes propias | Propio | Propio en estado inicial | No | No | No |
| Aprobador / Jefatura | Área/departamento | No | No | No | Solicitudes | No | No |
| Encargado de Bodega | Bodega | Artículos y operaciones de bodega | Sí | Restringido | No | Historial de bodega | No |
| Gestor de Compras | Compras/scope | Órdenes y proveedores | Sí | Restringido | No | Reportes de compras | No |
| Aprobador de Compras | Compras/scope | No | No | No | Órdenes de compra | No | No |
| Gestor de Activos Fijos | Activos | Bienes/activos | Sí | Restringido | No | Reportes de activos | No |
| Auditor / Consulta | Solo lectura | No | No | No | No | Sí | No |
| Operador de Fotocopiadora | Módulo propio | Sí | Sí | Restringido | No | No | No |
| Encargado de Bajas | Scope | Expedientes de baja | Sí | Restringido | No | Revisión del expediente | No |

## Permisos Críticos

Requieren doble control o auditoría reforzada:

- `bodega.ajustar_stock`
- `compras.aprobar_ordencompra`
- `compras.anular_ordencompra`
- confirmación de recepciones que impactan stock
- asignaciones críticas de activos
- administración de perfiles de acceso
- exportación de reportes sensibles
- visualización de auditoría global

## Visualización

### Niveles

- `GLOBAL`
- `DEPARTAMENTO`
- `AREA`
- `BODEGA`
- `OWN`

### Reglas

1. La vista protege acceso por permiso.
2. El queryset protege acceso por ámbito.
3. El detalle protege acceso por objeto.
4. El template solo refleja capacidades ya autorizadas.

## Restricciones actuales del dominio

### Activos

El modelo `Activos` no expone hoy una FK organizacional clara para aplicar el mismo
scope fuerte que sí existe en `Solicitudes`, `Compras` y `Bodega`.

Estado actual:

- se protege por permiso de módulo
- queda preparado para endurecerse con `core.authz`

Siguiente etapa recomendada:

- agregar relación formal a ubicación operativa, dependencia o establecimiento responsable

## Comando operativo

```bash
python manage.py setup_authorization_roles --reset
```

## Migración recomendada

1. Crear `UserAccessProfile`.
2. Poblar alcance por usuario.
3. Crear grupos oficiales.
4. Migrar usuarios desde roles ambiguos.
5. Quitar permisos directos a usuario salvo excepción auditada.
6. Revisar endpoints AJAX y reportes restantes.
