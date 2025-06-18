from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide2.QtGui import QScreen
from PySide2.QtCore import Qt
import nuke
import os
import re

class ReadNodeInfo(QWidget):
    def __init__(self, parent=None):
        super(ReadNodeInfo, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Read Nodes EXR Info")
        layout = QVBoxLayout(self)

        # Create the table
        self.table = QTableWidget(0, 6, self)  # Start with 0 rows and 5 columns now
        self.table.setHorizontalHeaderLabels(['Path', 'Read Node', 'IN', 'OUT', 'Frames', 'Missing Frames'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Load data into the table
        self.load_data()

        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Adjust window size and position to be centered
        self.adjust_window_size()


    def load_data(self):
        # Iterate over all Read nodes in the Nuke script
        print ("")
        print ("____________________________________")
        for node in nuke.allNodes('Read'):
            if node['file'].value().endswith('.exr'):  # Check if the file path ends with .exr
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                # No alignment change for 'Path'
                self.table.setItem(row_count, 0, QTableWidgetItem(node['file'].value()))
                
                # Center-align 'Read Node'
                read_node_item = QTableWidgetItem(node.name())
                read_node_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, 1, read_node_item)
                
                # Center-align 'IN'
                in_frame_item = QTableWidgetItem(str(node['first'].value()))
                in_frame_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, 2, in_frame_item)
                
                # Center-align 'OUT'
                out_frame_item = QTableWidgetItem(str(node['last'].value()))
                out_frame_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, 3, out_frame_item)
                
                # Calculate and center-align total frames
                in_frame = int(node['first'].value())
                out_frame = int(node['last'].value())
                total_frames = out_frame - in_frame + 1
                frames_item = QTableWidgetItem(str(total_frames))
                frames_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, 4, frames_item)
                
                # Determine the directory and file pattern
                directory = os.path.dirname(node['file'].value())
                filename_pattern = os.path.basename(node['file'].value())
                filename_pattern = re.sub(r'%0\d+d', r'%d', filename_pattern)  # Normalize the pattern       

                # Check for missing frames
                missing_frames = []
                for frame in range(in_frame, out_frame + 1):
                    expected_filename = os.path.join(directory, filename_pattern % frame)
                    if not os.path.exists(expected_filename):
                        missing_frames.append(str(frame))                
                
                print("")
                print(f"File path: {node['file'].value()}")
                # Add missing frames information or "OK" if none are missing
                if missing_frames:
                    missing_frames_items = QTableWidgetItem(", ".join(missing_frames))
                    missing_frames_item = QTableWidgetItem("MISSING")
                    print(f"missing: {missing_frames_items.text()}")  
                else:
                    missing_frames_item = QTableWidgetItem("OK")  
                    print(f"{missing_frames_item.text()}")

                # Move the alignment setting and setting the table item inside the if-else block
                missing_frames_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, 5, missing_frames_item)
               

        self.table.resizeColumnsToContents()


    def adjust_window_size(self):
        # Desactivar temporalmente el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana basado en el ancho de las columnas
        width = self.table.verticalHeader().width() - 40  # Un poco de relleno para estetica
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
            height += self.table.rowHeight(i) + 4  # Un pequeno relleno por fila

        # Asegurarse de que la altura no supera el 80% del alto de pantalla
        max_height = screen_rect.height() * 0.8
        final_height = min(height, max_height)

        # Reactivar el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamano de la ventana y centrarla
        self.resize(final_width, final_height)
        self.move((screen_rect.width() - final_width) // 2, (screen_rect.height() - final_height) // 2)

app = None
window = None

def main():
    global app, window
    # Check if there's already an instance of QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    if not app:  # If not, create a new instance
        app = QApplication([])
    window = ReadNodeInfo()
    window.show()

# Llamar a main() para iniciar la aplicacion
#main()
