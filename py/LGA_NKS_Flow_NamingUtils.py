"""
____________________________________________________________________

  LGA_NKS_Flow_NamingUtils v1.15 | Lega

  Utilidades para detectar y extraer información de nombres de archivos/shots
  Compatible con estos sistemas de nomenclatura:
  - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
  - PROYECTO_SEQ_SHOT (3 bloques simplificado)
  Si el ultimo bloque antes de la version es una task con track o un plate
  (aPlate, bPlate...), el shot es todo lo anterior y no se cuentan bloques.

  Usado por runtime activo:
  - LGA_NKS_Flow_Panel.py
  - LGA_NKS_Assignee_Panel.py
  - LGA_NKS_Flow_S3_Panel.py
  - LGA_NKS_Edit_Panel.py
  - LGA_NKS_Shared/LGA_NKS_GetClip.py
  - LGA_NKS_Flow_Rev_Panel_py/LGA_NKS_Flow_Pull.py
  - LGA_NKS_Flow_Rev_Panel_py/LGA_NKS_Flow_Push.py
  - LGA_NKS_Flow_Rev_Panel_py/LGA_NKS_Flow_Push_connector.py
  - LGA_NKS_Flow_Rev_Panel_py/LGA_NKS_Flow_Shot_info.py
  - LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assignee.py
  - LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assign_Assignee.py
  - LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Clear_Assignees.py
  - LGA_NKS_Flow_S3_Panel_py/LGA_NKS_Flow_ShowInFlow.py
  - LGA_NKS_Flow_S3_Panel_py/LGA_NKS_Flow_Thumbs.py
  - LGA_NKS_Flow_S3_Panel_py/LGA_NKS_Flow_CreateShot.py
  - LGA_NKS_Flow_S3_Panel_py/LGA_NKS_Flow_CheckTimelineShots.py
  - LGA_NKS_Flow_S3_Panel_py/LGA_NKS_Flow_ShotPriority.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_MatchVerToEXR.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_SetShotName.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_CompareVerToEditref.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_CompareEXR_to_aPlate.py

  v1.15: Igual que la v1.22 de la copia de HieroTools: el shot code se ancla
         en el ultimo bloque cuando es una task con track (comp, roto, cleanup,
         cg y aliases) o un plate, y se saca la deteccion de series. Con un
         primer bloque de descripcion numerico (PROYECTO_SEQ_SHOT_010_Desc) la
         serie confundia el formato y el shot code se llevaba la task.
         Ejemplos con nombres ficticios en vez de proyectos reales.
  v1.14: Actualiza las referencias documentales a las carpetas privadas
         Flow Rev y Flow S3 de HieroTools.
  v1.13: Copia local para LGA_ToolPack, usada por Show Flow Notes sin depender
         de HieroTools instalado/cargado.
  v1.12: extract_project_name_from_path(): extrae el nombre de proyecto desde
         el segmento de ruta "VFX-NOMBRE" en lugar del prefijo del filename.
         Fallback: extract_project_name() (comportamiento anterior).
         Ver docs/Docu_ProjectName_Extraction.md para el patrón completo.
  v1.11: Aliases de task: TASK_NAME_ALIASES y normalize_task_name().
         extract_task_name() normaliza el resultado para que "compo" → "comp"
         en toda la pipeline que use este módulo.
____________________________________________________________________________________
"""

import re
import os

_VERSION_RE = re.compile(r"^v\d+$", re.IGNORECASE)

# Aliases de task: nombres alternativos que deben tratarse como su canonical.
# Ej: archivos llamados "Compo" pertenecen a la task "comp".
TASK_NAME_ALIASES = {
    "compo": "comp",
}


def normalize_task_name(name):
    """Devuelve el nombre canonical de una task, resolviendo aliases conocidos."""
    if not name:
        return name
    return TASK_NAME_ALIASES.get(name.lower(), name.lower())


def _strip_version_suffix(parts):
    """Remueve un sufijo de versión tipo v### si está presente."""
    if parts and _VERSION_RE.match(parts[-1]):
        return parts[:-1]
    return parts


def _is_numeric_block(value):
    """True si el bloque comienza con un dígito."""
    return bool(value) and value[0].isdigit()


# Bloques del shot sin descripcion: PROYECTO_SEQ_SHOT. Ya no existe la base de
# serie (PROYECTO_TEMP_EP_SEQ_SHOT): no se usa mas, y detectarla por "tres
# bloques numericos tras el proyecto" confundia un shot con descripcion cuyo
# primer bloque es numerico (PROYECTO_SEQ_SHOT_010_Desc).
_BASE_BLOCKS = 3

# Ancla del parser: tasks con track en el timeline (espejo de TRACK_TASKS de
# LGA_NKS_TaskScope en HieroTools, que aca no se puede importar) mas aliases,
# y los plates de _input (<shot>_aPlate_v01, <shot>_bPlate...).
_ANCHOR_TASKS = frozenset({"comp", "roto", "cleanup", "cg"} | set(TASK_NAME_ALIASES))
_PLATE_TOKEN_RE = re.compile(r"^[a-z]plate$", re.IGNORECASE)


def _is_anchor_token(block):
    """True si el bloque es una task registrada (o alias) o un plate."""
    if not block:
        return False
    return block.lower() in _ANCHOR_TASKS or bool(_PLATE_TOKEN_RE.match(block))


def _analyze_shotname(base_name):
    """
    Separa el nombre base en shot y task. Retorna (shot_parts, task_block | None).

    1. Ancla: si el ultimo bloque es una task registrada o un plate, el shot es
       todo lo anterior, tenga la descripcion uno o dos bloques.
    2. Conteo, si el ultimo bloque no se reconoce: base de 3 bloques, +2 de
       descripcion si sobran al menos dos bloques.
    """
    if not base_name:
        return [], None

    core_parts = _strip_version_suffix(base_name.split("_"))
    if not core_parts:
        return [], None

    if len(core_parts) > _BASE_BLOCKS and _is_anchor_token(core_parts[-1]):
        return core_parts[:-1], core_parts[-1]

    shot_count = _BASE_BLOCKS + (2 if len(core_parts) >= _BASE_BLOCKS + 2 else 0)
    task = core_parts[shot_count] if len(core_parts) > shot_count else None
    return core_parts[:shot_count], task


def detect_shotname_format(base_name):
    """
    Detecta si el shotname lleva bloques de descripción: todo bloque del shot
    que sobra después de PROYECTO_SEQ_SHOT.

    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión

    Returns:
        bool: True si el shot tiene descripción, False si es simplificado
    """
    shot_parts, _ = _analyze_shotname(base_name)
    return len(shot_parts) > _BASE_BLOCKS


def extract_shot_code(base_name):
    """
    Extrae el shot_code de un nombre base de archivo.
    Detecta automáticamente el formato y extrae el shot_code correcto.

    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión

    Returns:
        str: Shot code extraído con o sin descripción
    """
    shot_parts, _ = _analyze_shotname(base_name)
    return "_".join(shot_parts)


def extract_project_name(base_name):
    """
    Extrae el nombre del proyecto del nombre base del archivo (primer bloque antes de _).
    Ej: "PROJA_1048_060_Compo" → "PROJA".

    NOTA: Este método es el fallback. Prefiere extract_project_name_from_path()
    cuando tenés la ruta completa del archivo disponible.

    Args:
        base_name (str): Nombre base del archivo

    Returns:
        str: Nombre del proyecto (primer campo)
    """
    if not base_name:
        return ""

    parts = base_name.split("_")
    return parts[0] if parts else ""


def extract_project_name_from_path(file_path):
    """
    Extrae el nombre del proyecto desde el segmento de ruta "VFX-NOMBRE".

    Los proyectos VFX siempre viven bajo una carpeta raíz con el patrón "VFX-NOMBRE"
    (ej: T:/VFX-PROJALT/...). El nombre del proyecto en la DB es "NOMBRE"
    (sin el prefijo "VFX-").

    Si no se encuentra ningún segmento con ese patrón, retorna None para que
    el caller pueda hacer fallback a extract_project_name().

    Ej:
        "T:/VFX-PROJALT/101/PROJA_1048_060/..." → "PROJALT"
        "T:/VFX-PROJF/102/..."                 → "PROJF"
        "/path/sin/prefijo/vfx/..."           → None

    Args:
        file_path (str): Ruta completa del archivo.

    Returns:
        str | None: Nombre del proyecto, o None si no se encuentra el patrón.
    """
    if not file_path:
        return None
    import os as _os
    normalized = _os.path.normpath(file_path)
    for part in normalized.split(_os.sep):
        if part.upper().startswith("VFX-") and len(part) > 4:
            return part[4:]  # strip "VFX-"
    return None


def clean_base_name(file_name):
    """
    Limpia el nombre de archivo removiendo extensiones y versiones.
    
    Args:
        file_name (str): Nombre completo del archivo
        
    Returns:
        str: Nombre base limpio sin extensión ni versión
    """
    if not file_name:
        return ""
    
    # Remover extensión de secuencia EXR/DPX y frames
    base_name = re.sub(r"_%04d\.(exr|dpx)$", "", file_name, flags=re.IGNORECASE)
    base_name = re.sub(r"_\d{4}\.(exr|dpx)$", "", base_name, flags=re.IGNORECASE)  # También formato sin %04d
    base_name = re.sub(r"\.%04d\.(exr|dpx)$", "", base_name, flags=re.IGNORECASE)  # Para archivos DPX con .%04d

    # Remover extensión común
    base_name = os.path.splitext(base_name)[0]

    # Remover versión al final (_v19, _v001, etc.)
    base_name = re.sub(r"_v\d+$", "", base_name)
    
    return base_name


def extract_task_name(base_name):
    """
    Extrae el nombre de la tarea del nombre base del archivo.
    
    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión
        
    Returns:
        str: Nombre de la tarea o None si no se encuentra
    """
    # Devuelve el bloque tal cual ("Compo", "aPlate"): normalizarlo es cosa
    # del caller, con normalize_task_name().
    _, task = _analyze_shotname(base_name)
    return task
