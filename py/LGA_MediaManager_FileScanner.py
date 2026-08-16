"""
_______________________________________________________________________

  LGA_MediaManager_FileScanner v2.15 | Lega

  Escaneo del proyecto, tabla de medias y relink de archivos offline.

  v2.15: La letra de la tabla pasa a pixeles, la fila de botones lleva
         separacion propia y se van el boton '>' y los seis controles
         que desplegaba.

  v2.14: Los botones y los tooltips salen del modulo de estilo y el
         fondo de la ventana pasa al de la paleta. La hoja de la tabla
         deja de pintar la seleccion: de eso se encarga el delegado,
         que respeta el color propio de la columna Status.

  v2.13: El relink rellena con ceros el frame al reconstruir el nombre
         de la secuencia, y si ese frame no esta en la carpeta nueva
         cae a un patron que acepta cualquier frame de la misma
         secuencia. El estado relinkeado se compara con commonpath
         normalizado y la fila queda deseleccionada para que se vea
         el fondo del estado y no el de la seleccion.
_______________________________________________________________________

"""

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore

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
QSpinBox = QtWidgets.QSpinBox
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
import nuke
import os
import re
import subprocess
import time
import shutil
import sys
import configparser
import logging
QThreadPool = QtCore.QThreadPool

from LGA_MediaManager_logging import configure_logger, debug_print
from LGA_UI_Style_ToolPack import Color, Metric, Style

try:
    from LGA_tooltip_helper import apply_tooltip_stylesheet
except ImportError:
    # La ventana funciona igual sin el helper; solo pierde el look estandar.
    def apply_tooltip_stylesheet(target=None):
        pass


# Los tooltips van en castellano y salen de aca, no hardcodeados en el widget,
# para que la migracion a bilingue sea un cambio de datos.
TOOLTIPS = {
    "go_to_read": "Selecciona en el Node Graph el Read que usa esta media",
    "explorer": "Abre la carpeta de la media en el explorador de archivos",
    "relink": "Vuelve a apuntar el Read offline al archivo, buscandolo en la carpeta que elijas",
    "delete": "Manda a la papelera los archivos seleccionados",
    "copy_to": "Copia lo seleccionado a una carpeta del shot y reapunta el Read",
    "settings": "Abre los ajustes del Media Manager",
    "version": "Lega | 2023",
}

# Separacion en pixeles entre los botones de la fila de herramientas. Vive aca
# y no en Metric del modulo de estilo porque es un valor a tunear a ojo: cuando
# quede firme conviene subirlo al modulo, que es donde van las medidas.
BUTTON_SPACING = 12

# Tamano de letra de la tabla, en PIXELES. Iba en pt, que Qt convierte con el
# DPI logico del sistema: 72 en macOS y 96 en Windows, o sea que el mismo
# numero daba una letra un tercio mas chica en Mac. En px mide igual en las dos.
# 13 es el equivalente de los 10pt que se veian bien en Windows.
DEFAULT_FONT_SIZE = 13


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

# Importar clases auxiliares desde utils
from LGA_MediaManager_utils import (
    ScannerWorker,
    TransparentTextDelegate,
    LoadingWindow,
    CopyThread,
    DeleteThread,
)

# Importar SettingsWindow desde settings
from LGA_MediaManager_settings import SettingsWindow


class FileScanner(QWidget):
    def __init__(self, parent=None):
        super(FileScanner, self).__init__(parent)  # Inicializar la clase base primero

        # Comprobar si el script de Nuke está guardado
        if not nuke.root().name() or nuke.root().name() == "Root":
            self.initialization_successful = False
            return  # Finalizar la inicialización aquí sin crear ninguna ventana

        # Inicializar atributos básicos primero
        self.matched_reads = []
        self.font_size = DEFAULT_FONT_SIZE
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

        # Fondo de la ventana. Va por paleta y no por hoja de estilo a proposito:
        # una regla 'QWidget { background-color }' se propaga a todos los hijos y
        # les come la caja a los spinboxes y a los checkbox nativos. La paleta la
        # heredan igual, pero cada control la usa para el rol que le corresponde.
        self.setAutoFillBackground(True)
        window_palette = self.palette()
        window_palette.setColor(QPalette.Window, QColor(Color.WINDOW))
        self.setPalette(window_palette)

        # Crea y configura el status_label
        # self.status_label = QLabel("")
        # self.layout.addWidget(self.status_label)

        # Crear layout para botones a la izquierda
        left_buttons_layout = QHBoxLayout()
        left_buttons_layout.setSpacing(BUTTON_SPACING)

        apply_tooltip_stylesheet(self)

        # Crear botones Reveal, Delete, y Go to Read y agregarlos despues del checkbox
        # Ninguno es el boton de accion de la ventana -son una fila de herramientas,
        # cualquiera es valido segun lo que este seleccionado- asi que van todos
        # secundarios y no hay violeta: marcar uno seria decir que Enter lo ejecuta.
        self.go_to_read_button = QPushButton("&Go to Read")
        self.go_to_read_button.setToolTip(TOOLTIPS["go_to_read"])
        self.reveal_button = QPushButton("&Explorer")
        self.reveal_button.setToolTip(TOOLTIPS["explorer"])
        self.delete_button = QPushButton("&Delete")
        self.delete_button.setToolTip(TOOLTIPS["delete"])
        self.relink_button = QPushButton("Re&link")
        self.relink_button.setToolTip(TOOLTIPS["relink"])

        for button in (
            self.go_to_read_button,
            self.reveal_button,
            self.delete_button,
            self.relink_button,
        ):
            button.setStyleSheet(Style.BTN_SECONDARY)
            button.setFixedHeight(Metric.BUTTON_HEIGHT)

        self.relink_button.clicked.connect(self.relink)
        self.reveal_button.clicked.connect(self.reveal_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.go_to_read_button.clicked.connect(self.go_to_read)

        # Crear el boton 'Copy to...'
        self.copy_button = QToolButton(self)
        self.copy_button.setText("&Copy to")
        self.copy_button.setPopupMode(QToolButton.InstantPopup)
        self.copy_menu = QMenu(self)
        self.copy_button.setToolTip(TOOLTIPS["copy_to"])
        # Mismo look que los otros botones de la fila. El estilo se deriva del
        # secundario en vez de escribir uno propio: BTN_SECONDARY apunta a
        # QPushButton y este es un QToolButton, que no lo recibiria.
        self.copy_button.setStyleSheet(
            Style.BTN_SECONDARY.replace("QPushButton", "QToolButton")
            + "QToolButton::menu-indicator { image: none; }"
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

        # Todos los botones de la fila miden lo mismo, y esa medida sale del texto
        # mas largo: con un ancho fijo a ojo, el padding del estilo se comia la
        # primera letra de "Go to Read".
        self.copy_button.setFixedHeight(Metric.BUTTON_HEIGHT)
        self.copy_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_buttons = (
            self.go_to_read_button,
            self.reveal_button,
            self.relink_button,
            self.delete_button,
            self.copy_button,
        )
        button_width = max(100, max(b.sizeHint().width() for b in row_buttons))
        for button in row_buttons:
            button.setFixedWidth(button_width)

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

        # Crear el layout principal que incluye todos los layouts de botones
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.addLayout(left_buttons_layout)

        # Espacio flexible que empuja el engranaje y la version hacia la derecha
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
        self.settings_button.setToolTip(TOOLTIPS["settings"])
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
        version_label = QLabel("v2.24  ")
        version_label.setToolTip(TOOLTIPS["version"])
        version_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )  # Alineacion a la derecha y verticalmente centrado

        # Agregar el engranaje y la version al final de la fila
        main_buttons_layout.addWidget(self.settings_button)
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
        self.toggle_columns(False)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        # Cambiar el color de fondo de la tabla y el tamano de la fuente.
        # La seleccion se deja transparente a proposito: si la hoja define un
        # background para 'item:selected' le gana al setBackground() del item y a
        # la paleta del delegado, y la columna Status pierde su color justo cuando
        # esta seleccionada. Del color de la seleccion se encarga
        # TransparentTextDelegate, que sabe que celdas tienen color propio.
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {Color.SURFACE};
                font-size: {self.font_size}px;
            }}
            QTableWidget::item:selected {{
                background-color: transparent;
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
        self.logger.debug("[Altura] ===============================================")
        self.logger.debug("[Altura] Iniciando adjust_window_size()")
        self.logger.debug(f"[Altura] Filas en tabla: {self.table.rowCount()}")
        self.logger.debug(f"[Altura] Columnas en tabla: {self.table.columnCount()}")

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

        self.logger.debug(
            f"[Altura] Ancho header vertical + margen: {self.table.verticalHeader().width() + 4}"
        )
        for i in range(self.table.columnCount()):
            self.logger.debug(
                f"[Altura] Ancho columna {i}: {self.table.columnWidth(i) + 4}"
            )
        self.logger.debug(
            f"[Altura] Ancho reservado para scroll vertical: {self.table.verticalScrollBar().width()}"
        )
        self.logger.debug(f"[Altura] Ancho total calculado: {width}")

        # Calcular la altura basada en la altura de los headers y las filas
        height = self.table.horizontalHeader().height() + 4
        self.logger.debug(
            f"[Altura] Alto header horizontal + margen: {self.table.horizontalHeader().height() + 4}"
        )
        for i in range(self.table.rowCount()):
            row_height = self.table.rowHeight(i)
            height += row_height
            self.logger.debug(f"[Altura] Alto fila {i}: {row_height}")

        horizontal_scrollbar = self.table.horizontalScrollBar()
        horizontal_scrollbar_height = horizontal_scrollbar.height()
        reserve_horizontal_scrollbar = horizontal_scrollbar.isVisible()
        reserved_horizontal_scrollbar_height = (
            horizontal_scrollbar_height if reserve_horizontal_scrollbar else 0
        )
        height += reserved_horizontal_scrollbar_height
        self.logger.debug(
            f"[Altura] Alto reservado para scroll horizontal: {horizontal_scrollbar_height}"
        )
        self.logger.debug(
            f"[Altura] Scroll horizontal visible al calcular: {reserve_horizontal_scrollbar}"
        )
        self.logger.debug(
            f"[Altura] Alto realmente sumado por scroll horizontal: {reserved_horizontal_scrollbar_height}"
        )

        # Agregar el alto del layout de botones al tamano de la ventana
        top_layout_height = self.layout.itemAt(0).sizeHint().height()
        height += top_layout_height
        self.logger.debug(f"[Altura] Alto layout superior: {top_layout_height}")

        layout_margins = self.layout.contentsMargins()
        margins_height = layout_margins.top() + layout_margins.bottom()
        spacing_total = self.layout.spacing()
        height += margins_height
        height += spacing_total
        self.logger.debug(
            f"[Altura] Margenes layout principal top/bottom: {layout_margins.top()}/{layout_margins.bottom()} total={margins_height}"
        )
        self.logger.debug(f"[Altura] Spacing layout principal: {spacing_total}")
        self.logger.debug(f"[Altura] Alto total calculado antes del limite: {height}")

        # Obtener la altura del monitor
        screen_height = QApplication.primaryScreen().geometry().height()
        available_screen_height = QApplication.primaryScreen().availableGeometry().height()
        self.logger.debug(f"[Altura] Alto total de pantalla: {screen_height}")
        self.logger.debug(f"[Altura] Alto disponible de pantalla: {available_screen_height}")

        # Establecer un limite para la altura, por ejemplo, el 80% de la altura del monitor
        max_height = screen_height * 0.8
        self.logger.debug(f"[Altura] Alto maximo permitido (80%): {max_height}")

        # Usar el menor entre la altura calculada y el maximo permitido
        final_height = min(height, max_height)
        self.logger.debug(f"[Altura] Alto final aplicado: {final_height}")
        self.logger.debug(f"[Altura] El limite maximo recorto el alto: {height > max_height}")

        # Reactivar el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el tamano de la ventana
        self.resize(width, final_height)
        QApplication.processEvents()
        self.logger.debug(
            "[Altura] Resize aplicado. Se agenda validacion post-layout para medir geometria real."
        )
        QTimer.singleShot(
            0,
            lambda: self._log_height_post_layout(
                calculated_width=width,
                calculated_height=height,
                final_height=final_height,
                max_height=max_height,
                reserved_horizontal_scrollbar=reserve_horizontal_scrollbar,
                reserved_horizontal_scrollbar_height=reserved_horizontal_scrollbar_height,
            ),
        )

    def _log_height_post_layout(
        self,
        calculated_width,
        calculated_height,
        final_height,
        max_height,
        reserved_horizontal_scrollbar,
        reserved_horizontal_scrollbar_height,
    ):
        vertical_scrollbar = self.table.verticalScrollBar()
        horizontal_scrollbar = self.table.horizontalScrollBar()
        vertical_scroll_visible = vertical_scrollbar.isVisible()
        horizontal_scroll_visible = horizontal_scrollbar.isVisible()
        window_rect = self.rect()
        contents_rect = self.contentsRect()
        table_geometry = self.table.geometry()
        viewport_geometry = self.table.viewport().geometry()

        self.logger.debug("[Altura] ---------- Validacion post-layout ----------")
        self.logger.debug(
            f"[Altura] Geometria final ventana: width={self.width()} height={self.height()}"
        )
        self.logger.debug(
            f"[Altura] rect ventana: width={window_rect.width()} height={window_rect.height()}"
        )
        self.logger.debug(
            f"[Altura] contentsRect ventana: width={contents_rect.width()} height={contents_rect.height()}"
        )
        self.logger.debug(
            f"[Altura] sizeHint ventana: width={self.sizeHint().width()} height={self.sizeHint().height()}"
        )
        self.logger.debug(
            f"[Altura] minimumSizeHint ventana: width={self.minimumSizeHint().width()} height={self.minimumSizeHint().height()}"
        )
        self.logger.debug(
            f"[Altura] Geometria tabla: x={table_geometry.x()} y={table_geometry.y()} width={table_geometry.width()} height={table_geometry.height()}"
        )
        self.logger.debug(
            f"[Altura] Geometria viewport tabla: x={viewport_geometry.x()} y={viewport_geometry.y()} width={viewport_geometry.width()} height={viewport_geometry.height()}"
        )
        self.logger.debug(
            f"[Altura] Scroll vertical visible: {vertical_scroll_visible} max={vertical_scrollbar.maximum()} pageStep={vertical_scrollbar.pageStep()}"
        )
        self.logger.debug(
            f"[Altura] Scroll horizontal visible: {horizontal_scroll_visible} max={horizontal_scrollbar.maximum()} pageStep={horizontal_scrollbar.pageStep()}"
        )
        self.logger.debug(
            f"[Altura] Resumen calculado: width={calculated_width} height={calculated_height} final_height={final_height} max_height={max_height}"
        )
        self.logger.debug(
            f"[Altura] Resumen scroll horizontal reservado: visible_al_calcular={reserved_horizontal_scrollbar} alto_sumado={reserved_horizontal_scrollbar_height}"
        )
        self.logger.debug(
            f"[Altura] Analisis: alto calculado suficiente sin scroll vertical = {not vertical_scroll_visible}"
        )
        self.logger.debug(
            f"[Altura] Analisis: alto final coincide con alto calculado = {final_height == calculated_height}"
        )
        self.logger.debug("[Altura] ===============================================")

    def toggle_columns(self, state):

        is_visible = bool(state)
        self.table.setColumnHidden(3, not is_visible)  # Columna Folder_Delete
        self.table.setColumnHidden(4, not is_visible)  # Columna Sequence
        self.adjust_window_size()

    def reorder_by_status(self):
        status_column_index = (
            2  # Asegurate de que este es el indice correcto para la columna de Estado
        )
        self.table.sortByColumn(status_column_index, Qt.AscendingOrder)

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

            # Obtener los nodos Read y CopyCat actualmente seleccionados en Nuke
            selected_reads = [
                node.name()
                for node in nuke.selectedNodes()
                if node.Class()
                in ["Read", "CopyCat", "AudioRead", "ReadGeo", "DeepRead"]
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

    def build_search_patterns(self, file_name):
        """
        Arma los dos criterios de busqueda para el relink a partir del texto de la tabla.

        Devuelve (exact_name, sequence_pattern, first_frame):
          - exact_name: nombre exacto del primer frame, con el padding correcto.
          - sequence_pattern: regex que acepta cualquier frame de la misma secuencia.
          - first_frame: primer frame declarado en la tabla (sin padding).
        """
        base_name = os.path.basename(file_name).split("[")[0]
        hashes_match = re.search(r"#+", base_name)

        if not hashes_match:
            # Archivo unico: el nombre ya viene completo
            return os.path.basename(file_name).lower(), None, ""

        hashes = hashes_match.group(0)
        prefix, suffix = base_name.split(hashes, 1)

        # Criterio primario: reconstruir el nombre exacto del primer frame.
        # El rango de un Read offline viene sin padding (ej. [0-530]), asi que hay
        # que rellenarlo al ancho de los '#' para que coincida con el archivo real.
        exact_name = None
        first_frame = ""
        frame_range = re.search(r"\[(\d+)-\d+\]", file_name)
        if frame_range:
            first_frame = frame_range.group(1)
            exact_name = (prefix + first_frame.zfill(len(hashes)) + suffix).lower()

        # Criterio de respaldo: mismo nombre y mismo padding, cualquier numero de frame.
        # Cubre el caso en que el frame inicial guardado en el nodo no existe en la
        # carpeta nueva (secuencia recopiada con otro rango, primer frame faltante, etc).
        sequence_pattern = re.compile(
            re.escape(prefix) + r"\d{" + str(len(hashes)) + r"}" + re.escape(suffix) + r"$",
            re.IGNORECASE,
        )

        return exact_name, sequence_pattern, first_frame

    def search_file_in_directory(self, directory, file_name):
        self.loading_window = LoadingWindow("Searching...", self)
        self.loading_window.show()
        QApplication.processEvents()

        exact_name, sequence_pattern, first_frame = self.build_search_patterns(file_name)

        nuke.executeInMainThread(
            lambda: self.logger.debug(
                f"\nBuscando el archivo: {exact_name} en {directory}"
                f" (patron de respaldo: {sequence_pattern.pattern if sequence_pattern else 'ninguno'})"
            )
        )

        fallback_path = None

        for root, dirs, files in os.walk(directory):
            if "$RECYCLE.BIN" in [
                os.path.basename(dir)
                for dir in os.path.normpath(root).split(os.path.sep)
            ]:
                nuke.executeInMainThread(lambda: self.logger.debug(f"Skipping {root}"))
                continue

            for file in files:
                if exact_name and file.lower() == exact_name:
                    new_file_path = os.path.join(root, file)
                    nuke.executeInMainThread(
                        lambda: self.logger.debug(
                            f"Archivo encontrado (match exacto): {new_file_path}"
                        )
                    )
                    self.update_read_node(file_name, new_file_path, first_frame)
                    self.loading_window.close()
                    return

                # Se guarda el primer candidato del patron, pero se sigue recorriendo
                # por si mas adelante aparece el match exacto, que tiene prioridad
                if (
                    fallback_path is None
                    and sequence_pattern is not None
                    and sequence_pattern.match(file)
                ):
                    fallback_path = os.path.join(root, file)

        if fallback_path:
            nuke.executeInMainThread(
                lambda: self.logger.debug(
                    f"Archivo encontrado (match por patron de secuencia): {fallback_path}"
                )
            )
            self.update_read_node(file_name, fallback_path, first_frame)
            self.loading_window.close()
            return

        nuke.executeInMainThread(
            lambda: self.logger.debug("No se encontro ningun archivo compatible")
        )
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

                    # Verificar si la nueva ruta esta dentro de la carpeta del proyecto.
                    # Se usa commonpath sobre rutas normalizadas: commonprefix compara
                    # caracter por caracter y falla por mayusculas o por carpetas
                    # hermanas con el mismo prefijo (proj vs proj2).
                    normi_new_directory = normalize_path_for_comparison(
                        os.path.dirname(new_file_path)
                    )
                    normi_project_folder = normalize_path_for_comparison(
                        self.project_folder
                    )
                    try:
                        common_path = os.path.commonpath(
                            [normi_new_directory, normi_project_folder]
                        )
                    except ValueError:
                        # Rutas en unidades distintas: no hay path comun posible
                        common_path = ""

                    if common_path.replace("\\", "/") == normi_project_folder:
                        # Actualizar el estado a "OK" y cambiar el color correspondiente
                        status_item.setBackground(QColor("#25321e"))
                        status_item.setText("OK")

                    else:
                        # Actualizar el estado a "Outside" y cambiar el color correspondiente
                        status_item.setBackground(QColor("#321e1e"))
                        status_item.setText("Outside")

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

        # Obtener el logger configurado
        logger = configure_logger()
        logger.debug(f"\n=== INICIO search_unmatched_reads ===")
        logger.debug(f"Total read files a procesar: {len(all_read_files)}")
        logger.debug(f"Nodos ya matched: {self.matched_reads}")

        # FILTRO PARA COPYCAT: Crear lista de checkpointFile paths para filtrarlos
        copycat_checkpoint_files = set()
        copycat_nodes = nuke.executeInMainThreadWithResult(
            lambda: nuke.allNodes("CopyCat")
        )
        for node in copycat_nodes:
            if node.knob("checkpointFile"):
                checkpoint_file = node["checkpointFile"].getValue().replace("\\", "/")
                if checkpoint_file:
                    copycat_checkpoint_files.add(os.path.normpath(checkpoint_file))

        logger.debug(
            f"[READ_COPYCAT] CheckpointFiles encontrados para filtrar: {copycat_checkpoint_files}"
        )

        for read_path, nodes in all_read_files.items():
            read_path = os.path.normpath(read_path)
            unmatched_nodes = [node for node in nodes if node not in self.matched_reads]
            logger.debug(f"\nProcesando read_path: {read_path}")
            logger.debug(f"  - Nodos del read: {nodes}")
            logger.debug(f"  - Nodos unmatched: {unmatched_nodes}")

            # FILTRO PARA COPYCAT: Si el read_path es una carpeta (dataDirectory) y no existe como archivo,
            # no lo agregamos a unmatched_reads porque es solo para matching, no para mostrar en tabla
            if os.path.isdir(read_path) and not os.path.isfile(read_path):
                logger.debug(
                    f"[READ_COPYCAT] Saltando carpeta dataDirectory (no es archivo): {read_path}"
                )
                continue

            # FILTRO PARA COPYCAT: Si el read_path es un checkpointFile, no lo mostramos en tabla
            if read_path in copycat_checkpoint_files:
                logger.debug(
                    f"[READ_COPYCAT] Saltando checkpointFile (solo para referencia): {read_path}"
                )
                continue

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
                    logger.debug(
                        f"  --> AGREGANDO nodo {node} al to_add como unmatched"
                    )
                    logger.debug(f"      Ruta: {read_path}")
                    logger.debug(f"      Is sequence: {is_sequence}")
                    logger.debug(f"      Frame range: {frame_range}")
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

        logger.debug(f"\n=== FIN search_unmatched_reads ===")
        logger.debug(f"Total archivos para agregar: {len(to_add)}")
        for i, (
            file_path,
            read_files_dict,
            is_seq,
            frame_range,
            is_unmatched,
            is_deletable,
            seq_state,
        ) in enumerate(to_add):
            logger.debug(
                f"[{i+1}/{len(to_add)}] {file_path} - Is_seq: {is_seq} - Range: {frame_range}"
            )

        return to_add  # En lugar de llamar a add_file_to_table, devuelve los datos
        self.adjust_window_size()

    def get_read_files(self):
        read_files = {}
        node_types = ["Read", "AudioRead", "ReadGeo", "DeepRead"]
        
        # Importar la función para resolver rutas relativas
        from LGA_MediaManager_utils import resolve_relative_path
        
        # Obtener el directorio del proyecto para resolver rutas relativas
        project_path = nuke.root().name()
        if project_path:
            project_folder = os.path.dirname(project_path)
        else:
            project_folder = ""

        # Procesar nodos Read y similares (usando knob 'file')
        for node_type in node_types:
            nodes = nuke.executeInMainThreadWithResult(lambda: nuke.allNodes(node_type))
            for node in nodes:
                file_path = node["file"].getValue().replace("\\", "/")
                # Resolver ruta relativa a absoluta
                resolved_path = resolve_relative_path(file_path, project_folder)
                if resolved_path not in read_files:
                    read_files[resolved_path] = []
                read_files[resolved_path].append(node.name())

        # Procesar nodos CopyCat (usando knobs 'dataDirectory' y 'checkpointFile')
        copycat_nodes = nuke.executeInMainThreadWithResult(
            lambda: nuke.allNodes("CopyCat")
        )
        logger = configure_logger()
        logger.debug(
            f"[READ_COPYCAT] Encontrados {len(copycat_nodes)} nodos CopyCat en el proyecto"
        )

        for node in copycat_nodes:
            logger.debug(f"[READ_COPYCAT] Procesando nodo CopyCat: {node.name()}")

            # Obtener dataDirectory si existe
            if node.knob("dataDirectory"):
                data_dir = node["dataDirectory"].getValue().replace("\\", "/")
                # Resolver ruta relativa a absoluta
                resolved_data_dir = resolve_relative_path(data_dir, project_folder)
                logger.debug(f"[READ_COPYCAT]   - dataDirectory original: '{data_dir}'")
                logger.debug(f"[READ_COPYCAT]   - dataDirectory resuelto: '{resolved_data_dir}'")
                if resolved_data_dir and resolved_data_dir not in read_files:
                    read_files[resolved_data_dir] = []
                if resolved_data_dir:
                    read_files[resolved_data_dir].append(node.name())
                    logger.debug(
                        f"[READ_COPYCAT]   - Agregado dataDirectory al read_files: {resolved_data_dir} -> {node.name()}"
                    )
            else:
                logger.debug(f"[READ_COPYCAT]   - Sin knob dataDirectory")

            # Obtener checkpointFile si existe
            if node.knob("checkpointFile"):
                checkpoint_file = node["checkpointFile"].getValue().replace("\\", "/")
                # Resolver ruta relativa a absoluta
                resolved_checkpoint = resolve_relative_path(checkpoint_file, project_folder)
                logger.debug(f"[READ_COPYCAT]   - checkpointFile original: '{checkpoint_file}'")
                logger.debug(f"[READ_COPYCAT]   - checkpointFile resuelto: '{resolved_checkpoint}'")
                if resolved_checkpoint and resolved_checkpoint not in read_files:
                    read_files[resolved_checkpoint] = []
                if resolved_checkpoint:
                    read_files[resolved_checkpoint].append(node.name())
                    logger.debug(
                        f"[READ_COPYCAT]   - Agregado checkpointFile al read_files: {resolved_checkpoint} -> {node.name()}"
                    )
            else:
                logger.debug(f"[READ_COPYCAT]   - Sin knob checkpointFile")

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
        self.logger.debug(
            f"\n=== on_files_found: Agregando {len(files_data)} archivos de find_files ==="
        )
        self.add_file_to_table(files_data)
        self.logger.debug(
            f"\n=== on_files_found: Agregando {len(unmatched_reads_data)} archivos de unmatched_reads ==="
        )
        self.add_file_to_table(unmatched_reads_data)

    def add_file_to_table(self, files_data):
        # NUEVA SOLUCION QUIRURGICA: Deduplicación inteligente al inicio de add_file_to_table

        self.logger.debug(
            f"\n[FIX!!!] ===== ADD_FILE_TO_TABLE INICIADO (FileScanner.py) ====="
        )
        self.logger.debug(
            f"[FIX!!!] Recibiendo {len(files_data)} archivos para procesar"
        )

        # Crear un registro de archivos ya procesados en esta sesión
        if not hasattr(self, "_processed_files_session"):
            self._processed_files_session = set()
            self.logger.debug(f"[FIX!!!] Creando nuevo _processed_files_session")
        else:
            self.logger.debug(
                f"[FIX!!!] Usando _processed_files_session existente con {len(self._processed_files_session)} archivos"
            )

        # Filtrar duplicados antes de procesar
        original_count = len(files_data)
        unique_files_data = []
        duplicates_removed = 0

        for file_data in files_data:
            file_path = file_data[0]  # El primer elemento es el path
            normalized_path = normalize_path_for_comparison(file_path)

            if normalized_path not in self._processed_files_session:
                self._processed_files_session.add(normalized_path)
                unique_files_data.append(file_data)

                # Log para EditRef cuando se agrega
                if "EditRef_v01.mov" in file_path:
                    self.logger.debug(f"[FIX!!!] EditRef ACEPTADO: {file_path}")
            else:
                duplicates_removed += 1
                # Log para EditRef cuando se rechaza por duplicado
                if "EditRef_v01.mov" in file_path:
                    self.logger.debug(
                        f"[FIX!!!] EditRef RECHAZADO (duplicado): {file_path}"
                    )

        # Usar los archivos únicos para el procesamiento
        files_data = unique_files_data

        self.logger.debug(
            f"\n[FIX!!!] DEDUPLICACION: {original_count} → {len(files_data)} archivos (eliminados: {duplicates_removed})"
        )

        # Agrega los archivos a la tabla y determina su estado en relacion con los nodos Read
        end_time = time.time()
        # logging.info("")
        # logging.info("add_file_to_table execution time start: ", end_time - start_time, "seconds")

        self.logger.debug(
            f"\n>> add_file_to_table: Procesando {len(files_data)} archivos únicos"
        )

        for i, file_data in enumerate(files_data):
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

            self.logger.debug(f"\n[ARCHIVO {i+1}/{len(files_data)}] Agregando a tabla:")
            self.logger.debug(f"  - File path: {file_path}")
            self.logger.debug(f"  - Is sequence: {is_sequence}")
            self.logger.debug(f"  - Frame range: {frame_range}")
            self.logger.debug(f"  - Is unmatched read: {is_unmatched_read}")
            self.logger.debug(f"  - Is folder deletable: {is_folder_deletable}")
            self.logger.debug(f"  - Row position: {row_position}")

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
                # Convertir %0Xd a # en las claves de read_files y normalizar para comparacion
                normalized_read_files = {}
                for path, nodes in read_files.items():
                    new_key = re.sub(r"%0(\d+)d", lambda m: "#" * int(m.group(1)), path)
                    # Usar la funcion de normalizacion centralizada
                    new_key = normalize_path_for_comparison(new_key)
                    normalized_read_files[new_key] = nodes

            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.logger.debug(f"  *** FILA INSERTADA EN POSICION {row_position} ***")

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
                f"color: rgb(200, 200, 200); font-size: {self.font_size}px;"
            )
            self.table.setCellWidget(row_position, 0, label)

            if not is_unmatched_read:
                # Manejo de los archivos del find_files
                status = "-"
                state = "Unused"
                # Usar la funcion de normalizacion centralizada
                normalized_read_files = {
                    normalize_path_for_comparison(path): nodes
                    for path, nodes in read_files.items()
                }
                status_color = "#32311e"

                # Normalizar el file_path encontrado para comparacion
                normalized_file_path_for_comparison = normalize_path_for_comparison(
                    file_path
                )

                if is_sequence:
                    for read_path, nodes in normalized_read_files.items():
                        if self.is_sequence_match(
                            normalized_file_path_for_comparison, read_path, frame_range
                        ):
                            status = ", ".join(nodes)
                            state = "OK"
                            status_color = "#25321e"
                            self.matched_reads.extend(nodes)
                            break
                else:
                    for read_path, nodes in normalized_read_files.items():
                        if normalized_file_path_for_comparison == read_path:
                            status = ", ".join(nodes)
                            state = "OK"
                            status_color = "#25321e"
                            self.matched_reads.extend(nodes)
                            break

                # Si no se encontro match exacto, verificar matching por carpeta para CopyCat
                if state == "Unused":
                    file_directory = normalize_path_for_comparison(
                        os.path.dirname(file_path)
                    )
                    self.logger.debug(
                        f"[READ_COPYCAT] Verificando matching por carpeta para archivo: {file_path}"
                    )
                    self.logger.debug(
                        f"[READ_COPYCAT]   - Directorio del archivo: {file_directory}"
                    )

                    for read_path, nodes in normalized_read_files.items():
                        # Verificar si read_path es una carpeta (para CopyCat dataDirectory)
                        read_path_normalized = normalize_path_for_comparison(read_path)
                        self.logger.debug(
                            f"[READ_COPYCAT]   - Comparando con read_path: {read_path_normalized}"
                        )

                        # Normalizar ambas rutas eliminando barras finales para comparacion consistente
                        file_dir_clean = file_directory.rstrip("/")
                        read_path_clean = read_path_normalized.rstrip("/")

                        self.logger.debug(
                            f"[READ_COPYCAT]   - Comparacion normalizada: '{file_dir_clean}' vs '{read_path_clean}'"
                        )

                        if (
                            file_dir_clean == read_path_clean
                            or file_dir_clean.startswith(read_path_clean + "/")
                        ):
                            status = ", ".join(nodes)
                            state = "OK"
                            status_color = "#25321e"
                            self.matched_reads.extend(nodes)
                            self.logger.debug(
                                f"[READ_COPYCAT]   - ¡MATCH ENCONTRADO! Archivo {file_path} asociado a nodo(s): {nodes}"
                            )
                            break

                    if state == "Unused":
                        self.logger.debug(
                            f"[READ_COPYCAT]   - Sin match por carpeta para: {file_path}"
                        )

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

                # Normalizar el file_path para la comparacion
                normalized_file_path_for_unmatched = normalize_path_for_comparison(
                    file_path
                )
                if (
                    normalized_file_path_for_unmatched in normalized_read_files
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
                            ", ".join(
                                normalized_read_files[
                                    normalized_file_path_for_unmatched
                                ]
                            )
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
                                ", ".join(
                                    normalized_read_files[
                                        normalized_file_path_for_unmatched
                                    ]
                                )
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
                                ", ".join(
                                    normalized_read_files[
                                        normalized_file_path_for_unmatched
                                    ]
                                )
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
                # Usar la funcion de normalizacion centralizada
                file_path = normalize_path_for_comparison(
                    self.table.item(row, 0).text()
                )
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
        # Usar la funcion de normalizacion centralizada para la comparacion
        return normalize_path_for_comparison(
            sequence_base_path
        ) == normalize_path_for_comparison(read_base_path)

    def normalize_sequence_path(self, file_path):
        # Normaliza la ruta del archivo para secuencias, reemplazando los digitos al final por '#'
        directory, filename = os.path.split(file_path)
        base, ext = os.path.splitext(filename)
        if any(ext.lower() == e for e in self.sequence_extensions):
            base = re.sub(r"\d+$", lambda m: "#" * len(m.group()), base)
        normalized_path = os.path.join(directory, base + ext)
        # Usar la funcion de normalizacion centralizada
        return normalize_path_for_comparison(normalized_path)

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

            level = self.project_folder_depth
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
