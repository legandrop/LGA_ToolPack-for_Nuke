"""
_____________________________________________________________________________

  LGA_Write_Presets v2.67 | Lega

  Creates Write nodes with predefined settings for different purposes.
  Supports both script-based and Read node-based path generation.


  v2.67: Comportamiento automatico - Si hay un Write seleccionado al abrir el script,
         automaticamente abre la ventana de edicion. El boton solo aparece si no hay
         Write seleccionado.

  v2.66: Eliminado LGA_Write_PathToText.py. Boton "Show selected Write node file path"
         ahora abre ventana editable para modificar Writes existentes en lugar de
         mostrar informacion solo de lectura.

  v2.68: Eliminado completamente el boton "Show selected Write node file path". La
         funcionalidad ahora es 100% automatica - si hay Write seleccionado se abre
         la edicion, si no hay Write no aparece ningun boton extra.

  v2.64: Greyed out items in the table when the script is not saved.

  v2.63: Color coding for original extensions in the path.

  v2.62: UI improvements.

  v2.61: Ventana de verificacion con controles para editar Naming Segments y Folder Up Levels.
         Ambos controles siempre visibles. Naming Segments deshabilitado cuando no aplica.

  v2.53: Shift+Click permite editar indices ajustables en tiempo real antes de crear el Write.

  v2.52: Shift+Click en presets muestra ventana de verificacion del path antes de crear el Write.

  v2.51: Usa modulo compartido LGA_ToolPack_NamingUtils para detectar el formato del shotname.

  v2.50: Automatically detects and adapts to naming formats:
        - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 blocks with description)
        - PROYECTO_SEQ_SHOT (3 blocks simplified)
_____________________________________________________________________________

"""

from qt_compat import QtWidgets, QtGui, QtCore, QGuiApplication

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QPushButton = QtWidgets.QPushButton
QHBoxLayout = QtWidgets.QHBoxLayout
QDialog = QtWidgets.QDialog
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QFrame = QtWidgets.QFrame
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QStyle = QtWidgets.QStyle
Qt = QtCore.Qt
QTimer = QtCore.QTimer
QCursor = QtGui.QCursor
QPalette = QtGui.QPalette
QColor = QtGui.QColor
QKeyEvent = QtGui.QKeyEvent
QBrush = QtGui.QBrush
QMouseEvent = QtGui.QMouseEvent
import nuke
import sys
import os
import configparser
import ntpath
import posixpath
import unicodedata
import re

# Variable global para activar o desactivar los debug_prints
DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


# Importar modulo compartido de naming utils
try:
    from LGA_ToolPack_NamingUtils import (
        detect_shotname_format,
        get_script_base_name,
    )

    naming_utils_available = True
except ImportError:
    naming_utils_available = False
    debug_print(
        "[Write_Presets] Advertencia: LGA_ToolPack_NamingUtils no disponible. Usando funcion local."
    )


# Intentar importar el modulo LGA_oz_backdropReplacer
script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)

try:
    import LGA_oz_backdropReplacer

    oz_backdrop_available = True
except ImportError:
    oz_backdrop_available = False
    debug_print(
        "El modulo LGA_oz_backdropReplacer no esta disponible. Continuando sin reemplazar el backdrop."
    )

# Importar modulo de verificacion de path
try:
    from LGA_Write_Presets_Check import show_path_check_window

    path_check_available = True
except ImportError:
    path_check_available = False
    debug_print(
        "El modulo LGA_Write_Presets_Check no esta disponible. Shift+Click no funcionara."
    )

# Añadir al inicio del archivo
FORMAT_COLORS = {
    "EXR": "#FDFD91",  # Amarillo
    "MOV": "#A4A4FF",  # Azul
    "MXF": "#ff8050",  # Azul
    "TIFF": "#9AFD9A",  # Verde
    "PNG": "#FFA7D3",  # Rosa
}


def format_name_with_color(text):
    for fmt, color in FORMAT_COLORS.items():
        if fmt in text.upper():
            return text.replace(
                fmt, f'<span style="color: {color}; font-weight: bold;">{fmt}</span>'
            )
    return text


# Funciones auxiliares del preRender original
def align_write_to_dot(dot_node, write_node):
    dot_center_y = dot_node.ypos() + dot_node.screenHeight() / 2
    write_center_y = write_node.ypos() + write_node.screenHeight() / 2
    y_offset = dot_center_y - write_center_y
    if y_offset != 0:
        write_node.setYpos(int(write_node.ypos() + y_offset))


def get_unique_node_name(base_name):
    node_name = base_name
    index = 1
    while nuke.exists(node_name):
        node_name = f"{base_name}{index}"
        index += 1
    return node_name


class NameInputDialog(QDialog):
    def __init__(self, initial_text=""):
        super().__init__()
        self.esc_exit = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        # Widget contenedor principal con esquinas redondeadas
        main_widget = QWidget(self)
        main_widget.setStyleSheet(
            """
            QWidget {
                background-color: #222222;
                border: none;
                border-radius: 9px;  /* Esquinas redondeadas */
            }
        """
        )

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(12, 6, 12, 6)

        title = QLabel("Render Name")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #AAAAAA; font-family: Verdana; font-weight: bold; font-size: 10pt;"
        )
        layout.addWidget(title)

        # Crear layout horizontal para el line_edit y el botón OK
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)  # Agregar espacio entre los widgets

        self.line_edit = QLineEdit(self)
        self.line_edit.setFixedHeight(24)
        self.line_edit.setFrame(False)
        self.line_edit.setStyleSheet(
            """
            background-color: #3e3e3e;
            color: #FFFFFF;
            border-radius: 3px;
        """
        )
        self.line_edit.setText(initial_text)
        self.line_edit.setCursorPosition(len(initial_text))
        input_layout.addWidget(self.line_edit)

        # Agregar botón OK
        ok_button = QPushButton("OK", self)
        ok_button.setFixedSize(50, 24)
        ok_button.setStyleSheet(
            """
            QPushButton {
                background-color: #323232;
                color: #B0B0B0;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #282828;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
        """
        )
        ok_button.clicked.connect(self.accept)
        input_layout.addWidget(ok_button)

        layout.addLayout(input_layout)

        help_label = QLabel(
            '<span style="font-size:7pt; color:#AAAAAA;">Enter to confirm</span>',
            self,
        )
        help_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(help_label)

        # Layout principal del diálogo
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_widget)

        self.resize(220, 90)

        self.line_edit.installEventFilter(self)
        self.line_edit.setFocus()  # Asegurar que el line_edit tenga el foco

    def showEvent(self, event):
        """Se llama cuando el diálogo se muestra"""
        super().showEvent(event)
        self.activateWindow()  # Activar la ventana
        self.raise_()  # Traer al frente
        self.line_edit.setFocus()  # Dar foco al line_edit

    def eventFilter(self, widget, event):
        if isinstance(event, QKeyEvent):
            if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                if (
                    event.modifiers() == Qt.ControlModifier
                    or event.modifiers() == Qt.NoModifier
                ):
                    self.accept()
                return True
            elif event.key() == Qt.Key_Escape:
                self.esc_exit = True
                self.reject()
                return True
        return super().eventFilter(widget, event)


def show_name_input_dialog(initial_text=""):
    dialog = NameInputDialog(initial_text)
    cursor_pos = QCursor.pos()
    screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
    if screen:
        avail_space = screen.availableGeometry()
        posx = min(
            max(cursor_pos.x() - 100, avail_space.left()), avail_space.right() - 200
        )
        posy = min(
            max(cursor_pos.y() - 80, avail_space.top()), avail_space.bottom() - 150
        )
        dialog.move(posx, posy)

    if dialog.exec_() == QDialog.Accepted:
        return dialog.esc_exit, dialog.line_edit.text()
    else:
        return dialog.esc_exit, None


def get_selected_node():
    try:
        return nuke.selectedNode()
    except ValueError:
        return None


def find_top_read_node(node):
    """Encuentra el nodo Read más alto en las dependencias ascendentes del nodo"""
    if node.Class() == "Read":
        return node

    for input_node in node.dependencies():
        return find_top_read_node(input_node)

    return None


def get_write_name_from_read(current_node, default_name):
    """Obtiene un nombre único para el Write basado en el Read más alto o usa el default"""
    read_node = find_top_read_node(current_node)

    if read_node:
        file_path = read_node["file"].value()
        file_name = os.path.basename(file_path)
        file_name = os.path.splitext(file_name)[0]

        # Eliminar el padding y sufijos numéricos existentes
        if "_" in file_name:
            base_parts = file_name.split("_")
            # Eliminar el último segmento si es numérico
            if base_parts[-1].isdigit():
                file_name = "_".join(base_parts[:-1])
            else:
                file_name = (
                    "_".join(base_parts[:-1]) if len(base_parts) > 1 else base_parts[0]
                )

        # Normalizar el nombre del archivo
        normalized_file_name = normalize_node_name(file_name)
        base_name = "Write_" + normalized_file_name
        return get_unique_write_name(base_name)
    else:
        # Normalizar el nombre por defecto
        normalized_default = normalize_node_name(default_name)
        return "Write_" + normalized_default


def get_unique_write_name(base_name):
    """Genera un nombre único para el Write node agregando sufijos numéricos si es necesario"""
    index = 1
    node_name = base_name
    while nuke.exists(node_name):
        node_name = f"{base_name}_{index}"
        index += 1
    return node_name


def detect_shotname_format_local():
    """
    Funcion local de respaldo si el modulo compartido no esta disponible.
    Detecta el formato del shotname basado en el script actual de Nuke.
    Retorna True si es formato con descripcion (5 bloques), False si es simplificado (3 bloques).
    Si no hay script guardado, asume formato simplificado.
    """
    try:
        script_path = nuke.root().name()
        if not script_path or script_path == "Root":
            debug_print(
                "[Write_Presets] No hay script guardado, asumiendo formato simplificado (3 bloques)"
            )
            return False

        script_name = os.path.basename(script_path)
        # Eliminar extension .nk
        base_name = re.sub(r"\.nk$", "", script_name)
        parts = base_name.split("_")

        debug_print(f"[Write_Presets] Analizando script: {script_name}")
        debug_print(f"[Write_Presets] Base name: {base_name}")
        debug_print(f"[Write_Presets] Partes: {parts}")

        # Verificar si el campo 5 (indice 4) es una version
        if len(parts) >= 5:
            field_5 = parts[4]
            if field_5.startswith("v") and len(field_5) > 1 and field_5[1:].isdigit():
                debug_print(
                    f"[Write_Presets] Campo 5 '{field_5}' es version -> Formato SIMPLIFICADO (3 bloques)"
                )
                return False
            else:
                debug_print(
                    f"[Write_Presets] Campo 5 '{field_5}' no es version -> Formato CON DESCRIPCION (5 bloques)"
                )
                return True
        else:
            debug_print(
                f"[Write_Presets] Menos de 5 campos -> Formato SIMPLIFICADO (3 bloques)"
            )
            return False

    except Exception as e:
        debug_print(
            f"[Write_Presets] Error detectando formato: {e}, asumiendo formato simplificado"
        )
        return False


def detect_shotname_format_from_script():
    """
    Detecta el formato del shotname basado en el script actual de Nuke.
    Usa el modulo compartido LGA_ToolPack_NamingUtils si esta disponible.
    Retorna True si es formato con descripcion (5 bloques), False si es simplificado (3 bloques).
    Si no hay script guardado, asume formato simplificado.
    """
    if naming_utils_available:
        try:
            base_name = get_script_base_name()
            if base_name is None:
                debug_print(
                    "[Write_Presets] No hay script guardado, asumiendo formato simplificado (3 bloques)"
                )
                return False

            debug_print(f"[Write_Presets] Base name del script: {base_name}")
            parts = base_name.split("_")
            debug_print(f"[Write_Presets] Partes: {parts}")

            has_description = detect_shotname_format(base_name)

            if has_description:
                debug_print(
                    "[Write_Presets] Formato CON DESCRIPCION (5 bloques) detectado usando modulo compartido"
                )
            else:
                debug_print(
                    "[Write_Presets] Formato SIMPLIFICADO (3 bloques) detectado usando modulo compartido"
                )

            return has_description
        except Exception as e:
            debug_print(
                f"[Write_Presets] Error usando modulo compartido: {e}, usando funcion local"
            )
            return detect_shotname_format_local()
    else:
        # Fallback a funcion local si el modulo no esta disponible
        return detect_shotname_format_local()


def adjust_tcl_formulas(presets, has_description):
    """
    Ajusta las formulas TCL en los presets segun el formato detectado.
    Si has_description=True, suma 2 a todos los indices TCL.
    Si has_description=False, usa los indices del .ini tal como estan (ya ajustados para 3 bloques).
    """
    if not has_description:
        debug_print(
            "[Write_Presets] Usando formulas TCL tal como estan en .ini (formato simplificado)"
        )
        return presets

    debug_print(
        "[Write_Presets] Ajustando formulas TCL para formato con descripcion (+2 bloques)"
    )
    adjusted_presets = {}

    for section_name, preset in presets.items():
        adjusted_preset = preset.copy()

        # Buscar y ajustar formulas TCL en file_pattern
        if "file_pattern" in adjusted_preset:
            original_pattern = adjusted_preset["file_pattern"]

            # Buscar patrones como "] 0 X]" o "] 0 X ]" (con o sin espacio antes del ultimo ]) y sumarles 2
            def adjust_index(match):
                current_index = int(match.group(1))
                new_index = current_index + 2
                debug_print(
                    f"[Write_Presets] Ajustando indice TCL: {current_index} -> {new_index}"
                )
                # Preservar el formato original (con o sin espacio)
                has_space = match.group(0).endswith(" ]")
                return f"] 0 {new_index} ]" if has_space else f"] 0 {new_index}]"

            # Regex que acepta espacios opcionales antes del ultimo ]
            adjusted_pattern = re.sub(
                r"\] 0 (\d+)\s*\]", adjust_index, original_pattern
            )
            adjusted_preset["file_pattern"] = adjusted_pattern

            if original_pattern != adjusted_pattern:
                debug_print(f"[Write_Presets] Formula ajustada en {section_name}")

        adjusted_presets[section_name] = adjusted_preset

    return adjusted_presets


def load_presets():
    """Lee el archivo .ini y retorna un diccionario con los presets"""
    config = configparser.ConfigParser(interpolation=None)  # Desactivar interpolación
    ini_path = os.path.join(os.path.dirname(__file__), "LGA_Write_Presets.ini")
    config.read(ini_path)
    return {section: dict(config[section]) for section in config.sections()}


def create_write_from_preset(preset, user_text=None, modified_file_pattern=None):
    """
    Crea un Write node y nodos adicionales según el preset

    Args:
        preset: Diccionario con la configuracion del preset
        user_text: Texto ingresado por el usuario (si aplica, reemplaza ****)
        modified_file_pattern: File pattern modificado desde la ventana de verificacion (opcional)
    """
    nuke.Undo().begin("Create Write Node")

    # Obtener nodo seleccionado o crear NoOp
    selected_node = get_selected_node()
    current_node = selected_node or nuke.createNode("NoOp")

    # Variables para posicionamiento
    preferences_node = nuke.toNode("preferences")
    if preferences_node:
        # Obtener el valor del knob si el nodo existe
        dot_scale = preferences_node["dot_node_scale"].value()
        dot_width = int(dot_scale * 12)
    else:
        # Si el nodo 'preferences' no existe, usar un valor por defecto
        debug_print(
            "Advertencia: No se encontro el nodo 'preferences'. Usando tamaño de Dot por defecto."
        )
        dot_width = 12  # O el valor por defecto que consideres apropiado

    distanciaX = 180
    distanciaY = 150

    # Convertir strings a booleanos
    switch_enabled = preset["switch_node"].lower() == "true"
    create_directories = preset["create_directories"].lower() == "true"
    backdrop_enabled = preset["backdrop"].lower() == "true"

    # Crear nodos según el preset
    if switch_enabled:
        # Crear Dot
        dot_node = nuke.nodes.Dot()
        dot_node.setInput(0, current_node)
        dot_node.setXpos(
            int(
                current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2)
            )
        )
        dot_node.setYpos(current_node.ypos() + current_node.screenHeight() + distanciaY)

        # Crear Switch
        switch_node = nuke.nodes.Switch()
        switch_node.setInput(0, dot_node)
        switch_node.setInput(1, None)
        switch_node["which"].setValue(int(preset["switch_which"]))
        switch_node["disable"].setValue(preset["switch_disabled"].lower() == "true")
        switch_node.setXpos(
            dot_node.xpos() - (switch_node.screenWidth() // 2) + (dot_width // 2)
        )
        switch_node.setYpos(dot_node.ypos() + distanciaY)

        # Crear Write
        write_node = nuke.nodes.Write()
        write_node.setInput(0, dot_node)
        write_node.setXpos(
            int(
                dot_node.xpos()
                + (dot_width / 2)
                - (write_node.screenWidth() // 2)
                - distanciaX
            )
        )
        write_node.setYpos(dot_node.ypos())

        # Reconectar nodos descendentes al Switch
        if selected_node:
            downstream_nodes = current_node.dependent(
                nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False
            )
            for node in downstream_nodes:
                for i in range(node.inputs()):
                    if node.input(i) == current_node:
                        node.setInput(i, switch_node)

    else:
        # Crear solo Write
        debug_print(
            "[DEBUG] Nodo seleccionado:",
            selected_node.name() if selected_node else None,
        )
        debug_print(
            "[DEBUG] Tipo de nodo seleccionado:",
            selected_node.Class() if selected_node else None,
        )
        debug_print(
            "[DEBUG] Posicion X nodo seleccionado:",
            selected_node.xpos() if selected_node else None,
        )
        debug_print(
            "[DEBUG] screenWidth nodo seleccionado:",
            selected_node.screenWidth() if selected_node else None,
        )

        write_node = nuke.nodes.Write()
        write_node.setInput(0, current_node)
        write_x = (
            current_node.xpos()
            + (current_node.screenWidth() // 2)
            - (write_node.screenWidth() // 2)
        )
        debug_print("[DEBUG] Posicion X a setear para Write:", write_x)
        write_node.setXpos(write_x)
        write_node.setYpos(current_node.ypos() + 100)
        debug_print(
            "[DEBUG] Posicion X real del Write luego de crearlo:", write_node.xpos()
        )

        # Reconectar nodos descendentes al Write
        if selected_node:
            downstream_nodes = current_node.dependent(
                nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False
            )
            for node in downstream_nodes:
                for i in range(node.inputs()):
                    if node.input(i) == current_node:
                        node.setInput(i, write_node)

    # Configurar Write node
    write_node["file_type"].setValue(preset["file_type"])
    write_node["channels"].setValue(preset["channels"])

    # Configurar parámetros específicos según el tipo de archivo
    if preset["file_type"] == "tiff":
        write_node["datatype"].setValue(preset["datatype"])
        write_node["colorspace"].setValue(preset["colorspace"])
    elif preset["file_type"] == "mov":
        write_node["mov64_format"].setValue(preset["mov64_format"])
        write_node["mov64_codec"].setValue(preset["mov64_codec"])
        write_node["mov_prores_codec_profile"].setValue(
            preset["mov_prores_codec_profile"]
        )
        write_node["mov64_pixel_format"].setValue(int(preset["mov64_pixel_format"]))
        write_node["mov64_quality"].setValue(preset["mov64_quality"])
        write_node["mov64_fast_start"].setValue(
            preset["mov64_fast_start"].lower() == "true"
        )
        write_node["mov64_write_timecode"].setValue(
            preset["mov64_write_timecode"].lower() == "true"
        )
        write_node["mov64_gop_size"].setValue(int(preset["mov64_gop_size"]))
        write_node["mov64_b_frames"].setValue(int(preset["mov64_b_frames"]))
        write_node["mov64_bitrate"].setValue(int(preset["mov64_bitrate"]))
        write_node["mov64_bitrate_tolerance"].setValue(
            int(preset["mov64_bitrate_tolerance"])
        )
        write_node["mov64_quality_min"].setValue(int(preset["mov64_quality_min"]))
        write_node["mov64_quality_max"].setValue(int(preset["mov64_quality_max"]))
        write_node["colorspace"].setValue(preset["colorspace"])
    elif preset["file_type"] == "mxf":
        write_node["mxf_codec_profile_knob"].setValue(preset["mxf_codec_profile_knob"])
        write_node["mxf_advanced"].setValue(preset["mxf_advanced"].lower() == "true")
        write_node["dataRange"].setValue(preset.get("dataRange"))
        write_node["colorspace"].setValue(preset["colorspace"])
    elif preset["file_type"] == "png":
        write_node["datatype"].setValue(
            "16 bit" if preset.get("datatype", "16 bit") == "16 bit" else "8 bit"
        )
        write_node["colorspace"].setValue(preset["colorspace"])
    else:
        if preset["file_type"] == "exr":
            write_node["compression"].setValue(preset["compression"])
            write_node["dw_compression_level"].setValue(
                int(preset["compression_level"])
            )
            write_node["colorspace"].setValue(preset["colorspace"])

    write_node["create_directories"].setValue(create_directories)

    # Configurar el patrón de archivo
    # Si hay un file_pattern modificado desde la ventana de verificacion, usarlo
    if modified_file_pattern:
        base_pattern = modified_file_pattern
    else:
        base_pattern = preset["file_pattern"]

    # Reemplazar **** con user_text si aplica
    if user_text and "****" in base_pattern:
        file_pattern = base_pattern.replace("****", user_text)
    else:
        file_pattern = base_pattern

    write_node["file"].setValue(file_pattern)

    # Configurar nombre del Write
    if preset["button_type"] == "read":
        write_node["name"].setValue(get_write_name_from_read(current_node, "Denoised"))
    else:
        # Normalizar el texto del usuario para el nombre del nodo
        text_to_normalize = user_text if user_text else preset["button_name"]
        normalized_text = normalize_node_name(text_to_normalize)
        base_write_name = "Write_" + normalized_text
        write_node["name"].setValue(get_unique_node_name(base_write_name))

    # Añadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob("User", "User"))
    write_node.addKnob(nuke.String_Knob("render_time", "Render Time"))
    write_node["render_time"].setValue("00:18:27")

    # Alinear Write con Dot después de añadir todos los knobs
    if switch_enabled:
        align_write_to_dot(dot_node, write_node)

    # Crear backdrop si es necesario
    if backdrop_enabled:
        nodes = [write_node, dot_node, switch_node]
        bd_x = min(node.xpos() for node in nodes) - 64
        bd_y = min(node.ypos() for node in nodes) - 115
        bd_w = max(node.xpos() + node.screenWidth() for node in nodes) - bd_x + 63
        bd_h = max(node.ypos() + node.screenHeight() for node in nodes) - bd_y + 50

        backdrop_node = nuke.nodes.BackdropNode(
            xpos=bd_x,
            ypos=bd_y,
            bdwidth=bd_w,
            bdheight=bd_h,
            tile_color=int(preset["backdrop_color"], 16),
            note_font=preset["backdrop_font"],
            note_font_size=int(preset["backdrop_font_size"]),
            label=user_text,
            z_order=4,
            name="Backdrop_preRender",
        )

        backdrop_node.hideControlPanel()

        if oz_backdrop_available:
            backdrop_node["selected"].setValue(True)
            LGA_oz_backdropReplacer.replace_with_oz_backdrop()
            # Obtener el nuevo backdrop después del reemplazo
            selected_nodes = nuke.selectedNodes("BackdropNode")
            if selected_nodes:
                new_backdrop_node = selected_nodes[0]
                new_backdrop_node.hideControlPanel()
                new_backdrop_node["selected"].setValue(False)

    # Eliminar NoOp temporal si se creó y es un NoOp
    if not selected_node and current_node.Class() == "NoOp":
        nuke.delete(current_node)

    # Abrir propiedades del Write y seleccionarlo
    write_node.showControlPanel()
    for node in nuke.allNodes():
        node["selected"].setValue(False)
    write_node["selected"].setValue(True)

    nuke.Undo().end()


class ColoredItemDelegate(QStyledItemDelegate):
    def __init__(self, table_widget=None, parent=None):
        super().__init__(parent)
        self.table_widget = table_widget

    def paint(self, painter, option, index):
        text = index.data()
        if text:
            painter.save()

            # Verificar si el item esta deshabilitado
            is_enabled = True
            if self.table_widget:
                row = index.row()
                col = index.column()
                item = self.table_widget.item(row, col)
                if item:
                    # Verificar si el item tiene el flag ItemIsEnabled
                    is_enabled = bool(item.flags() & Qt.ItemIsEnabled)

            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, QColor("#424242"))

            padding_left = 5
            adjusted_rect = option.rect.adjusted(padding_left, 0, 0, 0)

            # Separar prefijo y nombre
            parts = text.split(" ", 1)
            prefix, name = parts if len(parts) > 1 else ("", text)

            # Color base segun si esta habilitado o no
            if not is_enabled:
                base_color = QColor("#666666")  # Gris para items deshabilitados
                prefix_color_script = QColor("#666666")
                prefix_color_read = QColor("#666666")
            else:
                base_color = QColor("white")
                prefix_color_script = QColor("#ed2464")
                prefix_color_read = QColor("#66e2ff")

            # Dibujar prefijo
            if prefix == "[Script]":
                painter.setPen(prefix_color_script)
                painter.drawText(
                    adjusted_rect, Qt.AlignLeft | Qt.AlignVCenter, prefix + " "
                )
                prefix_width = painter.fontMetrics().horizontalAdvance(prefix + " ")
            elif prefix == "[Read]":
                painter.setPen(prefix_color_read)
                painter.drawText(
                    adjusted_rect, Qt.AlignLeft | Qt.AlignVCenter, prefix + " "
                )
                prefix_width = painter.fontMetrics().horizontalAdvance(prefix + " ")
            else:
                prefix_width = 0

            # Dibujar nombre con formato de color
            remaining_rect = adjusted_rect.adjusted(prefix_width, 0, 0, 0)
            painter.setPen(base_color)

            # Buscar formatos en el nombre
            for fmt, color in FORMAT_COLORS.items():
                if fmt in name.upper():
                    # Dividir el texto en partes
                    parts = name.split(fmt, 1)

                    # Dibujar parte antes del formato
                    before_width = painter.fontMetrics().horizontalAdvance(parts[0])
                    painter.drawText(
                        remaining_rect, Qt.AlignLeft | Qt.AlignVCenter, parts[0]
                    )

                    # Dibujar formato con color (gris si esta deshabilitado)
                    fmt_rect = remaining_rect.adjusted(before_width, 0, 0, 0)
                    fmt_color = QColor("#666666") if not is_enabled else QColor(color)
                    painter.setPen(fmt_color)
                    painter.drawText(fmt_rect, Qt.AlignLeft | Qt.AlignVCenter, fmt)

                    # Dibujar parte restante
                    remaining_rect = fmt_rect.adjusted(
                        painter.fontMetrics().horizontalAdvance(fmt), 0, 0, 0
                    )
                    painter.setPen(base_color)
                    painter.drawText(
                        remaining_rect,
                        Qt.AlignLeft | Qt.AlignVCenter,
                        parts[1] if len(parts) > 1 else "",
                    )
                    break
            else:
                # Si no encuentra formato, dibujar texto normal
                painter.drawText(remaining_rect, Qt.AlignLeft | Qt.AlignVCenter, name)

            painter.restore()


class ShiftClickTableWidget(QTableWidget):
    """
    QTableWidget personalizado que detecta Shift+Click y emite una senal personalizada.
    """

    def __init__(self, rows, columns, parent=None):
        super().__init__(rows, columns, parent)
        self.shift_click_callback = None  # type: ignore

    def mousePressEvent(self, event):
        """Detecta Shift+Click y llama al callback si esta definido."""
        debug_print("[ShiftClickTableWidget] mousePressEvent detectado")
        debug_print(
            f"[ShiftClickTableWidget] Boton: {event.button()}, Modifiers: {event.modifiers()}"
        )
        debug_print(f"[ShiftClickTableWidget] ShiftModifier: {Qt.ShiftModifier}")
        debug_print(
            f"[ShiftClickTableWidget] Shift presionado: {bool(event.modifiers() & Qt.ShiftModifier)}"
        )

        # Obtener el item bajo el mouse para verificar si esta habilitado
        item = self.itemAt(event.pos())
        if item is not None:
            # Verificar si el item esta deshabilitado usando flags
            table_item = self.item(item.row(), item.column())
            if table_item and not (table_item.flags() & Qt.ItemIsEnabled):
                debug_print(
                    "[ShiftClickTableWidget] Item deshabilitado, ignorando click"
                )
                event.ignore()
                return

        if event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier:
            debug_print("[ShiftClickTableWidget] Shift+Click detectado!")
            # Obtener la celda bajo el mouse
            debug_print(f"[ShiftClickTableWidget] Item encontrado: {item is not None}")
            if item is not None:
                row = item.row()
                column = item.column()
                debug_print(f"[ShiftClickTableWidget] Fila: {row}, Columna: {column}")
                debug_print(
                    f"[ShiftClickTableWidget] Callback disponible: {self.shift_click_callback is not None}"
                )
                if self.shift_click_callback:
                    debug_print("[ShiftClickTableWidget] Llamando al callback...")
                    # Seleccionar la fila antes de llamar al callback
                    self.selectRow(row)
                    # Llamar al callback con la fila y columna
                    self.shift_click_callback(row, column)
                    # Aceptar el evento para evitar que se propague
                    event.accept()
                    return
        # Si no es Shift+Click, procesar normalmente
        debug_print("[ShiftClickTableWidget] No es Shift+Click, procesando normalmente")
        super().mousePressEvent(event)


class SelectedNodeInfo(QWidget):
    def __init__(self, parent=None):
        super(SelectedNodeInfo, self).__init__(parent)

        # Detectar formato del shotname y ajustar presets
        debug_print(
            "[Write_Presets] ========== INICIANDO DETECCION DE FORMATO =========="
        )
        has_description = detect_shotname_format_from_script()

        # Cargar presets base y ajustarlos segun el formato detectado
        base_presets = load_presets()
        self.presets = adjust_tcl_formulas(base_presets, has_description)

        debug_print(
            f"[Write_Presets] Formato detectado: {'CON DESCRIPCION (5 bloques)' if has_description else 'SIMPLIFICADO (3 bloques)'}"
        )
        debug_print("[Write_Presets] ========== DETECCION COMPLETADA ==========")

        self.options = []
        for section, preset in self.presets.items():
            prefix = "[Script]" if preset["button_type"] == "script" else "[Read]"
            self.options.append(f"{prefix} {preset['button_name']}")
        self.initUI()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_row = self.table.currentRow()
            if current_row >= 0:
                # Verificar si el item esta habilitado antes de procesar
                item = self.table.item(current_row, 0)
                if item and (item.flags() & Qt.ItemIsEnabled):
                    self.handle_render_option(current_row, 0)
        elif event.key() in (Qt.Key_Up, Qt.Key_Down):
            QWidget.keyPressEvent(self, event)
        else:
            event.ignore()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("RENDER TYPE")

        # Crear un widget contenedor principal
        main_container = QWidget(self)
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet(
            """
            QWidget#mainContainer {
                background-color: #282828;
                border-radius: 9px;
            }
        """
        )

        # Layout principal
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(10, 6, 10, 8)

        # Crear la barra de título
        title_bar = QWidget(self)
        title_bar.setFixedHeight(20)
        title_bar.setAutoFillBackground(True)
        title_bar.setStyleSheet(
            """
            QWidget {
                background-color: #282828;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """
        )

        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.addStretch(1)

        title_label = QPushButton(self.windowTitle(), self)
        title_label.setStyleSheet(
            "background-color: none; color: #B0B0B0; border: none; font-weight: bold;"
        )
        title_label.setEnabled(False)
        title_bar_layout.addWidget(title_label)

        title_bar_layout.addStretch(1)

        close_button = QPushButton("X", self)
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet(
            "background-color: none; color: #B0B0B0; border: none;"
        )
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)
        title_bar_layout.setSpacing(0)

        main_layout.addWidget(title_bar)

        # Crear y configurar la tabla (una sola vez)
        self.table = ShiftClickTableWidget(len(self.options), 1, self)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Cargar datos en la tabla
        self.load_render_options()

        # Conectar eventos de clic
        self.table.cellClicked.connect(self.handle_render_option)
        # Conectar Shift+Click
        self.table.shift_click_callback = self.handle_render_option_shift  # type: ignore

        main_layout.addWidget(self.table)

        # Verificar si hay un Write seleccionado para abrir directamente la ventana de edición
        selected_write = None
        for node in nuke.selectedNodes():
            if node.Class() == "Write":
                selected_write = node
                break

        if selected_write:
            # Si hay un Write seleccionado, abrir directamente la ventana de edición
            debug_print(
                f"[Write_Presets] Write seleccionado detectado: {selected_write.name()}"
            )
            # Llamar a la función de edición después de un pequeño delay para asegurar que la ventana esté inicializada
            QTimer.singleShot(10, lambda: self.show_write_path_window())
            return  # No crear el botón ni continuar con la interfaz

        # Nota: Ya no se crea el botón "Show selected Write node file path"
        # La funcionalidad ahora es completamente automática

        # Layout de la ventana principal
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(main_container)

        # Ajustar el tamaño de la ventana y posicionarla
        self.adjust_window_size()

        # Seleccionar la primera fila habilitada y establecer el foco
        # (después de que se hayan cargado los items)
        first_enabled_row = -1
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and (item.flags() & Qt.ItemIsEnabled):
                first_enabled_row = row
                break

        if first_enabled_row >= 0:
            self.table.selectRow(first_enabled_row)
        self.table.setFocus()

    def is_script_saved(self):
        """Verifica si el script de Nuke esta guardado."""
        script_path = nuke.root().name()
        return script_path and script_path != "Root"

    def load_render_options(self):
        """Carga las opciones de render en la tabla con formato de color."""
        self.table.setItemDelegate(ColoredItemDelegate(self.table))

        # Verificar si el script esta guardado
        script_saved = self.is_script_saved()

        for row, name in enumerate(self.options):
            # Extraer el nombre real del preset
            preset_number = row + 1
            preset = self.presets[f"Preset{preset_number}"]
            display_name = preset["button_name"]

            item = QTableWidgetItem(
                f"[{preset['button_type'].capitalize()}] {display_name}"
            )
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            # Deshabilitar items de tipo script si el script no esta guardado
            # QTableWidgetItem no tiene setEnabled(), usamos flags en su lugar
            if preset["button_type"] == "script" and not script_saved:
                # Quitar flags de habilitado y seleccionable
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)

            self.table.setItem(row, 0, item)

        self.table.resizeColumnsToContents()
        self.table.setStyleSheet(
            """
            QTableView {
                background-color: #222222;
                border: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QTableView::item {
                padding-left: 0px;    /* Aumentado el padding izquierdo */
                padding-right: 0px;   /* Aumentado el padding derecho */
                padding-top: 5px;      /* Mantener padding vertical */
                padding-bottom: 5px;
            }
            QTableView::item:selected {
                background-color: #212121;
            }
        """
        )

    def adjust_window_size(self):
        """Ajusta el tamaño de la ventana basado en el contenido de la tabla y la posición del cursor."""
        # Desactivar temporalmente el estiramiento de la última columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana basado en el ancho de las columnas y el texto más ancho
        width = self.table.verticalHeader().width()  # Un poco de relleno para estética
        for i in range(self.table.columnCount()):
            width += (
                self.table.columnWidth(i) + 50
            )  # Un poco más de relleno entre columnas

        # Ajustar el ancho adicional basado en el texto más ancho
        longest_text = max(self.options, key=len)
        font_metrics = self.table.fontMetrics()
        text_width = (
            font_metrics.horizontalAdvance(longest_text) + 50
        )  # Un poco de relleno adicional
        width = max(width, text_width)

        # Asegurarse de que el ancho no supera el 80% del ancho de pantalla
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        max_width = screen_rect.width() * 0.8
        final_width = min(width, max_width)

        # Calcular la altura basada en la altura de los headers y las filas
        height = (
            self.table.horizontalHeader().height() + 20
        )  # Altura del encabezado + espacio adicional
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)

        # Agregar un relleno total de 10 píxeles
        height += 0

        # Incluir la altura de la barra de título personalizada
        title_bar_height = 20
        height += title_bar_height

        # Nota: Ya no hay botón extra que sumar a la altura

        # Asegurarse de que la altura no supera el 80% del alto de pantalla
        max_height = screen_rect.height() * 0.8
        final_height = min(height, max_height)

        # Reactivar el estiramiento de la última columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamaño de la ventana
        self.resize(final_width, final_height)

        # Obtener la posición actual del puntero del mouse
        cursor_pos = QCursor.pos()
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        # Calcular la posición inicial centrada en el cursor
        posx = cursor_pos.x() - final_width // 2
        posy = cursor_pos.y() - final_height // 2

        # Ajustar la posición si la ventana se sale de la pantalla
        if posx + final_width > screen_rect.right():
            posx = screen_rect.right() - final_width
        if posx < screen_rect.left():
            posx = screen_rect.left()

        if posy + final_height > screen_rect.bottom():
            posy = screen_rect.bottom() - final_height
        if posy < screen_rect.top():
            posy = screen_rect.top()

        # Ajustar el tamaño de la ventana y moverla a la posición calculada
        self.resize(final_width, final_height)
        self.move(posx, posy)

    def handle_render_option(self, row, column):
        """Maneja el clic normal en un preset, mostrando ventana de verificacion."""
        if not path_check_available:
            # Si el modulo no esta disponible, comportarse como Shift+Click (crear directamente)
            self.handle_render_option_shift(row, column)
            return

        selected_option = self.options[row]
        preset_number = row + 1
        preset = self.presets[f"Preset{preset_number}"]

        # Verificar si es un preset de tipo script y el script no esta guardado
        if preset["button_type"] == "script" and not self.is_script_saved():
            debug_print(
                "[Write_Presets] Preset de tipo script deshabilitado: script no guardado"
            )
            return

        dialog_enabled = preset["dialog_enabled"].lower() == "true"

        if dialog_enabled:
            esc_exit, user_text = show_name_input_dialog(
                initial_text=preset["dialog_default_name"]
            )
            if not esc_exit and user_text is not None:
                # Guardar preset y user_text para usar en el callback
                self._pending_preset = preset
                self._pending_user_text = user_text

                # Cerrar y mostrar ventana de verificacion
                self.close()
                show_path_check_window(
                    preset, user_text, self._create_write_from_pending
                )
        else:
            # Guardar preset para usar en el callback
            self._pending_preset = preset
            self._pending_user_text = None

            # Cerrar y mostrar ventana de verificacion
            self.close()
            show_path_check_window(preset, None, self._create_write_from_pending)

    def handle_render_option_shift(self, row, column):
        """Maneja Shift+Click en un preset, creando el Write directamente sin ventana."""
        selected_option = self.options[row]
        preset_number = row + 1
        preset = self.presets[f"Preset{preset_number}"]

        # Verificar si es un preset de tipo script y el script no esta guardado
        if preset["button_type"] == "script" and not self.is_script_saved():
            debug_print(
                "[Write_Presets] Preset de tipo script deshabilitado: script no guardado"
            )
            return

        self.close()

        dialog_enabled = preset["dialog_enabled"].lower() == "true"

        if dialog_enabled:
            esc_exit, user_text = show_name_input_dialog(
                initial_text=preset["dialog_default_name"]
            )
            if not esc_exit and user_text is not None:
                create_write_from_preset(preset, user_text)
        else:
            create_write_from_preset(preset)

    def _create_write_from_pending(self, modified_file_pattern=None):
        """
        Callback que crea el Write usando los valores pendientes.

        Args:
            modified_file_pattern: File pattern modificado desde la ventana de verificacion (opcional)
        """
        create_write_from_preset(
            self._pending_preset, self._pending_user_text, modified_file_pattern
        )

    def show_write_path_window(self):
        """Abre una ventana editable con el contenido del Write seleccionado."""
        from LGA_Write_Presets_Check import (
            PathCheckWindow,
            evaluate_file_pattern,
            get_shot_folder_parts,
            normalize_path_preserve_case,
        )

        # Obtener el Write seleccionado
        selected_write = None
        for node in nuke.selectedNodes():
            if node.Class() == "Write":
                selected_write = node
                break

        if not selected_write:
            debug_print("[Write_Presets] No hay ningun nodo Write seleccionado.")
            return

        # Obtener el file_pattern del Write seleccionado
        file_pattern = selected_write["file"].value()
        if not file_pattern:
            debug_print("[Write_Presets] El Write seleccionado no tiene file pattern.")
            return

        self.close()

        # Evaluar y normalizar el path para mostrar el resultado final
        evaluated_path, original_extensions = evaluate_file_pattern(file_pattern)
        normalized_path = None
        if evaluated_path:
            normalized_path = normalize_path_preserve_case(evaluated_path)

        # Obtener path del script para calcular shot_folder_parts
        script_path = nuke.root().name()
        if not script_path or script_path == "Root":
            script_path = None
        shot_folder_parts = get_shot_folder_parts(script_path)

        # Callback para aplicar cambios al Write seleccionado
        def apply_changes_to_write(modified_pattern):
            if modified_pattern:
                # Aplicar el patrón modificado al Write seleccionado
                nuke.Undo().begin("Modify Write File Pattern")
                selected_write["file"].setValue(modified_pattern)
                nuke.Undo().end()
                debug_print(
                    f"[Write_Presets] File pattern actualizado en Write: {selected_write.name()}"
                )

        # Crear y mostrar la ventana editable
        global app, window
        app = QApplication.instance() or QApplication([])
        window = PathCheckWindow(
            file_pattern,
            normalized_path,
            shot_folder_parts,
            apply_changes_to_write,
            original_extensions=original_extensions,
        )
        window.exec_()


def normalize_node_name(name):
    """
    Normaliza el nombre de un nodo para cumplir con las reglas de Nuke:
    - Reemplaza espacios y guiones medios con guiones bajos
    - Elimina acentos y caracteres especiales
    - Solo permite letras, numeros y guiones bajos
    - Asegura que empiece con letra o guion bajo
    - Elimina guiones bajos consecutivos
    """
    if not name:
        return "Write"

    # Convertir a string si no lo es
    name = str(name)

    # Normalizar unicode y eliminar acentos
    normalized = unicodedata.normalize("NFD", name)
    # Filtrar solo caracteres ASCII
    ascii_name = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # Reemplazar espacios y guiones medios con guiones bajos
    ascii_name = ascii_name.replace(" ", "_").replace("-", "_")

    # Eliminar cualquier caracter que no sea letra, numero o guion bajo
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "", ascii_name)

    # Eliminar guiones bajos consecutivos
    clean_name = re.sub(r"_+", "_", clean_name)

    # Eliminar guiones bajos al inicio y final
    clean_name = clean_name.strip("_")

    # Asegurar que empiece con letra o guion bajo si empieza con numero
    if clean_name and clean_name[0].isdigit():
        clean_name = "_" + clean_name

    # Si el nombre queda vacio, usar un nombre por defecto
    if not clean_name:
        clean_name = "Write"

    return clean_name


def check_and_fix_selected_write():
    """
    Verifica si el nodo seleccionado es un Write y corrige su nombre si tiene caracteres ilegales
    """
    selected_node = get_selected_node()
    if selected_node and selected_node.Class() == "Write":
        current_name = selected_node.name()
        normalized_name = normalize_node_name(current_name)

        if current_name != normalized_name:
            # Verificar que el nombre normalizado sea unico
            unique_name = get_unique_node_name(normalized_name)
            selected_node.setName(unique_name)
            debug_print(
                f"Nombre del Write corregido: '{current_name}' -> '{unique_name}'"
            )
            return True
    return False


# El resto del código se mantiene igual
app = None
window = None


def main():
    global app, window

    # Verificar y corregir Write seleccionado antes de mostrar la interfaz
    # Si se corrigio un Write, se mostrara un mensaje en la consola de Nuke.
    check_and_fix_selected_write()

    app = QApplication.instance() or QApplication([])
    window = SelectedNodeInfo()
    window.show()


# Llamar a main() para iniciar la aplicacion
if __name__ == "__main__":
    main()
