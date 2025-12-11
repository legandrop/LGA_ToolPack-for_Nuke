# Plan de migración Nuke 15 → Nuke 16 (PySide2 → PySide6)

## Estrategia
- Capa de compatibilidad de imports (`qt_compat.py` o `qtpy`) con fallback PySide6 → PySide2.
- Reemplazar APIs Qt5 deprecadas: `QDesktopWidget`, `QtOpenGL.QGLWidget`, `QAction` en `QtWidgets`, enums de `QSizePolicy` en instancias, `QSound`.
- Ajustar accesos a DAG: ya es `QWidget`, no OpenGL; usar `objectName` y `render()`.
- Mantener compatibilidad con Nuke 15 mediante `try/except` o helper único.

## Resultado de revisión en ESTE ToolPack
### Cambios funcionales (API Qt deprecada o mezcla de bindings)
- [x] `channel_hotbox.py` — ahora usa `qt_compat` (sin mezcla PySide/PySide2).
- [x] `init.py` — timers via `qt_compat.QtCore.QTimer`.
- [x] `menu.py` — timers via `qt_compat.QtCore.QTimer`.
- [x] `LGA_ToolPack_settings.py` — `QDesktopWidget` → `QGuiApplication.primaryScreen().availableGeometry()`.
- [x] `LGA_Write_Presets.py` — `QDesktopWidget` → `screenAt/primaryScreen().availableGeometry()`.
- [x] `LGA_Write_RenderComplete.py` — audio: PySide6 usa `QMediaPlayer+QAudioOutput`, PySide2 mantiene `QSound`.

- [x] `qt_compat.py` (copiado, fallback PySide6→PySide2).
- [x] `LGA_viewer_SnapShot.py` — ahora via `qt_compat`.
- [x] `LGA_viewer_SnapShot_Buttons.py` — ahora via `qt_compat`, limpieza por `objectName`, detección slider robusta (N15/16).
- [x] `LGA_viewer_SnapShot_Gallery.py` — imports via `qt_compat`.
- [x] `LGA_mediaPathReplacer.py` — via `qt_compat`.
- [x] `LGA_Write_PathToText.py` — via `qt_compat`.
- [x] `LGA_Write_Presets_Check.py` — via `qt_compat`.
- [x] `LGA_RnW_ColorSpace_Favs.py` — via `qt_compat`.
- [x] `LGA_disable_A_B.py` — via `qt_compat`.
- [x] `LGA_CopyCat_Cleaner.py` — via `qt_compat`.
- [x] `LGA_MediaManager.py` — via `qt_compat`.
- [x] `LGA_MediaManager_utils.py` — via `qt_compat`.
- [x] `LGA_MediaManager_settings.py` — via `qt_compat`.
- [x] `LGA_MediaManager_FileScanner.py` — via `qt_compat`.
- [x] `LGA_build_Grade.py` — via `qt_compat`.
- [x] `LGA_build_Merge.py` — via `qt_compat`.
- [x] `LGA_build_Roto.py` — via `qt_compat`.
- [x] `LGA_build_iteration.py` — via `qt_compat`.

Notas rápidas:
- `QDesktopWidget` → `QGuiApplication.primaryScreen().availableGeometry()`; para posicionar relativo al cursor usar `screenAt(pos) or primaryScreen()`.
- `QSound` → `QMediaPlayer` + `QAudioOutput` en PySide6.
- Viewers/hotbox/init/menu: unificar imports con `qt_compat` para evitar mezcla PySide/PySide2.
- Resto de scripts: solo envolver imports con `qt_compat` (QtWidgets/QtCore/QtGui); no se detectaron APIs Qt5 deprecadas.

## Pasos sugeridos
1) Crear `qt_compat.py` que exporte `QtWidgets`, `QtGui`, `QtCore`, `QAction`, `QGuiApplication`, `PYSIDE_VER` con fallback PySide6 → PySide2.
2) Cambiar imports en todos los scripts de la lista para usar el helper.
3) Reemplazar `QDesktopWidget` por `QGuiApplication.primaryScreen().geometry()` o `.availableGeometry()`. Para coords relativas usar `screenAt(cursor_pos) or primaryScreen()`.
4) Sustituir `QtOpenGL.QGLWidget` en `scale_widget.py`; si no se usa GL real, eliminar dependencia y usar DAG como `QWidget`.
5) Asegurar `QAction` se importe desde `QtGui` en PySide6.
6) Si aparece audio con `QSound`, migrar a `QMediaPlayer + QAudioOutput`.
7) Probar manualmente en Nuke 15 y 16: paneles, backdrops, zoom middle-click, selectNodes, Km NodeGraph, captura/render de DAG.

## Cambios ya aplicados en el otro ToolPack (referencia)
- `qt_compat.py` agregado con fallback PySide6 → PySide2.
- `LGA_StickyNote.py` v1.92: usa `qt_compat`, tooltips se cierran en cerrar/OK/Cancel, debug off, auto-run comentado.
- `LGA_NodeLabel.py` v0.83: usa `qt_compat`, tooltips con parent y cierre garantizado en OK/Cancel/cierre, namespace/version actualizado.
- `LGA_StickyNote_Utils.py` v1.01: usa `qt_compat` para PySide6/2.
- `LGA_backdrop.py` v0.81: usa `qt_compat`, tooltips con parent/cierre en OK/Cancel/closeEvent, `QDesktopWidget` → `QGuiApplication.primaryScreen().availableGeometry()`, namespace/version actualizado.
- `LGA_BD_knobs.py`: imports con `qt_compat`.
- `LGA_BD_fit.py`: imports con `qt_compat` (`QFont/QFontMetrics`).
- `LGA_BD_callbacks.py`: callback inline prueba PySide6 y luego PySide2 en `QFont/QFontMetrics`.
- `scale_widget.py`: usa `qt_compat`, DAG `QWidget` (sin QtOpenGL), wheel reenviado al DAG.
- `distributeNodes.py` y `dag.py`: usan `qt_compat`.
- `LGA_zoom.py`: usa `qt_compat` y alias para mantener API original.
- `LGA_selectNodes.py.panel`: usa `qt_compat`.
- `LGA_scriptChecker.py`: usa `qt_compat`.
- `Km_NodeGraphEN/PysideImport.py`: usa `qt_compat` y exporta nombres.
- `Km_NodeGraphEN/Km_NodeGraph_Easy_Navigate.py`: usa `qt_compat`, `QDesktopWidget` → `QGuiApplication.primaryScreen()`.

## Nota de problema y solución (imports LGA_backdrop en Nuke)
- Síntoma: `ImportError: attempted relative import with no known parent package` al iniciar Nuke y crash.
- Causa: Nuke carga módulos sin contexto de paquete; imports relativos fallan.
- Fix:
  1) Asegurar `LGA_backdrop` está en `sys.path` y limpiar `__pycache__`.
  2) Usar imports planos dentro de `LGA_backdrop.py` (`import LGA_BD_knobs`, etc.) y exponer `autoBackdrop` en `__init__.py`.
  3) En `position_window_relative_to_cursor`, usar `screenAt(cursor_pos) or primaryScreen()` y `availableGeometry()` sin argumentos (Qt6).

## Notas sobre tooltips persistentes (NodeLabel/StickyNote)
## Incidencias encontradas hoy (Nuke 16, Viewer SnapShot)
- PySide2 no disponible en N16 → `LGA_viewer_SnapShot.py` y Buttons migrados a `qt_compat`.
- Botones duplicados en Viewer (Qt6) → limpiar instancias por `objectName` antes de insertar.
- Detección de frameslider fallaba (layouts/AAction) → BFS ignorando `QAction`/`QLayout` y detección por tooltip/objectName/clase o `QSlider`.
- `LGA_disable_A_B`: en PySide6 los eventos `QChildEvent` no tienen `MouseButtonPress`; se usa `QEvent.MouseButton*` y se valida `pos()` antes de usarlo.
- `LGA_mediaPathReplacer`: `QFontMetrics.width` no existe en Qt6; usar `horizontalAdvance` con fallback a `width`.
- MediaManager (N16): `QAction` solo en `QtGui` y `QThreadPool` en `QtCore`; evitar imports PySide2.

- Crear tooltip como `QLabel` con `parent=self`, flags `Qt.Tool | FramelessWindowHint | WindowStaysOnTopHint`, `WA_DeleteOnClose`, `WA_ShowWithoutActivating`.
- Conectar `destroyed` del diálogo a `hide_custom_tooltip_*`.
- Llamar a `hide_custom_tooltip_*` en OK/Cancel/closeEvent.
- En `hide_custom_tooltip_*`, llamar a `close()`, `deleteLater()`, `QToolTip.hideText()` y `QApplication.processEvents(...)`.

## Cómo cargar el ToolPack en Nuke
```python
import nuke
nuke.pluginAddPath("/Users/leg4/.nuke/LGA_ToolPack-Layout")
```
