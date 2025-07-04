"""
_______________________________________

  LGA_mediaManager v1.61 | Lega
_______________________________________

"""

from PySide2.QtWidgets import (
    QApplication,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QToolButton,
    QSizePolicy,
    QFileDialog,
)
from PySide2.QtWidgets import (
    QItemDelegate,
    QStyle,
    QMessageBox,
    QCheckBox,
    QLabel,
    QHBoxLayout,
    QSpinBox,
    QFrame,
    QMenu,
    QAction,
    QProgressBar,
    QLineEdit,
)
from PySide2.QtGui import QBrush, QColor, QPalette, QMovie, QScreen, QIcon
from PySide2.QtCore import Qt, QTimer, QThread, Signal, QObject, QRunnable, Slot
import nuke
import os
import re
import subprocess
import time
import shutil
import sys
import configparser
import logging
from PySide2.QtCore import QThreadPool


start_time = time.time()


def configure_logger():
    if hasattr(configure_logger, "logger"):
        return configure_logger.logger

    log_file_path = os.path.join(os.path.dirname(__file__), "LGA_mediaManager.log")

    # Abrir el archivo de log en modo 'w' para limpiarlo cada vez que se ejecuta el script
    with open(log_file_path, "w") as f:
        f.write("")  # Sobrescribe el contenido del archivo, limpiandolo

    logger = logging.getLogger("LGA_MediaManager")
    logger.setLevel(logging.DEBUG)

    # Eliminar cualquier manejador que ya este configurado en el logger
    if logger.hasHandlers():
        logger.handlers.clear()

    # Crear manejador de archivo
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)

    # Crear formateador y anadirlo al manejador
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)

    # Anadir el manejador al logger
    logger.addHandler(file_handler)

    configure_logger.logger = logger
    return logger


# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


# Agrega el directorio send2trash a sys.path
script_dir = os.path.dirname(
    __file__
)  # Obtiene el directorio en el que se encuentra el script
send2trash_dir = os.path.join(
    script_dir, "Send2Trash-1.8.2"
)  # Construye la ruta al directorio send2trash
sys.path.append(
    send2trash_dir
)  # Anade el directorio send2trash a la lista de rutas de busqueda
import send2trash


class SettingsWindow(QWidget):
    def __init__(self, settings_data, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.settings_data = (
            settings_data.copy()
        )  # Hacemos una copia en memoria del diccionario de configuracion
        self.initUI()

    def initUI(self):
        # Reseteamos el layout cada vez que se llama a initUI
        self.layout = QVBoxLayout(self)  # Crear un nuevo layout
        self.setLayout(self.layout)
        self.setStyleSheet("background-color: #2e2e2e;")
        self.path_layouts = []  # Lista para almacenar los layouts de los paths

        # Configuracion de "Folder scan depth" con QSpinBox
        folder_scan_hbox = QHBoxLayout()
        folder_scan_hbox.setObjectName("Folder scan depth layout")
        label = QLabel("Folder scan depth:")
        label.setObjectName("Folder scan depth label")
        label.setStyleSheet("font-weight: bold")  # Establecer el texto en negrita

        self.folder_depth_spinbox = QSpinBox()
        self.folder_depth_spinbox.setRange(1, 10)
        folder_depth_value = int(self.settings_data.get("Folder scan depth", 3))
        self.folder_depth_spinbox.setValue(folder_depth_value)
        self.folder_depth_spinbox.setFixedWidth(30)  # Limitar el ancho del QSpinBox
        self.folder_depth_spinbox.setObjectName("Folder scan depth spinbox")
        self.folder_depth_spinbox.setStyleSheet(
            """
            QSpinBox {
                background-color: #282828;
                color: #D3D3D3;
                border: 0px solid black;
                padding: 2px;
                min-height: 17px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #282828;
                border: 1px sold white;
            }
            QToolTip {
                color: #D3D3D3;
                background-color: #222222;
                border: 1px solid #222222;
                padding: 6px;
            }
        """
        )
        self.folder_depth_spinbox.setToolTip(
            "Sets the number of folder levels to move up from the script's location to find the main shot folder"
        )

        folder_scan_hbox.addWidget(label)
        folder_scan_hbox.addWidget(self.folder_depth_spinbox)
        folder_scan_hbox.addStretch()  # Anadir un espacio flexible a la derecha
        self.layout.addLayout(folder_scan_hbox)

        # Anadir una linea en blanco antes de la primera linea divisora
        self.layout.addSpacing(10)

        # Linea separadora debajo de "Folder scan depth"
        separator1 = QFrame()
        separator1.setObjectName("First separator line")
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator1)

        # Anadir una linea en blanco despues de la primera linea divisora
        self.layout.addSpacing(10)

        # Texto que dice "Copy to:"
        copy_to_label = QLabel("Copy to:")
        copy_to_label.setObjectName("Copy to label")
        copy_to_label.setStyleSheet(
            "font-weight: bold"
        )  # Establecer el texto en negrita

        self.layout.addWidget(copy_to_label)
        self.layout.addSpacing(10)

        # Configuraciones de paths con nombre y path
        i = 1
        while True:
            button_text_key = f"copy_{i}_button_text"
            path_key = f"copy_{i}_subdirectory"
            if (
                button_text_key not in self.settings_data
                or path_key not in self.settings_data
            ):
                break  # Si no hay mas configuraciones, salir del bucle

            button_text = self.settings_data.get(button_text_key, f"Button Name {i}")
            path_value = self.settings_data.get(path_key, "")

            # Crear un layout vertical que contenga todo lo relacionado con este path
            path_vbox = QVBoxLayout()
            path_vbox.setObjectName(f"Path {i} layout")

            # Layout para el nombre del boton
            button_name_hbox = QHBoxLayout()
            button_name_hbox.setObjectName(f"Button name {i} layout")
            button_name_label = QLabel(f"Name {i}:")
            button_name_label.setObjectName(f"Button name {i} label")
            button_name_line_edit = QLineEdit(button_text)
            button_name_line_edit.setObjectName(f"Button name {i} line edit")
            button_name_line_edit.setToolTip(
                "Name to be displayed in the Copy menu.\nUse & before a letter in the name to use that letter as a shortcut.\ne.g., &Assets will have shortcut Alt+A"
            )
            button_name_line_edit.setFixedWidth(
                283
            )  # Ancho fijo para la caja de entrada del nombre
            button_name_line_edit.setStyleSheet(
                """
                QLineEdit {
                    background-color: #282828;
                    color: #D3D3D3;
                    border: 0px solid black;
                    padding: 2px;
                    min-height: 17px;
                }
                QToolTip {
                    color: #D3D3D3;
                    background-color: #222222;
                    border: 1px solid #222222;
                    padding: 6px;
                }
            """
            )

            button_name_hbox.addWidget(button_name_label)
            button_name_hbox.addWidget(button_name_line_edit)
            button_name_hbox.addStretch()  # Anadir un espacio para alinear el ancho con el boton de menos
            path_vbox.addLayout(button_name_hbox)

            # Layout para el path y el boton de eliminar
            path_hbox = QHBoxLayout()
            path_hbox.setObjectName(f"Path {i} hbox layout")
            path_label = QLabel(f"Path {i}:  ")
            path_label.setObjectName(f"Path {i} label")
            path_line_edit = QLineEdit(path_value)
            path_line_edit.setObjectName(f"Path {i} line edit")
            path_line_edit.setToolTip(
                "This is the path to the folder relative to the shot's base path"
            )
            path_line_edit.setStyleSheet(
                """
                QLineEdit {
                    background-color: #282828;
                    color: #D3D3D3;
                    border: 0px solid black;
                    padding: 2px;
                    min-height: 17px;
                }
                QToolTip {
                    color: #D3D3D3;
                    background-color: #222222;
                    border: 1px solid #222222;
                    padding: 6px;
                }
            """
            )
            minus_button = QPushButton("-")
            minus_button.setObjectName(f"Path {i} minus button")
            minus_button.setFixedWidth(30)
            minus_button.setToolTip("Remove this path")
            minus_button.setStyleSheet(
                """
                QToolTip {
                    color: #D3D3D3;
                    background-color: #222222;
                    border: 1px solid #222222;
                    padding: 6px;
                }
            """
            )

            minus_button.clicked.connect(self.create_remove_path_callback(i - 1))

            path_hbox.addWidget(path_label)
            path_hbox.addWidget(path_line_edit)
            path_hbox.addWidget(minus_button)
            path_vbox.addLayout(path_hbox)

            # Anadir un espaciado entre los paths
            path_vbox.addSpacing(10)

            # Guardar el layout principal para este path
            self.layout.addLayout(path_vbox)
            self.path_layouts.append(path_vbox)  # Solo guardar el layout principal
            i += 1

        # Boton "Add Path" debajo de los paths
        self.add_path_button = QPushButton("+")
        self.add_path_button.setObjectName("Add path button")
        self.add_path_button.setToolTip("Add a new path")
        self.add_path_button.setStyleSheet(
            """
            QToolTip {
                color: #D3D3D3;
                background-color: #222222;
                border: 1px solid #222222;
                padding: 6px;
            }
        """
        )
        self.add_path_button.clicked.connect(self.add_path)
        add_path_hbox = QHBoxLayout()
        add_path_hbox.setObjectName("Add path hbox layout")
        add_path_hbox.addStretch()  # Agregar espacio flexible a la izq del boton
        add_path_hbox.addWidget(self.add_path_button)
        self.layout.addLayout(add_path_hbox)

        # Anadir una linea en blanco antes de la segunda linea divisora
        self.layout.addSpacing(10)

        # Linea separadora debajo del boton "Add Path"
        separator2 = QFrame()
        separator2.setObjectName("Second separator line")
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator2)

        # Espaciado antes de los botones "Cancel" y "Save Settings"
        self.layout.addSpacing(10)

        # Crear los botones "Cancel" y "Save"
        buttons_layout = QHBoxLayout()
        buttons_layout.setObjectName("Buttons layout")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("Cancel button")
        self.cancel_button.clicked.connect(self.close)
        self.save_button = QPushButton("Save Settings")
        self.save_button.setObjectName("Save button")
        self.save_button.clicked.connect(self.save_settings)

        buttons_layout.addStretch()  # Agregar espacio flexible a la izquierda de los botones
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        self.layout.addLayout(buttons_layout)

        self.setLayout(self.layout)

    def save_settings(self):
        # Actualizar self.settings_data con la informacion visible en pantalla
        new_settings_data = {
            "Folder scan depth": self.settings_data["Folder scan depth"]
        }
        for i, path_layout in enumerate(self.path_layouts):
            # Obtener el texto del boton y el path desde la interfaz
            button_name_line_edit = path_layout.itemAt(0).layout().itemAt(1).widget()
            path_line_edit = path_layout.itemAt(1).layout().itemAt(1).widget()

            # Actualizar el diccionario con los valores actuales
            new_settings_data[f"copy_{i + 1}_button_text"] = (
                button_name_line_edit.text()
            )
            new_settings_data[f"copy_{i + 1}_subdirectory"] = path_line_edit.text()

        # Asignar el nuevo diccionario actualizado
        self.settings_data = new_settings_data

        # Imprimir el estado que se guardara en el archivo .ini
        print(f"\n\nGuardando la siguiente informacion en el .ini:")
        print(self.format_ini_output())

        # Guardar la informacion en un archivo .ini
        ini_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "LGA_mediaManagerSettings.ini"
        )

        # Abrir el archivo para escribir
        with open(ini_path, "w") as ini_file:
            ini_file.write(self.format_ini_output())

        print(f"Configuracion guardada en {ini_path}")

    def add_path(self):
        index = len(self.path_layouts) + 1

        # Crear un layout vertical que contenga todo lo relacionado con este path
        path_vbox = QVBoxLayout()

        # Layout para el nombre del boton
        button_name_hbox = QHBoxLayout()
        button_name_label = QLabel(f"Name {index}:")
        button_name_line_edit = QLineEdit("")
        button_name_line_edit.setToolTip(
            "Name to be displayed in the Copy menu. Use & before a letter in the name to use that letter as a shortcut (e.g., &Assets will have shortcut Alt+A)"
        )
        button_name_line_edit.setFixedWidth(
            283
        )  # Ancho fijo para la caja de entrada del nombre
        button_name_line_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #282828;
                color: #D3D3D3;
                border: 0px solid black;
                padding: 2px;
                min-height: 17px;
            }
            QToolTip {
                color: #D3D3D3;
                background-color: #222222;
                border: 1px solid #222222;
                padding: 6px;
            }
        """
        )
        button_name_hbox.addWidget(button_name_label)
        button_name_hbox.addWidget(button_name_line_edit)
        button_name_hbox.addStretch()  # Anadir un espacio para alinear el ancho con el boton de menos
        path_vbox.addLayout(button_name_hbox)

        # Layout para el path y el boton de eliminar
        path_hbox = QHBoxLayout()
        path_label = QLabel(f"Path {index}:  ")
        path_line_edit = QLineEdit("")
        path_line_edit.setToolTip(
            "This is the path to the folder relative to the shot's base path"
        )
        path_line_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #282828;
                color: #D3D3D3;
                border: 0px solid black;
                padding: 2px;
                min-height: 17px;
            }
            QToolTip {
                color: #D3D3D3;
                background-color: #222222;
                border: 1px solid #222222;
                padding: 6px;
            }
        """
        )
        minus_button = QPushButton("-")
        minus_button.setFixedWidth(30)
        minus_button.setToolTip("Remove this path")
        minus_button.setStyleSheet(
            """
            QToolTip {
                color: #D3D3D3;
                background-color: #222222;
                border: 1px solid #222222;
                padding: 6px;
            }
        """
        )

        minus_button.clicked.connect(self.create_remove_path_callback(index - 1))

        path_hbox.addWidget(path_label)
        path_hbox.addWidget(path_line_edit)
        path_hbox.addWidget(minus_button)
        path_vbox.addLayout(path_hbox)

        # Anadir un espaciado entre los paths
        path_vbox.addSpacing(10)

        # Guardar el layout principal para este path
        self.layout.insertLayout(self.layout.count() - 5, path_vbox)
        self.path_layouts.append(path_vbox)  # Solo guardar el layout principal

        # Agregar el nuevo path a self.settings_data
        self.settings_data[f"copy_{index}_button_text"] = button_name_line_edit.text()
        self.settings_data[f"copy_{index}_subdirectory"] = path_line_edit.text()

    def remove_path(self, index):
        # Print de depuracion antes de modificar el ini
        debug_print(f"INI Antes de remover el path {index + 1}:")
        debug_print(self.format_ini_output())

        # Imprimir la cantidad y tipos de layouts/widgets antes de eliminar
        self.print_layout_widget_info()

        # Eliminar el path del ini en memoria
        del self.settings_data[f"copy_{index + 1}_button_text"]
        del self.settings_data[f"copy_{index + 1}_subdirectory"]

        # Remover el layout correspondiente de la UI
        layout_to_remove = self.path_layouts[index]
        self.clear_layout(layout_to_remove)

        # Remover el layout del layout principal
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.layout() == layout_to_remove:
                self.layout.takeAt(i)
                break

        layout_to_remove.deleteLater()  # Asegurar que se elimina correctamente

        # Eliminar el layout del path de la lista path_layouts
        del self.path_layouts[index]

        # Renumerar los paths restantes en la interfaz
        for i, path_layout in enumerate(self.path_layouts):
            # Actualizar el numero en la etiqueta y en el objectName
            button_name_label = path_layout.itemAt(0).layout().itemAt(0).widget()
            button_name_label.setText(f"Name {i + 1}:")
            button_name_label.setObjectName(f"Button name {i + 1} label")

            # Actualizar el QLineEdit objectName
            button_name_line_edit = path_layout.itemAt(0).layout().itemAt(1).widget()
            button_name_line_edit.setObjectName(f"Button name {i + 1} line edit")

            # Actualizar el QLabel del path
            path_label = path_layout.itemAt(1).layout().itemAt(0).widget()
            path_label.setText(f"Path {i + 1}:")
            path_label.setObjectName(f"Path {i + 1} label")

            # Actualizar el QPushButton del remove
            minus_button = path_layout.itemAt(1).layout().itemAt(2).widget()
            minus_button.setObjectName(f"Path {i + 1} minus button")
            minus_button.clicked.disconnect()
            minus_button.clicked.connect(self.create_remove_path_callback(i))

            # Actualizar el objectName del layout
            path_layout.setObjectName(f"Path {i + 1} layout")

        # Renumerar los paths en settings_data
        new_settings_data = {
            "Folder scan depth": self.settings_data["Folder scan depth"]
        }
        for i, path_layout in enumerate(self.path_layouts):
            # Usar i + 1 porque estamos reindexando los paths
            new_settings_data[f"copy_{i + 1}_button_text"] = self.settings_data.get(
                f"copy_{i + 2}_button_text", ""
            )
            new_settings_data[f"copy_{i + 1}_subdirectory"] = self.settings_data.get(
                f"copy_{i + 2}_subdirectory", ""
            )

        self.settings_data = new_settings_data

        # Imprimir la cantidad y tipos de layouts/widgets despues de eliminar
        debug_print("\nLAYOUT Despues de eliminar el path:")
        self.print_layout_widget_info()

        # Ajustar solo la altura de la ventana, manteniendo el ancho predeterminado
        self.adjustSize()
        self.setFixedWidth(400)  # Ancho predeterminado

        # Print de depuracion despues de modificar el ini
        debug_print(f"\n\nINI Despues de remover el path {index + 1}:")
        debug_print(self.format_ini_output())

        # Actualizar self.settings_data con la informacion visible en pantalla
        new_settings_data = {
            "Folder scan depth": self.settings_data["Folder scan depth"]
        }
        for i, path_layout in enumerate(self.path_layouts):
            # Obtener el texto del boton y el path desde la interfaz
            button_name_line_edit = path_layout.itemAt(0).layout().itemAt(1).widget()
            path_line_edit = path_layout.itemAt(1).layout().itemAt(1).widget()

            # Actualizar el diccionario con los valores actuales
            new_settings_data[f"copy_{i + 1}_button_text"] = (
                button_name_line_edit.text()
            )
            new_settings_data[f"copy_{i + 1}_subdirectory"] = path_line_edit.text()

        # Asignar el nuevo diccionario actualizado
        self.settings_data = new_settings_data

        # Imprimir el estado actualizado despues de modificar el ini
        debug_print(
            f"\n\nINI Despues de actualizar self.settings_data con la informacion de la pantalla:"
        )
        debug_print(self.format_ini_output())

    def clear_layout(self, layout):
        debug_print("")
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                debug_print(f"  Eliminando widget: {child.widget().objectName()}")
                child.widget().deleteLater()
            elif child.layout():
                debug_print(f"  Eliminando layout: {child.layout().objectName()}")
                self.clear_layout(child.layout())
                child.layout().deleteLater()

    def create_remove_path_callback(self, index):
        def callback():
            self.remove_path(index)

        return callback

    def print_layout_widget_info(self):
        # Funcion para imprimir informacion sobre los layouts y widgets
        debug_print("\nInformacion de Layouts y Widgets:")
        count = self.layout.count()
        debug_print(f"  Total elementos en layout principal: {count}")
        for i in range(count):
            item = self.layout.itemAt(i)
            if item.widget():
                debug_print(
                    f"    Widget: {item.widget().__class__.__name__} - ObjectName: {item.widget().objectName()}"
                )
            elif item.layout():
                debug_print(
                    f"    Layout: {item.layout().__class__.__name__} - ObjectName: {item.layout().objectName()}"
                )
            else:
                debug_print("    Elemento desconocido")

    def format_ini_output(self):
        ini_representation = "[LGA_mediaManagerSettings]\n"
        ini_representation += f"project_folder_depth = {self.settings_data.get('Folder scan depth', 3)}\n\n"
        ini_representation += "[CopyOptions]\n"

        current_index = 1  # Inicializar el indice para la reindexacion
        i = 1
        while True:
            button_text_key = f"copy_{i}_button_text"
            path_key = f"copy_{i}_subdirectory"
            if (
                button_text_key not in self.settings_data
                or path_key not in self.settings_data
            ):
                break

            button_text_value = self.settings_data[button_text_key]
            path_value = self.settings_data[path_key]

            # Comprobar si alguna de las variables esta vacia
            if not button_text_value or not path_value:
                i += 1
                continue  # Omitir esta entrada si hay un campo vacio

            # Agregar comillas alrededor de los valores
            button_text_value = f'"{button_text_value}"'
            path_value = f'"{path_value}"'

            # Utilizar current_index para asegurar una numeracion continua
            ini_representation += (
                f"copy_{current_index}_button_text = {button_text_value}\n"
            )
            ini_representation += (
                f"copy_{current_index}_subdirectory = {path_value}\n\n"
            )

            current_index += 1  # Incrementar solo si se utilizo un valor valido
            i += 1

        return ini_representation.strip()  # Eliminar cualquier espacio extra al final

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


class FileScanner(QWidget):
    def __init__(self, parent=None):
        super(FileScanner, self).__init__(parent)  # Inicializar la clase base primero

        # Comprobar si el script de Nuke está guardado
        if not nuke.root().name() or nuke.root().name() == "Root":
            self.initialization_successful = False
            return  # Finalizar la inicialización aquí sin crear ninguna ventana

        # Inicializar atributos básicos primero
        self.matched_reads = []
        self.font_size = 10
        self.sequence_extensions = [".exr", ".tif", ".png", ".jpg"]
        self.non_sequence_extensions = [".mov", ".psd", ".avi", ".mp4"]

        # Configurar logger
        self.logger = configure_logger()

        # Cargar configuración
        self.settings_data = (
            None  # Crear un atributo para guardar los settings en memoria
        )
        self.load_settings()  # Cargar settings del archivo .ini

        # Crear el scanner_worker después de que los atributos estén inicializados
        self.scanner_worker = ScannerWorker(self)

        # Asumimos que la inicialización es exitosa
        self.initialization_successful = True

        # Inicializar la UI
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Crea y configura el status_label
        # self.status_label = QLabel("")
        # self.layout.addWidget(self.status_label)

        # Crear layout para botones a la izquierda
        left_buttons_layout = QHBoxLayout()

        # Crear botones Reveal, Delete, y Go to Read y agregarlos despues del checkbox
        self.go_to_read_button = QPushButton("&Go to Read")
        self.go_to_read_button.setToolTip("Go to the Read node in Nuke")
        self.reveal_button = QPushButton("&Explorer")
        self.reveal_button.setToolTip("Reveal the file location in the file explorer")
        self.delete_button = QPushButton("&Delete")
        self.delete_button.setToolTip("Delete the selected file")
        self.relink_button = QPushButton("Re&link")
        self.relink_button.setToolTip("Relink the selected offline file")

        self.relink_button.clicked.connect(self.relink)
        self.reveal_button.clicked.connect(self.reveal_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.go_to_read_button.clicked.connect(self.go_to_read)

        # Crear el boton 'Copy to...'
        self.copy_button = QToolButton(self)
        self.copy_button.setText("&Copy to")
        self.copy_button.setPopupMode(QToolButton.InstantPopup)
        self.copy_menu = QMenu(self)
        self.copy_button.setToolTip(
            "Copy the selected files to a specific folder and update the corresponding Read node's path"
        )

        # Crear acciones dinamicamente basadas en las opciones cargadas
        for button_text, subdirectory in self.copy_options:
            action = QAction(button_text, self)

            # Buscar la letra despues de '&' para establecer el shortcut
            if "&" in button_text:
                ampersand_index = button_text.index("&")
                if ampersand_index < len(button_text) - 1:
                    shortcut_letter = button_text[ampersand_index + 1].upper()
                    shortcut = f"Alt+{shortcut_letter}"
                    action.setShortcut(shortcut)

            # Conectar la accion
            action.triggered.connect(
                lambda checked=False, subdir=subdirectory: self.copy_to(subdir)
            )

            # Anadir la accion al menu
            self.copy_menu.addAction(action)

        self.copy_button.setMenu(self.copy_menu)

        # Establecer un ancho fijo para los botones
        self.reveal_button.setFixedWidth(100)
        self.go_to_read_button.setFixedWidth(100)
        self.delete_button.setFixedWidth(100)
        self.relink_button.setFixedWidth(100)
        self.copy_button.setFixedWidth(100)
        self.copy_button.setMaximumHeight(24)
        self.copy_button.setMinimumHeight(24)
        self.copy_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Agregar botones al layout de botones
        left_buttons_layout.addWidget(self.go_to_read_button)
        left_buttons_layout.addWidget(self.reveal_button)
        left_buttons_layout.addWidget(self.relink_button)
        left_buttons_layout.addWidget(self.delete_button)
        left_buttons_layout.insertWidget(4, self.copy_button)

        # Configura el margen interno vertical del layout de botones izquierdo
        left_buttons_layout.setContentsMargins(
            0, 9, 0, 9
        )  # Anade un margen superior e inferior de 9 pixeles

        # Layout para Color, Font Size, Folder Depth y el boton Rescan
        right_buttons_layout = QHBoxLayout()

        # Boton de la flecha
        self.are_buttons_hidden = True  # Estado inicial de los botones
        self.arrow_button = QPushButton(">")
        self.arrow_button.clicked.connect(self.toggle_buttons_visibility)
        self.arrow_button.setStyleSheet("background: transparent; border: none;")
        right_buttons_layout.addWidget(self.arrow_button)

        # Seccion de Column
        column_layout = QHBoxLayout()
        self.column_label = QLabel("Columns")
        self.column_checkbox = QCheckBox()
        self.column_checkbox.setToolTip(
            "Toggle visibility of Folder Delete and Sequence columns"
        )
        self.column_checkbox.setChecked(False)
        self.column_checkbox.stateChanged.connect(self.toggle_columns)
        column_layout.addWidget(self.column_label)
        column_layout.addWidget(self.column_checkbox)
        self.column_frame = QFrame()
        self.column_frame.setLayout(column_layout)
        right_buttons_layout.addWidget(self.column_frame)
        self.column_frame.setVisible(False)

        # Seccion de Color
        color_layout = QHBoxLayout()
        self.color_label = QLabel("Color")
        self.color_checkbox = QCheckBox()
        self.color_checkbox.setToolTip("Toggle color-coded file paths")
        self.color_checkbox.setChecked(True)
        self.color_checkbox.stateChanged.connect(self.change_footage_text_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_checkbox)
        self.color_frame = QFrame()
        self.color_frame.setLayout(color_layout)
        right_buttons_layout.addWidget(self.color_frame)
        self.color_frame.setVisible(
            False
        )  # Solo hacemos invisible el frame, no los widgets internos

        # Seccion de Font Size
        font_size_layout = QHBoxLayout()
        self.font_size_label = QLabel("Font Size")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setToolTip("Adjust the font size of the table")
        self.font_size_spinbox.setRange(1, 30)
        self.font_size_spinbox.setValue(int(self.font_size))
        self.font_size_spinbox.valueChanged.connect(self.change_font_size)
        font_size_layout.addWidget(self.font_size_label)
        font_size_layout.addWidget(self.font_size_spinbox)
        self.font_size_frame = (
            QFrame()
        )  # Usar self para hacerlo un atributo de la instancia
        self.font_size_frame.setLayout(font_size_layout)
        right_buttons_layout.addWidget(self.font_size_frame)
        self.font_size_frame.setVisible(False)
        # right_buttons_layout.addSpacing(50)  # Agrega un espacio

        # Seccion de Folder Depth
        folder_depth_layout = QHBoxLayout()
        self.level_label = QLabel("Shot Folder Depth")
        self.level_spinbox = QSpinBox()
        self.level_spinbox.setToolTip(
            "Sets the number of folder levels to move up from the script's location to find the main shot folder"
        )
        self.level_spinbox.setRange(1, 10)
        self.level_spinbox.setValue(self.project_folder_depth)
        folder_depth_layout.addWidget(self.level_label)
        folder_depth_layout.addWidget(self.level_spinbox)
        self.folder_depth_frame = (
            QFrame()
        )  # Usar self para hacerlo un atributo de la instancia
        self.folder_depth_frame.setLayout(folder_depth_layout)
        self.folder_depth_frame.setVisible(False)
        right_buttons_layout.addWidget(self.folder_depth_frame)

        # Boton Rescan
        self.refresh_button = QPushButton("Rescan")
        self.refresh_button.setToolTip(
            "Rescan the project directory, refresh the data, and save the project depth as the new default"
        )
        self.refresh_button.clicked.connect(self.refresh_data)
        right_buttons_layout.addWidget(self.refresh_button)
        self.refresh_button.setVisible(False)
        right_buttons_layout.addSpacing(10)

        # Boton Refresh Window Size
        self.refresh_window_size_button = QPushButton("Resize")
        self.refresh_window_size_button.setToolTip(
            "Adjust the window size to fit the contents"
        )
        self.refresh_window_size_button.clicked.connect(self.adjust_window_size)
        right_buttons_layout.addWidget(self.refresh_window_size_button)
        self.refresh_window_size_button.setVisible(
            False
        )  # Asegurate de que el boton sea visible

        # Crear el layout principal que incluye todos los layouts de botones
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.addLayout(left_buttons_layout)
        main_buttons_layout.addSpacing(10)
        main_buttons_layout.addLayout(right_buttons_layout)
        main_buttons_layout.addStretch()

        # Agregar un espacio flexible para empujar el texto de la version hacia la derecha
        main_buttons_layout.addStretch(1)

        # Obtener la ruta del directorio del script actual
        script_dir = os.path.dirname(__file__)

        # Crear el boton 'Settings' con imagenes
        settings_off_path = os.path.join(script_dir, "icons", "settings_off.png")
        settings_on_path = os.path.join(script_dir, "icons", "settings_on.png")

        # Verificar si los archivos existen
        if not os.path.exists(settings_off_path):
            debug_print(f"settings_off.png no encontrado en {settings_off_path}")
        else:
            debug_print(f"settings_off.png encontrado en {settings_off_path}")

        if not os.path.exists(settings_on_path):
            debug_print(f"settings_on.png no encontrado en {settings_on_path}")
        else:
            debug_print(f"settings_on.png encontrado en {settings_on_path}")

        self.settings_button = QPushButton()
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.setFixedWidth(24)  # Ajusta el tamano al de la imagen
        self.settings_button.setFixedHeight(24)  # Ajusta el tamano al de la imagen
        self.settings_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Cargar imagenes y establecer iconos
        settings_off_icon = QIcon(settings_off_path)
        settings_on_icon = QIcon(settings_on_path)
        self.settings_button.setIcon(settings_off_icon)

        # Remover el estilo del boton para que solo se vea la imagen y evitar cambios al recibir el foco
        self.settings_button.setStyleSheet(
            """
            QPushButton { 
                border: none; 
                background-color: transparent;
            }
            QPushButton:focus {
                outline: none;
            }
        """
        )

        # Cambiar la imagen al hacer clic y quitar el foco del boton
        self.settings_button.pressed.connect(
            lambda: self.settings_button.setIcon(settings_on_icon)
        )
        self.settings_button.released.connect(
            lambda: [
                self.settings_button.setIcon(settings_off_icon),
                self.settings_button.clearFocus(),
            ]
        )

        self.settings_button.clicked.connect(self.show_settings_window)

        # Crear y configurar el QLabel para el texto de la version
        version_label = QLabel("v1.6  ")
        version_label.setToolTip("Lega | 2024")
        version_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )  # Alineacion a la derecha y verticalmente centrado

        # Agregar el QLabel al layout principal de botones
        main_buttons_layout.insertWidget(5, self.settings_button)
        main_buttons_layout.addWidget(version_label)

        # Agregar layout de botones al layout principal
        self.layout.addLayout(main_buttons_layout)

        # Crear la tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["File Path", "Read", "Status", "Folder_Delete", "Sequence"]
        )
        # self.table.setColumnHidden(1, True)
        # self.table.setColumnHidden(2, True)
        # self.table.horizontalHeader().setStretchLastSection(True) # Estira la ultima columna hasta la derecha de la ventana

        # Aplicar la configuracion inicial de visibilidad de columnas
        self.toggle_columns(self.column_checkbox.isChecked())

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        # Cambiar el color de fondo de la tabla, de la barra de seleccion y el tamano de la fuente
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: #282828;
                font-size: {self.font_size}pt; 
            }}
            QTableWidget::item:selected {{
                background-color: #FF0000;
            }}
        """
        )

        # Aplicar el delegado a cada columna
        delegate = TransparentTextDelegate(self.table)
        for column in range(self.table.columnCount()):
            self.table.setItemDelegateForColumn(column, delegate)

        self.setLayout(self.layout)
        self.scan_project()
        self.adjust_window_size()

    def toggle_buttons_visibility(self):
        self.are_buttons_hidden = not self.are_buttons_hidden
        # Alternar la visibilidad de los elementos
        self.column_frame.setVisible(not self.are_buttons_hidden)
        self.color_frame.setVisible(not self.are_buttons_hidden)
        self.font_size_frame.setVisible(not self.are_buttons_hidden)
        self.folder_depth_frame.setVisible(not self.are_buttons_hidden)
        self.refresh_button.setVisible(not self.are_buttons_hidden)
        self.refresh_window_size_button.setVisible(not self.are_buttons_hidden)

    def load_settings(self):
        config = configparser.ConfigParser()
        ini_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "LGA_mediaManagerSettings.ini"
        )
        debug_print(
            f"INI file path: {ini_path}"
        )  # Linea de depuracion para imprimir la ruta del INI

        if os.path.exists(ini_path):
            config.read(ini_path)

            # Cargar la configuracion de la profundidad del proyecto
            if "LGA_mediaManagerSettings" in config:
                self.project_folder_depth = config.getint(
                    "LGA_mediaManagerSettings", "project_folder_depth", fallback=3
                )
            else:
                self.project_folder_depth = 3

            # Cargar configuraciones de los botones de copia dinamicamente
            self.copy_options = []
            if "CopyOptions" in config:
                for key in config["CopyOptions"]:
                    if key.endswith("_button_text"):
                        # Obtener el indice del boton (ej. "1", "2", etc.)
                        index = key.split("_")[1]
                        button_text = config["CopyOptions"].get(key).strip('"')
                        subdirectory = (
                            config["CopyOptions"]
                            .get(f"copy_{index}_subdirectory")
                            .strip('"')
                        )
                        self.copy_options.append((button_text, subdirectory))
        else:
            self.project_folder_depth = 3
            self.copy_options = [
                ("&Input", "_input"),
                ("&Assets", "comp/0_assets"),
                ("&Prerenders", "comp/2_prerenders"),
            ]
        debug_print(
            f"Project folder depth loaded from INI: {self.project_folder_depth}"
        )  # Linea de depuracion

    def show_settings_window(self):
        # Cargar la configuracion del archivo .ini
        settings_data = {
            "Shot Folder depth": str(self.project_folder_depth),
        }
        for i, (button_text, subdirectory) in enumerate(self.copy_options, start=1):
            settings_data[f"copy_{i}_button_text"] = button_text
            settings_data[f"copy_{i}_subdirectory"] = subdirectory

        self.settings_window = SettingsWindow(settings_data, self)
        self.settings_window.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.settings_window.size(),
                QApplication.primaryScreen().availableGeometry(),
            )
        )
        self.settings_window.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def adjust_window_size(self):
        # Desactivar temporalmente el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana basado en el ancho de las columnas
        width = (
            self.table.verticalHeader().width() + 4
        )  # Con ajuste para evitar scroll horizontal
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i) + 4
        width += self.table.verticalScrollBar().width()

        # Calcular la altura basada en la altura de los headers y las filas
        height = self.table.horizontalHeader().height() + 4
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)
        height += self.table.horizontalScrollBar().height()

        # Agregar el alto del layout de botones al tamano de la ventana
        height += self.layout.itemAt(0).sizeHint().height()

        # Obtener la altura del monitor
        screen_height = QApplication.primaryScreen().geometry().height()

        # Establecer un limite para la altura, por ejemplo, el 80% de la altura del monitor
        max_height = screen_height * 0.8

        # Usar el menor entre la altura calculada y el maximo permitido
        final_height = min(height, max_height)

        # Reactivar el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamano de la ventana
        self.resize(width, final_height)

    def toggle_columns(self, state):

        is_visible = bool(state)
        self.table.setColumnHidden(3, not is_visible)  # Columna Folder_Delete
        self.table.setColumnHidden(4, not is_visible)  # Columna Sequence
        self.adjust_window_size()

    def refresh_data(self):
        # Guardar la configuracion actual en el .ini
        self.save_settings()

        # Guardar la configuracion actual de ordenacion
        current_sort_column = self.table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.table.horizontalHeader().sortIndicatorOrder()

        # Muestra la ventana de carga
        self.loading_window = LoadingWindow("Rescanning...", self)
        self.center_window(self.loading_window)
        self.loading_window.show()

        QApplication.processEvents()  # Actualiza la UI para mostrar el mensaje

        # Restablecer el orden de la tabla
        self.table.sortByColumn(
            -1, Qt.AscendingOrder
        )  # -1 significa no ordenar por ninguna columna

        # Limpia la tabla
        self.table.setRowCount(0)
        self.matched_reads = []

        # Usa el valor actual del level_spinbox para realizar la operacion
        project_path = nuke.root().name()
        if not project_path:
            nuke.message("Por favor guarda el script antes de ejecutar este script.")
            return

        project_folder = project_path
        for _ in range(self.level_spinbox.value()):  # Usar el valor del spinbox
            project_folder = os.path.dirname(project_folder)

        self.project_folder = project_folder  # Guardo la variable para obtenerla desde cualquier lado (add file to table)
        # self.find_files(project_folder)
        temp_worker = ScannerWorker(self)
        files_data = temp_worker.find_files(project_folder)
        self.search_unmatched_reads()
        self.adjust_window_size()

        # Aplicar el color del checkbox despues de actualizar la tabla
        self.change_footage_text_color(self.color_checkbox.isChecked())

        # Iniciar un temporizador para reordenar la tabla despues de que se haya completado la actualizacion
        QTimer.singleShot(
            10, lambda: self.table.sortByColumn(current_sort_column, current_sort_order)
        )
        # QTimer.singleShot(10, self.reorder_by_status)  # 500 milisegundos despues

        # Ocultar la ventana de carga
        self.loading_window.stop()

    def save_settings(self):
        config = configparser.ConfigParser()
        ini_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "LGA_mediaManagerSettings.ini"
        )
        config["LGA_mediaManagerSettings"] = {
            "project_folder_depth": self.level_spinbox.value()
        }
        with open(ini_path, "w") as configfile:
            config.write(configfile)
        debug_print(f"Settings saved to INI: {ini_path}")  # Linea de depuracion

    def reorder_by_status(self):
        status_column_index = (
            2  # Asegurate de que este es el indice correcto para la columna de Estado
        )
        self.table.sortByColumn(status_column_index, Qt.AscendingOrder)

    def change_font_size(self, value):
        self.font_size = value
        self.update_table_font_size()
        self.adjust_window_size()

    def update_table_font_size(self):
        for row in range(self.table.rowCount()):
            label = self.table.cellWidget(row, 0)
            if label:
                label.setStyleSheet(f"QLabel {{ font-size: {self.font_size}pt; }}")

    def on_level_change(self):
        # Limpia la tabla antes de una nueva busqueda
        self.table.setRowCount(0)
        self.matched_reads = []

        # Obtiene el nuevo nivel de directorio
        level = self.level_spinbox.value()

        # Encuentra los archivos con el nuevo nivel
        project_path = nuke.root().name()
        if not project_path:
            nuke.message("Por favor guarda el script antes de ejecutar este script.")
            return

        # Calcula el directorio del proyecto basado en el nivel especificado
        project_folder = project_path
        for _ in range(level):
            project_folder = os.path.dirname(project_folder)
        self.project_folder = project_folder  # Guardo la variable para obtenerla desde cualquier lado (add file to table)

        # Realiza las busquedas con el nivel ajustado
        # self.find_files(project_folder)
        temp_worker = ScannerWorker(self)
        files_data = temp_worker.find_files(project_folder)
        self.search_unmatched_reads()
        self.adjust_window_size()

        # Aplicar el color del checkbox despues de actualizar la tabla
        self.change_footage_text_color(self.color_checkbox.isChecked())

    def get_color_for_level(self, level):
        # Define los colores por nivel aqui
        colors = {
            0: "#ffff66",  # Amarillo           T
            1: "#28b5b5",  # Verde Cian         Proye
            2: "#ff9a8a",  # Naranja pastel     Grupo
            3: "#0088ff",  # Rojo coral         Shot
            4: "#ffd369",  # Amarillo mostaza
            5: "#28b5b5",  # Verde Cian
            6: "#ff9a8a",  # Naranja pastel
            7: "#6bc9ff",  # Celeste
            8: "#ffd369",  # Amarillo mostaza
            9: "#28b5b5",  # Verde Cian
            10: "#ff9a8a",  # Naranja pastel
            11: "#6bc9ff",  # Celeste
            # Anade mas colores si hay mas niveles
        }
        return colors.get(
            level, "#000000"
        )  # Color por defecto en caso de no encontrar el nivel

    def change_footage_text_color(self, state):
        # Cambia el color de los textos
        for row in range(self.table.rowCount()):
            label = self.table.cellWidget(row, 0)  # Obtener el QLabel
            if label:
                # Extraemos el texto sin etiquetas HTML para evitar duplicados
                original_text = re.sub(r"<[^>]*>", "", label.text())
                parts = (
                    original_text.lower().replace("\\", "/").split("/")
                )  # Normaliza a minusculas y reemplaza las barras

                if state:
                    project_folder_parts = (
                        self.project_folder.lower().replace("\\", "/").split("/")
                    )
                    colored_parts = []

                    # Aplica los colores a cada parte de la ruta si coincide
                    for i, part in enumerate(parts[:-1]):
                        if (
                            i < len(project_folder_parts)
                            and part == project_folder_parts[i]
                        ):
                            background_color = ""
                            text_color = "#c56cf0"  # Color personalizado
                        else:
                            background_color = ""
                            text_color = self.get_color_for_level(i)

                        colored_parts.append(
                            f"<span style='{background_color} color: {text_color};'>{part}</span>"
                        )

                    # El nombre del archivo permanece en blanco y negrita
                    file_name = f"<b style='color: rgb(200, 200, 200);'>{parts[-1]}</b>"
                    colored_parts.append(file_name)

                    colored_text = '<span style="color: white;">/</span>'.join(
                        colored_parts
                    )
                    label.setText(colored_text)
                else:
                    # Si el checkbox esta desmarcado, se muestra solo el nombre del archivo en negrita y blanco
                    file_name = f"<b style='color: white;'>{parts[-1]}</b>"
                    label.setText("/".join(parts[:-1]) + "/" + file_name)

                label.setTextFormat(
                    Qt.RichText
                )  # Habilitar texto enriquecido para mostrar colores

    def apply_color_to_label(self, label, project_folder, full_path):
        # Metodo para aplicar los colores solo a una fila (despues del copy)
        if label:
            parts = full_path.lower().replace("\\", "/").split("/")
            project_folder_parts = project_folder.lower().replace("\\", "/").split("/")
            colored_parts = []

            # Aplica los colores a cada parte de la ruta si coincide
            for i, part in enumerate(parts[:-1]):
                text_color = (
                    self.get_color_for_level(i)
                    if i >= len(project_folder_parts) or part != project_folder_parts[i]
                    else "#c56cf0"
                )
                colored_parts.append(
                    f"<span style='color: {text_color};'>{part}</span>"
                )

            # El nombre del archivo permanece en blanco y negrita
            file_name = f"<b style='color: rgb(200, 200, 200);'>{parts[-1]}</b>"
            colored_parts.append(file_name)

            colored_text = '<span style="color: white;">/</span>'.join(colored_parts)
            label.setText(colored_text)
            label.setTextFormat(
                Qt.RichText
            )  # Habilitar texto enriquecido para mostrar colores

    def center_window(self, child_window):
        # Tamano de la ventana principal
        main_window_width = self.size().width()
        main_window_height = self.size().height()

        # Tamano de la ventana del GIF
        child_window_width = child_window.size().width()
        child_window_height = child_window.size().height()

        # Calcula las nuevas coordenadas x y y
        new_x = (main_window_width - child_window_width) / 2
        new_y = (main_window_height - child_window_height) / 2

        # Establece la nueva posicion
        child_window.move(new_x, new_y)

    ##### Botones de la izq:
    def go_to_read(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            read_node_names = (
                selected_items[1].text().split(",")
            )  # Divide los nombres de los nodos Read
            read_node_names = [name.strip() for name in read_node_names]

            # Obtener los nodos Read actualmente seleccionados en Nuke
            selected_reads = [
                node.name() for node in nuke.selectedNodes() if node.Class() == "Read"
            ]

            # Encuentra el indice del nodo Read seleccionado que esta en la lista, si existe
            selected_index = None
            for selected_read in selected_reads:
                if selected_read in read_node_names:
                    selected_index = read_node_names.index(selected_read)
                    break

            # Determinar el siguiente nodo Read al que moverse
            if selected_index is not None:
                next_index = (selected_index + 1) % len(
                    read_node_names
                )  # Mover al siguiente, o volver al primero si es el ultimo
            else:
                next_index = 0  # No se encontro un nodo Read seleccionado que coincida, ir al primero de la lista

            # Busca el siguiente nodo en Nuke y lo selecciona en el Node Graph
            next_read_node_name = read_node_names[next_index]
            read_node = nuke.toNode(next_read_node_name)
            if read_node:
                # Asegurarse de que ningun otro nodo este seleccionado
                nuke.selectAll()
                nuke.invertSelection()
                # Selecciona y centra el nodo en el Node Graph
                read_node.setSelected(True)
                nuke.zoomToFitSelected()
                read_node.showControlPanel()

            else:
                # Manejar el caso en que el nombre no corresponda a un nodo existente
                debug_print(f"No se encontro el nodo Read: {next_read_node_name}")
                pass

    def reveal_selected(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            file_path = selected_items[
                0
            ].text()  # Obtiene el file_path de la fila seleccionada
            self.reveal_in_explorer(file_path)

    def reveal_in_explorer(self, file_path):
        directory = os.path.dirname(file_path)
        debug_print("Attempting to open folder: " + directory)
        if os.path.exists(directory):
            if sys.platform == "win32":
                os.startfile(directory)
            elif sys.platform == "darwin":
                os.system('open "' + directory + '"')
            # Anade la logica para otros sistemas operativos si es necesario
        else:
            debug_print("Path does not exist: " + directory)
            pass

    ##### Metodos para relinkear:
    def relink(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            status = selected_items[
                2
            ].text()  # Asumiendo que la columna de estado es la tercera
            if status == "Offline":
                directory = QFileDialog.getExistingDirectory(self, "Select Directory")
                if directory:
                    self.search_file_in_directory(directory, selected_items[0].text())
            else:
                QMessageBox.information(
                    self, "Information", "Relink is only available for Offline files."
                )

    def search_file_in_directory(self, directory, file_name):
        self.loading_window = LoadingWindow("Searching...", self)
        self.loading_window.show()
        QApplication.processEvents()
        first_frame = ""

        if "#" in file_name:
            # Extraer el primer numero del rango de cuadros
            frame_range = re.search(r"\[(\d+)-\d+\]", file_name)
            if frame_range:
                first_frame = frame_range.group(1)
                # Reemplazar '#' por el primer numero de cuadro y eliminar el rango de cuadros del nombre
                file_name_only = re.sub(
                    r"#+", first_frame, os.path.basename(file_name).split("[")[0]
                ).lower()
            else:
                file_name_only = os.path.basename(file_name).split("[")[0].lower()
        else:
            file_name_only = os.path.basename(file_name).lower()

        nuke.executeInMainThread(
            lambda: self.logger.debug(
                f"\nBuscando el archivo: {file_name_only} en {directory}"
            )
        )

        for root, dirs, files in os.walk(directory):
            if "$RECYCLE.BIN" in [
                os.path.basename(dir)
                for dir in os.path.normpath(root).split(os.path.sep)
            ]:
                nuke.executeInMainThread(lambda: self.logger.debug(f"Skipping {root}"))
                continue

            for file in files:
                if file.lower() == file_name_only:
                    new_file_path = os.path.join(root, file)
                    nuke.executeInMainThread(
                        lambda: self.logger.debug(
                            f"Archivo encontrado: {new_file_path}"
                        )
                    )
                    self.update_read_node(file_name, new_file_path, first_frame)
                    self.loading_window.close()
                    return

        self.loading_window.close()
        QMessageBox.information(self, "Information", "File not found.")

    def update_read_node(self, original_file_name, new_file_path, first_frame):
        # Normalizar las barras en la ruta del archivo
        new_file_path = new_file_path.replace("\\", "/")

        # Buscar el nodo Read asociado al archivo original en la tabla y actualizar
        for row in range(self.table.rowCount()):
            table_file_name = self.table.item(row, 0).text()
            if (
                table_file_name == original_file_name
                or table_file_name in original_file_name
            ):
                node_name = self.table.item(row, 1).text()
                node = nuke.toNode(node_name)
                if node:
                    # Construir la nueva ruta para el nodo
                    new_file_path_for_node = os.path.join(
                        os.path.dirname(new_file_path),
                        os.path.basename(node["file"].getValue()),
                    ).replace("\\", "/")

                    # Seleccionar y actualizar el nodo en Nuke
                    nuke.selectAll()
                    nuke.invertSelection()
                    node.setSelected(True)
                    nuke.zoomToFitSelected()
                    node["file"].setValue(new_file_path_for_node)
                    node.showControlPanel()

                    # Actualizar la ruta en la tabla manteniendo el nombre de archivo
                    new_table_path = os.path.join(
                        os.path.dirname(new_file_path),
                        os.path.basename(table_file_name),
                    ).replace("\\", "/")
                    self.table.item(row, 0).setText(new_table_path)

                    # Actualizar QLabel
                    label = self.table.cellWidget(row, 0)
                    if label:
                        label.setText(new_table_path)
                        self.apply_color_to_label(
                            label, self.project_folder, new_table_path
                        )

                    # Actualizar el estado y el color de fondo
                    status_item = self.table.item(row, 2)

                    # Verificar si la nueva ruta esta dentro de la carpeta del proyecto
                    if (
                        os.path.commonprefix([self.project_folder, new_file_path])
                        == self.project_folder
                    ):
                        # Actualizar el estado a "OK" y cambiar el color correspondiente
                        self.table.item(row, 2).setBackground(QColor("#25321e"))
                        self.table.item(row, 2).setText("OK")

                    else:
                        # Actualizar el estado a "Outside" y cambiar el color correspondiente
                        self.table.item(row, 2).setBackground(QColor("#321e1e"))
                        self.table.item(row, 2).setText("Outside")

                    break

    ##### Buesqueda de archivos:
    def search_unmatched_reads(self):
        # Realiza una busqueda adicional en los nodos Read que no tuvieron match
        # logging.info("--------------- search_unmatched_reads ----------------")
        end_time = time.time()
        # logging.info("")
        # logging.info("unmatched_reads execution time start: ", end_time - start_time, "seconds")
        all_read_files = self.get_read_files()
        # logging.info(self.matched_reads)
        to_add = []  # Lista para acumular los datos
        secuencia = False

        for read_path, nodes in all_read_files.items():
            read_path = os.path.normpath(read_path)
            unmatched_nodes = [node for node in nodes if node not in self.matched_reads]
            if unmatched_nodes:
                is_sequence = (
                    "%" in read_path or "#" in read_path
                )  # Detecta si es una secuencia por '%' o '#'
                # logging.info(f"is_sequence: {is_sequence}")
                directory = os.path.dirname(read_path)
                # logging.info(f"directory: {directory}")
                # logging.info(f"read_path: {read_path}")
                # logging.info("")

                # Define valores predeterminados para frame_range y is_folder_deletable
                frame_range = ""
                is_folder_deletable = False
                secuencia = is_sequence

                if is_sequence:
                    secuencia = True
                    if os.path.exists(directory):  # Verifica si la carpeta existe
                        # Si es una secuencia y contiene '%', reemplazamos por un patron de busqueda con digitos
                        suffix = ""  # Inicializa un sufijo vacio
                        file_pattern = None  # Inicializa el patron de expresion regular

                        if "%" in read_path:
                            hashes = "#" * read_path.count("%0d")
                            file_pattern = re.compile(
                                os.path.basename(read_path)
                                .replace("%0d", r"(\d+)(.*)")
                                .replace("%04d", r"(\d{4})(.*)")
                                .replace("%03d", r"(\d{3})(.*)")
                            )
                            # logging.info(f"file_pattern %: {file_pattern}")
                        elif "#" in read_path:
                            # Si es una secuencia y ya tiene '#', usamos esos directamente en el patron de busqueda
                            hashes = "#" * read_path.count("#")
                            file_pattern = re.compile(
                                os.path.basename(read_path).replace(
                                    hashes, r"(\d{" + str(len(hashes)) + "})(.*)"
                                )
                            )
                            # logging.info(f"file_pattern #: {file_pattern}")
                        else:
                            is_sequence = False
                            hashes = ""

                        frame_numbers = []
                        if file_pattern:
                            for filename in os.listdir(directory):
                                m = file_pattern.match(filename)
                                if m:
                                    frame_numbers.append(int(m.group(1)))
                        # logging.info(f"frame_numbers: {frame_numbers}")

                        if frame_numbers:
                            frame_range = f"[{min(frame_numbers)}-{max(frame_numbers)}]"
                            # No necesitamos reemplazar los '#' si ya estaban en la ruta
                            if "%" in read_path:
                                is_sequence = True
                                # Reemplaza los especificadores de formato por la cantidad correcta de '#'
                                read_path = (
                                    re.sub(
                                        r"%0(\d+)d",
                                        lambda m: "#" * int(m.group(1)),
                                        read_path,
                                    )
                                    + suffix
                                )
                            elif "#" in read_path:
                                is_sequence = True
                                read_path = read_path + suffix
                                # No es necesario hacer ningun reemplazo, los '#' ya estan presentes
                            else:
                                is_sequence = False
                            # read_path = read_path if '#' in read_path else read_path.replace('%0d', hashes).replace('%04d', hashes).replace('%03d', hashes)
                            # logging.info(f"read_path: {read_path}")
                            is_folder_deletable = len(frame_numbers) == (
                                max(frame_numbers) - min(frame_numbers) + 1
                            ) and len(os.listdir(directory)) == len(frame_numbers)

                        else:
                            # Aqui, debes asegurarte de que 'nodes' no este vacio y luego obtener el nombre del nodo
                            if nodes:
                                read_node_name = nodes[
                                    0
                                ]  # Tomando el primer nodo como ejemplo
                                read_node = nuke.toNode(read_node_name)
                                if read_node:
                                    # Toma los valores originales del nodo Read
                                    orig_first = int(read_node["origfirst"].getValue())
                                    orig_last = int(read_node["origlast"].getValue())
                                    frame_range = f"[{orig_first}-{orig_last}]"
                                else:
                                    # En caso de que no haya informacion disponible, deja un rango predeterminado
                                    frame_range = "[1001-1001]"
                            else:
                                # Manejar el caso donde 'nodes' esta vacio
                                frame_range = "[1001-1001]"
                            is_folder_deletable = False

                    else:
                        if nodes:
                            read_node_name = nodes[
                                0
                            ]  # Tomando el primer nodo como ejemplo
                            read_node = nuke.toNode(read_node_name)
                            if read_node:
                                # Toma los valores originales del nodo Read
                                orig_first = int(read_node["origfirst"].getValue())
                                orig_last = int(read_node["origlast"].getValue())
                                frame_range = f"[{orig_first}-{orig_last}]"
                            else:
                                # En caso de que no haya informacion disponible, deja un rango predeterminado
                                frame_range = "[1001-1001]"
                        else:
                            # Manejar el caso donde 'nodes' esta vacio
                            frame_range = "[1001-1001]"
                        is_folder_deletable = False

                else:
                    # Para archivos que no son secuencias
                    if not os.path.exists(directory):  # Verifica si la carpeta existe
                        # logging.info("no existe no seq")
                        pass
                    else:
                        frame_range = ""
                        is_folder_deletable = False

                # Para archivos no secuenciales, agregarlos directamente con is_sequence=False
                for node in unmatched_nodes:
                    to_add.append(
                        (
                            read_path,
                            {read_path: [node]},
                            is_sequence,
                            frame_range,
                            True,
                            is_folder_deletable,
                            secuencia,
                        )
                    )

        end_time = time.time()
        # logging.info("unmatched_reads execution time end: ", end_time - start_time, "seconds")
        return to_add  # En lugar de llamar a add_file_to_table, devuelve los datos
        self.adjust_window_size()

    def get_read_files(self):
        read_files = {}
        node_types = ["Read", "AudioRead", "ReadGeo", "DeepRead"]

        for node_type in node_types:
            nodes = nuke.executeInMainThreadWithResult(lambda: nuke.allNodes(node_type))
            for node in nodes:
                file_path = node["file"].getValue().replace("\\", "/")
                if file_path not in read_files:
                    read_files[file_path] = []
                read_files[file_path].append(node.name())

        return read_files

    def scan_project(self):
        # Esta función ahora solo configura el worker y lo inicia
        project_path = nuke.root().name()
        if not project_path:
            nuke.message("Por favor guarda el script antes de ejecutar este script.")
            return

        project_folder = project_path
        for _ in range(self.project_folder_depth):
            project_folder = os.path.dirname(project_folder)
        self.project_folder = (
            project_folder  # Guardo la variable para obtenerla desde cualquier lado
        )

        # El escaneo real se realizará en el worker
        scanner_worker = ScannerWorker(self)  # Solo pasamos la instancia de FileScanner

        # Conectar señales
        scanner_worker.signals.files_found.connect(self.on_files_found)
        scanner_worker.signals.finished.connect(
            lambda: [
                self.table.resizeColumnsToContents(),
                self.adjust_window_size(),
                self.change_footage_text_color(True),
                self.reorder_by_status(),
            ]
        )

        # Iniciar el escaneo en segundo plano
        QThreadPool.globalInstance().start(scanner_worker)

    def on_files_found(self, data):
        files_data, unmatched_reads_data = data
        self.add_file_to_table(files_data)
        self.add_file_to_table(unmatched_reads_data)

    def add_file_to_table(self, files_data):
        # Agrega los archivos a la tabla y determina su estado en relacion con los nodos Read
        end_time = time.time()
        # logging.info("")
        # logging.info("add_file_to_table execution time start: ", end_time - start_time, "seconds")

        for file_data in files_data:
            (
                file_path,
                read_files,
                is_sequence,
                frame_range,
                is_unmatched_read,
                is_folder_deletable,
                sequence_state,
            ) = file_data
            read_node_name = next(iter(read_files.values()))[0]
            row_position = self.table.rowCount()

            debug_print("")
            debug_print(f"File path: {file_path}")
            debug_print(f"read_files: {read_files}")
            debug_print(f"Is sequence: {is_sequence}")
            debug_print(f"Frame range: {frame_range}")
            debug_print(f"Is unmatched read: {is_unmatched_read}")
            debug_print(f"Is folder deletable: {is_folder_deletable}")
            debug_print(f"sequence_state: {sequence_state}")

            # Encuentra el patron de digitos en el nombre del archivo y reemplazalo con '#'
            if is_unmatched_read:
                match = re.search(r"%0(\d+)d", file_path)
                if match:
                    digits = int(match.group(1))
                    file_path = re.sub(r"%0\d+d", "#" * digits, file_path)
                # Convertir %0Xd a # en las claves de read_files
                normalized_read_files = {}
                for path, nodes in read_files.items():
                    new_key = re.sub(r"%0(\d+)d", lambda m: "#" * int(m.group(1)), path)
                    normalized_read_files[new_key] = nodes

            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # Normalizacion del path y adicion a la tabla
            normalized_file_path = file_path.replace("\\", "/").lower()
            casi_file_path = file_path.replace(
                "\\", "/"
            )  # Se mantiene para visualizacion en la UI
            file_item = QTableWidgetItem(
                normalized_file_path + (frame_range if is_sequence else "")
            )
            file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)

            # Usar casi_file_path para el item que se mostrara en la tabla
            casi_file_item = QTableWidgetItem(
                casi_file_path + (frame_range if is_sequence else "")
            )
            casi_file_item.setFlags(casi_file_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 0, casi_file_item)

            # Usar casi_file_path para el item que se mostrara en la tabla
            label_file_item = QTableWidgetItem(
                casi_file_path + (frame_range if is_sequence else "")
            )
            label_file_item.setFlags(label_file_item.flags() & ~Qt.ItemIsEditable)

            # Preparar el texto para el QLabel
            display_text = casi_file_path + (frame_range if is_sequence else "")

            # Crear QLabel y establecer el texto
            label = QLabel(display_text)
            label.setTextFormat(Qt.RichText)  # Habilitar texto enriquecido
            label.setStyleSheet(
                f"color: rgb(200, 200, 200); font-size: {self.font_size}pt;"
            )
            self.table.setCellWidget(row_position, 0, label)

            if not is_unmatched_read:
                # Manejo de los archivos del find_files
                status = "-"
                state = "Unused"
                normalized_read_files = {
                    path.replace("\\", "/").lower(): nodes
                    for path, nodes in read_files.items()
                }
                status_color = "#32311e"

                if is_sequence:
                    for read_path, nodes in normalized_read_files.items():
                        if self.is_sequence_match(
                            normalized_file_path, read_path, frame_range
                        ):
                            status = ", ".join(nodes)
                            state = "OK"
                            status_color = "#25321e"
                            self.matched_reads.extend(nodes)
                            break
                else:
                    for read_path, nodes in normalized_read_files.items():
                        if normalized_file_path == read_path:
                            status = ", ".join(nodes)
                            state = "OK"
                            status_color = "#25321e"
                            self.matched_reads.extend(nodes)
                            break

                # Ajustar y establecer el valor para la columna "Read"
                read_item = QTableWidgetItem(status)
                read_item.setTextAlignment(Qt.AlignCenter)  # Centra el texto
                self.table.setItem(row_position, 1, read_item)

                # Establecer y Agregar el estado a la columna "Status"
                status_item = QTableWidgetItem(state)
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_position, 2, status_item)

            else:
                # Manejo de los archivos del unmatched_reads
                # print("")
                # print("en unmatche read")
                # print(f"file_path: {file_path}")
                # print(f"normalized_read_files: {normalized_read_files}")

                if (
                    file_path in normalized_read_files
                ):  # esta al pedo, deberia dar siempre verdadero
                    # print(f"normalized_read_files[file_path]: {normalized_read_files[file_path]}")

                    if is_sequence:
                        # Asignar el primer numero de frame si es una secuencia
                        num_hashes = file_path.count("#")
                        if frame_range:
                            first_frame = (
                                frame_range.split("-")[0]
                                .replace("[", "")
                                .zfill(num_hashes)
                            )
                            check_path = file_path.replace(
                                "#" * num_hashes, first_frame
                            )
                            # print(f"check_path: {check_path}")
                        else:
                            # Si no hay frame_range, no se puede verificar
                            check_path = None
                    else:
                        # Para archivos no secuencia, usar el path tal como esta
                        check_path = file_path

                    is_offline = not os.path.exists(check_path) if check_path else True

                    if is_offline:
                        read_item = QTableWidgetItem(
                            ", ".join(normalized_read_files[file_path])
                        )
                        read_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_position, 1, read_item)
                        self.table.setItem(row_position, 2, QTableWidgetItem("Offline"))
                        state = "Offline"
                        status_color = "#621e1e"
                    else:
                        # Verificar si el archivo esta dentro del directorio del shot
                        file_directory = os.path.dirname(os.path.normpath(file_path))
                        normi_file_directory = file_directory.replace("\\", "/").lower()
                        # print(f"normi_file_directory: {normi_file_directory}")

                        # Normalizar self.project_folder
                        normi_project_folder = self.project_folder.replace(
                            "\\", "/"
                        ).lower()
                        # print(f"normi_project_folder: {normi_project_folder}")

                        # Calcular el commonpath con rutas normalizadas y imprimirlo
                        try:
                            common_path = os.path.commonpath(
                                [normi_file_directory, normi_project_folder]
                            )
                        except ValueError:
                            # print("Las rutas estan en unidades de disco diferentes, no se puede encontrar un path comun.")
                            common_path = ""

                        common_path_normi = common_path.replace("\\", "/").lower()
                        # print(f"common_path_normi: {common_path_normi}")

                        if common_path_normi == normi_project_folder:
                            # Construir el full_file_path con frame range si es necesario y normalizar
                            full_file_path = (
                                (casi_file_path + (frame_range if is_sequence else ""))
                                .lower()
                                .replace("/", "\\")
                            )
                            read_item = QTableWidgetItem(
                                ", ".join(normalized_read_files[file_path])
                            )
                            read_item.setTextAlignment(Qt.AlignCenter)
                            self.table.setItem(row_position, 1, read_item)
                            self.table.setItem(row_position, 2, QTableWidgetItem("OK"))
                            state = "OK"
                            status_color = "#25321e"
                            self.matched_reads.extend(nodes)

                        else:
                            # read_item = QTableWidgetItem(', '.join(read_files.get(file_path, [])))
                            # print(f"file_path no esta en read_files: {file_path}")
                            read_item = QTableWidgetItem(
                                ", ".join(normalized_read_files[file_path])
                            )
                            read_item.setTextAlignment(Qt.AlignCenter)
                            self.table.setItem(row_position, 1, read_item)
                            self.table.setItem(
                                row_position, 2, QTableWidgetItem("Outside")
                            )
                            state = "Outside"
                            status_color = "#321e1e"

                else:
                    # Si file_path no esta en read_files, asumir que el archivo esta Offline (no deberia pasar nunca!)
                    print(
                        "if file_path in read_files da que ELSE (esto no deberia pasar nunca!!!!!!!!!!!!!!!!!!!!!!!)"
                    )
                    # print(f"file_path: {file_path}")
                    # print(f"is_offline: {is_offline}")
                    pass

            # Agregar el valor de is_folder_deletable a la cuarta columna
            folder_delete_item = QTableWidgetItem(str(is_folder_deletable))
            folder_delete_item.setTextAlignment(Qt.AlignCenter)
            folder_delete_item.setFlags(folder_delete_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 3, folder_delete_item)
            # Insertar el estado de la secuencia
            sequence_item = QTableWidgetItem(str(sequence_state))
            sequence_item.setTextAlignment(Qt.AlignCenter)
            sequence_item.setFlags(sequence_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(
                row_position, 4, sequence_item
            )  # Asumiendo que la nueva columna es la 5ta (indice 4)

            # Agregar el estado a la tabla
            status_item = QTableWidgetItem(state)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 2, status_item)

            # Aplicar el color de fondo solo a la celda del estado
            status_item.setBackground(QColor(status_color))

        self.remove_duplicates()

        end_time = time.time()
        # print("add_file_to_table execution time end: ", end_time - start_time, "seconds")

    def remove_duplicates(self):
        paths = {}  # Diccionario para almacenar los paths y sus indices de fila
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                file_path = self.table.item(row, 0).text().lower().replace("/", "\\")
                file_path = os.path.normpath(file_path)
                status = self.table.item(row, 2).text()
                if file_path in paths and status != "OK":
                    # Si el path esta duplicado y el estado actual no es "OK", eliminar la fila
                    self.table.removeRow(row)
                elif (
                    file_path in paths
                    and self.table.item(paths[file_path], 2).text() != "OK"
                ):
                    # Si el path esta duplicado y el estado del path previamente almacenado no es "OK", eliminar la fila previa
                    self.table.removeRow(paths[file_path])
                    paths[file_path] = (
                        row  # Actualizar el indice con la fila actual porque la anterior fue eliminada
                    )
                else:
                    paths[file_path] = row  # Almacenar el indice de la fila
            else:
                pass

    def is_sequence_match(self, sequence_path, read_path, frame_range):
        # Verifica si la secuencia de archivos coincide con algun archivo en los nodos Read
        # Ajustamos el proceso de coincidencia para secuencias
        sequence_base_path = re.sub(r"#+", "", sequence_path.split("[")[0])
        read_base_path = re.sub(r"%\d+d", "", read_path)
        # Se compara sin tener en cuenta mayusculas o minusculas y los separadores de ruta
        return sequence_base_path.lower() == read_base_path.lower()

    def normalize_sequence_path(self, file_path):
        # Normaliza la ruta del archivo para secuencias, reemplazando los digitos al final por '#'
        directory, filename = os.path.split(file_path)
        base, ext = os.path.splitext(filename)
        if any(ext.lower() == e for e in self.sequence_extensions):
            base = re.sub(r"\d+$", lambda m: "#" * len(m.group()), base)
        return os.path.join(directory, base + ext).replace("\\", "/").lower()

    def normalize_sequence_path_for_comparison(self, file_path):
        # Normalizar el file_path, quitando el rango de cuadros si esta presente
        # Aqui asumimos que el rango de cuadros siempre sigue el formato "[####-####]"
        # print("--------------- normalize_sequence_path_for_comparison ----------------")
        # print(f"file_path: '{file_path}'")
        file_path_without_frames = re.sub(r"\[\d+-\d+\]", "", file_path).rstrip()
        # print(f"file_path_without_frames: '{file_path_without_frames}'")
        return self.normalize_sequence_path(file_path_without_frames)

    def expand_frame_range(self, file_path_pattern, frame_range):
        # print("--------------- expand_frame_range ----------------")
        start_frame, end_frame = map(int, frame_range.strip("[]").split("-"))
        # Dividimos el patron en la base del nombre del archivo y la extension
        base_pattern, file_ext = os.path.splitext(file_path_pattern)
        # print(f"base_pattern: '{base_pattern}'")
        # print(f"file_ext: '{file_ext}'")
        # Aseguramos de eliminar los '####' de la base, no de la extension
        base_pattern = base_pattern.replace("####", "")
        # print(f"base_pattern: '{base_pattern}'")
        # Generamos cada nombre de archivo reemplazando los '####' con el numero de cuadro correspondiente
        return [
            f"{base_pattern}{str(i).zfill(4)}{file_ext}"
            for i in range(start_frame, end_frame + 1)
        ]

    ##### Borrado:
    def delete_selected(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        rows_to_delete = set()  # Usar un conjunto para evitar duplicados
        files_to_delete = []  # Almacena los archivos que se van a borrar

        # Primera fase: Verificacion y confirmaciones
        for item in selected_items:
            row = self.table.row(item)

            # Verificar si la fila ya ha sido procesada
            if row in rows_to_delete:
                continue

            file_path = self.table.item(
                row, 0
            ).text()  # Obtiene el file_path de la fila seleccionada
            status = self.table.item(
                row, 2
            ).text()  # Obtiene el estado del archivo seleccionado
            read_node_name = self.table.item(
                row, 1
            ).text()  # Obtiene el nombre del nodo Read de la fila seleccionada

            # Verifica si el estado es 'Offline'
            if status == "Offline":
                QMessageBox.warning(
                    self, "Cannot Delete", "Cannot delete an offline file."
                )
                return  # Si algun archivo esta "Offline", cancelar la operacion completa

            # Mostrar un mensaje de advertencia si el archivo esta siendo usado por un nodo Read
            if read_node_name != "-" and len(rows_to_delete) == 0:
                read_warning_msg = QMessageBox(self)
                read_warning_msg.setIcon(QMessageBox.Warning)
                read_warning_msg.setWindowTitle("File in Use")
                read_warning_msg.setText(
                    f"The file {file_path} is being used by a Read node in Nuke."
                )
                read_warning_msg.setInformativeText(
                    "Are you sure you want to delete it?"
                )
                read_warning_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                read_warning_msg.setDefaultButton(QMessageBox.No)
                read_reply = read_warning_msg.exec_()

                if read_reply == QMessageBox.No:
                    return  # Cancelar la operacion de borrado si el usuario no confirma

            # Agregar la fila al conjunto de filas a borrar
            rows_to_delete.add(row)
            files_to_delete.append((file_path, row))

        multiple_delete = len(rows_to_delete) > 1

        total_files_to_delete = self.calculate_total_files_to_delete(files_to_delete)

        # Confirmacion de borrado basado en el tipo y cantidad de archivos
        if multiple_delete:
            print("muchas fila")
            # Confirmacion para multiples filas (usando el calculo total de archivos)
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Confirm delete")
            msgBox.setText(
                f"Are you sure you want to delete <font color='white'>{total_files_to_delete} files</font>?"
            )
            # msgBox.setInformativeText(f"<i>{file_path}</i>")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            reply = msgBox.exec_()
            if reply != QMessageBox.Yes:
                return  # Si el usuario cancela, no se borra nada
        else:
            print("1 fila")
            # Confirmacion para una sola fila (archivo unico o secuencia)
            file_path = files_to_delete[0][0]
            sequence_status = self.table.item(
                files_to_delete[0][1], 4
            ).text()  # Usando el indice 4 directamente

            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Confirm delete")

            if sequence_status.lower() == "true":
                # Si es una secuencia, mostrar el numero total de archivos en la secuencia
                msgBox.setText(
                    f"Are you sure you want to delete the <font color='white'>{total_files_to_delete} files</font> in the sequence?"
                )
            else:
                # Si es un solo archivo, mensaje estandar
                msgBox.setText(
                    f"Are you sure you want to send to trash <font color='white'>1 file</font>?"
                )

            msgBox.setInformativeText(f"<i>{file_path}</i>")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            reply = msgBox.exec_()
            if reply != QMessageBox.Yes:
                return  # Si el usuario cancela, no proceder con el borrado

        # Segunda fase: Borrado de archivos
        self.show_delete_window(total_files_to_delete)
        QApplication.processEvents()  # Asegura que la ventana de borrado se muestre antes de proceder
        # Usamos un QTimer de una sola vez para introducir una pequena pausa
        QTimer.singleShot(50, lambda: None)  # Pausa de 50 milisegundos

        # Evitar procesar filas duplicadas durante el borrado
        for file_path, row in set(files_to_delete):
            delete_thread = DeleteThread(file_path, self)
            delete_thread.start()
            delete_thread.wait()  # Esperar a que el hilo termine antes de proceder

        # Tercera fase: Actualizacion de la GUI
        for row in sorted(rows_to_delete, reverse=True):
            self.table.removeRow(row)

        self.close_delete_window()

    def calculate_total_files_to_delete(self, files_to_delete):
        total_files = 0
        processed_rows = set()  # Para evitar procesar la misma fila mas de una vez

        # Imprimir el contenido de files_to_delete
        debug_print("Contenido de files_to_delete:")
        for file_path, row in files_to_delete:
            debug_print(f"  - file_path: {file_path}, row: {row}")

        for file_path, row in files_to_delete:
            if row in processed_rows:
                continue  # Si ya procesamos esta fila, la saltamos

            # Agregar la fila al conjunto de filas procesadas
            processed_rows.add(row)

            # Obtener el texto del file_path directamente desde la tabla
            file_path_text = self.table.item(row, 0).text()  # Columna "File Path"
            sequence_status = self.table.item(row, 4).text()  # Columna "Sequence"

            # Imprimir los valores para depuracion
            debug_print(f"Fila {row}:")
            debug_print(f"  - File Path: {file_path_text}")
            debug_print(f"  - Sequence Status: {sequence_status}")

            # Verificar si es una secuencia buscando el rango en el file_path_text
            frame_range_match = re.search(r"\[(\d+)-(\d+)\]", file_path_text)
            if frame_range_match:
                start_frame, end_frame = map(int, frame_range_match.groups())
                total_files += end_frame - start_frame + 1
                debug_print(
                    f"  - Secuencia detectada: {end_frame - start_frame + 1} archivos"
                )
            else:
                # Si no es una secuencia, contar como un solo archivo
                total_files += 1
                debug_print("  - Archivo unico detectado")

        debug_print(f"Total de archivos a borrar: {total_files}")
        return total_files

    def show_delete_window(self, total_files_to_delete):
        self.delete_window = QWidget(self)
        self.delete_window.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        )
        self.delete_window.setStyleSheet(
            "background-color: #333; color: white; font-weight: bold;"
        )

        # Definir el mensaje basado en el numero de archivos a borrar
        if total_files_to_delete == 1:
            message = "Deleting..."
        elif 2 <= total_files_to_delete <= 200:
            message = (
                f"Deleting {total_files_to_delete} files.<br><br>"
                "<span style='color: #CCCCCC;'>Please wait...</span>"
            )
        elif 201 <= total_files_to_delete <= 500:
            message = (
                f"Deleting {total_files_to_delete} files.<br><br>"
                "<span style='color: #CCCCCC;'>"
                "The Nuke GUI may become unresponsive or freeze.<br>"
                "It will return once the deletion is complete.<br>"
                "Please wait..."
                "</span>"
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
        layout = QVBoxLayout(self.delete_window)
        layout.setContentsMargins(
            20, 30, 20, 30
        )  # Margenes: izquierda, arriba, derecha, abajo

        # Crear QLabel con el mensaje
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setTextFormat(
            Qt.RichText
        )  # Habilitar HTML para cambiar el color del texto
        layout.addWidget(label)

        # Calcular el numero de lineas de texto
        lines_of_text = (
            message.count("<br>") + 1
        )  # Cuenta los <br> y suma 1 para considerar todas las lineas

        # Ajusta la altura de la ventana en funcion del numero de lineas
        additional_height = 40 + (
            lines_of_text * 10
        )  # Ajusta 10 pixeles adicionales por linea

        # Calcular el tamano de la ventana segun el texto
        label.adjustSize()
        self.delete_window.resize(
            label.sizeHint().width() + 100,
            label.sizeHint().height() + additional_height,
        )

        # Centramos la ventana usando el metodo ya existente
        self.center_window(self.delete_window)

        # Mostrar la ventana
        self.delete_window.show()

    def close_delete_window(self):
        if hasattr(self, "delete_window"):
            self.delete_window.close()
            del self.delete_window

    def on_delete_finished(self):
        # Se llama cuando el hilo de eliminacion termina
        self.loading_window.stop()  # Cerrar la ventana de carga

    def deleteTableRow(self, row):
        self.table.removeRow(row)  # Elimina la fila en el hilo principal

    def print_debug_info(self, file_path):
        # print(f"Normalized requested to delete: '{file_path}'", f"Length: {len(file_path)}")
        for row in range(self.table.rowCount()):
            table_file_path = self.table.item(row, 0).text().replace("\\", "/").lower()

    def _confirm_and_delete(self, file_path):
        # Crear un QMessageBox personalizado para confirmar la eliminacion
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Confirm delete")
        msgBox.setText(f"Are you sure you want to delete {file_path}?")
        msgBox.setInformativeText(
            "<b><font color='#f67d7d'>Warning:</font></b> <font color='#cce56c'>This will permanently delete the file(s) without sending them to the recycle bin.</font>"
        )
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)

        reply = (
            msgBox.exec_()
        )  # Mostrar el QMessageBox y esperar la respuesta del usuario

        if reply == QMessageBox.Yes:
            self.loading_window = LoadingWindow("Deleting...", self)
            self.center_window(self.loading_window)
            self.loading_window.show()

            # Iniciar el hilo de eliminacion
            self.delete_thread = DeleteThread(file_path, self)
            self.delete_thread.deleteRow.connect(self.deleteTableRow)
            self.delete_thread.finished.connect(self.on_delete_finished)
            self.delete_thread.start()
        else:
            print("Deletion cancelled.")

    ##### Copia:
    def copy_to(self, subdirectory):
        selected_items = self.table.selectedItems()
        if selected_items:
            source_file_path = selected_items[0].text()

            # Obtener el estado del archivo seleccionado
            status = selected_items[2].text()

            # Permitir la copia solo si el estado es 'Outside'
            if status != "Outside":
                QMessageBox.warning(
                    self,
                    "Copy Not Allowed",
                    "The copy operation is limited to 'Outside' files",
                )
                return  # Sale del metodo si el archivo no tiene estado 'Outside'

            # Obtener el nombre del nodo Read de la fila seleccionada
            read_node_name = selected_items[1].text()

            # Verificar si el footage pertenece a algun Read
            if read_node_name != "-":
                self.current_read_node_name = read_node_name
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"\n  El footage pertenece al nodo Read: {self.current_read_node_name}"
                    )
                )
            else:
                self.current_read_node_name = None
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        "\n  El footage no pertenece a ningun nodo Read."
                    )
                )

            level = self.level_spinbox.value()
            project_path = nuke.root().name()
            project_folder = project_path
            for _ in range(level):
                project_folder = os.path.dirname(project_folder)

            # Determina la ruta de destino basada en la opcion seleccionada
            dest_folder = os.path.join(project_folder, subdirectory)

            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)

            self.loading_window = LoadingWindow("Copying...", self)
            self.center_window(self.loading_window)
            self.loading_window.show()

            self.copy_thread = CopyThread(source_file_path, dest_folder)
            self.copy_thread.finishedCopying.connect(self.on_copy_finished)
            self.copy_thread.finishedCopyingUnico.connect(self.on_copy_finished_unico)
            self.copy_thread.errorOccurred.connect(self.show_simple_message)
            self.copy_thread.confirmationNeeded.connect(self.show_confirmation_dialog)
            self.copy_thread.confirmationNeededUnico.connect(
                self.show_confirmation_dialog_unico
            )
            self.copy_thread.copyCancelled.connect(self.on_copy_cancelled)
            self.copy_thread.copyCancelledUnico.connect(self.on_copy_finished_unico)
            self.copy_thread.copyCancelledUnico.connect(self.on_copy_cancelled_unico)

            self.copy_thread.start()

    def on_copy_finished(self, specific_dest_folder):
        if self.current_read_node_name:
            read_node = nuke.toNode(self.current_read_node_name)
            if read_node:
                # Ejecutar en el hilo principal
                nuke.executeInMainThread(
                    lambda: self.update_read_node_and_gui(
                        read_node, specific_dest_folder
                    )
                )
        self.loading_window.stop()

    def update_read_node_and_gui(self, read_node, specific_dest_folder):
        # Seleccionar al nodo Read en el node graph
        nuke.selectAll()
        nuke.invertSelection()
        read_node.setSelected(True)
        nuke.zoomToFitSelected()
        read_node.showControlPanel()

        # Obtener el nombre del archivo o patron de archivo desde la ruta actual
        original_file_path = read_node["file"].getValue()
        filename = os.path.basename(original_file_path)

        # Construir la nueva ruta con el nombre del archivo y la carpeta de destino
        new_file_path = os.path.join(specific_dest_folder, filename).replace("\\", "/")

        # Reemplaza los especificadores de formato por '#'
        new_file_path_table = re.sub(
            r"%0(\d+)d", lambda m: "#" * int(m.group(1)), new_file_path
        )

        # Establecer la nueva ruta en el nodo Read
        if read_node.Class() == "Read":
            read_node["file"].setValue(new_file_path)

        # Buscar la fila en la tabla que corresponde al archivo copiado
        for row in range(self.table.rowCount()):
            # Actualizar la ruta en el QTableWidgetItem y el QLabel
            table_path = self.table.item(row, 0).text()
            if table_path.startswith(original_file_path[: -len(filename)]):
                # Actualizar la ruta manteniendo los '#' y el rango de cuadros
                new_table_path = (
                    new_file_path_table + table_path[len(original_file_path) :]
                )
                self.table.item(row, 0).setText(new_table_path)

                label = self.table.cellWidget(row, 0)
                if label:
                    label.setText(new_table_path)
                    self.apply_color_to_label(
                        label, self.project_folder, new_table_path
                    )

                # Si el archivo estaba "OUTSIDE", actualizar el estado a "OK"
                status_item = self.table.item(row, 2)
                if status_item.text() == "Outside":
                    status_item.setText("OK")
                    status_item.setBackground(
                        QColor("#25321e")
                    )  # Verde oscuro para "OK"

    def on_copy_finished_unico(self, specific_dest_folder=None):
        if specific_dest_folder and self.current_read_node_name:
            read_node = nuke.toNode(self.current_read_node_name)
            if read_node:
                # Ejecutar en el hilo principal
                nuke.executeInMainThread(
                    lambda: self.update_read_node_and_gui_unico(
                        read_node, specific_dest_folder
                    )
                )
        self.loading_window.stop()

    def update_read_node_and_gui_unico(self, read_node, specific_dest_folder):
        # Seleccionar al nodo Read en el node graph
        nuke.selectAll()
        nuke.invertSelection()
        read_node.setSelected(True)
        nuke.zoomToFitSelected()
        read_node.showControlPanel()

        # Preparar la nueva ruta del archivo
        original_file_path = read_node["file"].getValue()
        filename = os.path.basename(original_file_path)
        new_file_path = os.path.join(specific_dest_folder, filename).replace("\\", "/")

        if read_node.Class() == "Read":
            # Establecer la nueva ruta del archivo en el nodo Read
            read_node["file"].setValue(new_file_path)

        # Buscar la fila en la tabla que corresponde al archivo copiado
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == original_file_path:
                # Actualizar la ruta en el QTableWidgetItem
                self.table.item(row, 0).setText(new_file_path)

                # Actualizar tambien el QLabel si es necesario
                label = self.table.cellWidget(row, 0)
                if label:
                    label.setText(new_file_path)
                    self.apply_color_to_label(label, self.project_folder, new_file_path)

                # Si el archivo estaba "OUTSIDE", actualizar el estado a "OK"
                status_item = self.table.item(row, 2)
                if status_item.text() == "Outside":
                    status_item.setText("OK")
                    # Actualizar el color de

    def show_simple_message(self, message):
        QMessageBox.information(self, "Error", message)
        self.on_copy_finished("")

    def show_confirmation_dialog_unico(self, message, dest_path, source_path):
        # Dialogo de confirmacion para la sobreescritura de secuencias de cuadros

        # Verificar si el archivo de origen y destino son el mismo
        source_dir = os.path.dirname(source_path)
        if os.path.normpath(source_dir) == os.path.normpath(dest_path):
            QMessageBox.information(
                self,
                "Same Source and Destination",
                "The source and destination files are the same. No action taken.",
            )
            self.copy_thread.copyCancelledUnico.emit()  # Emite la senal de cancelacion especifica para archivos unicos
            return

        reply = QMessageBox.question(
            self,
            "Confirm Overwrite",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.copy_thread.start_copying_signal.emit(
                source_path, dest_path
            )  # Emite una senal para empezar la copia
        else:
            nuke.executeInMainThread(
                lambda: self.logger.debug("  Copy operation cancelled.")
            )
            self.copy_thread.copyCancelledUnico.emit()  # Emite la senal de cancelacion especifica para archivos unicos

    def show_confirmation_dialog(self, message, dest_path, source_path):
        # Dialogo de confirmacion para la sobreescritura de secuencias de cuadros

        # Verificar si el archivo de origen y destino son el mismo
        # Obtener el directorio base de la secuencia de origen
        source_dir = os.path.dirname(source_path)
        dest_dir = os.path.dirname(dest_path)
        nuke.executeInMainThread(
            lambda: self.logger.debug(f"    source_dir {source_dir}")
        )
        nuke.executeInMainThread(lambda: self.logger.debug(f"    dest_dir {dest_dir}"))

        # Comparar los directorios normalizados
        if os.path.normpath(source_dir) == os.path.normpath(dest_dir):
            QMessageBox.information(
                self,
                "Same Source and Destination",
                "The source and destination directories for the sequence are the same. No action taken.",
            )
            self.copy_thread.copyCancelled.emit()  # Emite la senal de cancelacion
            return

        reply = QMessageBox.question(
            self,
            "Confirm Overwrite",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Llama a copy_sequence con los detalles almacenados
                self.copy_thread.copy_sequence(
                    self.copy_thread.start_frame,
                    self.copy_thread.end_frame,
                    self.copy_thread.file_base,
                    self.copy_thread.frame_padding,
                    self.copy_thread.extension,
                    self.copy_thread.specific_dest_folder,
                )
                self.on_copy_finished(self.copy_thread.specific_dest_folder)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error while copying: {e}")
                self.on_copy_finished(self.copy_thread.specific_dest_folder)
        else:
            print("Copy operation cancelled.")
            self.copy_thread.copyCancelled.emit()  # Emitir la senal cuando la copia es cancelada

    def on_copy_cancelled_unico(self):
        print("Copy operation for a single file was cancelled.")
        self.loading_window.stop()

    def on_copy_cancelled(self):
        print("Copy operation for a single file was cancelled.")
        self.loading_window.stop()


class CopyThread(QThread):
    start_copying_signal = Signal(str, str)
    finishedCopying = Signal(str)  # Modificado para emitir el directorio especifico
    finishedCopyingUnico = Signal(str)
    errorOccurred = Signal(str)  # Senal para enviar mensajes de error
    confirmationNeeded = Signal(
        str, str, str, int, int, str, int, str, str
    )  # Anade los parametros necesarios para copy_sequence
    confirmationNeededUnico = Signal(str, str, str)  # Mensaje, destino, origen
    copyCancelled = Signal()  # senal de que tiene que cerrar ventana de Copying...
    copyCancelledUnico = Signal()

    def __init__(self, source_file_path, dest_folder, parent=None):
        super(CopyThread, self).__init__(parent)
        self.source_file_path = source_file_path
        self.start_copying_signal.connect(self.copy_single_file)
        self.dest_folder = dest_folder
        # Agregar atributos para almacenar informacion de la secuencia
        self.start_frame = None
        self.end_frame = None
        self.file_base = None
        self.frame_padding = None
        self.extension = None
        self.specific_dest_folder = None
        # Configurar logger
        self.logger = configure_logger()

    def copy_sequence(
        self,
        start_frame,
        end_frame,
        file_base,
        frame_padding,
        extension,
        specific_dest_folder,
    ):
        for frame in range(start_frame, end_frame + 1):
            frame_file = f"{file_base.replace('#' * frame_padding, str(frame).zfill(frame_padding))}{extension}"
            dest_file_path = os.path.join(
                specific_dest_folder, os.path.basename(frame_file)
            )
            try:
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"      Copied seq sobreescribir: {frame_file} to {dest_file_path}"
                    )
                )
                shutil.copy(frame_file, dest_file_path)
            except Exception as e:
                nuke.executeInMainThread(
                    lambda: self.logger.debug(f"      ++++Error copying: {e}")
                )

    def copy_single_file(self, source_path, dest_path):

        try:
            shutil.copy(source_path, dest_path)
            self.finishedCopyingUnico.emit(
                dest_path
            )  # Emite la senal indicando que la copia ha finalizado
        except Exception as e:
            self.errorOccurred.emit(f"Error while copying: {e}")

    def run(self):
        start_copy_time = time.time()
        nuke.executeInMainThread(
            lambda: self.logger.debug(
                f"  copy execution time start: {start_copy_time} seconds"
            )
        )

        nuke.executeInMainThread(
            lambda: self.logger.debug("  Copying in background thread")
        )
        # Normalizar las rutas de origen y destino
        normalized_source_path = os.path.normpath(self.source_file_path)
        normalized_dest_folder = os.path.normpath(self.dest_folder)
        # Inicializa el contador de archivos
        copied_files_count = 0

        if "#" in normalized_source_path:
            # Identificar el nombre de la carpeta contenedora
            source_folder = os.path.dirname(normalized_source_path)
            folder_name = os.path.basename(source_folder)

            # Verificar y crear la carpeta en el destino si no existe
            specific_dest_folder = os.path.join(normalized_dest_folder, folder_name)
            self.specific_dest_folder = (
                specific_dest_folder  # Establecer el atributo de la clase
            )

            if not os.path.exists(specific_dest_folder):
                os.makedirs(specific_dest_folder)
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"    Creating folder {specific_dest_folder}"
                    )
                )

            # Copiar los archivos de la secuencia
            frame_range_match = re.search(r"\[(\d+)-(\d+)\]", normalized_source_path)
            if frame_range_match:
                start_frame, end_frame = map(int, frame_range_match.groups())
                file_base = normalized_source_path.split("[")[0]
                extension = normalized_source_path.split("]")[1]
                hash_match = re.search(r"#+", file_base)
                frame_padding = len(hash_match.group()) if hash_match else 1
                # Almacenar los detalles de la secuencia
                self.start_frame = start_frame
                self.end_frame = end_frame
                self.file_base = file_base
                self.frame_padding = frame_padding
                self.extension = extension
                self.specific_dest_folder = specific_dest_folder

                # Solo verifica el primer archivo de la secuencia
                first_frame_file = f"{file_base.replace('#' * frame_padding, str(start_frame).zfill(frame_padding))}{extension}"
                if not os.path.exists(first_frame_file):
                    error_message = f"The file does not exist: {first_frame_file}"
                    self.errorOccurred.emit(error_message)
                    return  # No proceder si el primer archivo no existe

                # Comprobar si el primer archivo de la secuencia ya existe en el destino
                dest_first_frame_file_path = os.path.join(
                    specific_dest_folder, os.path.basename(first_frame_file)
                )
                if os.path.exists(dest_first_frame_file_path):
                    confirm_message = f"The sequence starting with {os.path.basename(first_frame_file)} already exists in the destination. Do you want to overwrite it?"
                    self.confirmationNeeded.emit(
                        confirm_message,
                        dest_first_frame_file_path,
                        first_frame_file,
                        start_frame,
                        end_frame,
                        file_base,
                        frame_padding,
                        extension,
                        specific_dest_folder,
                    )
                    # self.confirmationNeeded.emit(confirm_message, dest_first_frame_file_path, first_frame_file)
                    return  # Esperar confirmacion antes de proceder

                # Si el archivo no existe o si el usuario confirmo la sobrescritura, copiar la secuencia
                for frame in range(start_frame, end_frame + 1):
                    frame_file = f"{file_base.replace('#' * frame_padding, str(frame).zfill(frame_padding))}{extension}"
                    dest_file_path = os.path.join(
                        specific_dest_folder, os.path.basename(frame_file)
                    )
                    nuke.executeInMainThread(
                        lambda: self.logger.debug(
                            f"      Copied seq unico: {frame_file} to {dest_file_path}"
                        )
                    )
                    # try:
                    #    print(f"Copied seq unico: {frame_file} to {dest_file_path}")
                    shutil.copy(frame_file, dest_file_path)
                    copied_files_count += 1  # Incrementa el contador
                    # except Exception as e:
                    #    print(f"Error copying: {e}")
                self.finishedCopying.emit(
                    specific_dest_folder
                )  # Emite la senal indicando que la copia ha finalizado
        else:
            copied_files_count = 1
            # Para archivos unicos, verifica primero si el archivo existe
            if os.path.exists(normalized_source_path):
                self.specific_dest_folder = (
                    self.dest_folder
                )  # Esto deberia ser solo el directorio
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"        normalized_source_path: {normalized_source_path}"
                    )
                )
                dest_file_path = os.path.join(
                    self.specific_dest_folder, os.path.basename(normalized_source_path)
                )
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"        Checking if FILE dest_file_path {dest_file_path} exists in destination..."
                    )
                )

                # Verifica si el archivo ya existe en el destino
                if os.path.exists(dest_file_path):
                    # Si existe, emite una senal para pedir confirmacion
                    confirm_message = f"The file {os.path.basename(normalized_source_path)} already exists in the destination. Do you want to overwrite it?"
                    self.confirmationNeededUnico.emit(
                        confirm_message,
                        self.specific_dest_folder,
                        normalized_source_path,
                    )

                # Si no existe, copia el archivo
                else:
                    dest_folder_path = os.path.dirname(dest_file_path)
                    self.start_copying_signal.emit(
                        normalized_source_path, dest_folder_path
                    )
            else:
                # Si el archivo no existe, muestra un mensaje de error
                error_message = f"The file does not exist: {normalized_source_path}"
                self.errorOccurred.emit(error_message)

        end_time = time.time()
        nuke.executeInMainThread(
            lambda: self.logger.debug(
                f"      Copied {copied_files_count} files in {end_time - start_copy_time} seconds."
            )
        )


class DeleteThread(QThread):
    deleteRow = Signal(int)
    # finishedDeleting = Signal()

    def __init__(self, file_path, main_window, parent=None):
        super(DeleteThread, self).__init__(parent)
        self.file_path = file_path
        self.main_window = (
            main_window  # Referencia a la instancia principal de FileScanner
        )

    def run(self):
        debug_print("--------------- run (delete) ----------------")
        normalized_file_path = self.main_window.normalize_sequence_path_for_comparison(
            self.file_path
        )
        # print(f"file_path: {self.file_path}")
        # print(f"normalized_file_path: {normalized_file_path}")
        found = False
        for row in range(self.main_window.table.rowCount()):
            table_file_path = (
                self.main_window.table.item(row, 0).text().replace("\\", "/").lower()
            )
            normalized_table_file_path = (
                self.main_window.normalize_sequence_path_for_comparison(table_file_path)
            )
            if normalized_table_file_path == normalized_file_path:
                # Verificar si el nombre del archivo en la tabla contiene '#'
                # print(f"table_file_path: {table_file_path}")
                if "#" in table_file_path:
                    # Es una secuencia de cuadros, expandir rango de frames
                    # print("es secuencia")
                    frame_range_match = re.search(r"\[(\d+)-(\d+)\]", table_file_path)
                    if frame_range_match:
                        start_frame, end_frame = map(int, frame_range_match.groups())
                        file_base = table_file_path.split("[")[0]
                        extension = table_file_path.split("]")[1]
                        hash_match = re.search(r"#+", file_base)
                        frame_padding = len(hash_match.group()) if hash_match else 1

                        all_frame_files = [
                            f"{file_base.replace('#' * frame_padding, str(frame).zfill(frame_padding))}{extension}"
                            for frame in range(start_frame, end_frame + 1)
                        ]
                else:
                    # No es una secuencia, es un archivo unico
                    all_frame_files = table_file_path.replace(
                        "/", "\\"
                    )  # Reemplazar barras normales con barras invertidas
                    # print(f"Delete file NO Seq: {all_frame_files}") # SOLO USAR PRINT COMENTANDO EL BORRADO O SE CUELGA!
                    send2trash.send2trash(all_frame_files)
                    # os.remove(all_frame_files)

                # Comprobar si la carpeta es borrable
                folder_delete_value = (
                    self.main_window.table.item(row, 3).text().lower() == "true"
                )
                if (
                    folder_delete_value and "#" in table_file_path
                ):  # Solo intentar borrar la carpeta si es una secuencia
                    folder_path = os.path.dirname(table_file_path).replace(
                        "/", "\\"
                    )  # Normalizar la ruta de la carpeta
                    # print(f"Delete folder Seq: {folder_path}")
                    send2trash.send2trash(folder_path)
                else:
                    # Borrado de archivos individualmente si la carpeta no se puede borrar
                    if "#" in table_file_path:
                        # Borrado de archivos de la secuencia
                        for frame_file in all_frame_files:
                            normalized_frame_file = frame_file.replace(
                                "/", "\\"
                            )  # Normalizar la ruta
                            # print(f"Delete file Seq: {normalized_frame_file}")
                            send2trash.send2trash(normalized_frame_file)

                self.deleteRow.emit(row)
                found = True
                break

        if not found:
            print(f"File path not found in the table: {normalized_file_path}")


class TransparentTextDelegate(QItemDelegate):
    # Clase para crear la interfaz de usuario
    def paint(self, painter, option, index):
        # Modificar el color del texto para todos los estados
        if index.column() == 0:  # Aplicar solo en la columna 'Footage'
            # Configurar el color del texto como transparente para esconderlo y que no se pise con el del QLabel
            option.palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0, 0))
            option.palette.setColor(QPalette.Text, QColor(0, 0, 0, 0))
            # Configurar el color de fondo de la seleccion
            if option.state & QStyle.State_Selected:
                option.palette.setColor(
                    QPalette.Highlight, QColor(62, 62, 62)
                )  # Un gris para la seleccion

        else:  # Para otras columnas, establece el color del texto para el estado seleccionado
            if option.state & QStyle.State_Selected:
                option.palette.setColor(
                    QPalette.Highlight, QColor(62, 62, 62)
                )  # Color de fondo de seleccion
                option.palette.setColor(
                    QPalette.HighlightedText, QColor(200, 200, 200)
                )  # Color del texto seleccionado

        super(TransparentTextDelegate, self).paint(painter, option, index)


class LoadingWindow(QWidget):
    # Clase que sirve para abrir las ventanas de Scanning, Copying, Deleting
    def __init__(self, message, parent=None):
        super(LoadingWindow, self).__init__(parent)
        self.setFixedSize(200, 50)  # Ajusta el tamano segun necesites
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Configura la hoja de estilos para la ventana y el texto
        self.setStyleSheet(
            "background-color: #282828; color: white; font-weight: bold;"
        )

        layout = QVBoxLayout(self)
        self.label = QLabel(message, self)
        self.label.setAlignment(Qt.AlignCenter)  # Centrar el texto
        layout.addWidget(self.label)

    def stop(self):
        self.close()


class StartupWindow(QWidget):
    def __init__(self, message, parent=None):
        super(StartupWindow, self).__init__(parent)
        self.setFixedSize(300, 100)
        self.setWindowTitle("Starting...")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Configura la hoja de estilos para la ventana y el texto
        self.setStyleSheet(
            "background-color: #282828; color: white; font-weight: bold;"
        )

        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #444;
                border-radius: 2px;
                text-align: center;
                background-color: #222;
            }
            QProgressBar::chunk {
                background-color: #666;
                width: 1px;
            }
        """
        )
        layout.addWidget(self.progressBar)

        self.setLayout(layout)

        # Configurar un temporizador para actualizar la barra de progreso
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgressBar)
        self.timer.start(100)  # Actualizar cada 100 milisegundos

    def updateProgressBar(self):
        current_value = self.progressBar.value()
        if current_value < 100:
            self.progressBar.setValue(current_value + 1)
        else:
            self.timer.stop()  # Detener el temporizador cuando llegue a 100

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def stop(self):
        self.timer.stop()  # Asegurarse de detener el temporizador
        self.close()


class ScannerSignals(QObject):
    progress = Signal(int)  # Para actualizar la barra de progreso
    finished = Signal()  # Para indicar que terminó el escaneo
    files_found = Signal(list)  # Para enviar los archivos encontrados


class ScannerWorker(QRunnable):
    def __init__(self, file_scanner):
        super(ScannerWorker, self).__init__()
        self.file_scanner = file_scanner
        self.signals = ScannerSignals()
        self.signals.moveToThread(QApplication.instance().thread())
        self.start_time = time.time()

        # Definir los rangos de progreso para cada etapa
        self.Etapa1_inicio = 0
        self.Etapa1_fin = 10
        self.Etapa2_inicio = 10
        self.Etapa2_fin = 70
        self.Etapa3_inicio = 70
        self.Etapa3_fin = 100

        # Copiar propiedades necesarias desde file_scanner
        self.sequence_extensions = self.file_scanner.sequence_extensions
        self.non_sequence_extensions = self.file_scanner.non_sequence_extensions

        # Obtener el logger configurado
        self.logger = logging.getLogger("LGA_MediaManager")

    def get_timestamp(self):
        elapsed = time.time() - self.start_time
        return f"[{elapsed:.3f}s]"

    @Slot()
    def run(self):
        try:
            self.start_time = time.time()
            total_items = 0
            processed_items = 0

            # Cambiar self.items_log.append por self.logger.debug
            self.logger.debug(f"\n{self.get_timestamp()} Items en carpeta principal:")

            root_items = os.listdir(self.file_scanner.project_folder)
            for item in root_items:
                item_path = os.path.join(self.file_scanner.project_folder, item)
                if os.path.isfile(item_path):
                    total_items += 1
                    self.logger.debug(f"{self.get_timestamp()}   Archivo: {item}")
                elif os.path.isdir(item_path):
                    self.logger.debug(
                        f"\n{self.get_timestamp()} Contenido de carpeta {item}:"
                    )
                    try:
                        subdir_items = os.listdir(item_path)
                        for subitem in subdir_items:
                            total_items += 1
                            self.logger.debug(f"{self.get_timestamp()}   - {subitem}")
                    except Exception:
                        self.logger.debug(
                            f"{self.get_timestamp()}   (No se pudo acceder)"
                        )
                        continue

            # Contar nodos Read para el cálculo del progreso
            read_nodes = nuke.allNodes("Read")
            total_reads = len(read_nodes)

            # Calcular incrementos usando los rangos definidos
            items_increment = 1.0 / total_items if total_items > 0 else 0
            reads_increment = 1.0 / total_reads if total_reads > 0 else 0

            self.logger.debug(
                f"\n{self.get_timestamp()} Total de items encontrados: {total_items}"
            )
            self.logger.debug(
                f"{self.get_timestamp()} Total de nodos Read: {total_reads}"
            )
            self.logger.debug(
                f"\n{self.get_timestamp()} --- Inicio del procesamiento ---"
            )

            def update_progress(increment, description="", is_second_phase=False):
                nonlocal processed_items
                processed_items += increment

                # Calcular el progreso según la etapa
                if not is_second_phase:
                    base_progress = processed_items * 100  # Convertir a porcentaje
                    # Mapear al rango de la Etapa1
                    progress = self.Etapa1_inicio + (
                        base_progress * (self.Etapa1_fin - self.Etapa1_inicio) / 100
                    )
                else:
                    base_progress = processed_items * 100  # Convertir a porcentaje
                    # Mapear al rango de la Etapa3
                    progress = self.Etapa3_inicio + (
                        base_progress * (self.Etapa3_fin - self.Etapa3_inicio) / 100
                    )

                progress = min(int(progress), 100)

                if description:
                    self.logger.debug(
                        f"{self.get_timestamp()} Progreso {progress}%: {description}"
                    )
                self.signals.progress.emit(progress)
                # Forzar el procesamiento de eventos de la UI
                QApplication.processEvents()
                # Pequeña pausa para permitir que la UI se actualice
                time.sleep(0.001)

            # Primera fase
            self.logger.debug(
                f"\n{self.get_timestamp()} Primera fase ({self.Etapa1_inicio}-{self.Etapa1_fin}%):"
            )
            processed_items = 0  # Reiniciar contador para la primera fase

            for item in root_items:
                item_path = os.path.join(self.file_scanner.project_folder, item)
                if os.path.isdir(item_path):
                    try:
                        subdir_items = os.listdir(item_path)
                        for subitem in subdir_items:
                            update_progress(
                                items_increment, f"Procesando {item}/{subitem}"
                            )
                    except Exception:
                        continue
                else:
                    update_progress(items_increment, f"Procesando {item}")

            # Marcar inicio de find_files
            find_files_start = time.time()
            files_data = self.find_files(self.file_scanner.project_folder)
            find_files_time = time.time() - find_files_start

            # Segunda fase
            self.logger.debug(
                f"\n{self.get_timestamp()} Segunda fase ({self.Etapa3_inicio}-{self.Etapa3_fin}%):"
            )
            processed_items = 0  # Reiniciar contador para la segunda fase

            # Marcar inicio de search_unmatched_reads
            reads_start = time.time()
            unmatched_reads_data = self.file_scanner.search_unmatched_reads()

            for node in read_nodes:
                update_progress(
                    reads_increment,
                    f"Procesando nodo Read: {node.name()}",
                    is_second_phase=True,
                )

            reads_time = time.time() - reads_start

            # Logging de tiempos
            self.logger.debug(
                f"\n{self.get_timestamp()} Tiempo total de find_files: {find_files_time:.3f}s"
            )
            self.logger.debug(
                f"\n{self.get_timestamp()} Tiempo total de search_unmatched_reads: {reads_time:.3f}s"
            )
            self.logger.debug(f"\n{self.get_timestamp()} --- Fin del procesamiento ---")
            self.logger.debug(
                f"{self.get_timestamp()} Tiempo total de ejecución: {time.time() - self.start_time:.3f}s"
            )

            # Emitir resultados
            self.signals.files_found.emit((files_data, unmatched_reads_data))
            self.signals.finished.emit()

        except Exception as e:
            debug_print(f"Error en el escaneo: {e}")
            self.signals.finished.emit()

    def find_files(self, folder, progress_callback=None):
        # Encuentra los archivos en la carpeta del proyecto y determina si son secuencias
        end_time = time.time()
        # logging.info(f"Scanning folder: {folder}")
        # logging.info("")
        # logging.info("find_files execution time start: ", end_time - start_time, "seconds")

        sequences = {}
        all_read_files = self.get_read_files()
        to_add = []

        # Contador para el progreso
        total_processed = 0
        total_files = 0
        processed_items = 0
        update_interval = 20  # Actualizar cada 20 archivos

        # Primera pasada para contar archivos totales
        for root, _, files in os.walk(folder):
            filtered_files = [
                f
                for f in files
                if f.lower().endswith(
                    tuple(self.sequence_extensions + self.non_sequence_extensions)
                )
            ]
            total_files += len(filtered_files)

        def update_find_progress(description=""):
            nonlocal processed_items
            processed_items += 1

            # Solo actualizar cada update_interval archivos
            if processed_items % update_interval == 0:
                base_progress = (processed_items / max(1, total_files)) * 100
                progress = self.Etapa2_inicio + (
                    base_progress * (self.Etapa2_fin - self.Etapa2_inicio) / 100
                )
                progress = min(int(progress), self.Etapa2_fin)
                self.logger.debug(
                    f"{self.get_timestamp()} Progreso {progress}%: {description}"
                )
                self.signals.progress.emit(progress)
                QApplication.processEvents()

        # Log del inicio de la etapa 2
        self.logger.debug(
            f"\n{self.get_timestamp()} Segunda fase ({self.Etapa2_inicio}-{self.Etapa2_fin}%):"
        )

        for root, dirs, files in os.walk(folder):
            # logging.info(f"Analyzing folder: {root}")

            # Filtrar archivos segun las extensiones definidas
            filtered_files = [
                f
                for f in files
                if f.lower().endswith(
                    tuple(self.sequence_extensions + self.non_sequence_extensions)
                )
            ]
            filtered_files.sort(key=lambda x: x.lower())

            for i in range(len(filtered_files) - 1):
                file1, file2 = filtered_files[i], filtered_files[i + 1]
                # logging.info(f"Comparing: {file1} and {file2}")

                # Actualizar progreso mientras procesamos
                update_find_progress(f"Analizando {file1}")

                # Solo procesar archivos de secuencia para comparar diferencias
                if file1.lower().endswith(
                    tuple(self.sequence_extensions)
                ) and file2.lower().endswith(tuple(self.sequence_extensions)):

                    difference = [char1 != char2 for char1, char2 in zip(file1, file2)]
                    # logging.info(f"Differences: {difference}")
                    diff_indices = [i for i, x in enumerate(difference) if x]
                    # logging.info(f"diff_indices: {difference}")

                    if 1 <= len(diff_indices) <= 2:
                        index = diff_indices[0]
                        try:
                            match1 = re.match(r"(.*?)(\d+)(\D*)$", file1)
                            match2 = re.match(r"(.*?)(\d+)(\D*)$", file2)
                            if progress_callback:
                                progress_callback(f"Procesando secuencia {file1}")

                            if match1 and match2:
                                left_part_file1, frame_num1, right_part_file1 = (
                                    match1.groups()
                                )
                                left_part_file2, frame_num2, right_part_file2 = (
                                    match2.groups()
                                )

                            # logging.info(f"Frame numbers extracted: {frame_num1} and {frame_num2}")

                            # Verifica si los numeros de frame son consecutivos
                            if int(frame_num1) + 1 == int(frame_num2):
                                # logging.info(f"Frames {frame_num1} and {frame_num2} are consecutive")
                                sequence_base = os.path.join(
                                    root,
                                    str(left_part_file1)
                                    + "#" * len(str(frame_num1))
                                    + str(right_part_file1),
                                )
                                if sequence_base not in sequences:
                                    sequences[sequence_base] = []
                                sequences[sequence_base].extend(
                                    [frame_num1, frame_num2]
                                )
                            else:
                                # logging.info(f"Frames {frame_num1} and {frame_num2} are not consecutive")

                                left_part = file1[:index]
                                right_part = file1[index + len(frame_num1) :]

                                # Separar la extension de right_part
                                right_part, extension = os.path.splitext(right_part)

                                # Buscar numeros al final de left_part
                                left_part_match = re.search(r"(.*?)(\d*)$", left_part)
                                if left_part_match:
                                    left_part, left_numbers = left_part_match.groups()
                                    frame_num1 = left_numbers + frame_num1
                                    frame_num2 = left_numbers + frame_num2

                                if int(frame_num1) + 1 == int(frame_num2):
                                    # logging.info(f"Frames {frame_num1} and {frame_num2} are consecutive")
                                    sequence_base = os.path.join(
                                        root,
                                        left_part
                                        + "#" * len(frame_num1)
                                        + right_part
                                        + extension,
                                    )
                                    if sequence_base not in sequences:
                                        sequences[sequence_base] = []
                                    sequences[sequence_base].extend(
                                        [frame_num1, frame_num2]
                                    )
                                else:
                                    # logging.info(f"Frames {frame_num1} and {frame_num2} are not consecutive")
                                    pass
                        except AttributeError as e:
                            debug_print(
                                f"Error parsing files: {file1} and {file2} at index {index}"
                            )  # Anadido
                            debug_print(f"AttributeError: {e}")  # Anadido
                            # Continua con la proxima iteracion si no se pueden dividir los nombres correctamente
                            continue

            # Agregar archivos no secuenciales despues de procesar todas las secuencias
            for file in filtered_files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(
                    tuple(self.sequence_extensions + self.non_sequence_extensions)
                ):
                    in_sequence = False
                    for base, frames in sequences.items():
                        if file_path.startswith(
                            base.split("#")[0]
                        ) and file_path.endswith(base.split("#")[-1]):
                            in_sequence = True
                            break
                    if not in_sequence:
                        # logging.info(f"Agregando archivo no secuencial: {file_path}")
                        to_add.append(
                            (file_path, all_read_files, False, "", False, False, False)
                        )

                update_find_progress(f"Procesando {file}")

        ##############################################

        # Procesar las secuencias identificadas y verificar carpetas borrables
        for base, frames in sequences.items():
            sequences[base] = sorted(set(frames))
            frame_range = f"[{min(frames)}-{max(frames)}]"
            # logging.info (f"frame_range {frame_range}")
            # logging.info (f"min(frames) {min(frames)}")
            # logging.info (f"max(frames) {max(frames)}")

            # logging.info(f"Secuencia identificada: {base} con frames {sequences[base]}")

            # Normalizar la base para la comparacion
            normalized_base = os.path.normpath(base).replace("\\\\", "\\").lower()
            normalized_base = normalized_base.replace("\\", "/")
            # logging.info("")
            # logging.info (f"base {base}")
            # logging.info (f"normalized_base {normalized_base}")

            # Normalizar y resolver las rutas de los reads
            normalized_read_files = {
                os.path.abspath(os.path.normpath(path))
                .replace("\\\\", "\\")
                .lower(): nodes
                for path, nodes in all_read_files.items()
            }

            # Reemplazar %0Xd por la cantidad correspondiente de #
            for path, nodes in list(normalized_read_files.items()):
                new_key = re.sub(r"%0(\d+)d", lambda m: "#" * int(m.group(1)), path)
                normalized_read_files[new_key] = normalized_read_files.pop(path)

            normalized_read_files = {
                path.replace("\\", "/"): nodes
                for path, nodes in normalized_read_files.items()
            }

            # logging.info(f"normalized_base: {normalized_base}")
            # logging.info(f"normalized_read_files: {normalized_read_files}")

            # Ahora utiliza normalized_read_files para la comparacion
            matched_nodes = []
            for read_path, nodes in normalized_read_files.items():
                # logging.info(f"Normalized read path: {read_path}, Nodes: {nodes}")
                match_check = normalized_base.startswith(os.path.dirname(read_path))
                # logging.info(f"Comparing: {normalized_base} with {read_path} - Match: {match_check}")
                if normalized_base.startswith(os.path.dirname(read_path)):
                    matched_nodes.extend(nodes)
                    # logging.info(f"Matched nodes for {normalized_base}: {matched_nodes}")

            # Verificar si la carpeta contiene solo archivos de la secuencia
            directory_path = os.path.dirname(base)
            # logging.info (f"directory_path {directory_path}")
            all_files_in_directory = set(os.listdir(directory_path))

            sequence_files_set = set(
                [
                    os.path.basename(base).replace(
                        "#" * len(str(min(frames))),
                        str(frame).zfill(len(str(min(frames)))),
                    )
                    for frame in frames
                ]
            )
            # logging.info (f"sequence_files_set {sequence_files_set}")
            is_folder_deletable = all_files_in_directory == sequence_files_set
            # logging.info (f"is_folder_deletable {is_folder_deletable}")

            to_add.append(
                (
                    base,
                    all_read_files,
                    True,
                    frame_range,
                    False,
                    is_folder_deletable,
                    True,
                )
            )

        # Ordenar to_add por "Status" y luego por "Footage" antes de Agregar a la tabla
        to_add.sort(
            key=lambda x: x[0].replace("_", "0" + "_")
        )  # Ordenar por Footage, considerando _ despues de letras.

        # end_time = time.time()
        # logging.info("find_files execution time end: ", end_time - start_time, "seconds")

        return to_add  # En lugar de llamar a add_file_to_table, devuelve los datos

    def get_read_files(self):
        # Usar el método de file_scanner
        return self.file_scanner.get_read_files()


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    # Verificar si el script está guardado
    if not nuke.root().name() or nuke.root().name() == "Root":
        QMessageBox.warning(
            None, "Warning", "Please save the Nuke script before running this tool."
        )
        return

    # Crear y mostrar la ventana de inicio
    startup_window = StartupWindow("Scanning, please wait...")
    # Centrar la ventana de inicio
    screen = QApplication.primaryScreen().geometry()
    startup_window.move(
        screen.center().x() - startup_window.width() // 2,
        screen.center().y() - startup_window.height() // 2,
    )
    startup_window.show()
    app.processEvents()

    # Crear la ventana principal y realizar el escaneo inicial
    window = FileScanner()
    if window.initialization_successful:

        def delayed_show():
            window.adjust_window_size()
            # Centrar la ventana principal
            window.move(
                screen.center().x() - window.width() // 2,
                screen.center().y() - window.height() // 2,
            )
            window.show()

        def on_scan_complete():
            startup_window.stop()
            # Usar QTimer para retrasar la visualización
            QTimer.singleShot(100, delayed_show)  # 100ms de retraso

        # Usar el scanner_worker de window.scan_project()
        window.scanner_worker.signals.progress.connect(startup_window.updateProgress)
        window.scanner_worker.signals.finished.connect(on_scan_complete)

        # Iniciar el escaneo en segundo plano usando el worker existente
        QThreadPool.globalInstance().start(window.scanner_worker)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication([])
    window = FileScanner()
    window.show()
