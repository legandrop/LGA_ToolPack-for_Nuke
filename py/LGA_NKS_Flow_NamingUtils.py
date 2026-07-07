"""
____________________________________________________________________

  LGA_NKS_Flow_NamingUtils v1.13 | Lega

  Utilidades para detectar y extraer información de nombres de archivos/shots
  Compatible con sistemas de nomenclatura actuales y series:
  - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
  - PROYECTO_SEQ_SHOT (3 bloques simplificado)
  - PROYECTO_TempEP_SEQ_SHOT_DESC1_DESC2 (6 bloques con descripción)
  - PROYECTO_TempEP_SEQ_SHOT (4 bloques simplificado)

  Usado por runtime activo:
  - LGA_NKS_Flow_Panel.py
  - LGA_NKS_Assignee_Panel.py
  - LGA_NKS_Coordination_Panel.py
  - LGA_NKS_Edit_Panel.py
  - LGA_NKS_Shared/LGA_NKS_GetClip.py
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push_connector.py
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Shot_info.py
  - LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assignee.py
  - LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assign_Assignee.py
  - LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Clear_Assignees.py
  - LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ShowInFlow.py
  - LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_Thumbs.py
  - LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_CreateShot.py
  - LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_CheckTimelineShots.py
  - LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ShotPriority.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_MatchVerToEXR.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_SetShotName.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_CompareVerToEditref.py
  - LGA_NKS_Edit_Panel_py/LGA_NKS_CompareEXR_to_aPlate.py

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


def _is_series_format(parts):
    """
    Detecta formato de serie:
    Después del proyecto, los 3 bloques siguientes empiezan con dígito.
    """
    return len(parts) >= 4 and all(_is_numeric_block(p) for p in parts[1:4])


def _analyze_shotname(base_name):
    """
    Analiza el shotname y retorna:
    (core_parts, is_series, has_description, base_count)
    """
    if not base_name:
        return [], False, False, 0

    parts = base_name.split("_")
    core_parts = _strip_version_suffix(parts)
    if not core_parts:
        return [], False, False, 0

    is_series = _is_series_format(core_parts)
    base_count = 4 if is_series else 3
    has_description = len(core_parts) >= (base_count + 2)

    return core_parts, is_series, has_description, base_count


def detect_shotname_format(base_name):
    """
    Detecta el formato del shotname basado en el nombre base del archivo.
    
    Técnicas de detección:
    - Si después del proyecto los 3 bloques siguientes empiezan con dígito → formato de serie
    - Si hay al menos 2 bloques adicionales tras el bloque base → formato con descripción
    
    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión
        
    Returns:
        bool: True si es formato con descripción (5/6 bloques), False si es simplificado (3/4 bloques)
    """
    core_parts, _, has_description, _ = _analyze_shotname(base_name)
    if not core_parts:
        return False

    return has_description


def extract_shot_code(base_name):
    """
    Extrae el shot_code de un nombre base de archivo.
    Detecta automáticamente el formato y extrae el shot_code correcto.
    
    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión
        
    Returns:
        str: Shot code extraído con o sin descripción (incluye variante de serie)
    """
    core_parts, _, has_description, base_count = _analyze_shotname(base_name)
    if not core_parts:
        return ""

    desc_count = 2 if has_description else 0
    target_count = base_count + desc_count

    if len(core_parts) >= target_count:
        return "_".join(core_parts[:target_count])

    return "_".join(core_parts)


def extract_project_name(base_name):
    """
    Extrae el nombre del proyecto del nombre base del archivo (primer bloque antes de _).
    Ej: "MOR_1048_060_Compo" → "MOR".

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
    (ej: T:/VFX-MORLASP/...). El nombre del proyecto en la DB es "NOMBRE"
    (sin el prefijo "VFX-").

    Si no se encuentra ningún segmento con ese patrón, retorna None para que
    el caller pueda hacer fallback a extract_project_name().

    Ej:
        "T:/VFX-MORLASP/101/MOR_1048_060/..." → "MORLASP"
        "T:/VFX-BRDA/102/..."                 → "BRDA"
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
    core_parts, _, has_description, base_count = _analyze_shotname(base_name)
    if not core_parts:
        return None

    # Estructura base:
    # - Standard: PROYECTO_SEQ_SHOT
    # - Serie: PROYECTO_TEMP_EP_SEQ_SHOT
    # Si hay descripción, suma DESC1_DESC2 antes de TASK
    task_index = base_count + (2 if has_description else 0)

    if len(core_parts) > task_index:
        return core_parts[task_index]

    return None

