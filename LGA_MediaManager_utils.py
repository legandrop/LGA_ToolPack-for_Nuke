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

# Importar el tiempo de inicio global del archivo principal
try:
    from LGA_mediaManager import _start_time
except ImportError:
    _start_time = time.time()

start_time = time.time()


def get_log_prefix(caller_class=None, caller_method=None):
    """
    Genera el prefijo para logs con formato [tiempo] [clase::metodo]
    """
    elapsed = time.time() - _start_time
    timestamp = f"[{elapsed:.3f}s]"

    if caller_class and caller_method:
        location = f"[{caller_class}::{caller_method}]"
        return f"{timestamp} {location}"
    else:
        return timestamp


def configure_logger():
    # Importar la configuracion centralizada del archivo principal
    try:
        from LGA_mediaManager import configure_logger as main_configure_logger

        return main_configure_logger()
    except ImportError:
        # Fallback en caso de problemas de importacion
        import logging

        logger = logging.getLogger("LGA_MediaManager")
        return logger


# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def normalize_path_for_comparison(file_path):
    """
    Normaliza una ruta de archivo para comparaciones consistentes.
    Convierte barras a forward slashes y pone todo en minusculas.
    """
    if not file_path:
        return ""

    # Primero normalizar con os.path.normpath para manejar ./ ../ etc
    normalized = os.path.normpath(file_path)
    # Convertir todas las barras a forward slashes
    normalized = normalized.replace("\\", "/")
    # Convertir a minusculas para comparacion case-insensitive
    normalized = normalized.lower()

    return normalized


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

        # LOG DE TRAZABILIDAD EN CONSTRUCTOR: Identificar dónde se crea cada worker
        import traceback

        stack = traceback.extract_stack()
        caller_info = []
        for frame in stack[-15:]:  # Últimas 15 llamadas para más contexto
            caller_info.append(f"{frame.filename}:{frame.lineno} in {frame.name}")

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
        self.logger = configure_logger()

        # LOG DE CREACIÓN DEL WORKER
        self.logger.debug(
            f"\n[FIX!!!] ========== CONSTRUCTOR SCANNER WORKER =========="
        )
        self.logger.debug(f"[FIX!!!] Worker ID: {id(self)}")
        self.logger.debug(f"[FIX!!!] Creado desde:")
        for i, call in enumerate(caller_info):
            self.logger.debug(f"[FIX!!!]   {i}: {call}")
        self.logger.debug(f"[FIX!!!] =============================================")

        # Guardar información para debugging
        self.creation_stack = caller_info

    def get_timestamp(self):
        # Usar el nuevo formato centralizado
        return get_log_prefix(self.__class__.__name__, "ScannerWorker")

    @Slot()
    def run(self):
        try:
            # LOG DE TRAZABILIDAD: Identificar quién llamó a este worker
            import traceback
            import inspect

            stack = traceback.extract_stack()
            caller_info = []
            for frame in stack[-10:]:  # Últimas 10 llamadas
                caller_info.append(f"{frame.filename}:{frame.lineno} in {frame.name}")

            self.logger.debug(
                f"\n[FIX!!!] ========== SCANNER WORKER INICIADO =========="
            )
            self.logger.debug(f"[FIX!!!] Worker ID: {id(self)}")
            self.logger.debug(f"[FIX!!!] Llamado desde:")
            for i, call in enumerate(caller_info):
                self.logger.debug(f"[FIX!!!]   {i}: {call}")
            self.logger.debug(
                f"[FIX!!!] ==============================================="
            )

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
        processed_files = set()  # Para evitar duplicados causados por os.walk()

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

            # LOG ESPECIFICO: Detectar cuántas veces aparece EditRef en las carpetas
            editref_files = [f for f in filtered_files if "EditRef_v01.mov" in f]
            if editref_files:
                self.logger.debug(
                    f"\n[FIX!!!] FIND_FILES COUNT: EditRef encontrado en root: {root}"
                )
                self.logger.debug(f"[FIX!!!] Archivos EditRef: {editref_files}")

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

            # LOG ESPECIFICO: Detectar cuántas veces aparece EditRef en la segunda pasada
            editref_files = [f for f in filtered_files if "EditRef_v01.mov" in f]
            if editref_files:
                self.logger.debug(
                    f"\n[FIX!!!] FIND_FILES SEGUNDA PASADA: EditRef en root: {root}"
                )
                self.logger.debug(f"[FIX!!!] Archivos EditRef: {editref_files}")

            for i in range(len(filtered_files) - 1):
                file1, file2 = filtered_files[i], filtered_files[i + 1]
                # logging.info(f"Comparing: {file1} and {file2}")

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
                # Actualizar progreso una sola vez por archivo
                update_find_progress(f"Procesando {file}")

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
                        # SOLUCION QUIRURGICA: Verificar si ya fue procesado para evitar duplicados
                        normalized_file_path = normalize_path_for_comparison(file_path)

                        # LOG ESPECIFICO: Debug del estado antes de verificar
                        if "EditRef_v01.mov" in file_path:
                            self.logger.debug(
                                f"\n*** FIND_FILES: Evaluando EDITREF ***"
                            )
                            self.logger.debug(f"File path: {file_path}")
                            self.logger.debug(
                                f"Normalized path: {normalized_file_path}"
                            )
                            self.logger.debug(
                                f"¿Ya estaba en processed_files?: {normalized_file_path in processed_files}"
                            )
                            self.logger.debug(
                                f"Tamaño de processed_files: {len(processed_files)}"
                            )

                        if normalized_file_path not in processed_files:
                            processed_files.add(normalized_file_path)

                            # LOG ESPECIFICO: Detectar cuando agregamos EditRef en find_files
                            if "EditRef_v01.mov" in file_path:
                                self.logger.debug(
                                    f"*** FIND_FILES: Agregando EDITREF como no secuencial ***"
                                )
                                self.logger.debug(f"In sequence: {in_sequence}")
                            # logging.info(f"Agregando archivo no secuencial: {file_path}")
                            to_add.append(
                                (
                                    file_path,
                                    all_read_files,
                                    False,
                                    "",
                                    False,
                                    False,
                                    False,
                                )
                            )
                        else:
                            # LOG ESPECIFICO: Detectar duplicados evitados
                            if "EditRef_v01.mov" in file_path:
                                self.logger.debug(
                                    f"\n*** FIND_FILES: DUPLICADO EVITADO - EditRef ya procesado ***"
                                )
                                self.logger.debug(f"File path: {file_path}")
                                self.logger.debug(
                                    f"Normalized path: {normalized_file_path}"
                                )

        ##############################################

        # Procesar las secuencias identificadas y verificar carpetas borrables
        for base, frames in sequences.items():
            sequences[base] = sorted(set(frames))
            frame_range = f"[{min(frames)}-{max(frames)}]"
            # logging.info (f"frame_range {frame_range}")
            # logging.info (f"min(frames) {min(frames)}")
            # logging.info (f"max(frames) {max(frames)}")

            # logging.info(f"Secuencia identificada: {base} con frames {sequences[base]}")

            # Normalizar la base para la comparacion usando la funcion centralizada
            normalized_base = normalize_path_for_comparison(base)
            # logging.info("")
            # logging.info (f"base {base}")
            # logging.info (f"normalized_base {normalized_base}")

            # Normalizar y resolver las rutas de los reads usando la funcion centralizada
            normalized_read_files = {}
            for path, nodes in all_read_files.items():
                # Reemplazar %0Xd por la cantidad correspondiente de #
                new_key = re.sub(r"%0(\d+)d", lambda m: "#" * int(m.group(1)), path)
                # Usar la funcion de normalizacion centralizada
                new_key = normalize_path_for_comparison(new_key)
                normalized_read_files[new_key] = nodes

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

            # SOLUCION QUIRURGICA: Verificar duplicados en secuencias también
            normalized_base = normalize_path_for_comparison(base)
            if normalized_base not in processed_files:
                processed_files.add(normalized_base)
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
            else:
                self.logger.debug(f"\n*** FIND_FILES: SECUENCIA DUPLICADA EVITADA ***")
                self.logger.debug(f"Base: {base}")
                self.logger.debug(f"Normalized base: {normalized_base}")

        # SOLUCION QUIRURGICA FINAL: Eliminar duplicados de to_add antes de devolver
        self.logger.debug(
            f"\n[FIX!!!] FIND_FILES: Eliminando duplicados de {len(to_add)} archivos ***"
        )

        # Usar un diccionario para rastrear archivos únicos por path normalizado
        unique_files = {}
        duplicates_found = 0
        editref_count = 0

        for i, item in enumerate(to_add):
            (
                file_path,
                read_files,
                is_sequence,
                frame_range,
                is_unmatched_read,
                is_folder_deletable,
                sequence_state,
            ) = item
            normalized_path = normalize_path_for_comparison(file_path)

            # Contar EditRef para debugging
            if "EditRef_v01.mov" in file_path:
                editref_count += 1
                self.logger.debug(
                    f"[FIX!!!] EditRef #{editref_count} encontrado en posición {i}"
                )
                self.logger.debug(f"[FIX!!!] Path original: {file_path}")
                self.logger.debug(f"[FIX!!!] Path normalizado: {normalized_path}")

            if normalized_path not in unique_files:
                unique_files[normalized_path] = item
                if "EditRef_v01.mov" in file_path:
                    self.logger.debug(
                        f"[FIX!!!] EditRef #{editref_count} AGREGADO como único"
                    )
            else:
                duplicates_found += 1
                if "EditRef_v01.mov" in file_path:
                    self.logger.debug(
                        f"[FIX!!!] DUPLICADO ENCONTRADO Y ELIMINADO: EditRef #{editref_count}"
                    )
                    self.logger.debug(f"[FIX!!!] Path original: {file_path}")
                    self.logger.debug(f"[FIX!!!] Path normalizado: {normalized_path}")

        # Convertir de vuelta a lista
        to_add = list(unique_files.values())

        self.logger.debug(f"[FIX!!!] Duplicados eliminados: {duplicates_found} ***")
        self.logger.debug(f"[FIX!!!] Archivos únicos restantes: {len(to_add)} ***")
        self.logger.debug(f"[FIX!!!] EditRef total encontrados: {editref_count} ***")

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

    # Importación local para evitar importación circular
    from LGA_MediaManager_FileScanner import FileScanner

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

        # LOG DE TRAZABILIDAD: Verificar si window ya tiene scanner_worker
        logger = configure_logger()
        logger.debug(f"\n[FIX!!!] ========== MAIN FUNCTION ==========")
        logger.debug(f"[FIX!!!] Window creada: {id(window)}")
        logger.debug(
            f"[FIX!!!] ¿Window tiene scanner_worker?: {hasattr(window, 'scanner_worker')}"
        )
        if hasattr(window, "scanner_worker"):
            logger.debug(
                f"[FIX!!!] Scanner_worker ID: {id(window.scanner_worker) if window.scanner_worker else 'None'}"
            )
        logger.debug(f"[FIX!!!] =====================================")

        # SOLUCION QUIRURGICA: El worker ya se inicia en scan_project(), no iniciarlo de nuevo
        # Conectar las señales al worker que ya está corriendo
        def connect_signals_when_ready():
            if hasattr(window, "scanner_worker") and window.scanner_worker:
                window.scanner_worker.signals.progress.connect(
                    startup_window.updateProgress
                )
                window.scanner_worker.signals.finished.connect(on_scan_complete)
                logger.debug("[FIX!!!] MAIN: Señales conectadas al worker existente")
            else:
                # Si no hay worker, crear uno (fallback)
                logger.debug("[FIX!!!] MAIN: No hay worker, llamando scan_project()")
                window.scan_project()
                connect_signals_when_ready()

        connect_signals_when_ready()

        # NO iniciar worker adicional - ya se inicia en scan_project()
        # QThreadPool.globalInstance().start(window.scanner_worker)  # COMENTADO - CAUSABA DUPLICACION


if __name__ == "__main__":
    # Importación local para evitar importación circular
    from LGA_MediaManager_FileScanner import FileScanner

    app = QApplication.instance() or QApplication([])
    window = FileScanner()
    window.show()
