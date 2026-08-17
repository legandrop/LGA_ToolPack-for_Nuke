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
- Operaciones de usuario: borrar, copiar, revelar archivos
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
  - `LoadingWindow`: Ventanas de progreso (Scanning, Copying, Deleting)
  - `StartupWindow`: Ventana de inicio con barra de progreso
  - `CopyThread`: Worker para operaciones de copia de archivos
  - `DeleteThread`: Worker para operaciones de borrado
  - `ScannerSignals`: Señales Qt para comunicación entre hilos

### Los índices de columna viven en `utils`

`COL_PATH`, `COL_READ`, `COL_STATUS`, `COL_FOLDER_DELETE`, `COL_SEQUENCE` y
`COL_NUM` están en `LGA_MediaManager_utils.py`, no en el FileScanner: los
delegados de ese módulo también los necesitan, y el FileScanner ya importa de
ahí. Al revés sería circular.

El `#` es la columna 5 y no la 0: se agrega al final y se mueve al primer lugar
**visual** con `moveSection()`. En Qt el orden visual es independiente del
lógico, así que se ve primera sin correr un solo índice.

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
5. **Operaciones**: Copiar/borrar archivos usando `CopyThread`/`DeleteThread`

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
| `py/LGA_MediaManager_utils.py` | `PathDelegate`, `ReadCellDelegate`, `TransparentTextDelegate`, `paint_row_separator()`, `tinted_icon()`, `ScannerWorker`, `PathResolveWorker`, los `COL_*` |
| `py/LGA_UI_Style_ToolPack.py` | `theme()`, `apply_ui_font()`, `semibold_css()`, `THEMES` |
| `docs/Docu_UI_Style.md` | Cómo se usa el módulo de estilo y las trampas de Qt ya pisadas |
