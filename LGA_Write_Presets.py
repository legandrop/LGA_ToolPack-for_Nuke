"""
_____________________________________________________________________________

  LGA_Write_Presets v2.01 | Lega

  Creates Write nodes with predefined settings for different purposes.
  Supports both script-based and Read node-based path generation.
_____________________________________________________________________________

"""

from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QDialog,
    QLabel,
    QLineEdit,
    QDesktopWidget,
    QFrame,
    QStyledItemDelegate,
    QStyle,
)
from PySide2.QtCore import Qt
from PySide2.QtGui import QCursor, QPalette, QColor, QKeyEvent, QBrush
import nuke
import sys
import os
import configparser
import ntpath
import posixpath

# Intentar importar el modulo LGA_oz_backdropReplacer
script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)

try:
    import LGA_oz_backdropReplacer

    oz_backdrop_available = True
except ImportError:
    oz_backdrop_available = False
    nuke.tprint(
        "El modulo LGA_oz_backdropReplacer no esta disponible. Continuando sin reemplazar el backdrop."
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
            '<span style="font-size:7pt; color:#AAAAAA;">Ctrl+Enter to confirm</span>',
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
                if event.modifiers() == Qt.ControlModifier:
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
    avail_space = QDesktopWidget().availableGeometry(cursor_pos)
    posx = min(max(cursor_pos.x() - 100, avail_space.left()), avail_space.right() - 200)
    posy = min(max(cursor_pos.y() - 80, avail_space.top()), avail_space.bottom() - 150)
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

        base_name = "Write_" + file_name
        return get_unique_write_name(base_name)
    else:
        return "Write_" + default_name


def get_unique_write_name(base_name):
    """Genera un nombre único para el Write node agregando sufijos numéricos si es necesario"""
    index = 1
    node_name = base_name
    while nuke.exists(node_name):
        node_name = f"{base_name}_{index}"
        index += 1
    return node_name


def load_presets():
    """Lee el archivo .ini y retorna un diccionario con los presets"""
    config = configparser.ConfigParser(interpolation=None)  # Desactivar interpolación
    ini_path = os.path.join(os.path.dirname(__file__), "LGA_Write_Presets.ini")
    config.read(ini_path)
    return {section: dict(config[section]) for section in config.sections()}


def create_write_from_preset(preset, user_text=None):
    """Crea un Write node y nodos adicionales según el preset"""
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
        nuke.tprint(
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
        print(
            "[DEBUG] Nodo seleccionado:",
            selected_node.name() if selected_node else None,
        )
        print(
            "[DEBUG] Tipo de nodo seleccionado:",
            selected_node.Class() if selected_node else None,
        )
        print(
            "[DEBUG] Posicion X nodo seleccionado:",
            selected_node.xpos() if selected_node else None,
        )
        print(
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
        print("[DEBUG] Posicion X a setear para Write:", write_x)
        write_node.setXpos(write_x)
        write_node.setYpos(current_node.ypos() + 100)
        print("[DEBUG] Posicion X real del Write luego de crearlo:", write_node.xpos())

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
    if user_text and "****" in preset["file_pattern"]:
        file_pattern = preset["file_pattern"].replace("****", user_text)
    else:
        file_pattern = preset["file_pattern"]
    write_node["file"].setValue(file_pattern)

    # Configurar nombre del Write
    if preset["button_type"] == "read":
        write_node["name"].setValue(get_write_name_from_read(current_node, "Denoised"))
    else:
        # Normalizar el texto del usuario para el nombre del nodo
        normalized_user_text = (
            user_text.replace("-", "_") if user_text else preset["button_name"]
        )
        base_write_name = "Write_" + normalized_user_text
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
    def paint(self, painter, option, index):
        text = index.data()
        if text:
            painter.save()

            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, QColor("#424242"))

            padding_left = 5
            adjusted_rect = option.rect.adjusted(padding_left, 0, 0, 0)

            # Separar prefijo y nombre
            parts = text.split(" ", 1)
            prefix, name = parts if len(parts) > 1 else ("", text)

            # Dibujar prefijo
            if prefix == "[Script]":
                painter.setPen(QColor("#ed2464"))
                painter.drawText(
                    adjusted_rect, Qt.AlignLeft | Qt.AlignVCenter, prefix + " "
                )
                prefix_width = painter.fontMetrics().horizontalAdvance(prefix + " ")
            elif prefix == "[Read]":
                painter.setPen(QColor("#66e2ff"))
                painter.drawText(
                    adjusted_rect, Qt.AlignLeft | Qt.AlignVCenter, prefix + " "
                )
                prefix_width = painter.fontMetrics().horizontalAdvance(prefix + " ")
            else:
                prefix_width = 0

            # Dibujar nombre con formato de color
            remaining_rect = adjusted_rect.adjusted(prefix_width, 0, 0, 0)
            painter.setPen(QColor("white"))

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

                    # Dibujar formato con color
                    fmt_rect = remaining_rect.adjusted(before_width, 0, 0, 0)
                    painter.setPen(QColor(color))
                    painter.drawText(fmt_rect, Qt.AlignLeft | Qt.AlignVCenter, fmt)

                    # Dibujar parte restante
                    remaining_rect = fmt_rect.adjusted(
                        painter.fontMetrics().horizontalAdvance(fmt), 0, 0, 0
                    )
                    painter.setPen(QColor("white"))
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


class SelectedNodeInfo(QWidget):
    def __init__(self, parent=None):
        super(SelectedNodeInfo, self).__init__(parent)
        self.presets = load_presets()
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
        self.table = QTableWidget(len(self.options), 1, self)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Cargar datos en la tabla
        self.load_render_options()

        # Conectar solo el evento de clic
        self.table.cellClicked.connect(self.handle_render_option)

        main_layout.addWidget(self.table)

        # --- Agregar botón personalizado debajo de la tabla ---
        self.show_path_button = QPushButton("Show selected Write node file path")
        self.show_path_button.setStyleSheet(
            """
            QPushButton {
                background-color: #443a91;
                color: #cccccc;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 0px;
                margin-top: 2px;
                margin-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #372e7a;
            }
            QPushButton:pressed {
                background-color: #2d265e;
            }
            """
        )
        self.show_path_button.setCursor(Qt.PointingHandCursor)
        self.show_path_button.clicked.connect(self.show_write_path_window)
        main_layout.addWidget(self.show_path_button)
        # --- Fin botón personalizado ---

        # Layout de la ventana principal
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(main_container)

        # Ajustar el tamaño de la ventana y posicionarla
        self.adjust_window_size()

        # Seleccionar la primera fila y establecer el foco
        self.table.selectRow(0)
        self.table.setFocus()

    def load_render_options(self):
        """Carga las opciones de render en la tabla con formato de color."""
        self.table.setItemDelegate(ColoredItemDelegate())

        for row, name in enumerate(self.options):
            # Extraer el nombre real del preset
            preset_number = row + 1
            preset = self.presets[f"Preset{preset_number}"]
            display_name = preset["button_name"]

            item = QTableWidgetItem(
                f"[{preset['button_type'].capitalize()}] {display_name}"
            )
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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

        # Sumar la altura del botón extra (aprox 38px)
        height += 42

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
        selected_option = self.options[row]
        preset_number = row + 1
        preset = self.presets[f"Preset{preset_number}"]

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

    def show_write_path_window(self):
        """Importa y ejecuta el main() de LGA_Write_PathToText.py para mostrar el path del Write seleccionado."""
        import importlib.util
        import os

        def normalize_path(path):
            # Normalizar barras y convertir a minúsculas
            path = path.replace("\\", "/").lower()
            # Eliminar redundancias como '.' o '..'
            path = os.path.normpath(path)
            return path

        self.close()
        script_path = os.path.join(os.path.dirname(__file__), "LGA_Write_PathToText.py")
        spec = importlib.util.spec_from_file_location(
            "LGA_Write_PathToText", script_path
        )
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "main"):
                # Pasar la función de normalización al módulo
                module.normalize_path = normalize_path
                module.main()


# El resto del código se mantiene igual
app = None
window = None


def main():
    global app, window
    app = QApplication.instance() or QApplication([])
    window = SelectedNodeInfo()
    window.show()


# Llamar a main() para iniciar la aplicacion
if __name__ == "__main__":
    main()
