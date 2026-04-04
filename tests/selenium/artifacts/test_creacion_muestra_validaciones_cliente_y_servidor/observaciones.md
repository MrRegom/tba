# Observaciones UI

Prueba: `test_creacion_muestra_validaciones_cliente_y_servidor`

## Paso 1: Formulario inicial
- URL: `http://localhost:65321/solicitudes/articulos/crear/`
- Titulo: `Crear Solicitud de Artículos | Sistema`
- Screenshot: `01-20260310-224304-formulario-inicial.png`
- Observacion: Se verifica la presencia de campos clave y el estado vacio antes de agregar articulos.

## Paso 2: Advertencia por detalle faltante
- URL: `http://localhost:65321/solicitudes/articulos/crear/`
- Titulo: `Crear Solicitud de Artículos | Sistema`
- Screenshot: `02-20260310-224337-advertencia-por-detalle-faltante.png`
- Observacion: El frontend debe bloquear el envio cuando no se agrega ningun articulo.

## Paso 3: Articulo agregado con cantidad invalida
- URL: `http://localhost:65321/solicitudes/articulos/crear/`
- Titulo: `Crear Solicitud de Artículos | Sistema`
- Screenshot: `03-20260310-224353-articulo-agregado-con-cantidad-invalida.png`
- Observacion: Se espera un bloqueo visual porque la cantidad no puede ser cero.

## Paso 4: Error de negocio en backend
- URL: `http://localhost:65321/solicitudes/articulos/crear/`
- Titulo: `Crear Solicitud de Artículos | Sistema`
- Screenshot: `04-20260310-224448-error-de-negocio-en-backend.png`
- Observacion: La fecha requerida en el pasado debe dejar feedback claro en el formulario.

