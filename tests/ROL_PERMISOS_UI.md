# Matriz de Roles UI Selenium

Este archivo define los usuarios de prueba Selenium por rol funcional, para evitar depender de `superuser` en flujos donde la aplicación usa permisos finos.

## Roles implementados

### `sel_solicitante`
- Módulo: `solicitudes`
- Permisos:
  - `solicitudes.view_solicitud`
  - `solicitudes.add_solicitud`
  - `solicitudes.ver_mis_solicitudes`
  - `solicitudes.crear_solicitud_articulos`
  - `solicitudes.ver_solicitudes_articulos`
  - `solicitudes.view_estadosolicitud`
  - `solicitudes.view_tiposolicitud`

### `sel_aprobador`
- Módulo: `solicitudes`
- Permisos:
  - `solicitudes.view_solicitud`
  - `solicitudes.gestionar_solicitudes`
  - `solicitudes.ver_todas_solicitudes`
  - `solicitudes.aprobar_solicitudes`
  - `solicitudes.rechazar_solicitudes`
  - `solicitudes.view_estadosolicitud`

### `sel_despachador`
- Módulo: `solicitudes`
- Permisos:
  - `solicitudes.view_solicitud`
  - `solicitudes.gestionar_solicitudes`
  - `solicitudes.ver_todas_solicitudes`
  - `solicitudes.despachar_solicitudes`
  - `solicitudes.view_estadosolicitud`

### `sel_bodeguero`
- Módulo: `bodega`
- Permisos:
  - `bodega.view_articulo`
  - `bodega.add_articulo`
  - `bodega.change_articulo`
  - `bodega.view_movimiento`
  - `bodega.add_movimiento`
  - `bodega.view_bodega`
  - `bodega.view_recepcionarticulo`
  - `bodega.add_recepcionarticulo`
  - `bodega.registrar_recepcion_articulo`
  - `bodega.ver_todas_recepciones_articulos`

### `sel_comprador`
- Módulo: `compras`
- Permisos:
  - `compras.view_ordencompra`
  - `compras.add_ordencompra`
  - `compras.change_ordencompra`
  - `compras.view_proveedor`
  - `compras.add_proveedor`
  - `compras.change_proveedor`
  - `compras.view_estadoordencompra`

### `sel_activos_operador`
- Módulo: `activos`
- Permisos:
  - `activos.view_activo`
  - `activos.add_activo`
  - `activos.change_activo`
  - `activos.view_movimientoactivo`
  - `activos.add_movimientoactivo`
  - `activos.view_categoriaactivo`
  - `activos.view_estadoactivo`
  - `activos.view_marca`
  - `activos.view_ubicacion`
  - `activos.view_proveniencia`
  - `activos.view_tipomovimientoactivo`

### `sel_bajas_operador`
- Módulo: `bajas_inventario`
- Permisos:
  - `bajas_inventario.view_bajainventario`
  - `bajas_inventario.add_bajainventario`
  - `bajas_inventario.change_bajainventario`
  - `bajas_inventario.view_motivobaja`
  - `bajas_inventario.add_motivobaja`

### `sel_admin_usuarios`
- Módulo: `accounts`
- Permisos:
  - `auth.view_user`
  - `auth.add_user`
  - `auth.change_user`
  - `auth.delete_user`
  - `auth.view_group`
  - `auth.add_group`
  - `auth.change_group`
  - `auth.delete_group`
  - `auth.view_permission`

## Criterio

- Cada prueba UI debe usar el usuario mínimo necesario para la ruta.
- `sel_admin` queda solo para escenarios donde se quiere cobertura de superusuario o debugging transversal.
- Si una ruta falla con el rol mínimo pero funciona con `superuser`, eso debe tratarse como señal de bug de permisos o navegación, no como solución de test.
