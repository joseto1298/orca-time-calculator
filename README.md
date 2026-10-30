# Hora de Finalización — plugin para OrcaSlicer

Plugin que muestra la **hora actual** y, a partir de la estimación del laminado, **a qué hora terminará la impresión**. Lee el G-code de previsualización que OrcaSlicer deja en la caché temporal al laminar, así que no necesita configuración manual.

![Captura de la pestaña Tiempo](<Captura de pantalla.png>)

## Qué muestra

- Reloj en vivo con la hora actual.
- Hora y **fecha completa** de finalización (hora actual + duración estimada).
- Duración total estimada en un campo de **solo lectura**.
- Totales de **filamento (mm), peso (g) y coste**.
- Un tablero tipo **kanban** con una tarjeta por placa: número, nombre de la placa (el guardado en el proyecto; si no tiene, «Placa N»), hora/fecha de fin de esa placa y su duración estimada.
- Dos modos con botón: **Secuencial** (las placas se imprimen una tras otra y el fin acumula las duraciones) e **Independiente** (cada placa empieza en la hora actual; el fin usa su propia duración y el héroe muestra la placa más larga).

## Requisitos

- Una versión de OrcaSlicer con soporte de plugins Python (nightly o posterior a 2.4.2).
- Python 3.9 o superior (lo gestiona OrcaSlicer).

## Instalación

1. Abre OrcaSlicer.
2. Ve a **Plugins → Install local plugin**.
3. Selecciona `calculadora_tiempo.py` o el wheel `dist/hora_de_finalizacion-0.7.17-py3-none-any.whl`.
4. Acepta una vez el permiso de lectura para `%TEMP%\orcaslicer_model`; el plugin lo pide como carpeta completa para no preguntar sesión por sesión. El icono de la pestaña va incrustado en el `.py`; no hace falta copiar imágenes junto al plugin.

## Uso

1. Lamina la pieza con **Slice** (o exporta el G-code).
2. Abre la pestaña **Tiempo**.
3. Pulsa **Refrescar** si acabas de laminar.
4. Alterna **Secuencial** / **Independiente** en el héroe para ver los fines acumulados o por placa.
5. Si añades, borras o mueves placas, la pestaña te pedirá laminar de nuevo: los tiempos salen del G-code. Renombrar una placa se refleja al momento.
6. La pestaña lee las placas actuales del proyecto, aunque no hayas guardado, para no mostrar G-code antiguo de placas borradas.
7. Si la placa está vacía, muestra un aviso y no recorre `%TEMP%` ni vuelve a pedir permisos.
8. Si no encuentra G-code, guarda el aviso 30 segundos para no recorrer la caché en cada refresco.

La pestaña se actualiza sola al empezar y terminar un laminado, y cada segundo refresca el reloj y las horas de fin. Si el laminado falla o se cancela, se limpian los datos anteriores en lugar de mostrar una estimación obsoleta.

## Cómo funciona

- Al laminar, OrcaSlicer escribe el G-code de previsualización en:
  `%TEMP%\orcaslicer_model\<Día>\<HH_MM_SS>#<pid>#<id>\Metadata\.<pid>.<n>.gcode`
- Al laminar, el plugin captura las rutas exactas de los `.gcode` exportados y lee solo esos archivos, sin listar carpetas ni recorrer `%TEMP%`. Los cruza con las placas actuales del proyecto (aunque no estén guardadas) para ignorar G-code antiguo.
- Si aún no ha visto un laminado, muestra un aviso; no recorre `%TEMP%` ni busca sesiones antiguas.
- Las estadísticas están al **final** del archivo, después de `; CONFIG_BLOCK_END`, por eso se lee el pie del G-code y no la cabecera.
- Los nombres de placa salen de `plater_name` en el proyecto actual (exportado aunque no esté guardado); si están vacíos, se usa «Placa N».
- El total es la suma de todas las placas. En **Secuencial** el fin principal usa el total y cada tarjeta el fin acumulado; en **Independiente** cada placa empieza ahora y el fin principal es la placa más larga.
- Los resultados se cachean por archivo y fecha de modificación; no se recorre la caché general.

Formatos de tiempo reconocidos: `; total estimated time:`, `; model printing time:`, `; estimated printing time (normal mode) =`, `; TIME: <seg>`, `; print time:`, además de `1:23:45` y `2d3h15m`. El filamento y el coste admiten varios extrusores separados por comas.

## Limitaciones

- Solo se consideran las placas presentes en la **última sesión de laminado**. Si laminas placa por placa en sesiones separadas, verás únicamente la última.
- Requiere haber laminado al menos una vez: sin G-code en la caché, la pestaña muestra "sin datos de laminado".
- La primera lectura de cada sesión de `%TEMP%` puede abrir diálogos de permisos de OrcaSlicer; es normal y solo hay que aceptarlos una vez. Los permisos son por ruta exacta: no se puede autorizar `%TEMP%` entero de antemano.

## Desarrollo

No hay suite de tests ni build. Para validar cambios:

```powershell
python -c "import ast; ast.parse(open('calculadora_tiempo.py', encoding='utf-8').read())"
python build_wheel.py
```

Para probar la lógica Python, crea un `orca` falso en `sys.modules` antes de importar el módulo (clases `PagesPluginCapabilityBase`, `LifecycleEvent`, `LifecycleEvtCode`, etc.). El JavaScript está embebido en la constante `PAGE`; extrae el bloque `<script>` y pruébalo con Node usando un DOM y un puente `orca` simulados (modos, reset, sin datos y recuperación).

Al modificar el plugin, **sube la versión** en el encabezado PEP 723 (`# version = "x.y.z"`) para que OrcaSlicer cargue la nueva build.

## Archivos

- `calculadora_tiempo.py` — plugin completo (metadatos, captura del G-code y pestaña de UI).
- `dist/hora_de_finalizacion-0.7.17-py3-none-any.whl` — paquete instalable con el plugin y el icono.
- `build_wheel.py` — genera el wheel a partir del `.py` y `3.png`.
- `Captura de pantalla.png` — captura de la pestaña Tiempo usada en este README.
- `AGENTS.md` — notas para asistentes/agentes que trabajen en el repositorio.

