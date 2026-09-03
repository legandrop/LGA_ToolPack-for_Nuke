> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_mediaManager

La versión de la herramienta no se escribe acá: vive en el header de
`py/LGA_mediaManager.py` y los siete módulos la comparten. La ventana de
ajustes la muestra abajo a la izquierda, leyéndola de ese header.

## División de Responsabilidades

### Archivos Principales

#### `LGA_mediaManager.py`
- **Punto de entrada principal** del script
- Contiene la función `main()` que inicializa la aplicación
- Maneja los imports de todas las clases auxiliares
- Es también el header canónico de la versión de la tool

#### `LGA_MediaManager_FileScanner.py`
- **Clase FileScanner**: Interfaz principal de usuario
- Gestión de la tabla de archivos y su visualización
- Funciones de escaneo, filtrado y manipulación de archivos
- Operaciones de usuario: borrar, copiar, revelar y descargar archivos
- La barra de herramientas, las pastillas de estado, el buscador y el pie
- `SortHeaderView`: cabecera dibujada a mano, con el icono de orden después
  del texto y en color de acento en la columna ordenada
- `StatusCellDelegate`: la celda de Status, con su fondo a alto completo

#### `LGA_MediaManager_settings.py`
- **Clase SettingsWindow**: Ventana de configuración
- Una sola tabla de *locations*: cada fila es una carpeta con sus casillas de
  `Scan` y `Copy to`, su atajo y a qué carpeta real resuelve
- La primera fila es la **carpeta del shot**, una ruta explícita. Reemplazó al
  viejo `Folder scan depth`
- Tema de color y tamaño de letra de las tablas

#### `LGA_MediaManager_config.py`
- Dónde vive el `.ini` del usuario y qué tiene adentro
- Lectura, escritura atómica, valores de fábrica y migración del formato viejo
- No sabe nada de Nuke ni de Qt: se puede probar sin abrir el host

#### `LGA_MediaManager_paths.py`
- Qué significa una ruta relativa al `.nk` y con comodines
- Una mitad no toca disco —parsear, y decidir si una location incluye a otra—
  y otra sí, que expande el comodín contra el filesystem

#### `LGA_MediaManager_logging.py`
- El logger a `logs/LGA_mediaManager.log`

#### `LGA_MediaManager_download.py`
- Detecta si están instalados FileManager S3 y PipeSync studio, y dónde
- Arma el comando del CLI de FileManager S3 para el botón Download
- Sin Qt ni `nuke`: se prueba desde `tests/test_media_manager_download.py`

#### `LGA_MediaManager_utils.py`
- **Clases auxiliares compartidas**:
  - `ScannerWorker`: Worker en hilo separado para escaneo de archivos
  - `PathResolveWorker`: resuelve las rutas de la ventana de ajustes fuera del
    hilo principal
  - `PathDelegate`: dibuja el path coloreado de la tabla principal
  - `ReadCellDelegate`: la celda de la columna `Read`
  - `TransparentTextDelegate`: el resto de las celdas; respeta el color propio
    de la columna Status cuando la fila está seleccionada
  - `tinted_icon()`: los SVG de trazo teñidos, a la escala de la pantalla
  - `ProgressWindow`: la ventana de progreso de las cuatro operaciones, con su
    X que aborta. `StartupWindow` la extiende para el escaneo inicial
  - `BatchWorker` y sus dos hijos, `CopyWorker` y `DeleteWorker`: reciben un
    plan ya decidido y sólo tocan disco
  - `expand_sequence()`: convierte una fila de la tabla en sus archivos reales
  - `ScannerSignals` / `BatchSignals`: señales Qt para comunicación entre hilos

### Los índices de columna viven en `utils`

`COL_PATH`, `COL_READ`, `COL_STATUS`, `COL_FOLDER_DELETE`, `COL_SEQUENCE` y
`COL_NUM` están en `LGA_MediaManager_utils.py`, no en el FileScanner: los
delegados de ese módulo también los necesitan, y el FileScanner ya importa de
ahí. Al revés sería circular.

El `#` es la columna 5 y no la 0: se agrega al final y se mueve al primer lugar
**visual** con `moveSection()`. En Qt el orden visual es independiente del
lógico, así que se ve primera sin correr un solo índice.

## Tamaño de las ventanas

### Ventana principal

- **Ancho al abrir**: el justo para que entre el **path más largo** sin
  cortarse. Se mide con la letra del delegado —un punto más grande que la de
  la tabla— más el chrome de la celda.
- **Tope**: el 80% del ancho de la pantalla. Una ventana más ancha que el
  monitor no se puede ni mover.
- **Cuando el tope corta, el path no se recorta**: aparece un scroll
  horizontal. Poder llegar al final de un path es el punto de la herramienta.
- **Ese scroll es de la columna, no de la tabla.** `self.table` tiene la barra
  horizontal apagada y la columna del path ocupa siempre todo el sobrante del
  viewport (`fit_path_column()`); cuando el path más largo no entra, la
  diferencia la cubre `self.path_scroll`, que corre el dibujo con
  `PathDelegate.set_offset()`. Con el scroll de la tabla se iban de la vista
  también el número de fila, el `Read` y el `Status`, que son con lo que se
  decide qué hacer con la fila.
- **Los anchos de `Read` y `Status` se miden**, no son constantes: su
  contenido se conoce entero, así que un número a ojo sólo puede sobrar, y lo
  que sobra ahí se lo saca al path. `Status` se mide sobre los cuatro estados
  y no sobre los cargados, para que no cambie de ancho según lo que encuentre
  el escaneo.
- **Ninguna columna se arrastra a mano**: las cuatro van en `QHeaderView.Fixed`,
  que bloquea al usuario pero deja que `setColumnWidth` siga valiendo. Los
  anchos los decide la herramienta, así que un arrastre sólo podría desarmarlos.
- **`fit_path_column()` se llama desde el `eventFilter` del viewport, nunca
  desde el `resizeEvent` de la ventana.** Qt le entrega el resize al padre
  *antes* de reacomodar a los hijos, así que ahí el viewport todavía mide lo
  de antes: la columna se quedaba en su mínimo y sobraba media ventana vacía.
- **Ancho mínimo**: lo fija sólo la barra de herramientas, que es lo único
  incompresible. Las explicaciones de la leyenda del pie se esconden cuando no
  entran (`fit_footer_legend()`) en vez de cortarse a la mitad de una palabra.
- **Alto**: el del contenido, con el mismo tope del 80%, y recortado para
  cerrar en una fila entera.

### Ventana de ajustes

El mínimo sale del contenido —la suma de los mínimos de las columnas más los
márgenes— y no de un número escrito a mano. El área de filas se puede
comprimir hasta `TABLE_MIN_ROWS` y de ahí se scrollea.

Los anchos de columna son las tuplas `COL_*` de
`LGA_MediaManager_settings.py`, en el formato
`(ancho fijo o None, factor de estiramiento, ancho mínimo)`. El encabezado y
cada fila salen de esa misma lista: si no salieran del mismo lugar se
desalinean en cuanto una cambia.

Las tres de la derecha —`Scan`, `Copy to`, `Copy Shortcut`— miden lo que mide
su **encabezado**, que es lo más ancho que tienen adentro: el contenido son un
checkbox de 19 px y un par de teclas. Cualquier holgura sobre eso se lee como
un hueco entre columnas, no como aire. Título y contenido van los dos
centrados.

**Los títulos se sangran lo mismo que su contenido.** El encabezado pone un
`QLabel` pelado en cada columna y la fila pone widgets con estructura —una
ranura, el borde y el padding de un campo—, así que el texto de los dos no
arranca en el mismo lugar salvo que se lo corrija. Esa corrección son las
constantes `HEAD_INDENT_*`, escritas **como la suma de las medidas que la
producen** (`RANURA_WIDTH`, `RANURA_GAP`, `FIELD_BORDER`, `FIELD_PADDING_H`) y
no como un número calibrado a ojo: si cambia el padding del campo, la sangría
se mueve sola.

**La reserva de la barra de scroll se mide, no se deduce.** `_sync_head_margin()`
compara el ancho real del encabezado con el del viewport y lo llama el
`eventFilter` del viewport, que es cuando la barra aparece o se va. Deducirlo
de si el contenido pasa el alto máximo estuvo mal desde que la ventana se puede
achicar: con pocas filas y la ventana baja la barra aparece igual.

> **El encabezado y las filas tienen que tener los MISMOS items.** Son dos
> `QHBoxLayout` distintos que se alinean sólo porque recorren la misma lista de
> columnas. Un `QHBoxLayout` pone su espaciado *entre* items sin mirar cuánto
> mide cada uno, así que **agregar al encabezado un widget aunque sea de ancho
> 0 le roba un espaciado entero** (9 px) a las columnas elásticas — y como esas
> van primero, corre todo lo que viene después. Fue exactamente lo que pasó con
> el hueco que reservaba la barra de scroll. Eso se reserva con el
> `contentsMargins` derecho del layout del encabezado (lo escribe
> `_fit_table()`), nunca con un item.

Los anchos de `Read` y `Status` de la ventana principal tienen sus perillas de
ajuste fino en `COL_READ_EXTRA` y `COL_STATUS_EXTRA` (en
`LGA_MediaManager_FileScanner.py`): se suman a lo medido y son el único lugar
donde retocarlos.

**El ancho de las tarjetas de ayuda no es una constante**: lo mide
`_card_width()` sobre el renglón más largo del texto. El texto trae sus saltos
de línea escritos, así que una tarjeta más angosta parte un renglón y aparece
uno que nadie escribió.

Se mide con la **familia y el tamaño exactos con los que se dibuja**
(`UIStyle.font_family()` y `CARD_FONT_SIZE`), no con `cuerpo.font()`: el label
todavía no tiene la familia del pack cuando se lo crea, y su tamaño se lo pone
recién `apply_appearance()`. Medir con una fuente y dibujar con otra es como no
medir — falló así. Por lo mismo, `apply_ui_font()` se llama **antes** de
`_build()`: todo lo que se mida al armar tiene que medirse con la definitiva.

## Operaciones sobre varias filas: relink, copy to y delete

Las tres trabajan sobre **todas** las filas seleccionadas y siguen la misma
forma. Es la regla central de esta parte del código:

> **El hilo principal arma el PLAN. El worker sólo toca disco.**
>
> 1. En el hilo principal se lee la tabla, se expanden las secuencias a
>    archivos reales (`expand_sequence()`) y se hacen **todas** las preguntas
>    al usuario.
> 2. El worker recibe el plan ya decidido. No lee widgets, no abre carteles y
>    no llama a la API de `nuke`.

Eso no es una preferencia de estilo: las dos versiones anteriores lo violaban y
las dos tenían el mismo tipo de bug. El borrado leía `table.rowCount()` y
`table.item()` **desde el hilo worker** —comportamiento indefinido en Qt— y la
copia terminaba corriendo `shutil.copy` **en el hilo principal**, porque la
señal que la disparaba estaba conectada a un slot de un objeto que vive ahí.

| | worker | plan que recibe |
|---|---|---|
| relink | `RelinkSearchWorker` (uno por archivo, encadenados) | carpeta + patrones de búsqueda |
| copy to | `CopyWorker` (la tanda entera) | pares `(origen, destino)` ya resueltos |
| delete | `DeleteWorker` (la tanda entera) | rutas reales a mandar a la papelera |

**El relink va encadenado y las otras dos no**, y es deliberado: cada búsqueda
es un `os.walk` sobre la misma carpeta, así que lanzarlas juntas multiplica el
trabajo del disco por la cantidad de filas. La copia y el borrado no tienen ese
problema: recorren una lista ya resuelta.

**Sobreescritura: una pregunta por tanda.** `_plan_copy()` detecta todos los
conflictos antes de arrancar, y `copy_to()` pregunta una sola vez —*Overwrite
all* / *Skip them* / *Cancel*—. Preguntar dentro del worker obligaría a
bloquear el hilo esperando un diálogo; resolverlo antes lo evita del todo.

**Nada de Nuke desde un worker.** `nuke.allNodes`, `toNode` y `getValue` no son
thread-safe, y el síntoma con un script grande es un cuelgue duro de Nuke, no
un error. La regla es la misma que con la tabla: se saca una **foto** en el
hilo principal —`get_read_files()` devuelve datos, no nodos— y el worker
trabaja sobre eso. Envolver sólo el `allNodes()` y después leer los knobs de
los nodos devueltos afuera **no sirve de nada**, que es como estaba.

**`setAutoDelete(False)` en todos los workers.** El pool destruye el
`QRunnable` apenas `run()` retorna, pero el `finished` viaja en cola: hay un
hueco en el que el objeto C++ ya no está y la ventana todavía no se enteró. Un
clic en la X ahí adentro llama a `cancel()` sobre un objeto muerto.

**`closeEvent` corta todo.** Cerrar el Media Manager con una tanda en curso
cancela el batch, el relink y el escaneo. La `ProgressWindow` es hija de la
ventana principal, así que sin esto desaparecía y el worker seguía trabajando
sin nada que lo mostrara ni forma de pararlo.

**Cancelación.** Siempre una **bandera** mirada entre archivo y archivo, nunca
un kill de hilo: cortar a la mitad de un `shutil.copy` deja un archivo truncado
en el destino que después parece bueno. Al terminar, un solo cartel resume
hechos / sin hacer / errores.

**Borrado: siempre a la papelera.** Nunca permanente. Es la única red que le
queda al usuario si se equivocó de selección. Y las filas se sacan de la tabla
sólo si su archivo realmente dejó de estar: con una tanda cancelada a la mitad,
sacarlas todas mostraría como borrado lo que sigue en disco.

## Download: descarga desde Wasabi

El botón **Download** (Alt+D) es el *Download Clip* de HieroTools llevado a la
tabla, sin el modo *latest*: se le pide a FileManager S3 exactamente la ruta
que muestra la fila. Todo vive en `LGA_MediaManager_download.py`, que no
importa Qt ni `nuke`.

**El botón existe sólo si hay con qué descargar.** Al abrir el Media Manager
se busca —y sólo el hallazgo de FileManager S3 se cachea por sesión: si faltó,
la próxima apertura vuelve a mirar, para que instalarlo y reabrir alcance—:

1. **FileManager S3.** Si está, el botón descarga.
2. Si no está, **PipeSync studio** (no la edición Client). Si está, el botón
   igual aparece, pero lo único que hace es avisar que falta FileManager S3 y
   abrir PipeSync en su Tools tab (`--open-tab tools`), que es de donde se
   instala. Ojo: esa fila del Tools tab la ve sólo un usuario con algún rol
   en PipeSync; para uno sin rol, PipeSync avisa que el tab no está
   disponible y hay que pedir el instalador.
3. Sin ninguna de las dos, la barra queda como estaba.

**Cómo se detecta cada app** es lo mismo que hace el card de LGA Updates del
Tools tab de PipeSync (`UpdateProbe.cpp`), y lo que ya hacía
`LGA_OpenInShotPlayer.py` para el Shot Player, en este orden:

| fuente | qué se lee | cuándo sirve |
|---|---|---|
| registro compartido de LGA | `%APPDATA%/LGA/<App>.json` (`installPath`, `executable`, `version`) | la app se abrió alguna vez: lo escribe ella al arrancar |
| registro de desinstalación de Windows | `HKCU`/`HKLM`/`WOW6432Node\...\Uninstall\<AppId>_is1` (`DisplayVersion`, `InstallLocation`) | se instaló pero nunca se abrió |
| carpeta por defecto del instalador | `C:\Portable\LGA\FileManagerS3`, `/Applications/LGA FileManager S3.app`… | ninguno de los dos registros la tiene |

Ninguna fuente se cree sin mirar el disco: la carpeta tiene que tener el
`.exe` (o `Contents/MacOS` en el bundle) y no ser una salida `build`/`deploy`.
Una clave huérfana o un JSON viejo no cuentan.

**El plan.** Una fila que es secuencia (`nombre.####.exr[1001-1129]`) se pide
por su **carpeta** con `--download`; un archivo suelto, por su ruta con
`--download-file`. Todo va en **una sola invocación** del CLI, sin
`--context`: sin ese flag FileManager S3 usa el contexto de su edición
(`edition.ini`), que es lo que tiene que mandar en la máquina del artista. Las
rutas sin raíz `VFX-` se omiten y se avisan, porque el CLI las rechaza.

**Después del lanzamiento no se espera nada.** La descarga la muestra
FileManager S3 en su Activity tab; no hay watcher ni reconexión automática
como en Hiero. Cuando termina, Rescan actualiza la tabla.

**Alt+D era de Delete**, que pasa a **Alt+T**.

## Las ventanas de progreso

`ProgressWindow` (en `LGA_MediaManager_utils.py`) es la ventana de progreso de
las cuatro operaciones: escaneo, búsqueda del relink, copia y borrado.

### El escaneo inicial

`StartupWindow` (en `LGA_MediaManager_utils.py`) es la **primera** que ve el
usuario, y se abre **antes** que la principal: no hay ventana a quién
preguntarle el tema, así que lo lee del `.ini` con `_tema()`.

Es frameless con esquinas redondeadas — para eso necesita
`WA_TranslucentBackground` en la ventana y un `QFrame` interno que lleve el
color y el radio; sin la transparencia, Qt pinta el rectángulo por debajo y
las esquinas quedan cuadradas igual.

Al no tener marco tampoco tiene botón de cerrar del sistema, así que la **X va
adentro** y emite `cancelled`. `main()` la conecta a `ScannerWorker.cancel()`,
que es una **bandera** mirada en los dos bucles largos del escaneo, no un kill:
matar el hilo dejaría la tabla a medio llenar. Cancelado, el worker no emite
resultados — una tabla incompleta se lee igual que una completa.

Copying, Deleting y la búsqueda del relink usan la misma `ProgressWindow`, con
progreso real en cantidad de archivos. La del relink va con la barra
indeterminada: un `os.walk` no sabe cuánto le falta hasta que termina.

## Aspecto de las ventanas

Todo lo visual sale de `py/LGA_UI_Style_ToolPack.py`; acá no se escribe ningún
hex suelto. Dos cosas que hay que saber al tocar estas ventanas:

- **La fuente hay que aplicarla**, no alcanza con que el pack la registre:
  `UIStyle.apply_ui_font(ventana)` después de armarla.
- **El peso 600 se pide con `UIStyle.semibold_css()`**, no con
  `font-weight: 600`. La SemiBold de Inter vive en otra familia.

El detalle está en `docs/Docu_UI_Style.md`.

## Flujo de Ejecución

1. **Inicio**: `LGA_mediaManager.main()` → Crea `StartupWindow`
2. **Escaneo**: Instancia `FileScanner` → Inicia `ScannerWorker` 
3. **UI**: `FileScanner` muestra tabla con archivos encontrados
4. **Configuración**: Usuario puede abrir `SettingsWindow` para ajustes
5. **Operaciones**: Copiar/borrar archivos usando `CopyWorker`/`DeleteWorker`

## Escaneo de Nodos Read y CopyCat

### Nodos Soportados

El sistema escanea automáticamente los siguientes tipos de nodos en el proyecto de Nuke:

#### Nodos Read (Matching exacto de archivos)
- **Read, AudioRead, ReadGeo, DeepRead**: Utilizan el knob `file`
- **Matching**: Coincidencia exacta del path del archivo o secuencia
- **Función**: `get_read_files()` en `LGA_MediaManager_FileScanner.py`

#### Nodos CopyCat (Matching por carpeta)
- **CopyCat**: Utiliza los knobs `dataDirectory` y `checkpointFile`
- **Matching**: Coincidencia de carpeta - cualquier archivo dentro del directorio del CopyCat se considera asociado
- **Archivos relacionados**:
  - `LGA_ToolPack/LGA_MediaManager_FileScanner.py` - funciones `get_read_files()` líneas 1170-1210 y `add_file_to_table()` líneas 1440-1480
  - `LGA_ToolPack/LGA_MediaManager_FileScanner.py` - función `search_unmatched_reads()` líneas 990-1000 (filtro para evitar mostrar carpetas vacías)

### Lógica de Matching

#### Para Nodos Read
- **Archivos individuales**: Comparación directa del path completo
- **Secuencias**: Verificación usando `is_sequence_match()` con patrones de frame

#### Para Nodos CopyCat
- **Matching por directorio**: Comparación normalizada de rutas usando `normalize_path_for_comparison()`
- **Implementación**: Después del matching exacto fallido, se compara el directorio del archivo con los paths de CopyCat
- **Filtrado**: Las carpetas `dataDirectory` no se muestran en la tabla como archivos faltantes
- **Ejemplo**: CopyCat con `dataDirectory = "T:/project/copycat/"` → archivos en esa carpeta se marcan como "OK"
- **Logs de debug**: Prefijo `[READ_COPYCAT]` para rastrear el proceso de matching

## Detección de Secuencias de Archivos

### Reglas de Detección

El sistema determina si archivos forman una secuencia basándose en estas reglas:

#### Archivos Involucrados
- **LGA_ToolPack/LGA_MediaManager_utils.py** - función `find_files()` (líneas 799-950)
- **LGA_ToolPack/LGA_MediaManager_FileScanner.py** - función `search_unmatched_reads()` (líneas 981-1080)

#### Extensiones Válidas
- **Secuencias**: `.exr`, `.tif`, `.png`, `.jpg`
- **No secuencias**: `.mov`, `.psd`, `.avi`, `.mp4`

#### Algoritmo de Detección
1. **Comparación consecutiva**: Se analizan archivos adyacentes alfabéticamente
2. **Diferencias limitadas**: Solo 1-2 caracteres diferentes entre nombres
3. **Patrón regex**: `r"(.*?)(\d+)(\D*)$"` extrae números al final del nombre
4. **Verificación de consecutividad**: Los números deben ser secuenciales (ej: 001, 002, 003)
5. **Construcción de secuencia**: Reemplaza números por `#` según el padding

#### Ejemplo de Detección Válida
```
archivo_001.exr  →  archivo_###.exr[001-250]
archivo_002.exr
archivo_003.exr
```

#### Excepciones y Limitaciones
- **Números de versión**: Archivos con números precedidos por "v" se excluyen de secuencias
  - ✅ Correcto: `ETDM_3015_0010_DeAging_v02.tif` → archivo individual
  - ❌ Incorrecto: tratarlo como frame 02 de una secuencia
- **Gaps en numeración**: Secuencias con frames faltantes se detectan correctamente
- **Padding inconsistente**: Solo se agrupan archivos con mismo padding de dígitos

#### Secuencias Especiales Training_ (CopyCat/Nuke)

**Problema y solución**
Las secuencias generadas por Nuke con CopyCat tienen un patrón especial que va de 100 en 100 (ej: 1, 100, 200, 300... 40000) en lugar de ser consecutivas. El algoritmo estándar las dividía en múltiples grupos pequeños.

**Implementación**
Se agregó detección especial para archivos que empiezan con `Training_` en la función `find_files()`:

- **Función clave**: `parse_training_sequence_filename()` - Detecta archivos con patrón `Training_YYMMDD_HHMMSS.FRAME.ext`
- **Extensiones soportadas**: `.png` y `.cat` (cada extensión forma secuencias separadas)
- **Agrupación**: Todos los archivos Training_ con el mismo baseName+extensión se agrupan en una sola secuencia
- **Requisito mínimo**: Al menos 4 archivos para formar una secuencia

**Ejemplo de Detección Válida**
```
Training_250715_215458.110000.png   →  Training_250715_215458.#.png [110000-150000]
Training_250715_215458.114000.png
Training_250715_215458.118000.png
...
Training_250715_215458.150000.png
```

**Separación por extensión**
```
Training_250715_215458.110000.png   →  Training_250715_215458.#.png [110000-150000]
Training_250715_215458.110000.cat   →  Training_250715_215458.#.cat [110000-150000]
```

## Referencias técnicas

| Archivo | Qué mirar ahí |
|---|---|
| `py/LGA_mediaManager.py` | `main()`, y el header con la versión de la tool |
| `py/LGA_MediaManager_FileScanner.py` | `FileScanner.initUI()`, `apply_table_stylesheet()`, `update_minimum_width()`, `fit_footer_legend()`, `renumber_visible_rows()`, `adjust_window_size()`, `SortHeaderView`, `StatusCellDelegate` |
| `py/LGA_MediaManager_settings.py` | `SettingsWindow._build()`, `LocationRow`, `_fit_table()`, `_persist_theme()`, `_editable_state()`, y las tuplas `COL_*` con los anchos de la tabla |
| `py/LGA_MediaManager_config.py` | `load_settings()`, `format_ini()`, `save_settings()`, `get_write_path()`, `DEFAULT_*` |
| `py/LGA_MediaManager_paths.py` | `parse_path()`, `resolve()`, `scanning_parent()` |
| `py/LGA_MediaManager_utils.py` | `PathDelegate`, `ReadCellDelegate`, `TransparentTextDelegate`, `paint_row_separator()`, `tinted_icon()`, `ProgressWindow`, `BatchWorker`, `CopyWorker`, `DeleteWorker`, `expand_sequence()`, `ScannerWorker`, `RelinkSearchWorker`, `PathResolveWorker`, los `COL_*` |
| `py/LGA_UI_Style_ToolPack.py` | `theme()`, `apply_ui_font()`, `semibold_css()`, `THEMES` |
| `docs/Docu_UI_Style.md` | Cómo se usa el módulo de estilo y las trampas de Qt ya pisadas |
