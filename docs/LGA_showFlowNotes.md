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
PROJA_2029A_040_comp_v004.nk      → PROJA_2029A_040_comp
PROJA_2033_050_comp_v005_1001.exr → PROJA_2033_050_comp
PROJA_2033_050_comp_v005_%04d.exr → PROJA_2033_050_comp
```

### 2.3 Extracción del project_name

Fuente: `LGA_NKS_Flow_NamingUtils.extract_project_name(base_name)`

Simplemente toma el primer campo separado por `_`.

```
PROJA_2029A_040_comp → project_name = "PROJA"
PROJA_2033_050_comp  → project_name = "PROJA"
```

### 2.4 Extracción del shot_code

Fuente: `LGA_NKS_Flow_NamingUtils.extract_shot_code(base_name)`

Internamente llama a `_analyze_shotname(base_name)`, que separa shot y task en dos pasos:

1. **Ancla.** Si el último bloque es una task con track (`comp`, `roto`, `cleanup`, `cg`, o el alias `compo`) o un plate (`aPlate`, `bPlate`…), el shot es todo lo anterior. No cuenta bloques, así que no importa si la descripción tiene uno o dos bloques.
2. **Conteo**, si el último bloque no se reconoce: base de 3 bloques (`PROYECTO_SEQ_SHOT`), más 2 de descripción si sobran al menos dos bloques.

Ya no hay formato de serie (`PROYECTO_TEMP_EP_SEQ_SHOT`): no se usa más, y detectarlo por "tres bloques numéricos tras el proyecto" confundía un shot con descripción cuyo primer bloque es numérico. Con `PROJA_000_115_010_Desc_comp` el shot code se llevaba la task y no se encontraba en la DB.

El `shot_code` devuelto incluye el nombre del proyecto y es el valor que se busca en la columna `shot_name` de la DB local:

| Nombre de archivo limpio | Resuelve por | `shot_code` |
|--------------------------|--------------|-------------|
| `PROJA_2029A_040_comp` | ancla `comp` | `PROJA_2029A_040` |
| `PROJA_000_140_Chroma_Auto_comp` | ancla `comp` | `PROJA_000_140_Chroma_Auto` |
| `PROJA_000_115_010_Desc_comp` | ancla `comp` | `PROJA_000_115_010_Desc` |
| `PROJA_000_140_Chroma_Auto_layout` | conteo (3 + 2) | `PROJA_000_140_Chroma_Auto` |

Límite: el conteo supone dos bloques de descripción. Una task sin track con un solo bloque de descripción (`PROJA_000_140_Chroma_layout`) no se separa bien; con task con track el ancla lo resuelve.

> **Importante:** el `shot_code` incluye el prefijo del proyecto (`PROJA_...`), no solo `SEQ_SHOT`. Así está guardado en la columna `shots.shot_name` de `pipesync.db`.

### 2.5 Detección de la task

Fuente: `NukeOperations.infer_task_name(base_name)` → `LGA_NKS_Flow_NamingUtils.extract_task_name(base_name)`

`extract_task_name` devuelve el bloque que `_analyze_shotname` separó como task (el ancla, o el que sigue al shot en el conteo), tal cual viene en el nombre.

Luego `infer_task_name` valida que sea uno de `("comp", "roto", "cleanup")`. Si no encaja, devuelve `"comp"` como fallback.

**Ejemplos:**

```
PROJA_2029A_040_comp  → task = "comp"
PROJA_2033_050_roto   → task = "roto"
PROJA_000_140_Chroma_Auto_cleanup → task = "cleanup"
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
find_shot("PROJA", "PROJA_2029A_040")
find_shot("PROJA", "PROJA_2033_050")
```

Luego `find_task(shot, task_name)` busca dentro de `shot["tasks"]` por `task_type.lower() == task_name`.

---

## 3. Flujo completo — ejemplo con Read node

**Path en el Read:** `T:\VFX-PROJA\102\PROJA_2033_050\Comp\4_publish\PROJA_2033_050_comp_v005\PROJA_2033_050_comp_v005_1001.exr`

| Paso | Resultado |
|------|-----------|
| `_get_source_file_name` | `"PROJA_2033_050_comp_v005_1001.exr"`, source=`read_node` |
| `clean_base_name` | `"PROJA_2033_050_comp"` |
| `extract_project_name` | `"PROJA"` |
| `extract_shot_code` | `"PROJA_2033_050"` |
| `infer_task_name` | `"comp"` |
| DB query | `find_shot("PROJA", "PROJA_2033_050")` → task `"comp"` |

## 4. Flujo completo — ejemplo con script

**Script abierto:** `T:\VFX-PROJA\102\PROJA_2029A_040\Comp\1_projects\PROJA_2029A_040_comp_v004.nk`

| Paso | Resultado |
|------|-----------|
| `_get_source_file_name` | `"PROJA_2029A_040_comp_v004.nk"`, source=`script` |
| `clean_base_name` | `"PROJA_2029A_040_comp"` |
| `extract_project_name` | `"PROJA"` |
| `extract_shot_code` | `"PROJA_2029A_040"` |
| `infer_task_name` | `"comp"` |
| DB query | `find_shot("PROJA", "PROJA_2029A_040")` → task `"comp"` |

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
- `projects.project_name` — nombre del proyecto (ej: `"PROJA"`)
- `shots.shot_name` — shot code completo incluyendo proyecto (ej: `"PROJA_2033_050"`)
- `tasks.task_type` — nombre de la task en minúsculas (ej: `"comp"`, `"roto"`, `"cleanup"`)
- `versions` — versiones asociadas a cada task
- `version_notes` — notas/comentarios de cada versión

### Doc relacionada (Add Comment)

`C:\Users\leg4-pc\.nuke\LGA_ToolPack\docs\LGA_showFlowNotes_AddComment_Plan.md`
- Plan técnico del botón Add Comment para reviewers
