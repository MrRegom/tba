# Templates Desalineados Detectados

Este documento resume templates que hoy no están alineados con sus formularios o vistas, y que afectan tanto la operación manual como la automatización Selenium.

## 1. Bodega movimientos

### Archivo
- `templates/bodega/movimiento/form.html`

### Backend relacionado
- `apps/bodega/forms.py` `MovimientoForm`
- `apps/bodega/views.py` `MovimientoCreateView`

### Desalineación
- El template renderiza `operacion` con opciones hardcodeadas `ENTRADA` y `SALIDA`.
- El formulario espera `operacion` como `ModelChoiceField` sobre `Operacion`.
- La validación del formulario usa `operacion.tipo`, lo que solo existe si `operacion` es una instancia del modelo y no un string.

### Impacto
- El POST del template puede no coincidir con lo que el formulario espera.
- La automatización requiere inyectar valores o trabajar alrededor del template.
- Riesgo de errores silenciosos o validaciones inconsistentes en UI real.

### Medida sugerida
- Reemplazar el `select` manual por `{{ form.operacion }}`.
- Alinear `articulo`, `tipo`, `cantidad` y `motivo` también a `{{ form.campo }}` para evitar divergencias futuras.
- Si se necesita UI custom, iterar sobre `form.operacion.field.queryset`, no sobre strings fijos.

## 2. Bajas de inventario

### Archivo
- `templates/bajas_inventario/form_baja.html`

### Backend relacionado
- `apps/bajas_inventario/forms.py` `BajaInventarioForm`
- `apps/bajas_inventario/views.py` `BajaInventarioCreateView`

### Desalineación
- El template intenta renderizar campos como `bodega`, `descripcion` y `documento`.
- `BajaInventarioForm` define `activo`, `numero`, `fecha_baja`, `motivo`, `ubicacion`, `observaciones`.
- El template no refleja el contrato real del formulario actual.

### Impacto
- Puede mostrar campos vacíos o inexistentes.
- Selenium no puede cubrir el flujo de alta de baja con confianza.
- Alto riesgo de que usuarios vean una UI que no corresponde al modelo vigente.

### Medida sugerida
- Regenerar `form_baja.html` desde el formulario actual.
- Eliminar referencias a campos no presentes en `BajaInventarioForm`.
- Si el negocio requiere `bodega`, `descripcion` o `documento`, primero incorporarlos en modelo y formulario, y recién después en template.

## 3. Administración de usuarios

### Archivo
- `templates/account/gestion_usuarios/form_usuario.html`

### Backend relacionado
- `apps/accounts/forms.py` `UserCreateForm`
- `apps/accounts/views.py` `crear_usuario`

### Desalineación
- El template incluye referencias a `form.first_name` y `form.last_name`.
- `UserCreateForm` en creación trabaja principalmente con `username`, `email`, `password1`, `password2`, `pin`, `pin_confirmacion`, `nombres`, `apellido1`, `apellido2`, `sexo`, `fecha_nacimiento`, etc.
- No es una ruptura dura porque Django template tolera campos ausentes, pero sí es una señal de template mezclado entre create/update.

### Impacto
- Confusión de mantenimiento.
- Mayor dificultad para automatizar validaciones campo a campo.
- Riesgo de que una refactorización posterior deje secciones inconsistentes sin detectarlo.

### Medida sugerida
- Separar explícitamente template de creación y template de edición, o condicionar bloques con `if form.first_name`.
- Mantener en creación solo los campos reales del `UserCreateForm`.

## Prioridad recomendada

1. `templates/bodega/movimiento/form.html`
2. `templates/bajas_inventario/form_baja.html`
3. `templates/account/gestion_usuarios/form_usuario.html`
