# Observaciones UI

Prueba: `test_aprobacion_y_rechazo_muestran_errores_por_campo`

## Paso 1: Solicitud base creada
- URL: `http://localhost:65321/solicitudes/47/`
- Titulo: `Solicitud SOL-00000001 | Sistema`
- Screenshot: `01-20260310-224602-solicitud-base-creada.png`
- Observacion: Se usara la solicitud SOL-00000001 para verificar errores de aprobacion y rechazo.

## Paso 2: Cantidad aprobada sobre el maximo
- URL: `http://localhost:65321/solicitudes/47/aprobar/`
- Titulo: `Aprobar Solicitud SOL-00000001 | Sistema`
- Screenshot: `02-20260310-224607-cantidad-aprobada-sobre-el-maximo.png`
- Observacion: La validacion cliente debe advertir que no se puede aprobar mas de lo solicitado.

## Paso 3: Motivo de rechazo obligatorio
- URL: `http://localhost:65321/solicitudes/47/rechazar/`
- Titulo: `Rechazar Solicitud SOL-00000001 | Sistema`
- Screenshot: `03-20260310-224615-motivo-de-rechazo-obligatorio.png`
- Observacion: El campo de rechazo debe informar claramente que es requerido.

