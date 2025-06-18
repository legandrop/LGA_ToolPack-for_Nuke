"""
_____________________________________________________________________________

  LGA_Write_Presets v1.3 | 2024 | Lega

  Creates Write nodes with predefined settings for different purposes.
  Includes presets for preRenders, publish, denoise and other common tasks.
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
)  # Añadido QStyle aquí
from PySide2.QtCore import Qt
from PySide2.QtGui import QCursor, QPalette, QColor, QKeyEvent, QBrush
import nuke
import sys
import os

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


def create_name_input_dialog(initial_text=""):
    dialog = QDialog()
    dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Popup)
    dialog.esc_exit = False

    dialog.setStyleSheet("QDialog { background-color: #242527; }")

    layout = QVBoxLayout(dialog)

    title = QLabel("preRender Name")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        "color: #AAAAAA; font-family: Verdana; font-weight: bold; font-size: 10pt;"
    )
    layout.addWidget(title)

    line_edit = QLineEdit(dialog)
    line_edit.setFixedHeight(25)
    line_edit.setFrame(False)
    line_edit.setStyleSheet(
        """
        background-color: #242527;
        color: #FFFFFF;
    """
    )
    line_edit.setText(initial_text)
    layout.addWidget(line_edit)

    help_label = QLabel(
        '<span style="font-size:7pt; color:#AAAAAA;">Ctrl+Enter para confirmar</span>',
        dialog,
    )
    help_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(help_label)

    dialog.setLayout(layout)
    dialog.resize(200, 100)
    line_edit.setCursorPosition(len(initial_text))

    def event_filter(widget, event):
        if isinstance(event, QKeyEvent):
            if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                if event.modifiers() == Qt.ControlModifier:  # Solo aceptar con Ctrl
                    dialog.accept()
                return True  # Consumir el evento Enter sin Ctrl
            elif event.key() == Qt.Key_Escape:
                dialog.esc_exit = True
                dialog.reject()
                return True
        return False

    line_edit.installEventFilter(dialog)
    dialog.eventFilter = event_filter
    line_edit.setFocus()

    return dialog, line_edit


def show_name_input_dialog(initial_text=""):
    dialog, line_edit = create_name_input_dialog(initial_text)
    cursor_pos = QCursor.pos()
    avail_space = QDesktopWidget().availableGeometry(cursor_pos)
    posx = min(max(cursor_pos.x() - 100, avail_space.left()), avail_space.right() - 200)
    posy = min(max(cursor_pos.y() - 80, avail_space.top()), avail_space.bottom() - 150)
    dialog.move(posx, posy)

    if dialog.exec_() == QDialog.Accepted:
        return dialog.esc_exit, line_edit.text()
    else:
        return dialog.esc_exit, None


def get_selected_node():
    try:
        return nuke.selectedNode()
    except ValueError:
        return None


def create_prerender_write(user_text):
    """Función que implementa la lógica del EXR preRender básico"""
    nuke.Undo().begin("LGA_preRender")

    # Verificar si hay un nodo seleccionado
    selected_node = get_selected_node()
    if selected_node:
        current_node = selected_node
    else:
        current_node = nuke.createNode("NoOp")

    # Crear Write conectado directamente al nodo actual
    write_node = nuke.nodes.Write()
    write_node.setInput(0, current_node)
    write_node.setXpos(current_node.xpos())
    write_node.setYpos(current_node.ypos() + 100)

    # Reconectar nodos descendentes al Write
    if selected_node:
        downstream_nodes = current_node.dependent(
            nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False
        )
        for node in downstream_nodes:
            for i in range(node.inputs()):
                if node.input(i) == current_node:
                    node.setInput(i, write_node)

    # Configurar Write node con los mismos parámetros
    write_node["channels"].setValue("rgba")
    original_file_value = "[file dir [value root.name]]/../2_prerenders/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01_%04d.exr"
    new_file_value = original_file_value.replace("Pre", user_text)
    write_node["file"].setValue(new_file_value)

    write_node["file_type"].setValue("exr")
    write_node["compression"].setValue("DWAA")
    write_node["dw_compression_level"].setValue(60)
    write_node["first_part"].setValue("rgba")
    write_node["create_directories"].setValue(True)
    write_node["checkHashOnRead"].setValue(False)
    write_node["version"].setValue(4)
    write_node["colorspace"].setValue("default")

    base_write_name = "Write_" + user_text
    unique_write_name = get_unique_node_name(base_write_name)
    write_node["name"].setValue(unique_write_name)

    # Añadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob("User", "User"))
    write_node.addKnob(nuke.String_Knob("render_time", "Render Time"))
    write_node["render_time"].setValue("00:18:27")

    # Eliminar NoOp temporal si se creó
    if not selected_node:
        nuke.delete(current_node)

    # Abrir propiedades del Write y seleccionarlo
    write_node.showControlPanel()
    for node in nuke.allNodes():
        node["selected"].setValue(False)
    write_node["selected"].setValue(True)

    nuke.Undo().end()


def create_prerender_with_switch(user_text):
    """Función que implementa la lógica del EXR preRender con switch"""
    nuke.Undo().begin("LGA_preRender")

    # Variables para posicionamiento
    dot_width = int(nuke.toNode("preferences")["dot_node_scale"].value() * 12)
    distanciaX = 180
    distanciaY = 130  # Cambiado de 80 a 120

    # Verificar si hay un nodo seleccionado
    selected_node = get_selected_node()

    if selected_node:
        current_node = selected_node
        no_op = None
    else:
        no_op = nuke.createNode("NoOp")
        current_node = no_op

    # Crear un Dot debajo del nodo actual
    dot_node = nuke.nodes.Dot()
    dot_node.setInput(0, current_node)
    dot_node.setXpos(
        int(current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2))
    )

    if no_op:
        dot_node.setYpos(current_node.ypos() + current_node.screenHeight() - distanciaY)
    else:
        dot_node.setYpos(current_node.ypos() + current_node.screenHeight() + distanciaY)

    # Crear Switch
    switch_node = nuke.nodes.Switch()
    switch_node.setInput(0, dot_node)
    switch_node.setInput(1, None)
    switch_node["which"].setValue(1)
    switch_node["disable"].setValue(True)
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

    # Configurar Write node
    write_node["channels"].setValue("rgba")
    original_file_value = "[file dir [value root.name]]/../2_prerenders/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01_%04d.exr"
    new_file_value = original_file_value.replace("Pre", user_text)
    write_node["file"].setValue(new_file_value)

    # Configurar el resto de los parámetros del Write
    write_node["file_type"].setValue("exr")
    write_node["compression"].setValue("DWAA")
    write_node["dw_compression_level"].setValue(60)
    write_node["first_part"].setValue("rgba")
    write_node["create_directories"].setValue(True)
    write_node["checkHashOnRead"].setValue(False)
    write_node["version"].setValue(4)
    write_node["colorspace"].setValue("default")

    base_write_name = "Write_" + user_text
    unique_write_name = get_unique_node_name(base_write_name)
    write_node["name"].setValue(unique_write_name)

    # Añadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob("User", "User"))
    write_node.addKnob(nuke.String_Knob("render_time", "Render Time"))
    write_node["render_time"].setValue("00:18:27")

    # Reconectar nodos descendentes
    if not no_op:
        downstream_nodes = current_node.dependent(
            nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False
        )
        for node in downstream_nodes:
            for i in range(node.inputs()):
                if node.input(i) == current_node:
                    node.setInput(i, switch_node)

    # Crear BackdropNode
    nodes = [write_node, dot_node, switch_node]
    margen_izquierdo = 64
    margen_superior = 115
    margen_derecho = 63
    margen_inferior = 50

    bd_x = min(node.xpos() for node in nodes) - margen_izquierdo
    bd_y = min(node.ypos() for node in nodes) - margen_superior
    bd_w = (
        max(node.xpos() + node.screenWidth() for node in nodes) - bd_x + margen_derecho
    )
    bd_h = (
        max(node.ypos() + node.screenHeight() for node in nodes)
        - bd_y
        + margen_inferior
    )

    backdrop_node = nuke.nodes.BackdropNode(
        xpos=bd_x,
        ypos=bd_y,
        bdwidth=bd_w,
        bdheight=bd_h,
        tile_color=int("0x9F9000FF", 16),
        note_font="Verdana Bold",
        note_font_size=50,
        label=user_text,
        z_order=4,
        name="Backdrop_preRender",
    )
    backdrop_node["selected"].setValue(True)

    # Alinear Write con Dot
    align_write_to_dot(dot_node, write_node)

    backdrop_node.hideControlPanel()
    backdrop_node["selected"].setValue(False)

    # Reemplazar backdrop si está disponible
    if oz_backdrop_available:
        LGA_oz_backdropReplacer.replace_with_oz_backdrop()
        selected_nodes = nuke.selectedNodes("BackdropNode")
        if selected_nodes:
            new_backdrop_node = selected_nodes[0]
            new_backdrop_node.hideControlPanel()

    # Eliminar NoOp temporal si existe
    if no_op:
        nuke.delete(no_op)

    # Abrir propiedades del Write
    write_node.showControlPanel()

    # Seleccionar solo el Write
    for node in nuke.allNodes():
        node["selected"].setValue(False)
    write_node["selected"].setValue(True)

    nuke.Undo().end()


def create_publish_write():
    """Función que implementa la lógica del EXR Publish DWAA"""
    nuke.Undo().begin("LGA_preRender")

    # Verificar si hay un nodo seleccionado
    selected_node = get_selected_node()
    if selected_node:
        current_node = selected_node
    else:
        current_node = nuke.createNode("NoOp")

    # Crear Write conectado directamente al nodo actual
    write_node = nuke.nodes.Write()
    write_node.setInput(0, current_node)
    write_node.setXpos(current_node.xpos())
    write_node.setYpos(current_node.ypos() + 100)

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
    write_node["channels"].setValue("rgb")  # Cambiado de 'rgba' a 'rgb'
    write_node["file"].setValue(
        "[file dir [value root.name]]/../4_publish/[file tail [file rootname [value root.name]]]/[file tail [file rootname [value root.name]]]_%04d.exr"
    )
    write_node["file_type"].setValue("exr")
    write_node["compression"].setValue("DWAA")
    write_node["dw_compression_level"].setValue(60)
    write_node["first_part"].setValue("rgba")
    write_node["create_directories"].setValue(True)
    write_node["checkHashOnRead"].setValue(False)
    write_node["version"].setValue(4)
    write_node["colorspace"].setValue("default")

    base_write_name = "Write_Publish"
    unique_write_name = get_unique_node_name(base_write_name)
    write_node["name"].setValue(unique_write_name)

    # Añadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob("User", "User"))
    write_node.addKnob(nuke.String_Knob("render_time", "Render Time"))
    write_node["render_time"].setValue("00:18:27")

    # Eliminar NoOp temporal si se creó
    if not selected_node:
        nuke.delete(current_node)

    # Abrir propiedades del Write y seleccionarlo
    write_node.showControlPanel()
    for node in nuke.allNodes():
        node["selected"].setValue(False)
    write_node["selected"].setValue(True)

    nuke.Undo().end()


def find_top_read_node(node):
    """Encuentra el nodo Read más alto en las dependencias ascendentes del nodo"""
    if node.Class() == "Read":
        return node

    for input_node in node.dependencies():
        return find_top_read_node(input_node)

    return None


def get_write_name_from_read(current_node, default_name):
    """Obtiene el nombre para el Write basado en el Read más alto o usa el default"""
    read_node = find_top_read_node(current_node)

    if read_node:
        file_path = read_node["file"].value()
        file_name = os.path.basename(file_path)
        file_name = os.path.splitext(file_name)[0]
        # Eliminar el padding si existe
        if "_" in file_name:
            file_name = "_".join(file_name.split("_")[:-1])
        return "Write_" + file_name
    else:
        return "Write_" + default_name


def create_script_denoised_write(user_text):
    """Función que implementa la lógica del EXR denoised basado en script"""
    nuke.Undo().begin("LGA_preRender")

    # Verificar si hay un nodo seleccionado
    selected_node = get_selected_node()
    if selected_node:
        current_node = selected_node
    else:
        current_node = nuke.createNode("NoOp")

    # Crear Write conectado directamente al nodo actual
    write_node = nuke.nodes.Write()
    write_node.setInput(0, current_node)
    write_node.setXpos(current_node.xpos())
    write_node.setYpos(current_node.ypos() + 100)

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
    write_node["channels"].setValue("rgb")
    original_file_value = "[file dir [value root.name]]/../2_prerenders/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_aPlate_Denoised_v01/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_aPlate_Denoised_v01_%04d.exr"
    new_file_value = original_file_value.replace("aPlate_Denoised", user_text)
    write_node["file"].setValue(new_file_value)

    write_node["file_type"].setValue("exr")
    write_node["compression"].setValue("DWAA")
    write_node["dw_compression_level"].setValue(60)
    write_node["first_part"].setValue("rgba")
    write_node["create_directories"].setValue(True)
    write_node["checkHashOnRead"].setValue(False)
    write_node["version"].setValue(4)
    write_node["colorspace"].setValue("default")

    # Usar el nombre estándar en lugar del nombre del topfile
    base_write_name = "Write_" + user_text
    unique_write_name = get_unique_node_name(base_write_name)
    write_node["name"].setValue(unique_write_name)

    # Añadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob("User", "User"))
    write_node.addKnob(nuke.String_Knob("render_time", "Render Time"))
    write_node["render_time"].setValue("00:18:27")

    # Eliminar NoOp temporal si se creó
    if not selected_node:
        nuke.delete(current_node)

    # Abrir propiedades del Write y seleccionarlo
    write_node.showControlPanel()
    for node in nuke.allNodes():
        node["selected"].setValue(False)
    write_node["selected"].setValue(True)

    nuke.Undo().end()


def create_denoised_topread_write():
    """Función que implementa la lógica del EXR denoised usando topnode"""
    nuke.Undo().begin("LGA_preRender")

    # Verificar si hay un nodo seleccionado
    selected_node = get_selected_node()
    if selected_node:
        current_node = selected_node
    else:
        current_node = nuke.createNode("NoOp")

    # Crear Write conectado directamente al nodo actual
    write_node = nuke.nodes.Write()
    write_node.setInput(0, current_node)
    write_node.setXpos(current_node.xpos())
    write_node.setYpos(current_node.ypos() + 100)

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
    write_node["channels"].setValue("rgb")
    write_node["file"].setValue(
        "[file dirname [value [topnode].file]]/../../Comp/2_prerenders/[join [lrange [split [file tail [knob [topnode].file]] _ ] 0 6 ] _]_Denoised_v01/[join [lrange [split [file tail [knob [topnode].file]] _ ] 0 6 ] _]_Denoised_v01_%04d.exr"
    )
    write_node["file_type"].setValue("exr")
    write_node["compression"].setValue("DWAA")
    write_node["dw_compression_level"].setValue(60)
    write_node["first_part"].setValue("rgba")
    write_node["create_directories"].setValue(True)
    write_node["checkHashOnRead"].setValue(False)
    write_node["version"].setValue(4)
    write_node["colorspace"].setValue("default")

    # Obtener el nombre del Write basado en el Read o usar el default
    write_node["name"].setValue(get_write_name_from_read(current_node, "Denoised"))

    # Añadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob("User", "User"))
    write_node.addKnob(nuke.String_Knob("render_time", "Render Time"))
    write_node["render_time"].setValue("00:18:27")

    # Eliminar NoOp temporal si se creó
    if not selected_node:
        nuke.delete(current_node)

    # Abrir propiedades del Write y seleccionarlo
    write_node.showControlPanel()
    for node in nuke.allNodes():
        node["selected"].setValue(False)
    write_node["selected"].setValue(True)

    nuke.Undo().end()


# Mantener la clase SelectedNodeInfo como está, solo modificar change_option
class SelectedNodeInfo(QWidget):
    def __init__(self, parent=None):
        super(SelectedNodeInfo, self).__init__(parent)
        self.options = self.get_render_options()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("Render type")
        layout = QVBoxLayout(self)

        # Crear la barra de título
        title_bar = QWidget(self)
        title_bar.setFixedHeight(20)
        title_bar.setAutoFillBackground(True)
        title_bar.setStyleSheet("background-color: #323232;")

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

        layout.addWidget(title_bar)

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

        # Conectar el evento de clic
        self.table.cellClicked.connect(self.on_cell_clicked)

        layout.addWidget(self.table)
        self.setLayout(layout)

        # Ajustar el tamaño de la ventana y posicionarla
        self.adjust_window_size()

        # Seleccionar la primera fila y establecer el foco
        self.table.selectRow(0)
        self.table.setFocus()

        # Instalar el filtro de eventos en la tabla
        self.table.installEventFilter(self)

    def get_render_options(self):
        """Retorna la lista de opciones de render disponibles."""
        return [
            "[Script] EXR preRender",
            "[Script] EXR preRender + Switch",
            "[Script] EXR Publish DWAA",
            "[Script] EXR Denoise",
            "[Read] EXR Denoise",
            "[Read] TIFF Matte cct",
            "[Read] TIFF Matte Rec709",
            "[Read] MOV Review",
        ]

    def load_render_options(self):
        """Carga las opciones de render en la tabla."""
        # Establecer el delegado personalizado
        self.table.setItemDelegate(ColoredItemDelegate())

        for row, name in enumerate(self.options):
            item = QTableWidgetItem(name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 0, item)

        self.table.resizeColumnsToContents()
        self.table.setStyleSheet(
            """
            QTableView {
                background-color: #282828;
            }
            QTableView::item {
                padding: 5px;
            }
            QTableView::item:selected {
                background-color: rgb(230, 230, 230);
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
        height += 10

        # Incluir la altura de la barra de título personalizada
        title_bar_height = 20
        height += title_bar_height

        # Asegurarse de que la altura no supera el 80% del alto de pantalla
        max_height = screen_rect.height() * 0.8
        final_height = min(height, max_height)

        # Reactivar el estiramiento de la última columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamaño de la ventana
        self.resize(final_width, final_height)

        # Obtener la posición actual del puntero del mouse
        cursor_pos = QCursor.pos()

        # Mover la ventana para que se centre en la posición actual del puntero del mouse
        self.move(cursor_pos.x() - final_width // 2, cursor_pos.y() - final_height // 2)

    def on_cell_clicked(self, row, column):
        """Maneja el evento de clic en la tabla"""
        self.execute_selected_option(row)

    def execute_selected_option(self, row):
        """Ejecuta la opción seleccionada"""
        selected_option = self.options[row]

        if selected_option == "[Script] EXR preRender":
            self.close()
            esc_exit, user_text = show_name_input_dialog(initial_text="Pre-")
            if not esc_exit and user_text is not None:
                create_prerender_write(user_text)
        elif selected_option == "[Script] EXR preRender + Switch":
            self.close()
            esc_exit, user_text = show_name_input_dialog(initial_text="Pre-")
            if not esc_exit and user_text is not None:
                create_prerender_with_switch(user_text)
        elif selected_option == "[Script] EXR Publish DWAA":
            self.close()
            create_publish_write()
        elif selected_option == "[Script] EXR Denoise":
            self.close()
            esc_exit, user_text = show_name_input_dialog(initial_text="aPlate_Denoised")
            if not esc_exit and user_text is not None:
                create_script_denoised_write(user_text)
        elif selected_option == "[Read] EXR Denoise":
            self.close()
            create_denoised_topread_write()
        else:
            print(f"Opción seleccionada: {selected_option}")
            self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            event.accept()
            self.close()
        elif key in (Qt.Key_Return, Qt.Key_Enter):  # Quitamos el modificador Ctrl
            event.accept()
            current_row = self.table.currentRow()
            if current_row >= 0:
                self.execute_selected_option(current_row)
        elif key in (Qt.Key_Up, Qt.Key_Down):
            super(SelectedNodeInfo, self).keyPressEvent(event)
        else:
            event.ignore()

    def eventFilter(self, obj, event):
        if obj == self.table and event.type() == event.KeyPress:
            if (
                event.key() in (Qt.Key_Return, Qt.Key_Enter)
                and event.modifiers() == Qt.ControlModifier
            ):
                current_row = self.table.currentRow()
                if current_row >= 0:
                    self.execute_selected_option(current_row)
                return True  # Consumir el evento
            elif event.key() == Qt.Key_Escape:
                self.close()
                return True  # Consumir el evento
        return super(SelectedNodeInfo, self).eventFilter(obj, event)


# Agregar esta clase después de las importaciones
class ColoredItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        text = index.data()
        if text:
            painter.save()

            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, QColor("#212121"))

            if text.startswith("[Script]"):
                painter.setPen(QColor("#ed2464"))
                prefix = "[Script]"
                painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, prefix)
                painter.setPen(QColor("white"))
                # Ajustar el offset basado en el ancho real del texto "[Script]"
                text_width = painter.fontMetrics().horizontalAdvance(prefix)
                painter.drawText(
                    option.rect.adjusted(text_width, 0, 0, 0),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    text[len(prefix) :],
                )
            elif text.startswith("[Read]"):
                painter.setPen(QColor("#66e2ff"))
                prefix = "[Read]"
                painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, prefix)
                painter.setPen(QColor("white"))
                # Ajustar el offset basado en el ancho real del texto "[Read]"
                text_width = painter.fontMetrics().horizontalAdvance(prefix)
                painter.drawText(
                    option.rect.adjusted(text_width, 0, 0, 0),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    text[len(prefix) :],
                )
            else:
                painter.setPen(QColor("white"))
                painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, text)

            painter.restore()


# El resto del código se mantiene igual
app = None
window = None


def main():
    global app, window
    print("Abriendo ventana de opciones...")
    app = QApplication.instance() or QApplication([])
    window = SelectedNodeInfo()
    window.show()


# Llamar a main() para iniciar la aplicación
main()
