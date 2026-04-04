# Selenium Visual

Pruebas UI pensadas para ser observadas, no solo para validar.

## Ejecucion lenta y visible

```powershell
$env:SELENIUM_HEADLESS="false"
$env:SELENIUM_PAUSE="1.5"
$env:SELENIUM_OBSERVE="true"
.\.venv\Scripts\python.exe -m pytest tests/selenium/test_ui_solicitudes_detallado.py -m selenium -v
```

## Evidencia generada

- Screenshots por paso: `tests/selenium/artifacts/<nombre_test>/`
- Bitacora de observaciones: `tests/selenium/artifacts/<nombre_test>/observaciones.md`

## Variables utiles

- `SELENIUM_HEADLESS=false`: abre Chrome visible.
- `SELENIUM_PAUSE=2`: pausa entre acciones para revisar visualmente.
- `SELENIUM_OBSERVE=true`: guarda capturas y notas automaticas.
- `SELENIUM_ARTIFACTS_DIR=...`: cambia la carpeta de evidencia.

## Suite detallada actual

- `test_creacion_muestra_validaciones_cliente_y_servidor`
- `test_aprobacion_y_rechazo_muestran_errores_por_campo`
- `test_flujo_visual_desde_creacion_hasta_despacho`
