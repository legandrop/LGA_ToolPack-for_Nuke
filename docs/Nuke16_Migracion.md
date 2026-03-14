> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Plan de migración Nuke 15 → Nuke 16 (PySide2 → PySide6)

## Estrategia
- Capa de compatibilidad de imports (`LGA_QtAdapter_ToolPack.py`) con funciones helper avanzadas y fallback PySide6 → PySide2.
- Funciones helper automatizan cambios de API Qt5/Qt6: `horizontal_advance()`, `primary_screen_geometry()`, `set_layout_margin()`.
- Reemplazar APIs Qt5 deprecadas: `QDesktopWidget`, `QtOpenGL.QGLWidget`, `QAction` en `QtWidgets`, enums de `QSizePolicy` en instancias, `QSound`.
- Ajustar accesos a DAG: ya es `QWidget`, no OpenGL; usar `objectName` y `render()`.
- Mantener compatibilidad con Nuke 15 mediante `try/except` o helper único.

## Resultado de revisión en ESTE ToolPack
### Cambios funcionales (API Qt deprecada o mezcla de bindings)
- [x] `channel_hotbox.py` — ahora usa `LGA_QtAdapter_ToolPack` (sin mezcla PySide/PySide2).
- [x] `init.py` — timers via `LGA_QtAdapter_ToolPack.QtCore.QTimer`.
- [x] `menu.py` — timers via `LGA_QtAdapter_ToolPack.QtCore.QTimer`.
- [x] `LGA_ToolPack_settings.py` — geometría via `LGA_QtAdapter_ToolPack.primary_screen_geometry()`.
- [x] `LGA_Write_Presets.py` — geometría via `LGA_QtAdapter_ToolPack.primary_screen_geometry()`.
- [x] `LGA_Write_RenderComplete.py` — audio: PySide6 usa `QMediaPlayer+QAudioOutput`, PySide2 mantiene `QSound`.

- [x] `LGA_QtAdapter_ToolPack.py` (funciones helper avanzadas: `horizontal_advance`, `primary_screen_geometry`, `set_layout_margin`).
- [x] `LGA_viewer_SnapShot.py` — ahora via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_viewer_SnapShot_Buttons.py` — ahora via `LGA_QtAdapter_ToolPack`, limpieza por `objectName`, detección slider robusta (N15/16).
- [x] `LGA_viewer_SnapShot_Gallery.py` — imports via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_mediaPathReplacer.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_Write_Presets_Check.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_RnW_ColorSpace_Favs.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_disable_A_B.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_CopyCat_Cleaner.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_MediaManager.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_MediaManager_utils.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_MediaManager_settings.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_MediaManager_FileScanner.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_build_Grade.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_build_Merge.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_build_Roto.py` — via `LGA_QtAdapter_ToolPack`.
- [x] `LGA_build_iteration.py` — via `LGA_QtAdapter_ToolPack`.

Notas rápidas:
- Geometría de pantalla: usar `LGA_QtAdapter_ToolPack.primary_screen_geometry(pos)` (maneja automáticamente QDesktopWidget vs QGuiApplication).
- `QSound` → `QMediaPlayer` + `QAudioOutput` en PySide6.
- `QFontMetrics.width` → usar `LGA_QtAdapter_ToolPack.horizontal_advance(metrics, text)` (compatible Qt5/Qt6).
- Márgenes de layout: usar `LGA_QtAdapter_ToolPack.set_layout_margin(layout, margin)` (compatible Qt5/Qt6).
- Viewers/hotbox/init/menu: unificar imports con `LGA_QtAdapter_ToolPack` para evitar mezcla PySide/PySide2.
- Resto de scripts: solo envolver imports con `LGA_QtAdapter_ToolPack` (QtWidgets/QtCore/QtGui); APIs Qt5 deprecadas manejadas por funciones helper.

## Pasos sugeridos
1) `LGA_QtAdapter_ToolPack.py` ya incluye funciones helper avanzadas (`horizontal_advance`, `primary_screen_geometry`, `set_layout_margin`) con fallback PySide6 → PySide2.
2) Cambiar imports en todos los scripts para usar `LGA_QtAdapter_ToolPack` en lugar de imports directos de PySide.
3) Para geometría de pantalla usar `LGA_QtAdapter_ToolPack.primary_screen_geometry(pos)` (maneja automáticamente QDesktopWidget vs QGuiApplication).
4) Para ancho de texto usar `LGA_QtAdapter_ToolPack.horizontal_advance(metrics, text)` (compatible Qt5/Qt6 automáticamente).
5) Para márgenes de layout usar `LGA_QtAdapter_ToolPack.set_layout_margin(layout, margin)` (compatible Qt5/Qt6 automáticamente).
6) Sustituir `QtOpenGL.QGLWidget` en `scale_widget.py`; si no se usa GL real, eliminar dependencia y usar DAG como `QWidget`.
7) Asegurar `QAction` se importe desde `QtGui` en PySide6 (ya manejado por LGA_QtAdapter_ToolPack).
8) Si aparece audio con `QSound`, migrar a `QMediaPlayer + QAudioOutput`.
9) Probar manualmente en Nuke 15 y 16: paneles, backdrops, zoom middle-click, selectNodes, Km NodeGraph, captura/render de DAG.

## Cambios ya aplicados en el otro ToolPack (referencia)
- `LGA_QtAdapter_ToolPack.py` agregado con fallback PySide6 → PySide2.
- `LGA_StickyNote.py` v1.92: usa `LGA_QtAdapter_ToolPack`, tooltips se cierran en cerrar/OK/Cancel, debug off, auto-run comentado.
- `LGA_NodeLabel.py` v0.83: usa `LGA_QtAdapter_ToolPack`, tooltips con parent y cierre garantizado en OK/Cancel/cierre, namespace/version actualizado.
- `LGA_StickyNote_Utils.py` v1.01: usa `LGA_QtAdapter_ToolPack` para PySide6/2.
- `LGA_backdrop.py` v0.81: usa `LGA_QtAdapter_ToolPack`, tooltips con parent/cierre en OK/Cancel/closeEvent, `QDesktopWidget` → `QGuiApplication.primaryScreen().availableGeometry()`, namespace/version actualizado.
- `LGA_BD_knobs.py`: imports con `LGA_QtAdapter_ToolPack`.
- `LGA_BD_fit.py`: imports con `LGA_QtAdapter_ToolPack` (`QFont/QFontMetrics`).
- `LGA_BD_callbacks.py`: callback inline prueba PySide6 y luego PySide2 en `QFont/QFontMetrics`.
- `scale_widget.py`: usa `LGA_QtAdapter_ToolPack`, DAG `QWidget` (sin QtOpenGL), wheel reenviado al DAG.
- `distributeNodes.py` y `dag.py`: usan `LGA_QtAdapter_ToolPack`.
- `LGA_zoom.py`: usa `LGA_QtAdapter_ToolPack` y alias para mantener API original.
- `LGA_selectNodes.py.panel`: usa `LGA_QtAdapter_ToolPack`.
- `LGA_scriptChecker.py`: usa `LGA_QtAdapter_ToolPack`.
- `Km_NodeGraphEN/PysideImport.py`: usa `LGA_QtAdapter_ToolPack` y exporta nombres.
- `Km_NodeGraphEN/Km_NodeGraph_Easy_Navigate.py`: usa `LGA_QtAdapter_ToolPack`, `QDesktopWidget` → `QGuiApplication.primaryScreen()`.

## Nota de problema y solución (imports LGA_backdrop en Nuke)
- Síntoma: `ImportError: attempted relative import with no known parent package` al iniciar Nuke y crash.
- Causa: Nuke carga módulos sin contexto de paquete; imports relativos fallan.
- Fix:
  1) Asegurar `LGA_backdrop` está en `sys.path` y limpiar `__pycache__`.
  2) Usar imports planos dentro de `LGA_backdrop.py` (`import LGA_BD_knobs`, etc.) y exponer `autoBackdrop` en `__init__.py`.
  3) En `position_window_relative_to_cursor`, usar `screenAt(cursor_pos) or primaryScreen()` y `availableGeometry()` sin argumentos (Qt6).

## Notas sobre tooltips persistentes (NodeLabel/StickyNote)
## Incidencias encontradas hoy (Nuke 16, Viewer SnapShot)
- PySide2 no disponible en N16 → `LGA_viewer_SnapShot.py` y Buttons migrados a `LGA_QtAdapter_ToolPack`.
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
