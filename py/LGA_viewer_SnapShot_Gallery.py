"""
___________________________________________________________________________________

  LGA_viewer_SnapShot_Gallery v0.54 - Lega
  Crea una ventana que muestra los snapshots guardados organizados por proyecto

  v0.53 - Shift click para revelar en explorador de archivos
        - Tooltips
  v0.54 - Thumb size persistente en config
___________________________________________________________________________________

"""

import nuke
import os
import glob
import shutil
import subprocess  # Importar subprocess para abrir archivos en macOS/Linux
import platform  # Importar platform para detectar el SO
import configparser
from LGA_QtAdapter_ToolPack import QtWidgets, QtCore, QtGui
from LGA_tooltip_helper import (
    TOOLTIP_BG,
    TOOLTIP_PADDING_PX,
    TOOLTIP_PRIMARY_TEXT,
    TOOLTIP_RADIUS_PX,
    TOOLTIP_SECONDARY_TEXT,
)

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QScrollArea = QtWidgets.QScrollArea
QFrame = QtWidgets.QFrame
QSlider = QtWidgets.QSlider
QToolBar = QtWidgets.QToolBar
QSizePolicy = QtWidgets.QSizePolicy
QMessageBox = QtWidgets.QMessageBox
QLayout = QtWidgets.QLayout
Qt = QtCore.Qt
QSize = QtCore.QSize
Signal = QtCore.Signal
QRect = QtCore.QRect
QPoint = QtCore.QPoint
QPixmap = QtGui.QPixmap
QFont = QtGui.QFont
QCursor = QtGui.QCursor
QIcon = QtGui.QIcon
QPainter = QtGui.QPainter
QColor = QtGui.QColor

# Variable global para activar o desactivar los prints de depuracion
debug = False  # Cambiar a False para ocultar los mensajes de debug

# Variables para personalizar el slider
SLIDER_BAR_WIDTH = 100  # Ancho de la barra del slider
SLIDER_BAR_HEIGHT = 4  # Alto de la barra del slider
SLIDER_HANDLE_SIZE = 9  # Diametro de la bolita del slider
DEFAULT_THUMBNAIL_SIZE = 150
MIN_THUMBNAIL_SIZE = 50
MAX_THUMBNAIL_SIZE = 500
CONFIG_FILE_NAME = "SnapshotGallery.ini"
CONFIG_SECTION = "Settings"
CONFIG_THUMBNAIL_SIZE_KEY = "thumbnail_size"

app = None
window = None


def debug_print(*message):
    if debug:
        print("[LGA_viewer_SnapShot_Gallery]", *message)


def get_user_config_dir():
    """
    Obtiene el directorio de configuracion del usuario segun el sistema operativo.
    Usa la misma base que el resto de settings del ToolPack.
    """
    system = platform.system()
    if system == "Windows":
        config_path = os.getenv("APPDATA")
        if not config_path:
            debug_print("Error: No se pudo encontrar la variable de entorno APPDATA.")
            return None
    elif system == "Darwin":
        config_path = os.path.expanduser("~/Library/Application Support")
    else:
        config_path = os.path.expanduser("~/.config")
        debug_print(
            f"Sistema no reconocido ({system}), usando ~/.config como fallback."
        )

    return config_path


def get_config_path():
    """Devuelve la ruta completa al ini persistente de la galeria."""
    try:
        user_config_dir = get_user_config_dir()
        if not user_config_dir:
            return None
        config_dir = os.path.join(user_config_dir, "LGA", "ToolPack")
        return os.path.join(config_dir, CONFIG_FILE_NAME)
    except Exception as e:
        debug_print(f"Error al obtener la ruta de configuracion: {e}")
        return None


def ensure_config_exists():
    """Asegura que exista el ini de la galeria con defaults."""
    config_file_path = get_config_path()
    if not config_file_path:
        return

    config_dir = os.path.dirname(config_file_path)
    try:
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            debug_print(f"Directorio de configuracion creado: {config_dir}")

        if not os.path.exists(config_file_path):
            config = configparser.ConfigParser()
            config[CONFIG_SECTION] = {
                CONFIG_THUMBNAIL_SIZE_KEY: str(DEFAULT_THUMBNAIL_SIZE)
            }
            with open(config_file_path, "w", encoding="utf-8") as configfile:
                config.write(configfile)
            debug_print(f"Archivo de configuracion creado: {config_file_path}")
    except Exception as e:
        debug_print(f"Error al asegurar la configuracion: {e}")


def clamp_thumbnail_size(value):
    """Limita el valor del thumbnail al rango valido del slider."""
    return max(MIN_THUMBNAIL_SIZE, min(MAX_THUMBNAIL_SIZE, int(value)))


def get_thumbnail_size_from_config():
    """Lee el tamaño persistente del slider o devuelve el default."""
    ensure_config_exists()
    config_file_path = get_config_path()
    if not config_file_path or not os.path.exists(config_file_path):
        return DEFAULT_THUMBNAIL_SIZE

    config = configparser.ConfigParser()
    try:
        config.read(config_file_path, encoding="utf-8")
        value = config.getint(
            CONFIG_SECTION,
            CONFIG_THUMBNAIL_SIZE_KEY,
            fallback=DEFAULT_THUMBNAIL_SIZE,
        )
        return clamp_thumbnail_size(value)
    except Exception as e:
        debug_print(f"Error al leer thumbnail_size desde config: {e}")
        return DEFAULT_THUMBNAIL_SIZE


def save_thumbnail_size_to_config(value):
    """Guarda el tamaño del slider en el ini persistente."""
    config_file_path = get_config_path()
    if not config_file_path:
        return False

    config_dir = os.path.dirname(config_file_path)
    try:
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config = configparser.ConfigParser()
        if os.path.exists(config_file_path):
            config.read(config_file_path, encoding="utf-8")
        if not config.has_section(CONFIG_SECTION):
            config.add_section(CONFIG_SECTION)

        config.set(
            CONFIG_SECTION,
            CONFIG_THUMBNAIL_SIZE_KEY,
            str(clamp_thumbnail_size(value)),
        )
        with open(config_file_path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
        return True
    except Exception as e:
        debug_print(f"Error al guardar thumbnail_size en config: {e}")
        return False


def get_project_info():
    """
    Obtiene informacion del proyecto actual de Nuke.
    Retorna tupla (project_name_without_version, full_project_name)
    """
    try:
        script_path = nuke.root().name()
        if not script_path or script_path == "Root":
            debug_print("No hay proyecto guardado, usando nombre generico")
            return "untitled_project", "untitled_project"

        # Obtener solo el nombre del archivo sin extension
        project_name = os.path.splitext(os.path.basename(script_path))[0]
        debug_print(f"Nombre del proyecto: {project_name}")

        # Separar por guiones bajos
        parts = project_name.split("_")

        # Verificar si el ultimo bloque es un numero de version (vXX)
        if (
            len(parts) > 1
            and parts[-1].lower().startswith("v")
            and parts[-1][1:].isdigit()
        ):
            # Hay numero de version
            project_name_without_version = "_".join(parts[:-1])
            debug_print(
                f"Proyecto con version detectado. Sin version: {project_name_without_version}"
            )
        else:
            # No hay numero de version
            project_name_without_version = project_name
            debug_print(
                f"Proyecto sin version detectado: {project_name_without_version}"
            )

        return project_name_without_version, project_name

    except Exception as e:
        debug_print(f"Error al obtener info del proyecto: {e}")
        return "untitled_project", "untitled_project"


class FlowLayout(QLayout):
    """Layout que organiza widgets en filas, ajustando automaticamente al ancho disponible"""

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spacing = self.spacing()

        for item in self.item_list:
            wid = item.widget()
            if wid is None:
                continue

            # Usar spacing simple en lugar de layoutSpacing complejo
            spaceX = spacing if spacing >= 0 else 12
            spaceY = spacing if spacing >= 0 else 12

            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


def extract_version_from_filename(filename):
    """
    Extrae el numero de version de un nombre de archivo.
    Retorna el numero de version (ej: "v01") o None si no encuentra
    """
    try:
        # Obtener solo el nombre sin extension
        name_without_ext = os.path.splitext(os.path.basename(filename))[0]
        debug_print(f"Extrayendo version de: {name_without_ext}")

        # Separar por guiones bajos
        parts = name_without_ext.split("_")

        # Buscar partes que empiecen con 'v' seguido de numeros
        for part in parts:
            if part.lower().startswith("v") and len(part) > 1 and part[1:].isdigit():
                debug_print(f"Version encontrada: {part}")
                return part

        debug_print("No se encontro version en el nombre del archivo")
        return None

    except Exception as e:
        debug_print(f"Error al extraer version: {e}")
        return None


class DeleteButton(QPushButton):
    """Boton de borrar personalizado con hover"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Cargar iconos
        script_dir = os.path.dirname(__file__)
        self.normal_icon_path = os.path.join(script_dir, "icons", "delete.png")
        self.hover_icon_path = os.path.join(script_dir, "icons", "delete_white.png")

        self.load_icons()
        self.setStyleSheet(
            """
            QPushButton {
                border: none;
                background-color: transparent;
            }
        """
        )

    def load_icons(self):
        """Carga los iconos normal y hover"""
        try:
            if os.path.exists(self.normal_icon_path):
                normal_pixmap = QPixmap(self.normal_icon_path)
                if not normal_pixmap.isNull():
                    self.normal_pixmap = normal_pixmap.scaledToWidth(
                        16, Qt.SmoothTransformation
                    )
                    self.setIcon(QIcon(self.normal_pixmap))

            if os.path.exists(self.hover_icon_path):
                hover_pixmap = QPixmap(self.hover_icon_path)
                if not hover_pixmap.isNull():
                    self.hover_pixmap = hover_pixmap.scaledToWidth(
                        16, Qt.SmoothTransformation
                    )
        except Exception as e:
            debug_print(f"Error al cargar iconos de borrar: {e}")

    def enterEvent(self, event):
        """Evento cuando el mouse entra al boton"""
        if hasattr(self, "hover_pixmap"):
            self.setIcon(QIcon(self.hover_pixmap))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Evento cuando el mouse sale del boton"""
        if hasattr(self, "normal_pixmap"):
            self.setIcon(QIcon(self.normal_pixmap))
        super().leaveEvent(event)


class RoundedTooltipPopup(QWidget):
    """Tooltip propio con fondo pintado y padding real."""

    def __init__(
        self,
        html,
        parent=None,
        padding=TOOLTIP_PADDING_PX,
        radius=TOOLTIP_RADIUS_PX,
    ):
        super().__init__(parent)
        self.bg_color = QColor(TOOLTIP_BG)
        self.padding = padding
        self.radius = radius

        flags = Qt.ToolTip | Qt.FramelessWindowHint
        if hasattr(Qt, "NoDropShadowWindowHint"):
            flags = flags | Qt.NoDropShadowWindowHint
        self.setWindowFlags(flags)
        if hasattr(Qt, "WA_ShowWithoutActivating"):
            self.setAttribute(Qt.WA_ShowWithoutActivating)
        if hasattr(Qt, "WA_TranslucentBackground"):
            self.setAttribute(Qt.WA_TranslucentBackground)
        if hasattr(Qt, "WA_NoSystemBackground"):
            self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(0)

        self.label = QLabel()
        self.label.setTextFormat(Qt.RichText)
        self.label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: 0px;
                margin: 0px;
                padding: 0px;
            }
            """
        )
        self.label.setContentsMargins(0, 0, 0, 0)
        self.label.setMargin(0)
        self.label.setIndent(0)
        layout.addWidget(self.label)
        self.set_html(html)

    def set_html(self, html):
        self.label.setText(html)
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.bg_color)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.drawRoundedRect(rect, self.radius, self.radius)


class ThumbnailWidget(QLabel):
    """Widget personalizado para mostrar un thumbnail"""

    def __init__(self, image_path, size=150):
        super().__init__()
        self.image_path = image_path
        self.original_pixmap = None
        self.tooltip_popup = None
        self.load_image()
        self.update_size(size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """
            QLabel {
                border: 0px;
                background-color: #2a2a2a;
                margin: 2px;
            }
            QLabel:hover {
                border: 0px;
            }
        """
        )
        self.setup_tooltip()

    def load_image(self):
        """Carga la imagen original"""
        try:
            self.original_pixmap = QPixmap(self.image_path)
            if self.original_pixmap.isNull():
                debug_print(f"No se pudo cargar la imagen: {self.image_path}")
                # Crear un pixmap de placeholder
                self.original_pixmap = QPixmap(150, 100)
                self.original_pixmap.fill(Qt.gray)
        except Exception as e:
            debug_print(f"Error al cargar imagen {self.image_path}: {e}")
            self.original_pixmap = QPixmap(150, 100)
            self.original_pixmap.fill(Qt.gray)

    def update_size(self, width):
        """Actualiza el tamaño del thumbnail manteniendo la relación de aspecto"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled_pixmap = self.original_pixmap.scaledToWidth(
                width, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            self.setFixedSize(scaled_pixmap.size())

    def setup_tooltip(self):
        """Configura el tooltip de acciones del thumbnail."""
        system = platform.system()
        reveal_target = "Finder" if system == "Darwin" else "Explorer"
        if system not in ("Windows", "Darwin"):
            reveal_target = "File Manager"

        self.tooltip_html = (
            "<table border='0' cellspacing='0' cellpadding='0' style='"
            f"background-color:{TOOLTIP_BG};"
            "border:0px;"
            "border-collapse:collapse;"
            "margin:0px;"
            "padding:0px;"
            "'>"
            "<tr>"
            f"<td style='background-color:{TOOLTIP_BG}; color:{TOOLTIP_PRIMARY_TEXT}; padding:0px 12px 3px 0px; white-space:nowrap;'>Click</td>"
            f"<td style='background-color:{TOOLTIP_BG}; color:{TOOLTIP_SECONDARY_TEXT}; padding:0px 0px 3px 0px; white-space:nowrap;'>Open JPG in your default viewer</td>"
            "</tr>"
            "<tr>"
            f"<td style='background-color:{TOOLTIP_BG}; color:{TOOLTIP_PRIMARY_TEXT}; padding:0px 12px 0px 0px; white-space:nowrap;'>Shift-click</td>"
            f"<td style='background-color:{TOOLTIP_BG}; color:{TOOLTIP_SECONDARY_TEXT}; padding:0px; white-space:nowrap;'>Show in {reveal_target}</td>"
            "</tr>"
            "</table>"
        )
        self.setMouseTracking(True)

    def show_custom_tooltip(self):
        """Muestra un tooltip propio con padding y esquinas redondeadas."""
        if self.tooltip_popup is None:
            self.tooltip_popup = RoundedTooltipPopup(self.tooltip_html)
        else:
            self.tooltip_popup.set_html(self.tooltip_html)

        self.tooltip_popup.move(QCursor.pos() + QPoint(12, 18))
        self.tooltip_popup.show()

    def hide_custom_tooltip(self):
        """Oculta el tooltip propio."""
        if self.tooltip_popup is not None:
            self.tooltip_popup.hide()

    def enterEvent(self, event):
        """Muestra el tooltip inmediatamente al pasar por arriba."""
        self.show_custom_tooltip()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Oculta el tooltip al salir del thumbnail."""
        self.hide_custom_tooltip()
        super().leaveEvent(event)

    def reveal_in_file_browser(self):
        """Revela el archivo del thumbnail en el explorador del sistema."""
        try:
            normalized_path = os.path.normpath(self.image_path)

            if platform.system() == "Windows":
                subprocess.Popen(["explorer", "/select,", normalized_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "-R", normalized_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", os.path.dirname(normalized_path)])
        except Exception as e:
            debug_print(f"Error al revelar imagen: {e}")
            QMessageBox.warning(
                self, "Error", f"No se pudo revelar la imagen:\n{str(e)}"
            )

    def open_image_in_default_viewer(self):
        """Abre el snapshot en el visor de imagenes predeterminado."""
        debug_print(f"Abriendo imagen: {self.image_path}")
        try:
            if platform.system() == "Windows":
                os.startfile(self.image_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", self.image_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", self.image_path])
        except Exception as e:
            debug_print(f"Error al abrir imagen: {e}")
            QMessageBox.warning(
                self, "Error", f"No se pudo abrir la imagen:\n{str(e)}"
            )

    def mousePressEvent(self, event):
        """Maneja click para abrir y Shift+click para revelar."""
        if event.button() == Qt.LeftButton:
            self.hide_custom_tooltip()

            if event.modifiers() & Qt.ShiftModifier:
                debug_print(f"Revelando imagen en explorador: {self.image_path}")
                self.reveal_in_file_browser()
                super().mousePressEvent(event)
                return

            self.open_image_in_default_viewer()

        super().mousePressEvent(event)


class ThumbnailContainerWidget(QWidget):
    """Widget contenedor que incluye thumbnail, version y boton de borrar"""

    thumbnail_deleted = Signal(str)  # Señal que emite la ruta del archivo borrado

    def __init__(self, image_path, size=150):
        super().__init__()
        self.image_path = image_path
        self.thumbnail_size = size

        self.setStyleSheet("background-color: transparent;")
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del contenedor"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail principal
        self.thumbnail = ThumbnailWidget(self.image_path, self.thumbnail_size)
        layout.addWidget(self.thumbnail, alignment=Qt.AlignCenter)

        # Widget contenedor para la información (versión + botón borrar)
        # Este widget tendrá el mismo ancho que el thumbnail
        self.info_widget = QWidget()
        # Usar el ancho real del thumbnail después del escalado
        actual_width = self.thumbnail.width()
        self.info_widget.setFixedWidth(actual_width)

        # Layout horizontal para version y boton de borrar
        info_layout = QHBoxLayout(self.info_widget)
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Label de version (alineado a la izquierda)
        version = extract_version_from_filename(self.image_path)
        version_text = version if version else "---"
        self.version_label = QLabel(version_text)
        self.version_label.setStyleSheet(
            "color: #cccccc; font-size: 12px; background-color: transparent; margin-left: 4px;"
        )
        self.version_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(self.version_label)

        # Boton de borrar (ahora justo al lado de la version)
        self.delete_button = DeleteButton()
        self.delete_button.clicked.connect(self.delete_thumbnail)
        self.delete_button.setStyleSheet("padding-bottom: 2px;")
        info_layout.addWidget(self.delete_button)

        # Spacer para empujar el conjunto (version + boton) a la izquierda
        info_layout.addStretch()

        layout.addWidget(self.info_widget, alignment=Qt.AlignCenter)

    def delete_thumbnail(self):
        """Borra el thumbnail del disco y emite señal"""
        try:
            if os.path.exists(self.image_path):
                os.remove(self.image_path)
                debug_print(f"Archivo borrado: {self.image_path}")
                self.thumbnail_deleted.emit(self.image_path)
            else:
                debug_print(f"El archivo no existe: {self.image_path}")

        except Exception as e:
            debug_print(f"Error al borrar thumbnail: {e}")
            QMessageBox.warning(
                self, "Error", f"No se pudo borrar el archivo:\n{str(e)}"
            )

    def update_size(self, width):
        """Actualiza el tamaño del thumbnail y del widget de información"""
        self.thumbnail_size = width
        self.thumbnail.update_size(width)

        # Actualizar el ancho del widget de información para que coincida con el thumbnail
        if hasattr(self, "info_widget"):
            # Obtener el ancho real del thumbnail después del escalado
            actual_width = self.thumbnail.width()
            self.info_widget.setFixedWidth(actual_width)


class ClickableLabel(QLabel):
    """Label clickeable para el titulo de las carpetas"""

    clicked = Signal()

    def __init__(self, text):
        super().__init__(text)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ProjectFolderWidget(QFrame):
    """Widget que contiene los thumbnails de un proyecto"""

    project_deleted = Signal(str)  # Señal que emite el nombre del proyecto borrado

    def __init__(
        self, project_name, image_paths, thumbnail_size=150, is_current_project=False
    ):
        super().__init__()
        self.project_name = project_name
        self.image_paths = image_paths
        self.thumbnails = []
        self.thumbnail_size = thumbnail_size
        self.is_expanded = is_current_project  # Solo expandir si es el proyecto actual
        self.thumbnails_widget = None
        self.arrow_label = None
        self.expanded_arrow_pixmap = None
        self.collapsed_arrow_pixmap = None

        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(
            """
            QFrame {
                border: 0px solid #444444;
                border-radius: 0px;
                background-color: #262626;
                margin: 0px;
                padding: 0px;
            }
        """
        )

        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del widget del proyecto"""
        # Eliminar el sufijo "_comp" si el nombre del proyecto termina con el
        display_project_name = self.project_name
        if display_project_name.endswith("_comp"):
            display_project_name = display_project_name[:-5]  # Eliminar "_comp"
            debug_print(
                f"Nombre de proyecto ajustado para UI: {self.project_name} -> {display_project_name}"
            )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header con titulo y flecha
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        header_layout.setAlignment(Qt.AlignLeft)

        # Flecha desplegable
        self.arrow_label = QLabel()
        self.load_arrow_icon()
        self.arrow_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.arrow_label.mousePressEvent = self.toggle_expanded
        header_layout.addWidget(self.arrow_label)

        # Título del proyecto (clickeable)
        self.title_label = ClickableLabel(
            f"<b style='color:#cccccc; font-size:13px;'>{display_project_name}</b>"
        )
        self.title_label.clicked.connect(self.toggle_expanded)
        header_layout.addWidget(self.title_label)

        # Boton de borrar proyecto (justo al lado del titulo con 4px de espacio)
        self.delete_project_button = DeleteButton()
        self.delete_project_button.clicked.connect(self.delete_project)
        header_layout.addWidget(self.delete_project_button)

        # Spacer para empujar todo a la izquierda
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Contenedor para los thumbnails
        self.thumbnails_widget = QWidget()
        thumbnails_layout = FlowLayout(self.thumbnails_widget, margin=20, spacing=12)
        thumbnails_layout.setContentsMargins(20, 0, 0, 0)  # Indentacion

        # Crear thumbnails para cada imagen
        for image_path in self.image_paths:
            thumbnail = ThumbnailContainerWidget(image_path, self.thumbnail_size)
            thumbnail.thumbnail_deleted.connect(self.on_thumbnail_deleted)
            self.thumbnails.append(thumbnail)
            thumbnails_layout.addWidget(thumbnail)

        # Si no hay imágenes, mostrar mensaje
        if not self.image_paths:
            no_images_label = QLabel(
                "<i style='color:#888888;'>No hay snapshots en este proyecto</i>"
            )
            thumbnails_layout.addWidget(no_images_label)

        layout.addWidget(self.thumbnails_widget)

        # Establecer estado inicial
        if not self.is_expanded:
            self.thumbnails_widget.hide()

    def load_arrow_icon(self):
        """Carga los iconos de la flecha para los estados expandido y colapsado"""
        if self.arrow_label is None:
            return

        script_dir = os.path.dirname(__file__)
        expanded_icon_path = os.path.join(script_dir, "icons", "dropdown_arrow.png")
        collapsed_icon_path = os.path.join(
            script_dir, "icons", "dropdown_arrow_collapsed.png"
        )

        # Cargar icono expandido
        if os.path.exists(expanded_icon_path):
            pixmap = QPixmap(expanded_icon_path)
            if not pixmap.isNull():
                self.expanded_arrow_pixmap = pixmap.scaledToWidth(
                    12, Qt.SmoothTransformation
                )

        # Cargar icono colapsado
        if os.path.exists(collapsed_icon_path):
            pixmap = QPixmap(collapsed_icon_path)
            if not pixmap.isNull():
                self.collapsed_arrow_pixmap = pixmap.scaledToWidth(
                    12, Qt.SmoothTransformation
                )

        # Si ambos iconos se cargaron, establecer el inicial y retornar
        if self.expanded_arrow_pixmap and self.collapsed_arrow_pixmap:
            self.update_arrow_icon()
            return

        # Fallback a texto si no se pueden cargar los iconos
        debug_print(
            "No se pudieron cargar los iconos de flecha, usando fallback de texto."
        )
        self.arrow_label.setText("▼" if self.is_expanded else "►")
        self.arrow_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        self.arrow_label.setFixedSize(12, 12)

    def update_arrow_icon(self):
        """Actualiza el icono de la flecha segun el estado de expansion"""
        if self.arrow_label is None:
            return

        if self.is_expanded and self.expanded_arrow_pixmap:
            self.arrow_label.setPixmap(self.expanded_arrow_pixmap)
            self.arrow_label.setFixedSize(self.expanded_arrow_pixmap.size())
        elif not self.is_expanded and self.collapsed_arrow_pixmap:
            self.arrow_label.setPixmap(self.collapsed_arrow_pixmap)
            self.arrow_label.setFixedSize(self.collapsed_arrow_pixmap.size())
        else:
            # Fallback a texto si no hay pixmap adecuado
            self.arrow_label.setText("▼" if self.is_expanded else "►")
            self.arrow_label.setStyleSheet("color: #cccccc; font-size: 10px;")
            self.arrow_label.setFixedSize(12, 12)

    def toggle_expanded(self, event=None):
        """Alterna entre expandido y colapsado"""
        self.is_expanded = not self.is_expanded

        if self.thumbnails_widget is None or self.arrow_label is None:
            return

        if self.is_expanded:
            self.thumbnails_widget.show()
        else:
            self.thumbnails_widget.hide()

        self.update_arrow_icon()  # Actualizar el icono de la flecha

    def update_thumbnail_size(self, size):
        """Actualiza el tamaño de todos los thumbnails"""
        self.thumbnail_size = size
        for thumbnail in self.thumbnails:
            thumbnail.update_size(size)

    def on_thumbnail_deleted(self, image_path):
        """Se ejecuta cuando se borra un thumbnail"""
        debug_print(f"Thumbnail borrado: {image_path}")

        # Remover de la lista de rutas de imagenes
        if image_path in self.image_paths:
            self.image_paths.remove(image_path)

        # Buscar y remover el widget del thumbnail
        for i, thumbnail in enumerate(self.thumbnails):
            if thumbnail.image_path == image_path:
                thumbnail.setParent(None)
                thumbnail.deleteLater()
                self.thumbnails.pop(i)
                break

        # Si no quedan thumbnails, mostrar mensaje
        if not self.thumbnails and self.thumbnails_widget:
            no_images_label = QLabel(
                "<i style='color:#888888;'>No hay snapshots en este proyecto</i>"
            )
            layout = self.thumbnails_widget.layout()
            if layout:
                layout.addWidget(no_images_label)

    def delete_project(self):
        """Borra todo el proyecto (carpeta completa)"""
        try:
            # Obtener la ruta de la carpeta del proyecto
            script_dir = os.path.dirname(__file__)
            gallery_path = os.path.join(script_dir, "snapshot_gallery")
            project_path = os.path.join(gallery_path, self.project_name)

            if os.path.exists(project_path):
                shutil.rmtree(project_path)
                debug_print(f"Proyecto borrado: {project_path}")
                self.project_deleted.emit(self.project_name)
            else:
                debug_print(f"La carpeta del proyecto no existe: {project_path}")

        except Exception as e:
            debug_print(f"Error al borrar proyecto: {e}")
            QMessageBox.warning(
                self, "Error", f"No se pudo borrar el proyecto:\n{str(e)}"
            )


class ToolbarWidget(QWidget):
    """Widget separado para el toolbar"""

    size_changed = Signal(int)

    def __init__(self, initial_thumbnail_size=DEFAULT_THUMBNAIL_SIZE):
        super().__init__()
        self.current_thumbnail_size = clamp_thumbnail_size(initial_thumbnail_size)
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del toolbar"""
        self.setStyleSheet("background-color: #1d1d1d;")

        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 14, 15, 14)

        # Spacer para empujar el slider a la derecha
        layout.addStretch()

        # Label para el slider
        size_label = QLabel("Thumbnail Size")
        size_label.setStyleSheet(
            "color: #cccccc; font-size: 12px; background-color: #1d1d1d;"
        )
        layout.addWidget(size_label, alignment=Qt.AlignVCenter)

        # Slider para controlar el tamaño de los thumbnails
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(MIN_THUMBNAIL_SIZE)
        self.size_slider.setMaximum(MAX_THUMBNAIL_SIZE)
        self.size_slider.setValue(self.current_thumbnail_size)
        self.size_slider.setFixedWidth(SLIDER_BAR_WIDTH)

        # Calcular el margen para centrar el handle
        handle_margin = -(SLIDER_HANDLE_SIZE - SLIDER_BAR_HEIGHT) // 2
        handle_radius = SLIDER_HANDLE_SIZE // 2

        self.size_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                border: 0px;
                height: {SLIDER_BAR_HEIGHT}px;
                background: #ADADAD;
                border-radius: {SLIDER_BAR_HEIGHT // 2}px;
                margin-top: 2px;
            }}
            QSlider::handle:horizontal {{
                background: #ADADAD;
                border: 0px;
                width: {SLIDER_HANDLE_SIZE}px;
                height: {SLIDER_HANDLE_SIZE}px;
                margin: {handle_margin}px 0;
                border-radius: {handle_radius}px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #ffffff;
            }}
        """
        )
        self.size_slider.valueChanged.connect(self.on_size_changed)
        layout.addWidget(self.size_slider, alignment=Qt.AlignVCenter)

    def on_size_changed(self, value):
        """Se ejecuta cuando cambia el valor del slider"""
        self.current_thumbnail_size = clamp_thumbnail_size(value)
        self.size_changed.emit(self.current_thumbnail_size)


class SnapshotGalleryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.project_widgets = []
        self.current_thumbnail_size = get_thumbnail_size_from_config()
        self.current_project_name = None

        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("LGA SnapShot Gallery")
        self.setStyleSheet("background-color: #1d1d1d;")
        self.setMinimumSize(1200, 900)

        # Establecer un nombre de objeto unico para esta ventana
        self.setObjectName("LGA_SnapshotGalleryWindow")

        # Obtener el proyecto actual
        self.current_project_name, _ = get_project_info()
        debug_print(f"Proyecto actual detectado: {self.current_project_name}")

        self.setup_ui()
        self.load_gallery_content()

    def setup_ui(self):
        """Configura la interfaz principal"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar separado
        self.toolbar = ToolbarWidget(self.current_thumbnail_size)
        self.toolbar.size_changed.connect(self.on_size_changed)
        main_layout.addWidget(self.toolbar)

        # Widget principal de la galería
        gallery_widget = QWidget()
        gallery_widget.setStyleSheet("background-color: #262626; border-radius: 0px;")
        gallery_layout = QVBoxLayout(gallery_widget)
        gallery_layout.setContentsMargins(10, 10, 10, 10)
        gallery_layout.setSpacing(10)

        # Área de scroll para el contenido
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: #232323;
            }
            QScrollBar:vertical {
                background-color: #333333;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #888888;
            }
        """
        )

        # Widget contenedor para el scroll
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        gallery_layout.addWidget(scroll_area)

        main_layout.addWidget(gallery_widget)

    def on_size_changed(self, value):
        """Se ejecuta cuando cambia el valor del slider"""
        self.current_thumbnail_size = clamp_thumbnail_size(value)
        save_thumbnail_size_to_config(self.current_thumbnail_size)

        # Actualizar el tamaño de todos los thumbnails
        for project_widget in self.project_widgets:
            project_widget.update_thumbnail_size(self.current_thumbnail_size)

    def load_gallery_content(self):
        """Carga el contenido de la galería organizando por proyectos"""
        gallery_path = self.get_gallery_path()

        if not gallery_path or not os.path.exists(gallery_path):
            # Mostrar mensaje si no existe la galería
            no_gallery_label = QLabel(
                f"<div style='text-align: center; color: #888888; font-size: 14px;'>"
                f"<b>No se encontró la carpeta de galería</b><br><br>"
                f"Ruta esperada: {gallery_path if gallery_path else 'No definida'}<br><br>"
                f"Toma algunos snapshots para crear la galería automáticamente."
                f"</div>"
            )
            no_gallery_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(no_gallery_label)
            return

        # Obtener todas las subcarpetas (proyectos)
        project_folders = []
        try:
            for item in os.listdir(gallery_path):
                item_path = os.path.join(gallery_path, item)
                if os.path.isdir(item_path):
                    project_folders.append(item)
        except Exception as e:
            debug_print(f"Error al leer carpeta de galería: {e}")
            return

        if not project_folders:
            # No hay proyectos
            no_projects_label = QLabel(
                "<div style='text-align: center; color: #888888; font-size: 14px;'>"
                "<b>No hay proyectos en la galería</b><br><br>"
                "Toma algunos snapshots para empezar a llenar la galería."
                "</div>"
            )
            no_projects_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(no_projects_label)
            return

        # Ordenar proyectos alfabeticamente
        project_folders.sort()

        # Mover el proyecto actual al principio de la lista si existe
        if self.current_project_name and self.current_project_name in project_folders:
            project_folders.remove(self.current_project_name)
            project_folders.insert(0, self.current_project_name)

        # Crear widget para cada proyecto
        for project_name in project_folders:
            project_path = os.path.join(gallery_path, project_name)

            # Buscar todas las imágenes en la carpeta del proyecto
            image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.tiff", "*.tif", "*.exr"]
            image_paths = []

            for extension in image_extensions:
                pattern = os.path.join(project_path, extension)
                image_paths.extend(glob.glob(pattern))

            # Ordenar imágenes alfabéticamente
            image_paths.sort()

            # Determinar si es el proyecto actual
            is_current_project = project_name == self.current_project_name

            # Crear widget del proyecto
            project_widget = ProjectFolderWidget(
                project_name,
                image_paths,
                self.current_thumbnail_size,
                is_current_project,
            )
            project_widget.project_deleted.connect(self.on_project_deleted)
            self.project_widgets.append(project_widget)
            self.scroll_layout.addWidget(project_widget)

        debug_print(f"Cargados {len(project_folders)} proyectos en la galería")
        debug_print(f"Proyecto actual expandido: {self.current_project_name}")

    def on_project_deleted(self, project_name):
        """Se ejecuta cuando se borra un proyecto completo"""
        debug_print(f"Proyecto borrado: {project_name}")

        # Buscar y remover el widget del proyecto
        for i, project_widget in enumerate(self.project_widgets):
            if project_widget.project_name == project_name:
                project_widget.setParent(None)
                project_widget.deleteLater()
                self.project_widgets.pop(i)
                break

        # Si no quedan proyectos, mostrar mensaje
        if not self.project_widgets:
            no_projects_label = QLabel(
                "<div style='text-align: center; color: #888888; font-size: 14px;'>"
                "<b>No hay proyectos en la galería</b><br><br>"
                "Toma algunos snapshots para empezar a llenar la galería."
                "</div>"
            )
            no_projects_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(no_projects_label)

    def get_gallery_path(self):
        """Obtiene la ruta de la carpeta snapshot_gallery"""
        try:
            script_dir = os.path.dirname(__file__)
            gallery_path = os.path.join(script_dir, "snapshot_gallery")
            return gallery_path
        except Exception as e:
            debug_print(f"Error al obtener gallery path: {e}")
            return None


def buscar_ventana_existente(nombre_objeto):
    """
    Busca si ya existe una ventana con el nombre de objeto especificado.
    Devuelve la ventana si existe y esta visible, None en caso contrario.
    """
    for widget in QApplication.instance().allWidgets():
        if (
            widget.objectName() == nombre_objeto
            and isinstance(widget, QWidget)
            and widget.isVisible()
        ):
            return widget
    return None


def open_snapshot_gallery():
    """Funcion principal que abre la ventana de galeria de snapshots"""
    global app, window

    debug_print("Abriendo galeria de snapshots...")

    # Verificar si ya existe una ventana abierta con el mismo nombre de objeto
    ventana_existente = buscar_ventana_existente("LGA_SnapshotGalleryWindow")

    if ventana_existente:
        # Si ya existe, activarla y traerla al frente
        debug_print(f"Ya existe una ventana con ID: {ventana_existente.winId()}")
        debug_print(
            f"Usando ventana existente con nombre de objeto: {ventana_existente.objectName()}"
        )
        ventana_existente.setWindowState(
            ventana_existente.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
        )
        ventana_existente.activateWindow()
        ventana_existente.raise_()
    else:
        # Si no existe, crear una nueva ventana
        app = QApplication.instance() or QApplication([])
        window = SnapshotGalleryWindow()
        window.show()


# --- Main Execution ---
if __name__ == "__main__":
    open_snapshot_gallery()
