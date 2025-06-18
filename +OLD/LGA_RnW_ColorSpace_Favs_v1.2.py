"""
________________________________________________________________________

  LGA_RnW_ColorSpace_Favs v1.2 | 2024 | Lega  
  Tool for applying OCIO color spaces to selected Read and Write nodes  
________________________________________________________________________

"""

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout
from PySide2.QtCore import Qt, QRect
from PySide2.QtGui import QCursor, QPalette, QColor
import configparser
import nuke
import os

class SelectedNodeInfo(QWidget):
    def __init__(self, parent=None):
        super(SelectedNodeInfo, self).__init__(parent)
        self.color_spaces = self.load_color_spaces()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)  # Quitar la barra de titulo estandar
        self.setWindowTitle("Node Information")
        layout = QVBoxLayout(self)

        # Crear una barra de titulo personalizada
        title_bar = QWidget(self)
        title_bar.setFixedHeight(20)  # Hacer la barra de titulo mas pequena
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Agregar un espacio para empujar el boton de cierre a la derecha
        title_bar_layout.addStretch(1)
        
        # Agregar el boton de cierre personalizado
        close_button = QPushButton('X', self)
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("background-color: none; color: white; border: none;")
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)
        
        layout.addWidget(title_bar)

        # Crear la tabla con 1 columna y 5 filas
        self.table = QTableWidget(len(self.color_spaces), 1, self)
        self.table.setHorizontalHeaderLabels(['Output Transform'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Eliminar numeros de las filas
        self.table.verticalHeader().setVisible(False)
        
        # Centrar los titulos de la columna
        self.table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)

        # Configurar la paleta de la tabla para cambiar el color de seleccion a gris claro
        palette = self.table.palette()
        palette.setColor(QPalette.Highlight, QColor(230, 230, 230))  # Gris claro
        palette.setColor(QPalette.HighlightedText, QColor(Qt.black))
        self.table.setPalette(palette)

        # Configurar el estilo de la tabla
        self.table.setStyleSheet("""
            QTableView::item:selected {
                background-color: rgb(230, 230, 230);  # Gris claro
                color: black;
            }
        """)

        # Configurar el comportamiento de seleccion para seleccionar filas enteras
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # Cargar datos en la tabla
        self.load_data()

        # Conectar el evento de clic de la celda para cambiar el espacio de color
        self.table.cellClicked.connect(self.change_color_space)

        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Ajustar el tamano de la ventana y posicionarla en el centro
        self.adjust_window_size()

    def load_color_spaces(self):
        config = configparser.ConfigParser(allow_no_value=True)
        ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'LGA_RnW_ColorSpace_Favs_List.ini')
        
        if not os.path.exists(ini_path):
            print(f"Error: El archivo {ini_path} no se encuentra.")
            return ["Default", "ACES - ACES2065-1", "ACES - ACEScg", "ACES - ACEScct", "Output - Rec.709"]
        
        config.optionxform = str  # Esto asegura que se respeten las mayusculas
        config.read(ini_path)

        if 'ColorSpaces' not in config:
            print("Error: La seccion 'ColorSpaces' no se encuentra en el archivo INI.")
            return ["Default", "ACES - ACES2065-1", "ACES - ACEScg", "ACES - ACEScct", "Output - Rec.709"]

        return [key for key in config['ColorSpaces']]


    def load_data(self):
        for row, name in enumerate(self.color_spaces):
            node_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, node_item)

        self.table.resizeColumnsToContents()

    def adjust_window_size(self):
        # Desactivar temporalmente el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana basado en el ancho de las columnas y el texto mas ancho
        width = self.table.verticalHeader().width()  # Un poco de relleno para estetica
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i) + 50  # Un poco mas de relleno entre columnas

        # Ajustar el ancho adicional basado en el texto mas ancho
        longest_text = max(self.color_spaces, key=len)
        font_metrics = self.table.fontMetrics()
        text_width = font_metrics.horizontalAdvance(longest_text) + 50  # Un poco de relleno adicional
        width = max(width, text_width)

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

        # Incluir la altura de la barra de titulo personalizada
        title_bar_height = 20
        height += title_bar_height

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_row = self.table.currentRow()
            if current_row >= 0:
                self.change_color_space(current_row, 0)
        else:
            super(SelectedNodeInfo, self).keyPressEvent(event)

    def change_color_space(self, row, column):
        selected_color_space = self.color_spaces[row]
        
        # Obtener los nodos seleccionados
        selected_nodes = nuke.selectedNodes()

        if selected_nodes:
            for node in selected_nodes:
                if node.Class() == 'Read' or node.Class() == 'Write':
                    try:
                        node['colorspace'].setValue(selected_color_space)
                    except Exception as e:
                        print(f"Error al cambiar el espacio de color: {e}")
        
        # Cerrar la ventana despues de aplicar los cambios
        self.close()

app = None
window = None

def main():
    global app, window
    # Verificar si ya hay una instancia de QApplication
    app = QApplication.instance() or QApplication([])
    window = SelectedNodeInfo()
    window.show()

# Llamar a main() para iniciar la aplicacion
#main()
