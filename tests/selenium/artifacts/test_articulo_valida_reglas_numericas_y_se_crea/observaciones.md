# Observaciones UI

Prueba: `test_articulo_valida_reglas_numericas_y_se_crea`

## Paso 1: Formulario crear articulo
- URL: `http://localhost:63911/bodega/articulos/crear/`
- Titulo: `Crear Artículo | Sistema`
- Screenshot: `01-20260310-203014-formulario-crear-articulo.png`
- Observacion: Se revisa alta de articulo con reglas numericas.

## Paso 2: Error por stock inconsistente
- URL: `http://localhost:63911/account/login/?next=/bodega/articulos/crear/`
- Titulo: `Iniciar sesión | Sistema`
- Screenshot: `02-20260310-203045-error-por-stock-inconsistente.png`
- Observacion: El stock maximo no debe ser menor al minimo.

