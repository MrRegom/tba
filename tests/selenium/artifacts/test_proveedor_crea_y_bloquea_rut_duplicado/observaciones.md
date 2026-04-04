# Observaciones UI

Prueba: `test_proveedor_crea_y_bloquea_rut_duplicado`

## Paso 1: Formulario proveedor
- URL: `http://localhost:65060/compras/proveedores/crear/`
- Titulo: `| Sistema`
- Screenshot: `01-20260310-213232-formulario-proveedor.png`
- Observacion: Se crea proveedor y luego se prueba RUT duplicado.

## Paso 2: Proveedor creado
- URL: `http://localhost:65060/compras/proveedores/`
- Titulo: `| Sistema`
- Screenshot: `02-20260310-213235-proveedor-creado.png`
- Observacion: Debe quedar persistido con su RUT y razon social.

## Paso 3: RUT duplicado
- URL: `http://localhost:65060/compras/proveedores/crear/`
- Titulo: `| Sistema`
- Screenshot: `03-20260310-213237-rut-duplicado.png`
- Observacion: La UI debe mostrar validacion por unicidad.

