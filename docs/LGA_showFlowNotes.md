> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_showFlowNotes — Documentación técnica

## 1. Propósito

`LGA_showFlowNotes.py` muestra un popover con las versiones y notas de un shot desde la DB local de PipeSync. Determina automáticamente el shot y la task a consultar a partir de un archivo fuente (Read node o script de Nuke).

---

## 2. Resolución del shot: cómo se determina qué buscar

### 2.1 Fuente del archivo (prioridad)

Al ejecutarse, `NukeOperations._get_source_file_name()` determina el archivo fuente en este orden:

1. **Read node seleccionado** — si hay al menos un nodo `Read` seleccionado en Nuke, usa el `file` knob del primero (`nuke.selectedNodes('Read')[0]['file'].value()`).
2. **Script abierto** — si no hay Read seleccionado, usa `nuke.root().name()`.

En ambos casos se toma solo el basename del path (`os.path.basename`).

### 2.2 Limpieza del nombre de archivo (`clean_base_name`)

Fuente: `LGA_NKS_Flow_NamingUtils.clean_base_name(file_name)`

Pasos aplicados en orden:

| Paso | Regex / función | Qué elimina | Ejemplo |
|------|----------------|-------------|---------|
| 1 | `re.sub(r"_%04d\.(exr\|dpx)$")` | Frame con formato printf | `_v005_%04d.exr` → `_v005` |
| 2 | `re.sub(r"_\d{4}\.(exr\|dpx)$")` | Frame con 4 dígitos literales | `_v005_1001.exr` → `_v005` |
| 3 | `os.path.splitext` | Extensión restante | `.nk`, `.mov`, etc. |
| 4 | `re.sub(r"_v\d+$")` | Sufijo de versión | `_v005`, `_v004` |

**Ejemplos concretos:**

```
MOR_2029A_040_comp_v004.nk      → MOR_2029A_040_comp
MOR_2033_050_comp_v005_1001.exr → MOR_2033_050_comp
MOR_2033_050_comp_v005_%04d.exr → MOR_2033_050_comp
```

### 2.3 Extracción del project_name

Fuente: `LGA_NKS_Flow_NamingUtils.extract_project_name(base_name)`

Simplemente toma el primer campo separado por `_`.

```
MOR_2029A_040_comp → project_name = "MOR"
MOR_2033_050_comp  → project_name = "MOR"
```

### 2.4 Extracción del shot_code

Fuente: `LGA_NKS_Flow_NamingUtils.extract_shot_code(base_name)`

Internamente llama a `_analyze_shotname(base_name)` que determina:

- **¿Es formato de serie?** (`_is_series_format`): si `parts[1]`, `parts[2]` y `parts[3]` empiezan todos con dígito → formato de serie (4 bloques base: `PROYECTO_TEMPEP_SEQ_SHOT`). Si no, formato estándar (3 bloques base: `PROYECTO_SEQ_SHOT`).
- **¿Tiene descripción?** (`has_description`): si después de los bloques base hay al menos 2 bloques más antes de la task.

El `shot_code` devuelto incluye el nombre del proyecto y es el valor que se busca en la columna `shot_name` de la DB local:

| Nombre de archivo limpio | ¿Serie? | ¿Desc? | `shot_code` |
|--------------------------|---------|--------|-------------|
| `MOR_2029A_040_comp` | No | No | `MOR_2029A_040` |
| `MOR_2033_050_comp` | No | No | `MOR_2033_050` |
| `MOR_000_140_Chroma_Auto_comp` | No | Sí | `MOR_000_140_Chroma_Auto` |

> **Importante:** el `shot_code` incluye el prefijo del proyecto (`MOR_...`), no solo `SEQ_SHOT`. Así está guardado en la columna `shots.shot_name` de `pipesync.db`.

### 2.5 Detección de la task

Fuente: `NukeOperations.infer_task_name(base_name)` → `LGA_NKS_Flow_NamingUtils.extract_task_name(base_name)`

`extract_task_name` calcula el índice de la task como:
```
task_index = base_count + (2 si has_description else 0)
```
y devuelve `core_parts[task_index]`.

Luego `infer_task_name` valida que sea uno de `("comp", "roto", "cleanup")`. Si no encaja, devuelve `"comp"` como fallback.

**Ejemplos:**

```
MOR_2029A_040_comp  → task = "comp"
MOR_2033_050_roto   → task = "roto"
MOR_000_140_Chroma_Auto_cleanup → task = "cleanup"
```

### 2.6 Consulta en la DB local

Función: `ShotGridManager.find_shot(project_name, shot_code)`

```sql
SELECT s.*, p.project_sg_id FROM shots s
JOIN projects p ON s.project_id = p.id
WHERE p.project_name = ? AND s.shot_name = ?
```

Con los valores extraídos en los pasos anteriores. Por ejemplo:
```python
find_shot("MOR", "MOR_2029A_040")
find_shot("MOR", "MOR_2033_050")
```

Luego `find_task(shot, task_name)` busca dentro de `shot["tasks"]` por `task_type.lower() == task_name`.

---

## 3. Flujo completo — ejemplo con Read node

**Path en el Read:** `T:\VFX-MOR\102\MOR_2033_050\Comp\4_publish\MOR_2033_050_comp_v005\MOR_2033_050_comp_v005_1001.exr`

| Paso | Resultado |
|------|-----------|
| `_get_source_file_name` | `"MOR_2033_050_comp_v005_1001.exr"`, source=`read_node` |
| `clean_base_name` | `"MOR_2033_050_comp"` |
| `extract_project_name` | `"MOR"` |
| `extract_shot_code` | `"MOR_2033_050"` |
| `infer_task_name` | `"comp"` |
| DB query | `find_shot("MOR", "MOR_2033_050")` → task `"comp"` |

## 4. Flujo completo — ejemplo con script

**Script abierto:** `T:\VFX-MOR\102\MOR_2029A_040\Comp\1_projects\MOR_2029A_040_comp_v004.nk`

| Paso | Resultado |
|------|-----------|
| `_get_source_file_name` | `"MOR_2029A_040_comp_v004.nk"`, source=`script` |
| `clean_base_name` | `"MOR_2029A_040_comp"` |
| `extract_project_name` | `"MOR"` |
| `extract_shot_code` | `"MOR_2029A_040"` |
| `infer_task_name` | `"comp"` |
| DB query | `find_shot("MOR", "MOR_2029A_040")` → task `"comp"` |

---

## 5. Referencias técnicas

### Script principal

`C:\Users\leg4-pc\.nuke\LGA_ToolPack\py\LGA_showFlowNotes.py`
- `NukeOperations._get_source_file_name` — determina fuente (Read node o script)
- `NukeOperations.parse_nuke_script_name` — llama a `clean_base_name`
- `NukeOperations.infer_task_name` — detecta task desde el nombre limpio
- `NukeOperations.process_current_script` — orquesta toda la resolución y devuelve resultados
- `ShotGridManager.find_shot` — query SQL a `pipesync.db`
- `ShotGridManager.find_task` — busca task dentro del shot por nombre
- `GUIWindow.display_results` — muestra el resultado en la UI
- `GUIWindow.refresh_results` — refresca tras agregar un comentario

### Módulo de naming compartido

`C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_Flow_NamingUtils.py`
- `clean_base_name` — limpia extensión, frame number y versión del nombre de archivo
- `extract_project_name` — devuelve el primer campo (proyecto)
- `extract_shot_code` — devuelve `PROYECTO_SEQ_SHOT[_DESC1_DESC2]` según formato detectado
- `extract_task_name` — devuelve el campo de task según formato detectado
- `_analyze_shotname` — núcleo de detección: determina si es serie, si tiene descripción, y cuenta de bloques base

### DB local de PipeSync

`C:\Portable\LGA\PipeSync\cache\pipesync.db`
- `projects.project_name` — nombre del proyecto (ej: `"MOR"`)
- `shots.shot_name` — shot code completo incluyendo proyecto (ej: `"MOR_2033_050"`)
- `tasks.task_type` — nombre de la task en minúsculas (ej: `"comp"`, `"roto"`, `"cleanup"`)
- `versions` — versiones asociadas a cada task
- `version_notes` — notas/comentarios de cada versión

### Doc relacionada (Add Comment)

`C:\Users\leg4-pc\.nuke\LGA_ToolPack\docs\LGA_showFlowNotes_AddComment_Plan.md`
- Plan técnico del botón Add Comment para reviewers
