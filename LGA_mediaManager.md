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

## Debugging de Archivos Duplicados (Problema Resuelto)

### Problema Identificado
El archivo `ETDM_1000_0120_DeAging_Atropella_EditRef_v01.mov` (y muchos otros) aparecía **DOS VECES** en la tabla del media manager.

### Proceso de Debugging

#### 1. **Identificación del Problema**
- Los logs mostraron que el archivo se agregaba dos veces:
  - **Primera vez**: Desde `find_files` (archivos encontrados en disco)
  - **Segunda vez**: Desde `search_unmatched_reads` (nodos Read sin match)

#### 2. **Análisis de la Causa Raíz**
- **Hipótesis inicial**: El problema estaba en `add_file_to_table` donde no se actualizaban correctamente los `matched_reads`
- **Realidad descubierta**: El problema estaba en `find_files` que agregaba el mismo archivo DOS VECES desde el inicio

#### 3. **Descubrimiento del Bug Real**
Los logs de conteo mostraron:
```
*** FIND_FILES COUNT: EditRef encontrado en root: T:/VFX-ETDM/101/ETDM_1000_0120_DeAging_Atropella\_input
Archivos EditRef: ['ETDM_1000_0120_DeAging_Atropella_EditRef_v01.mov']
```
Este log aparecía **DOS VECES** para la misma carpeta, indicando que `os.walk()` visitaba la misma carpeta múltiples veces.

#### 4. **Causa del Problema**
- **os.walk()** estaba procesando la misma carpeta múltiples veces debido a links simbólicos, accesos directos, o referencias circulares en el sistema de archivos
- Cada procesamiento agregaba el mismo archivo a `to_add[]`

#### 5. **Soluciones Intentadas**

**Intento 1**: Set de archivos procesados durante el escaneo
```python
processed_files = set()  # Para evitar duplicados causados por os.walk()
if normalized_file_path not in processed_files:
    processed_files.add(normalized_file_path)
    to_add.append(...)
```
**Resultado**: Falló porque el `set` se perdía entre diferentes bucles de `os.walk()`

**Intento 2**: Logs de debugging detallados
- Confirmó que el mismo archivo se evaluaba múltiples veces
- Reveló que `processed_files` se reseteaba entre llamadas

#### 6. **Solución Final Implementada**
**Deduplicación post-procesamiento** en `find_files()`:
```python
# Eliminar duplicados de to_add antes de devolver
unique_files = {}
for item in to_add:
    normalized_path = normalize_path_for_comparison(file_path)
    if normalized_path not in unique_files:
        unique_files[normalized_path] = item
    else:
        duplicates_found += 1

to_add = list(unique_files.values())
```

#### 7. **Logs de Debugging Agregados**
- `*** FIND_FILES COUNT: EditRef encontrado en root`
- `*** FIND_FILES SEGUNDA PASADA: EditRef en root`
- `*** FIND_FILES: Evaluando EDITREF`
- `*** DUPLICADO ENCONTRADO Y ELIMINADO: EditRef`

### Resultado
- **Problema resuelto**: Los archivos duplicados en `find_files` se eliminan antes de enviar a `add_file_to_table`
- **Impacto**: Soluciona duplicados tanto para archivos individuales como secuencias
- **Método**: Solución quirúrgica que no afecta la lógica existente del código

### Lecciones Aprendidas
1. **os.walk()** puede visitar la misma carpeta múltiples veces en sistemas de archivos complejos
2. La deduplicación debe hacerse **después** de completar todo el escaneo
3. Los logs detallados son esenciales para identificar problemas de flujo de datos
4. Las soluciones quirúrgicas son preferibles a refactorizaciones completas 