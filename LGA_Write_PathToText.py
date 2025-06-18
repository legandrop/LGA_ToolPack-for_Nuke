"""
_______________________________________________________________________________________________________________________________

  LGA_Write_PathToText v1.0 | Lega
  Script para mostrar el path de un Write seleccionado, su evaluación y su versión normalizada en una ventana personalizada.
_______________________________________________________________________________________________________________________________
"""

import nuke
import os
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide2.QtCore import Qt

# Variable global para activar o desactivar los prints de depuracion
debug = False  # Cambiar a False para ocultar los mensajes de debug

app = None
window = None


def debug_print(*message):
    if debug:
        print("[LGA_Write_PathToText]", *message)


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
                f"<span style='color:#c56cf0;font-weight:bold;'>{common_prefix}</span>"
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


def main():
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
            debug_print(f"Path evaluado: {evaluated_path}")
            normalized_path = os.path.normpath(evaluated_path)
            debug_print(f"Path normalizado: {normalized_path}")
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
        # Normalizar ambos paths para comparar
        script_dir = os.path.dirname(os.path.normpath(script_path)) + os.sep
        norm_path = os.path.normpath(normalized_path)
        # Buscar el prefijo comun caracter a caracter
        for i, (a, b) in enumerate(zip(script_dir, norm_path)):
            if a != b:
                break
            common_prefix += a
        if common_prefix:
            debug_print(f"Prefijo comun: {common_prefix}")
    app = QApplication.instance() or QApplication([])
    window = PathInfoWindow(
        write_file, evaluated_path, normalized_path, script_path, common_prefix
    )
    window.show()


# --- Main Execution ---
if __name__ == "__main__":
    main()
