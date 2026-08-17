"""
_______________________________________________________________________

  LGA_MediaManager_FileScanner v2.27 | Lega

  Escaneo del proyecto, tabla de medias y relink de archivos offline.

  v2.27: La ventana principal pasa al disenio nuevo. Aparece la columna
         '#', un id estable que no cambia al ordenar ni al filtrar: va
         ultima en indice logico y primera en pantalla, asi ninguna
         columna se corre. La celda de Status se dibuja con su punto de
         color a alto completo, la cabecera lleva el icono de orden -con
         el color de acento en la columna ordenada- y el ancho minimo de
         la ventana pasa a contemplar el pie, que se cortaba a la mitad
         de una palabra. El menu de Copy to deja de colgarse con
         setMenu(): la bandera HasMenu le reservaba a Qt el lugar de la
         flecha y el texto del boton terminaba encima del icono.
         Los paths dejan de
         ser un QLabel por celda y los dibuja PathDelegate: la tabla
         ordena por la columna 0, asi que el setItem de esa columna
         movia la fila y el setCellWidget de despues le colgaba el
         label a otra, que es por lo que los paths se veian sin color.
         Aparecen la fila de pastillas -Total, Offline, Unused,
         Outside, Online- que filtra por estado, el buscador con
         debounce que filtra por coincidencia parcial del path, y el
         pie con la leyenda y Rescan. El estado OK pasa a llamarse
         Online, Outside tiene dos colores segun el shot folder este
         activo o no, y los diez hexes de estado salen del modulo de
         estilo. Status se ordena por rango y no alfabeticamente, y
         Read numerico con las filas sin Read al final.
         La barra de herramientas pasa al disenio nuevo: icono, texto y
         el atajo escrito al lado, un separador antes de Delete y
         Settings con texto en vez del engranaje pelado. Explorer se
         llama Reveal y su atajo pasa a Alt+R. Los cuatro handlers que
         miraban solo la primera fila -Go to Read, Reveal, Relink y
         Copy to- trabajan con todas las filas seleccionadas, con las
         busquedas y las copias encadenadas de a una. Los botones se
         prenden segun lo que este elegido, y Relink deja de exigir
         Offline: se puede reapuntar un Read online a otro archivo.
         Deja de leer el .ini a mano y de derivar la carpeta del
         shot subiendo N niveles: la configuracion la normaliza
         LGA_MediaManager_config y el shot es una ruta explicita.
         Lo que se escanea son las scan locations resueltas contra
         disco, sin repetidas ni anidadas. El atajo del menu Copy
         to sale del campo shortcut y no del '&' del nombre, y el
         destino de la copia sale de la ruta de la location: si el
         comodin abre cero o varias carpetas no se copia, porque
         elegir una seria adivinar.
  v2.25: La busqueda del relink corre en un worker y el menu Copy to
         se rehace al guardar los ajustes. La config sale del .ini del
         usuario. La clave del depth es la que la ventana de ajustes
         lee -antes nunca coincidian- y el relink cubre nombres con
         varios grupos de '#', con corchetes propios y con frames
         negativos. La version sale de la barra: la muestra la ventana
         de ajustes. La letra de la tabla pasa a pixeles, la fila de
         botones lleva separacion propia y se van el boton '>' y los
         seis controles que desplegaba.

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

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore, horizontal_advance

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
QFont = QtGui.QFont
QFontMetrics = QtGui.QFontMetrics
QPainter = QtGui.QPainter
QPalette = QtGui.QPalette
QMovie = QtGui.QMovie
QScreen = QtGui.QScreen
QIcon = QtGui.QIcon
QHeaderView = QtWidgets.QHeaderView
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
Qt = QtCore.Qt
QRect = QtCore.QRect
QPoint = QtCore.QPoint
QSize = QtCore.QSize
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
import LGA_UI_Style_ToolPack as UIStyle


def _is_inside(hijo, padre):
    """Si `hijo` esta adentro de `padre`. Sin distinguir mayusculas."""
    a = os.path.normcase(os.path.normpath(hijo))
    b = os.path.normcase(os.path.normpath(padre))
    if a == b:
        return False
    try:
        # commonpath y no startswith: comparando texto, "shot_010" caia
        # adentro de "shot_01".
        return os.path.commonpath([a, b]) == b
    except ValueError:
        # Unidades distintas: no hay ancestro comun posible.
        return False
import LGA_MediaManager_config as mm_config
import LGA_MediaManager_paths as mm_paths
from LGA_MediaManager_config import get_read_path

try:
    from LGA_tooltip_helper import apply_tooltip_stylesheet
except ImportError:
    # La ventana funciona igual sin el helper; solo pierde el look estandar.
    def apply_tooltip_stylesheet(target=None):
        pass


# Los tooltips van en castellano y salen de aca, no hardcodeados en el widget,
# para que la migracion a bilingue sea un cambio de datos.
TOOLTIPS = {
    "go_to_read": "Selecciona el Read de este archivo en el Node Graph",
    "reveal": "Abre la carpeta en el explorador del sistema",
    "relink": "Busca el archivo y reapunta el Read",
    "copy_to": "Copia a una de las locations con Copy to",
    "delete": "Manda el archivo a la papelera",
    "settings": "Ajustes del Media Manager",
    # La ✕ del buscador.
    "search_clear": "Limpiar",
    "rescan": "Vuelve a escanear el proyecto desde cero",
    "search": "Filtra por coincidencia parcial del path",
    "pill_all": "Muestra todos los archivos, sin filtrar por estado",
    "pill_offline": "Solo los archivos que un Read referencia y no existen",
    "pill_unused": "Solo los archivos que existen y ningun Read usa",
    "pill_outside": "Solo los archivos que estan afuera",
    "pill_online": "Solo los archivos disponibles y usados por un Read",
}

# Los dos extremos donde va una accion adentro de un QLineEdit. Se resuelven
# aca porque en Qt6 los enums quedaron scopeados y el nombre pelado puede no
# existir segun la version de PySide con la que arranque Nuke.
try:
    LINEEDIT_LEADING = QLineEdit.LeadingPosition
    LINEEDIT_TRAILING = QLineEdit.TrailingPosition
except AttributeError:  # pragma: no cover - depende del binding
    LINEEDIT_LEADING = QLineEdit.ActionPosition.LeadingPosition
    LINEEDIT_TRAILING = QLineEdit.ActionPosition.TrailingPosition

# Textos VISIBLES de la leyenda del pie: en ingles, como toda la UI.
LEGEND_TEXTS = {
    "Offline": "Referenced by a Read but file is not available",
    "Unused": "File exists in a scan location but not used by any Read",
    "Outside": "File is outside the shot folder",
    "Online": "File is available and used by a Read",
}
# Con el shot folder apagado, Outside deja de significar "afuera del shot":
# si cambia lo que la palabra quiere decir, tiene que cambiar lo que dice.
LEGEND_OUTSIDE_INFO = "File is outside every scan location"

# ---------------------------------------------------------------------------
#                          Columnas de la tabla
# ---------------------------------------------------------------------------
# Los INDICES LOGICOS no cambian nunca: son los que usan los cinco archivos del
# Media Manager, incluidos el worker del escaneo y el hilo de borrado, que leen
# item(row, 0) para el path e item(row, 3) para el flag de carpeta borrable.
#
# La columna '#' del disenio nuevo se agrega al FINAL (indice 5) y despues se
# mueve al PRIMER lugar VISUAL con moveSection(). Es a proposito: en Qt el
# orden visual de las columnas es independiente del logico, asi que se ve
# primera sin correr un solo indice. Insertarla como columna 0 habria corrido
# los cinco indices en este archivo y ademas en LGA_MediaManager_utils, que
# lee las suyas por numero.
COL_PATH = 0
COL_READ = 1
COL_STATUS = 2
COL_FOLDER_DELETE = 3
COL_SEQUENCE = 4
COL_NUM = 5

# Anchos del disenio: `52 | 1fr (min 300) | 96 | 118`. El del path no se fija:
# es la que se estira.
COL_NUM_WIDTH = 52
COL_READ_WIDTH = 96
COL_STATUS_WIDTH = 118
COL_PATH_MIN_WIDTH = 300

# Cabecera: alto derivado del tamano de letra (fs + 25), el icono de orden a
# 13 px y su separacion del texto.
HEADER_HEIGHT_OFFSET = 25
HEADER_PADDING = 10
HEADER_ICON_SIZE = 13
HEADER_ICON_GAP = 6
# El icono va apagado salvo en la columna por la que se esta ordenando.
HEADER_ICON_OPACITY = 0.45

# Celda de Status: `padding 0 12`, `gap 8` y el punto de 9 px, a alto completo.
STATUS_CELL_PADDING = 12
STATUS_CELL_GAP = 8
STATUS_DOT_SIZE = 9

# El orden de la columna Status NO es alfabetico. Por texto quedaria
# Offline < Online < Unused, que no es el orden en que se leen los estados:
# primero lo que esta roto. La clave va en Qt.UserRole y la lee SortKeyItem.
STATUS_RANK = {"Offline": 0, "Unused": 1, "Outside": 2, "Online": 3}
# El mismo orden manda en las pastillas y en la leyenda del pie.
STATUS_ORDER = ("Offline", "Unused", "Outside", "Online")

# Separacion en pixeles entre los botones de la fila de herramientas. Vive aca
# y no en Metric del modulo de estilo porque es un valor a tunear a ojo: cuando
# quede firme conviene subirlo al modulo, que es donde van las medidas.
BUTTON_SPACING = 10

# Medidas de la barra de herramientas. Las tres estan fuera de Metric a
# proposito: el modulo tiene BUTTON_HEIGHT = 30 y RADIUS = 5, y subirlas ahi le
# cambiaria el look a las nueve tools ya migradas. Cuando Metric se versione con
# los valores del rediseño (ver §10 de las notas del port) estas se van.
TOOLBAR_BUTTON_HEIGHT = 42
TOOLBAR_ICON_SIZE = 17
# Aire a izquierda y derecha del contenido del boton, y separacion entre el
# icono y el texto.
TOOLBAR_PADDING = 16
TOOLBAR_ICON_GAP = 9
# El separador vertical que va antes de Delete.
TOOLBAR_SEPARATOR_HEIGHT = 26
# El disenio pide 13.5 y 11.5 px; Qt redondea los decimales en la hoja de
# estilo, asi que van enteros.
TOOLBAR_FONT_SIZE = 13
TOOLBAR_SHORTCUT_FONT_SIZE = 12

# Medidas de la fila de pastillas y del buscador. Mismo criterio que las de la
# barra: quedan aca hasta que Metric se versione con los valores del rediseño.
PILL_HEIGHT = 32
PILL_PADDING = 13
PILL_RADIUS = 16
PILL_GAP = 8
PILL_DOT_SIZE = 9
PILL_ICON_SIZE = 14
PILL_FONT_SIZE = 13
SEARCH_WIDTH = 300
SEARCH_HEIGHT = 34
SEARCH_ICON_SIZE = 15
SEARCH_FONT_SIZE = 13
# Sin debounce se rehace el filtro de cada fila por tecla apretada, y con
# miles de archivos eso se siente en el tipeo.
SEARCH_DEBOUNCE_MS = 150
# El cartel de "no hay coincidencias".
EMPTY_FONT_SIZE = 13
EMPTY_PADDING = 44

# Pie: leyenda de estados y Rescan.
FOOTER_GAP = 22
FOOTER_LEGEND_FONT_SIZE = 12
RESCAN_HEIGHT = 34
RESCAN_PADDING = 15
RESCAN_ICON_SIZE = 15
RESCAN_FONT_SIZE = 13

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
    tinted_icon,
    PathDelegate,
    RelinkSearchWorker,
    ScannerWorker,
    TransparentTextDelegate,
    LoadingWindow,
    CopyThread,
    DeleteThread,
)

# Importar SettingsWindow desde settings
from LGA_MediaManager_settings import SettingsWindow


def read_sort_key(texto):
    """
    La clave de orden de la columna Read.

    Se ordena NUMERICO -Read2 antes que Read12- y las filas sin Read van al
    final. Por texto, "Read12" caia antes que "Read2" y las filas sin Read se
    mezclaban en el medio con las que si tienen.
    """
    nombres = [n.strip() for n in (texto or "").split(",") if n.strip()]
    nombres = [n for n in nombres if n != "-"]
    if not nombres:
        # El 1 de adelante los manda al final sin importar el resto.
        return (1, 0, "")
    primero = nombres[0]
    numero = re.search(r"(\d+)\s*$", primero)
    return (0, int(numero.group(1)) if numero else 0, primero.lower())


class SortKeyItem(QTableWidgetItem):
    """
    Una celda que se ordena por la clave de Qt.UserRole y no por su texto.

    Qt ordena los QTableWidgetItem comparando el texto que muestran, que no
    sirve ni para Status -el orden es Offline < Unused < Outside < Online, no
    el alfabetico- ni para Read, que va numerico.
    """

    def __lt__(self, otro):
        mia = self.data(Qt.UserRole)
        suya = otro.data(Qt.UserRole) if isinstance(otro, QTableWidgetItem) else None
        if mia is None or suya is None:
            return super(SortKeyItem, self).__lt__(otro)
        try:
            return mia < suya
        except TypeError:
            # Claves de tipos distintos: no puede pasar, pero no vale colgar
            # el orden de la tabla entera por una celda mal cargada.
            return str(mia) < str(suya)


class StatusCellDelegate(QStyledItemDelegate):
    """
    La celda de Status: fondo a alto completo, punto de color y texto.

    No alcanzaba con el item pelado. El fondo del estado ES la informacion, y
    el disenio lo pide a alto completo con el punto de 9 px adelante y el texto
    a la izquierda, tres cosas que un QTableWidgetItem no sabe dibujar: el item
    solo pinta el rectangulo de fondo y centra el texto.

    Los colores salen de la ventana -status_bg(), status_bg_selected() y
    status_dot()- y no de una tabla propia, porque el color de Outside depende
    del shot folder y cambia sin que la tabla se toque.
    """

    def __init__(self, tabla, ventana, parent=None):
        super(StatusCellDelegate, self).__init__(parent or tabla)
        self.ventana = ventana

    def paint(self, painter, option, index):
        estado = index.data() or ""
        ventana = self.ventana
        Paleta = (getattr(ventana, "UI", None) or UIStyle.theme(None)).Color

        seleccionada = bool(option.state & QStyle.State_Selected)
        if not estado:
            # Celda sin estado -pasa mientras se puebla la fila-: sin esto
            # caia en el fondo por default, que es el verde de Online.
            painter.fillRect(
                option.rect,
                QColor(Paleta.SURFACE_SELECTED if seleccionada else Paleta.SURFACE),
            )
            return
        fondo = (
            ventana.status_bg_selected(estado)
            if seleccionada
            else ventana.status_bg(estado)
        )

        painter.save()
        painter.fillRect(option.rect, QColor(fondo))

        # El punto, centrado verticalmente en la fila.
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(ventana.status_dot(estado)))
        x = option.rect.left() + STATUS_CELL_PADDING
        y = option.rect.top() + (option.rect.height() - STATUS_DOT_SIZE) // 2
        painter.drawEllipse(x, y, STATUS_DOT_SIZE, STATUS_DOT_SIZE)

        # El texto arranca despues del punto y su separacion.
        painter.setPen(QColor(Paleta.TEXT_STRONG))
        painter.setFont(option.font)
        izquierda = STATUS_CELL_PADDING + STATUS_DOT_SIZE + STATUS_CELL_GAP
        painter.drawText(
            option.rect.adjusted(izquierda, 0, -STATUS_CELL_PADDING, 0),
            Qt.AlignVCenter | Qt.AlignLeft,
            estado,
        )
        painter.restore()

    def sizeHint(self, option, index):
        base = super(StatusCellDelegate, self).sizeHint(option, index)
        metrica = QFontMetrics(option.font)
        ancho = (
            STATUS_CELL_PADDING * 2
            + STATUS_DOT_SIZE
            + STATUS_CELL_GAP
            + horizontal_advance(metrica, index.data() or "")
        )
        return QSize(ancho, base.height())


class SortHeaderView(QHeaderView):
    """
    La cabecera de la tabla, con el icono de orden al lado de cada titulo.

    Se dibuja entera a mano en vez de dejarle la seccion al estilo nativo: el
    disenio pide el icono `chevrons-up-down` DESPUES del texto -Qt solo sabe
    poner el icono de un item antes-, apagado al 45% salvo en la columna por la
    que se esta ordenando, donde va con el color de acento. La flecha nativa de
    orden no se dibuja porque no se llama a la implementacion de la clase base;
    el orden en si lo sigue manejando Qt, que es quien recibe el click.
    """

    def __init__(self, tabla, ventana):
        super(SortHeaderView, self).__init__(Qt.Horizontal, tabla)
        self.ventana = ventana
        self.font_size = DEFAULT_FONT_SIZE
        self.setSectionsClickable(True)
        # Sin esto Qt hunde la seccion clickeada con el color del estilo del
        # host, que no es ninguno de los del tema.
        self.setHighlightSections(False)
        self.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.set_font_size(DEFAULT_FONT_SIZE)

    def set_font_size(self, tamano):
        """El alto de la cabecera se DERIVA del tamano de letra: fs + 25."""
        self.font_size = tamano
        self.setFixedHeight(tamano + HEADER_HEIGHT_OFFSET)
        self.viewport().update()

    def _fuente(self):
        fuente = QFont(self.font())
        # El disenio pide 12.5 px; Qt no dibuja medios pixeles.
        fuente.setPixelSize(max(1, self.font_size - 1))
        try:
            # En Qt6 el enum quedo scopeado y el nombre pelado puede no existir
            # segun la version de PySide con la que arranque Nuke.
            fuente.setWeight(QFont.DemiBold)
        except (AttributeError, TypeError):  # pragma: no cover - depende del binding
            fuente.setBold(True)
        return fuente

    def paintSection(self, painter, rect, logicalIndex):
        Paleta = (getattr(self.ventana, "UI", None) or UIStyle.theme(None)).Color
        modelo = self.model()
        texto = ""
        if modelo is not None:
            texto = modelo.headerData(logicalIndex, Qt.Horizontal) or ""
        ordenada = self.sortIndicatorSection() == logicalIndex

        painter.save()
        painter.fillRect(rect, QColor(Paleta.SURFACE_HEADER))
        painter.fillRect(
            QRect(rect.left(), rect.bottom(), rect.width(), 1),
            QColor(Paleta.BORDER),
        )

        fuente = self._fuente()
        painter.setFont(fuente)
        painter.setPen(
            QColor(Paleta.TEXT_STRONG if ordenada else Paleta.TEXT_HEADER)
        )

        if logicalIndex == COL_NUM:
            # El '#' va centrado y sin icono: es un id, no un dato por el que
            # uno ordene mirando la flecha.
            painter.drawText(rect, Qt.AlignCenter, texto)
            painter.restore()
            return

        ancho_texto = horizontal_advance(QFontMetrics(fuente), texto)

        x = rect.left() + HEADER_PADDING
        painter.drawText(
            QRect(x, rect.top(), ancho_texto, rect.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            texto,
        )

        icono = tinted_icon(
            "chevrons-up-down",
            Paleta.ACCENT_HOVER if ordenada else Paleta.TEXT_HEADER,
            HEADER_ICON_SIZE,
        )
        painter.setOpacity(1.0 if ordenada else HEADER_ICON_OPACITY)
        painter.drawPixmap(
            x + ancho_texto + HEADER_ICON_GAP,
            rect.top() + (rect.height() - HEADER_ICON_SIZE) // 2,
            icono.pixmap(HEADER_ICON_SIZE, HEADER_ICON_SIZE),
        )
        painter.restore()

    def sectionSizeFromContents(self, logicalIndex):
        """El ancho pedido tiene que incluir el icono, que Qt no ve."""
        base = super(SortHeaderView, self).sectionSizeFromContents(logicalIndex)
        if logicalIndex == COL_NUM:
            return base
        return QSize(
            base.width() + HEADER_PADDING * 2 + HEADER_ICON_GAP + HEADER_ICON_SIZE,
            base.height(),
        )


class CopyStepWindow(LoadingWindow):
    """
    La ventanita de "Copying..." de un paso de la tanda de copias.

    Avisa cuando el paso termino para poder encadenar el siguiente. El aviso
    cuelga del cierre de la ventanita y no de las senales del CopyThread
    porque la copia termina por cinco caminos distintos -fin, fin de archivo
    unico, cancelado, cancelado unico y error-, algunos de los cuales se
    emiten dos veces para el mismo archivo. Lo unico que hacen todos, siempre,
    es cerrar esta ventana.
    """

    def __init__(self, mensaje, parent, al_terminar):
        super(CopyStepWindow, self).__init__(mensaje, parent)
        self._al_terminar = al_terminar
        self._avisado = False

    def stop(self):
        super(CopyStepWindow, self).stop()
        if self._avisado:
            return
        self._avisado = True
        # Diferido: el callback abre la ventanita del paso siguiente, y
        # crearla adentro del cierre de esta las deja a las dos vivas.
        QTimer.singleShot(0, self._al_terminar)


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
        # Estado de la busqueda del relink: el worker en curso y su ventanita.
        # Van aparte de self.loading_window, que la comparten copia y borrado.
        self.relink_worker = None
        self.relink_loading_window = None
        # La tanda de relink: las rutas que faltan buscar, la carpeta elegida
        # una sola vez para todas, y lo que no aparecio, que se avisa junto al
        # final en vez de un cartel por archivo.
        self.relink_queue = []
        self.relink_directory = ""
        self.relink_missing = []
        # La tanda de copias, encadenada por la misma razon: una por vez.
        self.copy_queue = []
        self.copy_dest_folder = ""
        # Filtro de estado y busqueda. Se combinan con AND: la pastilla dice
        # que estados se ven y el buscador que paths, y una fila se muestra
        # solo si pasa los dos.
        self.status_filter = "all"
        self.search_query = ""
        self.status_pills = []
        # Un escaneo por vez: dos ScannerWorker escribiendo sobre la misma
        # tabla se pisan las filas.
        self._scan_running = False
        self.load_settings()  # Cargar settings del archivo .ini
        # El tema y el tamano de letra salen del .ini, asi que se resuelven
        # ANTES de armar la UI: la hoja de la tabla los usa al construirse.
        self.UI = UIStyle.theme(self.appearance.get("theme"))
        self.font_size = max(
            UIStyle.Metric.TABLE_FONT_SIZE_MIN,
            min(UIStyle.Metric.TABLE_FONT_SIZE_MAX,
                int(self.appearance.get("table_font_size", DEFAULT_FONT_SIZE))),
        )
        self.scan_folders = []
        # Un valor de arranque para project_folder: lo definitivo lo escribe
        # resolve_shot_folder() adentro del worker, pero hasta entonces hay
        # codigo que lo lee y no puede encontrarse sin el atributo.
        self.project_folder = self.nk_dir()
        if self.settings.get("load_error"):
            # Con el .ini ilegible lo que se cargo son los defaults y no la
            # configuracion del usuario. Se avisa aca y no se toca el archivo:
            # el guardado lo hace la ventana de ajustes, que vuelve a
            # preguntar antes de pisarlo.
            debug_print(
                "No se pudo leer la configuracion: %s" % self.settings["load_error"]
            )

        # Crear el scanner_worker después de que los atributos estén inicializados
        self.scanner_worker = ScannerWorker(self)

        # Asumimos que la inicialización es exitosa
        self.initialization_successful = True

        # Inicializar la UI
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.apply_window_background()

        # Crea y configura el status_label
        # self.status_label = QLabel("")
        # self.layout.addWidget(self.status_label)

        # ------------------------------------------------------------------
        #                      Barra de herramientas
        # ------------------------------------------------------------------
        # Cinco botones con icono + texto + el atajo escrito al lado, un
        # separador antes de Delete, y Settings a la derecha con texto y el
        # mismo estilo que los demas: antes era un engranaje pelado de 24x24
        # con la hoja puesta en 'border: none', que no se leia como boton.
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(BUTTON_SPACING)
        main_buttons_layout.setContentsMargins(0, 9, 0, 9)

        apply_tooltip_stylesheet(self)

        # Los botones se guardan para poder repintarlos cuando cambia el tema
        # sin tener que reabrir la ventana.
        self.toolbar_buttons = []

        # Ninguno es el boton de accion de la ventana -son una fila de
        # herramientas, cualquiera es valido segun lo que este seleccionado-
        # asi que van todos secundarios y no hay violeta: marcar uno seria
        # decir que Enter lo ejecuta.
        self.go_to_read_button = self._make_toolbar_button(
            "&Go to Read", "scan", "Alt + G", TOOLTIPS["go_to_read"]
        )
        # Antes se llamaba Explorer, con atajo Alt+E. El nombre nuevo dice lo
        # que hace y la letra acompania: Alt+R.
        self.reveal_button = self._make_toolbar_button(
            "&Reveal", "folder-open", "Alt + R", TOOLTIPS["reveal"]
        )
        self.relink_button = self._make_toolbar_button(
            "Re&link", "link-2", "Alt + L", TOOLTIPS["relink"]
        )
        self.copy_button = self._make_toolbar_button(
            "&Copy to…", "folder-input", "Alt + C", TOOLTIPS["copy_to"]
        )
        self.delete_button = self._make_toolbar_button(
            "&Delete", "trash-2", "Alt + D", TOOLTIPS["delete"], peligro=True
        )
        self.settings_button = self._make_toolbar_button(
            "Settings", "settings", "", TOOLTIPS["settings"]
        )

        # El menu de Copy to cuelga del boton: se abre al clickearlo o con
        # Alt+C, y el Alt+letra de cada location copia directo sin abrirlo.
        # Es un QPushButton y no el QToolButton de antes para que las seis
        # cajas de la barra sean el mismo widget y compartan hoja de estilo.
        self.copy_menu = QMenu(self)
        self.populate_copy_menu()
        # El menu NO se cuelga con setMenu(). Con menu puesto, Qt le marca al
        # boton la bandera HasMenu y le reserva el lugar de la flecha por
        # dentro, sin avisarle a la hoja de estilo: el padding-left que reserva
        # el icono dejaba de valer y el texto se dibujaba ENCIMA del icono, que
        # es lo que pasaba solo en este boton de los seis. Abriendolo a mano el
        # boton queda igual que los otros cinco, y de paso el menu se posiciona
        # donde lo quiere el disenio: alineado al borde izquierdo, 6 px abajo.
        self.copy_button.clicked.connect(self.show_copy_menu)
        # Con el menu abierto el boton queda hundido, que es lo que hacia solo
        # cuando el menu colgaba de el.
        self.copy_menu.aboutToHide.connect(
            lambda: self.copy_button.setDown(False)
        )

        self.go_to_read_button.clicked.connect(self.go_to_read)
        self.reveal_button.clicked.connect(self.reveal_selected)
        self.relink_button.clicked.connect(self.relink)
        self.delete_button.clicked.connect(self.delete_selected)
        self.settings_button.clicked.connect(self.show_settings_window)

        main_buttons_layout.addWidget(self.go_to_read_button)
        main_buttons_layout.addWidget(self.reveal_button)
        main_buttons_layout.addWidget(self.relink_button)
        main_buttons_layout.addWidget(self.copy_button)

        # Delete va del otro lado de un separador: es el unico de la fila que
        # toca archivos en disco.
        self.toolbar_separator = QFrame(self)
        self.toolbar_separator.setFixedSize(1, TOOLBAR_SEPARATOR_HEIGHT)
        # Sin esto Qt resuelve la hoja y no pinta un solo pixel, asi que el
        # separador quedaba invisible aunque su regla fuera correcta.
        self.toolbar_separator.setFrameShape(QFrame.NoFrame)
        self.toolbar_separator.setAttribute(Qt.WA_StyledBackground, True)
        main_buttons_layout.addWidget(self.toolbar_separator)
        main_buttons_layout.addWidget(self.delete_button)

        # Espacio flexible que empuja Settings hacia la derecha
        main_buttons_layout.addStretch(1)

        # La version ya no vive en la barra: estaba escrita a mano y se
        # desincronizaba del header. Ahora la muestra la ventana de ajustes,
        # leyendola del header del script principal.
        main_buttons_layout.addWidget(self.settings_button)

        self.apply_toolbar_stylesheet()

        # Agregar layout de botones al layout principal
        self.layout.addLayout(main_buttons_layout)

        # ------------------------------------------------------------------
        #                  Pastillas de estado y buscador
        # ------------------------------------------------------------------
        self.layout.addLayout(self.build_status_bar())

        # Crear la tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        # El '#' va ultimo en la lista porque su indice LOGICO es el 5. Lo que
        # lo pone primero en pantalla es el moveSection de mas abajo.
        self.table.setHorizontalHeaderLabels(
            ["File Path", "Read", "Status", "Folder_Delete", "Sequence", "#"]
        )
        # Cabecera propia: la nativa no sabe poner el icono de orden despues
        # del texto ni pintarlo con el color de acento en la columna ordenada.
        self.header = SortHeaderView(self.table, self)
        self.table.setHorizontalHeader(self.header)
        self.header.set_font_size(self.font_size)
        # El '#' se corre al primer lugar VISUAL. Los indices logicos siguen
        # siendo los de siempre, asi que ningun callsite se entera.
        self.header.moveSection(self.header.visualIndex(COL_NUM), 0)
        # self.table.setColumnHidden(1, True)
        # self.table.setColumnHidden(2, True)
        # self.table.horizontalHeader().setStretchLastSection(True) # Estira la ultima columna hasta la derecha de la ventana

        # Aplicar la configuracion inicial de visibilidad de columnas
        self.toggle_columns(False)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setSortingEnabled(True)
        # El encabezado vertical se oculta: dibujaba la POSICION visual de la
        # fila al lado de la columna `#`, que es un id ESTABLE, o sea dos
        # numeros distintos pegados diciendo cosas distintas. El diseno tiene
        # uno solo, y es el estable.
        self.table.verticalHeader().setVisible(False)
        # La barra depende de lo que este seleccionado, no de que haya filas:
        # cada boton pide una condicion distinta sobre el estado y el Read de
        # las filas elegidas.
        self.table.itemSelectionChanged.connect(self.update_button_states)
        # Con la ventana recien abierta no hay nada seleccionado, asi que la
        # barra arranca apagada salvo Settings.
        self.update_button_states()
        self.layout.addWidget(self.table)

        # Cambiar el color de fondo de la tabla y el tamano de la fuente.
        # La seleccion se deja transparente a proposito: si la hoja define un
        # background para 'item:selected' le gana al setBackground() del item y a
        # la paleta del delegado, y la columna Status pierde su color justo cuando
        # esta seleccionada. Del color de la seleccion se encarga
        # TransparentTextDelegate, que sabe que celdas tienen color propio.
        self.apply_table_stylesheet()

        # Aplicar el delegado a cada columna
        self.status_delegate = TransparentTextDelegate(self.table, self.UI)
        delegate = self.status_delegate
        for column in range(self.table.columnCount()):
            self.table.setItemDelegateForColumn(column, delegate)

        # La columna del path la dibuja PathDelegate, no un QLabel por celda:
        # el color y el resaltado de la busqueda se recalculan al pintar y
        # dejan de depender de que un widget siga colgado de su fila.
        self.path_delegate = PathDelegate(self.table, self.UI, self.font_size)
        self.table.setItemDelegateForColumn(COL_PATH, self.path_delegate)
        self.refresh_path_delegate()

        # La celda de Status la dibuja su propio delegado: fondo a alto
        # completo, punto de color y texto a la izquierda, que es lo que el
        # item pelado no sabe hacer.
        self.status_cell_delegate = StatusCellDelegate(self.table, self)
        self.table.setItemDelegateForColumn(COL_STATUS, self.status_cell_delegate)

        # El cartel de "no hay coincidencias" vive adentro del viewport de la
        # tabla, que es el espacio que tiene que ocupar cuando el filtro no
        # deja nada. Arranca escondido.
        self.empty_label = QLabel("", self.table.viewport())
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.hide()
        # Para reubicarlo cuando la tabla cambia de tamano.
        self.table.viewport().installEventFilter(self)

        # ------------------------------------------------------------------
        #                                 Pie
        # ------------------------------------------------------------------
        self.layout.addLayout(self.build_footer())
        self.apply_status_bar_stylesheet()
        self.apply_footer_stylesheet()

        self.setLayout(self.layout)
        # El alto de fila y la letra de la tabla se DERIVAN del ajuste, asi
        # que hay que aplicarlos al armar y no solo cuando el usuario toca el
        # tema: sin esto la tabla abria con el alto de fila default de Qt y
        # recien tomaba los 35 px del disenio despues de entrar a los ajustes.
        self.update_table_font_size(self.font_size)
        self.scan_project()
        self.adjust_window_size()

    # ----------------------------------------------------------------------
    #                       Barra de herramientas
    # ----------------------------------------------------------------------
    def _make_toolbar_button(self, texto, icono, atajo, tooltip, peligro=False):
        """
        Un boton de la barra: icono + texto + el atajo escrito al costado.

        El cartel del atajo NO sale del mnemonico. En Qt el '&' subraya la
        letra dentro del texto pero no imprime "Alt + G" al costado, asi que el
        atajo va en un QLabel gris adentro del layout del boton; el '&' se
        sigue declarando en el texto para que Alt+letra dispare.

        El icono tambien va en un QLabel y no con setIcon(): asi la separacion
        entre el icono y el texto es la del disenio y no la que Qt elige, que
        no se puede tocar por hoja de estilo.
        """
        boton = QPushButton(texto, self)
        boton.setToolTip(tooltip)
        boton.setFixedHeight(TOOLBAR_BUTTON_HEIGHT)
        boton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Sin foco no queda el rectangulo punteado encima del icono. El
        # mnemonico funciona igual: lo resuelve el atajo del boton, no el foco.
        boton.setFocusPolicy(Qt.NoFocus)

        icono_label = QLabel(boton)
        # Sin esto los labels se comen el click y el boton no dispara.
        icono_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        icono_label.setFixedSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE)

        atajo_label = None
        if atajo:
            atajo_label = QLabel(atajo, boton)
            atajo_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        fila = QHBoxLayout(boton)
        fila.setContentsMargins(TOOLBAR_PADDING, 0, TOOLBAR_PADDING, 0)
        fila.setSpacing(0)
        fila.addWidget(icono_label, 0, Qt.AlignVCenter)
        fila.addStretch(1)
        if atajo_label is not None:
            fila.addWidget(atajo_label, 0, Qt.AlignVCenter)

        self.toolbar_buttons.append(
            {
                "boton": boton,
                "icono": icono,
                "icono_label": icono_label,
                "atajo_label": atajo_label,
                "peligro": peligro,
            }
        )
        return boton

    def apply_toolbar_stylesheet(self):
        """
        La hoja de los botones de la barra, con los colores del tema activo.

        Sale a un metodo propio porque el tema se cambia desde los ajustes con
        la ventana abierta: si quedara escrita en el armado, la unica forma de
        aplicar un tema nuevo seria reabrir la herramienta.
        """
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        Paleta = UI.Color

        for datos in self.toolbar_buttons:
            boton = datos["boton"]
            atajo_label = datos["atajo_label"]

            if atajo_label is not None:
                atajo_label.setStyleSheet(
                    "QLabel { color: %s; font-size: %dpx; font-weight: 600;"
                    " background: transparent; border: none; }"
                    % (Paleta.TEXT_DIM, TOOLBAR_SHORTCUT_FONT_SIZE)
                )
            datos["icono_label"].setStyleSheet(
                "QLabel { background: transparent; border: none; }"
            )

            # El texto arranca despues del icono y termina antes del cartel del
            # atajo: los dos son labels flotando adentro del boton, y sin
            # reservarles el lugar por padding el texto les pasaria por encima.
            izquierda = TOOLBAR_PADDING + TOOLBAR_ICON_SIZE + TOOLBAR_ICON_GAP
            derecha = TOOLBAR_PADDING
            if atajo_label is not None:
                derecha += atajo_label.sizeHint().width() + TOOLBAR_ICON_GAP

            boton.setStyleSheet(
                "QPushButton {"
                " background-color: %(fondo)s;"
                " border: 1px solid %(borde)s;"
                " border-radius: %(radio)dpx;"
                " color: %(texto)s;"
                " font-size: %(letra)dpx;"
                " font-weight: 600;"
                " text-align: left;"
                " padding-left: %(izq)dpx;"
                " padding-right: %(der)dpx;"
                " }"
                "QPushButton:hover:!disabled {"
                " background-color: %(hover)s; border-color: %(borde_hover)s; }"
                # Con el menu abierto el boton queda hundido: es el unico
                # estado que Qt expone para eso en un QPushButton con menu.
                "QPushButton:pressed {"
                " background-color: %(hover)s; border-color: %(acento)s; }"
                "QPushButton:disabled { color: %(apagado)s; }"
                # La flecha del menu no va: el disenio no la tiene y ademas
                # descentraria el texto de Copy to contra los demas botones.
                "QPushButton::menu-indicator { image: none; width: 0px; }"
                % {
                    "fondo": Paleta.SURFACE_RAISED,
                    "borde": Paleta.BORDER_STRONG,
                    "radio": Metric.RADIUS_CONTROL,
                    "texto": Paleta.TEXT_STRONG,
                    "letra": TOOLBAR_FONT_SIZE,
                    "izq": izquierda,
                    "der": derecha,
                    "hover": Paleta.SURFACE_HOVER,
                    "borde_hover": Paleta.BORDER_HOVER,
                    "acento": Paleta.ACCENT_HOVER,
                    "apagado": Paleta.TEXT_DIM,
                }
            )
            # El ancho sale del texto y de los dos paddings, que ya reservan el
            # icono y el atajo: con un ancho fijo a ojo, el padding se comia la
            # primera letra de "Go to Read".
            boton.setFixedWidth(boton.sizeHint().width())

        if getattr(self, "toolbar_separator", None) is not None:
            self.toolbar_separator.setStyleSheet(
                "QFrame { background-color: %s; border: none; }" % Paleta.BORDER
            )

        self.refresh_toolbar_icons()
        # El ancho minimo depende del ancho de los botones, que acaba de
        # recalcularse: si se fija antes, el numero es el del tema anterior.
        self.update_minimum_width()

    def refresh_toolbar_icons(self):
        """
        Repinta los iconos segun el tema y segun si el boton esta habilitado.

        Los SVG de trazo se tienen que volver a generar para cambiarles el
        color: Qt no atenua un QLabel deshabilitado como si atenua un QIcon.
        """
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        Paleta = UI.Color
        for datos in self.toolbar_buttons:
            if not datos["boton"].isEnabled():
                color = Paleta.TEXT_DIM
            elif datos["peligro"]:
                # El unico icono con color propio: Delete es el que no se
                # puede deshacer.
                color = Paleta.ERROR
            else:
                color = Paleta.TEXT
            datos["icono_label"].setPixmap(
                tinted_icon(datos["icono"], color, TOOLBAR_ICON_SIZE).pixmap(
                    TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE
                )
            )
            # El cartel del atajo se queda en TEXT_DIM en los dos estados: ya
            # es el texto mas apagado del boton y bajarlo mas lo borra.

    def update_minimum_width(self):
        """
        Que la ventana no pueda achicarse hasta cortar la barra ni la leyenda.

        Son dos filas de ancho fijo que no envuelven: con la ventana angosta el
        ultimo boton -justamente el de los ajustes- se sale de la vista, y la
        leyenda del pie se corta a la mitad de una palabra
        ("File is outside the sho..."). Manda la mas ancha de las dos.
        """
        if not getattr(self, "toolbar_buttons", None):
            return
        ancho = sum(datos["boton"].width() for datos in self.toolbar_buttons)
        # Los cinco espacios entre botones, mas el del separador.
        ancho += BUTTON_SPACING * (len(self.toolbar_buttons) + 1)
        ancho += 1  # el separador vertical

        ancho = max(ancho, self.footer_minimum_width())

        margenes = self.layout.contentsMargins()
        ancho += margenes.left() + margenes.right()

        # Un minimo mas ancho que la pantalla deja la ventana sin poder
        # moverse. Si no entra, que se corte: es preferible a eso.
        pantalla = QApplication.primaryScreen()
        if pantalla is not None:
            ancho = min(ancho, int(pantalla.availableGeometry().width() * 0.95))
        self.setMinimumWidth(ancho)

    def footer_minimum_width(self):
        """
        El ancho que necesita el pie para que no se corte ningun texto.

        Se mide sobre los labels y no con el sizeHint del layout porque el pie
        se arma antes de que la ventana tenga geometria y ahi el layout todavia
        no sabe cuanto mide.
        """
        entradas = getattr(self, "legend_entries", None)
        if not entradas:
            return 0
        ancho = 0
        for entrada in entradas:
            # El punto, el nombre del estado y su explicacion, con la
            # separacion de adentro de cada entrada.
            ancho += PILL_DOT_SIZE + PILL_GAP * 2
            ancho += entrada["nombre"].sizeHint().width()
            ancho += entrada["texto"].sizeHint().width()
        # La separacion entre entradas y la que las despega del Rescan.
        ancho += FOOTER_GAP * len(entradas)
        if getattr(self, "rescan_button", None) is not None:
            ancho += self.rescan_button.sizeHint().width()
        return ancho

    # ----------------------------------------------------------------------
    #                   Pastillas de estado y buscador
    # ----------------------------------------------------------------------
    def build_status_bar(self):
        """
        La fila de pastillas y el buscador, que reemplaza a los controles
        viejos.

        Las pastillas filtran por estado y el buscador por coincidencia
        parcial del path; los dos se combinan con AND.
        """
        fila = QHBoxLayout()
        fila.setSpacing(PILL_GAP)
        fila.setContentsMargins(0, 0, 0, 6)

        # Total va con el icono de archivo y no con un punto: no es un estado,
        # es la ausencia de filtro.
        fila.addWidget(
            self._make_status_pill("all", "Total", TOOLTIPS["pill_all"], icono="file")
        )
        for estado in STATUS_ORDER:
            fila.addWidget(
                self._make_status_pill(
                    estado, estado, TOOLTIPS["pill_%s" % estado.lower()]
                )
            )

        fila.addStretch(1)

        # El buscador no lleva boton de filtro: filtra al tipear.
        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText("Filter paths…")
        self.search_field.setToolTip(TOOLTIPS["search"])
        self.search_field.setFixedSize(SEARCH_WIDTH, SEARCH_HEIGHT)
        self.search_field.setClearButtonEnabled(False)
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        self.search_field.addAction(
            tinted_icon("search", UI.Color.TEXT_DIM, SEARCH_ICON_SIZE),
            LINEEDIT_LEADING,
        )
        # La ✕ existe solo cuando hay texto: sin texto no hay nada que limpiar
        # y un boton que no hace nada es peor que ninguno.
        self.search_clear_action = self.search_field.addAction(
            tinted_icon("x", UI.Color.TEXT_DIM, SEARCH_ICON_SIZE),
            LINEEDIT_TRAILING,
        )
        self.search_clear_action.setToolTip(TOOLTIPS["search_clear"])
        self.search_clear_action.setVisible(False)
        self.search_clear_action.triggered.connect(self.clear_search)

        # El filtro NO corre en cada tecla: sin debounce se recorre la tabla
        # entera por caracter tipeado.
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self.search_timer.timeout.connect(self.apply_search)
        self.search_field.textChanged.connect(self.on_search_text_changed)
        # Escape adentro del campo limpia la busqueda en vez de cerrar la
        # ventana, que es lo que hace el Escape de la ventana.
        self.search_field.installEventFilter(self)

        fila.addWidget(self.search_field)
        return fila

    def _make_status_pill(self, clave, etiqueta, tooltip, icono=""):
        """
        Una pastilla: punto de color -o icono-, nombre del estado y contador.

        El contador va en un QLabel aparte y no adentro del texto del boton
        porque tiene su propio color: un QPushButton pinta todo su texto de un
        solo color.
        """
        boton = QPushButton(etiqueta, self)
        boton.setToolTip(tooltip)
        boton.setFixedHeight(PILL_HEIGHT)
        boton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        boton.setFocusPolicy(Qt.NoFocus)
        boton.setCursor(Qt.PointingHandCursor)

        punto = QLabel(boton)
        punto.setAttribute(Qt.WA_TransparentForMouseEvents)
        if icono:
            punto.setFixedSize(PILL_ICON_SIZE, PILL_ICON_SIZE)
        else:
            punto.setFixedSize(PILL_DOT_SIZE, PILL_DOT_SIZE)

        contador = QLabel("0", boton)
        contador.setAttribute(Qt.WA_TransparentForMouseEvents)

        caja = QHBoxLayout(boton)
        caja.setContentsMargins(PILL_PADDING, 0, PILL_PADDING, 0)
        caja.setSpacing(0)
        caja.addWidget(punto, 0, Qt.AlignVCenter)
        caja.addStretch(1)
        caja.addWidget(contador, 0, Qt.AlignVCenter)

        datos = {
            "clave": clave,
            "boton": boton,
            "punto": punto,
            "contador": contador,
            "icono": icono,
        }
        self.status_pills.append(datos)
        boton.clicked.connect(lambda checked=False, c=clave: self.on_pill_clicked(c))
        return boton

    def apply_status_bar_stylesheet(self):
        """La hoja de las pastillas y del buscador, con el tema activo."""
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        Paleta = UI.Color

        for datos in self.status_pills:
            clave = datos["clave"]
            activa = clave != "all" and clave == self.status_filter

            if datos["icono"]:
                datos["punto"].setPixmap(
                    tinted_icon(
                        datos["icono"], Paleta.TEXT, PILL_ICON_SIZE
                    ).pixmap(PILL_ICON_SIZE, PILL_ICON_SIZE)
                )
                datos["punto"].setStyleSheet(
                    "QLabel { background: transparent; border: none; }"
                )
            else:
                datos["punto"].setStyleSheet(
                    "QLabel { background-color: %s; border: none;"
                    " border-radius: %dpx; }"
                    % (self.status_dot(clave), PILL_DOT_SIZE // 2)
                )

            datos["contador"].setStyleSheet(
                "QLabel { color: %s; font-size: %dpx; font-weight: 600;"
                " background: transparent; border: none; }"
                % (Paleta.TEXT_STRONG, PILL_FONT_SIZE)
            )

            # Igual que en la barra: el punto y el contador flotan adentro del
            # boton, asi que hay que reservarles el lugar por padding para que
            # el texto no les pase por encima.
            ancho_punto = datos["punto"].width()
            izquierda = PILL_PADDING + ancho_punto + PILL_GAP
            derecha = (
                PILL_PADDING + datos["contador"].sizeHint().width() + PILL_GAP
            )

            datos["boton"].setStyleSheet(
                "QPushButton {"
                " background-color: %(fondo)s;"
                " border: 1px solid %(borde)s;"
                " border-radius: %(radio)dpx;"
                " color: %(texto)s;"
                " font-size: %(letra)dpx;"
                " text-align: left;"
                " padding-left: %(izq)dpx;"
                " padding-right: %(der)dpx;"
                " }"
                "QPushButton:hover { background-color: %(hover)s; }"
                % {
                    # La pastilla activa se distingue por fondo y borde; Total
                    # NUNCA se marca: es el estado sin filtro, no una opcion
                    # elegida, y marcado parecia decir algo que no decia.
                    "fondo": Paleta.SURFACE_RAISED if activa else "transparent",
                    "borde": Paleta.BORDER_HOVER if activa else "transparent",
                    "radio": PILL_RADIUS,
                    "texto": Paleta.TEXT_STRONG if activa else Paleta.TEXT,
                    "letra": PILL_FONT_SIZE,
                    "izq": izquierda,
                    "der": derecha,
                    "hover": Paleta.SURFACE_HOVER,
                }
            )
            datos["boton"].setFixedWidth(datos["boton"].sizeHint().width())

        if getattr(self, "search_field", None) is not None:
            self.search_field.setStyleSheet(
                "QLineEdit {"
                " background-color: %(fondo)s;"
                " border: 1px solid %(borde)s;"
                " border-radius: %(radio)dpx;"
                " color: %(texto)s;"
                " font-size: %(letra)dpx;"
                " padding: 0 6px;"
                " }"
                "QLineEdit:focus { border-color: %(foco)s; }"
                % {
                    "fondo": Paleta.SURFACE,
                    "borde": Paleta.BORDER_STRONG,
                    "radio": Metric.RADIUS_CONTROL,
                    "texto": Paleta.TEXT_STRONG,
                    "letra": SEARCH_FONT_SIZE,
                    "foco": Paleta.ACCENT_HOVER,
                }
            )

        if getattr(self, "empty_label", None) is not None:
            self.empty_label.setStyleSheet(
                "QLabel { color: %s; font-size: %dpx; background: transparent;"
                " padding: %dpx 0; }"
                % (Paleta.TEXT_DIM, EMPTY_FONT_SIZE, EMPTY_PADDING)
            )

    def status_dot(self, estado):
        """El color del punto de un estado, para las pastillas y la leyenda."""
        Paleta = (getattr(self, "UI", None) or UIStyle.theme(None)).Color
        if estado == "Offline":
            return Paleta.DOT_ERROR
        if estado == "Unused":
            return Paleta.DOT_WARNING
        if estado == "Outside":
            # Dos significados, dos colores: con shot folder activo estar
            # afuera es un error, y sin el es apenas un dato.
            return (
                Paleta.DOT_OUTSIDE
                if self.shot_folder_enabled()
                else Paleta.DOT_OUTSIDE_INFO
            )
        if estado == "Online":
            return Paleta.DOT_OK
        return Paleta.TEXT_DIM

    def status_bg(self, estado):
        """El fondo de la celda de Status. Sale del tema, no de un hex suelto."""
        Paleta = (getattr(self, "UI", None) or UIStyle.theme(None)).Color
        if estado == "Offline":
            return Paleta.ERROR_BG
        if estado == "Unused":
            return Paleta.WARNING_BG
        if estado == "Outside":
            return (
                Paleta.OUTSIDE_BG
                if self.shot_folder_enabled()
                else Paleta.OUTSIDE_BG_INFO
            )
        return Paleta.OK_BG

    def status_bg_selected(self, estado):
        """
        El fondo de la celda de Status cuando la fila esta elegida.

        Es el mismo color mezclado al 50% contra el gris de la seleccion: sin
        esto la barra de seleccion quedaba cortada justo en la ultima columna.
        La mezcla ya viene derivada por tema en el modulo de estilo.
        """
        Paleta = (getattr(self, "UI", None) or UIStyle.theme(None)).Color
        if estado == "Offline":
            return Paleta.ERROR_BG_SELECTED
        if estado == "Unused":
            return Paleta.WARNING_BG_SELECTED
        if estado == "Outside":
            return (
                Paleta.OUTSIDE_BG_SELECTED
                if self.shot_folder_enabled()
                else Paleta.OUTSIDE_BG_INFO_SELECTED
            )
        return Paleta.OK_BG_SELECTED

    def shot_folder_enabled(self):
        """Si el shot folder esta activo, que es lo que define que es Outside."""
        return bool((getattr(self, "shot", None) or {}).get("enabled", True))

    def set_row_status(self, row, estado):
        """
        Escribe el estado de una fila: texto, color de fondo y clave de orden.

        Sale a un metodo propio porque el estado se escribe desde cinco
        lugares -el escaneo, el relink y las tres variantes de la copia- y
        antes cada uno repetia el texto y su hex a mano.
        """
        item = self.table.item(row, COL_STATUS)
        if item is None:
            item = SortKeyItem(estado)
            # A la izquierda y no centrado: el punto de color va adelante del
            # texto, y con el texto centrado los dos quedaban separados.
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, COL_STATUS, item)
        else:
            item.setText(estado)
        item.setData(Qt.UserRole, STATUS_RANK.get(estado, len(STATUS_RANK)))
        item.setBackground(QColor(self.status_bg(estado)))
        return item

    def repaint_status_column(self):
        """
        Repinta los fondos de Status con el tema y el shot folder actuales.

        Hace falta cuando cambia el tema y cuando se prende o se apaga el shot
        folder: los dos cambian el color de Outside sin tocar la tabla.
        """
        if getattr(self, "table", None) is None:
            return
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_STATUS)
            if item is not None:
                item.setBackground(QColor(self.status_bg(item.text())))

    def assign_row_ids(self):
        """
        Numera la columna '#'.

        El numero es un ID ESTABLE y no la posicion visual: se asigna con la
        tabla en el orden en que se cargo -o sea con el orden apagado, antes
        del primer sortByColumn- y despues no se vuelve a tocar, asi que
        ordenar o filtrar no lo cambia. Por eso ordenar por '#' devuelve la
        tabla al orden de carga.
        """
        if getattr(self, "table", None) is None:
            return
        Paleta = (getattr(self, "UI", None) or UIStyle.theme(None)).Color
        for row in range(self.table.rowCount()):
            numero = row + 1
            item = self.table.item(row, COL_NUM)
            if item is None:
                # SortKeyItem para que ordene por el numero y no por el texto:
                # por texto, "10" caia antes que "9".
                item = SortKeyItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, COL_NUM, item)
            item.setText(str(numero))
            item.setData(Qt.UserRole, numero)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QBrush(QColor(Paleta.TEXT_DIM)))

    def repaint_row_numbers(self):
        """
        Repinta el '#' con el tema actual, SIN volver a numerar.

        Renumerar aca cambiaria los ids cada vez que se cambia el tema, porque
        para entonces la tabla ya no esta en el orden en que se cargo.
        """
        if getattr(self, "table", None) is None:
            return
        Paleta = (getattr(self, "UI", None) or UIStyle.theme(None)).Color
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_NUM)
            if item is not None:
                item.setForeground(QBrush(QColor(Paleta.TEXT_DIM)))

    def update_status_counts(self):
        """
        Los contadores de las pastillas, sobre el TOTAL.

        No los afecta el buscador: son cuantos archivos hay de cada estado, no
        cuantos se ven. Total es siempre la cantidad de filas cargadas.
        """
        if not getattr(self, "status_pills", None):
            return
        cuentas = {estado: 0 for estado in STATUS_ORDER}
        total = self.table.rowCount()
        for row in range(total):
            estado = self.row_status(row)
            if estado in cuentas:
                cuentas[estado] += 1
        for datos in self.status_pills:
            clave = datos["clave"]
            datos["contador"].setText(
                str(total if clave == "all" else cuentas.get(clave, 0))
            )
        self.apply_status_bar_stylesheet()

    def on_pill_clicked(self, clave):
        """Cambia el filtro de estado. Total apaga el filtro."""
        self.status_filter = clave
        self.apply_status_bar_stylesheet()
        self.apply_filters()

    def on_search_text_changed(self, texto):
        """Solo agenda el filtro: quien filtra es apply_search, con debounce."""
        self.search_clear_action.setVisible(bool(texto))
        self.search_timer.start()

    def clear_search(self):
        """Limpia el buscador y filtra en el acto, sin esperar el debounce."""
        self.search_field.clear()
        self.search_timer.stop()
        self.apply_search()
        self.search_field.setFocus()

    def apply_search(self):
        """
        Toma lo escrito y refiltra.

        El strip() es previo a propósito: un espacio suelto no es una busqueda
        y no tiene que vaciar la tabla.
        """
        self.search_query = self.search_field.text().strip()
        if getattr(self, "path_delegate", None) is not None:
            # El delegado resalta lo buscado adentro del path coloreado.
            self.path_delegate.set_query(self.search_query)
            self.table.viewport().update()
        self.apply_filters()

    def apply_filters(self):
        """
        Muestra y esconde filas segun el estado elegido y lo buscado.

        Los dos filtros se combinan con AND. La busqueda es coincidencia
        parcial sobre el path completo, sin distinguir mayusculas.
        """
        if getattr(self, "table", None) is None:
            return
        buscado = (self.search_query or "").lower()
        visibles = 0
        for row in range(self.table.rowCount()):
            pasa_estado = (
                self.status_filter == "all"
                or self.row_status(row) == self.status_filter
            )
            pasa_texto = not buscado or buscado in self.row_path(row).lower()
            visible = pasa_estado and pasa_texto
            self.table.setRowHidden(row, not visible)
            if visible:
                visibles += 1

        # Las filas escondidas SIGUEN seleccionadas y selectedItems() las
        # devuelve: sin limpiar la seleccion, Delete borraria archivos que el
        # usuario no tiene a la vista.
        self.table.clearSelection()
        self.update_button_states()
        self.update_empty_label(visibles)

    def select_first_visible_row(self):
        """Deja elegida la primera fila que se ve, si hay alguna."""
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                self.table.selectRow(row)
                return

    def update_empty_label(self, visibles):
        """El cartel de "no hay coincidencias", solo cuando hay algo buscado."""
        if getattr(self, "empty_label", None) is None:
            return
        if visibles == 0 and self.search_query:
            self.empty_label.setText('No paths match "%s"' % self.search_query)
            self.position_empty_label()
            self.empty_label.show()
        else:
            self.empty_label.hide()

    def position_empty_label(self):
        """Lo estira sobre el viewport de la tabla para que quede centrado."""
        if getattr(self, "empty_label", None) is None:
            return
        self.empty_label.setGeometry(self.table.viewport().rect())

    def eventFilter(self, obj, event):
        """
        Dos cosas puntuales que no salen de una senal.

        Escape adentro del buscador limpia la busqueda -y no cierra la
        ventana, que es lo que hace el Escape de afuera-, y el cartel de
        "no hay coincidencias" se reubica cuando la tabla cambia de tamano.
        """
        if obj is getattr(self, "search_field", None):
            if event.type() == QtCore.QEvent.KeyPress and (
                event.key() == Qt.Key_Escape
            ):
                self.clear_search()
                return True
        elif getattr(self, "table", None) is not None and (
            obj is self.table.viewport()
        ):
            if event.type() == QtCore.QEvent.Resize:
                self.position_empty_label()
        return super(FileScanner, self).eventFilter(obj, event)

    def refresh_path_delegate(self):
        """
        Le pasa al delegado el ancla del coloreo y el tema.

        El ancla son los segmentos de la carpeta del shot: lo que coincide con
        ella va en violeta y el resto cicla la paleta, que es lo que hace ver
        de un vistazo donde deja de ser este shot.
        """
        # El de la columna Status va junto: su tabla de fondos seleccionados
        # sale del tema, asi que si cambia el tema hay que rearmarla.
        if getattr(self, "status_delegate", None) is not None:
            self.status_delegate.set_theme(self.UI)
        if getattr(self, "path_delegate", None) is None:
            return
        self.path_delegate.set_theme(self.UI, self.font_size)
        try:
            self.path_delegate.set_shot_segments(
                mm_paths.shot_segments(self.shot, self.nk_dir())
            )
        except Exception as problema:
            debug_print("No se pudo resolver el ancla del shot: %s" % problema)
            self.path_delegate.set_shot_segments([])
        self.table.viewport().update()

    # ----------------------------------------------------------------------
    #                                 Pie
    # ----------------------------------------------------------------------
    def build_footer(self):
        """
        La leyenda de los estados y el boton Rescan.

        "Last scan: ..." no va: la hora del ultimo escaneo no cambia ninguna
        decision del usuario.
        """
        fila = QHBoxLayout()
        fila.setSpacing(FOOTER_GAP)
        fila.setContentsMargins(0, 6, 0, 0)

        self.legend_entries = []
        for estado in STATUS_ORDER:
            caja = QHBoxLayout()
            caja.setSpacing(PILL_GAP)
            caja.setContentsMargins(0, 0, 0, 0)

            punto = QLabel(self)
            punto.setFixedSize(PILL_DOT_SIZE, PILL_DOT_SIZE)
            nombre = QLabel(estado, self)
            texto = QLabel(LEGEND_TEXTS[estado], self)

            caja.addWidget(punto, 0, Qt.AlignVCenter)
            caja.addWidget(nombre, 0, Qt.AlignVCenter)
            caja.addWidget(texto, 0, Qt.AlignVCenter)
            fila.addLayout(caja)

            self.legend_entries.append(
                {"estado": estado, "punto": punto, "nombre": nombre, "texto": texto}
            )

        fila.addStretch(1)

        self.rescan_button = QPushButton("Rescan", self)
        self.rescan_button.setToolTip(TOOLTIPS["rescan"])
        self.rescan_button.setFixedHeight(RESCAN_HEIGHT)
        self.rescan_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.rescan_button.setFocusPolicy(Qt.NoFocus)
        self.rescan_icon = QLabel(self.rescan_button)
        self.rescan_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.rescan_icon.setFixedSize(RESCAN_ICON_SIZE, RESCAN_ICON_SIZE)
        caja_rescan = QHBoxLayout(self.rescan_button)
        caja_rescan.setContentsMargins(RESCAN_PADDING, 0, RESCAN_PADDING, 0)
        caja_rescan.setSpacing(0)
        caja_rescan.addWidget(self.rescan_icon, 0, Qt.AlignVCenter)
        caja_rescan.addStretch(1)
        self.rescan_button.clicked.connect(self.rescan)
        fila.addWidget(self.rescan_button)

        return fila

    def apply_footer_stylesheet(self):
        """La hoja del pie, con los colores del tema activo."""
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        Paleta = UI.Color

        for entrada in getattr(self, "legend_entries", []):
            entrada["punto"].setStyleSheet(
                "QLabel { background-color: %s; border: none;"
                " border-radius: %dpx; }"
                % (self.status_dot(entrada["estado"]), PILL_DOT_SIZE // 2)
            )
            entrada["nombre"].setStyleSheet(
                "QLabel { color: %s; font-size: %dpx; font-weight: 600;"
                " background: transparent; }"
                % (Paleta.TEXT_STRONG, PILL_FONT_SIZE)
            )
            entrada["texto"].setStyleSheet(
                "QLabel { color: %s; font-size: %dpx; background: transparent; }"
                % (Paleta.TEXT_DIM, FOOTER_LEGEND_FONT_SIZE)
            )
        self.update_legend_texts()

        if getattr(self, "rescan_button", None) is not None:
            izquierda = RESCAN_PADDING + RESCAN_ICON_SIZE + PILL_GAP
            self.rescan_button.setStyleSheet(
                "QPushButton {"
                " background-color: %(fondo)s;"
                " border: 1px solid %(borde)s;"
                " border-radius: %(radio)dpx;"
                " color: %(texto)s;"
                " font-size: %(letra)dpx;"
                " font-weight: 600;"
                " text-align: left;"
                " padding-left: %(izq)dpx;"
                " padding-right: %(der)dpx;"
                " }"
                "QPushButton:hover:!disabled {"
                " background-color: %(hover)s; border-color: %(borde_hover)s; }"
                "QPushButton:disabled { color: %(apagado)s; }"
                % {
                    "fondo": Paleta.SURFACE_RAISED,
                    "borde": Paleta.BORDER_STRONG,
                    "radio": Metric.RADIUS_CONTROL,
                    "texto": Paleta.TEXT_STRONG,
                    "letra": RESCAN_FONT_SIZE,
                    "izq": izquierda,
                    "der": RESCAN_PADDING,
                    "hover": Paleta.SURFACE_HOVER,
                    "borde_hover": Paleta.BORDER_HOVER,
                    "apagado": Paleta.TEXT_DIM,
                }
            )
            color_icono = (
                Paleta.TEXT if self.rescan_button.isEnabled() else Paleta.TEXT_DIM
            )
            self.rescan_icon.setStyleSheet(
                "QLabel { background: transparent; border: none; }"
            )
            self.rescan_icon.setPixmap(
                tinted_icon("refresh-cw", color_icono, RESCAN_ICON_SIZE).pixmap(
                    RESCAN_ICON_SIZE, RESCAN_ICON_SIZE
                )
            )
            self.rescan_button.setFixedWidth(self.rescan_button.sizeHint().width())

        # El pie puede ser mas ancho que la barra, asi que el minimo de la
        # ventana se recalcula aca tambien: cuando la barra lo fijo, el pie
        # todavia no existia.
        self.update_minimum_width()

    def update_legend_texts(self):
        """
        El texto de Outside acompania al toggle del shot folder.

        Con el shot apagado la palabra deja de querer decir "afuera del shot",
        asi que decirlo igual seria mentir.
        """
        for entrada in getattr(self, "legend_entries", []):
            if entrada["estado"] != "Outside":
                continue
            entrada["texto"].setText(
                LEGEND_TEXTS["Outside"]
                if self.shot_folder_enabled()
                else LEGEND_OUTSIDE_INFO
            )

    def rescan(self):
        """
        Vuelve a escanear desde cero.

        No alcanza con volver a llamar a scan_project(): esa funcion no limpia
        nada, add_file_to_table agrega a partir de rowCount(), y
        _processed_files_session vive toda la sesion, asi que un segundo
        escaneo no agregaba ni una fila nueva.
        """
        if self._scan_running:
            debug_print("Ya hay un escaneo corriendo: se ignora el Rescan")
            return

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.matched_reads = []
        # Sin esto, un archivo recien copiado a una scan location no aparece:
        # el dedup de la sesion lo sigue dando por procesado.
        self._processed_files_session = set()
        self.update_status_counts()
        self.scan_project()

    # ----------------------------------------------------------------------
    #                     Lectura de la seleccion
    # ----------------------------------------------------------------------
    def selected_rows(self):
        """
        Las filas seleccionadas, sin repetir y en orden.

        La seleccion es por fila pero selectedItems() devuelve una celda por
        columna visible, asi que leer selected_items[0], [1] y [2] no daba
        "las tres celdas de la fila" sino las tres primeras celdas de la
        PRIMERA fila, y todo lo demas seleccionado se ignoraba en silencio.
        """
        # Por el modelo y no por selectedItems(): ese devuelve una celda por
        # columna, o sea cinco objetos por fila, y esto se llama en cada
        # cambio de seleccion sobre una tabla que puede tener miles de filas.
        modelo = self.table.selectionModel()
        if modelo is not None:
            return sorted(indice.row() for indice in modelo.selectedRows())
        filas = set()
        for item in self.table.selectedItems():
            filas.add(self.table.row(item))
        return sorted(filas)

    def row_path(self, row):
        """La ruta de una fila, o cadena vacia si la celda no existe."""
        item = self.table.item(row, COL_PATH)
        return item.text() if item is not None else ""

    def row_read(self, row):
        """El o los nodos Read de una fila. '-' cuando no hay ninguno."""
        item = self.table.item(row, COL_READ)
        return item.text() if item is not None else "-"

    def row_status(self, row):
        """El estado de una fila: Offline, Outside, Unused u Online."""
        item = self.table.item(row, COL_STATUS)
        return item.text() if item is not None else ""

    def row_read_names(self, row):
        """Los nombres de nodo de una fila, ya separados y sin el '-'."""
        texto = self.row_read(row)
        if not texto or texto == "-":
            return []
        return [nombre.strip() for nombre in texto.split(",") if nombre.strip()]

    def update_button_states(self):
        """
        Prende y apaga la barra segun lo que este seleccionado.

        Cada boton pide una condicion propia; no alcanza con "hay seleccion".
        Los guards de adentro de cada handler se quedan igual como red de
        seguridad, porque el atajo Alt+letra dispara aunque el boton este
        apagado en algunas versiones de Qt.
        """
        # Se llama tambien desde on_settings_saved, que puede correr antes de
        # que la barra o la tabla existan.
        if not getattr(self, "toolbar_buttons", None):
            return
        if getattr(self, "table", None) is None:
            return

        filas = self.selected_rows()
        estados = [self.row_status(fila) for fila in filas]
        hay_seleccion = bool(filas)
        ninguno_offline = hay_seleccion and "Offline" not in estados
        algun_read = any(self.row_read_names(fila) for fila in filas)
        todos_outside = hay_seleccion and all(
            estado == "Outside" for estado in estados
        )
        hay_destinos = bool(getattr(self, "copy_options", None))

        self.go_to_read_button.setEnabled(algun_read)
        self.reveal_button.setEnabled(ninguno_offline)
        # Relink va siempre que haya seleccion: se puede querer reapuntar un
        # Read online a otro archivo con el mismo nombre, no solo arreglar uno
        # offline.
        self.relink_button.setEnabled(hay_seleccion)
        self.copy_button.setEnabled(todos_outside and hay_destinos)
        self.delete_button.setEnabled(ninguno_offline)

        self.refresh_toolbar_icons()

    def apply_table_stylesheet(self):
        """
        La hoja de la tabla, que depende del tamano de letra elegido.

        Sale a un metodo propio porque el tamano ahora se cambia desde los
        ajustes con la ventana abierta: si quedara escrita en el armado, la
        unica forma de aplicar un tamano nuevo seria reabrir la herramienta.
        """
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        self.table.setStyleSheet(
            "QTableWidget { background-color: %s; font-size: %dpx; }"
            # La seleccion se deja transparente a proposito: si la hoja define
            # un background para 'item:selected' le gana al setBackground() del
            # item y a la paleta del delegado, y la columna Status pierde su
            # color justo cuando esta seleccionada. De eso se encarga
            # TransparentTextDelegate, que sabe que celdas tienen color propio.
            "QTableWidget::item:selected { background-color: transparent; }"
            % (UI.Color.SURFACE, self.font_size)
        )

    def update_table_font_size(self, tamano):
        """
        Cambia la letra de la tabla y, con ella, el alto de fila.

        El alto se DERIVA del tamano y no es una constante: sin eso, subir la
        letra la corta contra el borde de la fila.
        """
        self.font_size = tamano
        self.apply_table_stylesheet()
        self.table.verticalHeader().setDefaultSectionSize(tamano + 22)
        # El alto de la cabecera tambien se deriva del tamano: fs + 25.
        if getattr(self, "header", None) is not None:
            self.header.set_font_size(tamano)
        # El path lo dibuja el delegado con su propia fuente -un punto mas
        # grande que el resto de la tabla-, asi que la hoja no lo alcanza.
        self.refresh_path_delegate()

    def populate_copy_menu(self):
        """
        Arma las acciones del menu Copy to desde self.copy_options.

        Se rehace entero cada vez y no solo al abrir la ventana: si no, un
        destino agregado en los ajustes no aparecia hasta reabrir el Media
        Manager, y uno borrado seguia en el menu copiando a una carpeta que
        el usuario acababa de sacar.
        """
        self.copy_menu.clear()
        for location in self.copy_options:
            # El nombre va limpio: el atajo dejo de estar embebido con un '&'
            # y sale de su propio campo. Un '&' que quedo en un nombre viejo
            # se escapa para que Qt lo dibuje y no se lo coma como mnemonico.
            action = QAction(location["name"].replace("&", "&&"), self)
            letra = (location.get("shortcut") or "").strip().upper()
            if letra:
                # Qt dibuja solo el atajo a la derecha del item.
                action.setShortcut(f"Alt+{letra}")
            action.triggered.connect(
                lambda checked=False, loc=location: self.copy_to(loc)
            )
            self.copy_menu.addAction(action)
        # Las acciones tambien se cuelgan de la ventana: el menu esta oculto
        # hasta que se lo abre, y un QAction que solo vive en un menu oculto no
        # siempre tiene el atajo activo. Colgarlas de un widget visible no
        # duplica el atajo -es del QAction, no del widget- pero garantiza que
        # Alt+letra copie sin abrir el menu.
        for action in getattr(self, "_copy_actions", []):
            self.removeAction(action)
        self._copy_actions = list(self.copy_menu.actions())
        for action in self._copy_actions:
            self.addAction(action)

    def show_copy_menu(self):
        """Abre el menu de Copy to pegado al boton, como pide el disenio."""
        if self.copy_menu.isEmpty():
            return
        self.copy_button.setDown(True)
        self.copy_menu.popup(
            self.copy_button.mapToGlobal(QPoint(0, self.copy_button.height() + 6))
        )

    def on_settings_saved(self):
        """Relee el .ini y refleja lo guardado sin tener que reabrir la tool."""
        self.load_settings()
        self.populate_copy_menu()
        # Sin destinos con Copy to el boton no tiene a donde copiar: si el
        # usuario los saco en los ajustes, se apaga sin reabrir la ventana.
        self.update_button_states()
        # El shot y las carpetas a escanear pueden haber cambiado: sin
        # recalcularlos, el coloreo de paths y los estados OK/Outside se
        # siguen midiendo contra la carpeta vieja hasta el proximo escaneo.
        self.apply_appearance(self.appearance)
        # El shot y las carpetas a escanear se recalculan adentro del worker
        # del escaneo, para no bloquear la ventana mientras se guarda.

    def apply_window_background(self):
        """
        El fondo de la ventana, del tema ELEGIDO.

        Va por paleta y no por hoja de estilo a proposito: una regla
        'QWidget { background-color }' se propaga a todos los hijos y les come
        la caja a los spinboxes y a los checkbox nativos. La paleta la heredan
        igual, pero cada control la usa para el rol que le corresponde.

        Sale a un metodo porque el color depende del tema y el tema se cambia
        con la ventana abierta: escrito una sola vez en el armado, y encima
        leyendo el Color del modulo -que es el del tema BASE y no el elegido-,
        la ventana quedaba con el gris del tema equivocado y no se repintaba
        nunca.
        """
        UI = getattr(self, "UI", None) or UIStyle.theme(None)
        self.setAutoFillBackground(True)
        paleta = self.palette()
        paleta.setColor(QPalette.Window, QColor(UI.Color.WINDOW))
        self.setPalette(paleta)

    def apply_appearance(self, appearance):
        """
        Aplica el tema y el tamano de letra sin reabrir la ventana.

        La ventana de ajustes lo llama tambien MIENTRAS esta abierta, para que
        el usuario vea el tema sobre la tabla de atras, y le manda el guardado
        de vuelta si cancela.
        """
        self.appearance = dict(appearance or {})
        self.UI = UIStyle.theme(self.appearance.get("theme"))
        self.apply_window_background()
        # La barra tambien sale del tema: sin esto los botones se quedaban con
        # los colores del tema anterior hasta reabrir la ventana.
        if getattr(self, "toolbar_buttons", None):
            self.apply_toolbar_stylesheet()
        # Las pastillas, el pie y los fondos de la columna Status salen todos
        # del tema: sin repintarlos, el cambio de tema deja media ventana con
        # los colores viejos.
        if getattr(self, "status_pills", None):
            self.apply_status_bar_stylesheet()
        if getattr(self, "legend_entries", None):
            self.apply_footer_stylesheet()
        self.repaint_status_column()
        # El '#' se repinta SIN renumerar: para cuando se cambia el tema la
        # tabla ya no esta en el orden en que se cargo.
        self.repaint_row_numbers()
        tamano = self.appearance.get(
            "table_font_size", UIStyle.Metric.TABLE_FONT_SIZE
        )
        self.table_font_size = max(
            UIStyle.Metric.TABLE_FONT_SIZE_MIN,
            min(UIStyle.Metric.TABLE_FONT_SIZE_MAX, int(tamano)),
        )
        self.update_table_font_size(self.table_font_size)

    def nk_dir(self):
        """La carpeta del .nk abierto, contra la que se resuelve todo."""
        project_path = nuke.root().name()
        return os.path.dirname(project_path) if project_path else ""

    def load_settings(self):
        """
        Toda la configuracion, leida por el modulo que la normaliza.

        La lectura, la migracion del formato viejo y los defaults viven en
        LGA_MediaManager_config: aca solo se traduce a lo que usa la ventana.
        """
        self.settings = mm_config.load_settings(theme_ids=UIStyle.theme_ids())
        self.shot = dict(self.settings.get("shot") or mm_config.DEFAULT_SHOT)
        self.locations = list(self.settings.get("locations") or ())
        self.appearance = dict(
            self.settings.get("appearance") or mm_config.DEFAULT_APPEARANCE
        )
        # El menu Copy to ya no es una lista aparte: son las locations que
        # tienen la casilla prendida, en el orden de la tabla.
        self.copy_options = mm_config.copy_destinations(self.locations)
        debug_print(
            "Config leida: %d locations, %d en Copy to, shot=%s"
            % (len(self.locations), len(self.copy_options), self.shot.get("path"))
        )

    def resolve_shot_folder(self):
        """
        La carpeta del shot, que es el limite de lo que esta adentro.

        Reemplaza al viejo project_folder_depth: en vez de subir N niveles
        desde el .nk, se resuelve la ruta explicita que el usuario configuro.
        Con el shot apagado no hay adentro ni afuera y queda en "": el estado
        Outside pasa a medirse contra las scan locations.
        """
        base = self.nk_dir()
        if not base or not self.shot.get("enabled", True):
            self.project_folder = "" if not base else base
            return self.project_folder
        resultado = mm_paths.resolve(self.shot.get("path") or "", base)
        # Con un comodin que abre varias, la primera: el shot es uno solo, y
        # una ruta de shot con comodin ya no es una ruta de shot.
        self.project_folder = resultado.folders[0] if resultado.folders else base
        return self.project_folder

    def resolve_scan_folders(self):
        """
        Las carpetas reales a escanear, sin repetidas ni anidadas.

        Deduplicar no es un lujo: dos locations pueden resolver a la misma
        carpeta, y una que contiene a otra haria que las hijas se escaneen dos
        veces. El escaneo es recursivo, asi que con la de mas arriba alcanza.
        """
        base = self.nk_dir()
        carpetas = []

        # La carpeta del shot NO se escanea por ser el shot: es el limite de
        # lo que esta adentro, no una carpeta donde buscar. De donde se busca
        # lo dice la tabla de locations, y si el usuario quiere el shot entero
        # se agrega como location. Sumandolo aca, el dedup por anidamiento se
        # comia todas las demas y siempre se escaneaba el shot completo.
        explicitas = [l for l in self.locations if l.get("path")]
        candidatas = [{"path": l.get("path", ""), "scan": bool(l.get("scan"))}
                      for l in explicitas]
        for i, location in enumerate(explicitas):
            # El scan EFECTIVO: la propia casilla, o que otra location con
            # scan la incluya.
            efectivo = bool(location.get("scan")) or (
                mm_paths.scanning_parent(candidatas, i, base) is not None
            )
            if efectivo:
                carpetas.extend(mm_paths.resolve(location["path"], base).folders)

        # Se saca la que ya vive adentro de otra de la lista.
        unicas = []
        vistas = set()
        for carpeta in carpetas:
            clave = os.path.normcase(os.path.normpath(carpeta))
            if clave in vistas:
                continue
            vistas.add(clave)
            unicas.append(carpeta)

        self.scan_folders = [
            c for c in unicas
            if not any(o is not c and _is_inside(c, o) for o in unicas)
        ]
        debug_print("Carpetas a escanear: %s" % self.scan_folders)
        return self.scan_folders

    def show_settings_window(self):
        self.settings_window = SettingsWindow(self.settings, self.nk_dir(), self)
        self.settings_window.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.settings_window.size(),
                QApplication.primaryScreen().availableGeometry(),
            )
        )
        # Al guardar hay que releer el .ini: si no, los destinos nuevos no
        # aparecen en el menu Copy to hasta reabrir el Media Manager, y la
        # profundidad de la ventana y la de la tabla quedan distintas.
        self.settings_window.settings_saved.connect(self.on_settings_saved)
        # El tema y el tamano de letra se ven MIENTRAS se eligen, sobre esta
        # tabla. Si el usuario cancela, la ventana manda los guardados de
        # vuelta por la misma senal y todo queda como estaba.
        self.settings_window.appearance_previewed.connect(self.apply_appearance)
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
        # Y despues los anchos del disenio, que no salen del contenido:
        # `52 | 1fr (min 300) | 96 | 118`. Van DESPUES del ajuste al contenido
        # porque ese los pisaria.
        self.apply_column_widths()

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

        # Agregar el alto de TODO lo que no es la tabla: la barra de botones,
        # la fila de pastillas y el pie. Sumar solo el primero dejaba la
        # ventana corta justo por el alto de las dos filas nuevas.
        top_layout_height = 0
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.widget() is self.table:
                continue
            top_layout_height += item.sizeHint().height()
        height += top_layout_height
        self.logger.debug(f"[Altura] Alto de las filas fuera de la tabla: {top_layout_height}")

        layout_margins = self.layout.contentsMargins()
        margins_height = layout_margins.top() + layout_margins.bottom()
        # Un espacio por cada junta entre items del layout, no uno solo.
        spacing_total = self.layout.spacing() * max(0, self.layout.count() - 1)
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
        # La que se estira es File Path y NO la ultima. Con la ultima, el
        # bloque de color de Status crecia hasta el borde de la ventana y el
        # path -que es lo largo y lo que se lee- quedaba cortado con el resto
        # vacio al lado. El diseno fija 52 | 1fr | 96 | 118.
        encabezado = self.table.horizontalHeader()
        encabezado.setStretchLastSection(False)
        encabezado.setSectionResizeMode(COL_PATH, QHeaderView.Stretch)
        for columna in (COL_NUM, COL_READ, COL_STATUS):
            encabezado.setSectionResizeMode(columna, QHeaderView.Fixed)

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

    def apply_column_widths(self):
        """
        Los anchos fijos del disenio. El path no lleva: es el que se estira.

        El minimo del path no es un lujo: sin el, con paths cortos la columna
        se achica hasta que el resto de la ventana no tiene de donde agarrarse.
        """
        if getattr(self, "table", None) is None:
            return
        self.table.setColumnWidth(COL_NUM, COL_NUM_WIDTH)
        self.table.setColumnWidth(COL_READ, COL_READ_WIDTH)
        self.table.setColumnWidth(COL_STATUS, COL_STATUS_WIDTH)
        if self.table.columnWidth(COL_PATH) < COL_PATH_MIN_WIDTH:
            self.table.setColumnWidth(COL_PATH, COL_PATH_MIN_WIDTH)

    def toggle_columns(self, state):

        is_visible = bool(state)
        self.table.setColumnHidden(COL_FOLDER_DELETE, not is_visible)
        self.table.setColumnHidden(COL_SEQUENCE, not is_visible)
        self.adjust_window_size()

    def reorder_by_status(self):
        self.table.sortByColumn(COL_STATUS, Qt.AscendingOrder)

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
        """
        Selecciona en el Node Graph los Reads de TODO lo seleccionado.

        Con una sola fila se cicla entre sus Reads, que es el comportamiento de
        siempre: una media puede estar usada por varios nodos y apretar de
        nuevo lleva al siguiente. Con varias filas no hay ciclo posible -no
        habria a que "siguiente" ir- asi que se seleccionan todos juntos.
        """
        filas = self.selected_rows()
        if not filas:
            return

        if len(filas) == 1:
            self._go_to_read_cycle(self.row_read_names(filas[0]))
            return

        # Varias filas: se juntan todos los Reads, sin repetir y respetando el
        # orden de la tabla.
        nombres = []
        for fila in filas:
            for nombre in self.row_read_names(fila):
                if nombre not in nombres:
                    nombres.append(nombre)

        nodos = [nuke.toNode(nombre) for nombre in nombres]
        nodos = [nodo for nodo in nodos if nodo]
        if not nodos:
            debug_print("Ninguna de las filas seleccionadas tiene un Read vivo")
            return

        nuke.selectAll()
        nuke.invertSelection()
        for nodo in nodos:
            nodo.setSelected(True)
        nuke.zoomToFitSelected()
        # Sin showControlPanel: con veinte filas seleccionadas serian veinte
        # paneles de propiedades abiertos de golpe.

    def _go_to_read_cycle(self, read_node_names):
        """Ciclado entre los Reads de una sola fila."""
        if not read_node_names:
            return

        # Obtener los nodos Read y CopyCat actualmente seleccionados en Nuke
        selected_reads = [
            node.name()
            for node in nuke.selectedNodes()
            if node.Class() in ["Read", "CopyCat", "AudioRead", "ReadGeo", "DeepRead"]
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

    # Cuantas carpetas se abren sin preguntar. Mas que esto y el explorador
    # tapa la pantalla con ventanas que el usuario no pidio de a una.
    REVEAL_MAX_FOLDERS = 5

    def reveal_selected(self):
        """Abre en el explorador la carpeta de cada fila seleccionada."""
        filas = self.selected_rows()
        if not filas:
            return

        # Se abre una ventana por CARPETA y no por fila: seleccionar una
        # secuencia entera de la misma carpeta abria la misma ventana N veces.
        carpetas = []
        for fila in filas:
            ruta = self.row_path(fila)
            if not ruta:
                continue
            carpeta = os.path.dirname(ruta)
            if carpeta and carpeta not in carpetas:
                carpetas.append(carpeta)

        if not carpetas:
            return

        if len(carpetas) > self.REVEAL_MAX_FOLDERS:
            respuesta = QMessageBox.question(
                self,
                "Reveal",
                "This will open %d explorer windows. Continue?" % len(carpetas),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if respuesta != QMessageBox.Yes:
                return

        for carpeta in carpetas:
            self.open_folder(carpeta)

    def reveal_in_explorer(self, file_path):
        """Abre la carpeta que contiene un archivo."""
        self.open_folder(os.path.dirname(file_path))

    def open_folder(self, directory):
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
        """
        Reapunta los Reads de TODAS las filas seleccionadas.

        Ya no exige que el archivo este Offline: se puede querer reapuntar un
        Read online a otro archivo con el mismo nombre -otra version del mismo
        plano, por ejemplo-, y el boton habilitado que solo sabia decir que no
        era peor que no tenerlo.

        La carpeta se elige UNA vez y despues se busca archivo por archivo. Las
        busquedas van encadenadas y no en paralelo porque cada una es un
        os.walk sobre la misma carpeta: lanzarlas juntas multiplica el trabajo
        del disco por la cantidad de filas.
        """
        filas = self.selected_rows()
        if not filas:
            return

        # Una tanda por vez, igual que una busqueda por vez.
        if self.relink_worker is not None or self.relink_queue:
            debug_print("Ya hay un relink en curso")
            return

        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not directory:
            return

        self.relink_directory = directory
        self.relink_queue = [self.row_path(fila) for fila in filas]
        self.relink_queue = [ruta for ruta in self.relink_queue if ruta]
        self.relink_missing = []
        self._relink_next()

    def _relink_next(self):
        """Arranca la busqueda del proximo archivo de la tanda, si queda alguno."""
        if self.relink_queue:
            ruta = self.relink_queue.pop(0)
            try:
                self.search_file_in_directory(self.relink_directory, ruta)
            except Exception as problema:
                # Si armar la busqueda falla, la tanda se corta pero no se
                # queda colgada: con la cola llena, Relink no se podia volver
                # a apretar nunca.
                debug_print("No se pudo buscar %s: %s" % (ruta, problema))
                self.relink_queue = []
                self.relink_missing = []
            return

        # Terminada la tanda se avisa UNA vez de lo que no aparecio, en vez de
        # un cartel por archivo que habria que cerrar de a uno.
        if self.relink_missing:
            faltantes = self.relink_missing
            self.relink_missing = []
            if len(faltantes) == 1:
                QMessageBox.information(self, "Information", "File not found.")
            else:
                QMessageBox.information(
                    self,
                    "Information",
                    "%d files were not found:\n\n%s"
                    % (len(faltantes), "\n".join(faltantes[:12])),
                )

    def build_search_patterns(self, file_name):
        """
        Arma los dos criterios de busqueda para el relink a partir del texto de la tabla.

        Devuelve (exact_name, sequence_pattern):
          - exact_name: nombre exacto del primer frame, con el padding correcto,
            o None si el frame no se puede reconstruir.
          - sequence_pattern: regex que acepta cualquier frame de la misma
            secuencia, o None si el archivo no es una secuencia.
        """
        # El rango se corta anclado al final y no con split("["): un archivo que
        # tenga un '[' en el nombre -take[1]_####.exr- se partia por el corchete
        # equivocado y el nombre quedaba sin sentido.
        texto = os.path.basename(file_name)
        base_name = re.sub(r"\[-?\d+--?\d+\]\s*$", "", texto).strip()

        grupos = list(re.finditer(r"#+", base_name))

        if not grupos:
            # Archivo unico: el nombre ya viene completo
            return base_name.lower(), None

        # El grupo del frame es el ULTIMO. Con el primero, un nombre como
        # sh010_comp_v###_####.exr resolvia el frame sobre la version y la
        # secuencia no se podia relinkear nunca.
        hashes_match = grupos[-1]
        hashes = hashes_match.group(0)
        prefix = base_name[: hashes_match.start()]
        suffix = base_name[hashes_match.end() :]

        # Criterio primario: reconstruir el nombre exacto del primer frame.
        # El rango de un Read offline viene sin padding (ej. [0-530]), asi que hay
        # que rellenarlo al ancho de los '#' para que coincida con el archivo real.
        # Solo se puede armar si el frame es el unico grupo de '#': con mas de uno
        # no sabemos que numero va en los otros, y ahi trabaja el patron.
        exact_name = None
        frame_range = re.search(r"\[(-?\d+)--?\d+\]\s*$", texto)
        if frame_range and len(grupos) == 1 and not frame_range.group(1).startswith("-"):
            first_frame = frame_range.group(1)
            exact_name = (prefix + first_frame.zfill(len(hashes)) + suffix).lower()

        # Criterio de respaldo: mismo nombre y mismo padding, cualquier numero de frame.
        # Cubre el caso en que el frame inicial guardado en el nodo no existe en la
        # carpeta nueva (secuencia recopiada con otro rango, primer frame faltante, etc).
        # Cualquier otro grupo de '#' del nombre tambien es un numero en disco,
        # asi que en el patron van todos como digitos: escapar el prefijo tal
        # cual dejaba los '###' de una version como literales, que no matchean
        # nada. El del frame acepta signo, para las secuencias que arrancan en
        # negativo.
        def a_digitos(texto_fijo):
            partes = re.split(r"(#+)", texto_fijo)
            return "".join(
                r"\d{%d}" % len(parte) if parte.startswith("#") else re.escape(parte)
                for parte in partes
            )

        # El grupo del frame acepta ademas un numero negativo. El signo ocupa
        # lugar dentro del padding -"%04d" % -5 da "-005"-, asi que con signo
        # va un digito menos.
        ancho = len(hashes)
        numero = r"(?:-\d{%d}|\d{%d})" % (ancho - 1, ancho) if ancho > 1 else r"-?\d"

        sequence_pattern = re.compile(
            a_digitos(prefix) + numero + a_digitos(suffix) + r"$",
            re.IGNORECASE,
        )

        return exact_name, sequence_pattern

    def search_file_in_directory(self, directory, file_name):
        # Una busqueda por vez: la UI quedo responsiva al pasar el walk a un
        # worker, asi que nada impedia apretar Relink de nuevo y quedarse con
        # dos busquedas pisandose los resultados.
        if self.relink_worker is not None:
            return

        # Los patrones se arman ANTES de mostrar la ventanita: es frameless y
        # siempre encima, asi que si algo falla armandolos queda pegada sin
        # forma de cerrarla.
        exact_name, sequence_pattern = self.build_search_patterns(file_name)

        # Ventana propia y no self.loading_window, que la comparten la copia y
        # el borrado: con la busqueda corriendo en paralelo, el que terminaba
        # primero cerraba la ventanita del otro.
        self.relink_loading_window = LoadingWindow("Searching...", self)
        self.relink_loading_window.show()
        QApplication.processEvents()
        self.logger.debug(
            f"\nBuscando el archivo: {exact_name} en {directory}"
            f" (patron de respaldo: {sequence_pattern.pattern if sequence_pattern else 'ninguno'})"
        )

        # El recorrido va a un worker: sobre un servidor grande el os.walk
        # tarda lo suficiente como para congelar Nuke entero, y encima el
        # patron de respaldo obliga a recorrer todo el arbol cuando no hay
        # match exacto, que es el caso normal de una secuencia movida.
        self.relink_worker = RelinkSearchWorker(directory, exact_name, sequence_pattern)
        self.relink_worker.signals.finished.connect(
            lambda encontrado: self.on_relink_search_finished(file_name, encontrado)
        )
        QThreadPool.globalInstance().start(self.relink_worker)

    def on_relink_search_finished(self, file_name, found_path):
        """Aplica el resultado de la busqueda. Corre en el hilo principal."""
        self.relink_worker = None

        # El walk puede tardar minutos: si el usuario cerro la ventana mientras
        # tanto, los widgets ya no existen del lado de C++ aunque Python siga
        # teniendo la referencia viva por el lambda de la conexion.
        try:
            if self.relink_loading_window is not None:
                self.relink_loading_window.close()
                self.relink_loading_window = None

            if found_path:
                self.update_read_node(file_name, found_path)
            else:
                # El aviso no sale aca sino al final de la tanda: con varias
                # filas seleccionadas serian N carteles seguidos.
                self.relink_missing.append(os.path.basename(file_name))
        except RuntimeError:
            # La ventana del Media Manager se cerro durante la busqueda
            self.logger.debug(
                "La ventana se cerro antes de que terminara la busqueda del relink"
            )
            self.relink_queue = []
            self.relink_missing = []
            return

        self._relink_next()

    def update_read_node(self, original_file_name, new_file_path):
        # Normalizar las barras en la ruta del archivo
        new_file_path = new_file_path.replace("\\", "/")

        # Buscar el nodo Read asociado al archivo original en la tabla y actualizar
        for row in range(self.table.rowCount()):
            table_file_name = self.table.item(row, COL_PATH).text()
            if (
                table_file_name == original_file_name
                or table_file_name in original_file_name
            ):
                node_name = self.table.item(row, COL_READ).text()
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
                    self.table.item(row, COL_PATH).setText(new_table_path)
                    # El path lo repinta el delegado a partir del dato de la
                    # fila: no hay label que actualizar.

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

                    # El estado, su color y su clave de orden salen del mismo
                    # lugar que en el escaneo.
                    if common_path.replace("\\", "/") == normi_project_folder:
                        self.set_row_status(row, "Online")
                    else:
                        self.set_row_status(row, "Outside")
                    self.update_status_counts()

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

        # La carpeta del shot y las carpetas a escanear las resuelve el
        # WORKER, no esta funcion: resolver un comodin es un os.scandir por
        # nivel y por rama, y contra un servidor eso cuelga Nuke entero.

        # Un escaneo por vez: dos workers escribiendo sobre la misma tabla se
        # pisan las filas.
        self._scan_running = True
        if getattr(self, "rescan_button", None) is not None:
            self.rescan_button.setEnabled(False)
            self.apply_footer_stylesheet()

        # Mientras se puebla la tabla el orden va apagado: con el orden activo,
        # el setItem de la columna 0 mueve la fila en el acto y todo lo que se
        # escribe despues para esa fila cae en otra.
        self.table.setSortingEnabled(False)

        # El escaneo real se realizará en el worker
        scanner_worker = ScannerWorker(self)  # Solo pasamos la instancia de FileScanner

        # Conectar señales
        scanner_worker.signals.files_found.connect(self.on_files_found)
        scanner_worker.signals.finished.connect(self.on_scan_finished)

        # Iniciar el escaneo en segundo plano
        QThreadPool.globalInstance().start(scanner_worker)

    def on_scan_finished(self):
        """
        Cierre del escaneo: orden, medidas, contadores y filtro.

        Cada paso va en su propia linea y no en una lista adentro de un
        lambda: ahi, una excepcion en el primero se llevaba puestos a todos
        los demas sin dejar rastro.
        """
        self._scan_running = False

        # Los ids se asignan con el orden TODAVIA apagado, o sea con la tabla
        # en el orden en que se cargo: son un id estable y no la posicion.
        self.assign_row_ids()

        self.table.setSortingEnabled(True)
        # Lo primero que se busca al abrir es que se rompio, asi que la tabla
        # arranca ordenada por estado y no por path.
        self.reorder_by_status()

        try:
            self.table.resizeColumnsToContents()
            self.adjust_window_size()
        except Exception as problema:
            debug_print("No se pudo reajustar la ventana al terminar: %s" % problema)

        self.refresh_path_delegate()
        self.update_status_counts()
        # El filtro se vuelve a aplicar sobre las filas nuevas: si no, un
        # Rescan con un filtro puesto mostraba todo.
        self.apply_filters()
        # Con nada seleccionado la barra queda entera apagada y la ventana se
        # abre pareciendo rota.
        self.select_first_visible_row()

        if getattr(self, "rescan_button", None) is not None:
            self.rescan_button.setEnabled(True)
            self.apply_footer_stylesheet()

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
            self.table.setItem(row_position, COL_PATH, casi_file_item)
            # No hay QLabel por celda: el path lo dibuja PathDelegate a partir
            # de este mismo item, asi que no puede quedar colgado de otra fila.

            # Si la rama rara del final no asigna estado, la fila queda
            # marcada como rota y no hereda el estado de la vuelta anterior.
            state = "Offline"

            if not is_unmatched_read:
                # Manejo de los archivos del find_files
                status = "-"
                state = "Unused"
                # Usar la funcion de normalizacion centralizada
                normalized_read_files = {
                    normalize_path_for_comparison(path): nodes
                    for path, nodes in read_files.items()
                }

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
                            state = "Online"
                            self.matched_reads.extend(nodes)
                            break
                else:
                    for read_path, nodes in normalized_read_files.items():
                        if normalized_file_path_for_comparison == read_path:
                            status = ", ".join(nodes)
                            state = "Online"
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
                            state = "Online"
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
                self.table.setItem(row_position, COL_READ, read_item)

                # El estado NO se escribe aca: lo pone set_row_status al final
                # de la vuelta, que crea la celda como SortKeyItem. Puesta a
                # mano quedaba un QTableWidgetItem comun, o sea que esas filas
                # se ordenaban por el TEXTO del estado y no por el rango
                # Offline < Unused < Outside < Online.

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
                        self.table.setItem(row_position, COL_READ, read_item)
                        state = "Offline"
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
                            self.table.setItem(row_position, COL_READ, read_item)
                            state = "Online"
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
                            self.table.setItem(row_position, COL_READ, read_item)
                            state = "Outside"

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
            self.table.setItem(row_position, COL_FOLDER_DELETE, folder_delete_item)
            # Insertar el estado de la secuencia
            sequence_item = QTableWidgetItem(str(sequence_state))
            sequence_item.setTextAlignment(Qt.AlignCenter)
            sequence_item.setFlags(sequence_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, COL_SEQUENCE, sequence_item)

            # La columna Read se rehace como SortKeyItem para que se ordene
            # numerico -Read2 antes que Read12- y las filas sin Read caigan al
            # final. Por texto, Read12 iba antes que Read2.
            read_existente = self.table.item(row_position, COL_READ)
            texto_read = read_existente.text() if read_existente is not None else "-"
            read_item = SortKeyItem(texto_read)
            read_item.setTextAlignment(Qt.AlignCenter)
            read_item.setData(Qt.UserRole, read_sort_key(texto_read))
            read_item.setFlags(read_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, COL_READ, read_item)

            # El estado, su color de fondo y su clave de orden, todos del
            # mismo lugar: los hexes de estado ya no se escriben a mano.
            self.set_row_status(row_position, state)

        self.remove_duplicates()
        # El '#' se numera aca y no al final del escaneo para que las filas ya
        # cargadas no se vean con la celda vacia mientras el resto llega. Se
        # renumera despues de cada tanda porque remove_duplicates puede haber
        # sacado filas del medio.
        self.assign_row_ids()

        end_time = time.time()
        # print("add_file_to_table execution time end: ", end_time - start_time, "seconds")

    def remove_duplicates(self):
        paths = {}  # Diccionario para almacenar los paths y sus indices de fila
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_PATH)
            if item is not None:
                # Usar la funcion de normalizacion centralizada
                file_path = normalize_path_for_comparison(
                    self.table.item(row, COL_PATH).text()
                )
                status = self.table.item(row, COL_STATUS).text()
                if file_path in paths and status != "Online":
                    # Si el path esta duplicado y el estado actual no es Online, eliminar la fila
                    self.table.removeRow(row)
                elif (
                    file_path in paths
                    and self.table.item(paths[file_path], COL_STATUS).text() != "Online"
                ):
                    # Si el path esta duplicado y el estado del path previamente almacenado no es Online, eliminar la fila previa
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

            # Path, estado y Read de la fila seleccionada.
            file_path = self.table.item(row, COL_PATH).text()
            status = self.table.item(row, COL_STATUS).text()
            read_node_name = self.table.item(row, COL_READ).text()

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
                files_to_delete[0][1], COL_SEQUENCE
            ).text()

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
            file_path_text = self.table.item(row, COL_PATH).text()  # Columna "File Path"
            sequence_status = self.table.item(row, COL_SEQUENCE).text()  # Columna "Sequence"

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
            table_file_path = self.table.item(row, COL_PATH).text().replace("\\", "/").lower()

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
    def copy_to(self, location):
        """
        Copia a la location elegida TODAS las filas seleccionadas.

        Las copias van encadenadas y no en paralelo: cada una puede abrir su
        propio cartel de confirmacion por sobreescritura, y varias a la vez
        serian varios carteles pisandose sobre la misma carpeta destino.
        """
        filas = self.selected_rows()
        if not filas:
            return

        # Guard de siempre, ahora sobre TODAS las filas: Copy to es traerse
        # adentro del shot algo que esta afuera, y copiar de nuevo algo que ya
        # esta adentro no significa nada.
        if any(self.row_status(fila) != "Outside" for fila in filas):
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                "The copy operation is limited to 'Outside' files",
            )
            return

        if self.copy_queue:
            debug_print("Ya hay una tanda de copias en curso")
            return

        # El destino sale de la ruta de la location, resuelta contra
        # disco. Un comodin puede abrir cero o varias carpetas, y en los
        # dos casos elegir por el usuario seria adivinar: con cero no hay
        # que crear nada -"../*assets*" no es un nombre de carpeta- y con
        # varias no hay forma de saber cual queria. La ventana de ajustes
        # ya avisa antes de guardar; esto es la red de atras.
        resultado = mm_paths.resolve(location.get("path", ""), self.nk_dir())
        if len(resultado.folders) > 1:
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                "\"%s\" matches %d folders, so there is no single "
                "destination:\n\n%s"
                % (location.get("name", ""), len(resultado.folders),
                   "\n".join(resultado.folders[:8])),
            )
            return
        if not resultado.folders:
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                "\"%s\" does not match any existing folder."
                % (location.get("name") or location.get("path", "")),
            )
            return

        self.copy_dest_folder = resultado.folders[0]
        self.copy_queue = [
            (self.row_path(fila), self.row_read(fila))
            for fila in filas
            if self.row_path(fila)
        ]
        self._copy_next()

    def _copy_next(self):
        """Arranca la copia del proximo archivo de la tanda, si queda alguno."""
        if not self.copy_queue:
            return

        source_file_path, read_node_name = self.copy_queue.pop(0)

        # Verificar si el footage pertenece a algun Read
        if read_node_name and read_node_name != "-":
            # Con varios Reads sobre la misma media se reapunta el primero:
            # los demas siguen apuntando al original hasta que el usuario los
            # relinkee. Es lo que hacia antes y no cambia aca.
            self.current_read_node_name = read_node_name.split(",")[0].strip()
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

        self.loading_window = CopyStepWindow("Copying...", self, self._copy_next)
        self.center_window(self.loading_window)
        self.loading_window.show()

        # El hilo anterior se guarda un paso mas: si se lo suelta apenas
        # termina de emitir, Python puede destruir el QThread mientras su
        # run() todavia esta saliendo.
        self.previous_copy_thread = getattr(self, "copy_thread", None)

        self.copy_thread = CopyThread(source_file_path, self.copy_dest_folder)
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
            # Actualizar la ruta en el QTableWidgetItem
            table_path = self.table.item(row, COL_PATH).text()
            if table_path.startswith(original_file_path[: -len(filename)]):
                # Actualizar la ruta manteniendo los '#' y el rango de cuadros
                new_table_path = (
                    new_file_path_table + table_path[len(original_file_path) :]
                )
                self.table.item(row, COL_PATH).setText(new_table_path)
                # El path lo repinta el delegado a partir del item.

                # El archivo se trajo adentro del shot: deja de estar Outside.
                status_item = self.table.item(row, COL_STATUS)
                if status_item is not None and status_item.text() == "Outside":
                    self.set_row_status(row, "Online")
                    self.update_status_counts()

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
            if self.table.item(row, COL_PATH).text() == original_file_path:
                # Actualizar la ruta en el QTableWidgetItem
                self.table.item(row, COL_PATH).setText(new_file_path)
                # El path lo repinta el delegado a partir del item.

                # El archivo se trajo adentro del shot: deja de estar Outside.
                status_item = self.table.item(row, COL_STATUS)
                if status_item is not None and status_item.text() == "Outside":
                    self.set_row_status(row, "Online")
                    self.update_status_counts()

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
