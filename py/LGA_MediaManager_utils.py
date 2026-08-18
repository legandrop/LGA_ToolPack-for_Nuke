"""
_______________________________________________________________________

  LGA_MediaManager_utils v2.41 | Lega

  Worker de escaneo, copia de archivos y widgets compartidos del
  Media Manager.

  v2.41: El progreso de las tandas deja de avisar por archivo. Con
         una secuencia de tres mil frames eran seis mil eventos en la
         cola del hilo principal y tres mil repintados del cartel: la
         ventana que muestra que la herramienta avanza era la que la
         frenaba. Ahora avisa unas doscientas veces en total, y el
         ultimo aviso sale siempre.
  v2.40: Once defectos de concurrencia que salieron de auditar lo de
         v2.39. El peor: se arrancaban DOS ScannerWorker en cada
         apertura -uno en __init__ que nadie conectaba y otro en
         scan_project- asi que el disco se recorria dos veces, el
         resultado de uno se tiraba, y la X de la ventana de escaneo
         cancelaba justo el inutil: el que llenaba la tabla seguia
         corriendo despues de abortar.
         El escaneo tocaba la API de Nuke desde el hilo del pool.
         get_read_files envolvia el allNodes pero despues leia los
         knobs de los nodos devueltos afuera, con lo cual el wrapper
         no servia de nada. Ahora se saca una FOTO en el hilo
         principal y al worker le llegan datos, no nodos.
         expand_sequence fallaba en cuatro formas de path que la
         propia herramienta genera: nombres con version -v###_####,
         donde reemplazaba los dos grupos de #-, corchetes en el
         nombre, rangos negativos y rutas sin rango. Las filas se
         salteaban en silencio y el total del cartel no las contaba.
         Copy to podia mandar dos archivos distintos al MISMO destino
         -dos versiones del mismo plano se llaman igual- y el segundo
         pisaba al primero informando los dos como copiados.
         Sumado: closeEvent que corta todo lo que este corriendo,
         setAutoDelete(False) en los cuatro workers, las filas a
         borrar se buscan por ruta y no por indice, Rescan bloqueado
         durante una tanda, cancelar un relink deja de decir "File
         not found", la bandera de cancelacion del escaneo se mira en
         todos los bucles largos y no en dos, y se van el
         processEvents y el sleep que el worker hacia sobre un hilo
         sin bucle de eventos.
  v2.39: CopyThread y DeleteThread se van y entran CopyWorker y
         DeleteWorker sobre una base comun, BatchWorker: reciben un
         plan ya decidido y solo tocan disco. No leen widgets, no
         abren carteles y no llaman a la API de Nuke.
         El borrado va SIEMPRE a la papelera, con separadores
         nativos: la version vieja los forzaba a '\\' siempre, asi
         que en macOS y Linux le pasaba a send2trash rutas que no
         existen.
         ProgressWindow queda como la ventana de progreso de las
         cuatro operaciones -escaneo, busqueda del relink, copia y
         borrado- con su X que aborta. StartupWindow ya solo agrega
         el progreso que avanza solo, y LoadingWindow se va porque no
         la usaba nadie mas.
         expand_sequence() convierte una fila de la tabla en sus
         archivos reales. Vive aca porque la usan los dos workers y
         tambien el hilo principal, que necesita CONTAR los archivos
         antes de preguntar nada.
  v2.38: StartupWindow pasa al tema y suma la X que aborta. Es la
         primera ventana que se ve, y si no se parece a las dos que
         vienen despues la herramienta arranca pareciendo otra cosa:
         iba con tres hexes sueltos, en negrita y con la barra de
         progreso gris. Ahora todo el color sale del tema que el
         usuario tiene guardado -se lo lee del .ini, porque la
         ventana se abre antes que la principal y no hay a quien
         preguntarle-, va con la fuente del pack y con las esquinas
         redondeadas.
         ScannerWorker sabe cancelarse: es una bandera que se mira en
         los bucles largos, no un kill. Matar el hilo dejaria la
         tabla a medio llenar, y lo que se junto hasta ahi no se
         emite: una tabla incompleta se lee igual que una completa.
  v2.34: PathDelegate dibuja con un desplazamiento propio
         (set_offset): es el scroll horizontal de esa columna sola.
         El recorte pasa a hacerse ANTES de mover el origen y en
         coordenadas de la celda; puesto despues se corria junto con
         el texto y el path se salia de su columna al scrollear.
  v2.31: paint_row_separator, la linea entre filas que ahora
         dibuja cada delegado. Y ReadCellDelegate pinta el fondo de
         la seleccion el mismo: la hoja de la tabla declara
         `item:selected` transparente a proposito -si no le ganaria
         al color propio de Status- asi que delegarlo dejaba esa
         celda con el gris normal y la fila elegida aparecia
         iluminada salvo un bloque oscuro justo en Read.
  v2.29: tinted_icon() arma el pixmap a la escala de la PANTALLA. Lo
         escalaba a pixeles de dispositivo 1x y Qt lo agrandaba al
         doble en un monitor Retina: por eso el engranaje, la lupa,
         el refresh y las flechitas de ordenar salian borrosos.
         Suma ReadCellDelegate: la columna Read va alineada a la
         izquierda, en el gris de cuerpo y con una raya en las filas
         sin Read. La sustitucion de la raya se hace al DIBUJAR para
         no tocar el centinela "-" del modelo, que es lo que ocho
         comparaciones de la tool usan para saber si hay Read.
         El numero de la fila seleccionada deja de encenderse en
         blanco: la columna '#' es un id, no contenido, y el
         delegado ahora respeta el color que le puso el item.
         Los indices de columna se mudan aca, que es donde los
         necesitan los delegados; estaban escritos en los dos lados.
  v2.27: tinted_icon() para los SVG de trazo, que QIcon dibujaria
         negros, y PathResolveWorker, que resuelve las rutas de la
         ventana de ajustes fuera del hilo principal. El escaneo
         recorre varias carpetas y no una sola.
  v2.25: RelinkSearchWorker, para que el os.walk del relink no
         corra en el hilo principal.

  v2.13: TransparentTextDelegate deja que el color propio de una celda
         -el estado del archivo- sobreviva a la seleccion de la fila:
         se aclara en vez de taparse. Los grises salen de
         LGA_UI_Style_ToolPack en vez de estar escritos al pie.
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
QPixmap = QtGui.QPixmap
QFont = QtGui.QFont
QTextDocument = QtGui.QTextDocument
QTextOption = QtGui.QTextOption
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QStyleOptionViewItem = QtWidgets.QStyleOptionViewItem
QByteArray = QtCore.QByteArray
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

from LGA_MediaManager_logging import configure_logger, debug_print, get_log_prefix
from LGA_UI_Style_ToolPack import Color, PATH_PALETTE
import LGA_UI_Style_ToolPack as UIStyle


def resolve_relative_path(file_path, project_folder):
    """
    Resuelve una ruta relativa a una ruta absoluta usando el directorio del proyecto como base.

    Args:
        file_path: Ruta que puede ser relativa o absoluta
        project_folder: Directorio base del proyecto para resolver rutas relativas

    Returns:
        Ruta absoluta resuelta
    """
    if not file_path:
        return ""

    # Si ya es una ruta absoluta (empieza con unidad de disco o /), devolverla tal como está
    if os.path.isabs(file_path):
        return file_path

    # Para rutas relativas, resolverlas usando el directorio del proyecto
    resolved_path = os.path.join(project_folder, file_path)
    # Normalizar la ruta para manejar ./ ../ etc
    resolved_path = os.path.normpath(resolved_path)

    return resolved_path


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


# ---------------------------------------------------------------------------
#                        Columnas de la tabla principal
# ---------------------------------------------------------------------------
# Viven ACA y no en el FileScanner porque los delegados de este modulo tambien
# las necesitan, y el FileScanner ya importa de aca: al reves seria circular.
# Estaban escritas en los dos lados —el FileScanner por nombre y los delegados
# por numero pelado— que es la forma segura de que se separen sin que nada
# avise.
#
# El '#' es la columna 5 y no la 0: se agrega al final y despues se mueve al
# primer lugar VISUAL con moveSection(). En Qt el orden visual es independiente
# del logico, asi que se ve primera sin correr un solo indice.
COL_PATH = 0
COL_READ = 1
COL_STATUS = 2
COL_FOLDER_DELETE = 3
COL_SEQUENCE = 4
COL_NUM = 5

# El aire a los costados del texto de la celda Read, el mismo `padding: 0 10`
# que el prototipo le da a esa columna.
READ_CELL_PADDING = 10

# Donde arranca el path adentro de su celda, y el aire que le queda del otro
# lado. Los usa PathDelegate al dibujar y el FileScanner al medir cuanto mide
# el path mas largo: si salieran de dos lados distintos, la medicion daria de
# menos y el path terminaria cortado igual.
PATH_CELL_LEFT = 6
PATH_CELL_RIGHT = 10

# --------------------------------------------------------------------------
#  Las ventanas de progreso: escaneo, copia y borrado
# --------------------------------------------------------------------------
PROGRESS_WIDTH = 340
PROGRESS_PADDING = 18
PROGRESS_SPACING = 14
PROGRESS_FONT_SIZE = 13
PROGRESS_BAR_HEIGHT = 6
PROGRESS_CLOSE_SIZE = 22


def _tema():
    """El tema que el usuario tiene elegido, leido del .ini.

    La ventana del escaneo se abre ANTES que la principal, asi que no hay a
    quien preguntarle: se lee la configuracion. Si algo falla queda el tema
    base, que es mejor que no pintar nada.
    """
    try:
        import LGA_MediaManager_config as mm_config

        apariencia = (
            mm_config.load_settings(theme_ids=UIStyle.theme_ids()).get("appearance")
            or {}
        )
        return UIStyle.theme(apariencia.get("theme"))
    except Exception:
        return UIStyle.theme(None)


def paint_row_separator(painter, rect, color):
    """
    La linea de 1 px que separa una fila de la siguiente.

    La dibuja CADA delegado en vez de salir de la hoja de estilo. La regla
    `QTableWidget::item { border-bottom }` no se ve: todas las columnas de esta
    tabla tienen delegado propio y pintan la celda entera ellos, asi que el
    borde que dibujaria el estilo queda tapado. Y la grilla de Qt tampoco
    sirve, porque dibuja tambien las verticales, que el disenio no tiene.

    Va en ROW_LINE y no en BORDER: en el prototipo la tabla principal separa
    sus filas con un gris MAS CLARO que la fila -un divisor que suma- mientras
    que la tabla de los ajustes usa el borde, que es otro token y va un punto
    mas arriba. Son dos valores distintos a proposito.
    """
    painter.save()
    painter.setPen(QColor(color))
    painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
    painter.restore()


# ---------------------------------------------------------------------------
#                        Iconos de trazo, teñidos
# ---------------------------------------------------------------------------
# Los SVG de Lucide vienen con stroke="currentColor", que en Qt no hereda nada:
# QIcon los dibujaria negros. Se reemplaza el token por el hex antes de armar
# el icono, asi el mismo archivo sirve para el estado normal y el hover en vez
# de tener que guardar una copia por color.
_ICONS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")
_icon_cache = {}


def _device_pixel_ratio():
    """
    Cuantos pixeles fisicos hay por pixel logico. 1.0 si no se puede saber.

    Se pregunta a la aplicacion y no a una pantalla concreta: el icono se
    cachea por (nombre, color, tamano) y se puede terminar dibujando en
    cualquier monitor, asi que no hay una respuesta por widget.
    """
    try:
        app = QApplication.instance()
        if app is not None:
            return float(app.devicePixelRatio())
    except Exception:
        pass
    return 1.0


def tinted_icon(name, color, size=24):
    """
    Un icono de py/icons/lucide-<name>.svg pintado del color pedido.

    Devuelve un QIcon vacio si el archivo no esta: un icono que falta deja el
    boton sin dibujo, que es feo, pero no tiene que voltear la ventana.
    """
    clave = (name, color, size)
    if clave in _icon_cache:
        return _icon_cache[clave]

    icono = QIcon()
    ruta = os.path.join(_ICONS_DIR, "lucide-%s.svg" % name)
    try:
        with open(ruta, "r", encoding="utf-8") as handle:
            svg = handle.read()
        svg = svg.replace("currentColor", color)
        pixmap = QPixmap()
        # El QByteArray evita tener que escribir un archivo por color.
        if pixmap.loadFromData(QByteArray(svg.encode("utf-8")), "SVG"):
            # El pixmap se arma a la escala de la PANTALLA y no a la logica.
            # Antes se escalaba a `size` en pixeles de dispositivo 1x y Qt lo
            # agrandaba al doble al dibujarlo en un monitor Retina: por eso el
            # engranaje, la lupa, el refresh y las flechitas de ordenar salian
            # borrosos contra los trazos limpios del prototipo. Marcarle el
            # devicePixelRatio es lo que hace que Qt lo dibuje del tamano
            # logico correcto en vez de volver a estirarlo.
            escala = _device_pixel_ratio()
            if size:
                fisico = max(1, int(round(size * escala)))
                if pixmap.width() != fisico:
                    pixmap = pixmap.scaled(
                        fisico, fisico, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                pixmap.setDevicePixelRatio(escala)
            icono = QIcon(pixmap)
        else:
            # Sin el plugin de SVG el tenido no se puede hacer, pero el icono
            # de trazo negro es mejor que ningun icono.
            icono = QIcon(ruta)
    except (OSError, ValueError):
        pass

    _icon_cache[clave] = icono
    return icono


# El texto que lleva la celda Read cuando la fila no tiene ningun Read. Es un
# CENTINELA del modelo y no lo que se muestra: medio FileScanner pregunta
# `!= "-"` para decidir si hay Read, asi que el guion corto se queda en el
# item y la raya del disenio la dibuja ReadCellDelegate al pintar.
READ_NONE = "-"


class ReadCellDelegate(QStyledItemDelegate):
    """
    La celda de la columna Read.

    Existe por tres cosas que el item pelado hacia distinto del prototipo:
    iba CENTRADA cuando el disenio la alinea a la izquierda, iba en el gris
    fuerte cuando el disenio la pone en el gris de cuerpo, y mostraba el
    centinela "-" tal cual en vez de la raya.

    La sustitucion se hace al DIBUJAR y no en el modelo justamente para no
    tocar el centinela: cambiarlo por una raya en el item obligaba a revisar
    las ocho comparaciones `!= "-"` que deciden si una fila tiene Read, y una
    que se escapara habria roto el borrado o el relink en silencio.
    """

    # Raya (en dash) y no guion: es lo que dibuja el prototipo, y a la altura
    # de la x de la fuente el guion corto casi no se ve.
    DASH = "–"

    def __init__(self, table, ui, font_size=13, parent=None):
        super().__init__(parent or table)
        self.table = table
        self.UI = ui
        self.font_size = font_size

    def set_theme(self, ui, font_size):
        self.UI = ui
        self.font_size = font_size

    def paint(self, painter, option, index):
        C = self.UI.Color if self.UI else Color
        texto = index.data(Qt.DisplayRole) or ""
        vacia = not texto.strip() or texto.strip() == READ_NONE

        painter.save()
        # El fondo de la seleccion se pinta ACA y no se le deja al estilo. La
        # hoja de la tabla declara `item:selected` transparente a proposito
        # -si no, le ganaria al color propio de la columna Status- asi que
        # delegarlo dejaba esta celda con el gris de fondo normal: la fila
        # elegida se veia iluminada salvo un bloque oscuro justo en Read.
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(C.SURFACE_SELECTED))

        fuente = QFont(option.font)
        fuente.setPixelSize(max(1, self.font_size - 1))
        painter.setFont(fuente)
        painter.setPen(QColor(C.TEXT_DIM if vacia else C.TEXT))
        caja = option.rect.adjusted(READ_CELL_PADDING, 0, -READ_CELL_PADDING, 0)
        painter.drawText(
            caja,
            Qt.AlignLeft | Qt.AlignVCenter,
            self.DASH if vacia else texto,
        )
        painter.restore()
        paint_row_separator(painter, option.rect, C.ROW_LINE)


class PathDelegate(QStyledItemDelegate):
    """
    Dibuja el path coloreado de la columna 0, sin un QLabel por celda.

    Antes cada path era un QLabel puesto con setCellWidget(), y eso se rompia
    solo: la tabla ordena por la columna 0, asi que el setItem() de esa misma
    columna movia la fila en el acto y el setCellWidget() de despues le
    colgaba el label a OTRA fila. Quedaban filas con dos labels encima y
    filas sin ninguno, y una fila sin label mostraba el path invisible,
    porque el texto del item se pinta transparente a proposito.

    Dibujandolo al pintar, el color y el resaltado de la busqueda se
    recalculan solos y dejan de depender de que un widget siga en su lugar.
    De paso el filtro en vivo sale barato: solo se repinta lo visible.
    """

    def __init__(self, table, ui, font_size=13, parent=None):
        super().__init__(parent or table)
        self.table = table
        self.UI = ui
        self.font_size = font_size
        self.shot_segs = []
        self.query = ""
        # El scroll horizontal de esta columna. Ver set_offset().
        self.offset = 0
        self._doc = QTextDocument()
        self._doc.setDocumentMargin(0)

    def set_theme(self, ui, font_size):
        self.UI = ui
        self.font_size = font_size

    def set_shot_segments(self, segmentos):
        """Los segmentos de la carpeta del shot: el ancla del coloreo."""
        self.shot_segs = list(segmentos or [])

    def set_query(self, texto):
        """Lo que se esta buscando, para resaltarlo."""
        self.query = texto or ""

    def _html(self, path):
        import LGA_MediaManager_paths as mm_paths

        UI = self.UI
        return mm_paths.path_html(
            path,
            self.shot_segs,
            common=UI.Color.PATH_COMMON,
            palette=tuple(PATH_PALETTE),
            filename=UI.Color.TEXT_STRONG,
            # Las barras van del color del texto fuerte y no grises: en la
            # tabla separan tramos de colores y en gris se pierden.
            separator=UI.Color.TEXT_STRONG,
            query=self.query,
            mark_bg=UI.Color.MARK_BG,
        )

    def set_offset(self, pixeles):
        """
        Cuanto se corre el path hacia la izquierda dentro de su celda.

        Es el scroll horizontal de ESTA columna sola. La tabla entera no
        scrollea a proposito: si lo hiciera, el numero de fila, el Read y el
        Status se irian de la vista, y esos tienen que estar siempre.
        """
        pixeles = max(0, int(pixeles))
        if pixeles == self.offset:
            return False
        self.offset = pixeles
        return True

    def paint(self, painter, option, index):
        path = index.data() or ""
        painter.save()

        seleccionada = bool(option.state & QStyle.State_Selected)
        if seleccionada:
            painter.fillRect(option.rect, QColor(self.UI.Color.SURFACE_SELECTED))

        # El recorte va ANTES de mover el origen y en coordenadas de la celda:
        # asi vale igual con cualquier desplazamiento. Puesto despues, el
        # rectangulo se corria junto con el texto y el path se salia de su
        # columna al scrollear.
        painter.setClipRect(option.rect)

        # El path va un punto mas grande que el resto de la tabla: se lee
        # caracter por caracter -un 8 contra un 3, un _v02 contra un _v03- y a
        # la misma medida que el resto es lo primero que cuesta.
        fuente = QFont(option.font)
        fuente.setPixelSize(self.font_size + 1)
        self._doc.setDefaultFont(fuente)
        self._doc.setHtml(self._html(path))
        # Sin wrap: es una linea, y lo que no entra se recorta contra el
        # ancho de la columna.
        opciones = QTextOption()
        opciones.setWrapMode(QTextOption.NoWrap)
        self._doc.setDefaultTextOption(opciones)
        self._doc.setTextWidth(-1)

        alto = self._doc.size().height()
        painter.translate(
            option.rect.left() + PATH_CELL_LEFT - self.offset,
            option.rect.top() + max(0, (option.rect.height() - alto) / 2.0),
        )
        self._doc.drawContents(painter)
        painter.restore()
        paint_row_separator(painter, option.rect, self.UI.Color.ROW_LINE)


class PathResolveSignals(QObject):
    """El resultado de resolver rutas, de vuelta en el hilo principal."""

    # {clave de fila: Resolution}. Se manda el juego entero y no fila por
    # fila para que la ventana repinte una sola vez.
    resolved = Signal(object)


class PathResolveWorker(QRunnable):
    """
    Resuelve contra disco las rutas de la ventana de ajustes.

    Va en un worker porque un comodin contra un servidor tarda: resolverlo en
    el hilo principal cuelga la ventana entera mientras se escribe.
    """

    def __init__(self, pedidos, nk_dir):
        super().__init__()
        # pedidos: [(clave, ruta), ...]. La clave la pone quien llama para
        # poder devolverle cada resultado a su fila aunque el orden cambie.
        self.pedidos = list(pedidos)
        self.nk_dir = nk_dir
        self.signals = PathResolveSignals()
        self._cancelado = False
        # Sin esto Qt destruye el objeto C++ apenas run() termina, y el
        # cancel() que la ventana hace al cerrarse tira RuntimeError sobre un
        # objeto que ya no existe.
        self.setAutoDelete(False)

    def cancel(self):
        """Deja de servir: el resultado ya no le interesa a nadie."""
        self._cancelado = True

    def run(self):
        import LGA_MediaManager_paths as paths

        resultados = {}
        for clave, ruta in self.pedidos:
            if self._cancelado:
                return
            try:
                resultados[clave] = paths.resolve(ruta, self.nk_dir)
            except Exception as problema:  # el disco puede fallar de mil formas
                debug_print("resolve fallo en %s: %s" % (ruta, problema))
                resultados[clave] = paths.Resolution(paths.EMPTY)
        if not self._cancelado:
            self.signals.resolved.emit(resultados)


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


# ---------------------------------------------------------------------------
#                     Copia y borrado: el plan y el worker
# ---------------------------------------------------------------------------
# Las dos operaciones siguen la MISMA forma, y es a proposito:
#
#   1. El hilo principal arma un PLAN: la lista completa de archivos reales,
#      resuelta desde la tabla, y las preguntas que haya que hacer se hacen
#      ACA, antes de arrancar.
#   2. El worker recibe el plan ya decidido y solo toca disco. No lee widgets,
#      no abre carteles y no pregunta nada.
#
# Es lo que resuelve de raiz los dos problemas que tenian las versiones
# anteriores: el borrado leia la tabla -rowCount(), item()- desde el hilo
# worker, que es comportamiento indefinido en Qt, y la copia terminaba
# corriendo shutil.copy en el hilo principal, o sea congelando la ventana que
# la barra de progreso decia estar animando.


class BatchSignals(QObject):
    """Las senales de una tanda. Viven en el hilo principal."""

    # (hechos, total) despues de cada archivo
    progress = Signal(int, int)
    # el archivo que se esta por tocar, para el cartel
    item = Signal(str)
    # (hechos, salteados, errores, cancelado)
    finished = Signal(int, int, list, bool)


class BatchWorker(QRunnable):
    """
    Base de las tandas: progreso, cancelacion y conteo de errores.

    La cancelacion es una BANDERA que se mira entre archivo y archivo, no un
    kill del hilo: cortar a la mitad de un shutil.copy deja un archivo
    truncado en el destino que despues parece bueno.
    """

    def __init__(self, items):
        super(BatchWorker, self).__init__()
        self.items = list(items)
        self.signals = BatchSignals()
        self.signals.moveToThread(QApplication.instance().thread())
        self.logger = configure_logger()
        self._cancelado = False
        # Cada cuantos archivos se avisa. Ver avisa().
        self._cada = max(1, len(self.items) // 200)
        # Sin esto Qt destruye el objeto C++ apenas run() termina, y el
        # cancel() que la ventana hace al cerrarse tira RuntimeError: el
        # `finished` viaja en cola, asi que hay un hueco entre que el worker
        # muere y que el hilo principal se entera.
        self.setAutoDelete(False)

    def cancel(self):
        self._cancelado = True

    def cancelado(self):
        return self._cancelado

    def avisa(self, indice):
        """
        Si a este archivo le toca avisar del progreso.

        Con una secuencia de tres mil frames, una senal por archivo son seis
        mil eventos en la cola del hilo principal y tres mil repintados del
        cartel: la ventana que deberia mostrar que la herramienta avanza es
        justamente la que la frena. Con tandas chicas avisa siempre; con
        tandas grandes, unas doscientas veces en total, que es mas de lo que
        una barra de progreso puede mostrar.
        """
        return indice % self._cada == 0

    def ultimo(self, hechos, errores):
        """Si ya no queda nada: el ultimo aviso sale siempre."""
        return hechos + errores >= len(self.items)


class CopyWorker(BatchWorker):
    """
    Copia una tanda ya resuelta. Cada item es (origen, destino_final).

    El destino viene completo -carpeta y nombre- porque decidirlo es parte del
    plan, no de la copia: ahi es donde se resuelve si una secuencia va a su
    propia subcarpeta y si algo se sobreescribe o se saltea.
    """

    @Slot()
    def run(self):
        hechos = 0
        errores = []
        try:
            for indice, (origen, destino) in enumerate(self.items):
                if self._cancelado:
                    break
                avisa = self.avisa(indice)
                if avisa:
                    self.signals.item.emit(os.path.basename(origen))
                try:
                    carpeta = os.path.dirname(destino)
                    if carpeta and not os.path.isdir(carpeta):
                        os.makedirs(carpeta, exist_ok=True)
                    # copy2 y no copy: conserva fecha de modificacion, que en
                    # media es lo que despues permite comparar dos copias.
                    shutil.copy2(origen, destino)
                    hechos += 1
                except Exception as problema:
                    errores.append("%s: %s" % (os.path.basename(origen), problema))
                if avisa or self.ultimo(hechos, len(errores)):
                    self.signals.progress.emit(hechos + len(errores), len(self.items))
        except Exception as problema:
            errores.append(str(problema))
        # Salteados: los que el plan dejo afuera ya no estan en self.items, asi
        # que aca solo se informa lo que se dejo sin hacer por la cancelacion.
        sin_hacer = len(self.items) - hechos - len(errores)
        self.signals.finished.emit(hechos, max(0, sin_hacer), errores, self._cancelado)


class DeleteWorker(BatchWorker):
    """
    Manda a la papelera una tanda ya resuelta. Cada item es una ruta real.

    SIEMPRE a la papelera, nunca borrado permanente: es la unica red que tiene
    el usuario si se equivoco de seleccion, y la herramienta borra media de
    proyectos.
    """

    @Slot()
    def run(self):
        hechos = 0
        errores = []
        try:
            for indice, ruta in enumerate(self.items):
                if self._cancelado:
                    break
                avisa = self.avisa(indice)
                if avisa:
                    self.signals.item.emit(os.path.basename(ruta))
                try:
                    # send2trash quiere separadores nativos. La version vieja
                    # los forzaba a '\\' siempre, o sea que en macOS y Linux le
                    # pasaba rutas que no existen.
                    send2trash.send2trash(os.path.normpath(ruta))
                    hechos += 1
                except Exception as problema:
                    errores.append("%s: %s" % (os.path.basename(ruta), problema))
                if avisa or self.ultimo(hechos, len(errores)):
                    self.signals.progress.emit(hechos + len(errores), len(self.items))
        except Exception as problema:
            errores.append(str(problema))
        sin_hacer = len(self.items) - hechos - len(errores)
        self.signals.finished.emit(hechos, max(0, sin_hacer), errores, self._cancelado)


# El rango de frames va SIEMPRE al final del nombre y acepta signo: un Read
# offline puede traer origfirst negativo. Sin anclar al final, un '[' en el
# propio nombre del archivo -"take[1-2]_####.exr"- partia mal la ruta.
_RANGO_RE = re.compile(r"\[(-?\d+)-(-?\d+)\]\s*$")


def expand_sequence(path):
    """
    Los archivos REALES de una fila de la tabla.

    Una fila puede ser un archivo suelto o una secuencia escrita
    `nombre.####.exr[1001-1129]`. Devuelve siempre una lista, asi que quien
    llama no tiene que preguntar cual de las dos cosas es; con una lista vacia
    quiere decir que no pudo interpretarla.

    Vive aca y no adentro de cada worker porque la usan los dos y ademas el
    hilo principal, que necesita CONTAR los archivos antes de preguntar nada.

    Tres cosas que parecen detalles y no lo son, porque esta herramienta las
    genera sola:

      - El grupo de '#' del frame es el ULTIMO, no el primero: un nombre puede
        traer una version escrita "sh010_v###_####.exr". Se sustituye POR
        POSICION y no con str.replace, que reemplazaria los dos grupos.
      - El rango va anclado al final: un '[' en el nombre no es el rango.
      - El rango acepta signo: origfirst puede ser negativo.
    """
    if not path:
        return []
    ruta = path.replace("\\", "/")
    if "#" not in ruta:
        return [os.path.normpath(ruta)]

    rango = _RANGO_RE.search(ruta)
    if not rango:
        return []
    inicio, fin = int(rango.group(1)), int(rango.group(2))
    if fin < inicio:
        return []
    base = ruta[: rango.start()]

    # El ULTIMO grupo de '#', que es el del frame.
    grupos = list(re.finditer(r"#+", base))
    if not grupos:
        return []
    marca = grupos[-1]
    relleno = marca.end() - marca.start()
    izquierda, derecha = base[: marca.start()], base[marca.end():]

    salida = []
    for f in range(inicio, fin + 1):
        # zfill no sirve con negativos -pone los ceros antes del signo- asi que
        # el relleno se arma a mano.
        signo = "-" if f < 0 else ""
        numero = signo + str(abs(f)).rjust(relleno - len(signo), "0")
        salida.append(os.path.normpath(izquierda + numero + derecha))
    return salida


class ProgressWindow(QWidget):
    """
    La ventana de progreso del pack: escaneo, copia y borrado.

    Frameless con esquinas redondeadas y todo el color del tema. Al no tener
    marco no hay boton de cerrar del sistema, asi que la X va adentro, arriba a
    la derecha, y ABORTA la operacion en vez de solo esconder la ventana:
    esconderla dejaria el trabajo corriendo sin nada que lo muestre, que es
    peor que no poder cerrarla.

    El corte siempre es ENTRE archivos, nunca a la mitad de uno.
    """

    cancelled = Signal()

    def __init__(self, message, parent=None, ui=None, cancelable=True):
        super(ProgressWindow, self).__init__(parent)
        self.UI = ui or _tema()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # Las esquinas redondeadas necesitan que el fondo de la VENTANA sea
        # transparente: si no, Qt pinta el rectangulo entero por debajo y las
        # cuatro esquinas quedan cuadradas igual. Lo que se ve es el marco de
        # adentro, que es quien lleva el color y el radio.
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        afuera = QVBoxLayout(self)
        afuera.setContentsMargins(0, 0, 0, 0)

        self.marco = QFrame(self)
        self.marco.setObjectName("lgaProgressCard")
        self.marco.setAttribute(Qt.WA_StyledBackground, True)
        self.marco.setFrameShape(QFrame.NoFrame)
        afuera.addWidget(self.marco)

        adentro = QVBoxLayout(self.marco)
        adentro.setContentsMargins(
            PROGRESS_PADDING, PROGRESS_PADDING - 6, PROGRESS_PADDING, PROGRESS_PADDING
        )
        adentro.setSpacing(PROGRESS_SPACING)

        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        fila.addWidget(self.label, 1)

        self.close_button = QPushButton("\u2715")
        self.close_button.setFixedSize(PROGRESS_CLOSE_SIZE, PROGRESS_CLOSE_SIZE)
        self.close_button.setToolTip("Cancela la operacion y cierra")
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self._cancelar)
        self.close_button.setVisible(cancelable)
        fila.addWidget(self.close_button, 0, Qt.AlignTop)
        adentro.addLayout(fila)

        self.progressBar = QProgressBar(self.marco)
        self.progressBar.setRange(0, 100)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFixedHeight(PROGRESS_BAR_HEIGHT)
        adentro.addWidget(self.progressBar)

        self.apply_theme(self.UI)
        self.setFixedWidth(PROGRESS_WIDTH)

    # ------------------------------------------------------------- estilo ---
    def apply_theme(self, ui):
        """Todo el color sale del tema: ni un hex suelto."""
        self.UI = ui or _tema()
        C = self.UI.Color
        UIStyle.apply_ui_font(self)
        self.marco.setStyleSheet(
            "#lgaProgressCard { background-color: %s; border: 1px solid %s;"
            " border-radius: %dpx; }"
            % (C.WINDOW, C.BORDER, UIStyle.Metric.RADIUS_CARD)
        )
        # Sin negrita: es un cartel de espera, no un titulo.
        self.label.setStyleSheet(
            "QLabel { background: transparent; border: none; color: %s;"
            " font-size: %dpx; }" % (C.TEXT_STRONG, PROGRESS_FONT_SIZE)
        )
        self.close_button.setStyleSheet(self.UI.Style.BTN_CLOSE)
        self.progressBar.setStyleSheet(
            "QProgressBar { background-color: %s; border: none;"
            " border-radius: %dpx; }"
            "QProgressBar::chunk { background-color: %s; border-radius: %dpx; }"
            % (
                C.SURFACE_SUNKEN,
                PROGRESS_BAR_HEIGHT // 2,
                C.ACCENT,
                PROGRESS_BAR_HEIGHT // 2,
            )
        )

    # -------------------------------------------------------------- estado ---
    def _cancelar(self):
        """La X: avisa que hay que abortar. NO cierra sola.

        Quien recibe `cancelled` es el que sabe cuando la operacion realmente
        se detuvo: el worker corta entre archivos y puede tardar en enterarse.
        Cerrar aca dejaria la ventana muerta con el trabajo todavia corriendo.
        """
        self.close_button.setEnabled(False)
        self.set_message("Cancelling...")
        self.cancelled.emit()

    def set_message(self, texto):
        self.label.setText(texto)

    def set_progress(self, hechos, total):
        """Progreso real, en cantidad de archivos."""
        if total <= 0:
            return
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(min(hechos, total))

    def stop(self):
        self.close()


class StartupWindow(ProgressWindow):
    """
    La ventana del escaneo inicial. Es la PRIMERA que ve el usuario.

    Lo unico que agrega sobre la base es el progreso que avanza SOLO hasta que
    llegue el real del worker: sin eso la barra se queda en cero durante toda
    la primera etapa y la ventana parece colgada.
    """

    def __init__(self, message, parent=None, ui=None):
        super(StartupWindow, self).__init__(message, parent, ui)
        self.setWindowTitle("Starting...")
        self.setFixedSize(PROGRESS_WIDTH, self.sizeHint().height())
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgressBar)
        self.timer.start(100)

    def updateProgressBar(self):
        current_value = self.progressBar.value()
        if current_value < 100:
            self.progressBar.setValue(current_value + 1)
        else:
            self.timer.stop()

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def stop(self):
        self.timer.stop()
        super(StartupWindow, self).stop()


class ScannerSignals(QObject):
    progress = Signal(int)  # Para actualizar la barra de progreso
    finished = Signal()  # Para indicar que terminó el escaneo
    files_found = Signal(list)  # Para enviar los archivos encontrados


class RelinkSearchSignals(QObject):
    # Ruta encontrada, o cadena vacia si no aparecio nada
    finished = Signal(str)


class RelinkSearchWorker(QRunnable):
    """
    Busca el archivo de un Read offline recorriendo una carpeta.

    Va en un worker porque el os.walk puede tardar muchisimo sobre un
    servidor: hecho en el hilo principal congela Nuke entero y ni siquiera
    se repinta la ventanita de "Searching...". Aca no se toca la UI ni la
    API de Nuke: el resultado viaja por senal y lo aplica el hilo principal.
    """

    def __init__(self, directory, exact_name, sequence_pattern):
        super(RelinkSearchWorker, self).__init__()
        self.directory = directory
        self.exact_name = exact_name
        self.sequence_pattern = sequence_pattern
        self.signals = RelinkSearchSignals()
        self.logger = configure_logger()
        # Cortar la busqueda. Bandera y no kill, igual que en el escaneo: se
        # la mira en cada carpeta del walk.
        self._cancelado = False
        # Mismo motivo que en BatchWorker: la X puede llegar despues de que
        # run() termino y antes de que el hilo principal procese el finished.
        self.setAutoDelete(False)

    def cancel(self):
        self._cancelado = True

    def cancelado(self):
        return self._cancelado

    def run(self):
        # El primer candidato del patron se guarda pero la busqueda sigue: el
        # match exacto tiene prioridad y puede aparecer mas adelante.
        fallback_path = ""
        try:
            for root, dirs, files in os.walk(self.directory):
                if self._cancelado:
                    self.logger.debug("Busqueda del relink cancelada")
                    break
                if "$RECYCLE.BIN" in [
                    os.path.basename(parte)
                    for parte in os.path.normpath(root).split(os.path.sep)
                ]:
                    continue

                for nombre in files:
                    if self.exact_name and nombre.lower() == self.exact_name:
                        encontrado = os.path.join(root, nombre)
                        self.logger.debug(
                            f"Archivo encontrado (match exacto): {encontrado}"
                        )
                        self.signals.finished.emit(encontrado)
                        return

                    if (
                        not fallback_path
                        and self.sequence_pattern is not None
                        and self.sequence_pattern.match(nombre)
                    ):
                        fallback_path = os.path.join(root, nombre)
        except Exception as error:
            self.logger.debug(f"Error recorriendo {self.directory}: {error}")

        if fallback_path:
            self.logger.debug(
                f"Archivo encontrado (match por patron de secuencia): {fallback_path}"
            )
        else:
            self.logger.debug("No se encontro ningun archivo compatible")
        self.signals.finished.emit(fallback_path)


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
        # Abortar el escaneo. Es una bandera y no un kill: el worker corre en
        # un hilo del pool y matarlo dejaria la tabla a medio llenar. Se la
        # mira en TODOS los bucles largos -el conteo inicial, la fase 1, las
        # dos pasadas de find_files y antes de buscar los Reads sueltos- y ahi
        # devuelve, que es lo mas cerca de "ya" que se puede estar sin romper
        # nada.
        self._cancelado = False
        # La X de la ventana de escaneo puede llegar despues de que run()
        # termino: sin esto el objeto C++ ya no esta y cancel() explota.
        self.setAutoDelete(False)

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

    def parse_training_sequence_filename(self, filename):
        """
        Detecta si un archivo pertenece a una secuencia especial de Cattery/Nuke (Training_)

        Args:
            filename: Nombre del archivo a evaluar

        Returns:
            tuple: (base_name, frame, extension) si es secuencia Training_, (None, None, None) si no
        """
        import re

        # Patron especifico para secuencias Training_: Training_YYMMDD_HHMMSS.FRAME.png o Training_YYMMDD_HHMMSS.FRAME.cat
        pattern = r"^(Training_\d{6}_\d{6}\.)([0-9]+)\.(png|cat)$"
        match = re.match(pattern, filename)

        if match:
            base_name = match.group(1)  # Training_YYYYMMDD_HHMMSS.
            frame_str = match.group(2)  # numero de frame
            extension = "." + match.group(3)  # .png o .cat

            try:
                frame = int(frame_str)
                return base_name, frame, extension
            except ValueError:
                pass

        return None, None, None

    def cancel(self):
        """Pide cortar el escaneo. La atiende el propio worker, cuando puede."""
        self._cancelado = True

    def cancelado(self):
        return self._cancelado

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

            # Ya no se escanea UNA carpeta sino las scan locations, que pueden
            # ser varias: cada una entra a la cuenta del progreso y despues a
            # find_files. Si no hay ninguna se cae a la del shot, para que un
            # .ini sin locations no deje la ventana vacia.
            # La resolucion contra disco se hace ACA y no en el hilo
            # principal: es un os.scandir por nivel y por rama de cada
            # comodin, y contra un servidor eso cuelga la ventana entera.
            self.file_scanner.resolve_shot_folder()
            carpetas = list(self.file_scanner.resolve_scan_folders() or [])
            if not carpetas:
                # Sin ninguna location con Scan no habria nada que mostrar:
                # se cae a la carpeta del shot para no abrir la ventana vacia.
                carpetas = [self.file_scanner.project_folder]

            root_items = []
            for carpeta in carpetas:
                try:
                    for nombre in os.listdir(carpeta):
                        root_items.append((carpeta, nombre))
                except OSError:
                    self.logger.debug(
                        f"{self.get_timestamp()}   (No se pudo leer {carpeta})"
                    )
            for carpeta, item in root_items:
                if self._cancelado:
                    break
                item_path = os.path.join(carpeta, item)
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

            # Contar nodos Read para el calculo del progreso. Va envuelto:
            # allNodes desde el hilo del pool no es thread-safe, y con un
            # script grande el sintoma es un cuelgue duro de Nuke.
            total_reads = nuke.executeInMainThreadWithResult(
                lambda: len(nuke.allNodes("Read"))
            )

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
                # Solo la senal: viaja en cola al hilo principal y ahi se
                # repinta. El processEvents() que habia aca procesaba la cola
                # de ESTE hilo, que no tiene bucle de eventos, o sea que no
                # repintaba nada; y el sleep de 1 ms por item era un peaje de
                # segundos sobre un escaneo de miles de archivos.
                self.signals.progress.emit(progress)

            # Primera fase
            self.logger.debug(
                f"\n{self.get_timestamp()} Primera fase ({self.Etapa1_inicio}-{self.Etapa1_fin}%):"
            )
            processed_items = 0  # Reiniciar contador para la primera fase

            for carpeta, item in root_items:
                if self._cancelado:
                    break
                item_path = os.path.join(carpeta, item)
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
            files_data = []
            for carpeta in carpetas:
                files_data.extend(self.find_files(carpeta))
            find_files_time = time.time() - find_files_start

            # Segunda fase
            self.logger.debug(
                f"\n{self.get_timestamp()} Segunda fase ({self.Etapa3_inicio}-{self.Etapa3_fin}%):"
            )
            processed_items = 0  # Reiniciar contador para la segunda fase

            # Marcar inicio de search_unmatched_reads
            reads_start = time.time()
            # Cancelado: no se arranca otra etapa entera. search_unmatched_reads
            # hace un os.listdir por secuencia y toca Nuke por cada Read.
            if self._cancelado:
                self.signals.finished.emit()
                return
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

            # Cancelado: se avisa que termino pero SIN resultados. Cargar lo
            # que se alcanzo a juntar seria peor que no cargar nada -una tabla
            # incompleta se lee igual que una completa- y la ventana ya se esta
            # cerrando.
            if self._cancelado:
                self.signals.finished.emit()
                return

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
                # Sin processEvents: procesaba la cola de ESTE hilo, que no
                # tiene bucle de eventos, asi que no repintaba nada.
                self.signals.progress.emit(progress)

        # Log del inicio de la etapa 2
        self.logger.debug(
            f"\n{self.get_timestamp()} Segunda fase ({self.Etapa2_inicio}-{self.Etapa2_fin}%):"
        )

        for root, dirs, files in os.walk(folder):
            if self._cancelado:
                # Se corta acá y no en el medio de armar una secuencia: lo que
                # se devuelve es lo que ya estaba completo.
                self.logger.debug(f"{self.get_timestamp()} Escaneo cancelado")
                break
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

            # NUEVA LOGICA: Pre-procesar TODAS las secuencias Training_ del directorio
            processed_training_indices = set()
            all_training_groups = (
                {}
            )  # groupKey (baseName + extension) -> lista de (frame, filename)

            self.logger.debug(f"[COPYCAT] Procesando directorio: {root}")
            self.logger.debug(
                f"[COPYCAT] Archivos filtrados en directorio: {len(filtered_files)}"
            )
            training_files_found = [
                f for f in filtered_files if f.startswith("Training_")
            ]
            self.logger.debug(
                f"[COPYCAT] Archivos que empiezan con 'Training_': {len(training_files_found)}"
            )
            if training_files_found:
                self.logger.debug(
                    f"[COPYCAT] Lista de archivos Training_ encontrados: {training_files_found[:10]}{'...' if len(training_files_found) > 10 else ''}"
                )

            # Primer paso: Identificar TODOS los archivos Training_ del directorio
            for idx, filename in enumerate(filtered_files):
                if filename.startswith("Training_"):
                    self.logger.debug(
                        f"[COPYCAT] Analizando archivo Training_: '{filename}'"
                    )

                base_name, frame, extension = self.parse_training_sequence_filename(
                    filename
                )

                if filename.startswith("Training_"):
                    self.logger.debug(
                        f"[COPYCAT] Resultado parsing: base_name='{base_name}', frame={frame}, extension='{extension}'"
                    )

                if (
                    base_name is not None
                    and extension is not None
                    and frame is not None
                ):
                    # CLAVE: Usar baseName + extension para separar PNG y CAT
                    group_key = base_name + extension
                    if group_key not in all_training_groups:
                        all_training_groups[group_key] = []
                    all_training_groups[group_key].append((frame, filename))
                    processed_training_indices.add(idx)
                    self.logger.debug(
                        f"[COPYCAT] Pre-procesado Training_: '{filename}' -> groupKey='{group_key}', frame={frame}"
                    )

            # Segundo paso: Crear grupos para todas las secuencias Training_ encontradas
            self.logger.debug(
                f"[COPYCAT] Grupos Training_ encontrados: {len(all_training_groups)}"
            )
            for group_key, frame_filename_pairs in all_training_groups.items():
                self.logger.debug(
                    f"[COPYCAT] Grupo '{group_key}' tiene {len(frame_filename_pairs)} archivos"
                )
                # Solo crear grupo si tiene al menos 4 archivos
                if len(frame_filename_pairs) >= 4:
                    # Ordenar por frame para obtener el rango correcto
                    frame_filename_pairs.sort(key=lambda x: x[0])

                    frames = [pair[0] for pair in frame_filename_pairs]
                    first_frame = min(frames)
                    last_frame = max(frames)

                    # Extraer baseName y extension del groupKey
                    base_name = (
                        group_key.rsplit(".", 1)[0] + "."
                    )  # Training_YYYYMMDD_HHMMSS.
                    extension = "." + group_key.rsplit(".", 1)[1]  # .png o .cat

                    # Crear la clave de secuencia usando # para el padding variable
                    sequence_base = os.path.join(root, base_name + "#" + extension)

                    # Agregar al diccionario de secuencias
                    if sequence_base not in sequences:
                        sequences[sequence_base] = []
                    sequences[sequence_base] = sorted(set(frames))

                    self.logger.debug(
                        f"[COPYCAT] Creado grupo UNICO de secuencia: {base_name} | archivos: {len(frame_filename_pairs)} | rango: [{first_frame}-{last_frame}]"
                    )
                else:
                    self.logger.debug(
                        f"[COPYCAT] Grupo '{group_key}' descartado: solo tiene {len(frame_filename_pairs)} archivos (mínimo requerido: 4)"
                    )

            for i in range(len(filtered_files) - 1):
                file1, file2 = filtered_files[i], filtered_files[i + 1]
                # logging.info(f"Comparing: {file1} and {file2}")

                # Saltar archivos Training_ que ya fueron procesados
                if (
                    i in processed_training_indices
                    or (i + 1) in processed_training_indices
                ):
                    continue

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

                            # EXCEPCION: Excluir numeros de version que empiezan con 'v'
                            # Ejemplo: ETDM_3015_0010_DeAging_Cama_aPlate_Matte_r709_COPYCAT_1124_v02.tif
                            if left_part_file1.endswith(
                                "v"
                            ) or left_part_file2.endswith("v"):
                                # logging.info(f"Skipping version numbers: {frame_num1} and {frame_num2}")
                                continue

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

                                # EXCEPCION: Excluir numeros de version que empiezan con 'v'
                                # (segunda verificacion de consecutividad)
                                if left_part.endswith("v"):
                                    # logging.info(f"Skipping version numbers in second check: {frame_num1} and {frame_num2}")
                                    continue

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
            for idx, file in enumerate(filtered_files):
                file_path = os.path.join(root, file)
                # Actualizar progreso una sola vez por archivo
                update_find_progress(f"Procesando {file}")

                # Saltar archivos Training_ que ya fueron procesados
                if idx in processed_training_indices:
                    continue

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
