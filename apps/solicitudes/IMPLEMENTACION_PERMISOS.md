# Implementación del Sistema de Permisos - Módulo de Solicitudes

## Resumen de la Implementación

El módulo de solicitudes implementa un sistema de permisos organizados por categorías/módulos que se integra con el sistema centralizado de administración de permisos de la aplicación en `/usuarios/permisos/`.

## Arquitectura del Sistema

### 1. Modelo de Permisos Extendidos

**Archivo**: `apps/solicitudes/models_permisos.py`

Se creó el modelo `PermisoExtendido` que extiende el modelo `Permission` de Django mediante una relación OneToOne:

```python
class PermisoExtendido(models.Model):
    permiso = models.OneToOneField(Permission, ...)
    modulo = models.CharField(choices=MODULO_CHOICES, ...)  # Categoría del permiso
    descripcion_extendida = models.TextField(...)
    orden = models.IntegerField(...)
    destacado = models.BooleanField(...)
    color = models.CharField(...)
    icono = models.CharField(...)
```

**Ventajas de este enfoque**:
- ✅ No modifica las tablas core de Django (`auth_permission`, `django_content_type`)
- ✅ Permite agregar metadatos a los permisos sin alterar el modelo Permission
- ✅ Se integra perfectamente con el sistema de permisos existente
- ✅ Los permisos se almacenan en la base de datos, no en código JSON

### 2. Módulos/Categorías de Permisos

Los permisos están organizados en **4 módulos principales**:

#### GESTIÓN
Administración completa del módulo de solicitudes.

| Permiso | Descripción |
|---------|-------------|
| `gestionar_solicitudes` | Puede administrar completamente el módulo de solicitudes |
| `aprobar_solicitudes` | Puede aprobar solicitudes pendientes de aprobación |
| `rechazar_solicitudes` | Puede rechazar solicitudes y agregar observaciones |
| `despachar_solicitudes` | Puede despachar solicitudes aprobadas y registrar entregas |
| `ver_todas_solicitudes` | Puede visualizar todas las solicitudes del sistema |
| `editar_cualquier_solicitud` | Puede editar cualquier solicitud independiente del estado o solicitante |
| `eliminar_cualquier_solicitud` | Puede eliminar cualquier solicitud independiente del estado o solicitante |

#### SOLICITUD ARTÍCULOS
Crear y gestionar solicitudes de artículos de bodega.

| Permiso | Descripción |
|---------|-------------|
| `crear_solicitud_articulos` | Puede crear nuevas solicitudes de artículos de bodega |
| `ver_solicitudes_articulos` | Puede ver todas las solicitudes de artículos del sistema |

#### SOLICITUD BIENES
Crear y gestionar solicitudes de bienes/activos.

| Permiso | Descripción |
|---------|-------------|
| `crear_solicitud_bienes` | Puede crear nuevas solicitudes de bienes/activos de inventario |
| `ver_solicitudes_bienes` | Puede ver todas las solicitudes de bienes/activos del sistema |

#### MIS SOLICITUDES
Gestión de solicitudes propias del usuario.

| Permiso | Descripción |
|---------|-------------|
| `ver_mis_solicitudes` | Puede ver sus propias solicitudes creadas |
| `editar_mis_solicitudes` | Puede editar sus propias solicitudes en estado borrador o pendiente |
| `eliminar_mis_solicitudes` | Puede eliminar sus propias solicitudes en estado borrador |

## Integración con Sistema Centralizado

### URL de Gestión de Permisos

El sistema centralizado de permisos se encuentra en:
- **URL**: `http://127.0.0.1:8000/usuarios/permisos/`
- **Templates**: `templates/account/gestion_usuarios/`

Los permisos del módulo de solicitudes se gestionan desde este sistema centralizado, **NO** desde el módulo de solicitudes.

### Cómo Acceder a los Permisos Categorizados

El sistema centralizado puede consultar los permisos extendidos de la siguiente manera:

```python
from apps.solicitudes.models_permisos import PermisoExtendido
from apps.solicitudes.permissions import (
    obtener_permisos_por_modulo,
    enriquecer_permisos_con_modulo
)

# Opción 1: Obtener permisos organizados por módulo
permisos_por_modulo = obtener_permisos_por_modulo()
# Resultado:
# {
#     'Gestión': [Permission, Permission, ...],
#     'Solicitud Artículos': [Permission, ...],
#     ...
# }

# Opción 2: Enriquecer permisos con información del módulo
from django.contrib.auth.models import Permission
permisos = Permission.objects.filter(content_type__app_label='solicitudes')
permisos_enriquecidos = enriquecer_permisos_con_modulo(permisos)

# Ahora cada permiso tiene:
# - permiso.modulo: 'Gestión', 'Solicitud Artículos', etc.
# - permiso.destacado: True/False
# - permiso.color: '#0d6efd'
# - permiso.icono: 'bi bi-gear-fill'
# - permiso.descripcion_extendida: Descripción detallada
```

### Template de Ejemplo para Sistema Centralizado

```django
{% comment %}
En templates/account/gestion_usuarios/lista_permisos.html
Muestra permisos organizados por módulo
{% endcomment %}

{% load solicitudes_tags %}

<div class="permisos-container">
    <h2>Permisos del Módulo de Solicitudes</h2>

    {% with permisos_por_modulo=permisos_solicitudes_por_modulo %}
        {% for modulo, permisos in permisos_por_modulo.items %}
        <div class="modulo-seccion mb-4">
            <h4 class="border-bottom pb-2">{{ modulo }}</h4>

            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Módulo</th>
                        <th>Código</th>
                        <th>Nombre del Permiso</th>
                        <th>Tipo</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for permiso in permisos %}
                    <tr>
                        <td>
                            <span class="badge" style="background-color: {{ permiso.extendido.color }}">
                                <i class="{{ permiso.extendido.icono }}"></i>
                                {{ permiso.extendido.get_modulo_display }}
                            </span>
                        </td>
                        <td><code>{{ permiso.codename }}</code></td>
                        <td>
                            {{ permiso.name }}
                            {% if permiso.extendido.destacado %}
                                <i class="bi bi-star-fill text-warning"></i>
                            {% endif %}
                        </td>
                        <td>
                            {% if 'crear_' in permiso.codename %}
                                <span class="badge bg-success">Crear</span>
                            {% elif 'editar_' in permiso.codename %}
                                <span class="badge bg-primary">Editar</span>
                            {% elif 'eliminar_' in permiso.codename %}
                                <span class="badge bg-danger">Eliminar</span>
                            {% elif 'ver_' in permiso.codename %}
                                <span class="badge bg-info">Ver</span>
                            {% else %}
                                <span class="badge bg-warning">Personalizado</span>
                            {% endif %}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary">Asignar</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    {% endwith %}
</div>
```

## Comandos de Management

### Setup de Permisos

**Comando**: `python manage.py setup_permisos_solicitudes`

Este comando debe ejecutarse:
1. **Después de crear el modelo Solicitud** por primera vez
2. **Después de agregar nuevos permisos** al modelo
3. **Cuando se actualizan las categorías** de permisos existentes

```bash
python manage.py setup_permisos_solicitudes
```

**Salida esperada**:
```
Iniciando configuración de permisos...
[+] Creado: Gestión: Puede aprobar solicitudes pendientes de aprobación -> GESTION
[*] Actualizado: Puede ver todas las solicitudes -> GESTION
...
============================================================
[OK] Permisos creados: 13
[OK] Permisos actualizados: 1
============================================================
[OK] Configuracion de permisos completada exitosamente!
```

## Uso en Vistas

El módulo de solicitudes incluye mixins especializados para verificación de permisos:

```python
from apps.solicitudes.mixins import (
    GestionSolicitudesPermissionMixin,
    AprobarSolicitudesPermissionMixin,
    CrearSolicitudArticulosPermissionMixin,
    MisSolicitudesPermissionMixin,
)

class SolicitudListView(GestionSolicitudesPermissionMixin, ListView):
    """Vista que requiere permisos de Gestión."""
    pass

class CrearSolicitudArticulosView(CrearSolicitudArticulosPermissionMixin, CreateView):
    """Vista que requiere permisos de Solicitud Artículos."""
    pass
```

## Estructura de Archivos

```
apps/solicitudes/
├── models.py                    # Modelos principales
├── models_permisos.py          # Modelo PermisoExtendido
├── permissions.py               # Helpers para consultar permisos
├── mixins.py                    # Mixins de verificación de permisos
├── views.py                     # Vistas con permisos aplicados
├── management/
│   └── commands/
│       └── setup_permisos_solicitudes.py  # Comando de setup
└── migrations/
    ├── 0005_reorganizar_permisos.py
    ├── 0006_actualizar_descripciones_permisos.py
    └── 0007_agregar_permiso_extendido.py
```

## Migraciones Aplicadas

1. **0005_reorganizar_permisos.py**: Reorganizó permisos personalizados con nombres en español
2. **0006_actualizar_descripciones_permisos.py**: Limpió descripciones eliminando prefijos de categoría
3. **0007_agregar_permiso_extendido.py**: Creó tabla `tba_solicitudes_permiso_extendido`

## Base de Datos

### Tabla: `tba_solicitudes_permiso_extendido`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `permiso_id` | FK → auth_permission | PK, relación OneToOne con Permission |
| `modulo` | VARCHAR(50) | Categoría del permiso (GESTION, SOLICITUD_ARTICULOS, etc.) |
| `descripcion_extendida` | TEXT | Descripción detallada del permiso |
| `orden` | INTEGER | Orden de visualización dentro del módulo |
| `destacado` | BOOLEAN | Si debe destacarse en la UI |
| `color` | VARCHAR(7) | Color hexadecimal para UI |
| `icono` | VARCHAR(50) | Clase de icono (ej: bi bi-gear-fill) |

### Consultas SQL de Ejemplo

```sql
-- Obtener todos los permisos de GESTIÓN ordenados
SELECT p.codename, p.name, pe.modulo, pe.orden
FROM auth_permission p
INNER JOIN tba_solicitudes_permiso_extendido pe ON p.id = pe.permiso_id
WHERE pe.modulo = 'GESTION'
ORDER BY pe.orden;

-- Obtener permisos destacados
SELECT p.codename, p.name, pe.get_modulo_display
FROM auth_permission p
INNER JOIN tba_solicitudes_permiso_extendido pe ON p.id = pe.permiso_id
WHERE pe.destacado = TRUE;
```

## Integración Completada con Sistema Centralizado

### Vistas Actualizadas

Se actualizaron las siguientes vistas en `apps/accounts/views.py`:

1. **`lista_permisos`** (línea 566):
   - Filtra permisos del sistema (add_, change_, delete_, view_)
   - Organiza permisos por APP → CATEGORIA
   - Usa `CategoriaPermiso` para obtener módulos
   - Agrupa permisos personalizados por categoría funcional

2. **`asignar_permisos_grupo`** (línea 445):
   - Organiza permisos por APP → CATEGORIA al asignar a roles
   - Facilita la selección basada en módulos funcionales

3. **`asignar_permisos_usuario`** (línea 549):
   - Organiza permisos por APP → CATEGORIA al asignar a usuarios
   - Muestra categorías para mejor comprensión

### Templates Actualizados

1. **`lista_permisos.html`**:
   - Nueva columna "Módulo" en la tabla
   - Organización por APP → CATEGORIA (en lugar de APP → MODEL)
   - Solo muestra permisos personalizados
   - Badge de categoría con color distintivo

2. **`asignar_permisos_grupo.html`**:
   - Acordeones organizados por APP
   - Sub-secciones por CATEGORIA dentro de cada app
   - Badge mostrando el módulo de cada permiso

3. **`asignar_permisos_usuario.html`**:
   - Acordeones organizados por APP
   - Sub-secciones por CATEGORIA dentro de cada app
   - Badge mostrando el módulo de cada permiso

### Funcionalidades Implementadas

- **Filtrado automático**: Los permisos del sistema (add_, change_, delete_, view_) se ocultan automáticamente
- **Categorización dinámica**: Si un permiso tiene `CategoriaPermiso`, se usa su módulo; si no, se usa el nombre del modelo
- **Visualización mejorada**: Badges de color para identificar rápidamente el módulo de cada permiso
- **Escalabilidad**: Cualquier app puede usar el mismo patrón agregando categorías a sus permisos

## Notas Importantes

- ✅ **Los permisos se gestionan desde el sistema centralizado**, no desde el módulo de solicitudes
- ✅ **No se crean URLs ni vistas de permisos en el módulo de solicitudes**
- ✅ **Los permisos están en la base de datos**, no en código JSON
- ✅ **Se reutilizan las tablas de Django** (`auth_permission`), solo se extienden con metadatos
- ✅ **El sistema es escalable** y puede aplicarse a otros módulos de la aplicación

## Soporte

Para más información sobre el sistema de permisos, consultar:
- Documentación de permisos: `apps/solicitudes/PERMISOS_README.md`
- Código fuente: `apps/solicitudes/permissions.py`
- Modelos: `apps/solicitudes/models_permisos.py`
