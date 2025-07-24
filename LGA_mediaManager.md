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

## Ventajas de la Refactorización

- **Separación clara** de responsabilidades
- **Código más mantenible** y organizado
- **Reutilización** de clases auxiliares
- **Facilita testing** y debugging
- **Evita duplicación** de código 