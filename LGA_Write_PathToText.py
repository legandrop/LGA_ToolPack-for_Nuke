"""
_______________________________________________________________________________________________________________________________

  LGA_Write_PathToText v1.1 | Lega
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
    def __init__(
        self, write_file, evaluated_path, normalized_path, script_path, common_prefix
    ):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle("LGA Write PathToText")
        self.setStyleSheet("background-color: #232323; border-radius: 10px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

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
        # Path normalizado con coincidencia en rosa
        if normalized_path and common_prefix:
            norm_html = (
                f"<span style='color:#9354BE;font-weight:bold;'>{common_prefix}</span>"
                f"<span style='color:#AEAEAE;'>{normalized_path[len(common_prefix):]}</span>"
            )
            add_block("Path normalizado:", norm_html, rich=True)
        else:
            add_block(
                "Path normalizado:",
                normalized_path if normalized_path else "(No normalizado)",
            )

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
    # Buscar prefijo comun
    common_prefix = ""
    if script_path and normalized_path:
        # Normalizar el path del script a barras delanteras para la comparacion
        script_dir_for_comparison = os.path.dirname(
            os.path.normpath(script_path)
        ).replace(os.sep, "/")
        # Asegurarse de que script_dir_for_comparison termine con '/' si es un directorio base
        if script_dir_for_comparison and not script_dir_for_comparison.endswith("/"):
            script_dir_for_comparison += "/"

        debug_print(f"Script dir para comparación: {script_dir_for_comparison}")
        debug_print(f"Normalized path para comparación: {normalized_path}")

        # Convertir ambas rutas a minusculas para la comparacion case-insensitive
        script_dir_lower = script_dir_for_comparison.lower()
        normalized_path_lower = (
            normalized_path.lower() if normalized_path else ""
        )  # Asegurar que normalized_path_lower no sea None

        debug_print(f"Script dir (lower): {script_dir_lower}")
        debug_print(f"Normalized path (lower): {normalized_path_lower}")

        common_length = 0
        for a, b in zip(script_dir_lower, normalized_path_lower):
            if a != b:
                break
            common_length += 1

        if common_length > 0:
            # Obtener el prefijo comun del normalized_path original (con su casing original)
            common_prefix = normalized_path[:common_length]
            debug_print(f"Prefijo comun (con casing original): {common_prefix}")
        else:
            debug_print("No se encontró prefijo común")

    app = QApplication.instance() or QApplication([])
    window = PathInfoWindow(
        write_file, evaluated_path, normalized_path, script_path, common_prefix
    )
    window.show()


# --- Main Execution ---
if __name__ == "__main__":
    main()
