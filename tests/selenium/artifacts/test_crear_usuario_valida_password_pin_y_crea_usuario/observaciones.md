# Observaciones UI

Prueba: `test_crear_usuario_valida_password_pin_y_crea_usuario`

## Paso 1: Formulario crear usuario
- URL: `http://localhost:57997/administracion/usuarios/crear/`
- Titulo: `Crear Usuario | Sistema`
- Screenshot: `01-20260310-202725-formulario-crear-usuario.png`
- Observacion: Se prueban password, PIN numerico y alta completa.

## Paso 2: Error por PIN invalido
- URL: `http://localhost:57997/administracion/usuarios/crear/?`
- Titulo: `Crear Usuario | Sistema`
- Screenshot: `02-20260310-202734-error-por-pin-invalido.png`
- Observacion: La validacion debe rechazar caracteres no numericos.

## Paso 3: Password no coincide
- URL: `http://localhost:57997/account/login/?next=/administracion/usuarios/crear/`
- Titulo: `Iniciar sesión | Sistema`
- Screenshot: `03-20260310-202744-password-no-coincide.png`
- Observacion: La validacion de servidor debe informar conflicto entre contrasenas.

