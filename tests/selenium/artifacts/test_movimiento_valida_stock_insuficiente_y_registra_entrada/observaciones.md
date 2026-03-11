# Observaciones UI

Prueba: `test_movimiento_valida_stock_insuficiente_y_registra_entrada`

## Paso 1: Formulario movimiento
- URL: `http://localhost:64195/bodega/movimientos/crear/`
- Titulo: `| Sistema`
- Screenshot: `01-20260310-202158-formulario-movimiento.png`
- Observacion: Se prueba salida invalida y luego una entrada valida.

## Paso 2: Stock insuficiente
- URL: `http://localhost:64195/bodega/movimientos/crear/`
- Titulo: `| Sistema`
- Screenshot: `02-20260310-202201-stock-insuficiente.png`
- Observacion: La vista debe advertir que la salida excede el disponible.

## Paso 3: Movimiento registrado
- URL: `http://localhost:64195/bodega/movimientos/crear/`
- Titulo: `| Sistema`
- Screenshot: `03-20260310-202205-movimiento-registrado.png`
- Observacion: Se valida el alta correcta del movimiento de entrada.

