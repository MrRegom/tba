# Observaciones UI

Prueba: `test_articulo_formulario_y_creacion_exitosa`

## Paso 1: Formulario crear articulo
- URL: `http://localhost:65061/bodega/articulos/crear/`
- Titulo: `Crear Artículo | Sistema`
- Screenshot: `01-20260310-213231-formulario-crear-articulo.png`
- Observacion: Se revisa la estructura del formulario y luego un alta valida.

## Paso 2: Articulo creado
- URL: `http://localhost:65061/account/login/?next=/bodega/articulos/crear/`
- Titulo: `Iniciar sesión | Sistema`
- Screenshot: `02-20260310-213300-articulo-creado.png`
- Observacion: Se espera persistencia correcta con parametros validos.

