"""
_____________________________________________________________________________________________________

  LGA_ToolPack_settings_ShotName v0.1 | Lega
  Configuracion de la nomenclatura de archivos para LGA_ToolPack.
_____________________________________________________________________________________________________
"""

import sys
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QDesktopWidget,
    QMessageBox,
)
from PySide2.QtCore import Qt

# Variable global para controlar el debug (si se necesita en el futuro)
debug = False

# --- Instancia global para la ventana de ShotName Settings ---
shotname_window_instance = None


# Funcion debug_print (si se necesita en el futuro)
def debug_print(*message):
    if DEBUG:
        print(*message)


class ShotNameSettingsWindow(QWidget):
    """Ventana para configurar la nomenclatura de archivos de Nuke."""

    def __init__(self, parent=None):
        debug_print("[ShotName] ShotNameSettingsWindow.__init__ llamado")
        super().__init__(parent)  # Pasar parent al constructor base
        self.setWindowTitle("LGA Show in Flow - Shot Naming Settings")
        self.setMinimumWidth(550)  # Ajustar ancho segun diseno
        self.initUI()
        self.center_window()

    def center_window(self):
        """Centra la ventana en la pantalla."""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # --- 1. Filename Pattern Structure --- #
        pattern_group = QGroupBox("1. Filename Pattern Structure")
        pattern_layout = QVBoxLayout()

        pattern_desc1 = QLabel(
            "Define the structure of your Nuke script filenames using predefined\n"
            "tags separated by underscores (_). Do not include the version suffix\n"
            "(_vXX) or the file extension (.nk)."
        )
        pattern_desc2 = QLabel(
            "<b>Available tags:</b> Project, Sequence, Shot, Task, Version, Extra.<br>"
            "Ensure 'Project' and 'Shot' tags are included. 'Extra' can represent\n"
            "one or more optional parts. Define the full pattern structure, as\n"
            "other LGA tools might use all parts."
        )
        pattern_desc2.setStyleSheet("margin-top: 5px;")

        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("e.g., Project_Sequence_Shot_Extra_Task")

        pattern_example = QLabel(
            "<i>*Example Breakdown: If your file is 'MYPROJ_SQ010_SH020_comp_v01.nk',<br>"
            "your pattern might be: Project_Sequence_Shot_Task</i>"
        )
        pattern_example.setStyleSheet("margin-top: 5px; font-size: 9pt; color: grey;")

        pattern_layout.addWidget(pattern_desc1)
        pattern_layout.addWidget(pattern_desc2)
        pattern_layout.addWidget(self.pattern_input)
        pattern_layout.addWidget(pattern_example)
        pattern_group.setLayout(pattern_layout)
        main_layout.addWidget(pattern_group)

        # --- 2. Shot Code Composition --- #
        shotcode_group = QGroupBox("2. Shot Code Composition")
        shotcode_layout = QVBoxLayout()

        shotcode_desc = QLabel(
            "Write the tags from your pattern (above), separated by underscores (_),\n"
            "that combine to form the <b>exact Shot Code</b> used in Flow's 'Shot'\n"
            "entity 'code' field."
        )

        self.shotcode_input = QLineEdit()
        self.shotcode_input.setPlaceholderText("e.g., Sequence_Shot")

        shotcode_examples = QLabel(
            "<i>*Examples:*<br>"
            "- If Flow Code is 'SQ010_SH020' -> Write: Sequence_Shot<br>"
            "- If Flow Code is 'MYPROJ_SH020' -> Write: Project_Shot<br>"
            "- If Flow Code is just 'SH020' -> Write: Shot</i>"
        )
        shotcode_examples.setStyleSheet("margin-top: 5px; font-size: 9pt; color: grey;")

        shotcode_layout.addWidget(shotcode_desc)
        shotcode_layout.addWidget(self.shotcode_input)
        shotcode_layout.addWidget(shotcode_examples)
        shotcode_group.setLayout(shotcode_layout)
        main_layout.addWidget(shotcode_group)

        # --- 3. Target Flow Task Name --- #
        taskname_group = QGroupBox("3. Target Flow Task Name")
        taskname_layout = QVBoxLayout()

        taskname_desc = QLabel(
            "Enter the exact name (case-sensitive) of the Task to open in Flow.\n"
            "This must match the 'content' field of the 'Task' entity.<br>"
            "(This is often 'Comp' for Nuke scripts)."  # Separar linea
        )

        self.taskname_input = QLineEdit()
        self.taskname_input.setPlaceholderText("Comp")

        taskname_layout.addWidget(taskname_desc)
        taskname_layout.addWidget(self.taskname_input)
        taskname_group.setLayout(taskname_layout)
        main_layout.addWidget(taskname_group)

        # Separador y Botones
        main_layout.addStretch()  # Empuja botones abajo

        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Empuja botones a la derecha
        self.save_button = QPushButton("Save Settings")
        self.cancel_button = QPushButton("Cancel")

        # Conectar senales (por ahora, solo cierran o muestran mensaje)
        self.save_button.clicked.connect(
            self.save_settings
        )  # Cambiado a self.save_settings
        self.cancel_button.clicked.connect(self.close)  # Cancelar simplemente cierra

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        # Cargar settings iniciales (placeholder)
        self.load_initial_settings()

    def load_initial_settings(self):
        """Carga los settings guardados (funcion placeholder)."""
        # TODO: Implementar la carga real desde un archivo de configuracion
        # Por ahora, podemos poner valores por defecto o dejar los placeholders
        # self.pattern_input.setText("Project_Sequence_Shot_Task")
        # self.shotcode_input.setText("Sequence_Shot")
        # self.taskname_input.setText("Comp")
        pass

    def save_settings(self):
        """Guarda los settings (funcion placeholder)."""
        # TODO: Implementar la logica de guardado real
        pattern = self.pattern_input.text().strip()
        shotcode = self.shotcode_input.text().strip()
        taskname = self.taskname_input.text().strip()

        # Validacion basica (se puede mejorar)
        if not pattern or not shotcode or not taskname:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        # Mensaje temporal mientras no se implementa el guardado
        QMessageBox.information(
            self, "Not Implemented", "Save functionality is not yet implemented."
        )
        print(f"DEBUG: Pattern: {pattern}")
        print(f"DEBUG: Shot Code Composition: {shotcode}")
        print(f"DEBUG: Task Name: {taskname}")
        # self.close() # Opcional: cerrar despues de guardar

    def keyPressEvent(self, event):
        """Cerrar la ventana si se presiona ESC."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def main(parent=None):
    debug_print("[ShotName] main() llamado")
    global shotname_window_instance
    app = QApplication.instance() or QApplication(sys.argv)
    if shotname_window_instance is None or not shotname_window_instance.isVisible():
        debug_print("[ShotName] Creando nueva instancia de ShotNameSettingsWindow")
        shotname_window_instance = ShotNameSettingsWindow()  # No pasar parent
        shotname_window_instance.show()
    else:
        debug_print("[ShotName] Ventana ya existe, trayendo al frente")
        shotname_window_instance.raise_()
        shotname_window_instance.activateWindow()


# --- Main Execution ---
if __name__ == "__main__":
    # Necesario para ejecucion standalone fuera de Nuke
    main()
