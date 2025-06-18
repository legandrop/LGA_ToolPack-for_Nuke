"""
______________________________________________

  LGA_mediaPathReplacer v1.1 - 2024  
  Search and replace for Read and Write nodes  
______________________________________________

"""


from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QCheckBox, QHBoxLayout, QLabel
from PySide2.QtWidgets import QSpacerItem, QSizePolicy
from PySide2.QtGui import QFontMetrics, QKeySequence
from PySide2.QtCore import Qt
import nuke

# Solo se necesita una instancia de QApplication por script
app = QApplication.instance() or QApplication([])


class SearchAndReplaceWidget(QWidget):
    def __init__(self, nodes):
        super(SearchAndReplaceWidget, self).__init__()
        self.nodes = nodes
        self.initUI()

    def initUI(self):
        # Layout principal vertical
        self.layout = QVBoxLayout(self)

        # Widget para contener el QHBoxLayout
        checkboxes_widget = QWidget()
        checkboxes_layout = QHBoxLayout(checkboxes_widget)

        # Checkbox y etiqueta para 'Read'
        self.read_checkbox = QCheckBox()
        self.read_checkbox.setChecked(True)  # Activado por defecto
        self.read_checkbox.setToolTip("Include Read nodes in search and replace")
        read_label = QLabel("Reads")
        checkboxes_layout.addWidget(read_label)
        checkboxes_layout.addWidget(self.read_checkbox)

        # Espacio de 50 pixeles
        checkboxes_layout.addSpacing(20)

        # Checkbox y etiqueta para 'Write'
        self.write_checkbox = QCheckBox()
        self.write_checkbox.setChecked(True)  # Activado por defecto
        self.write_checkbox.setToolTip("Include Write nodes in search and replace")
        write_label = QLabel("Writes")
        checkboxes_layout.addWidget(write_label)
        checkboxes_layout.addWidget(self.write_checkbox)

        # Espaciador para empujar el texto 'v1.1' hacia la derecha
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        checkboxes_layout.addItem(spacer)

        # Texto 'v1.1' alineado a la derecha
        version_label = QLabel("v1.1")
        version_label.setToolTip("Lega Pugliese - 2024")
        checkboxes_layout.addWidget(version_label)

        # Establecer la altura minima para el widget que contiene el layout
        checkboxes_widget.setMinimumHeight(30)

        # Anadir el widget al layout principal
        self.layout.addWidget(checkboxes_widget)

        # Conectar los checkboxes con la funcion de actualizacion
        self.read_checkbox.stateChanged.connect(self.updatePreviews)
        self.write_checkbox.stateChanged.connect(self.updatePreviews)

        # Campo de busqueda
        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText('Search...')
        self.layout.addWidget(self.find_input)

        # Campo de texto donde mostrar la informacion original
        self.preview_original = QTextEdit(self)
        self.preview_original.setReadOnly(True)
        self.preview_original.setStyleSheet(
            "QTextEdit { background-color: #282828; color: #c8c8c8; font-size: 10pt; line-height: 120%; }"
        )
        self.layout.addWidget(self.preview_original)

        # Campo de reemplazo
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText('Replace...')
        self.layout.addWidget(self.replace_input)

        # Campo de texto donde mostrar la informacion reemplazada
        self.preview_replace = QTextEdit(self)
        self.preview_replace.setReadOnly(True)
        self.preview_replace.setStyleSheet(
            "QTextEdit { background-color: #282828; color: #c8c8c8; font-size: 10pt; line-height: 120%; }"
        )
        self.layout.addWidget(self.preview_replace)


        # Boton para ejecutar el reemplazo
        self.run_button = QPushButton('Replace Paths', self)
        self.run_button.clicked.connect(self.replacePaths)
        self.layout.addWidget(self.run_button)

        # Conectar cambios en los campos de entrada con la funcion de actualizacion
        self.find_input.textChanged.connect(self.updatePreviews)
        self.replace_input.textChanged.connect(self.updatePreviews)

        self.setWindowTitle('Search and Replace in Paths')
        self.adjustSizeDialog()
        self.updatePreviews()

        # Atajos de teclado
        self.run_button.setShortcut(QKeySequence(Qt.Key_Return))
        self.find_input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super(SearchAndReplaceWidget, self).keyPressEvent(event)

    def replacePaths(self):
        nuke.Undo().begin('Replace All Paths')
        try:
            find_text = self.find_input.text()
            replace_text = self.replace_input.text()
            for node in self.nodes:
                if (node.Class() == 'Read' and self.read_checkbox.isChecked()) or \
                   (node.Class() == 'Write' and self.write_checkbox.isChecked()):
                    original_path = node['file'].getValue()
                    if find_text in original_path:
                        new_path = original_path.replace(find_text, replace_text)
                        node['file'].setValue(new_path)
            self.updatePreviews()
        finally:
            nuke.Undo().end()

        self.updatePreviews()
        self.close()

    def updatePreviews(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        original_previews = []
        replace_previews = []

        for node in self.nodes:
            if (node.Class() == 'Read' and self.read_checkbox.isChecked()) or \
               (node.Class() == 'Write' and self.write_checkbox.isChecked()):
                original_path = node['file'].getValue()
                new_path = original_path.replace(find_text, replace_text)
                highlighted_original_path = original_path.replace(find_text, '<span style="color: orange; font-weight: bold;">' + find_text + '</span>')
                highlighted_new_path = new_path.replace(replace_text, '<span style="color: orange; font-weight: bold;">' + replace_text + '</span>')
                original_previews.append(highlighted_original_path)
                replace_previews.append(highlighted_new_path)

        self.preview_original.setHtml('<br>'.join(original_previews))
        self.preview_replace.setHtml('<br>'.join(replace_previews))

    def adjustSizeDialog(self):
        # Calcular el ancho del texto mas largo
        fm = QFontMetrics(self.font())
        max_text_width = max([fm.width(node['file'].getValue()) for node in self.nodes] + [200], default=0)
        width = min(max_text_width * 2, 1600)  # Ancho maximo ajustado

        # Calcular la altura basada en el numero de nodos
        height_per_item = fm.lineSpacing() * 2  # Altura para dos lineas de texto
        estimated_height = len(self.nodes) * height_per_item + self.find_input.height() + self.replace_input.height() + self.run_button.height()

        # Obtener la altura del monitor
        screen_height = QApplication.primaryScreen().geometry().height()

        # Establecer un limite para la altura, por ejemplo, el 80% de la altura del monitor
        max_height = screen_height * 0.8

        # Usar el menor entre la altura calculada y el maximo permitido
        final_height = min(estimated_height, max_height)

        # Ajustar el tamano de los campos de texto previo
        # El numero de items visible en los previews sera proporcional a la altura final
        visible_items = max(1, int((final_height - self.find_input.height() - self.replace_input.height() - self.run_button.height()) / (2 * height_per_item)))
        self.preview_original.setFixedHeight(height_per_item * min(len(self.nodes), visible_items))
        self.preview_replace.setFixedHeight(height_per_item * min(len(self.nodes), visible_items))

        # Establecer el tamano minimo del dialogo
        self.setMinimumSize(width, final_height)


def show_search_replace_widget():
    # Obtener nodos seleccionados o todos los nodos si no hay seleccionados
    selected_nodes = nuke.selectedNodes('Read') + nuke.selectedNodes('Write')
    if not selected_nodes:
        selected_nodes = nuke.allNodes('Read') + nuke.allNodes('Write')

    # Mostrar el widget
    global search_replace_widget
    search_replace_widget = SearchAndReplaceWidget(selected_nodes)
    search_replace_widget.show()

# Llamar a la funcion para mostrar el widget
show_search_replace_widget()