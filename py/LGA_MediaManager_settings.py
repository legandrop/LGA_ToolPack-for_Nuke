"""
_______________________________________

  LGA_MediaManager_settings v2.26 | Lega
  Ventana de ajustes del Media Manager

  v2.25: Cada destino ocupa una sola fila -nombre y ruta al lado,
         encabezado de columna una vez- con los campos alineados. El
         depth se maneja con un stepper de botones a los costados en
         vez del spinbox nativo, que iba de 20 px y se enfocaba en
         amarillo. Muestra la version de la herramienta, leida del
         header del script principal. Guarda de forma atomica en el
         .ini de la carpeta de datos del usuario y avisa por senal.

  v2.13: El look sale de LGA_UI_Style_ToolPack. Cada widget repetia
         su propio bloque de QToolTip inline —el mismo, seis veces—
         y la ventana iba mas clara que sus propios campos, con la
         jerarquia al reves.
  v2.12: El header decia LGA_mediaManager, el nombre de la
         herramienta y no el de este modulo. Se sigue la numeracion
         que traian los helpers del Media Manager.
_______________________________________

"""

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore
from LGA_UI_Style_ToolPack import Color, Metric, Style

QApplication = QtWidgets.QApplication
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QVBoxLayout = QtWidgets.QVBoxLayout
QWidget = QtWidgets.QWidget
QPushButton = QtWidgets.QPushButton
QToolButton = QtWidgets.QToolButton
QSizePolicy = QtWidgets.QSizePolicy
QFileDialog = QtWidgets.QFileDialog
QItemDelegate = QtWidgets.QItemDelegate
QStyle = QtWidgets.QStyle
QMessageBox = QtWidgets.QMessageBox
QCheckBox = QtWidgets.QCheckBox
QLabel = QtWidgets.QLabel
QHBoxLayout = QtWidgets.QHBoxLayout
QFrame = QtWidgets.QFrame
QMenu = QtWidgets.QMenu
try:
    QAction = QtGui.QAction
except Exception:
    QAction = QtWidgets.QAction
QProgressBar = QtWidgets.QProgressBar
QLineEdit = QtWidgets.QLineEdit
QBrush = QtGui.QBrush
QColor = QtGui.QColor
QPalette = QtGui.QPalette
QMovie = QtGui.QMovie
QScreen = QtGui.QScreen
QIcon = QtGui.QIcon
Qt = QtCore.Qt
QTimer = QtCore.QTimer
QThread = QtCore.QThread
Signal = QtCore.Signal
QObject = QtCore.QObject
QRunnable = QtCore.QRunnable
Slot = QtCore.Slot
QThreadPool = QtCore.QThreadPool
import nuke
import os
import re
import subprocess
import time
import shutil
import sys
import configparser
import logging

from LGA_MediaManager_logging import configure_logger, debug_print
from LGA_MediaManager_config import get_write_path, write_ini

QIntValidator = QtGui.QIntValidator


# Anchos de las columnas de la lista de destinos. El nombre va angosto y la
# ruta expande: un nombre son dos palabras y una ruta puede ser larga. Son
# distintos a proposito, no por como cayo cada fila.
INDEX_WIDTH = 16  # el numero de orden del destino
NAME_WIDTH = 150
ROW_SPACING = 8
STEPPER_FIELD_WIDTH = 56
# El boton chico de quitar/sumar mide lo mismo que la cruz de cerrar del
# resto del pack, asi que sale del modulo de estilo y no de un 26 local.
MINUS_BUTTON_SIZE = Metric.CLOSE_BUTTON_SIZE

FOLDER_DEPTH_MIN = 1
FOLDER_DEPTH_MAX = 10


# Los tooltips van en castellano y salen de aca, no hardcodeados en el widget,
# para que la migracion a bilingue sea un cambio de datos.
TOOLTIPS = {
    "depth": (
        "Cuantas carpetas hay que subir desde el script para llegar\n"
        "a la carpeta del shot"
    ),
    "depth_minus": "Una carpeta menos",
    "depth_plus": "Una carpeta mas",
    "name": (
        "Nombre que aparece en el menu Copy to.\n"
        "Un & antes de una letra la convierte en atajo:\n"
        "&Assets se dispara con Alt+A"
    ),
    "path": "Ruta de la carpeta, relativa a la carpeta del shot",
    "remove": "Quita este destino",
    "add": "Agrega un destino al menu Copy to",
}


def get_tool_version():
    """
    Version de la herramienta, leida del header de LGA_mediaManager.py.

    Se lee el archivo en vez de importarlo para no depender del orden de
    importacion: este modulo lo carga el script principal. Si el header
    cambia de formato se devuelve vacio y la ventana no muestra version,
    que es mejor que mostrar una equivocada.
    """
    try:
        main_script = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "LGA_mediaManager.py"
        )
        with open(main_script, "r", encoding="utf-8") as handle:
            header = handle.read(600)
        match = re.search(r"LGA_mediaManager\s+v(\d+\.\d+)\s*\|", header)
        return match.group(1) if match else ""
    except Exception:
        return ""


class DepthField(QLineEdit):
    """
    El campo del stepper de profundidad.

    Es un QLineEdit y no un QSpinBox para que le caiga la misma regla de
    estilo que al resto de los campos: el QSpinBox se deja nativo en el
    modulo de estilo, y nativo es justamente lo que se veia mal -20 px de
    alto y el anillo de foco amarillo de macOS. Conserva del spinbox lo
    que se usa: rango, flechas del teclado y rueda del mouse.
    """

    def __init__(self, value, parent=None):
        super().__init__(str(value), parent)
        self.setValidator(QIntValidator(FOLDER_DEPTH_MIN, FOLDER_DEPTH_MAX, self))
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(STEPPER_FIELD_WIDTH)

    def value(self):
        # Se acota aca y no solo en step(): QIntValidator da por Intermediate
        # cualquier numero mas corto que el minimo, asi que deja tipear un 0.
        # Un 0 guardado hace que la carpeta del shot sea el propio .nk.
        try:
            escrito = int(self.text())
        except ValueError:
            return FOLDER_DEPTH_MIN
        return max(FOLDER_DEPTH_MIN, min(FOLDER_DEPTH_MAX, escrito))

    def step(self, delta):
        nuevo = max(FOLDER_DEPTH_MIN, min(FOLDER_DEPTH_MAX, self.value() + delta))
        self.setText(str(nuevo))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.step(1)
        elif event.key() == Qt.Key_Down:
            self.step(-1)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            self.step(1 if event.angleDelta().y() > 0 else -1)
        else:
            event.ignore()


class DestinationRow(QWidget):
    """Una fila de la lista: numero, nombre, ruta y el boton de quitar."""

    def __init__(self, index, name, path, on_remove, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ROW_SPACING)

        self.index_label = QLabel(str(index))
        self.index_label.setFixedWidth(INDEX_WIDTH)
        self.index_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_edit = QLineEdit(name)
        self.name_edit.setFixedWidth(NAME_WIDTH)
        self.name_edit.setToolTip(TOOLTIPS["name"])

        self.path_edit = QLineEdit(path)
        self.path_edit.setToolTip(TOOLTIPS["path"])

        self.minus_button = QPushButton("-")
        self.minus_button.setFixedSize(MINUS_BUTTON_SIZE, MINUS_BUTTON_SIZE)
        self.minus_button.setToolTip(TOOLTIPS["remove"])
        self.minus_button.setStyleSheet(Style.BTN_ICON)
        self.minus_button.setFocusPolicy(Qt.NoFocus)
        self.minus_button.clicked.connect(lambda: on_remove(self))

        layout.addWidget(self.index_label)
        layout.addWidget(self.name_edit)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.minus_button)

    def set_index(self, index):
        self.index_label.setText(str(index))

    def name(self):
        return self.name_edit.text()

    def path(self):
        return self.path_edit.text()


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
    # La emite al guardar para que el Media Manager relea el .ini: sin esto,
    # un destino agregado aca no aparece en el menu Copy to hasta reabrir.
    settings_saved = Signal()

    def __init__(self, settings_data, parent=None):
        super().__init__(parent)
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
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*([Metric.WINDOW_MARGIN] * 4))
        self.setLayout(self.layout)
        self.setStyleSheet(Style.FORM + Style.TOOLTIP)
        self.rows = []  # Una entrada por destino, en orden

        # --- Folder scan depth -------------------------------------------
        # Stepper: el campo en el medio y los dos botones a los costados. El
        # spinbox nativo media 20 px contra los 30 de un campo, asi que sus
        # flechas quedaban de 7 px, y al enfocarlo se pintaba con el anillo
        # amarillo del sistema mientras el resto se pone violeta.
        folder_scan_hbox = QHBoxLayout()
        folder_scan_hbox.setSpacing(ROW_SPACING)
        depth_label = QLabel("Folder scan depth:")
        depth_label.setProperty("lgaTitle", True)

        self.depth_field = DepthField(
            int(self.settings_data.get("Folder scan depth", 3))
        )
        self.depth_field.setToolTip(TOOLTIPS["depth"])

        depth_minus = QPushButton("-")
        depth_plus = QPushButton("+")
        for boton, delta in ((depth_minus, -1), (depth_plus, 1)):
            boton.setFixedSize(MINUS_BUTTON_SIZE, MINUS_BUTTON_SIZE)
            boton.setStyleSheet(Style.BTN_ICON)
            boton.setFocusPolicy(Qt.NoFocus)
            boton.clicked.connect(lambda _=False, d=delta: self.depth_field.step(d))
        depth_minus.setToolTip(TOOLTIPS["depth_minus"])
        depth_plus.setToolTip(TOOLTIPS["depth_plus"])

        folder_scan_hbox.addWidget(depth_label)
        folder_scan_hbox.addWidget(depth_minus)
        folder_scan_hbox.addWidget(self.depth_field)
        folder_scan_hbox.addWidget(depth_plus)
        folder_scan_hbox.addStretch()
        self.layout.addLayout(folder_scan_hbox)

        self.layout.addSpacing(10)
        self.layout.addWidget(self.build_separator())
        self.layout.addSpacing(10)

        # --- Copy to ------------------------------------------------------
        copy_to_label = QLabel("Copy to:")
        copy_to_label.setProperty("lgaTitle", True)
        self.layout.addWidget(copy_to_label)
        self.layout.addSpacing(6)

        # Los encabezados van una sola vez, arriba: repetir "Name" y "Path" en
        # cada destino era ruido, el numero de fila ya dice cual es cual.
        heads = QHBoxLayout()
        heads.setSpacing(ROW_SPACING)
        spacer_head = QLabel("")
        spacer_head.setFixedWidth(INDEX_WIDTH)
        name_head = QLabel("Name")
        name_head.setFixedWidth(NAME_WIDTH)
        path_head = QLabel("Path")
        tail_head = QLabel("")
        tail_head.setFixedWidth(MINUS_BUTTON_SIZE)
        for widget in (spacer_head, name_head, path_head, tail_head):
            heads.addWidget(widget)
        self.layout.addLayout(heads)
        self.layout.addSpacing(2)

        # Contenedor propio para las filas: agregar y quitar destinos toca
        # solo este layout y no hay que contar posiciones del layout principal.
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(ROW_SPACING)
        self.layout.addLayout(self.rows_layout)

        i = 1
        while True:
            button_text_key = f"copy_{i}_button_text"
            path_key = f"copy_{i}_subdirectory"
            if (
                button_text_key not in self.settings_data
                or path_key not in self.settings_data
            ):
                break
            self.add_row(
                self.settings_data.get(button_text_key, ""),
                self.settings_data.get(path_key, ""),
            )
            i += 1

        self.layout.addSpacing(4)

        # El boton de agregar arranca en la columna del nombre, no pegado al
        # borde: ahi quedaba colgado debajo de los numeros de fila.
        add_hbox = QHBoxLayout()
        add_hbox.setSpacing(ROW_SPACING)
        add_spacer = QLabel("")
        add_spacer.setFixedWidth(INDEX_WIDTH)
        self.add_path_button = QPushButton("+ Add destination")
        self.add_path_button.setToolTip(TOOLTIPS["add"])
        self.add_path_button.setStyleSheet(Style.BTN_SMALL)
        self.add_path_button.clicked.connect(lambda: self.add_row("", ""))
        add_hbox.addWidget(add_spacer)
        add_hbox.addWidget(self.add_path_button)
        add_hbox.addStretch()
        self.layout.addLayout(add_hbox)

        self.layout.addSpacing(10)
        self.layout.addWidget(self.build_separator())
        self.layout.addSpacing(10)

        # --- Pie ----------------------------------------------------------
        buttons_layout = QHBoxLayout()
        version = get_tool_version()
        version_label = QLabel(
            "Media Manager v%s  ·  Developed by Lega" % version
            if version
            else "Media Manager  ·  Developed by Lega"
        )
        version_label.setStyleSheet("color: %s;" % Color.TEXT_DIM)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(Style.BTN_SECONDARY)
        self.cancel_button.setFixedHeight(Metric.BUTTON_HEIGHT)
        self.cancel_button.clicked.connect(self.close)
        self.save_button = QPushButton("Save Settings")
        self.save_button.setStyleSheet(Style.BTN_PRIMARY)
        self.save_button.setFixedHeight(Metric.BUTTON_HEIGHT)
        self.save_button.clicked.connect(self.save_settings)

        buttons_layout.addWidget(version_label)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        self.layout.addLayout(buttons_layout)

    def build_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator

    def add_row(self, name, path):
        row = DestinationRow(len(self.rows) + 1, name, path, self.remove_row)
        self.rows_layout.addWidget(row)
        self.rows.append(row)
        return row

    def remove_row(self, row):
        # La fila llega por referencia y no por indice: con indices habia que
        # reconectar el boton de cada fila despues de cada borrado, y bastaba
        # con que uno quedara viejo para borrar el destino equivocado.
        if row not in self.rows:
            return
        self.rows.remove(row)
        self.rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()

        for posicion, restante in enumerate(self.rows, start=1):
            restante.set_index(posicion)

        self.adjustSize()

    def collect_settings(self):
        """Lo que hay en pantalla, en el formato del .ini."""
        data = {"Folder scan depth": self.depth_field.value()}
        for posicion, row in enumerate(self.rows, start=1):
            data[f"copy_{posicion}_button_text"] = row.name()
            data[f"copy_{posicion}_subdirectory"] = row.path()
        return data

    def save_settings(self):
        self.settings_data = self.collect_settings()

        debug_print("\n\nGuardando la siguiente informacion en el .ini:")
        debug_print(self.format_ini_output())

        # Se escribe en la carpeta de datos del usuario, no adentro del pack:
        # el instalador reemplaza la carpeta del pack en cada actualizacion.
        ini_path = get_write_path()
        if not ini_path:
            QMessageBox.warning(
                self,
                "Settings",
                "The settings could not be saved: no writable config folder was found.",
            )
            return

        if not write_ini(ini_path, self.format_ini_output()):
            QMessageBox.warning(
                self,
                "Settings",
                "The settings could not be saved to:\n%s" % ini_path,
            )
            return

        debug_print(f"Configuracion guardada en {ini_path}")
        self.settings_saved.emit()
        self.close()

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

        # Con newline final: el .ini esta trackeado y sin el, cada guardado
        # deja un '\ No newline at end of file' en el diff.
        return ini_representation.strip() + "\n"

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
