"""
_______________________________________________

  LGA_mediaPathReplacer v1.8 | Lega
  Search and replace for Read and Write nodes
_______________________________________________

"""

from qt_compat import QtWidgets, QtGui, QtCore

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QLineEdit = QtWidgets.QLineEdit
QPushButton = QtWidgets.QPushButton
QTextEdit = QtWidgets.QTextEdit
QCheckBox = QtWidgets.QCheckBox
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QSpacerItem = QtWidgets.QSpacerItem
QSizePolicy = QtWidgets.QSizePolicy
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QDialog = QtWidgets.QDialog
QHeaderView = QtWidgets.QHeaderView
QFrame = QtWidgets.QFrame
QFontMetrics = QtGui.QFontMetrics
QKeySequence = QtGui.QKeySequence
QColor = QtGui.QColor
Qt = QtCore.Qt
import nuke
import re
import os
import configparser

# Solo se necesita una instancia de QApplication por script
app = QApplication.instance() or QApplication([])


class SearchAndReplaceWidget(QWidget):
    def __init__(self, nodes):
        super(SearchAndReplaceWidget, self).__init__()
        self.nodes = nodes
        # Inicializar la lista de nodos normalizados
        self.normalized_nodes = [node["file"].getValue().lower() for node in self.nodes]
        self.ini_path = self.get_ini_path()  # Define la ruta del archivo .ini aqui
        self.loadPresets()
        self.initUI()

    def initUI(self):
        # Layout principal vertical
        self.layout = QVBoxLayout(self)

        # Boton para ejecutar el reemplazo
        self.run_button = QPushButton("&Replace Paths", self)
        self.run_button.clicked.connect(self.replacePaths)
        self.layout.addWidget(self.run_button)

        # Boton para guardar el preset
        self.save_preset_button = QPushButton("&Save Preset", self)
        self.save_preset_button.clicked.connect(self.savePreset)
        self.layout.addWidget(self.save_preset_button)

        # Agregar boton de Presets
        self.presets_button = QPushButton("&Load Presets", self)
        self.presets_button.clicked.connect(self.applyPresets)
        self.layout.addWidget(self.presets_button)

        # Establecer un ancho fijo para los botones
        self.run_button.setFixedWidth(120)
        self.presets_button.setFixedWidth(120)
        self.save_preset_button.setFixedWidth(120)

        # Widget para contener el QHBoxLayout (incluyendo los botones presets)
        checkboxes_widget = QWidget()
        checkboxes_layout = QHBoxLayout(checkboxes_widget)
        checkboxes_layout.addWidget(self.run_button)
        # checkboxes_layout.addSpacing(20) # Espacio
        checkboxes_layout.addWidget(self.presets_button)
        checkboxes_layout.addWidget(self.save_preset_button)

        checkboxes_layout.addSpacing(20)  # Espacio

        # Checkbox para filtrado opcional
        self.filter_checkbox = QCheckBox("Filter List")
        self.filter_checkbox.setChecked(True)  # Activado por defecto
        self.filter_checkbox.setToolTip(
            "Toggle to enable/disable filtering of the list based on the search term."
        )
        checkboxes_layout.addWidget(self.filter_checkbox)
        self.filter_checkbox.stateChanged.connect(self.updatePreviews)

        checkboxes_layout.addSpacing(20)  # Espacio

        # Crear un divisor vertical
        divisor = QFrame()
        divisor.setFrameShape(
            QFrame.VLine
        )  # Establecer la forma del marco como una linea vertical
        divisor.setFrameShadow(
            QFrame.Sunken
        )  # Establecer la sombra del marco para un efecto 3D
        divisor.setStyleSheet(
            "border: 1px solid #1f1f1f;"
        )  # Ajustar el color y el grosor del borde
        checkboxes_layout.addWidget(divisor)  # Anadir el divisor al layout
        # divisor_reads = QLabel("|")
        # checkboxes_layout.addWidget(divisor_reads)

        checkboxes_layout.addSpacing(20)

        # Checkbox y etiqueta para 'Read'
        self.read_checkbox = QCheckBox()
        self.read_checkbox.setChecked(True)  # Activado por defecto
        self.read_checkbox.setToolTip("Include Read nodes in search and replace")
        read_label = QLabel("Reads")
        checkboxes_layout.addWidget(self.read_checkbox)
        checkboxes_layout.addWidget(read_label)

        # Espacio entre checkboxes
        checkboxes_layout.addSpacing(20)

        # Checkbox y etiqueta para 'Write'
        self.write_checkbox = QCheckBox()
        self.write_checkbox.setChecked(True)  # Activado por defecto
        self.write_checkbox.setToolTip("Include Write nodes in search and replace")
        write_label = QLabel("Writes")
        checkboxes_layout.addWidget(self.write_checkbox)
        checkboxes_layout.addWidget(write_label)

        # Espaciador para empujar el texto 'v1.6' hacia la derecha
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        checkboxes_layout.addItem(spacer)

        # Texto 'v1.6' alineado a la derecha
        version_label = QLabel("v1.6")
        version_label.setToolTip("Lega Pugliese - 2024")
        checkboxes_layout.addWidget(version_label)

        # Anadir el widget al layout principal
        self.layout.addWidget(checkboxes_widget)

        # Conectar los checkboxes con la funcion de actualizacion
        self.read_checkbox.stateChanged.connect(self.updatePreviews)
        self.write_checkbox.stateChanged.connect(self.updatePreviews)

        # Etiqueta y campo de busqueda
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Search...")
        # search_layout.addWidget(search_label)
        search_layout.addWidget(self.find_input)
        self.layout.addLayout(search_layout)

        # Campo de texto donde mostrar la informacion original
        self.preview_original = QTextEdit(self)
        self.preview_original.setReadOnly(True)
        self.preview_original.setStyleSheet(
            "QTextEdit { background-color: #282828; color: #c8c8c8; font-size: 10pt; line-height: 120%; }"
        )
        self.layout.addWidget(self.preview_original)

        # Espacio vertical
        self.layout.addSpacing(5)

        # Etiqueta y campo de reemplazo
        replace_layout = QHBoxLayout()
        replace_label = QLabel("Replace:")
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace...")
        # replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_input)
        self.layout.addLayout(replace_layout)

        # Campo de texto donde mostrar la informacion reemplazada
        self.preview_replace = QTextEdit(self)
        self.preview_replace.setReadOnly(True)
        self.preview_replace.setStyleSheet(
            "QTextEdit { background-color: #282828; color: #c8c8c8; font-size: 10pt; line-height: 120%; }"
        )
        self.layout.addWidget(self.preview_replace)

        # Conectar cambios en los campos de entrada con la funcion de actualizacion
        self.find_input.textChanged.connect(self.updatePreviews)
        self.replace_input.textChanged.connect(self.updatePreviews)

        self.setWindowTitle("Search and Replace in Paths")
        self.adjustSizeDialog()
        self.updatePreviews()

        # Atajos de teclado
        self.run_button.setShortcut(QKeySequence(Qt.Key_Return))
        self.find_input.setFocus()

    def get_ini_path(self):
        # Construir la ruta al archivo .ini ubicado en el mismo directorio que el script
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(dir_path, "LGA_mediaPathReplacer_presets.ini")

    def loadPresets(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.ini_path)

        # Asignar valores predeterminados si el archivo o las claves no existen
        self.search_preset = self.config.get("Presets", "Search_Preset_1", fallback="")
        self.replace_preset = self.config.get(
            "Presets", "Replace_Preset_1", fallback=""
        )

        # Asignar valores predeterminados si el archivo o las claves no existen
        self.search_preset = self.config.get("Presets", "Search_Preset_1", fallback="")
        self.replace_preset = self.config.get(
            "Presets", "Replace_Preset_1", fallback=""
        )

    def savePreset(self):
        # Guardar el nuevo preset en el archivo .ini
        search_text = self.find_input.text().strip()
        replace_text = self.replace_input.text().strip()

        if search_text and replace_text:
            self.config.read(
                self.ini_path
            )  # Recargar la configuracion para obtener el conteo actualizado
            preset_number = (
                len(self.config.items("Presets")) // 2 + 1
            )  # Calcular el nuevo numero de preset

            # Anadir el nuevo preset
            self.config.set("Presets", f"Search_Preset_{preset_number}", search_text)
            self.config.set("Presets", f"Replace_Preset_{preset_number}", replace_text)

            # Guardar los cambios
            with open(self.ini_path, "w") as configfile:
                self.config.write(configfile)
        else:
            print("Search and Replace fields must not be empty.")

    def applyPresets(self):
        dialog = PresetsDialog(self.config, self.ini_path, self)
        dialog.loadPresets()
        if dialog.exec_() and dialog.selected_preset:
            search_text, replace_text = dialog.selected_preset
            self.find_input.setText(search_text)
            self.replace_input.setText(replace_text)
            self.updatePreviews()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super(SearchAndReplaceWidget, self).keyPressEvent(event)

    def replacePaths(self):
        nuke.Undo().begin("Replace All Paths")
        try:
            find_text = (
                self.find_input.text().lower()
            )  # Version normalizada para busqueda
            replace_text = self.replace_input.text()
            for node, normalized_path in zip(self.nodes, self.normalized_nodes):
                if (node.Class() == "Read" and self.read_checkbox.isChecked()) or (
                    node.Class() == "Write" and self.write_checkbox.isChecked()
                ):
                    original_path = node["file"].getValue()
                    # Buscar el texto en la version normalizada para encontrar la posicion
                    if find_text in normalized_path:
                        # Reemplazar TODAS las ocurrencias - VERSION SEGURA
                        import re

                        pattern = re.escape(find_text)
                        new_path = re.sub(
                            pattern, replace_text, original_path, flags=re.IGNORECASE
                        )
                        node["file"].setValue(new_path)
        finally:
            nuke.Undo().end()
        self.updatePreviews()  # Actualizar las vistas previas para reflejar los cambios

    def updateNodes(self, new_nodes):
        self.nodes = new_nodes
        self.normalized_nodes = [node["file"].getValue().lower() for node in self.nodes]

    def updatePreviews(self):
        find_text = self.find_input.text().lower()
        replace_text = self.replace_input.text()
        original_previews = []
        replace_previews = []
        is_filtering_enabled = self.filter_checkbox.isChecked()

        for node, normalized_path in zip(self.nodes, self.normalized_nodes):
            original_path = node["file"].getValue()
            if (node.Class() == "Read" and self.read_checkbox.isChecked()) or (
                node.Class() == "Write" and self.write_checkbox.isChecked()
            ):
                # Realiza el reemplazo independientemente del filtrado
                if find_text in normalized_path:
                    # Usar regex para TODAS las ocurrencias - SEGURO
                    import re

                    pattern = re.escape(find_text)
                    new_path = re.sub(
                        pattern, replace_text, original_path, flags=re.IGNORECASE
                    )
                else:
                    new_path = (
                        original_path  # Si no hay coincidencia, usar la ruta original
                    )

                # Aplicar el resaltado segun corresponda - VERSION SEGURA SIN LOOPS
                highlighted_original_path = original_path
                highlighted_new_path = new_path

                if find_text in normalized_path:
                    # Resaltar TODAS las ocurrencias en la ruta original - SEGURO
                    import re

                    pattern = re.escape(find_text)
                    highlighted_original_path = re.sub(
                        pattern,
                        f'<span style="color: #ff9a8a; font-weight: bold;">{find_text}</span>',
                        original_path,
                        flags=re.IGNORECASE,
                    )

                    # Resaltar texto de reemplazo - SOLO SI ES DIFERENTE AL TEXTO DE BUSQUEDA
                    if replace_text and replace_text.lower() != find_text.lower():
                        pattern_replace = re.escape(replace_text)
                        highlighted_new_path = re.sub(
                            pattern_replace,
                            f'<span style="color: #ff9a8a; font-weight: bold;">{replace_text}</span>',
                            new_path,
                        )

                # Agregar a las vistas previas segun el estado del filtrado
                if (
                    is_filtering_enabled
                    and find_text in normalized_path
                    or not is_filtering_enabled
                ):
                    original_previews.append(highlighted_original_path)
                    replace_previews.append(highlighted_new_path)

        self.preview_original.setHtml("<br>".join(original_previews))
        self.preview_replace.setHtml("<br>".join(replace_previews))

    def adjustSizeDialog(self):
        # Calcular el ancho del texto mas largo
        fm = QFontMetrics(self.font())
        max_text_width = max(
            [fm.width(node["file"].getValue()) for node in self.nodes] + [200],
            default=0,
        )
        width = min(max_text_width * 2, 1600)  # Ancho maximo ajustado

        # Calcular la altura basada en el numero de nodos
        height_per_item = fm.lineSpacing() * 2  # Altura para dos lineas de texto
        estimated_height = (
            len(self.nodes) * height_per_item
            + self.find_input.height()
            + self.replace_input.height()
            + self.run_button.height()
        )

        # Obtener la altura del monitor
        screen_height = QApplication.primaryScreen().geometry().height()

        # Establecer un limite para la altura, por ejemplo, el 80% de la altura del monitor
        max_height = screen_height * 0.8

        # Usar el menor entre la altura calculada y el maximo permitido
        final_height = min(estimated_height, max_height)

        # Ajustar el tamano de los campos de texto previo
        # El numero de items visible en los previews sera proporcional a la altura final
        visible_items = max(
            1,
            int(
                (
                    final_height
                    - self.find_input.height()
                    - self.replace_input.height()
                    - self.run_button.height()
                )
                / (2 * height_per_item)
            ),
        )
        self.preview_original.setFixedHeight(
            height_per_item * min(len(self.nodes), visible_items)
        )
        self.preview_replace.setFixedHeight(
            height_per_item * min(len(self.nodes), visible_items)
        )

        # Establecer el tamano minimo del dialogo
        self.setMinimumSize(width, final_height)


class PresetsDialog(QDialog):
    def __init__(self, config, ini_path, parent=None):
        super(PresetsDialog, self).__init__(parent, Qt.FramelessWindowHint)
        self.ini_path = ini_path
        self.config = config
        self.parent_widget = parent  # Asignar el widget padre
        self.selected_preset = None
        self.applied_preset = None
        self.setMinimumWidth(400)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Search", "Replace"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.apply_and_close)

        # Conectar el evento de clic en la tabla para aplicar el preset
        self.table.clicked.connect(self.apply_preset)

        # Establecer el color de fondo y del texto
        self.table.setStyleSheet(
            """
            QTableWidget { background-color: #282828; color: rgb(200, 200, 200); }
            QTableWidget::item:selected { background-color: rgb(62, 62, 62); color: rgb(200, 200, 200); }
        """
        )

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.loadPresets()

        # Ajustar la altura de la ventana en funcion del numero de presets
        row_height = self.table.rowHeight(0) if self.table.rowCount() > 0 else 24
        header_height = self.table.horizontalHeader().height()
        self.setFixedHeight(
            min(400, self.table.rowCount() * row_height + header_height + 60)
        )  # 60 para espacio adicional y botones

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

        # Botones Apply, Delete y Cancel
        self.buttons_layout = QHBoxLayout()
        self.cancel_button = QPushButton("&Cancel", self)
        self.cancel_button.setShortcut("Alt+C")
        self.cancel_button.clicked.connect(self.close)

        self.delete_button = QPushButton("&Delete Preset", self)
        self.delete_button.setShortcut("Alt+D")
        self.delete_button.clicked.connect(self.delete_preset)

        self.apply_button = QPushButton("&Apply", self)
        self.apply_button.setShortcut("Alt+A")
        self.apply_button.clicked.connect(self.apply_and_close)

        self.buttons_layout.addWidget(self.cancel_button)
        self.buttons_layout.addWidget(self.delete_button)
        self.buttons_layout.addWidget(self.apply_button)

        self.layout.addLayout(self.buttons_layout)

    def loadPresets(self):
        # Limpiar la configuracion actual y recargar desde el archivo
        self.config = configparser.ConfigParser()
        self.config.read(self.ini_path)

        # Limpiar la tabla antes de volver a cargar los datos
        self.table.setRowCount(0)  # Esto elimina todas las filas existentes

        if self.config.has_section("Presets"):
            presets = self.config.items("Presets")
            # Determinar el numero de filas necesario
            self.table.setRowCount(len(presets) // 2)

            for key, value in presets:
                key_lower = key.lower()
                if "search_preset_" in key_lower:
                    index = int(key_lower.split("_")[2]) - 1
                    self.table.setItem(index, 0, QTableWidgetItem(value))
                elif "replace_preset_" in key_lower:
                    index = int(key_lower.split("_")[2]) - 1
                    self.table.setItem(index, 1, QTableWidgetItem(value))

            self.table.resizeColumnsToContents()

        # Selecciona la primera fila si hay alguna y aplica el preset
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
            self.apply_preset()

    def delete_preset(self):
        selected_row = self.table.currentRow()
        if selected_row != -1:
            # Eliminar la fila de la tabla
            self.table.removeRow(selected_row)

            # Reorganizar y guardar la nueva configuracion en el archivo .ini
            new_config = configparser.ConfigParser()
            new_config.add_section("Presets")

            for row in range(self.table.rowCount()):
                search_item = self.table.item(row, 0)
                replace_item = self.table.item(row, 1)
                if search_item and replace_item:
                    new_config.set(
                        "Presets", f"Search_Preset_{row + 1}", search_item.text()
                    )
                    new_config.set(
                        "Presets", f"Replace_Preset_{row + 1}", replace_item.text()
                    )

            with open(self.ini_path, "w") as configfile:
                new_config.write(configfile)

            # Ajustar la seleccion
            new_selected_row = (
                selected_row
                if selected_row < self.table.rowCount()
                else selected_row - 1
            )
            if new_selected_row >= 0:
                self.table.selectRow(new_selected_row)
                self.apply_preset(
                    self.table.currentIndex()
                )  # Aplicar el preset de la fila seleccionada

    def apply_preset(self, index=None):
        # Si no se proporciona un indice, usa la fila seleccionada actualmente
        selected_row = index.row() if index else self.table.currentRow()

        if selected_row != -1:
            search_item = self.table.item(selected_row, 0)
            replace_item = self.table.item(selected_row, 1)
            if search_item and replace_item:
                self.applied_preset = (search_item.text(), replace_item.text())
                if self.parent_widget:  # Verificar si el widget padre esta definido
                    self.parent_widget.find_input.setText(search_item.text())
                    self.parent_widget.replace_input.setText(replace_item.text())

    def apply_and_close(self):
        # Aplicar y cerrar solo si se presiona "Apply"
        if self.applied_preset:
            self.selected_preset = self.applied_preset
        self.accept()

    def closeEvent(self, event):
        # Revertir los cambios si se presiona "Cancel"
        if self.applied_preset and not self.selected_preset and self.parent_widget:
            # Restablece los valores originales o los vacia
            self.parent_widget.find_input.setText("")
            self.parent_widget.replace_input.setText("")
        super(PresetsDialog, self).closeEvent(event)


def show_search_replace_widget():
    # Obtener nodos seleccionados o todos los nodos si no hay seleccionados
    selected_nodes = nuke.selectedNodes("Read") + nuke.selectedNodes("Write")
    if not selected_nodes:
        selected_nodes = nuke.allNodes("Read") + nuke.allNodes("Write")

    # Mostrar el widget
    global search_replace_widget
    search_replace_widget = SearchAndReplaceWidget(selected_nodes)
    search_replace_widget.show()


# Llamar a la funcion para mostrar el widget
# show_search_replace_widget()
