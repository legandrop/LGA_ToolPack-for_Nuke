# ChangeLog

## v2.54
- Se agrega `LGA_tooltip_helper.py` y su documentacion `LGA_tooltip_helper.md` en `py/`, con standard de tooltips para la repo: fondo `#1e1e1e`, texto primario `#cccccc`, texto secundario `#888888`, padding `12px`, esquinas redondeadas y sin borde.
- Se agrega tooltip custom inmediato en los thumbnails de `LGA_viewer_SnapShot_Gallery`, usando popup propio con fondo redondeado pintado por Qt para evitar bordes/padding nativos de `QToolTip`.
- Se actualiza el comportamiento de thumbnails en la galeria de snapshots: click simple abre el JPG en el viewer default del usuario.
- Se agrega `Shift + click` sobre thumbnails para revelar el archivo en el explorador del sistema (`Show in Explorer` en Windows, `Show in Finder` en macOS y file manager en Linux).

## v2.53
- Se rehace la UI de `LGA_mediaPathReplacer` a una tabla de tres columnas (`Node`, `Type`, `Paths`) con filas dobles por item (`Original` y `New`) para mejorar lectura de rutas largas.
- Se incorporan dos etapas de `Search & Replace` en líneas separadas (S&R 1 y S&R 2), cada una con botón de swap y checkbox `Case Sensitive`.
- Se reemplaza el borrado de presets por botón con implementación de papelera en el dropdown (ícono normal/hover), siguiendo el patrón de presets del panel de Import Shots.
- Se agregan SVG locales en `py/icons` para `trash`, `trash_hover`, `node_read` y `node_write`, usados por el combo de presets y la columna `Node`.
- Se mantiene la ejecución directa del script (`__main__`) para que al pegar el archivo completo en Script Editor se abra la ventana automáticamente.
- Se ajusta la tabla para lectura de paths largos: headers alineados a izquierda, grid fino gris más visible, fondo uniforme en columna `Node`, labels `Original`/`Renamed` alineados y aumento de tamaño en íconos Read/Write.
- Se corrige el resaltado por etapas para que `Search & Replace 1` y `Search & Replace 2` pinten sectores específicos con colores distintos tanto en `Original` como en `Renamed`, en lugar de colorear toda la ruta.
- Se elimina completamente `Prefix/Suffix` (UI, lógica, presets y colores), se mueve `Search & Replace 2` a la segunda columna y se compacta la tercera columna (`Preset` + `Save Preset` + `Reset Values`) con botones angostos.
- Se aclaran separadores de secciones/columnas y se aplica estilo de scrollbar oscuro fino en la tabla para recuperar estética cercana al script original.
- Se fijan anchos de columnas de opciones para priorizar `Search & Replace 1/2` y achicar `Presets` (columna 3 más angosta y columnas 1/2 más amplias).
- Se amplía el ancho de la ventana en `+100px` y se redistribuye ese espacio extra en las dos primeras columnas de opciones.
- Se reduce en `10px` el espacio entre `Original`/`Renamed` y el path para mejorar compactación visual.
- Se reemplaza el guardado automático por nombre incremental y se copia el diálogo visual de “Guardar preset” del flujo original (popup frameless con campo de nombre y botones `Cancelar/Guardar`).

[mediapathreplacer-widths-savepreset-dialog]
