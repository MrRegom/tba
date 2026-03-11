# Observaciones UI

Prueba: `test_movimiento_bloquea_salida_con_stock_insuficiente`

## Paso 1: Salida invalida
- URL: `http://localhost:50602/bodega/movimientos/crear/`
- Titulo: `| Sistema`
- Screenshot: `01-20260310-212527-salida-invalida.png`
- Observacion: Se intenta registrar una salida por sobre el stock disponible.

## Paso 2: Stock insuficiente
- URL: `http://localhost:50602/bodega/movimientos/crear/`
- Titulo: `| Sistema`
- Screenshot: `02-20260310-212528-stock-insuficiente.png`
- Observacion: La vista debe advertir que la salida excede el disponible.

