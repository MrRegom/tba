# Observaciones UI

Prueba: `test_orden_compra_valida_fecha_y_se_crea`

## Paso 1: Formulario orden de compra
- URL: `http://localhost:50602/compras/ordenes/crear/`
- Titulo: `Nueva Orden de Compra | Sistema`
- Screenshot: `01-20260310-213202-formulario-orden-de-compra.png`
- Observacion: Se prueba fecha invalida y luego creacion valida.

## Paso 2: Fecha de entrega invalida
- URL: `http://localhost:50602/compras/ordenes/crear/`
- Titulo: `Nueva Orden de Compra | Sistema`
- Screenshot: `02-20260310-213220-fecha-de-entrega-invalida.png`
- Observacion: La fecha esperada no puede ser anterior a la fecha de orden.

## Paso 3: Orden creada
- URL: `http://localhost:50602/account/login/?next=/compras/ordenes/crear/`
- Titulo: `Iniciar sesión | Sistema`
- Screenshot: `03-20260310-213240-orden-creada.png`
- Observacion: Debe crearse una orden con datos minimos validos.

