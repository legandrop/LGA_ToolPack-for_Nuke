"""
_______________________________________________________________________________________________________________________________

  LGA_Write_PathToText v1.2 | Lega
  Script para mostrar el path de un Write seleccionado, su evaluación y su versión normalizada en una ventana personalizada.
_______________________________________________________________________________________________________________________________
"""

import nuke
import os
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide2.QtCore import Qt

# Variable global para activar o desactivar los prints de depuracion
debug = True  # Cambiar a False para ocultar los mensajes de debug

app = None
window = None


def debug_print(*message):
    if debug:
        print("[LGA_Write_PathToText]", *message)


def get_color_for_level(level):
    """
    Define los colores por nivel de directorio.
    Robado del sistema de colores del LGA_mediaManager.
    """
    colors = {
        0: "#ffff66",  # Amarillo           T
        1: "#28b5b5",  # Verde Cian         Proye
        2: "#ff9a8a",  # Naranja pastel     Grupo
        3: "#0088ff",  # Azul               Shot
        4: "#ffd369",  # Amarillo mostaza
        5: "#28b5b5",  # Verde Cian
        6: "#ff9a8a",  # Naranja pastel
        7: "#6bc9ff",  # Celeste
        8: "#ffd369",  # Amarillo mostaza
        9: "#28b5b5",  # Verde Cian
        10: "#ff9a8a",  # Naranja pastel
        11: "#6bc9ff",  # Celeste
    }
    return colors.get(level, "#AEAEAE")  # Color gris por defecto


def apply_path_coloring(path, shot_folder_parts):
    """
    Aplica el sistema de colores por nivel a una ruta.
    Basado en el sistema del LGA_mediaManager.
    PRESERVA LA CAPITALIZACIÓN ORIGINAL del path.
    """
    if not path:
        return path

    # Dividir la ruta en partes PRESERVANDO la capitalización original
    parts = path.replace("\\", "/").split("/")
    colored_parts = []

    # Para la comparación, convertir a minúsculas SOLO para comparar
    parts_lower = [part.lower() for part in parts]

    debug_print(f"Path a colorear: {path}")
    debug_print(f"Parts originales: {parts}")
    debug_print(f"Parts lowercase: {parts_lower}")
    debug_print(f"Shot folder parts: {shot_folder_parts}")

    # Aplicar colores a cada parte de la ruta excepto el nombre del archivo
    # USAR LA MISMA LÓGICA QUE EL MEDIA MANAGER
    for i, part in enumerate(parts[:-1]):  # Usar el part original (con capitalización)
        part_lower = parts_lower[i]  # Usar la versión en minúsculas solo para comparar

        # LÓGICA EXACTA DEL MEDIA MANAGER:
        # Si i >= len(shot_folder_parts) OR part != shot_folder_parts[i] → get_color_for_level(i)
        # Si no (i < len(shot_folder_parts) AND part == shot_folder_parts[i]) → violeta

        # Verificar si estamos dentro del rango del shot_folder_parts y si coincide
        within_shot_range = i < len(shot_folder_parts)
        matches_shot_part = within_shot_range and part_lower == shot_folder_parts[i]

        debug_print(f"  Parte {i}: '{part}' (lower: '{part_lower}')")
        debug_print(f"    within_shot_range: {within_shot_range}")
        if within_shot_range:
            debug_print(f"    shot_folder_parts[{i}]: '{shot_folder_parts[i]}'")
            debug_print(f"    matches_shot_part: {matches_shot_part}")

        if i >= len(shot_folder_parts) or part_lower != shot_folder_parts[i]:
            # Usar colores por nivel
            text_color = get_color_for_level(i)
            debug_print(f"    → Color por nivel {i}: {text_color}")
        else:
            # Si esta parte coincide con la ruta del shot, usar color violeta
            text_color = "#c56cf0"  # Color violeta para partes del shot
            debug_print(f"    → Color violeta (coincide con shot): {text_color}")

        # Usar el part ORIGINAL (con capitalización) para mostrar
        colored_parts.append(f"<span style='color: {text_color};'>{part}</span>")

    # El nombre del archivo permanece en blanco y negrita (también con capitalización original)
    if len(parts) > 0:
        file_name = f"<b style='color: rgb(200, 200, 200);'>{parts[-1]}</b>"
        colored_parts.append(file_name)

    # Unir con separadores blancos
    colored_text = '<span style="color: white;">/</span>'.join(colored_parts)
    debug_print(f"Resultado final: {colored_text}")
    return colored_text


def normalize_path_preserve_case(path):
    """
    Normaliza una ruta resolviendo .. y . pero preservando la capitalización original.
    Siempre devuelve rutas con barras delanteras (/).
    """
    if not path:
        return path

    # Trabajar con la ruta tal como viene, sin usar os.path.normpath que cambia capitalización
    # Reemplazar todas las \ con / para trabajar de forma consistente
    normalized_separators = path.replace("\\", "/")

    # Separar en componentes
    parts = normalized_separators.split("/")

    # Procesar los componentes para resolver .. y .
    resolved_parts = []
    for part in parts:
        if part == "." or part == "":
            # Ignorar '.' (directorio actual) y partes vacías (dobles barras)
            # Excepto si es el primer componente vacío (ruta absoluta que empieza con /)
            if (
                part == ""
                and len(resolved_parts) == 0
                and normalized_separators.startswith("/")
            ):
                resolved_parts.append(part)
            continue
        elif part == "..":
            # Subir un directorio si es posible
            if (
                resolved_parts
                and resolved_parts[-1] != ".."
                and resolved_parts[-1] != ""
            ):
                resolved_parts.pop()
            else:
                # Si no podemos subir más, mantener el ..
                resolved_parts.append(part)
        else:
            resolved_parts.append(part)

    # Reconstruir la ruta
    result = "/".join(resolved_parts)

    # Si la ruta original empezaba con / y no quedó vacía, asegurar que empiece con /
    if normalized_separators.startswith("/") and not result.startswith("/"):
        result = "/" + result

    return result


class PathInfoWindow(QWidget):
    def __init__(self, write_file, evaluated_path, normalized_path, script_path):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle("LGA Write PathToText")
        self.setStyleSheet("background-color: #232323; border-radius: 10px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Calcular la ruta del SHOT (no del script completo)
        # Subir niveles desde el script para encontrar la carpeta base del shot
        shot_folder_parts = []
        if script_path and script_path != "Root":
            # Por defecto, subir 3 niveles desde el script para encontrar el shot
            # Ejemplo: script en "T:/VFX-ETDM/101/SHOT/Comp/1_projects/script.nk"
            # Shot debería ser: "T:/VFX-ETDM/101/SHOT"
            project_folder_depth = 3  # Niveles a subir desde el script

            shot_folder = script_path
            for _ in range(project_folder_depth):
                shot_folder = os.path.dirname(shot_folder)

            debug_print(f"Script path: {script_path}")
            debug_print(f"Shot folder calculado: {shot_folder}")

            if shot_folder:
                shot_dir = shot_folder.replace("\\", "/").lower()
                shot_folder_parts = shot_dir.split("/")

        debug_print(f"Shot folder parts: {shot_folder_parts}")

        def add_block(title, value, rich=False):
            block_layout = QVBoxLayout()
            block_layout.setSpacing(2)  # Espacio reducido entre título y valor
            block_layout.setContentsMargins(0, 0, 0, 0)
            title_label = QLabel(f"<b style='color:#cccccc;'>{title}</b>")
            title_label.setStyleSheet("font-size:14px;")
            if rich:
                value_label = QLabel(value)
            else:
                value_label = QLabel(f"<span style='color:#AEAEAE;'>{value}</span>")
            value_label.setStyleSheet("font-size:13px;")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            block_layout.addWidget(title_label)
            block_layout.addWidget(value_label)
            layout.addLayout(block_layout)

        add_block("Código original:", write_file)
        add_block(
            "Path evaluado:", evaluated_path if evaluated_path else "(No evaluado)"
        )

        # Path normalizado con colores por nivel
        if normalized_path:
            colored_normalized = apply_path_coloring(normalized_path, shot_folder_parts)
            add_block("Path normalizado:", colored_normalized, rich=True)
        else:
            add_block("Path normalizado:", "(No normalizado)")

        self.setLayout(layout)
        self.adjustSize()


def main(normalize_path_func=None):
    global app, window
    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        debug_print("No hay nodos seleccionados. No se hace nada.")
        return
    write_node = None
    for node in selected_nodes:
        if node.Class() == "Write":
            write_node = node
            break
    if not write_node:
        debug_print("No hay ningun nodo Write seleccionado. No se hace nada.")
        return
    write_file = write_node["file"].value()
    evaluated_path = None
    normalized_path = None
    if "[" in write_file and "]" in write_file:
        try:
            evaluated_path = nuke.filename(write_node)
            if evaluated_path is None:
                evaluated_path = ""
            debug_print(f"Path evaluado (directo de nuke.filename): {evaluated_path}")
            debug_print(f"Tipo de evaluated_path: {type(evaluated_path)}")

            # SIEMPRE usar nuestra función personalizada que preserva capitalización
            # No usar normalize_path_func externa porque puede convertir a minúsculas
            temp_normalized_path = normalize_path_preserve_case(evaluated_path)
            debug_print(
                f"Normalizado con nuestra función (preserva capitalización): {temp_normalized_path}"
            )

            # Asegurar que las barras sean siempre hacia adelante (ya lo hace nuestra función personalizada)
            if temp_normalized_path:  # Si temp_normalized_path no es None o vacio
                normalized_path = temp_normalized_path
            else:
                normalized_path = (
                    None  # Mantenerlo None si temp_normalized_path fue None o vacio
                )

            debug_print(f"Path normalizado final para UI: {normalized_path}")

        except Exception as e:
            debug_print(f"Error al evaluar el path: {e}")

    # Obtener path del script actual
    script_path = nuke.root().name()
    if not script_path or script_path == "Root":
        script_path = None
    debug_print(f"Path del script: {script_path}")

    app = QApplication.instance() or QApplication([])
    window = PathInfoWindow(write_file, evaluated_path, normalized_path, script_path)
    window.show()


# --- Main Execution ---
if __name__ == "__main__":
    main()
