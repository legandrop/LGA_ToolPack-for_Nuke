> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Estado de Migración de Nomenclatura Dual - LGA ToolPack

Este documento rastrea el estado de migración de los scripts de LGA ToolPack para soportar ambos sistemas de nomenclatura:
- **Formato con descripción:** `PROYECTO_SEQ_SHOT_DESC1_DESC2` (5 bloques)
- **Formato simplificado:** `PROYECTO_SEQ_SHOT` (3 bloques)

## Leyenda de Estados

- ✅ **Dual Compartido:** Script migrado usando módulo compartido `LGA_ToolPack_NamingUtils.py` (a crear)
- 🔄 **Dual No Compartido:** Script migrado con detección dual pero usando su propia implementación
- ❌ **Sin Migrar:** Script que trabaja con shotnames pero aún no tiene detección dual
- ⚠️ **Revisar:** Script que podría necesitar migración pero requiere análisis más detallado
- ➖ **No Aplica:** Script que no trabaja con shotnames o no requiere migración

---

## Scripts Críticos (Trabajan directamente con shot_code)

### 1. LGA_showInlFlow.py
**Estado:** 🔄 **Dual No Compartido**  
**Descripción:** Extrae `shot_code` del nombre del script para buscar en ShotGrid/Flow  
**Implementación actual:** 
- Tiene detección dual implementada por campo 5
- Función `process_current_script()` detecta formato y genera `shot_code` correcto
- Lógica específica en líneas 301-329

**Acción requerida:** Migrar a módulo compartido cuando se cree `LGA_ToolPack_NamingUtils.py`

---

### 2. LGA_Write_Presets.py
**Estado:** ✅ **Dual Compartido**  
**Descripción:** Ajusta fórmulas TCL dinámicamente según el formato detectado  
**Implementación actual:**
- ✅ Usa módulo compartido `LGA_ToolPack_NamingUtils.py`
- Función `detect_shotname_format_from_script()` usa `detect_shotname_format()` y `get_script_base_name()` del módulo compartido
- Función `adjust_tcl_formulas()` ajusta índices TCL dinámicamente
- Mantiene función local `detect_shotname_format_local()` como fallback si el módulo no está disponible

**Cambios realizados:**
- Importa `detect_shotname_format` y `get_script_base_name` de `LGA_ToolPack_NamingUtils`
- Reemplazada función local `detect_shotname_format()` por `detect_shotname_format_from_script()` que usa el módulo compartido
- Compatibilidad hacia atrás mantenida con función local de respaldo

---

## Scripts Moderados (Trabajan con nombres de proyecto/archivos)

### 3. LGA_viewer_SnapShot.py
**Estado:** ⚠️ **Revisar**  
**Descripción:** Extrae nombre del proyecto sin versión para organizar snapshots en galería  
**Implementación actual:**
- Función `get_project_info()` extrae nombre del proyecto
- Solo remueve versión del final (`_v19`), no trabaja con shot_code
- Lógica en líneas 148-188

**Análisis:** 
- No extrae `shot_code` directamente
- Solo usa nombre del proyecto para organización de carpetas
- Probablemente funcione correctamente con ambos formatos sin cambios

**Acción requerida:** Verificar funcionamiento con ambos formatos y documentar

---

### 4. LGA_viewer_SnapShot_Gallery.py
**Estado:** ⚠️ **Revisar**  
**Descripción:** Muestra galería de snapshots organizados por proyecto  
**Implementación actual:**
- Función `get_project_info()` similar a LGA_viewer_SnapShot.py
- Función `extract_version_from_filename()` extrae versión de nombres de archivo
- Lógica en líneas 51-91 y 181-205

**Análisis:**
- Similar a LGA_viewer_SnapShot.py
- Probablemente funcione correctamente con ambos formatos sin cambios

**Acción requerida:** Verificar funcionamiento con ambos formatos y documentar

---

### 5. LGA_Write_Presets_Check.py - Función get_shot_folder_parts()
**Estado:** ➖ **No Aplica (Roadmap Futuro)**
**Descripción:** Calcula profundidad de directorios para coloreado de paths
**Implementación actual:**
- Calcula profundidad de directorios fija (`project_folder_depth = 3`)
- Mencionado en especificación como "ROADMAP FUTURO"
- Lógica en función `get_shot_folder_parts()`

**Análisis:**
- No trabaja directamente con shotnames
- Cálculo de profundidad podría mejorarse pero no es crítico
- Funciona correctamente tal como está

**Acción requerida:** Mejora futura opcional (no crítica)

---

## Scripts Auxiliares (Funciones helper)

### 6. LGA_Write_Presets.py - get_write_name_from_read()
**Estado:** ✅ **Funciona Correctamente**  
**Descripción:** Extrae nombre base de archivo Read para nombrar Write  
**Implementación actual:**
- Función en líneas 244-271
- Elimina padding y sufijos numéricos
- Según especificación: "✅ FUNCIONA CORRECTAMENTE - NO requiere cambios"

**Análisis:**
- No requiere cambios según especificación original
- Funciona con ambos formatos sin modificación

**Acción requerida:** Ninguna

---

## Scripts que NO trabajan con shotnames

### 7. LGA_MediaManager_utils.py
**Estado:** ➖ **No Aplica**  
**Descripción:** Utilidades para Media Manager  
**Análisis:** No trabaja con shotnames directamente

---

### 8. LGA_MediaManager_FileScanner.py
**Estado:** ➖ **No Aplica**  
**Descripción:** Scanner de archivos para Media Manager  
**Análisis:** No trabaja con shotnames directamente

---

### 9. LGA_CopyCat_Cleaner.py
**Estado:** ➖ **No Aplica**  
**Descripción:** Limpieza de archivos CopyCat  
**Análisis:** No trabaja con shotnames directamente

---

## Resumen de Migración

### Estadísticas
- ✅ **Dual Compartido:** 1 script (LGA_Write_Presets.py)
- 🔄 **Dual No Compartido:** 1 script (LGA_showInlFlow.py)
- ⚠️ **Revisar:** 2 scripts (LGA_viewer_SnapShot.py, LGA_viewer_SnapShot_Gallery.py)
- ➖ **No Aplica:** 5+ scripts
- ❌ **Sin Migrar:** 0 scripts críticos

### Próximos Pasos

1. ✅ **Crear módulo compartido** `LGA_ToolPack_NamingUtils.py` - COMPLETADO
2. ✅ **Migrar LGA_Write_Presets.py** - COMPLETADO
3. **Migrar LGA_showInlFlow.py** a usar el módulo compartido
4. **Revisar y validar** scripts marcados como "Revisar":
   - LGA_viewer_SnapShot.py
   - LGA_viewer_SnapShot_Gallery.py
5. **Documentar** decisiones sobre scripts que no requieren cambios

---

## Notas de Implementación

### Módulo Compartido Propuesto: LGA_ToolPack_NamingUtils.py

Funciones a incluir (basadas en LGA_NKS_Flow_NamingUtils.py):
- `detect_shotname_format(base_name)` - Detecta formato por campo 5
- `extract_shot_code(base_name)` - Extrae shot_code automáticamente
- `extract_project_name(base_name)` - Extrae nombre del proyecto
- `clean_base_name(file_name)` - Limpia nombres de archivo
- `extract_task_name(base_name)` - Extrae nombre de la tarea (si aplica)

### Técnica de Detección

**Campo 5 (índice 4) determina el formato:**
- Si `campo_5.startswith('v') AND campo_5[1:].isdigit()` → Formato simplificado (3 bloques)
- Si no → Formato con descripción (5 bloques)

**Ejemplos:**
- `MOR_000_140_comp_v19.nk` → Campo 5 = `v19` → Simplificado → Shot Code: `MOR_000_140`
- `MOR_000_140_Chroma_Auto_comp_v19.nk` → Campo 5 = `Auto` → Con Descripción → Shot Code: `MOR_000_140_Chroma_Auto`

---

## Historial de Cambios

### 2024-XX-XX - Migración de LGA_Write_Presets.py
- ✅ Creado módulo compartido `LGA_ToolPack_NamingUtils.py`
- ✅ Migrado `LGA_Write_Presets.py` para usar módulo compartido
- ✅ Mantenida compatibilidad hacia atrás con función local de respaldo

### 2024-XX-XX - Creación del documento
- Documentación inicial del estado de migración
- Identificación de scripts con detección dual no compartida
- Identificación de scripts a revisar

