# Observaciones UI

Prueba: `test_movimiento_activo_requiere_estado_y_se_registra`

## Paso 1: Formulario movimiento de activo
- URL: `http://localhost:50767/activos/movimientos/registrar/`
- Titulo: `Registrar Movimiento de Activo | Sistema`
- Screenshot: `01-20260310-211525-formulario-movimiento-de-activo.png`
- Observacion: Se valida estado obligatorio y registro final.

## Paso 2: Error por estado faltante
- URL: `http://localhost:50767/activos/movimientos/registrar/`
- Titulo: `Registrar Movimiento de Activo | Sistema`
- Screenshot: `02-20260310-211526-error-por-estado-faltante.png`
- Observacion: La regla de negocio exige nuevo estado.

## Paso 3: Movimiento registrado
- URL: `http://localhost:50767/activos/movimientos/`
- Titulo: `Movimientos de Inventario | Sistema`
- Screenshot: `03-20260310-211559-movimiento-registrado.png`
- Observacion: Debe quedar trazabilidad del activo en la tabla de movimientos.

