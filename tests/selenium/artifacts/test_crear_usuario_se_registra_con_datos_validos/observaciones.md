# Observaciones UI

Prueba: `test_crear_usuario_se_registra_con_datos_validos`

## Paso 1: Alta de usuario
- URL: `http://localhost:63914/administracion/usuarios/crear/`
- Titulo: `Crear Usuario | Sistema`
- Screenshot: `01-20260310-203114-alta-de-usuario.png`
- Observacion: Se recorre el flujo exitoso con credenciales, PIN y datos personales.

## Paso 2: Usuario creado
- URL: `http://localhost:63914/account/login/?next=/administracion/usuarios/crear/`
- Titulo: `Iniciar sesión | Sistema`
- Screenshot: `02-20260310-203124-usuario-creado.png`
- Observacion: Debe quedar persistido y redirigir a una vista de detalle o exito.

