# LGA_Write_Presets

Sistema para crear nodos Write con configuraciones predefinidas. Genera paths automáticamente basándose en el nombre del script o del nodo Read seleccionado.

## Archivos Principales

- **`LGA_ToolPack/LGA_Write_Presets.py`**: Script principal que contiene la interfaz y lógica de creación de Write nodes
- **`LGA_ToolPack/LGA_Write_Presets.ini`**: Archivo de configuración con los presets disponibles
- **`LGA_ToolPack/LGA_Write_Presets_Check.py`**: Módulo auxiliar para verificación y edición de paths antes de crear el Write
- **`LGA_ToolPack/LGA_Write_PathToText.py`**: Módulo para mostrar paths de Write nodes ya creados

## Funcionalidad Principal

### Creación de Write Nodes

El sistema permite crear nodos Write con configuraciones predefinidas mediante una interfaz de tabla. Cada preset puede:

- Generar paths basados en el script actual (`button_type = script`)
- Generar paths basados en el nodo Read más alto en la jerarquía (`button_type = read`)
- Incluir un diálogo para ingresar texto personalizado (reemplaza `****` en el `file_pattern`)
- Crear nodos Switch y Dot adicionales para bypass
- Crear backdrops con colores personalizados

### Detección Automática de Formato

El sistema detecta automáticamente el formato de naming del shot:

- **Formato con descripción** (5 bloques): `PROYECTO_SEQ_SHOT_DESC1_DESC2`
- **Formato simplificado** (3 bloques): `PROYECTO_SEQ_SHOT`

Las fórmulas TCL en los presets se ajustan automáticamente según el formato detectado, sumando 2 a los índices cuando se detecta formato con descripción.

### Funciones Clave

- `load_presets()`: Lee el archivo `.ini` y retorna los presets
- `adjust_tcl_formulas(presets, has_description)`: Ajusta las fórmulas TCL según el formato detectado
- `create_write_from_preset(preset, user_text=None, modified_file_pattern=None)`: Crea el Write node con toda la configuración
- `detect_shotname_format_from_script()`: Detecta el formato del shotname usando el módulo compartido `LGA_ToolPack_NamingUtils`

## Verificación y Edición de Paths

Al hacer **click normal** sobre un preset, se muestra una ventana de verificación (`PathCheckWindow`) que permite revisar y editar el path antes de crear el Write node.

**Shift+Click** crea el Write directamente sin mostrar la ventana de verificación.

### Contenido de la Ventana

La ventana muestra en orden:

1. **Controles de edición**: Dos controles en la misma sección (siempre visibles):
   - **Naming Segments**: Control para editar índices ajustables en expresiones `lrange`. Si el preset no tiene índices ajustables, aparece deshabilitado mostrando "N/A"
   - **FOLDER UP LEVELS**: Control para ajustar la cantidad de niveles de directorio hacia arriba (`../`, `../../`, etc.). Siempre habilitado
2. **Original TCL Path**: El `file_pattern` tal como está configurado, dividido en 3 o 4 líneas visuales según corresponda
3. **Final Path**: El path resuelto y normalizado con colores por nivel de directorio, dividido en 3 o 4 líneas visuales

Los paths se dividen automáticamente: la primera línea muestra la parte que coincide con el shot folder (en violeta), las siguientes muestran el resto del path. Si es una secuencia, se separa la subcarpeta y el archivo en líneas distintas. Esto mejora la legibilidad en paths largos.

### Edición de Índices Ajustables

El control **Naming Segments** siempre está visible en la ventana. Cuando el preset contiene expresiones `lrange` con índices ajustables (patrón `] 0 X]`), el control está habilitado y permite:

- Ver el número actual de segmentos a incluir
- Incrementar/decrementar el valor con botones triangulares (▲ ▼)
- Ver cambios en tiempo real en el "Final Path" (con debounce de 200ms)

Si el preset no tiene índices ajustables, el control aparece deshabilitado (gris) mostrando "N/A" y los botones no son funcionales.

### Edición de Niveles de Directorio

El control **FOLDER UP LEVELS** siempre está visible y habilitado. La ventana detecta automáticamente si el `file_pattern` contiene niveles de directorio (`../`, `../../`, etc.) y permite:

- Ver la cantidad actual de niveles hacia arriba detectados en el preset
- Incrementar/decrementar la cantidad de niveles con botones triangulares (▲ ▼)
- Modificar todos los patrones `../` consecutivos en el `file_pattern` simultáneamente
- Ver cambios en tiempo real en el "Original TCL Path" y "Final Path" (con debounce de 200ms)
- Los cambios se combinan con los de índices ajustables si ambos están presentes

### Controles de la Ventana

- **ESC**: Cancela y cierra la ventana sin crear el Write
- **Enter**: Acepta y crea el Write node con la configuración (modificada si se editaron índices o niveles de directorio)
- **Cancel**: Cierra la ventana sin crear el Write
- **OK**: Crea el Write node con la configuración

### Archivos y Funciones Relacionadas

**`LGA_ToolPack/LGA_Write_Presets_Check.py`**:
- `has_adjustable_indices(file_pattern)`: Detecta si el file_pattern tiene índices ajustables y retorna el valor actual
- `replace_indices_in_pattern(file_pattern, new_index)`: Reemplaza todos los índices ajustables con el nuevo valor
- `has_directory_levels(file_pattern)`: Detecta si el file_pattern tiene niveles de directorio (`../`, `../../`, etc.) y retorna la cantidad máxima
- `replace_directory_levels(file_pattern, new_level)`: Reemplaza todos los patrones `../` consecutivos con la cantidad especificada de niveles
- `split_path_at_violet_end(path, shot_folder_parts, is_sequence=False)`: Divide el path normalizado en partes visuales (parte violeta, intermedia, subcarpeta y archivo según corresponda)
- `split_tcl_path_at_shot_end(tcl_path, shot_folder_parts, is_sequence=False)`: Divide el TCL path en partes visuales correspondientes
- `is_sequence_pattern(pattern)`: Detecta si un pattern contiene una secuencia de cuadros (`%04d`, `%03d`, etc.)
- `evaluate_file_pattern(file_pattern)`: Evalúa expresiones TCL creando un Write temporal
- `show_path_check_window(preset, user_text=None, callback=None)`: Muestra la ventana de verificación
- `PathCheckWindow`: Clase de la ventana que muestra los controles de edición, el TCL path original y el path final normalizado

**`LGA_ToolPack/LGA_Write_Presets.py`**:
- `ShiftClickTableWidget`: Clase personalizada de `QTableWidget` que detecta Shift+Click
- `handle_render_option(row, column)`: Maneja click normal y muestra la ventana de verificación
- `handle_render_option_shift(row, column)`: Maneja Shift+Click y crea el Write directamente sin ventana
- `_create_write_from_pending(modified_file_pattern=None)`: Callback que crea el Write usando el file_pattern modificado si aplica
