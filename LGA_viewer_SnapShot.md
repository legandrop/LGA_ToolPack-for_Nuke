# Implementación LGA SnapShot Buttons

## Descripción
Sistema de botones personalizados para el viewer de Nuke que permite tomar snapshots, mostrar el último snapshot y acceder a una galería de snapshots organizados por proyecto.

## Archivos del Sistema

### 1. `LGA_ToolPack/init.py`
- **Función**: Registra el callback `OnViewerCreate` que se ejecuta cuando se crea un viewer
- **Importa**: `LGA_viewer_SnapShot_Buttons` para el sistema personalizado de botones

### 2. `LGA_ToolPack/LGA_viewer_SnapShot_Buttons.py`
- **Función**: Script principal que maneja la inserción de botones en el viewer
- **Características**:
  - Inserta tres botones en el viewer de Nuke
  - Primer botón (`Take_SnapShotButton`): Ejecuta `take_snapshot()` con detección de Shift
  - Segundo botón (`Show_SnapShotButton`): Ejecuta `show_snapshot_hold()` con comportamiento hold
  - Tercer botón (`Gallery_SnapShotButton`): Abre la galería de snapshots
  - Usa iconos `snap_camera.png`, `sanp_picture.png` y `sanp_gallery.png`
  - Tooltips en inglés: "Take snapshot and save to gallery - use shift to NOT save to gallery", "Show last snapshot in viewer", "Open snapshot gallery"
  - Importación única del módulo para mantener el estado entre llamadas

### 3. `LGA_ToolPack/LGA_viewer_SnapShot.py`
- **Función**: Contiene la lógica principal de snapshot
- **Características**:
  - Compatibilidad con PySide/PySide2
  - Verificaciones exhaustivas de canales válidos antes de procesar
  - Función `take_snapshot(save_to_gallery=False)` para capturar imagen del viewer
  - Función `show_snapshot_hold()` para mostrar snapshot con control manual
  - Sistema de galería organizado por proyecto con `save_snapshot_to_gallery()`
  - Funciones de proyecto: `get_project_info()`, `get_next_gallery_number()`
  - Función `get_viewer_info()` para obtener información del viewer activo con nodo conectado
  - Función `get_viewer_info_for_show()` para obtener información del viewer permitiendo trabajar sin nodo conectado
  - Integración con sistema RenderComplete para manejo de sonido
  - Sistema de numeración ascendente para snapshots únicos (evita problemas de cache)
  - Funciones auxiliares: `get_next_snapshot_number()`, `cleanup_old_snapshots()`, `get_latest_snapshot_path()`

### 4. `LGA_ToolPack/LGA_viewer_SnapShot_Gallery.py`
- **Función**: Interfaz de galería de snapshots con thumbnails
- **Características**:
  - Ventana con estilo consistente y área de scroll
  - Función principal `open_snapshot_gallery()` 
  - Organización por proyectos con thumbnails redimensionables
  - Toolbar superior con slider de tamaño (50px - 500px)
  - Thumbnails ordenados alfabéticamente por proyecto
  - Soporte para múltiples formatos de imagen (jpg, png, tiff, exr)
  - Interfaz responsiva con hover effects en thumbnails

## Funcionamiento del Sistema

### Flujo de Trabajo
1. **Inicialización**: Al abrir Nuke, `init.py` se carga automáticamente
2. **Creación de Viewer**: Se ejecuta el callback `OnViewerCreate()`
3. **Inserción de Botones**: `LGA_viewer_SnapShot_Buttons.launch()` busca el frameslider y agrega los botones
4. **Funcionalidad Activa**: Los botones ejecutan las funciones correspondientes

### Verificaciones de Seguridad
- **Viewer activo**: Verifica que hay un viewer disponible
- **Nodo válido**: Para `take_snapshot()` confirma que hay un nodo conectado al viewer
- **Canales válidos**: Verifica que el nodo tiene canales de color (RGB/RGBA) ANTES de cualquier procesamiento
- **Permisos de archivo**: Confirma acceso a carpeta temporal para guardar snapshots
- **Flexibilidad**: `show_snapshot_hold()` funciona con o sin nodo conectado al viewer

## Estructura de Clases

### Take_SnapShotButton
- **Función**: Botón para tomar snapshots
- **Icono**: `snap_camera.png`
- **Tooltip**: "Take snapshot and save to gallery - use shift to NOT save to gallery"
- **Comportamiento**: Ejecuta `take_snapshot()` al hacer clic, por defecto guarda en galería, detecta Shift para NO guardar en galería
- **Requisito**: Necesita nodo conectado al viewer

### Show_SnapShotButton
- **Función**: Botón para mostrar snapshot con control manual
- **Icono**: `sanp_picture.png`
- **Tooltip**: "Show last snapshot in viewer"
- **Comportamiento**: Ejecuta `show_snapshot_hold()` con eventos pressed/released
- **Flexibilidad**: Funciona con o sin nodo conectado al viewer
- **Importación**: Carga el módulo una sola vez para mantener estado entre llamadas

### Gallery_SnapShotButton
- **Función**: Botón para abrir galería de snapshots
- **Icono**: `sanp_gallery.png`
- **Tooltip**: "Open snapshot gallery"
- **Comportamiento**: Ejecuta `open_snapshot_gallery()` del módulo LGA_viewer_SnapShot_Gallery
- **Funcionalidad**: Abre ventana de galería con thumbnails organizados por proyecto y slider de tamaño

## Clases de la Galería

### ThumbnailWidget
- **Función**: Widget personalizado para mostrar un thumbnail de imagen
- **Características**:
  - Carga y escala imágenes manteniendo relación de aspecto
  - Redimensionamiento dinámico con el slider
  - Estilo visual con bordes y hover effects
  - Manejo de errores con placeholder para imágenes no válidas

### ProjectFolderWidget
- **Función**: Contenedor que agrupa thumbnails por proyecto
- **Características**:
  - Título del proyecto con estilo destacado
  - Layout horizontal para thumbnails
  - Actualización dinámica del tamaño de todos los thumbnails
  - Mensaje informativo cuando no hay imágenes

### SnapshotGalleryWindow
- **Función**: Ventana principal de la galería
- **Características**:
  - Toolbar superior con slider de tamaño (50px - 500px)
  - Área de scroll para navegación fluida
  - Carga automática de proyectos y organización alfabética
  - Soporte para múltiples formatos de imagen
  - Mensajes informativos para estados vacíos

## Funciones Principales

### `take_snapshot(save_to_gallery=False)`
- **Verificaciones iniciales**: Viewer activo, nodo conectado, canales válidos (ANTES de RenderComplete)
- **Numeración única**: Genera snapshots con nombres `LGA_snapshot_N.jpg` donde N es ascendente
- **Proceso**: Crea nodo Write temporal, ejecuta render, guarda en carpeta temporal
- **Galería por defecto**: Si `save_to_gallery=True` (comportamiento por defecto), guarda copia en `snapshot_gallery/proyecto/`
- **Organización por proyecto**: Crea subcarpetas basadas en nombre del proyecto sin versión
- **Numeración secuencial**: Archivos en galería usan formato `proyecto_vXX_N.jpg`
- **Limpieza automática**: Elimina snapshots anteriores después del guardado exitoso
- **Salida**: Copia imagen al portapapeles y mantiene archivo temporal
- **Integración**: Maneja sistema RenderComplete si está disponible
- **Requisito**: Necesita nodo conectado al viewer con canales válidos

### `show_snapshot_hold(start)`
- **Función**: Muestra snapshot con control manual del usuario
- **start=True**: Busca el snapshot más reciente y lo muestra en viewer
- **start=False**: Elimina nodo Read temporal y restaura estado original
- **Estado**: Usa variable global para mantener información entre llamadas
- **Posicionamiento inteligente**: 
  - Con nodo conectado: Posiciona Read debajo del nodo existente
  - Sin nodo conectado: Posiciona Read arriba del viewer
- **Sin cache**: No necesita reload ya que cada snapshot tiene nombre único
- **Restauración**: Reconecta nodo original o desconecta viewer según estado inicial
- **Rendimiento**: Incluye `processEvents()` para evitar bloqueos de UI

### `get_viewer_info()`
- **Función**: Obtiene información del viewer activo con nodo conectado requerido
- **Retorna**: Tupla con (viewer, view_node, input_index, input_node)
- **Uso**: Para funciones que requieren nodo conectado como `take_snapshot()`
- **Manejo de errores**: Verificaciones robustas con debug prints

### `get_viewer_info_for_show()`
- **Función**: Obtiene información del viewer activo permitiendo trabajar sin nodo conectado
- **Retorna**: Tupla con (viewer, view_node, input_index, input_node) donde input_node puede ser None
- **Uso**: Para `show_snapshot_hold()` que puede funcionar sin nodo conectado
- **Flexibilidad**: Permite mostrar snapshots en viewers vacíos

### Funciones Auxiliares de Numeración

### `get_next_snapshot_number()`
- **Función**: Obtiene el siguiente número para snapshot verificando archivos existentes
- **Retorna**: Número entero siguiente al más alto encontrado
- **Patrón**: Busca archivos `LGA_snapshot_*.jpg` en carpeta temporal

### `cleanup_old_snapshots(current_number)`
- **Función**: Elimina snapshots con número menor al actual
- **Proceso**: Mantiene solo el snapshot más reciente para ahorrar espacio
- **Seguridad**: Manejo de errores en eliminación de archivos

### `get_latest_snapshot_path()`
- **Función**: Obtiene la ruta del snapshot con número más alto
- **Retorna**: Ruta completa del archivo o None si no encuentra ninguno
- **Uso**: Para `show_snapshot_hold()` al buscar el snapshot más reciente

### Funciones de Galería

### `get_project_info()`
- **Función**: Analiza el nombre del proyecto actual de Nuke
- **Retorna**: Tupla (nombre_sin_version, nombre_completo)
- **Lógica**: Detecta versiones en formato `_vXX` al final del nombre
- **Uso**: Para organizar snapshots por proyecto en la galería

### `get_next_gallery_number(project_dir, project_name)`
- **Función**: Obtiene el siguiente número secuencial para archivos de galería
- **Retorna**: Número entero siguiente al más alto encontrado para el proyecto
- **Patrón**: Busca archivos `proyecto_vXX_*.jpg` en la carpeta del proyecto

### `save_snapshot_to_gallery(snapshot_path)`
- **Función**: Guarda snapshot en galería organizada por proyecto
- **Proceso**: Crea subcarpeta del proyecto, numera archivo secuencialmente
- **Estructura**: `snapshot_gallery/proyecto_sin_version/proyecto_vXX_N.jpg`
- **Retorna**: Ruta del archivo guardado o None si hay error

## Implementación del Control Hold

El segundo botón usa eventos nativos de PySide2 para máxima responsividad:
- **pressed()**: Inicia la visualización del snapshot
- **released()**: Termina la visualización y restaura estado
- **Estado persistente**: Variable global mantiene información entre eventos
- **Módulo único**: Importación una sola vez evita reseteo de variables
- **Posicionamiento adaptativo**: Se adapta a viewers con o sin nodos conectados
- **Sistema único**: Cada snapshot tiene nombre único, evita problemas de cache

## Características Técnicas

### Manejo de Errores
- **Verificación de canales**: Previene errores de "has no valid channels"
- **Limpieza robusta**: Eliminación correcta de nodos temporales
- **Mensajes descriptivos**: Errores claros para debugging
- **Manejo de referencias**: Previene errores de "PythonObject not attached"
- **Verificación de estado**: Manejo seguro de viewers con/sin nodos conectados

### Optimización de Rendimiento
- **processEvents()**: Evita bloqueos de UI en puntos críticos
- **Importación única**: Módulo se carga una vez por botón
- **Estado global**: Mantiene información entre llamadas press/release
- **Limpieza automática**: Eliminación de nodos temporales y snapshots antiguos garantizada
- **Numeración inteligente**: Sistema ascendente evita conflictos y problemas de cache

### Integración con Sistemas
- **RenderComplete**: Manejo automático de sonido durante snapshot
- **Portapapeles**: Copia automática de imagen generada
- **Archivos temporales**: Gestión de snapshots en carpeta del sistema
- **Galería de proyecto**: Sistema organizado por proyecto con numeración secuencial
- **Iconos**: Sistema de iconos personalizados para botones (`snap_camera.png`, `sanp_picture.png`, `sanp_gallery.png`)
- **Nuke API**: Uso correcto de `node["reload"].execute()` para recargar Read nodes
- **Galería visual**: Thumbnails redimensionables con soporte para múltiples formatos
- **UI responsiva**: Slider de tamaño en tiempo real y área de scroll optimizada

## Notas de Implementación
- Los tres botones se insertan buscando el widget con tooltip "frameslider range"
- Se limpian botones existentes antes de agregar los nuevos
- Detección de tecla Shift para evitar guardar en galería (comportamiento invertido: sin Shift guarda, con Shift no guarda)
- Organización automática por proyecto basada en nombre del archivo de Nuke
- Debug prints disponibles para seguimiento de ejecución
- Restauración automática del estado del viewer en todos los casos
- Compatibilidad con versiones antiguas y nuevas de Nuke/PySide
- Soporte completo para viewers vacíos en función de mostrar snapshot
- Galería con thumbnails organizados alfabéticamente por proyecto
- Slider de tamaño dinámico (50px - 500px) para thumbnails
- Soporte para formatos jpg, png, tiff, exr en la galería

 