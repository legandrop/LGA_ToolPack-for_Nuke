"""
_______________________________________________________________________________________________________________________________

  LGA_Write_Presets_Check v1.20 | Lega
  Script para mostrar una ventana de verificación del path normalizado antes de crear un Write node.
  Se usa cuando el usuario hace Shift+Click sobre un preset.

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
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide2.QtCore import Qt, QTimer

# Importar funciones de LGA_Write_PathToText para reutilizar
try:
    from LGA_Write_PathToText import (
        apply_path_coloring,
        normalize_path_preserve_case,
        get_color_for_level,
    )
except ImportError:
    # Si no se puede importar, definir funciones locales
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
            file_name = f"<b style='color: rgb(200, 200, 200);'>{parts[-1]}</b>"
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
DEBUG = False

app = None
window = None


def debug_print(*message):
    if DEBUG:
        print("[LGA_Write_Presets_Check]", *message)


def evaluate_file_pattern(file_pattern):
    """
    Evalua una expresion TCL file_pattern sin crear un Write node permanente.
    Crea un Write temporal solo para evaluar el path y luego lo elimina.
    Retorna el path evaluado o None si hay error.
    """
    if not file_pattern:
        return None

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

        # Evaluar el path usando nuke.filename()
        evaluated_path = nuke.filename(temp_write)

        # Si evaluated_path es None, usar cadena vacia
        if evaluated_path is None:
            evaluated_path = ""

        # Eliminar el Write temporal inmediatamente
        nuke.delete(temp_write)

        debug_print(f"File pattern original: {file_pattern}")
        debug_print(f"Path evaluado: {evaluated_path}")

        return evaluated_path if evaluated_path else None
    except Exception as e:
        debug_print(f"Error al evaluar file_pattern: {e}")
        # Asegurarse de eliminar el Write temporal incluso si hay error
        try:
            if "temp_write" in locals():
                nuke.delete(temp_write)
        except:
            pass
        return None


def get_shot_folder_parts(script_path):
    """
    Calcula las partes de la ruta del shot para el coloreado.
    Reutiliza la logica de LGA_Write_PathToText.
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


def split_path_at_violet_end(path, shot_folder_parts):
    """
    Divide un path en dos partes: la parte violeta (que coincide con shot_folder_parts) y el resto.
    Retorna (violet_part, rest_part) como strings HTML con colores.
    """
    if not path:
        return path, ""

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

    # Aplicar coloreado a la parte violeta
    colored_violet = []
    for i, part in enumerate(violet_parts):
        if i < len(shot_folder_parts) and parts_lower[i] == shot_folder_parts[i]:
            colored_violet.append(f"<span style='color: #c56cf0;'>{part}</span>")
        else:
            color = get_color_for_level(i)
            colored_violet.append(f"<span style='color: {color};'>{part}</span>")

    violet_str = '<span style="color: white;">/</span>'.join(colored_violet)
    # Agregar / al final si hay resto
    if rest_parts and violet_parts:
        violet_str += '<span style="color: white;">/</span>'

    # Aplicar coloreado al resto (si existe)
    rest_str = ""
    if rest_parts:
        colored_rest = []
        for i, part in enumerate(rest_parts[:-1]):
            level = violet_end_index + 1 + i
            color = get_color_for_level(level)
            colored_rest.append(f"<span style='color: {color};'>{part}</span>")

        # Agregar el nombre del archivo
        file_name = f"<b style='color: rgb(200, 200, 200);'>{rest_parts[-1]}</b>"
        colored_rest.append(file_name)

        rest_str = '<span style="color: white;">/</span>'.join(colored_rest)

    return violet_str, rest_str


def split_tcl_path_at_shot_end(tcl_path, shot_folder_parts):
    """
    Divide el TCL path en dos partes basandose en donde termina la parte del shot.
    Busca patrones comunes que indican salida del shot folder (como ../2_prerenders, ../4_publish, etc).
    """
    if not tcl_path:
        return tcl_path, ""

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
            return tcl_path[:prev_slash], tcl_path[prev_slash + 1 :]
        else:
            return tcl_path[:split_pos], tcl_path[split_pos:]

    # Si no encontramos el patron, buscar el primer ../ que aparece
    first_dotdot = tcl_path.find("../")
    if first_dotdot > 0:
        # Buscar el / anterior mas cercano
        prev_slash = tcl_path.rfind("/", 0, first_dotdot)
        if prev_slash > 0:
            return tcl_path[:prev_slash], tcl_path[prev_slash + 1 :]
        else:
            return tcl_path[:first_dotdot], tcl_path[first_dotdot:]

    # Si no encontramos nada, dividir aproximadamente al 60% buscando el / mas cercano
    split_point = int(len(tcl_path) * 0.6)
    nearest_slash = tcl_path.rfind("/", 0, split_point)
    if nearest_slash > 0:
        return tcl_path[:nearest_slash], tcl_path[nearest_slash + 1 :]
    else:
        return tcl_path, ""


class PathCheckWindow(QWidget):
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
    ):
        super().__init__()
        self.callback = callback
        self.original_file_pattern = file_pattern
        self.current_file_pattern = file_pattern
        self.shot_folder_parts = shot_folder_parts
        # Guardara el file_pattern modificado solo si el usuario cambia el indice
        # Si es None, se usara el patrón original del preset
        self.modified_file_pattern = None

        # Detectar si hay indices ajustables
        self.has_adjustable, self.current_index = has_adjustable_indices(file_pattern)

        # Timer para actualizacion en tiempo real (debounce)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_paths)

        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("LGA Write Path Check")
        self.setStyleSheet("background-color: #232323; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        def add_block(title, value, rich=False):
            block_layout = QVBoxLayout()
            block_layout.setSpacing(2)
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
            return value_label  # Retornar el label para poder actualizarlo

        # Agregar control de indice ajustable primero si aplica
        if self.has_adjustable:
            index_layout = QHBoxLayout()
            index_layout.setSpacing(10)
            index_layout.setContentsMargins(0, 0, 0, 0)

            index_title = QLabel(
                "<b style='color:#cccccc;'>Naming segments to include:</b>"
            )
            index_title.setStyleSheet("font-size:14px;")
            index_layout.addWidget(index_title)

            # Contenedor para el numero y botones
            control_layout = QHBoxLayout()
            control_layout.setSpacing(2)
            control_layout.setContentsMargins(0, 0, 0, 0)

            # Label con el numero (no editable)
            self.index_label = QLabel(str(self.current_index))
            self.index_label.setFixedSize(
                28, 24
            )  # Altura igual a los dos botones juntos (12+12=24)
            self.index_label.setStyleSheet(
                """
                QLabel {
                    background-color: #3e3e3e;
                    color: #FFFFFF;
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
            self.index_label.setAlignment(Qt.AlignCenter)
            control_layout.addWidget(self.index_label)

            # Contenedor vertical para los botones
            buttons_container = QWidget()
            buttons_layout = QVBoxLayout(buttons_container)
            buttons_layout.setSpacing(0)
            buttons_layout.setContentsMargins(0, 0, 0, 0)

            # Boton triangulo arriba
            self.up_button = QPushButton("▲")
            self.up_button.setFixedSize(24, 12)
            self.up_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #3e3e3e;
                    color: #FFFFFF;
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
            self.up_button.clicked.connect(self.increment_index)
            buttons_layout.addWidget(self.up_button)

            # Boton triangulo abajo
            self.down_button = QPushButton("▼")
            self.down_button.setFixedSize(24, 12)
            self.down_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #3e3e3e;
                    color: #FFFFFF;
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
            self.down_button.clicked.connect(self.decrement_index)
            buttons_layout.addWidget(self.down_button)

            control_layout.addWidget(buttons_container)

            # Widget contenedor para el control
            control_widget = QWidget()
            control_widget.setLayout(control_layout)
            index_layout.addWidget(control_widget)
            index_layout.addStretch()

            # Guardar valores minimo y maximo
            self.min_index = 0
            self.max_index = 20

            layout.addLayout(index_layout)
        else:
            # Mostrar mensaje informativo si no hay indices ajustables
            info_label = QLabel(
                "<span style='color:#888888; font-style:italic;'>"
                "Este preset no utiliza índices ajustables en su fórmula TCL"
                "</span>"
            )
            info_label.setStyleSheet("font-size:12px; padding: 8px 0px;")
            layout.addWidget(info_label)

        # Mostrar TCL path original (despues del control de indice) con salto de linea
        tcl_violet, tcl_rest = split_tcl_path_at_shot_end(
            file_pattern, shot_folder_parts
        )
        if tcl_rest:
            tcl_display = f"{tcl_violet}/<br>{tcl_rest}"
        else:
            tcl_display = file_pattern
        self.original_label = add_block("Original TCL Path:", tcl_display)

        # Label para path final normalizado (se actualizara en tiempo real) con salto de linea
        if normalized_path:
            violet_part, rest_part = split_path_at_violet_end(
                normalized_path, shot_folder_parts
            )
            if rest_part:
                colored_normalized = f"{violet_part}<br>{rest_part}"
            else:
                colored_normalized = apply_path_coloring(
                    normalized_path, shot_folder_parts
                )
            self.normalized_label = add_block(
                "Final Path:", colored_normalized, rich=True
            )
        else:
            self.normalized_label = add_block("Final Path:", "(No normalized)")

        # Botones Cancel y OK
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #443a3a;
                color: #cccccc;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a4a4a;
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
                background-color: #443a91;
                color: #cccccc;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #372e7a;
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

    def set_index_value(self, new_value):
        """Establece el nuevo valor del indice y actualiza todo."""
        if new_value == self.current_index:
            return

        self.current_index = new_value

        # Actualizar el label del numero
        self.index_label.setText(str(self.current_index))

        # Actualizar el file_pattern con el nuevo indice
        self.current_file_pattern = replace_indices_in_pattern(
            self.original_file_pattern, new_value
        )

        # Si el indice vuelve al valor original, usar None para que se use el patrón original
        original_index = has_adjustable_indices(self.original_file_pattern)[1]
        if new_value == original_index:
            self.modified_file_pattern = None
        else:
            self.modified_file_pattern = self.current_file_pattern

        # Actualizar el label del codigo original con salto de linea
        tcl_violet, tcl_rest = split_tcl_path_at_shot_end(
            self.current_file_pattern, self.shot_folder_parts
        )
        if tcl_rest:
            tcl_display = (
                f"<span style='color:#AEAEAE;'>{tcl_violet}/<br>{tcl_rest}</span>"
            )
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
        # Evaluar el nuevo path
        evaluated_path = evaluate_file_pattern(self.current_file_pattern)

        # Normalizar el path
        normalized_path = None
        if evaluated_path:
            normalized_path = normalize_path_preserve_case(evaluated_path)

        # Actualizar label del path final con salto de linea
        if normalized_path:
            violet_part, rest_part = split_path_at_violet_end(
                normalized_path, self.shot_folder_parts
            )
            if rest_part:
                colored_normalized = f"{violet_part}<br>{rest_part}"
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
        self.close()

    def reject(self):
        """Se llama cuando el usuario presiona Cancel."""
        self.close()


def show_path_check_window(preset, user_text=None, callback=None):
    """
    Muestra la ventana de verificacion del path.
    Funciona igual que main() en LGA_Write_PathToText.py

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
    evaluated_path = evaluate_file_pattern(processed_pattern)
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
    )
    window.show()
