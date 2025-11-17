"""
____________________________________________________________________________________

  LGA_ToolPack_NamingUtils v1.0 | Lega
  Utilidades para detectar y extraer informacion de nombres de archivos/shots
  Compatible con ambos sistemas de nomenclatura:
  - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripcion)
  - PROYECTO_SEQ_SHOT (3 bloques simplificado)

  Scripts que utilizan este modulo:
  - LGA_Write_Presets.py
  - LGA_showInlFlow.py
  - (otros scripts de LGA_ToolPack que trabajen con shotnames)
____________________________________________________________________________________
"""

import re
import os


def detect_shotname_format(base_name):
    """
    Detecta el formato del shotname basado en el nombre base del archivo.

    Tecnica de deteccion por Campo 5:
    - Si el campo 5 (indice 4) empieza con 'v' seguido de numeros -> formato simplificado (3 bloques)
    - Si no -> formato con descripcion (5 bloques)

    Args:
        base_name (str): Nombre base del archivo sin extension ni version

    Returns:
        bool: True si es formato con descripcion (5 bloques), False si es simplificado (3 bloques)
    """
    if not base_name:
        return False  # Por defecto, formato simplificado

    parts = base_name.split("_")

    # Verificar si el campo 5 (indice 4) es una version
    if len(parts) >= 5:
        field_5 = parts[4]
        # Si campo 5 empieza con 'v' seguido de numeros, es formato simplificado
        if field_5.startswith("v") and len(field_5) > 1 and field_5[1:].isdigit():
            return False  # Formato simplificado (3 bloques)
        else:
            return True  # Formato con descripcion (5 bloques)
    else:
        # Menos de 5 campos -> formato simplificado
        return False


def extract_shot_code(base_name):
    """
    Extrae el shot_code de un nombre base de archivo.
    Detecta automaticamente el formato y extrae el shot_code correcto.

    Args:
        base_name (str): Nombre base del archivo sin extension ni version

    Returns:
        str: Shot code extraido (PROYECTO_SEQ_SHOT o PROYECTO_SEQ_SHOT_DESC1_DESC2)
    """
    if not base_name:
        return ""

    parts = base_name.split("_")

    # Detectar formato
    has_description = detect_shotname_format(base_name)

    if has_description:
        # Formato con descripcion: tomar primeros 5 campos
        if len(parts) >= 5:
            shot_code = "_".join(parts[:5])
        else:
            # Fallback: usar todos los campos disponibles
            shot_code = "_".join(parts)
    else:
        # Formato simplificado: tomar primeros 3 campos
        if len(parts) >= 3:
            shot_code = "_".join(parts[:3])
        else:
            # Fallback: usar todos los campos disponibles
            shot_code = "_".join(parts)

    return shot_code


def extract_project_name(base_name):
    """
    Extrae el nombre del proyecto del nombre base del archivo.

    Args:
        base_name (str): Nombre base del archivo

    Returns:
        str: Nombre del proyecto (primer campo)
    """
    if not base_name:
        return ""

    parts = base_name.split("_")
    return parts[0] if parts else ""


def clean_base_name(file_name):
    """
    Limpia el nombre de archivo removiendo extensiones y versiones.

    Args:
        file_name (str): Nombre completo del archivo

    Returns:
        str: Nombre base limpio sin extension ni version
    """
    if not file_name:
        return ""

    # Remover extension de secuencia EXR
    base_name = re.sub(r"_%04d\.exr$", "", file_name)
    base_name = re.sub(r"_\d{4}\.exr$", "", base_name)  # Tambien formato sin %04d

    # Remover extension .nk y secuencias de frames _%04d.nk
    base_name = re.sub(r"_%04d\.nk$", "", base_name)
    base_name = re.sub(r"\.nk$", "", base_name)

    # Remover version al final (_v19, _v001, etc.)
    base_name = re.sub(r"_v\d+$", "", base_name)

    # Remover extension comun
    base_name = os.path.splitext(base_name)[0]

    return base_name


def extract_task_name(base_name):
    """
    Extrae el nombre de la tarea del nombre base del archivo.

    Args:
        base_name (str): Nombre base del archivo sin extension ni version

    Returns:
        str: Nombre de la tarea o None si no se encuentra
    """
    if not base_name:
        return None

    parts = base_name.split("_")

    # Detectar formato
    has_description = detect_shotname_format(base_name)

    if has_description:
        # Formato con descripcion: task esta en el campo 6 (indice 5)
        # Estructura: PROYECTO_SEQ_SHOT_DESC1_DESC2_TASK_vVERSION
        if len(parts) >= 6:
            return parts[5]
    else:
        # Formato simplificado: task esta en el campo 4 (indice 3)
        # Estructura: PROYECTO_SEQ_SHOT_TASK_vVERSION
        if len(parts) >= 4:
            return parts[3]

    return None


def get_script_base_name():
    """
    Obtiene el nombre base del script actual de Nuke sin extension ni version.
    Util para scripts que necesitan detectar el formato del shotname.

    Returns:
        str: Nombre base del script o None si no hay script guardado
    """
    try:
        import nuke

        script_path = nuke.root().name()
        if not script_path or script_path == "Root":
            return None

        script_name = os.path.basename(script_path)
        base_name = clean_base_name(script_name)
        return base_name
    except ImportError:
        # Nuke no disponible
        return None
    except Exception:
        return None
