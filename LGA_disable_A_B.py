"""
________________________________________________________________________________

  LGA_disable_A_B v1.8 | Lega
  Tool for creating A/B comparisons between selected nodes.
  Links the disable knob of nodes to a central Disable_A_B node for easy switching.
________________________________________________________________________________

"""

from qt_compat import QtWidgets, QtGui, QtCore

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QHeaderView = QtWidgets.QHeaderView
QCheckBox = QtWidgets.QCheckBox
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QPushButton = QtWidgets.QPushButton
QHBoxLayout = QtWidgets.QHBoxLayout
QStyle = QtWidgets.QStyle
QColor = QtGui.QColor
QBrush = QtGui.QBrush
QScreen = QtGui.QScreen
QFont = QtGui.QFont
QPalette = QtGui.QPalette
QKeyEvent = QtGui.QKeyEvent
QCursor = QtGui.QCursor
Qt = QtCore.Qt
QEvent = QtCore.QEvent
import nuke
import colorsys

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


class CenteredCheckbox(QCheckBox):
    def __init__(self, parent=None):
        super(CenteredCheckbox, self).__init__(parent)
        self.setStyleSheet("QCheckBox { margin-left: 50%; margin-right: 50%; }")


class ColorMixDelegate(QStyledItemDelegate):
    def __init__(
        self, table_widget, background_colors, mix_color=(88, 88, 88), parent=None
    ):
        super(ColorMixDelegate, self).__init__(parent)
        self.table_widget = table_widget
        self.background_colors = background_colors
        self.mix_color = mix_color

    def mix_colors(self, color1, color2):
        mixed_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
        return mixed_color

    def paint(self, painter, option, index):
        row = index.row()
        column = index.column()
        if option.state & QStyle.State_Selected:
            original_color = QColor(self.background_colors[row][column])
            mixed_color = self.mix_colors(
                (original_color.red(), original_color.green(), original_color.blue()),
                self.mix_color,
            )
            option.palette.setColor(QPalette.Highlight, QColor(*mixed_color))
        else:
            original_color = QColor(self.background_colors[row][column])
            option.palette.setColor(QPalette.Base, original_color)

        super(ColorMixDelegate, self).paint(painter, option, index)


def convert_color(value):
    r = int((value & 0xFF000000) >> 24)
    g = int((value & 0x00FF0000) >> 16)
    b = int((value & 0x0000FF00) >> 8)
    return r, g, b


def get_node_color(node):
    # Verificar si el nodo tiene un valor de color
    if "tile_color" in node.knobs():
        # Obtener el valor del color
        color_value = node["tile_color"].value()

        # Si el color es 0, significa que usa el color por defecto
        if color_value == 0:
            # Obtener el tipo de nodo
            node_class = node.Class()

            # Obtener el color por defecto desde las preferencias de Nuke
            default_color_value = nuke.defaultNodeColor(node_class)
            return convert_color(default_color_value)
        else:
            # Convertir el valor del color en RGB
            return convert_color(color_value)
    else:
        # Color por defecto si no hay valor de color
        return 255, 255, 255  # Blanco


def is_color_light(r, g, b):
    # Calcular el brillo del color
    brightness = r * 0.299 + g * 0.587 + b * 0.114
    return brightness > 126


def generate_unique_name(base_name):
    existing_names = [node.name() for node in nuke.allNodes()]
    if base_name not in existing_names:
        return base_name

    i = 1
    while f"{base_name}{i}" in existing_names:
        i += 1

    return f"{base_name}{i}"


class SelectedNodeInfo(QWidget):
    def __init__(
        self, nodes, initial_connections=None, disable_ab_node=None, parent=None
    ):
        super(SelectedNodeInfo, self).__init__(parent)

        # Variables para el manejo de arrastre
        self.is_dragging = False
        self.drag_start_pos = None

        # Filtrar los nodos Dot y nodos sin knob disable
        nodes = [
            node
            for node in nodes
            if node.Class() != "Dot" and "disable" in node.knobs()
        ]

        # Si initial_connections es None y disable_ab_node es None, inicializar todas las conexiones como "A"
        if initial_connections is None and disable_ab_node is None:
            initial_connections = ["A"] * len(nodes)

        # Ordenar los nodos segun la posicion Y y mantener las conexiones iniciales sincronizadas
        sorted_nodes_with_connections = sorted(
            zip(nodes, initial_connections), key=lambda item: item[0]["ypos"].value()
        )
        self.nodes = [item[0] for item in sorted_nodes_with_connections]
        self.initial_connections = [item[1] for item in sorted_nodes_with_connections]
        self.disable_ab_node = disable_ab_node

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Select Nodes Groups")
        layout = QVBoxLayout(self)

        # Create the table with 4 columns
        self.table = QTableWidget(len(self.nodes), 4, self)
        self.table.setHorizontalHeaderLabels(["A", "B", "Node Name", "Label"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Eliminar numeros de las filas
        self.table.verticalHeader().setVisible(False)

        # Centrar los titulos de las tres primeras columnas
        for i in range(3):
            self.table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)

        # Set the style for the table
        self.table.setStyleSheet(
            """
            QTableView::item:selected {
                color: black;
                background-color: transparent;  // Hacer transparente el fondo de los items seleccionados
            }
        """
        )

        # Set selection behavior to select entire rows
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # Disable selection
        self.table.setSelectionMode(QTableWidget.NoSelection)

        # Connect mouse events
        self.table.viewport().installEventFilter(self)

        # Load data into the table
        self.load_data()

        layout.addWidget(self.table)

        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()

        # Create Disconnect button (only if a Disable_A_B node is selected)
        if self.disable_ab_node:
            self.disconnect_button = QPushButton("Disconnect")
            button_layout.addWidget(self.disconnect_button)
            self.disconnect_button.clicked.connect(self.disconnect_nodes)

        # Create Connect button
        self.connect_button = QPushButton("Connect")
        button_layout.addWidget(self.connect_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect the Connect button to the connect_nodes method
        self.connect_button.clicked.connect(self.connect_nodes)

        # Adjust window size and position to be centered
        self.adjust_window_size()

        # Set the delegate for color mixing
        background_colors = [
            ["#ffffff" for _ in range(4)] for _ in range(len(self.nodes))
        ]  # Example background colors
        self.table.setItemDelegate(ColorMixDelegate(self.table, background_colors))

    def eventFilter(self, source, event):
        if source == self.table.viewport():
            etype = event.type()
            if etype == QEvent.MouseButtonPress and hasattr(event, "pos"):
                self.is_dragging = True
                self.drag_start_pos = event.pos()
                self.handle_drag(event.pos())
            elif etype == QEvent.MouseMove and self.is_dragging and hasattr(event, "pos"):
                self.handle_drag(event.pos())
            elif etype == QEvent.MouseButtonRelease:
                self.is_dragging = False
        return super(SelectedNodeInfo, self).eventFilter(source, event)

    def handle_drag(self, pos):
        index = self.table.indexAt(pos)
        if index.isValid():
            row = index.row()
            col = index.column()
            if col in (0, 1):  # Solo activar checkboxes en columnas A o B
                checkbox = self.table.cellWidget(row, col)
                if checkbox:
                    checkbox.setChecked(True)
                    self.handle_checkbox_change(row, col)

    def disconnect_nodes(self):
        # Abrir un UNDO
        nuke.Undo.begin("Disconnect nodes and delete Disable_A_B")

        try:
            # Restaurar el estado inicial del knob disable y eliminar las expresiones
            initial_states = (
                self.disable_ab_node["initial_disable_states"].value().split(",")
            )
            for state in initial_states:
                node_name, initial_value = state.split(":")
                node = nuke.toNode(node_name)
                if node:
                    node["disable"].clearAnimated()
                    node["disable"].setValue(int(initial_value))
                    debug_print(
                        f"Node {node_name} restore disable state to {initial_value}"
                    )

            # Eliminar el nodo Disable_A_B
            if self.disable_ab_node:
                nuke.delete(self.disable_ab_node)

            # Cerrar la ventana despues de desconectar y eliminar el nodo
            self.close()

        finally:
            # Cerrar el UNDO
            nuke.Undo.end()

    def load_data(self):
        for row, node in enumerate(self.nodes):
            r, g, b = get_node_color(node)
            node_qcolor = QColor(r, g, b)  # Convertir los valores RGB a QColor

            # Ajustar el color del texto en funcion del brillo del fondo
            if is_color_light(r, g, b):
                text_color = QColor(0, 0, 0)  # Texto negro para fondos claros
            else:
                text_color = QColor(255, 255, 255)  # Texto blanco para fondos oscuros

            for col in range(4):
                if col < 2:  # Las primeras dos columnas son checkboxes
                    checkbox = CenteredCheckbox()
                    checkbox.setStyleSheet(
                        "QCheckBox { margin-left: 50%; margin-right: 50%; }"
                    )
                    item = QTableWidgetItem()
                    item.setBackground(node_qcolor)
                    item.setForeground(QBrush(text_color))
                    self.table.setItem(row, col, item)
                    self.table.setCellWidget(row, col, checkbox)

                    # Comprobacion adicional para ajustar los checkboxes si solo quedan dos filas
                    if self.table.rowCount() == 2:
                        if row == 0 and col == 0:
                            checkbox.setChecked(True)
                        elif row == 1 and col == 1:
                            checkbox.setChecked(True)
                    else:
                        # Set checkbox state based on initial connections
                        if col == 0 and self.initial_connections[row] == "A":
                            checkbox.setChecked(True)
                            debug_print(
                                f"Row {row} - Column A - Node {node.name()} is checked"
                            )
                        elif col == 1 and self.initial_connections[row] == "B":
                            checkbox.setChecked(True)
                            debug_print(
                                f"Row {row} - Column B - Node {node.name()} is checked"
                            )

                    # Conectar la senal stateChanged al metodo handle_checkbox_change
                    checkbox.stateChanged.connect(
                        lambda state, row=row, col=col: self.handle_checkbox_change(
                            row, col
                        )
                    )
                elif col == 2:  # La tercera columna es el nombre del nodo
                    node_item = QTableWidgetItem(node.name())
                    node_item.setBackground(node_qcolor)
                    node_item.setForeground(QBrush(text_color))
                    self.table.setItem(row, col, node_item)
                else:  # La cuarta columna es el label del nodo, limitado a 30 caracteres
                    label_text = (
                        node["label"].value() if "label" in node.knobs() else ""
                    )
                    truncated_label = (
                        (label_text[:30] + "...")
                        if len(label_text) > 30
                        else label_text
                    )
                    label_item = QTableWidgetItem(truncated_label)
                    label_item.setBackground(node_qcolor)
                    label_item.setForeground(QBrush(text_color))
                    self.table.setItem(row, col, label_item)

        self.table.resizeColumnsToContents()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.connect_nodes()
        else:
            super(SelectedNodeInfo, self).keyPressEvent(event)

    def handle_checkbox_change(self, row, col):
        if col == 0:  # Checkbox de la columna A
            if self.table.cellWidget(row, 0).isChecked():
                self.table.cellWidget(row, 1).setChecked(False)
        elif col == 1:  # Checkbox de la columna B
            if self.table.cellWidget(row, 1).isChecked():
                self.table.cellWidget(row, 0).setChecked(False)

    def adjust_window_size(self):
        # Desactivar temporalmente el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana basado en el ancho de las columnas
        width = (
            self.table.verticalHeader().width() - 30
        )  # Un poco de relleno para estetica
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i) + 20  # Un poco de relleno entre columnas

        # Asegurarse de que el ancho no supera el 80% del ancho de pantalla
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        max_width = screen_rect.width() * 0.8
        final_width = min(width, max_width)

        # Calcular la altura basada en la altura de los headers y las filas
        height = self.table.horizontalHeader().height() + 20
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)

        # Agregar un relleno total de 6 pixeles
        height += 10

        # Agregar la altura de los botones (solo una vez)
        button_height = self.connect_button.sizeHint().height()
        height += button_height

        # Asegurarse de que la altura no supera el 80% del alto de pantalla
        max_height = screen_rect.height() * 0.8
        final_height = min(height, max_height)

        # Reactivar el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamano de la ventana
        self.resize(final_width, final_height)

        # Obtener la posicion actual del puntero del mouse
        cursor_pos = QCursor.pos()

        # Mover la ventana para que se centre en la posicion actual del puntero del mouse
        self.move(cursor_pos.x() - final_width // 2, cursor_pos.y() - final_height // 2)

    def connect_nodes(self):
        # Abrir un UNDO
        nuke.Undo.begin("Create or Update Disable_A_B and link nodes")

        try:
            # Deseleccionar todos los nodos
            for node in nuke.allNodes():
                node["selected"].setValue(False)

            if self.disable_ab_node:
                disable_ab_node = self.disable_ab_node
                unique_name = disable_ab_node.name()
                initial_disable_states = (
                    disable_ab_node["initial_disable_states"].value().split(",")
                )
            else:
                # Obtener la posicion del primer nodo
                first_node = self.nodes[0]
                first_node_xpos = int(first_node["xpos"].value())
                first_node_ypos = int(first_node["ypos"].value())

                # Generar un nombre unico para el nodo Disable_A_B
                unique_name = generate_unique_name("Disable_A_B")

                # Crear el nodo noOp llamado Disable_A_B
                disable_ab_node = nuke.createNode("NoOp")
                disable_ab_node.setName(unique_name)

                # Posicionar el nodo Disable_A_B 120 pixeles a la izquierda y 120 pixeles hacia arriba
                disable_ab_node.setXYpos(first_node_xpos - 120, first_node_ypos - 0)

                # Agregar el checkbox de Disable al nodo Disable_A_B
                disable_checkbox = nuke.Boolean_Knob("disable", "Disable")
                disable_ab_node.addKnob(disable_checkbox)

                # Valores HSV
                h, s, v = 0.98, 0.49, 0.87

                # Convertir HSV a RGB
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                r, g, b = int(r * 255), int(g * 255), int(b * 255)

                # Convertir RGB a hexadecimal RGBA
                rgba = (r << 24) + (g << 16) + (b << 8) + 255

                # Asignar el color al nodo
                disable_ab_node["tile_color"].setValue(rgba)

                # Agregar knobs ocultos para almacenar la informacion de conexiones
                disable_ab_node.addKnob(nuke.String_Knob("groupA_connections", ""))
                disable_ab_node["groupA_connections"].setVisible(False)
                disable_ab_node.addKnob(nuke.String_Knob("groupB_connections", ""))
                disable_ab_node["groupB_connections"].setVisible(False)
                disable_ab_node.addKnob(nuke.String_Knob("initial_disable_states", ""))
                disable_ab_node["initial_disable_states"].setVisible(False)

                initial_disable_states = []

            groupA_connections = []
            groupB_connections = []

            for row in range(self.table.rowCount()):
                node = self.nodes[row]
                node_name = node.name()

                if not self.disable_ab_node:
                    # Guardar el estado inicial del knob disable
                    initial_state = node["disable"].value()
                    initial_disable_states.append(f"{node_name}:{int(initial_state)}")

                # Confirmar el estado de los checkboxes
                if self.table.cellWidget(row, 0).isChecked():  # Nodo del grupo A
                    node["disable"].setExpression(f"parent.{unique_name}.disable")
                    groupA_connections.append(node_name)
                    debug_print(f"Node {node_name} linked as A")
                elif self.table.cellWidget(row, 1).isChecked():  # Nodo del grupo B
                    node["disable"].setExpression(f"!parent.{unique_name}.disable")
                    groupB_connections.append(node_name)
                    debug_print(f"Node {node_name} linked as B")
                else:
                    # En caso de que un checkbox no este seleccionado, restaurar el estado inicial
                    initial_state = next(
                        (
                            state.split(":")[1]
                            for state in initial_disable_states
                            if state.split(":")[0] == node_name
                        ),
                        None,
                    )
                    if initial_state is not None:
                        node["disable"].clearAnimated()
                        node["disable"].setValue(int(initial_state))
                        debug_print(
                            f"Node {node_name} has no A or B selected, restoring initial state to {initial_state}"
                        )

            # Almacenar la informacion de conexiones en los knobs ocultos
            disable_ab_node["groupA_connections"].setValue(",".join(groupA_connections))
            disable_ab_node["groupB_connections"].setValue(",".join(groupB_connections))
            disable_ab_node["initial_disable_states"].setValue(
                ",".join(initial_disable_states)
            )

            # Obtener el nivel de zoom actual
            current_zoom = nuke.zoom()

            # Obtener la posicion del nodo
            xpos = disable_ab_node["xpos"].value()
            ypos = disable_ab_node["ypos"].value()

            # Centrar en el nodo manteniendo el zoom actual
            nuke.zoom(current_zoom, [xpos, ypos])

            # Cerrar la ventana despues de crear o actualizar el nodo
            self.close()

        finally:
            # Cerrar el UNDO
            nuke.Undo.end()


app = None
window = None


def main():
    global app, window
    # Obtener los nodos seleccionados
    selected_nodes = nuke.selectedNodes()
    disable_ab_selected = False

    # Deseleccionar los nodos Dot y nodos sin knob disable
    selected_nodes = [
        node
        for node in selected_nodes
        if node.Class() != "Dot" and "disable" in node.knobs()
    ]

    # Verificar si hay un solo nodo seleccionado
    if len(selected_nodes) == 1:
        single_node = selected_nodes[0]
        if single_node.Class() == "NoOp" and single_node.name().startswith(
            "Disable_A_B"
        ):
            disable_ab_selected = True
            # Obtener la informacion de conexiones de los knobs ocultos
            groupA_connections = single_node["groupA_connections"].value().split(",")
            groupB_connections = single_node["groupB_connections"].value().split(",")

            connected_nodes = []
            initial_connections = []

            for node_name in groupA_connections:
                node = nuke.toNode(node_name)
                if node and node.Class() != "Dot" and "disable" in node.knobs():
                    connected_nodes.append(node)
                    initial_connections.append("A")
                    debug_print(f"Node {node_name} is connected as A")  # Depuracion

            for node_name in groupB_connections:
                node = nuke.toNode(node_name)
                if node and node.Class() != "Dot" and "disable" in node.knobs():
                    connected_nodes.append(node)
                    initial_connections.append("B")
                    debug_print(f"Node {node_name} is connected as B")  # Depuracion

            # Desconectar directamente sin abrir la ventana
            # Abrir un UNDO
            nuke.Undo.begin("Disconnect nodes and delete Disable_A_B")

            try:
                # Restaurar el estado inicial del knob disable y eliminar las expresiones
                initial_states = (
                    single_node["initial_disable_states"].value().split(",")
                )
                for state in initial_states:
                    node_name, initial_value = state.split(":")
                    node = nuke.toNode(node_name)
                    if node:
                        node["disable"].clearAnimated()
                        node["disable"].setValue(int(initial_value))
                        debug_print(
                            f"Node {node_name} restore disable state to {initial_value}"
                        )

                # Eliminar el nodo Disable_A_B
                nuke.delete(single_node)

            finally:
                # Cerrar el UNDO
                nuke.Undo.end()

            return
        else:
            debug_print("El nodo seleccionado no es un Disable_A_B")
            # Nuevo codigo para manejar un nodo que no es Disable_A_B
            if "disable" in single_node.knobs():
                disable_knob = single_node["disable"]
                debug_print(f"Estado actual del knob 'disable': {disable_knob.value()}")
                if disable_knob.hasExpression():
                    expression = disable_knob.toScript()
                    debug_print(f"El knob 'disable' tiene una expresion: {expression}")
                    # Mejora en la deteccion de la expresion
                    if "Disable_A_B" in expression:
                        debug_print(
                            "La expresion hace referencia a un nodo Disable_A_B"
                        )
                        referenced_node_name = expression.split("parent.")[1].split(
                            "."
                        )[0]
                        debug_print(
                            f"Nombre del nodo referenciado: {referenced_node_name}"
                        )
                        referenced_node = nuke.toNode(referenced_node_name)
                        if not referenced_node:
                            debug_print(
                                f"El nodo referenciado {referenced_node_name} no existe"
                            )
                            # El nodo Disable_A_B referenciado no existe, eliminar automaticamente
                            nuke.Undo.begin("Eliminar expresion huerfana")
                            try:
                                disable_knob.clearAnimated()
                                disable_knob.setValue(
                                    0
                                )  # Establecer en falso por defecto
                                debug_print(
                                    f"Se elimino automaticamente la expresion huerfana del nodo {single_node.name()}"
                                )
                            finally:
                                nuke.Undo.end()
                        else:
                            debug_print(
                                f"El nodo referenciado {referenced_node_name} existe"
                            )
                    else:
                        debug_print(
                            "La expresion no hace referencia a un nodo Disable_A_B"
                        )
                else:
                    debug_print("El knob 'disable' no tiene una expresion")
            else:
                debug_print("El nodo no tiene un knob 'disable'")
            debug_print("Saliendo despues de manejar el nodo unico")
            return  # Salir despues de manejar el nodo unico

    debug_print(f"Numero de nodos seleccionados: {len(selected_nodes)}")
    # Verificar si algun nodo tiene el knob disable linkeado por expresion o animado por keyframes
    for node in selected_nodes:
        if "disable" in node.knobs():
            knob = node["disable"]
            debug_print(
                f"Nodo: {node.name()}, Tiene expresion: {knob.hasExpression()}, Esta animado: {knob.isAnimated()}"
            )

    # Check if there's already an instance of QApplication
    app = QApplication.instance() or QApplication([])
    window = SelectedNodeInfo(selected_nodes, disable_ab_node=None)
    window.show()
    debug_print("Ventana SelectedNodeInfo mostrada")


# Llamar a main() para iniciar la aplicacion
if __name__ == "__main__":
    main()
