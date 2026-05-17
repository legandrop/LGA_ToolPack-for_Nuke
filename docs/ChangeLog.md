# ChangeLog

## v2.521
- Se rehace la UI de `LGA_mediaPathReplacer` a una tabla de tres columnas (`Node`, `Type`, `Paths`) con filas dobles por item (`Original` y `New`) para mejorar lectura de rutas largas.
- Se incorporan dos etapas de `Search & Replace` en líneas separadas (S&R 1 y S&R 2), cada una con botón de swap y checkbox `Case Sensitive`, más columnas de `Prefix` y `Suffix`.
- Se reemplaza el borrado de presets por botón con implementación de papelera en el dropdown (ícono normal/hover), siguiendo el patrón de presets del panel de Import Shots.
- Se agregan SVG locales en `py/icons` para `trash`, `trash_hover`, `node_read` y `node_write`, usados por el combo de presets y la columna `Node`.
- Se mantiene la ejecución directa del script (`__main__`) para que al pegar el archivo completo en Script Editor se abra la ventana automáticamente.
- Se ajusta la tabla para lectura de paths largos: headers alineados a izquierda, grid fino gris más visible, fondo uniforme en columna `Node`, labels `Original`/`Renamed` alineados y aumento de tamaño en íconos Read/Write.
- Se corrige el resaltado por etapas para que `Search & Replace 1`, `Search & Replace 2`, `Prefix` y `Suffix` pinten sectores específicos con colores distintos tanto en `Original` como en `Renamed`, en lugar de colorear toda la ruta.

[mediapathreplacer-ui-copy-importshots]
