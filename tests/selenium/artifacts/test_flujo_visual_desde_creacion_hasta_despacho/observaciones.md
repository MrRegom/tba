# Observaciones UI

Prueba: `test_flujo_visual_desde_creacion_hasta_despacho`

## Paso 1: Antes de crear la solicitud
- URL: `http://localhost:65321/solicitudes/articulos/crear/`
- Titulo: `Crear Solicitud de Artículos | Sistema`
- Screenshot: `01-20260310-224719-antes-de-crear-la-solicitud.png`
- Observacion: Se completan datos generales, estructura organizacional y detalle del articulo.

## Paso 2: Solicitud creada
- URL: `http://localhost:65321/solicitudes/48/`
- Titulo: `Solicitud SOL-00000001 | Sistema`
- Screenshot: `02-20260310-224722-solicitud-creada.png`
- Observacion: Se espera estado Pendiente y visibilidad del historial de creacion para SOL-00000001.

## Paso 3: Formulario de aprobacion
- URL: `http://localhost:65321/solicitudes/48/aprobar/`
- Titulo: `Aprobar Solicitud SOL-00000001 | Sistema`
- Screenshot: `03-20260310-224730-formulario-de-aprobacion.png`
- Observacion: Se reduce la cantidad aprobada para validar regla de negocio y trazabilidad.

## Paso 4: Solicitud aprobada
- URL: `http://localhost:65321/solicitudes/48/`
- Titulo: `Solicitud SOL-00000001 | Sistema`
- Screenshot: `04-20260310-224734-solicitud-aprobada.png`
- Observacion: La pagina de detalle debe mostrar aprobador, notas y el nuevo estado aprobado.

## Paso 5: Formulario de despacho
- URL: `http://localhost:65321/solicitudes/48/despachar/`
- Titulo: `Despachar Solicitud SOL-00000001 | Sistema`
- Screenshot: `05-20260310-224741-formulario-de-despacho.png`
- Observacion: Se despacha exactamente la cantidad aprobada para cerrar el flujo operativo.

## Paso 6: Solicitud lista para despacho
- URL: `http://localhost:65321/solicitudes/48/`
- Titulo: `Solicitud SOL-00000001 | Sistema`
- Screenshot: `06-20260310-224744-solicitud-lista-para-despacho.png`
- Observacion: El detalle debe quedar con despachador asignado, historial actualizado y estado para despachar.

