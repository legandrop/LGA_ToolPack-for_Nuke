"""
________________________________________________________________________

  LGA_RnW_ColorSpace_Favs v1.44 | Lega
  Tool for applying OCIO color spaces to selected Read and Write nodes
________________________________________________________________________

"""

from qt_compat import QtWidgets, QtCore, QtGui

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QHeaderView = QtWidgets.QHeaderView
QPushButton = QtWidgets.QPushButton
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QComboBox = QtWidgets.QComboBox
QSizePolicy = QtWidgets.QSizePolicy
Qt = QtCore.Qt
QRect = QtCore.QRect
QCursor = QtGui.QCursor
QPalette = QtGui.QPalette
QColor = QtGui.QColor
QFont = QtGui.QFont
import configparser
import nuke
import os
import shutil
import typing  # Importar typing para compatibilidad < 3.10
import platform

# Variable global para controlar el debug
DEBUG = False  # Poner en False para desactivar los mensajes de debug


def debug_print(*message):
    if DEBUG:
        print(*message)


def get_user_config_dir():
    """
    Obtiene el directorio de configuracion del usuario segun el sistema operativo.
    Windows: %APPDATA%
    Mac: ~/Library/Application Support
    """
    system = platform.system()
    if system == "Windows":
        config_path = os.getenv("APPDATA")
        if not config_path:
            debug_print("Error: No se pudo encontrar la variable de entorno APPDATA.")
            return None
    elif system == "Darwin":  # macOS
        config_path = os.path.expanduser("~/Library/Application Support")
    else:
        # Para otros sistemas, usar el directorio home como fallback
        config_path = os.path.expanduser("~/.config")
        debug_print(
            f"Sistema no reconocido ({system}), usando ~/.config como fallback."
        )

    return config_path


# --- Constantes ---
CONFIG_DIR_NAME = "LGA"
TOOLPACK_SUBDIR_NAME = "ToolPack"
COLORSPACE_INI_APPNAME = "ColorSpace_Favs.ini"
COLORSPACE_INI_LOCALNAME = "LGA_RnW_ColorSpace_Favs.ini"
COLORSPACE_SECTION = "ColorSpaces"


# --- Funciones de Manejo de Configuracion ---


def get_lga_toolpack_config_dir() -> typing.Optional[str]:
    """
    Obtiene la ruta completa del directorio de configuracion (%APPDATA%/LGA/ToolPack en Windows, ~/Library/Application Support/LGA/ToolPack en Mac).
    Crea el directorio si no existe.
    Devuelve la ruta o None si no se puede obtener el directorio de configuracion del usuario o hay error al crear.
    """
    user_config_dir = get_user_config_dir()
    if not user_config_dir:
        return None

    config_dir = os.path.join(user_config_dir, CONFIG_DIR_NAME, TOOLPACK_SUBDIR_NAME)

    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
            debug_print(f"Directorio de configuracion creado: {config_dir}")
        except OSError as e:
            debug_print(f"Error al crear el directorio {config_dir}: {e}")
            return None
    return config_dir


def get_colorspace_ini_path(create_if_missing: bool = True) -> typing.Optional[str]:
    """
    Obtiene la ruta del archivo INI de ColorSpaces en el directorio de configuracion del usuario.
    Si create_if_missing es True y el archivo no existe en el directorio de configuracion,
    intenta copiarlo desde la ubicacion local del script.
    Devuelve la ruta completa del archivo INI en el directorio de configuracion o None si hay errores.
    """
    config_dir = get_lga_toolpack_config_dir()
    if not config_dir:
        return None  # Error ya impreso en get_lga_toolpack_config_dir

    ini_path_config = os.path.join(config_dir, COLORSPACE_INI_APPNAME)
    local_script_dir = os.path.dirname(os.path.realpath(__file__))
    local_ini_path = os.path.join(local_script_dir, COLORSPACE_INI_LOCALNAME)

    if not os.path.exists(ini_path_config) and create_if_missing:
        debug_print(
            f"Archivo INI no encontrado en directorio de configuracion: {ini_path_config}"
        )
        if os.path.exists(local_ini_path):
            try:
                shutil.copy2(local_ini_path, ini_path_config)
                debug_print(
                    f"Archivo INI copiado desde {local_ini_path} a {ini_path_config}"
                )
            except Exception as e:
                debug_print(
                    f"Error al copiar el archivo INI local al directorio de configuracion: {e}"
                )
                # Continuamos, pero es posible que la lectura falle si el archivo no se copio
        else:
            debug_print(
                f"Archivo INI local ({local_ini_path}) tampoco encontrado. No se pudo copiar al directorio de configuracion."
            )
            # El archivo no existira en el directorio de configuracion, la funcion read fallara o devolvera lista vacia

    # Devolver la ruta del directorio de configuracion, exista o no (si no se creo/copio)
    return ini_path_config


def read_colorspaces_from_ini(ini_path: typing.Optional[str]) -> typing.List[str]:
    """
    Lee la seccion [ColorSpaces] desde el archivo INI especificado.
    Devuelve una lista de claves (nombres de colorspaces) o una lista vacia si hay error.
    """
    fallback_list: typing.List[str] = []
    if not ini_path or not os.path.exists(ini_path):
        debug_print(f"Error: Archivo INI no encontrado o ruta invalida: {ini_path}")
        return fallback_list

    config = configparser.ConfigParser(allow_no_value=True)
    try:
        debug_print(f"Leyendo configuracion desde: {ini_path}")
        config.optionxform = str  # Mantener mayusculas/minusculas
        config.read(ini_path)
        if config.has_section(COLORSPACE_SECTION):
            # Devolver solo las claves de la seccion
            return list(config[COLORSPACE_SECTION].keys())
        else:
            debug_print(
                f"Advertencia: Seccion '{COLORSPACE_SECTION}' no encontrada en {ini_path}."
            )
            return fallback_list
    except configparser.Error as e:
        debug_print(f"Error al leer el archivo INI {ini_path}: {e}")
        return fallback_list
    except Exception as e:
        debug_print(f"Error inesperado al leer {ini_path}: {e}")
        return fallback_list


def save_colorspaces_to_ini(
    ini_path: typing.Optional[str], colorspaces_list: typing.List[str]
):
    """
    Guarda la lista de colorspaces en la seccion [ColorSpaces] del archivo INI.
    Sobrescribe la seccion existente.
    """
    if not ini_path:
        debug_print(
            "Error: No se proporciono una ruta valida para guardar el archivo INI."
        )
        return False  # Indicar fallo

    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str  # Mantener mayusculas/minusculas

    try:
        # Leer el archivo existente para preservar otras secciones si las hubiera
        if os.path.exists(ini_path):
            config.read(ini_path)

        # Eliminar la seccion existente si existe, para empezar de cero
        if config.has_section(COLORSPACE_SECTION):
            config.remove_section(COLORSPACE_SECTION)

        # Anadir la nueva seccion
        config.add_section(COLORSPACE_SECTION)

        # Anadir cada colorspace como una clave sin valor
        for cs in colorspaces_list:
            if cs:  # Evitar guardar strings vacios
                config.set(COLORSPACE_SECTION, cs, None)

        # Escribir el archivo
        with open(ini_path, "w") as configfile:
            config.write(configfile)
        debug_print(f"Configuracion de ColorSpaces guardada en: {ini_path}")
        return True  # Indicar exito

    except configparser.Error as e:
        debug_print(f"Error de ConfigParser al guardar en {ini_path}: {e}")
        return False  # Indicar fallo
    except IOError as e:
        debug_print(f"Error de I/O al guardar en {ini_path}: {e}")
        return False  # Indicar fallo
    except Exception as e:
        debug_print(f"Error inesperado al guardar en {ini_path}: {e}")
        return False  # Indicar fallo


# --- Clase de la Interfaz ---


class SelectedNodeInfo(QWidget):
    def __init__(self, selected_nodes, parent=None, initial_color_spaces=None):
        super(SelectedNodeInfo, self).__init__(parent)
        # Usar la lista pre-cargada si se paso, sino cargarla usando las nuevas funciones
        self.color_spaces = (
            initial_color_spaces
            if initial_color_spaces is not None
            else self.load_color_spaces_wrapper()  # Usar el wrapper
        )
        self.selected_nodes = selected_nodes
        if self.color_spaces:  # initUI solo si hay color spaces
            self.initUI()
        else:
            debug_print(
                "Error interno: No se pudieron cargar los color spaces para la UI."
            )
            # Considerar no mostrar la ventana o cerrarla inmediatamente
            # self.close()

    def load_color_spaces_wrapper(self) -> typing.List[str]:
        """Metodo wrapper para llamar a las funciones de carga refactorizadas."""
        ini_path = get_colorspace_ini_path(
            create_if_missing=True
        )  # Asegura que exista/copie
        return read_colorspaces_from_ini(ini_path)  # Lee desde la ruta obtenida

    def initUI(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
        )  # Quitar la barra de titulo estandar

        # Verificar los tipos de nodos seleccionados y establecer el titulo apropiado
        node_classes = [node.Class() for node in self.selected_nodes]
        if "Write" in node_classes and "Read" in node_classes:
            self.setWindowTitle(" Input + Output Transform")
            header_label = "Input & Output Transform"
        elif "Write" in node_classes:
            self.setWindowTitle(" Output Transform")
            header_label = "Output Transform"
        elif "Read" in node_classes:
            self.setWindowTitle(" Input Transform")
            header_label = "Input Transform"
        else:
            # Esto no deberia pasar si main() filtra bien
            self.setWindowTitle("Node Information")
            header_label = "Transform"

        layout = QVBoxLayout(self)

        # Crear una barra de titulo personalizada con el titulo y el boton de cierre en la misma linea
        title_bar = QWidget(self)
        title_bar.setFixedHeight(20)  # Ajustar el alto de la barra de titulo
        title_bar.setAutoFillBackground(
            True
        )  # Asegurar que el fondo se llene con el color especificado
        title_bar.setStyleSheet(
            "background-color: #323232;"
        )  # Establecer el color de fondo

        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)  # Ajustar los margenes a cero

        # Anadir un expansor para centrar el titulo
        title_bar_layout.addStretch(1)

        # Crear el titulo de la ventana
        title_label = QPushButton(self.windowTitle(), self)
        title_label.setStyleSheet(
            "background-color: none; color: white; border: none; font-weight: bold;"
        )
        title_label.setEnabled(False)  # Hacer que el boton no sea clickeable
        title_bar_layout.addWidget(title_label)

        # Anadir otro expansor para centrar el titulo
        title_bar_layout.addStretch(1)

        # Agregar el boton de cierre personalizado al final
        close_button = QPushButton("X", self)
        close_button.setFixedSize(
            20, 20
        )  # Ajustar el tamano de la X para que sea consistente con la altura de la barra
        close_button.setStyleSheet(
            "background-color: none; color: white; border: none;"
        )
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)

        # Mover el boton de cierre al final con espaciado
        title_bar_layout.setSpacing(0)

        layout.addWidget(title_bar)

        # Crear la tabla sin el horizontal header
        self.table = QTableWidget(len(self.color_spaces), 1, self)
        self.table.horizontalHeader().setVisible(
            False
        )  # Ocultar el encabezado horizontal

        # Eliminar numeros de las filas
        self.table.verticalHeader().setVisible(False)

        # Configurar la paleta de la tabla para cambiar el color de seleccion a gris claro
        palette = self.table.palette()
        palette.setColor(QPalette.Highlight, QColor(230, 230, 230))  # Gris claro
        palette.setColor(QPalette.HighlightedText, QColor(Qt.black))
        self.table.setPalette(palette)

        # Configurar el estilo de la tabla
        self.table.setStyleSheet(
            """
            QTableView::item:selected {
                background-color: rgb(230, 230, 230);  # Gris claro
                color: black;
            }
        """
        )

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

    def load_data(self):
        for row, name in enumerate(self.color_spaces):
            node_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, node_item)
        # Ya no necesitamos resizeColumnsToContents aqui si se hace en adjust_window_size
        # self.table.resizeColumnsToContents()

    def adjust_window_size(self):
        # Desactivar temporalmente el estiramiento de la ultima columna
        self.table.horizontalHeader().setStretchLastSection(False)

        # Ajustar las columnas al contenido
        self.table.resizeColumnsToContents()

        # Calcular el ancho de la ventana basado en el ancho de las columnas y el texto mas ancho
        width = self.table.verticalHeader().width()  # Un poco de relleno para estetica
        for i in range(self.table.columnCount()):
            width += (
                self.table.columnWidth(i) + 50
            )  # Un poco mas de relleno entre columnas

        # Ajustar el ancho adicional basado en el texto mas ancho
        longest_text = max(self.color_spaces, key=len)
        font_metrics = self.table.fontMetrics()
        text_width = (
            font_metrics.horizontalAdvance(longest_text) + 50
        )  # Un poco de relleno adicional
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
        # Asegurarse de que el indice de fila sea valido
        if 0 <= row < len(self.color_spaces):
            selected_color_space = self.color_spaces[row]
            debug_print(f"Aplicando colorspace: {selected_color_space}")  # Debug

            # Volver a obtener nodos seleccionados por si cambio
            selected_nodes = nuke.selectedNodes()

            if selected_nodes:
                nodes_changed = 0
                for node in selected_nodes:
                    if node.Class() in ["Read", "Write"]:
                        try:
                            node["colorspace"].setValue(selected_color_space)
                            nodes_changed += 1
                            debug_print(f"  - Aplicado a {node.name()}")
                        except Exception as e:
                            debug_print(
                                f"  - Error al cambiar colorspace en {node.name()}: {e}"
                            )
                            nuke.message(
                                f"Error al aplicar colorspace a {node.name()}:\n{e}"
                            )
                            return  # Salir

                if nodes_changed > 0:
                    debug_print(f"Colorspace aplicado a {nodes_changed} nodo(s).")
                else:
                    debug_print("No se aplico el colorspace a ningun nodo valido.")

            else:
                debug_print(
                    "No hay nodos Read/Write seleccionados al momento de aplicar."
                )

            # Cerrar la ventana despues de intentar aplicar los cambios (incluso si hubo errores parciales)
            self.close()
        else:
            debug_print(f"Error: Fila invalida seleccionada ({row}).")


app = None
window = None


def main():
    global app, window
    selected_nodes = nuke.selectedNodes()

    valid_nodes = [node for node in selected_nodes if node.Class() in ["Read", "Write"]]

    if valid_nodes:
        # --- Carga inicial usando funciones refactorizadas ---
        ini_path = get_colorspace_ini_path(create_if_missing=True)
        color_spaces = read_colorspaces_from_ini(ini_path)
        # ----------------------------------------------------

        if not color_spaces:
            # Intentar obtener la ruta nuevamente para mostrarla en el mensaje
            ini_path_for_msg = (
                get_colorspace_ini_path(create_if_missing=False) or "ruta desconocida"
            )
            local_path_for_msg = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), COLORSPACE_INI_LOCALNAME
            )
            nuke.message(
                f"Error: No se pudieron cargar los espacios de color favoritos.\n"
                f"Verifique que el archivo '{COLORSPACE_INI_APPNAME}' exista en\n"
                f"'{os.path.dirname(ini_path_for_msg)}'\n"
                f"o que '{COLORSPACE_INI_LOCALNAME}' exista en\n"
                f"'{os.path.dirname(local_path_for_msg)}'."
            )
            return

        app = QApplication.instance() or QApplication([])
        # Pasar los nodos validos y los color spaces ya cargados
        window = SelectedNodeInfo(valid_nodes, initial_color_spaces=color_spaces)
        window.show()
    else:
        nuke.message("Por favor seleccione al menos un nodo Read o Write.")


if __name__ == "__main__":
    main()
