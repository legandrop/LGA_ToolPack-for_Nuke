> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Guia del Sistema de Logging de LGA_ToolPack

## Descripcion General

Esta guia documenta el sistema de logging adoptado en `LGA_ToolPack` para herramientas Python que deben escribir por defecto en un archivo `.log` dedicado, sin ensuciar la consola de Nuke.

El primer caso implementado con este esquema es `LGA_mediaManager`.

## Objetivos del Sistema

- Escribir logs solo a archivo por defecto.
- Guardar cada herramienta en su propio `.log`.
- Crear los logs dentro de la carpeta `logs` del proyecto.
- Limpiar el archivo anterior al iniciar.
- Mantener timestamps relativos desde el inicio.
- Ser seguro para hilos usando `QueueHandler` y `QueueListener`.

## Flags Base

```python
DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True
```

Comportamiento por defecto:

- `DEBUG = True`: activa el sistema de debug.
- `DEBUG_CONSOLE = False`: no imprime en Script Editor o consola.
- `DEBUG_LOG = True`: escribe al archivo `.log`.

## Ubicacion y Nombre del Log

Para `LGA_mediaManager`, el archivo queda en:

```text
LGA_ToolPack/logs/LGA_mediaManager.log
```

Estructura esperada:

```text
LGA_ToolPack/
|-- docs/
|-- logs/
|   `-- LGA_mediaManager.log
`-- py/
    |-- LGA_MediaManager_logging.py
    |-- LGA_mediaManager.py
    |-- LGA_MediaManager_FileScanner.py
    |-- LGA_MediaManager_settings.py
    `-- LGA_MediaManager_utils.py
```

## Implementacion Actual

### Helper central

El helper compartido vive en `LGA_MediaManager_logging.py` y concentra:

- `setup_debug_logging()`
- `configure_logger()`
- `debug_print()`
- `cleanup_logging()`
- `get_log_file_path()`

### Reglas del logger

- `logger.propagate = False`
- handler asincrono con cola
- formatter con tiempo relativo
- limpieza del archivo al iniciar
- un unico logger compartido por los modulos del Media Manager

### Formato actual del log

```text
[0.015s] [LGA_MediaManager_FileScanner::search_unmatched_reads] Total read files a procesar: 12
```

## Uso recomendado en herramientas de LGA_ToolPack

### 1. Importar el helper

```python
from LGA_MediaManager_logging import configure_logger, debug_print
```

### 2. Pedir el logger compartido

```python
logger = configure_logger()
logger.debug("Mensaje tecnico")
```

### 3. Usar `debug_print()` cuando convenga mantener el API simple

```python
debug_print("Mensaje general")
debug_print("Algo fallo", level="warning")
debug_print("Error critico", level="error")
```

## Reglas obligatorias

1. El archivo debe vivir en `logs/` dentro del proyecto de la tool.
2. El nombre del archivo debe coincidir con la tool.
3. El logger no debe propagar al root logger.
4. Los mensajes por defecto no deben salir a consola.
5. Los modulos auxiliares de una misma tool deben compartir el mismo logger.

## Alcance actual

Implementado en:

- `LGA_mediaManager.py`
- `LGA_MediaManager_FileScanner.py`
- `LGA_MediaManager_settings.py`
- `LGA_MediaManager_utils.py`
- `LGA_MediaManager_logging.py`

Pendiente para futuras tools del pack:

- mover helpers equivalentes a otras herramientas que hoy solo usan `print`
- normalizar nombres y niveles de log en el resto del pack

## Referencias tecnicas

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_MediaManager_logging.py`
  - `RelativeTimeFormatter`
  - `get_toolpack_root()`
  - `get_log_file_path()`
  - `setup_debug_logging()`
  - `configure_logger()`
  - `debug_print()`
  - `cleanup_logging()`

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_mediaManager.py`
  - `main()`
  - import del helper central de logging

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_MediaManager_FileScanner.py`
  - `FileScanner`
  - `search_unmatched_reads()`
  - `get_read_files()`
  - `add_file_to_table()`

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_MediaManager_utils.py`
  - `ScannerWorker`
  - `CopyThread`
  - `DeleteThread`
  - uso compartido de `configure_logger()`

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_MediaManager_settings.py`
  - `SettingsWindow`
  - uso compartido de `debug_print()`
