# Plan de Testing Visual y Funcional

## Criterio de cobertura

Cada modulo debe cubrir 3 capas:

1. Validacion individual de campos.
2. Regla de negocio y permisos por rol.
3. Flujo completo con transiciones visibles.

## Prioridad alta

### Solicitudes

- Crear solicitud de articulos.
- Crear solicitud de bienes.
- Validar campos obligatorios.
- Validar reglas numericas: mayor a cero, no negativo, no exceder maximo.
- Validar rechazo con motivo obligatorio.
- Flujo completo: crear -> aprobar -> despachar.
- Flujo alterno: crear -> rechazar.
- Flujo alterno: crear -> enviar a compras.
- Validar historial y mensajes visuales por paso.

### Bodega

- Crear articulo.
- Editar articulo.
- Validar stock minimo, maximo y numericos.
- Registrar movimiento de entrada.
- Registrar movimiento de salida.
- Validar bloqueo por stock insuficiente.
- Recepcionar articulos con y sin orden de compra.

### Compras

- Crear proveedor con validaciones de RUT/campos requeridos.
- Crear orden de compra.
- Agregar articulos y activos.
- Validar cantidades y valores numericos.
- Aprobar y recepcionar orden.

### Activos

- Crear activo.
- Validar codigo, numero de serie y campos unicos.
- Cambiar estado.
- Trasladar activo.
- Validar restricciones por estado.

### Bajas de inventario

- Registrar baja.
- Validar motivo obligatorio.
- Validar que no permita baja duplicada o inconsistente.

### Administracion y permisos

- Acceso por rol.
- Bloqueo de vistas sin permiso.
- Navegacion visible por menus.
- CRUD de usuario con validaciones.

## Evidencia por escenario

Cada prueba visual debe dejar:

- screenshot inicial
- screenshot de accion
- screenshot de validacion o error
- screenshot final de exito o bloqueo
- observacion en markdown con lo visto

## Convencion sugerida

- `tests/selenium/test_ui_<modulo>_detallado.py`
- `tests/selenium/pages/<modulo>_page.py`
- `tests/selenium/artifacts/` para evidencia

## Comando recomendado

```powershell
$env:SELENIUM_HEADLESS="false"
$env:SELENIUM_PAUSE="1.5"
$env:SELENIUM_OBSERVE="true"
.\.venv\Scripts\python.exe -m pytest tests/selenium -m selenium -v
```
