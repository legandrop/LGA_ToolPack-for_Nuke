"""
_______________________________________________________________________________________________________________________________

  LGA_Write_Presets_Check v2.66 | Lega
  Script para mostrar una ventana de verificación del path normalizado antes de crear un Write node.
  Se usa cuando el usuario hace Shift+Click sobre un preset o edita Writes existentes.

  v2.65: PathCheckWindow ahora hereda de QDialog en lugar de QWidget para comportamiento modal.
         Permite editar Writes existentes desde el boton "Show selected Write node file path".

  v2.64: Greyed out items in the table when the script is not saved.

  v2.63: Color coding for original extensions in the path.

  v2.62: UI improvements.

  v1.22: Flag para ocultar el TCL path original.
         - Agregada flag SHOW_ORIGINAL_TCL_PATH (por defecto False)
         - Cuando esta en False, el TCL path original no se muestra en la ventana
         - El path final normalizado siempre se muestra

  v1.21: Path dividido en 3 o 4 lineas segun corresponda.
         - Detecta si el path es una secuencia (busca %04d, %03d, etc.)
         - Si es secuencia: tercera linea muestra subcarpeta (con / al final), cuarta linea muestra archivo
         - Si NO es secuencia: tercera linea muestra solo el archivo
         - Aplica tanto al TCL path original como al path final normalizado

  v1.20: Edición de indices ajustables en tiempo real implementada.
         - Detecta si el preset tiene indices ajustables en expresiones lrange
         - Control custom con numero y botones triangulares (▲ ▼) para editar el indice
         - Actualiza path final normalizado en tiempo real con debounce
         - Muestra mensaje informativo cuando no hay indices ajustables
         - Soporte para ESC (cancelar) y Enter (aceptar)
_______________________________________________________________________________________________________________________________
"""

import nuke
import os
import re
from qt_compat import QtWidgets, QtCore

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QDialog = QtWidgets.QDialog
QVBoxLayout = QtWidgets.QVBoxLayout
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QHBoxLayout = QtWidgets.QHBoxLayout
Qt = QtCore.Qt
QTimer = QtCore.QTimer

# Importar funciones de LGA_Write_PathToText para reutilizar (ahora definidas localmente)
try:
    from LGA_Write_PathToText import (
        apply_path_coloring,
        normalize_path_preserve_case,
        get_color_for_level,
    )
except ImportError:
    # Si no se puede importar, usar funciones locales (desde v2.66)
    def get_color_for_level(level):
        colors = {
            0: "#ffff66",
            1: "#28b5b5",
            2: "#ff9a8a",
            3: "#0088ff",
            4: "#ffd369",
            5: "#28b5b5",
            6: "#ff9a8a",
            7: "#6bc9ff",
            8: "#ffd369",
            9: "#28b5b5",
            10: "#ff9a8a",
            11: "#6bc9ff",
        }
        return colors.get(level, "#AEAEAE")

    def apply_path_coloring(path, shot_folder_parts):
        if not path:
            return path
        parts = path.replace("\\", "/").split("/")
        colored_parts = []
        parts_lower = [part.lower() for part in parts]
        for i, part in enumerate(parts[:-1]):
            part_lower = parts_lower[i]
            within_shot_range = i < len(shot_folder_parts)
            matches_shot_part = within_shot_range and part_lower == shot_folder_parts[i]
            if i >= len(shot_folder_parts) or part_lower != shot_folder_parts[i]:
                text_color = get_color_for_level(i)
            else:
                text_color = "#c56cf0"
            colored_parts.append(f"<span style='color: {text_color};'>{part}</span>")
        if len(parts) > 0:
            file_name = f"<span style='color: #ffff66;'>{parts[-1]}</span>"
            colored_parts.append(file_name)
        colored_text = '<span style="color: white;">/</span>'.join(colored_parts)
        return colored_text

    def normalize_path_preserve_case(path):
        if not path:
            return path
        normalized_separators = path.replace("\\", "/")
        parts = normalized_separators.split("/")
        resolved_parts = []
        for part in parts:
            if part == "." or part == "":
                if (
                    part == ""
                    and len(resolved_parts) == 0
                    and normalized_separators.startswith("/")
                ):
                    resolved_parts.append(part)
                continue
            elif part == "..":
                if (
                    resolved_parts
                    and resolved_parts[-1] != ".."
                    and resolved_parts[-1] != ""
                ):
                    resolved_parts.pop()
                else:
                    resolved_parts.append(part)
            else:
                resolved_parts.append(part)
        result = "/".join(resolved_parts)
        if normalized_separators.startswith("/") and not result.startswith("/"):
            result = "/" + result
        return result


# Variable global para activar o desactivar los debug_prints
DEBUG = True

# Flag para mostrar/ocultar el TCL path original
SHOW_ORIGINAL_TCL_PATH = False

app = None
window = None


def debug_print(*message):
    if DEBUG:
        print("[LGA_Write_Presets_Check]", *message)


def get_topnode_file_path(temp_write):
    """
    Obtiene el path del archivo del topnode desde un Write temporal.
    Busca recursivamente el nodo Read mas alto en las dependencias.
    Retorna el path del archivo o None si no se puede obtener.
    """
    try:
        if not temp_write.input(0):
            return None

        input_node = temp_write.input(0)

        # Buscar recursivamente el Read mas alto en las dependencias
        def find_read(node):
            if node is None:
                return None
            if node.Class() == "Read":
                return node
            # Buscar en todos los inputs del nodo
            for i in range(node.inputs()):
                if node.input(i):
                    result = find_read(node.input(i))
                    if result:
                        return result
            return None

        read_node = find_read(input_node)
        if read_node:
            file_path = read_node["file"].value()
            if file_path:
                debug_print(f"Topnode file path encontrado: {file_path}")
                return file_path
    except Exception as e:
        debug_print(f"Error al obtener topnode file path: {e}")

    return None


def extract_original_extension(file_path):
    """
    Extrae la extension original del archivo, incluyendo el patron de frames si es secuencia.
    Retorna una lista de posibles extensiones a buscar (con y sin frames).
    Ejemplo: si el archivo es "shot.%04d.exr", retorna [".%04d.exr", ".exr"]
    """
    if not file_path:
        return []

    # Obtener el nombre del archivo
    file_name = os.path.basename(file_path)

    # Buscar patrones de secuencia como %04d, %03d, etc.
    sequence_pattern = re.search(r"(%0\d+d)", file_name)

    extensions = []

    if sequence_pattern:
        # Si tiene patron de secuencia, extraer desde el punto antes del patron hasta el final
        pattern_start = sequence_pattern.start()
        # Buscar el punto mas cercano antes del patron
        dot_before = file_name.rfind(".", 0, pattern_start)
        if dot_before >= 0:
            # Extension completa con frames: .%04d.exr
            full_extension = file_name[dot_before:]
            extensions.append(full_extension)

            # Tambien buscar la extension sin el patron de frames: .exr
            # Reemplazar el patron de frames con cualquier numero para encontrar la extension final
            temp_name = file_name.replace(sequence_pattern.group(1), "0001")
            ext_match = re.search(r"\.([^.]+)$", temp_name)
            if ext_match:
                simple_ext = "." + ext_match.group(1)
                if simple_ext not in extensions:
                    extensions.append(simple_ext)
    else:
        # Si no tiene patron de secuencia, solo extraer la extension normal
        ext_match = re.search(r"\.([^.]+)$", file_name)
        if ext_match:
            extensions.append("." + ext_match.group(1))

    debug_print(f"Extensiones originales extraidas de '{file_name}': {extensions}")
    return extensions


def evaluate_file_pattern(file_pattern):
    """
    Evalua una expresion TCL file_pattern sin crear un Write node permanente.
    Crea un Write temporal solo para evaluar el path y luego lo elimina.
    Retorna una tupla (evaluated_path, original_extensions) donde:
    - evaluated_path: el path evaluado o None si hay error
    - original_extensions: lista de extensiones originales del topnode o lista vacia
    """
    if not file_pattern:
        return None, []

    try:
        # Obtener el nodo seleccionado o crear un NoOp temporal para tener contexto
        selected_node = None
        try:
            selected_node = nuke.selectedNode()
        except ValueError:
            pass

        # Crear un Write temporal solo para evaluar el path
        # Esto es necesario porque algunas expresiones TCL de Nuke requieren un nodo para evaluarse
        temp_write = nuke.nodes.Write()

        # Conectar el Write temporal al nodo seleccionado si existe
        # Esto asegura que [topnode] funcione correctamente
        if selected_node:
            temp_write.setInput(0, selected_node)

        temp_write["file"].setValue(file_pattern)

        # Obtener el path del topnode ANTES de evaluar (necesitamos el Write conectado)
        topnode_file_path = get_topnode_file_path(temp_write)
        original_extensions = []
        if topnode_file_path:
            original_extensions = extract_original_extension(topnode_file_path)

        # Evaluar el path usando nuke.filename()
        evaluated_path = nuke.filename(temp_write)

        # Si evaluated_path es None, usar cadena vacia
        if evaluated_path is None:
            evaluated_path = ""

        # Eliminar el Write temporal inmediatamente
        nuke.delete(temp_write)

        debug_print(f"File pattern original: {file_pattern}")
        debug_print(f"Path evaluado: {evaluated_path}")
        debug_print(f"Extensiones originales detectadas: {original_extensions}")

        return (evaluated_path if evaluated_path else None, original_extensions)
    except Exception as e:
        debug_print(f"Error al evaluar file_pattern: {e}")
        # Asegurarse de eliminar el Write temporal incluso si hay error
        try:
            if "temp_write" in locals():
                nuke.delete(temp_write)
        except:
            pass
        return None, []


def get_shot_folder_parts(script_path):
    """
    Calcula las partes de la ruta del shot para el coloreado.
    Reutiliza la logica de coloreado de paths (originalmente de LGA_Write_PathToText).
    """
    shot_folder_parts = []
    if script_path and script_path != "Root":
        project_folder_depth = 3  # Niveles a subir desde el script
        shot_folder = script_path
        for _ in range(project_folder_depth):
            shot_folder = os.path.dirname(shot_folder)
        if shot_folder:
            shot_dir = shot_folder.replace("\\", "/").lower()
            shot_folder_parts = shot_dir.split("/")
    return shot_folder_parts


def is_sequence_pattern(pattern):
    """
    Detecta si un pattern (TCL o path) contiene una secuencia de cuadros.
    Busca patrones como %04d, %03d, %05d, etc.
    Retorna True si es una secuencia, False si no.
    """
    if not pattern:
        return False
    # Buscar patrones %0Xd donde X es un numero
    return bool(re.search(r"%0\d+d", pattern))


def has_adjustable_indices(file_pattern):
    """
    Detecta si el file_pattern tiene indices ajustables en expresiones lrange.
    Retorna (bool, int) donde bool indica si hay indices y int es el valor actual.
    Si hay multiples indices, todos deben tener el mismo valor.
    """
    if not file_pattern:
        return False, None

    # Buscar patrones ] 0 X] donde X es el numero ajustable
    matches = re.findall(r"\] 0 (\d+)\s*\]", file_pattern)
    if not matches:
        return False, None

    # Verificar que todos los valores sean iguales
    values = [int(m) for m in matches]
    if len(set(values)) == 1:
        return True, values[0]
    else:
        # Caso raro: valores diferentes, usar el primero
        debug_print(
            f"Advertencia: Se encontraron valores diferentes en indices: {values}"
        )
        return True, values[0]


def replace_indices_in_pattern(file_pattern, new_index):
    """
    Reemplaza todos los indices ajustables en el file_pattern con el nuevo valor.
    Busca patrones ] 0 X] y los reemplaza por ] 0 new_index].
    Preserva el formato original (espacios antes del ultimo ]).
    """
    if not file_pattern:
        return file_pattern

    def replace_index(match):
        # Preservar el formato original (con o sin espacio antes del ultimo ])
        has_space = match.group(0).endswith(" ]")
        return f"] 0 {new_index} ]" if has_space else f"] 0 {new_index}]"

    # Reemplazar todos los indices
    modified_pattern = re.sub(r"\] 0 (\d+)\s*\]", replace_index, file_pattern)
    return modified_pattern


def has_directory_levels(file_pattern):
    """
    Detecta si el file_pattern tiene niveles de directorio (../ o ../../, etc).
    Retorna (bool, int) donde bool indica si hay niveles y int es la cantidad actual.
    Busca patrones ../ seguidos opcionalmente por más ../.
    """
    if not file_pattern:
        return False, None

    # Buscar todos los patrones ../ seguidos usando finditer para obtener el texto completo
    # Buscamos ../ que aparezcan juntos (como ../../ o ../../../)
    matches = list(re.finditer(r"(\.\./)+", file_pattern))
    debug_print(f"has_directory_levels - matches encontrados: {len(matches)}")
    if not matches:
        return False, None

    # Contar la cantidad máxima de ../ consecutivos
    max_levels = 0
    for match in matches:
        # Obtener el texto completo del match (puede ser ../, ../../, ../../../, etc)
        match_text = match.group(0)
        # Contar cuantos ../ hay en este match
        levels = match_text.count("../")
        debug_print(
            f"has_directory_levels - match: '{match_text}', niveles contados: {levels}"
        )
        max_levels = max(max_levels, levels)

    debug_print(f"has_directory_levels - max_levels final: {max_levels}")
    if max_levels > 0:
        return True, max_levels
    return False, None


def replace_directory_levels(file_pattern, new_level):
    """
    Reemplaza los niveles de directorio en el file_pattern con el nuevo valor.
    Busca patrones ../ (repetidos) y los reemplaza por la cantidad especificada.
    Si new_level es 0, elimina todos los ../.
    Si new_level es mayor a 0, reemplaza por new_level veces ../.
    """
    if not file_pattern:
        return file_pattern

    if new_level < 0:
        new_level = 0

    # Crear el reemplazo
    replacement = "../" * new_level if new_level > 0 else ""

    # Buscar y reemplazar todos los patrones de ../ consecutivos
    # Usamos una funcion para reemplazar cada ocurrencia
    def replace_levels(match):
        return replacement

    # Reemplazar todos los patrones ../+ con el nuevo nivel
    modified_pattern = re.sub(r"(\.\./)+", replacement, file_pattern)
    return modified_pattern


def mark_original_extension_in_part(part, original_extensions, is_final_file=False):
    """
    Marca en rojo solo la parte específica que contiene extensiones originales heredadas.
    No marca extensiones propias del archivo final.

    Args:
        part: Parte del path a analizar (texto plano, sin HTML)
        original_extensions: Lista de extensiones originales del topnode
        is_final_file: Si es True, es el archivo final y tiene su propia extensión/frame

    Retorna:
        String HTML con solo las partes problemáticas marcadas en rojo dentro de spans,
        el resto del texto queda sin envolver para que se pueda aplicar el color base después
    """
    if not part or not original_extensions:
        return part

    # Si es el archivo final, verificar si tiene su propia extensión/frame
    # En ese caso, solo marcar extensiones heredadas que aparezcan ANTES de la extensión propia
    if is_final_file:
        # Buscar el último patrón de frame propio seguido de extensión (como _%04d.exr al final)
        # Esto identifica la extensión propia del archivo final
        # Buscamos un guion bajo o punto, seguido de %0Xd, seguido de .ext al final
        own_ext_pattern = re.search(r"[._]%0\d+d\.([^.]+)$", part)

        if own_ext_pattern:
            # Encontrar donde empieza la extensión propia (el frame pattern antes de la extensión)
            own_ext_start = own_ext_pattern.start()

            # Solo buscar extensiones heredadas antes de la extensión propia
            part_before_own = part[:own_ext_start]
            part_own = part[own_ext_start:]

            # Marcar extensiones heredadas en la parte antes de la extensión propia
            marked_part = part_before_own
            for ext in original_extensions:
                if ext.lower() in part_before_own.lower():
                    # Encontrar todas las ocurrencias y marcarlas en rojo
                    pattern = re.escape(ext)
                    marked_part = re.sub(
                        pattern,
                        lambda m: f"<span style='color: #ff0000;'>{m.group(0)}</span>",
                        marked_part,
                        flags=re.IGNORECASE,
                    )

            # Retornar la parte marcada + la parte propia sin modificar
            return marked_part + part_own
        else:
            # Si no tiene patrón de frame propio, buscar solo extensión al final
            own_ext_match = re.search(r"\.([^.]+)$", part)
            if own_ext_match:
                ext_start = own_ext_match.start()
                part_before_own = part[:ext_start]
                part_own = part[ext_start:]

                # Marcar extensiones heredadas en la parte antes de la extensión propia
                marked_part = part_before_own
                for ext in original_extensions:
                    if ext.lower() in part_before_own.lower():
                        pattern = re.escape(ext)
                        marked_part = re.sub(
                            pattern,
                            lambda m: f"<span style='color: #ff0000;'>{m.group(0)}</span>",
                            marked_part,
                            flags=re.IGNORECASE,
                        )

                return marked_part + part_own

    # Si no es archivo final o no tiene extensión propia, marcar todas las extensiones heredadas
    marked_part = part
    for ext in original_extensions:
        if ext.lower() in part.lower():
            # Encontrar todas las ocurrencias y marcarlas en rojo
            pattern = re.escape(ext)
            marked_part = re.sub(
                pattern,
                lambda m: f"<span style='color: #ff0000;'>{m.group(0)}</span>",
                marked_part,
                flags=re.IGNORECASE,
            )

    return marked_part


def split_path_at_violet_end(
    path, shot_folder_parts, is_sequence=False, original_extensions=None
):
    """
    Divide un path en partes: la parte violeta (que coincide con shot_folder_parts),
    la parte intermedia, y la parte final.
    Si es secuencia: retorna (violet_part, middle_part, subfolder_part, file_part) - 4 partes
    Si NO es secuencia: retorna (violet_part, middle_part, file_part, "") - 3 partes (ultima vacia)
    Todas las partes son strings HTML con colores.
    Los segmentos que contengan extensiones originales se marcan en rojo (#ff0000).

    Args:
        path: Path a dividir
        shot_folder_parts: Partes del shot folder para coloreado violeta
        is_sequence: Si el path es una secuencia
        original_extensions: Lista de extensiones originales del topnode para detectar problemas
    """
    if not path:
        if is_sequence:
            return path, "", "", ""
        else:
            return path, "", ""

    if original_extensions is None:
        original_extensions = []

    parts = path.replace("\\", "/").split("/")
    parts_lower = [part.lower() for part in parts]

    # Encontrar donde termina la parte violeta (donde coinciden con shot_folder_parts)
    violet_end_index = len(shot_folder_parts)
    for i in range(min(len(parts) - 1, len(shot_folder_parts))):
        if parts_lower[i] != shot_folder_parts[i]:
            violet_end_index = i
            break

    # Construir parte violeta hasta donde termina EXACTAMENTE (sin incluir el siguiente directorio)
    # La parte violeta va desde el inicio hasta violet_end_index (sin incluir el siguiente)
    if violet_end_index < len(parts) - 1:
        violet_parts = parts[:violet_end_index]
        rest_parts = parts[violet_end_index:]
    else:
        # Si toda la parte violeta incluye todo hasta el archivo, no hay resto
        violet_parts = parts
        rest_parts = []

    # Aplicar coloreado a la parte violeta (todos los directorios son violeta)
    colored_violet = []
    for i, part in enumerate(violet_parts):
        colored_violet.append(f"<span style='color: #c56cf0;'>{part}</span>")

    violet_str = '<span style="color: white;">/</span>'.join(colored_violet)
    # Agregar / al final si hay resto
    if rest_parts and violet_parts:
        violet_str += '<span style="color: white;">/</span>'

    # Dividir el resto en parte intermedia y parte final
    middle_str = ""
    subfolder_str = ""
    file_str = ""

    if rest_parts:
        if is_sequence and len(rest_parts) >= 2:
            # Si es secuencia: parte intermedia son todas las carpetas excepto las ultimas 2
            # Subcarpeta es la penultima
            # Archivo es la ultima
            middle_parts = rest_parts[:-2]
            subfolder_part = rest_parts[-2] if len(rest_parts) >= 2 else ""
            file_part = rest_parts[-1] if rest_parts else ""

            # Aplicar coloreado a la parte intermedia (violeta base, con extensiones heredadas en rojo)
            if middle_parts:
                colored_middle = []
                for part in middle_parts:
                    # Aplicar color violeta base y luego marcar extensiones heredadas en rojo
                    marked_part = mark_original_extension_in_part(
                        part, original_extensions, is_final_file=False
                    )
                    colored_middle.append(
                        f"<span style='color: #c56cf0;'>{marked_part}</span>"
                    )
                middle_str = '<span style="color: white;">/</span>'.join(colored_middle)
                if subfolder_part:
                    middle_str += '<span style="color: white;">/</span>'

            # Aplicar coloreado a la subcarpeta (color #6bc9ff base, con extensiones heredadas en rojo)
            if subfolder_part:
                marked_subfolder = mark_original_extension_in_part(
                    subfolder_part, original_extensions, is_final_file=False
                )
                subfolder_str = (
                    f"<span style='color: #6bc9ff;'>{marked_subfolder}</span>"
                    '<span style="color: white;">/</span>'
                )

            # Aplicar coloreado al archivo (color #6bc9ff base, con extensiones heredadas en rojo)
            # El archivo final tiene su propia extensión/frame, así que solo marcamos extensiones heredadas
            if file_part:
                marked_file = mark_original_extension_in_part(
                    file_part, original_extensions, is_final_file=True
                )
                file_str = f"<span style='color: #6bc9ff;'>{marked_file}</span>"
        else:
            # Si NO es secuencia: parte intermedia son todas las carpetas excepto el archivo
            # Parte final es solo el archivo
            middle_parts = rest_parts[:-1]
            file_part = rest_parts[-1] if rest_parts else ""

            # Aplicar coloreado a la parte intermedia (violeta base, con extensiones heredadas en rojo)
            if middle_parts:
                colored_middle = []
                for part in middle_parts:
                    # Aplicar color violeta base y luego marcar extensiones heredadas en rojo
                    marked_part = mark_original_extension_in_part(
                        part, original_extensions, is_final_file=False
                    )
                    colored_middle.append(
                        f"<span style='color: #c56cf0;'>{marked_part}</span>"
                    )
                middle_str = '<span style="color: white;">/</span>'.join(colored_middle)
                if file_part:
                    middle_str += '<span style="color: white;">/</span>'

            # Aplicar coloreado al archivo (color #6bc9ff base, con extensiones heredadas en rojo)
            # El archivo final tiene su propia extensión/frame, así que solo marcamos extensiones heredadas
            if file_part:
                marked_file = mark_original_extension_in_part(
                    file_part, original_extensions, is_final_file=True
                )
                file_str = f"<span style='color: #6bc9ff;'>{marked_file}</span>"

    if is_sequence:
        return violet_str, middle_str, subfolder_str, file_str
    else:
        return violet_str, middle_str, file_str, ""


def split_tcl_path_at_shot_end(tcl_path, shot_folder_parts, is_sequence=False):
    """
    Divide el TCL path en partes basandose en donde termina la parte del shot.
    Busca patrones comunes que indican salida del shot folder (como ../2_prerenders, ../4_publish, etc).
    Si es secuencia: retorna (violet_part, middle_part, subfolder_part, file_part) - 4 partes
    Si NO es secuencia: retorna (violet_part, middle_part, file_part, "") - 3 partes (ultima vacia)
    """
    if not tcl_path:
        if is_sequence:
            return tcl_path, "", "", ""
        else:
            return tcl_path, "", ""

    # Buscar patrones que indican salida del shot folder
    # Patrones comunes: ../2_prerenders, ../3_review, ../4_publish, etc.
    # O buscar el primer ../ seguido de un numero y guion bajo

    # Buscar el primer patron ../X_ donde X es un numero
    pattern_match = re.search(r"(\.\./[0-9]+_)", tcl_path)
    if pattern_match:
        split_pos = pattern_match.start()
        # Buscar el / anterior mas cercano para dividir mejor
        prev_slash = tcl_path.rfind("/", 0, split_pos)
        if prev_slash > 0:
            violet_part = tcl_path[:prev_slash]
            rest_part = tcl_path[prev_slash + 1 :]
        else:
            violet_part = tcl_path[:split_pos]
            rest_part = tcl_path[split_pos:]
    else:
        # Si no encontramos el patron, buscar el primer ../ que aparece
        first_dotdot = tcl_path.find("../")
        if first_dotdot > 0:
            # Buscar el / anterior mas cercano
            prev_slash = tcl_path.rfind("/", 0, first_dotdot)
            if prev_slash > 0:
                violet_part = tcl_path[:prev_slash]
                rest_part = tcl_path[prev_slash + 1 :]
            else:
                violet_part = tcl_path[:first_dotdot]
                rest_part = tcl_path[first_dotdot:]
        else:
            # Si no encontramos nada, dividir aproximadamente al 60% buscando el / mas cercano
            split_point = int(len(tcl_path) * 0.6)
            nearest_slash = tcl_path.rfind("/", 0, split_point)
            if nearest_slash > 0:
                violet_part = tcl_path[:nearest_slash]
                rest_part = tcl_path[nearest_slash + 1 :]
            else:
                violet_part = tcl_path
                rest_part = ""

    # Agregar / al final de violet_part si hay resto
    if rest_part and violet_part:
        violet_part = violet_part + "/"

    # Dividir el resto en parte intermedia y parte final
    if not rest_part:
        if is_sequence:
            return violet_part, "", "", ""
        else:
            return violet_part, "", ""

    # Dividir por / para obtener las partes
    rest_parts = rest_part.split("/")

    if is_sequence and len(rest_parts) >= 2:
        # Si es secuencia: parte intermedia son todas las carpetas excepto las ultimas 2
        # Subcarpeta es la penultima
        # Archivo es la ultima
        middle_parts = rest_parts[:-2]
        subfolder_part = rest_parts[-2] if len(rest_parts) >= 2 else ""
        file_part = rest_parts[-1] if rest_parts else ""

        middle_str = "/".join(middle_parts) if middle_parts else ""
        # Agregar / al final si hay subcarpeta
        if subfolder_part and middle_str:
            middle_str = middle_str + "/"
        subfolder_str = f"{subfolder_part}/" if subfolder_part else ""
        file_str = file_part if file_part else ""

        return violet_part, middle_str, subfolder_str, file_str
    else:
        # Si NO es secuencia: parte intermedia son todas las carpetas excepto el archivo
        # Parte final es solo el archivo
        middle_parts = rest_parts[:-1]
        file_part = rest_parts[-1] if rest_parts else ""

        middle_str = "/".join(middle_parts) if middle_parts else ""
        # Agregar / al final si hay archivo
        if file_part and middle_str:
            middle_str = middle_str + "/"
        file_str = file_part if file_part else ""

        return violet_part, middle_str, file_str, ""


class PathCheckWindow(QDialog):
    """
    Ventana de verificacion que muestra el TCL path original y el path final normalizado.
    Permite editar indices ajustables en tiempo real si el preset los tiene.
    """

    def __init__(
        self,
        file_pattern,
        normalized_path,
        shot_folder_parts,
        callback=None,
        original_extensions=None,
    ):
        super().__init__()
        self.callback = callback
        self.original_file_pattern = file_pattern
        self.current_file_pattern = file_pattern
        self.shot_folder_parts = shot_folder_parts
        # Guardara el file_pattern modificado solo si el usuario cambia el indice
        # Si es None, se usara el patrón original del preset
        self.modified_file_pattern = None
        # Extensiones originales del topnode para detectar problemas
        self.original_extensions = original_extensions if original_extensions else []

        # Detectar si hay indices ajustables
        self.has_adjustable, self.current_index = has_adjustable_indices(file_pattern)

        # Detectar si hay niveles de directorio
        self.has_dir_levels, self.current_dir_level = has_directory_levels(file_pattern)
        if not self.has_dir_levels:
            self.current_dir_level = 1  # Valor por defecto si no se detecta

        # Logs iniciales
        naming_segments = (
            self.current_index
            if self.has_adjustable and self.current_index is not None
            else "N/A"
        )
        folder_up_levels = (
            self.current_dir_level if self.has_dir_levels else self.current_dir_level
        )
        debug_print(f"Naming Segments: {naming_segments}")
        debug_print(f"Folder Up Levels: {folder_up_levels}")

        # Timer para actualizacion en tiempo real (debounce)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_paths)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle("Write Path Review")
        self.setStyleSheet("background-color: #212121; border-radius: 10px;")

        # Configurar el diálogo para que sea modal
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        def add_block(title, value, rich=False, is_section=False):
            """
            Crea un bloque con titulo y valor.
            """
            block_layout = QVBoxLayout()
            block_layout.setSpacing(8)
            block_layout.setContentsMargins(0, 0, 0, 0)

            # Contenedor para el contenido de la seccion con fondo
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(12, 10, 12, 10)
            content_layout.setSpacing(6)

            # Titulo con estilo mejorado
            title_label = QLabel(
                f"<span style='color:#E8E8E8; font-size:13px; letter-spacing:0.5px; text-transform:uppercase;'>{title}</span>"
            )
            title_label.setStyleSheet("font-size:13px; padding-bottom:2px;")
            content_layout.addWidget(title_label)

            # Valor con padding adicional
            if rich:
                value_label = QLabel(value)
            else:
                value_label = QLabel(f"<span style='color:#AEAEAE;'>{value}</span>")
            value_label.setStyleSheet("font-size:13px; padding:4px 0px;")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

            # Fondo sutil para la seccion (sin border)
            content_widget.setStyleSheet(
                """
                QWidget {
                    background-color: #292929;
                    border-radius: 6px;
                }
            """
            )

            content_layout.addWidget(value_label)
            block_layout.addWidget(content_widget)
            layout.addLayout(block_layout)

            return value_label  # Retornar el label para poder actualizarlo

        # Agregar controles de edicion (siempre se muestran)
        # Contenedor principal con fondo (sin border)
        index_container = QWidget()
        index_container.setStyleSheet(
            """
            QWidget {
                background-color: #292929;
                border-radius: 6px;
            }
        """
        )

        index_layout = QHBoxLayout(index_container)
        index_layout.setSpacing(12)
        index_layout.setContentsMargins(12, 10, 12, 10)

        # Primera columna: Naming Segments (siempre visible)
        naming_title_color = "#E8E8E8" if self.has_adjustable else "#666666"
        naming_title = QLabel(
            f"<span style='color:{naming_title_color}; font-size:13px; letter-spacing:0.5px; text-transform:uppercase;'>Naming Segments</span>"
        )
        naming_title.setStyleSheet("font-size:13px;")
        index_layout.addWidget(naming_title)

        # Contenedor para el numero y botones de Naming Segments
        naming_control_layout = QHBoxLayout()
        naming_control_layout.setSpacing(2)
        naming_control_layout.setContentsMargins(0, 0, 0, 0)

        # Label con el numero (muestra N/A si no hay indices ajustables)
        naming_display_value = (
            str(self.current_index)
            if self.has_adjustable and self.current_index is not None
            else "N/A"
        )
        self.index_label = QLabel(naming_display_value)
        self.index_label.setFixedSize(28, 24)
        # Estilo diferente si esta deshabilitado
        if self.has_adjustable:
            index_label_style = """
                QLabel {
                    background-color: #3e3e3e;
                    color: #CCCCCC;
                    border: none;
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 0px;
                    border-bottom-right-radius: 0px;
                    padding: 0px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """
        else:
            index_label_style = """
                QLabel {
                    background-color: #2a2a2a;
                    color: #666666;
                    border: none;
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 0px;
                    border-bottom-right-radius: 0px;
                    padding: 0px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """
        self.index_label.setStyleSheet(index_label_style)
        self.index_label.setAlignment(Qt.AlignCenter)
        naming_control_layout.addWidget(self.index_label)

        # Contenedor vertical para los botones
        naming_buttons_container = QWidget()
        naming_buttons_layout = QVBoxLayout(naming_buttons_container)
        naming_buttons_layout.setSpacing(0)
        naming_buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Boton triangulo arriba
        self.up_button = QPushButton("▲")
        self.up_button.setFixedSize(24, 12)
        if self.has_adjustable:
            up_button_style = """
                QPushButton {
                    background-color: #3e3e3e;
                    color: #CCCCCC;
                    border: none;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 4px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                    font-size: 8px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #4e4e4e;
                }
                QPushButton:pressed {
                    background-color: #2e2e2e;
                }
            """
        else:
            up_button_style = """
                QPushButton {
                    background-color: #2a2a2a;
                    color: #666666;
                    border: none;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 4px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                    font-size: 8px;
                    font-weight: bold;
                    padding: 0px;
                }
            """
        self.up_button.setStyleSheet(up_button_style)
        self.up_button.setEnabled(self.has_adjustable)
        self.up_button.clicked.connect(self.increment_index)
        naming_buttons_layout.addWidget(self.up_button)

        # Boton triangulo abajo
        self.down_button = QPushButton("▼")
        self.down_button.setFixedSize(24, 12)
        if self.has_adjustable:
            down_button_style = """
                QPushButton {
                    background-color: #3e3e3e;
                    color: #CCCCCC;
                    border: none;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 4px;
                    font-size: 8px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #4e4e4e;
                }
                QPushButton:pressed {
                    background-color: #2e2e2e;
                }
            """
        else:
            down_button_style = """
                QPushButton {
                    background-color: #2a2a2a;
                    color: #666666;
                    border: none;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 4px;
                    font-size: 8px;
                    font-weight: bold;
                    padding: 0px;
                }
            """
        self.down_button.setStyleSheet(down_button_style)
        self.down_button.setEnabled(self.has_adjustable)
        self.down_button.clicked.connect(self.decrement_index)
        naming_buttons_layout.addWidget(self.down_button)

        naming_control_layout.addWidget(naming_buttons_container)

        # Widget contenedor para el control de Naming Segments
        naming_control_widget = QWidget()
        naming_control_widget.setLayout(naming_control_layout)
        index_layout.addWidget(naming_control_widget)

        # Agregar stretch para separar las dos columnas
        index_layout.addStretch()

        # Segunda columna: Folder Up Levels (siempre visible y habilitada)
        upward_title = QLabel(
            "<span style='color:#E8E8E8; font-size:13px; letter-spacing:0.5px; text-transform:uppercase;'>FOLDER UP LEVELS</span>"
        )
        upward_title.setStyleSheet("font-size:13px;")
        index_layout.addWidget(upward_title)

        # Contenedor para el numero y botones de Upward Levels
        upward_control_layout = QHBoxLayout()
        upward_control_layout.setSpacing(2)
        upward_control_layout.setContentsMargins(0, 0, 0, 0)

        # Label con el numero (muestra el valor detectado o 1 por defecto)
        self.upward_level_label = QLabel(str(self.current_dir_level))
        self.upward_level_label.setFixedSize(28, 24)
        self.upward_level_label.setStyleSheet(
            """
            QLabel {
                background-color: #3e3e3e;
                color: #CCCCCC;
                border: none;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 0px;
                font-size: 13px;
                font-weight: bold;
            }
        """
        )
        self.upward_level_label.setAlignment(Qt.AlignCenter)
        upward_control_layout.addWidget(self.upward_level_label)

        # Contenedor vertical para los botones de Upward Levels
        upward_buttons_container = QWidget()
        upward_buttons_layout = QVBoxLayout(upward_buttons_container)
        upward_buttons_layout.setSpacing(0)
        upward_buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Boton triangulo arriba para Upward Levels
        self.upward_up_button = QPushButton("▲")
        self.upward_up_button.setFixedSize(24, 12)
        self.upward_up_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3e3e3e;
                color: #CCCCCC;
                border: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 4px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                font-size: 8px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
            QPushButton:pressed {
                background-color: #2e2e2e;
            }
        """
        )
        self.upward_up_button.clicked.connect(self.increment_upward_level)
        upward_buttons_layout.addWidget(self.upward_up_button)

        # Boton triangulo abajo para Upward Levels
        self.upward_down_button = QPushButton("▼")
        self.upward_down_button.setFixedSize(24, 12)
        self.upward_down_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3e3e3e;
                color: #CCCCCC;
                border: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 4px;
                font-size: 8px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
            QPushButton:pressed {
                background-color: #2e2e2e;
            }
        """
        )
        self.upward_down_button.clicked.connect(self.decrement_upward_level)
        upward_buttons_layout.addWidget(self.upward_down_button)

        upward_control_layout.addWidget(upward_buttons_container)

        # Widget contenedor para el control de Upward Levels
        upward_control_widget = QWidget()
        upward_control_widget.setLayout(upward_control_layout)
        index_layout.addWidget(upward_control_widget)

        # Guardar valores minimo y maximo para Naming Segments
        self.min_index = 0
        self.max_index = 20

        # Guardar valores minimo y maximo para Dir Levels
        self.min_dir_level = 0
        self.max_dir_level = 5

        layout.addWidget(index_container)
        layout.addSpacing(8)  # Espacio antes de la siguiente seccion

        # Mostrar TCL path original solo si la flag esta activada
        if SHOW_ORIGINAL_TCL_PATH:
            # Detectar si es una secuencia
            is_seq = is_sequence_pattern(file_pattern)

            # Mostrar TCL path original (despues del control de indice) con 3 o 4 lineas
            tcl_result = split_tcl_path_at_shot_end(
                file_pattern, shot_folder_parts, is_sequence=is_seq
            )

            # Desempaquetar segun si es secuencia o no
            tcl_violet = tcl_result[0]
            tcl_middle = tcl_result[1]
            if is_seq and len(tcl_result) >= 4:
                tcl_subfolder = tcl_result[2]
                tcl_file = tcl_result[3]
            else:
                tcl_subfolder = ""
                tcl_file = tcl_result[2] if len(tcl_result) >= 3 else ""

            # Construir display con 3 o 4 lineas segun corresponda
            tcl_lines = []
            if tcl_violet:
                tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_violet}</span>")
            if tcl_middle:
                tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_middle}</span>")
            if is_seq:
                # Si es secuencia: mostrar subcarpeta y archivo en lineas separadas
                if tcl_subfolder:
                    tcl_lines.append(
                        f"<span style='color:#AEAEAE;'>{tcl_subfolder}</span>"
                    )
                if tcl_file:
                    tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_file}</span>")
            else:
                # Si NO es secuencia: mostrar solo archivo
                if tcl_file:
                    tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_file}</span>")

            if tcl_lines:
                tcl_display = "<br>".join(tcl_lines)
            else:
                tcl_display = f"<span style='color:#AEAEAE;'>{file_pattern}</span>"

            self.original_label = add_block(
                "Original TCL Path", tcl_display, rich=True, is_section=True
            )
        else:
            # Si la flag esta desactivada, crear un label vacio pero no mostrarlo
            self.original_label = None

        # Label para path final normalizado (se actualizara en tiempo real) con 3 o 4 lineas
        if normalized_path:
            # Detectar si el path normalizado es secuencia (por si acaso)
            is_seq_normalized = is_sequence_pattern(normalized_path)
            path_result = split_path_at_violet_end(
                normalized_path,
                shot_folder_parts,
                is_sequence=is_seq_normalized,
                original_extensions=self.original_extensions,
            )

            # Desempaquetar segun si es secuencia o no
            violet_part = path_result[0]
            middle_part = path_result[1]
            if is_seq_normalized and len(path_result) >= 4:
                subfolder_part = path_result[2]
                file_part = path_result[3]
            else:
                subfolder_part = ""
                file_part = path_result[2] if len(path_result) >= 3 else ""

            # Construir display con 3 o 4 lineas segun corresponda
            path_lines = []
            if violet_part:
                path_lines.append(violet_part)
            if middle_part:
                path_lines.append(middle_part)
            if is_seq_normalized:
                # Si es secuencia: mostrar subcarpeta y archivo en lineas separadas
                if subfolder_part:
                    path_lines.append(subfolder_part)
                if file_part:
                    path_lines.append(file_part)
            else:
                # Si NO es secuencia: mostrar solo archivo
                if file_part:
                    path_lines.append(file_part)

            if path_lines:
                colored_normalized = "<br>".join(path_lines)
            else:
                colored_normalized = apply_path_coloring(
                    normalized_path, shot_folder_parts
                )

            self.normalized_label = add_block(
                "Final Path", colored_normalized, rich=True, is_section=True
            )
        else:
            self.normalized_label = add_block(
                "Final Path", "(No normalized)", is_section=True
            )

        # Botones Cancel y OK
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #cccccc;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #443a91;
            }
            QPushButton:pressed {
                background-color: #3a2e2e;
            }
        """
        )
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #cccccc;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #443a91;
            }
            QPushButton:pressed {
                background-color: #2d265e;
            }
        """
        )
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.adjustSize()

    def keyPressEvent(self, event):
        """Maneja eventos de teclado: ESC para cancelar, Enter para aceptar."""
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        else:
            super().keyPressEvent(event)

    def increment_index(self):
        """Incrementa el indice en 1."""
        if self.current_index is None:
            return
        new_value = min(self.current_index + 1, self.max_index)
        self.set_index_value(new_value)

    def decrement_index(self):
        """Decrementa el indice en 1."""
        if self.current_index is None:
            return
        new_value = max(self.current_index - 1, self.min_index)
        self.set_index_value(new_value)

    def increment_upward_level(self):
        """Incrementa el nivel de directorio en 1 y actualiza el file_pattern."""
        if self.current_dir_level is None:
            self.current_dir_level = 1
        new_value = min(self.current_dir_level + 1, self.max_dir_level)
        self.set_dir_level_value(new_value)

    def decrement_upward_level(self):
        """Decrementa el nivel de directorio en 1 y actualiza el file_pattern."""
        if self.current_dir_level is None:
            self.current_dir_level = 1
        new_value = max(self.current_dir_level - 1, self.min_dir_level)
        self.set_dir_level_value(new_value)

    def set_dir_level_value(self, new_value):
        """Establece el nuevo valor del nivel de directorio y actualiza todo."""
        if new_value == self.current_dir_level:
            return

        self.current_dir_level = new_value

        # Actualizar el label del numero
        self.upward_level_label.setText(str(self.current_dir_level))

        # Actualizar el file_pattern con el nuevo nivel de directorio
        # Primero aplicar cambios de indices si los hay
        base_pattern = self.original_file_pattern
        if self.has_adjustable and self.current_index is not None:
            base_pattern = replace_indices_in_pattern(
                self.original_file_pattern, self.current_index
            )

        # Luego aplicar cambios de niveles de directorio
        self.current_file_pattern = replace_directory_levels(base_pattern, new_value)

        # Log del cambio
        naming_segments = (
            self.current_index
            if self.has_adjustable and self.current_index is not None
            else "N/A"
        )
        debug_print(f"Folder Up Levels cambiado a: {new_value}")
        debug_print(
            f"Naming Segments: {naming_segments}, Folder Up Levels: {new_value}"
        )
        debug_print(f"Original TCL Path: {self.current_file_pattern}")

        # Si el nivel vuelve al valor original y no hay cambios de indices, usar None
        original_dir_level = has_directory_levels(self.original_file_pattern)[1]
        if new_value == (original_dir_level if original_dir_level else 1):
            # Verificar si hay cambios de indices
            if self.has_adjustable:
                original_index = has_adjustable_indices(self.original_file_pattern)[1]
                if self.current_index == original_index:
                    self.modified_file_pattern = None
                else:
                    self.modified_file_pattern = self.current_file_pattern
            else:
                self.modified_file_pattern = None
        else:
            self.modified_file_pattern = self.current_file_pattern

        # Actualizar el label del codigo original solo si esta visible
        if self.original_label is not None:
            # Detectar si es una secuencia
            is_seq = is_sequence_pattern(self.current_file_pattern)

            # Actualizar el label del codigo original con 3 o 4 lineas
            tcl_result = split_tcl_path_at_shot_end(
                self.current_file_pattern, self.shot_folder_parts, is_sequence=is_seq
            )

            # Desempaquetar segun si es secuencia o no
            tcl_violet = tcl_result[0]
            tcl_middle = tcl_result[1]
            if is_seq and len(tcl_result) >= 4:
                tcl_subfolder = tcl_result[2]
                tcl_file = tcl_result[3]
            else:
                tcl_subfolder = ""
                tcl_file = tcl_result[2] if len(tcl_result) >= 3 else ""

            # Construir display con 3 o 4 lineas segun corresponda
            tcl_lines = []
            if tcl_violet:
                tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_violet}</span>")
            if tcl_middle:
                tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_middle}</span>")
            if is_seq:
                # Si es secuencia: mostrar subcarpeta y archivo en lineas separadas
                if tcl_subfolder:
                    tcl_lines.append(
                        f"<span style='color:#AEAEAE;'>{tcl_subfolder}</span>"
                    )
                if tcl_file:
                    tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_file}</span>")
            else:
                # Si NO es secuencia: mostrar solo archivo
                if tcl_file:
                    tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_file}</span>")

            if tcl_lines:
                tcl_display = "<br>".join(tcl_lines)
            else:
                tcl_display = (
                    f"<span style='color:#AEAEAE;'>{self.current_file_pattern}</span>"
                )
            self.original_label.setText(tcl_display)

        # Programar actualizacion de paths (con debounce)
        self.update_timer.stop()
        self.update_timer.start(200)  # Esperar 200ms antes de actualizar

    def set_index_value(self, new_value):
        """Establece el nuevo valor del indice y actualiza todo."""
        if new_value == self.current_index:
            return

        self.current_index = new_value

        # Actualizar el label del numero
        self.index_label.setText(str(self.current_index))

        # Actualizar el file_pattern con el nuevo indice
        base_pattern = replace_indices_in_pattern(self.original_file_pattern, new_value)

        # Aplicar cambios de niveles de directorio si los hay
        if self.has_dir_levels:
            self.current_file_pattern = replace_directory_levels(
                base_pattern, self.current_dir_level
            )
        else:
            self.current_file_pattern = base_pattern

        # Log del cambio
        folder_up_levels = (
            self.current_dir_level if self.has_dir_levels else self.current_dir_level
        )
        debug_print(f"Naming Segments cambiado a: {new_value}")
        debug_print(
            f"Naming Segments: {new_value}, Folder Up Levels: {folder_up_levels}"
        )
        debug_print(f"Original TCL Path: {self.current_file_pattern}")

        # Si el indice vuelve al valor original y no hay cambios de niveles, usar None
        original_index = has_adjustable_indices(self.original_file_pattern)[1]
        if new_value == original_index:
            # Verificar si hay cambios de niveles de directorio
            if self.has_dir_levels:
                original_dir_level = has_directory_levels(self.original_file_pattern)[1]
                if self.current_dir_level == (
                    original_dir_level if original_dir_level else 1
                ):
                    self.modified_file_pattern = None
                else:
                    self.modified_file_pattern = self.current_file_pattern
            else:
                self.modified_file_pattern = None
        else:
            self.modified_file_pattern = self.current_file_pattern

        # Actualizar el label del codigo original solo si esta visible
        if self.original_label is not None:
            # Detectar si es una secuencia
            is_seq = is_sequence_pattern(self.current_file_pattern)

            # Actualizar el label del codigo original con 3 o 4 lineas
            tcl_result = split_tcl_path_at_shot_end(
                self.current_file_pattern, self.shot_folder_parts, is_sequence=is_seq
            )

            # Desempaquetar segun si es secuencia o no
            tcl_violet = tcl_result[0]
            tcl_middle = tcl_result[1]
            if is_seq and len(tcl_result) >= 4:
                tcl_subfolder = tcl_result[2]
                tcl_file = tcl_result[3]
            else:
                tcl_subfolder = ""
                tcl_file = tcl_result[2] if len(tcl_result) >= 3 else ""

            # Construir display con 3 o 4 lineas segun corresponda
            tcl_lines = []
            if tcl_violet:
                tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_violet}</span>")
            if tcl_middle:
                tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_middle}</span>")
            if is_seq:
                # Si es secuencia: mostrar subcarpeta y archivo en lineas separadas
                if tcl_subfolder:
                    tcl_lines.append(
                        f"<span style='color:#AEAEAE;'>{tcl_subfolder}</span>"
                    )
                if tcl_file:
                    tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_file}</span>")
            else:
                # Si NO es secuencia: mostrar solo archivo
                if tcl_file:
                    tcl_lines.append(f"<span style='color:#AEAEAE;'>{tcl_file}</span>")

            if tcl_lines:
                tcl_display = "<br>".join(tcl_lines)
            else:
                tcl_display = (
                    f"<span style='color:#AEAEAE;'>{self.current_file_pattern}</span>"
                )
            self.original_label.setText(tcl_display)

        # Programar actualizacion de paths (con debounce)
        self.update_timer.stop()
        self.update_timer.start(200)  # Esperar 200ms antes de actualizar

    def update_paths(self):
        """Actualiza el path final normalizado basado en el file_pattern actual."""
        # Evaluar el nuevo path (ahora retorna tupla con path y extensiones originales)
        evaluated_path, original_extensions = evaluate_file_pattern(
            self.current_file_pattern
        )

        # Actualizar las extensiones originales si se obtuvieron nuevas
        if original_extensions:
            self.original_extensions = original_extensions

        # Normalizar el path
        normalized_path = None
        if evaluated_path:
            normalized_path = normalize_path_preserve_case(evaluated_path)

        # Log del Final Path
        debug_print(
            f"Final Path: {normalized_path if normalized_path else '(No normalized)'}"
        )

        # Actualizar label del path final con 3 o 4 lineas
        if normalized_path:
            # Detectar si el path normalizado es secuencia
            is_seq_normalized = is_sequence_pattern(normalized_path)
            path_result = split_path_at_violet_end(
                normalized_path,
                self.shot_folder_parts,
                is_sequence=is_seq_normalized,
                original_extensions=self.original_extensions,
            )

            # Desempaquetar segun si es secuencia o no
            violet_part = path_result[0]
            middle_part = path_result[1]
            if is_seq_normalized and len(path_result) >= 4:
                subfolder_part = path_result[2]
                file_part = path_result[3]
            else:
                subfolder_part = ""
                file_part = path_result[2] if len(path_result) >= 3 else ""

            # Construir display con 3 o 4 lineas segun corresponda
            path_lines = []
            if violet_part:
                path_lines.append(violet_part)
            if middle_part:
                path_lines.append(middle_part)
            if is_seq_normalized:
                # Si es secuencia: mostrar subcarpeta y archivo en lineas separadas
                if subfolder_part:
                    path_lines.append(subfolder_part)
                if file_part:
                    path_lines.append(file_part)
            else:
                # Si NO es secuencia: mostrar solo archivo
                if file_part:
                    path_lines.append(file_part)

            if path_lines:
                colored_normalized = "<br>".join(path_lines)
            else:
                colored_normalized = apply_path_coloring(
                    normalized_path, self.shot_folder_parts
                )
            self.normalized_label.setText(colored_normalized)
        else:
            self.normalized_label.setText(
                "<span style='color:#AEAEAE;'>(No normalized)</span>"
            )

    def accept(self):
        """Se llama cuando el usuario presiona OK."""
        if self.callback:
            # Pasar el file_pattern modificado si hubo cambios
            # Si modified_file_pattern es None, se usara el patrón original del preset
            self.callback(self.modified_file_pattern)
        super().accept()

    def reject(self):
        """Se llama cuando el usuario presiona Cancel."""
        super().reject()


def show_path_check_window(preset, user_text=None, callback=None):
    """
    Muestra la ventana de verificacion del path.
    Funciona igual que el comportamiento original de mostrar paths (inspirado en LGA_Write_PathToText.py)

    Args:
        preset: Diccionario con la configuracion del preset
        user_text: Texto ingresado por el usuario (si aplica)
        callback: Funcion a llamar cuando el usuario confirma (OK)
                  El callback recibira el file_pattern modificado (o None si no hubo cambios)
    """
    global app, window

    file_pattern = preset.get("file_pattern", "")

    # Reemplazar **** con user_text si aplica
    if user_text and "****" in file_pattern:
        processed_pattern = file_pattern.replace("****", user_text)
    else:
        processed_pattern = file_pattern

    # Evaluar y normalizar el path para mostrar el resultado final
    # evaluate_file_pattern ahora retorna tupla (evaluated_path, original_extensions)
    evaluated_path, original_extensions = evaluate_file_pattern(processed_pattern)
    normalized_path = None
    if evaluated_path:
        normalized_path = normalize_path_preserve_case(evaluated_path)

    # Obtener path del script para calcular shot_folder_parts
    script_path = nuke.root().name()
    if not script_path or script_path == "Root":
        script_path = None
    shot_folder_parts = get_shot_folder_parts(script_path)

    # Crear wrapper del callback para pasar el file_pattern modificado
    def callback_wrapper(modified_pattern):
        if callback:
            callback(modified_pattern)

    app = QApplication.instance() or QApplication([])
    window = PathCheckWindow(
        processed_pattern,
        normalized_path,
        shot_folder_parts,
        callback_wrapper,
        original_extensions=original_extensions,
    )
    window.exec_()
