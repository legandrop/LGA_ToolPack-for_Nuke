# Especificación de Compatibilidad de Nomenclatura - LGA ToolPack

## Introducción

Este documento describe la evolución del sistema de nomenclatura utilizado en la empresa y los cambios necesarios para hacer que los scripts de LGA ToolPack sean compatibles con ambos sistemas de naming.

## Sistema de Nomenclatura Actual (Con Campos de Descripción)

### Estructura del Shotname
El sistema actual utiliza una estructura de 5 componentes principales separados por guiones bajos:

```
PROYECTO_SEQ_SHOT_DESC1_DESC2
```

**Ejemplo:**
```
MOR_000_140_Chroma_Auto
```

### Estructura Completa de Archivos
```
PROYECTO_SEQ_SHOT_DESC1_DESC2_TASK_vVERSION.EXT
```

**Ejemplos:**
- Script: `MOR_000_140_Chroma_Auto_comp_v19.nk`
- Video: `MOR_000_140_Chroma_Auto_comp_v18.mov`
- Secuencia: `MOR_000_140_Chroma_Auto_comp_v19_1001.exr`

### Campos y su Significado

| Campo | Posición | Descripción | Ejemplo |
|-------|----------|-------------|---------|
| PROYECTO | 1 | Código del proyecto | `MOR` |
| SEQ | 2 | Número de secuencia (3 dígitos) | `000` |
| SHOT | 3 | Número de shot (3-4 dígitos) | `140` |
| DESC1 | 4 | Primera descripción | `Chroma` |
| DESC2 | 5 | Segunda descripción | `Auto` |
| TASK | 6 | Nombre de la tarea | `comp` |
| VERSION | 7 | Número de versión | `v19` |

### Uso en Flow/ShotGrid
- **Shot Code:** `SEQ_SHOT` (ej: `000_140`)
- **Task:** `DESC1_DESC2_TASK` (ej: `Chroma_Auto_comp`)

## Sistema de Nomenclatura Simplificado (Sin Campos de Descripción)

### Estructura del Shotname
El sistema simplificado elimina los campos de descripción:

```
PROYECTO_SEQ_SHOT
```

**Ejemplo:**
```
MOR_000_140
```

### Estructura Completa de Archivos
```
PROYECTO_SEQ_SHOT_TASK_vVERSION.EXT
```

**Ejemplos:**
- Script: `MOR_000_140_comp_v19.nk`
- Video: `MOR_000_140_comp_v18.mov`
- Secuencia: `MOR_000_140_comp_v19_1001.exr`

### Campos y su Significado

| Campo | Posición | Descripción | Ejemplo |
|-------|----------|-------------|---------|
| PROYECTO | 1 | Código del proyecto | `MOR` |
| SEQ | 2 | Número de secuencia (3 dígitos) | `000` |
| SHOT | 3 | Número de shot (3-4 dígitos) | `140` |
| TASK | 4 | Nombre de la tarea | `comp` |
| VERSION | 5 | Número de versión | `v19` |

### Uso en Flow/ShotGrid
- **Shot Code:** `SEQ_SHOT` (ej: `000_140`)
- **Task:** `TASK` (ej: `comp`)

## Problemas Identificados en los Scripts Actuales

### 1. LGA_showInlFlow.py (Problema CRÍTICO)
**Problema:** Parsing rígido que asume 5 campos para el shot_code
```python
shot_code = "_".join(parts[:5])  # Siempre toma primeros 5 campos
```

**Impacto:**
- Con descripción: `['MOR', '000', '140', 'Chroma', 'Auto']` → `MOR_000_140_Chroma_Auto` ✓
- Sin descripción: `['MOR', '000', '140', 'comp', 'v19']` → `MOR_000_140_comp_v19` ❌

### 2. LGA_Write_Presets.py (Problema MÁS CRÍTICO)
**Problema:** Fórmulas TCL hardcodeadas que esperan cantidades específicas de campos

**Fórmulas problemáticas:**
```tcl
[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]
[join [lrange [split [file tail [knob [topnode].file]] _ ] 0 6 ] _]
[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 5] _]
```

**Impacto:**
- Estas fórmulas generan paths incorrectos cuando faltan campos de descripción
- Afecta directamente la generación de archivos de salida
- Puede generar nombres completamente incorrectos

### 3. LGA_Write_Presets_Check.py - Función get_shot_folder_parts() (Problema MODERADO)
**Problema:** Cálculo de profundidad de directorios fijo
```python
project_folder_depth = 3  # Siempre sube 3 niveles
```

**Impacto:**
- Puede calcular incorrectamente la ruta del shot para coloreado de paths

### 4. LGA_Write_Presets.py - Función get_write_name_from_read() (Problema MENOR)
**Problema:** Eliminación rígida de segmentos numéricos
```python
if base_parts[-1].isdigit():
    file_name = "_".join(base_parts[:-1])
```

**Impacto:**
- Puede eliminar números legítimos que no sean versiones

## Archivos que Requieren Modificación

### Archivos Críticos (Deben modificarse)

1. **LGA_showInlFlow.py**
   - ✅ **Agregar detección de formato** para generar `shot_code` correcto
   - Detectar si tiene campos de descripción y ajustar lógica de parsing

2. **LGA_Write_Presets.py**
   - ✅ **Manejar dinámicamente ambos formatos** sin modificar el .ini
   - El .ini siempre asume formato con descripción (4 campos base)
   - El .py debe detectar si falta descripción y ajustar fórmulas TCL restando 2 campos
   - ✅ **`get_write_name_from_read()` funciona correctamente** - NO requiere cambios

### Archivos Moderados (Deben revisarse)

3. **LGA_Write_Presets_Check.py - Función get_shot_folder_parts()**
   - 🔮 **ROADMAP FUTURO:** Mejorar cálculo de profundidad de directorios
   - Por ahora NO se modifica (es funcional tal como está)

4. **LGA_viewer_SnapShot.py y LGA_viewer_SnapShot_Gallery.py**
   - ✅ **Revisar lógica de extracción de versiones** para ambos formatos
   - Asegurar compatibilidad automática

## Técnica de Detección Implementada

### 🎯 **Detección Inteligente por Campo 5**

**Principio:** El campo 5 (índice 4) determina automáticamente el formato del shotname

**Lógica:**
```
Si campo_5.startswith('v') AND campo_5[1:].isdigit():
    → Formato Simplificado (3 campos base)
Sino:
    → Formato con Descripción (5 campos base)
```

**Casos de Uso:**
- `MOR_000_140_comp_v19.nk` → Campo 5 = `v19` → **Simplificado** → Shot Code: `MOR_000_140`
- `MOR_000_140_Chroma_Auto_comp_v19.nk` → Campo 5 = `Auto` → **Con Descripción** → Shot Code: `MOR_000_140_Chroma_Auto`

**Ventajas:**
- ✅ **100% preciso** - No hay falsos positivos
- ✅ **Automático** - Sin configuración manual
- ✅ **Robusto** - Funciona con cualquier nombre de task o descripción
- ✅ **Compatible** - Mantiene funcionamiento actual para formato con descripción

## Estrategia de Solución

### ❌ **ABANDONADO:** Sistema de Configuración Manual y Funciones Centralizadas
- ✅ **Eliminado** completamente `LGA_ToolPack_settings_ShotName.py`
- ✅ **Eliminado** el botón "Configure Shot Naming" del menú
- **NO crear** funciones helper centralizadas
- **Razón:** Cada script resuelve su problema específico de manera independiente

### ✅ **IMPLEMENTAR:** Lógica Específica en Cada Script

**Estrategia directa: cada script implementa su propia detección automática**

### 1. LGA_showInlFlow.py - Detección Inteligente para Shot Code

**Problema actual:**
```python
shot_code = "_".join(parts[:5])  # Siempre toma primeros 5 campos
```

**Solución específica - Técnica de Detección por Campo 5:**
```python
# Deteccion inteligente: verificar si el campo 5 es una version
# Si el campo 5 empieza con 'v' seguido de numeros, es formato simplificado
# Si no, es formato con descripcion
is_simplified_format = False
if len(parts) >= 5:
    field_5 = parts[4]  # Campo 5 (indice 4)
    if field_5.startswith('v') and len(field_5) > 1 and field_5[1:].isdigit():
        is_simplified_format = True

if is_simplified_format:
    shot_code = "_".join(parts[:3])  # proyecto_seq_shot
else:
    shot_code = "_".join(parts[:5])  # proyecto_seq_shot_desc1_desc2
```

**Lógica de Detección:**
- **Campo 5 = versión** (`v19`, `v001`) → Formato simplificado (3 campos base)
- **Campo 5 ≠ versión** (`Auto`, `Chroma`) → Formato con descripción (5 campos base)

**Ejemplos de Detección:**
- `MOR_000_140_comp_v19` → Campo 5 = `v19` → Simplificado → `MOR_000_140`
- `MOR_000_140_Chroma_Auto` → Campo 5 = `Auto` → Con descripción → `MOR_000_140_Chroma_Auto`

### 2. LGA_Write_Presets.py - Ajuste Dinámico de Fórmulas TCL

**Problema actual:**
```tcl
[join [lrange [split [file tail [value root.name]]] _ ] 0 4] _]
# Siempre asume 5 campos base (índice 4 = campo 5)
```

**Solución específica:**
```python
# Detectar formato y ajustar índice dinámicamente
base_parts = script_name.split('_')
if len(base_parts) > 5:  # Tiene descripción
    index = 4  # Usar índice original (5 campos)
else:  # Sin descripción
    index = 2  # Restar 2 campos (solo 3 campos base)

tcl_formula = f"[join [lrange [split [file tail [value root.name]]] _ ] 0 {index}] _]"
```

### 3. get_write_name_from_read() - ✅ FUNCIONA CORRECTAMENTE

**Análisis realizado:**
Después de revisar los formatos válidos de naming:

**Con descripción:**
- ✅ `MOR_000_140_Chroma_Auto_comp_v019.nk`
- ✅ `MOR_000_140_Chroma_Auto_comp_v19.nk`

**Sin descripción:**
- ✅ `MOR_000_140_comp_v019.nk`
- ✅ `MOR_000_140_comp_v19.nk`

**Conclusión:**
❌ **NO hay problema** con la función actual:
```python
if base_parts[-1].isdigit():
    file_name = "_".join(base_parts[:-1])
```

**Razón:**
- Nunca debería existir un número entre `comp` y `v19` en naming válido
- Si existe `MOR_000_140_comp_001_v19.nk`, sería un error de naming que debe corregirse
- La función actual elimina correctamente números inválidos al final del nombre

### 4. Roadmap Futuro - LGA_Write_Presets_Check.py - Función get_shot_folder_parts()

**Por ahora NO se modifica** (funciona correctamente)
**Mejora futura propuesta:**
- Calcular profundidad de directorios dinámicamente
- Basarse en estructura real del proyecto vs ruta del script

## Criterios de Éxito

1. **Compatibilidad hacia atrás:** Los scripts funcionan exactamente igual con el sistema actual (con descripción)
2. **Detección automática:** Cada script detecta automáticamente si hay descripción o no SIN configuración previa
3. **Lógica independiente:** Cada script resuelve su problema específico sin depender de módulos externos
4. **Fórmulas TCL dinámicas:** Los presets ajustan automáticamente sus fórmulas según el formato detectado
5. **Shot codes correctos:** Se generan códigos de shot correctos para Flow en ambos formatos
6. **Sin errores:** No se producen errores independientemente del formato del nombre
7. **Transparente para el usuario:** El usuario no necesita configurar nada, todo funciona automáticamente

## Consideraciones de Implementación

- **Tiempo de desarrollo:** 1-2 días
- **Testing requerido:** Crear casos de prueba exhaustivos con ambos formatos
- **Documentación:** Documentar la lógica de detección automática implementada
- **Rollback plan:** Mantener versiones anteriores por seguridad
- **Archivos afectados:** Solo 2 archivos críticos requieren modificación

## Estado del Proyecto

### ✅ Fase 1: Limpieza - COMPLETADA
1. ✅ **Eliminado** `LGA_ToolPack_settings_ShotName.py` completamente
2. ✅ **Eliminado** botón "Configure Shot Naming" del menú principal
3. ✅ **Limpiadas** referencias a configuración de naming en otros archivos

### ✅ Fase 2A: LGA_showInlFlow.py - COMPLETADA
4. ✅ **Implementada** detección inteligente por campo 5 en `LGA_showInlFlow.py`
   - Detección automática de formato simplificado vs con descripción
   - Generación correcta de shot_code para ambos formatos
   - Compatibilidad 100% hacia atrás
   - ✅ **Corregido** parsing de nombres - eliminación correcta de extensión .nk

### ✅ Fase 2B: LGA_Write_Presets.py - COMPLETADA
5. ✅ **Implementado** ajuste dinámico de fórmulas TCL en `LGA_Write_Presets.py`
   - Detección automática de formato usando la misma técnica (campo 5 = versión)
   - .ini configurado por defecto para formato simplificado (3 bloques)
   - Ajuste dinámico +2 bloques cuando se detecta formato con descripción
   - Logs detallados de detección y ajustes realizados
   - Manejo de casos edge (script no guardado = formato simplificado)

### Fase 3: Revisión y Testing (Día 2)
7. **Revisar** `LGA_viewer_SnapShot.py` y `LGA_viewer_SnapShot_Gallery.py`
8. **Probar** exhaustivamente con casos reales de ambos formatos
9. **Validar** funcionamiento correcto con proyectos existentes

### Fase 4: Documentación (Día 2-3)
10. **Documentar** cambios realizados
11. **Crear** casos de prueba automatizados

## Implementación Técnica Específica

### LGA_showInlFlow.py
```python
# ✅ IMPLEMENTADO - Detección inteligente por campo 5
parts = base_name.split("_")

# Verificar si el campo 5 es una version (v + numeros)
is_simplified_format = False
if len(parts) >= 5:
    field_5 = parts[4]  # Campo 5 (indice 4)
    if field_5.startswith('v') and len(field_5) > 1 and field_5[1:].isdigit():
        is_simplified_format = True

# Generar shot_code segun el formato detectado
if is_simplified_format:
    shot_code = "_".join(parts[:3])  # proyecto_seq_shot
else:
    shot_code = "_".join(parts[:5])  # proyecto_seq_shot_desc1_desc2
```

### LGA_Write_Presets.py
```python
# ✅ IMPLEMENTADO - Detección y ajuste dinámico de fórmulas TCL

def detect_shotname_format():
    """Detecta formato basado en script actual de Nuke"""
    script_path = nuke.root().name()
    if not script_path or script_path == "Root":
        return False  # Sin script = formato simplificado
    
    base_name = re.sub(r"\.nk$", "", os.path.basename(script_path))
    parts = base_name.split("_")
    
    if len(parts) >= 5:
        field_5 = parts[4]
        # Si campo 5 es versión -> formato simplificado
        return not (field_5.startswith('v') and field_5[1:].isdigit())
    return False

def adjust_tcl_formulas(presets, has_description):
    """Ajusta fórmulas TCL dinámicamente"""
    if not has_description:
        return presets  # Usar .ini tal como está (3 bloques)
    
    # Sumar 2 a todos los índices TCL para formato con descripción
    for preset in presets.values():
        if "file_pattern" in preset:
            preset["file_pattern"] = re.sub(
                r"\] 0 (\d+)\]", 
                lambda m: f"] 0 {int(m.group(1)) + 2}]", 
                preset["file_pattern"]
            )
    return presets

# En __init__ de SelectedNodeInfo:
has_description = detect_shotname_format()
base_presets = load_presets()
self.presets = adjust_tcl_formulas(base_presets, has_description)
```
