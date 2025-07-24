# LGA_mediaManager v1.61

## División de Responsabilidades

### Archivos Principales

#### `LGA_mediaManager.py`
- **Punto de entrada principal** del script
- Contiene la función `main()` que inicializa la aplicación
- Maneja los imports de todas las clases auxiliares
- Funciones utilitarias compartidas: `configure_logger()`, `debug_print()`, `normalize_path_for_comparison()`

#### `LGA_MediaManager_FileScanner.py`
- **Clase FileScanner**: Interfaz principal de usuario
- Gestión de la tabla de archivos y su visualización
- Funciones de escaneo, filtrado y manipulación de archivos
- Operaciones de usuario: borrar, copiar, revelar archivos
- Configuración de UI: botones, layouts, colores, fuentes

#### `LGA_MediaManager_settings.py`
- **Clase SettingsWindow**: Ventana de configuración 
- Gestión de paths de copia dinámicos
- Configuración de profundidad de carpetas del proyecto
- Manejo del archivo .ini de configuración

#### `LGA_MediaManager_utils.py`
- **Clases auxiliares compartidas**:
  - `ScannerWorker`: Worker en hilo separado para escaneo de archivos
  - `TransparentTextDelegate`: Delegado personalizado para la tabla
  - `LoadingWindow`: Ventanas de progreso (Scanning, Copying, Deleting)
  - `StartupWindow`: Ventana de inicio con barra de progreso
  - `CopyThread`: Worker para operaciones de copia de archivos
  - `DeleteThread`: Worker para operaciones de borrado
  - `ScannerSignals`: Señales Qt para comunicación entre hilos

## Flujo de Ejecución

1. **Inicio**: `LGA_mediaManager.main()` → Crea `StartupWindow`
2. **Escaneo**: Instancia `FileScanner` → Inicia `ScannerWorker` 
3. **UI**: `FileScanner` muestra tabla con archivos encontrados
4. **Configuración**: Usuario puede abrir `SettingsWindow` para ajustes
5. **Operaciones**: Copiar/borrar archivos usando `CopyThread`/`DeleteThread`

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

## Ventajas de la Refactorización

- **Separación clara** de responsabilidades
- **Código más mantenible** y organizado
- **Reutilización** de clases auxiliares
- **Facilita testing** y debugging
- **Evita duplicación** de código
