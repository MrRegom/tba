# Observaciones UI

Prueba: `test_activo_se_crea_y_genera_codigo`

## Paso 1: Formulario crear activo
- URL: `http://localhost:65062/activos/crear/`
- Titulo: `Crear Activo | Sistema`
- Screenshot: `01-20260310-213231-formulario-crear-activo.png`
- Observacion: Se valida alta individual y generacion automatica de codigo.

## Paso 2: Activo creado
- URL: `http://localhost:65062/account/login/?next=/activos/crear/`
- Titulo: `Iniciar sesión | Sistema`
- Screenshot: `02-20260310-213259-activo-creado.png`
- Observacion: Se espera persistencia correcta y codigo autogenerado.

