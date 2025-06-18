from PySide2.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide2.QtCore import Qt

class DeleteWindow(QWidget):
    def __init__(self, total_files_to_delete):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #333; color: white; font-weight: bold;")

        if total_files_to_delete == 1:
            message = "Deleting..."
        elif 2 <= total_files_to_delete <= 200:
            message = (
                f"Deleting {total_files_to_delete} files.<br><br>"
                "<span style='color: #CCCCCC;'>Please wait...</span>"
            )
        else:  # Mas de 500 archivos
            message = (
                f"Deleting {total_files_to_delete} files.<br><br>"
                "<span style='color: #CCCCCC;'>"
                "The Nuke GUI may become unresponsive or freeze.<br>"
                "It will return once the deletion is complete.<br>"
                "This may take some time.<br>"
                "Please wait..."
                "</span>"
            )

        # Configurar el layout con mayor margen libre
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)  # Aumentar los margenes: izquierda, arriba, derecha, abajo
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setTextFormat(Qt.RichText)  # Habilitar HTML para cambiar el color del texto
        layout.addWidget(label)

        # Calcular el tamano de la ventana segun el texto
        label.adjustSize()
        self.resize(label.sizeHint().width() + 100, label.sizeHint().height() + 40)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

def center_window(window):
    screen_geometry = QApplication.primaryScreen().geometry()
    window_geometry = window.frameGeometry()
    x = (screen_geometry.width() - window_geometry.width()) // 2
    y = (screen_geometry.height() - window_geometry.height()) // 2
    window.move(x, y)

# Probar la funcion con diferentes cantidades de archivos
app = QApplication.instance() or QApplication([])
delete_window = DeleteWindow(300)  # Cambia el numero para probar diferentes mensajes
center_window(delete_window)
delete_window.show()
app.exec_()
