# Observaciones UI

Prueba: `test_crear_usuario_rechaza_pin_no_numerico`

## Paso 1: PIN invalido
- URL: `http://localhost:63914/administracion/usuarios/crear/`
- Titulo: `Crear Usuario | Sistema`
- Screenshot: `01-20260310-203035-pin-invalido.png`
- Observacion: Se fuerza un PIN con letras para comprobar el mensaje de validacion.

## Paso 2: Error de PIN
- URL: `http://localhost:63914/administracion/usuarios/crear/?`
- Titulo: `Crear Usuario | Sistema`
- Screenshot: `02-20260310-203045-error-de-pin.png`
- Observacion: La pagina debe seguir en el formulario e informar que el PIN solo admite numeros.

