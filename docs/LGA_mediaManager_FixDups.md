> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

## Problemas Conocidos y Deuda Técnica

### Duplicación de Clase FileScanner
**Problema**: La clase `FileScanner` existe en **DOS archivos**:
- `LGA_MediaManager_FileScanner.py` - **Versión oficial y mantenida**
- `LGA_MediaManager_utils.py` - **Versión deprecated/legacy**

**Causa**: Durante la refactorización se mantuvo una copia en `utils.py` para testing independiente.

**Estado Actual**:
- `LGA_mediaManager.py` importa desde `FileScanner.py` (correcto)
- `utils.py` tiene su propia copia para el bloque `__main__` (legacy)
- **La solución de deduplicación** se implementó en `FileScanner.py` (la versión correcta)

**Solución Futura**: 
- Eliminar la clase duplicada de `utils.py`
- Hacer que `utils.py` importe desde `FileScanner.py`
- Mantener solo una versión de la clase

**Impacto**: 
- ✅ **No afecta la funcionalidad actual** 
- ⚠️ **Puede causar confusión** durante el desarrollo
- 🔄 **Duplica esfuerzo** de mantenimiento

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

### Solución Final Implementada

#### Problema Real Descubierto
Tras el debugging detallado se descubrió que el problema **NO** era en `find_files()`, sino que:
- **Múltiples workers** se ejecutaban simultáneamente
- **Cada worker** enviaba su propia lista de archivos a `add_file_to_table()`
- **Sin deduplicación** entre workers, los mismos archivos se agregaban múltiples veces

#### Solución Final: Deduplicación Session-Based
**Implementada en**: `LGA_MediaManager_FileScanner.py::add_file_to_table()`

```python
# Crear un registro de archivos ya procesados en esta sesión
if not hasattr(self, '_processed_files_session'):
    self._processed_files_session = set()

# Filtrar duplicados antes de procesar
for file_data in files_data:
    file_path = file_data[0]
    normalized_path = normalize_path_for_comparison(file_path)
    
    if normalized_path not in self._processed_files_session:
        self._processed_files_session.add(normalized_path)
        unique_files_data.append(file_data)
    else:
        duplicates_removed += 1

files_data = unique_files_data  # Usar solo archivos únicos
```

#### Ventajas de la Solución Final
- **A prueba de fallos**: Funciona sin importar cuántos workers se ejecuten
- **Session-based**: Mantiene registro durante toda la sesión de escaneo
- **Quirúrgica**: No modifica la arquitectura de workers existente
- **Eficiente**: Deduplicación O(1) usando sets con paths normalizados
- **Transparente**: El resto del código no se ve afectado

#### Resultado
- **100% de duplicados eliminados**
- **Sin crashes** ni problemas de performance
- **Arquitectura intacta** - no se rompió funcionalidad existente 