# ChangeLog

## v2.61

- El `install.pdf` se reemplaza por `install_es.pdf` e `install_en.pdf`. La hoja vieja salia de exportar un Google Doc a mano y quedo congelada en el metodo manual: no menciona los instaladores que el ZIP trae desde hace varias versiones, y ademas daba el backup del `init.py` como `init.py.bak`, un nombre que los motores ya no usan: hoy guardan una copia numerada en `~/.nuke/LGA_init_backups/`. Las dos hojas se generan ahora desde una plantilla unica en el repo de release, con la version leida del `VERSION` del repo, asi que el texto comun deja de mantenerse por separado en cada producto. Se documenta tambien que en macOS el instalador va con `bash installer_mac.sh`: los `.sh` pierden el permiso de ejecucion dentro del `.zip` y `./installer_mac.sh` da `Permission denied`. [ ToolPack - Reemplazar install.pdf por las hojas en castellano e ingles ]
- El preset `EXR Publish DWAA` pasa a escribir siempre en `ACES - ACES2065-1` en vez de seguir el default del proyecto: el publish es el entregable de intercambio y no tiene que moverse si cambia el config. Los demas presets EXR siguen en default. [ ToolPack - Fijar ACES2065-1 en el preset EXR Publish ]

- La compresion DWAA de todos los presets EXR baja de nivel 60 a 45. [ ToolPack - Bajar el nivel DWAA a 45 ]

- Los presets de `Write Presets` con `colorspace = default` dejaban el Write en `default (ACES2065-1)` en vez del colorspace que el proyecto resuelve por default, que con un config ACES es `scene_linear (ACEScg)`. El script seteaba el knob legacy `colorspace` al string literal `"default"`, y eso lo marca como modificado, lo desincroniza de `ocioColorspace` y congela el label en el default viejo. Ahora, cuando el preset pide `default`, no se toca ningun knob de color: el Write queda con el default dinamico de Nuke, que se resuelve solo segun el OCIO config del proyecto y el file_type. Los presets con un colorspace explicito, incluido el camino `Output - Rec.709` con display/view, siguen igual. [ ToolPack - Respetar el colorspace default dinamico en Write Presets ]

## v2.60
- El instalador dejaba el `init.py` roto en cualquier equipo que tuviera sus `pluginAddPath` adentro de un bloque `if` —por ejemplo para discriminar por version de Nuke— y ademas reportaba exito. Al reordenar los paths se llevaba tambien las lineas indentadas, dejando el bloque sin cuerpo, y Nuke no arrancaba con un `IndentationError`. Ahora solo toca las lineas en columna 0 y respeta las indentadas donde estan. Suma ademas deduplicacion de paths repetidos, preservacion del BOM del archivo original y una validacion del resultado: si el `init.py` quedaria invalido, no lo modifica y aborta la instalacion. [ ToolPack - Corregir el manejo del init.py del instalador ]

## v2.59
- `Paths to Relative` calcula las rutas contra el Project Directory y no contra la carpeta del script. Nuke resuelve los relativos contra `root.project_directory`, no contra la ubicación del `.nk`: con ese knob vacío —que es el default— los resuelve contra el working directory del proceso y no encuentra nada, así que las rutas convertidas quedaban rotas aunque se vieran correctas. Ahora el ancla es el Project Directory evaluado cuando tiene valor, y cuando está vacío la ventana ofrece dejarlo en `[python {nuke.script_directory()}]`, la misma expresión del botón Script Directory de Project Settings, dentro del mismo bloque de undo. Si no hay rutas absolutas para convertir pero el knob sigue vacío, también se ofrece arreglarlo. [ ToolPack - Calcular relativos contra el Project Directory ]

- Nueva tool `Paths to Relative` en la sección READ n WRITE: pasa a rutas relativas al directorio del script las rutas absolutas de los nodos que apuntan a archivos (Read, Write, DeepRead, ReadGeo, Precomp, Vectorfield, OCIOFileTransform), incluyendo el knob `proxy`. Si hay nodos seleccionados actúa solo sobre esos; si no, recorre todo el script entrando en los Groups pero no adentro de los Precomps, cuyos nodos internos vienen de otro `.nk`. Antes de escribir nada abre una tabla de preview con un checkbox por fila, la columna del Group que contiene cada nodo y marcas de color: verde convertible, amarillo cuando sube muchos niveles, rojo cuando la media está en otra unidad. Los knobs con expresiones TCL, como los Writes de Write Presets, nunca se tocan. El cambio va en un solo bloque de undo. [ ToolPack - Agregar Paths to Relative ]

## v2.58
- El ZIP del release deja de incluir `docs/`, `default/` y `Doc_Media/Originals`, que no cumplen ninguna funcion en una instalacion: `docs/` se lee en GitHub, `default/` son dos carpetas vacias y `Originals` son las fuentes de edicion de los GIF y SVG. El pack instalado pasa de 22,7 MB a 4,4 MB. [ ToolPack - Reducir el contenido del release ]

## v2.57
- `Duplicate Publish` deja elegir qué frames copiar cuando el rango del Read no coincide con lo que hay en disco. Antes avisaba y seguía siempre con el rango del disco, y el mensaje decía "Only the N frames found on disk will be copied" incluso cuando el disco tenía más frames que el Read, que es justo el caso donde la tool no puede decidir sola. Ahora la ventana ofrece Cancel, Copy read range y Copy disk range. `Copy read range` copia los frames que realmente existen dentro del rango del Read y avisa cuántos hay si faltan; si ese rango cae entero fuera de la secuencia, la opción no se ofrece. [ ToolPack - Elegir rango al duplicar publish ]

- Nueva tool `Duplicate Publish` en la sección READ n WRITE: duplica en disco la secuencia del Read seleccionado renombrándola con el número de versión del script actual, para poder re-renderizar solo un rango corto sin volver a procesar la secuencia completa. Antes eso se hacía a mano con copy/paste y rename desde el explorador. La tool avisa y pide confirmación cuando el basename de la secuencia no coincide con el del script, cuando el rango del Read difiere de los frames que hay en disco y cuando el destino ya tiene frames. El escaneo y la copia corren en threads aparte, con barra de progreso cancelable y sin bloquear la UI de Nuke. [ ToolPack - Agregar Duplicate Publish ]

- El instalador ordena `~/.nuke/init.py` de forma canónica en Windows y macOS: recolecta todos los bloques `pluginAddPath` de LGA, los reordena según el orden oficial (Layout, ToolPack-B, ToolPack, NodePack, OpenInNukeX, Defaults, CollectedTools), elimina duplicados y deja intactos los paths ajenos. Antes cada plataforma resolvía el orden de una manera distinta y macOS simplemente agregaba al final. [ ToolPack - Unificar el orden del init.py ]

- El startup del pack queda aislado de Hiero y Nuke Studio: `menu.py` pasa a ser un wrapper mínimo que consulta los flags oficiales de host antes de importar `LGA_ToolPack_menu.py`, mientras `init.py` aplica el mismo guard antes de agregar `py/` o registrar el callback del Viewer. La configuración global de `~/.nuke/init.py` puede conservar así su instalación simple basada únicamente en `pluginAddPath`. [ ToolPack - Evitar carga en Hiero y Nuke Studio ]

- Se incorpora `VERSION` como fuente única de la versión publicada y el menú obtiene desde allí su label de documentación. Se agregan reglas de desarrollo espejadas, se formaliza el changelog pendiente sin bumps durante el trabajo normal y se reserva la promoción de versión para el generador manual de `LGA_Release`. [ ToolPack - Unificar reglas, changelog y versión publicada ]

## v2.56
- Se actualiza la copia vendorizada de `certifi` en `py/shotgun_api3/lib` a `2026.6.17` para cerrar la alerta de seguridad de GitHub por certificados raiz retirados. [ ToolPack - Actualizar certifi vendorizado ]

## v2.54
- Se agrega `LGA_tooltip_helper.py` y su documentacion `LGA_tooltip_helper.md` en `py/`, con standard de tooltips para la repo: fondo `#1e1e1e`, texto primario `#cccccc`, texto secundario `#888888`, padding `12px`, esquinas redondeadas y sin borde.
- Se agrega tooltip custom inmediato en los thumbnails de `LGA_viewer_SnapShot_Gallery`, usando popup propio con fondo redondeado pintado por Qt para evitar bordes/padding nativos de `QToolTip`.
- Se actualiza el comportamiento de thumbnails en la galeria de snapshots: click simple abre el JPG en el viewer default del usuario.
- Se agrega `Shift + click` sobre thumbnails para revelar el archivo en el explorador del sistema (`Show in Explorer` en Windows, `Show in Finder` en macOS y file manager en Linux).
- Thumb size persistente
- Create roto con regla para dissolve

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
