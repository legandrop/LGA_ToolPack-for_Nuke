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

DEBUG = False


def configure_logger():
    # Si ya existe un logger configurado, lo retornamos sin crear uno nuevo
    if hasattr(configure_logger, "logger"):
        return configure_logger.logger

    # Crear un logger personalizado
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Verificar si ya tiene handlers para evitar duplicados
    if not logger.handlers:
        # Crear un handler para escribir en archivo
        log_dir = os.path.dirname(os.path.realpath(__file__))
        log_file = os.path.join(log_dir, "LGA_mediaManager_log.txt")
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging.DEBUG)

        # Crear un formatter para el output
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Agregar el handler al logger
        logger.addHandler(file_handler)

    # Guardar una referencia al logger para no duplicarlo
    configure_logger.logger = logger
    return logger


def debug_print(*message):
    if DEBUG:
        print(*message)


def normalize_path_for_comparison(file_path):
    """
    Normaliza una ruta de archivo para comparacion
    Convierte a minusculas y reemplaza barras invertidas por barras normales
    """
    return file_path.replace("\\", "/").lower()


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
