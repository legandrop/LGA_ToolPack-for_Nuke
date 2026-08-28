"""
_______________________________________

  LGA_MediaManager_settings v2.44 | Lega
  Ventana de ajustes del Media Manager

  v2.38: Add location lleva la fila nueva a la vista. Con la tabla ya
         en su alto maximo, la fila nacia abajo del area visible: la
         creaba, le ponia el foco y no se veia, asi que escribir el
         nombre parecia no hacer nada.
  v2.37: Seis desalineaciones entre el encabezado y las filas,
         medidas con Qt real. Los titulos de las tres columnas de
         texto se sangran lo mismo que su contenido -"Name" caia 35
         px antes que los nombres y "Path" 9 px antes que las rutas-
         con la cuenta escrita a partir de las medidas que la
         producen, no a ojo.
         La reserva de la barra de scroll deja de deducirse de si el
         contenido pasa el alto maximo: eso dejo de ser lo mismo que
         "hay barra" cuando la ventana se pudo achicar, y con pocas
         filas y la ventana baja las columnas de la derecha volvian a
         correrse 10 px. Ahora se mide la diferencia real entre el
         encabezado y el viewport, avisada por el propio viewport.
         El minimo de la caja reserva tambien esa barra: sin eso, en
         el ancho minimo con la barra puesta, a las filas les faltaban
         8 px y se los comia la papelera.
         El checkbox del shot pedia 22 px en una celda de 18 y Qt le
         recortaba 3 del indicador; va sin el padding de la hoja
         comun. El guion del atajo se centra -los 12 px de padding lo
         corrian 6,5 y prender Copy to movia el marcador- y "Shot
         folder" suma el pixel de borde que el campo tiene y el label
         no.
  v2.36: Los titulos de las tres columnas de la derecha SI estaban
         centrados; lo que estaba corrido era la columna. El
         encabezado llevaba un widget de ancho cero al final para
         reservar el ancho de la barra de scroll, y un QHBoxLayout
         pone su espaciado ENTRE items sin mirar cuanto mide cada
         uno: ese item de 0 px igual sumaba los 9 px de espaciado que
         van antes. El encabezado tenia entonces 9 px menos que las
         filas para repartir entre sus columnas elasticas y, como
         esas van primero, todo lo que venia despues quedaba corrido
         9 px a la izquierda. Ahora la barra se reserva con el margen
         derecho del layout, que no agrega ningun item.
         El ancho de las tarjetas se lo decide Qt: se le pregunta al
         propio label con heightForWidth() hasta que entre en los
         renglones que el texto declara. Calcularlo con QFontMetrics
         fallo dos veces -una por medir con otra fuente, otra por
         redondeo- y el sintoma siempre fue el mismo, un renglon de
         mas. El que envuelve es Qt, asi que decide Qt. La letra de
         la tarjeta va en su QFont y ya no en la hoja, para que medir
         y dibujar no puedan volver a usar dos fuentes distintas.
  v2.35: El ancho de las tarjetas se medía con la fuente equivocada,
         asi que seguia partiendo el renglon. El label no tiene la
         familia del pack cuando se lo crea -la ventana la aplicaba
         despues de armar- y su tamano se lo pone recien la hoja de
         estilo. Ahora la fuente del pack se aplica ANTES de armar y
         la medicion usa la familia y el tamano exactos con los que
         se dibuja. Las tres columnas de la derecha ceden otro tanto.
  v2.34: Las tres columnas de la derecha miden lo que mide su
         encabezado -el contenido son un checkbox y un par de
         teclas- y van centradas, titulo y contenido: "Copy
         Shortcut" quedaba pegado a la izquierda mientras las teclas
         caian al medio, y el sobrante del atajo se juntaba con el de
         la papelera dejandolas muy separadas.
         El ancho de las tarjetas de ayuda lo decide el renglon mas
         largo, MEDIDO. A ojo se quedaba corto por 10 px y el texto
         de dos renglones aparecia en tres, que es exactamente lo que
         vuelve a pasar cada vez que cambia el texto o la fuente.
  v2.33: "Resolves to" pasa de 120 a 185 de minimo. Muestra el
         nombre de una carpeta REAL y esos nombres son largos; con la
         ventana ya angosta se comia justo el dato que hay que
         verificar, que es para lo que existe la columna.
  v2.32: La ventana se puede achicar. El minimo de ancho sale del
         contenido y no del 1180 escrito a mano, que era mas ancho
         que lo que la tabla necesita; el area de filas se puede
         comprimir hasta dos filas en vez de tener el alto entero
         del contenido como piso.
         Las columnas se ajustan a lo que usan: nombre y ruta ceden
         ancho -la ruta ademas deja de llevarse casi todo el
         sobrante, estiraba 14 contra los 9 del nombre-, las dos
         casillas se achican a lo que mide su encabezado y la del
         atajo pierde la franja muerta que quedaba antes de la
         papelera.
         La tarjeta de "included by another scan path" pasa a tener
         su propio ancho: con 360 el renglon mas largo se partia y
         mostraba tres lineas donde el texto tiene dos.
  v2.31: El aire de la fila de apariencia va ENTRE los dos grupos
         y no despues: "Table font size" queda pegado a su stepper y
         separado de la tira de temas. `addStretch()` sin argumento
         agrega un espaciador de factor CERO, que no se lleva el
         sobrante, asi que se lo repartia lo unico elastico que
         quedaba -el propio QLabel- y el hueco caia justo al medio
         del grupo de la fuente.
  v2.30: Poner Inter no alcanzaba: sus tres caras NO forman una
         sola familia para Qt. La Regular y la Bold caen las dos en
         "Inter", pero la SemiBold cae en una familia PROPIA, "Inter
         SemiBold". Con eso, `font-weight: 600` sobre "Inter" no
         devuelve la SemiBold sino la cara mas cercana que si esta
         en esa familia: la Bold de 700. Por eso la etiqueta de los
         botones, la cabecera de la tabla, los contadores de las
         pastillas, la leyenda y Rescan seguian saliendo en negrita.
         Ahora el peso 600 se pide nombrando la familia.
  v2.29: La ventana toma la fuente del pack. Sin ella el
         `font-weight` de las hojas no encontraba una cara real y
         macOS sintetizaba la negrita, con lo que todo lo que el
         disenio pide en 600 salia con el peso de una 700 falsa.
  v2.28: El tema se guarda solo al elegirlo, y escribe sobre lo
         GUARDADO: las locations, el shot y el tamano de letra a medio
         editar no se cuelan por ese atajo. Cancel y Save arrancan
         apagados y se encienden juntos cuando hay algo que descartar
         o que guardar, contra el estado con el que abrio la ventana.
         El campo de ruta avisa por tecla para eso, aunque siga
         resolviendo contra disco recien al soltarlo: sin ese aviso,
         escribir una ruta y hacer click directo en Save no guardaba
         nada, porque un boton deshabilitado no acepta el click ni
         mueve el foco y editingFinished no llegaba a dispararse.
         Cancel y Save llevan su propio espaciado: el default del
         layout lo pone el host y en macOS es 0, asi que salian
         pegados.
  v2.27: Se rehace contra el esquema nuevo del .ini. El destino de
         Copy to y la carpeta a escanear pasan a ser la misma cosa
         -una location- asi que hay una sola tabla, con Scan y Copy
         to como dos casillas de la misma fila. El atajo sale de su
         propio campo y no del '&' embebido en el nombre.
         El Folder scan depth se va: la carpeta del shot es ahora
         una ruta explicita, y es la primera fila de la tabla.
         Cada fila muestra a que carpeta REAL llega su ruta, que se
         resuelve en un worker: un comodin contra un servidor
         resuelto en el hilo principal cuelga la ventana.
         Suma tema y tamano de letra, que se aplican en vivo y se
         revierten con Cancel.
         La tabla es una caja con borde y esquinas redondeadas, con
         la cabecera en SURFACE_HEADER y un separador por fila; la
         fila se ilumina al pasar por encima y el arrastre muestra
         adonde cae en vez de solo aclarar el texto.
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

import os
import re

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore, horizontal_advance
import LGA_UI_Style_ToolPack as UIStyle
import LGA_MediaManager_paths as paths
from LGA_MediaManager_config import (
    DEFAULT_APPEARANCE,
    DEFAULT_SHOT,
    format_ini,
    get_write_path,
    save_settings,
    write_ini,
)
from LGA_MediaManager_logging import debug_print
from LGA_MediaManager_utils import PathResolveWorker, tinted_icon

QWidget = QtWidgets.QWidget
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QPushButton = QtWidgets.QPushButton
QCheckBox = QtWidgets.QCheckBox
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QScrollArea = QtWidgets.QScrollArea
QFrame = QtWidgets.QFrame
QMessageBox = QtWidgets.QMessageBox
Qt = QtCore.Qt
Signal = QtCore.Signal
QTimer = QtCore.QTimer
QThreadPool = QtCore.QThreadPool


# --------------------------------------------------------------------------
#                              Medidas
# --------------------------------------------------------------------------
# Las columnas de la tabla. Cada fila y el encabezado usan EXACTAMENTE esta
# lista: si no salieran del mismo lugar se desalinean en cuanto una cambia.
# (ancho fijo o None, factor de estiramiento, ancho minimo)
COL_GRIP = (34, 0, 34)
COL_NAME = (None, 9, 130)
# La ruta se lleva menos sobrante que antes (estiraba 14 contra los 9 del
# nombre): con la ventana ancha era casi el doble que todo lo demas junto y la
# tabla se leia desbalanceada. Sigue siendo la mas ancha, que es lo correcto
# -es el contenido mas largo- pero ya no absorbe sola el crecimiento.
COL_PATH = (None, 9, 190)
# "Resolves to" muestra el nombre de una carpeta real -no un patron- y esos
# nombres son largos: ERSO_000_10133B_Test entra justo en 180. Con 120 la
# columna se comia el nombre justo en la fila donde hay algo que verificar,
# que es para lo que existe. Estira un poco mas que el nombre porque su
# contenido no se puede acortar: o entra o dice "2 folders".
COL_REAL = (None, 9, 185)
# Las tres columnas de la derecha miden lo que mide su ENCABEZADO, que es lo
# mas ancho que tienen adentro: el contenido son un checkbox de 19 px y un par
# de teclas. Cualquier holgura sobre eso se lee como un hueco entre columnas,
# no como aire. El titulo y el contenido van los dos centrados, asi que la
# columna se lee como una sola cosa.
COL_SCAN = (42, 0, 42)
COL_COPY = (56, 0, 56)
# 170 era el valor literal de la grilla del prototipo, con una franja libre a
# la derecha del campo. En la ventana real esa franja se sumaba a la de la
# papelera y quedaban casi 100 px muertos entre el atajo y el tacho.
COL_KEY = (96, 0, 96)
COL_TRASH = (34, 0, 34)
COLUMNS = (COL_GRIP, COL_NAME, COL_PATH, COL_REAL, COL_SCAN, COL_COPY,
           COL_KEY, COL_TRASH)

# La separacion entre columnas. La usan el encabezado y cada fila, y tiene que
# ser la MISMA en los dos: son dos QHBoxLayout distintos que se alinean solo
# porque recorren la misma lista con el mismo espaciado.
COLUMN_SPACING = 9

# El minimo lo pone el CONTENIDO -la suma de los minimos de las columnas mas
# los margenes- y no un numero escrito a mano. El 1180 de antes era mas ancho
# que lo que la tabla necesita, asi que la ventana no se podia achicar hasta
# donde el contenido lo permitia: sobraban casi 200 px que no se podian sacar.
WINDOW_MIN_HEIGHT = 420

# Las tarjetas de ayuda. El ancho NO es una constante: lo mide _card_width()
# sobre el renglon mas largo del texto, porque el texto ya trae sus saltos de
# linea escritos y una tarjeta mas angosta lo parte y suma un renglon que
# nadie escribio. De aca solo salen el piso y las medidas de su caja.
CARD_MIN_WIDTH = 360
CARD_PADDING = 15
CARD_ICON_SIZE = 20
CARD_ICON_GAP = 12
# El tamano con el que se DIBUJA el texto de la tarjeta. Sale de aca y lo usan
# los dos lados -la medicion del ancho y la hoja de estilo-: medir con un
# tamano y dibujar con otro es como no medir.
CARD_FONT_SIZE = 12
# Hasta donde puede crecer una tarjeta buscando que su renglon mas largo entre,
# y de a cuanto se prueba.
CARD_MAX_WIDTH = 720
CARD_WIDTH_STEP = 8
TABLE_MAX_HEIGHT = 420
# Cuantas filas tiene que seguir mostrando la tabla cuando la ventana se
# achica. Es el piso: de ahi para abajo no se comprime mas y la ventana
# tampoco. Con la fila del shot y una location alcanza para saber donde se
# esta parado; el resto se scrollea.
TABLE_MIN_ROWS = 2
# El aire que se deja abajo al llevar una fila a la vista, para que no quede
# lamiendo el borde del area.
ROW_REVEAL_MARGIN = 8

# Los altos se DERIVAN del tamano de letra en vez de ser constantes: sin eso,
# subir la letra la corta contra el borde de la fila.
ROW_EXTRA = 31  # 44 con letra 13
HEAD_EXTRA = 29  # 42 con letra 13
HEAD_FONT_OFFSET = -1  # la cabecera va un punto mas chica que la fila
HEAD_LETTER_SPACING = 0.4  # va por QFont: QSS no tiene letter-spacing

# La pastilla "Alt" y el campo de la letra tienen alto propio: sin fijarlo, un
# QLabel adentro de un QHBoxLayout se estira a todo el alto de la fila y la
# pastilla deja de leerse como una tecla.
KEY_HEIGHT = 28
KEY_MIN_WIDTH = 34
KEY_FONT = 12

# --------------------------------------------------------------------------
#  Alineacion del encabezado con las filas
# --------------------------------------------------------------------------
# El encabezado pone un QLabel pelado en cada columna y la fila pone widgets
# con estructura adentro, asi que el texto de los dos NO arranca en el mismo
# lugar salvo que se lo corrija. Estas medidas son las que reconstruyen, para
# el encabezado, el mismo margen que la fila tiene por su contenido. Si cambia
# alguna de las de abajo, el titulo se corre: son la misma cuenta.
#
# La ranura de la primera columna del nombre, y su separacion del campo.
# Suman 26, que es donde arrancan todos los nombres.
RANURA_WIDTH = 18
RANURA_GAP = 8
# El campo inline: 1 px de borde -transparente en reposo, pero ocupa- mas el
# padding horizontal de su hoja.
FIELD_BORDER = 1
FIELD_PADDING_H = 8
# Donde arranca el TEXTO de cada columna, contado desde el borde de la
# columna. El encabezado se sangra otro tanto para caer encima.
HEAD_INDENT_NAME = RANURA_WIDTH + RANURA_GAP + FIELD_BORDER + FIELD_PADDING_H
HEAD_INDENT_PATH = FIELD_BORDER + FIELD_PADDING_H
# "Resolves to" no lleva: su label no tiene ni borde ni padding.
HEAD_INDENT_REAL = 0

# Los botones de tema son mas chatos y con menos aire que los botones de
# accion del pie: son una tira de seis y con el padding del boton normal la
# fila no entraba.
THEME_BUTTON_HEIGHT = 34
THEME_BUTTON_PADDING = 14
THEME_BUTTON_FONT = 12

# El aire entre Cancel y Save, el mismo del prototipo. Va explicito porque el
# espaciado por default de un QHBoxLayout lo pone el estilo del host y en macOS
# es 0: los dos botones salian pegados.
FOOTER_BUTTON_GAP = 12

# La linea que marca donde cae la fila que se esta arrastrando.
DROP_LINE_WIDTH = 2
DRAG_OPACITY = 0.35

# Las cinco letras que ya usan los botones de la barra principal. Si una
# location toma una de estas, Qt no dispara NINGUNO de los dos y tira un
# warning de "ambiguous shortcut", asi que se rechazan.
RESERVED_SHORTCUTS = ("G", "R", "L", "C", "D")


# Los tooltips van en castellano y salen de aca, no hardcodeados en el widget,
# para que la migracion a bilingue sea un cambio de datos.
TOOLTIPS = {
    "shot_enabled": (
        "Sin shot folder no hay adentro ni afuera: Outside pasa a\n"
        "medirse contra las scan locations"
    ),
    "shot_path": "Carpeta del shot, relativa al .nk. Define que esta adentro",
    "name": "Nombre que aparece en el menu Copy to",
    "path": "Carpeta, relativa al .nk. Acepta * como comodin",
    "scan": "Buscar media adentro de esta carpeta",
    "scan_inherited": "Ya la cubre otra location que se escanea entera",
    "copy_to": "Ofrecer esta carpeta en el menu Copy to",
    "shortcut": "Letra del atajo, se dispara con Alt + esa letra",
    "remove": "Quita esta location",
    "add": "Agrega una location",
    "grip": "Arrastra para cambiar el orden del menu Copy to",
    "theme": "Paleta de colores de las dos ventanas",
    "font_minus": "Una letra mas chica",
    "font_plus": "Una letra mas grande",
    # Los de la columna "Resolves to" tambien son tooltips y van por el dict,
    # no escritos adentro de la funcion que los arma.
    "real_empty": "Sin ruta",
    "real_invalid": "La ruta sube mas alto que la raiz",
    "real_none": "Ninguna carpeta coincide",
    "real_one": "Resuelve a %s",
    "real_many": "Coinciden:",
}

# Lo que la columna "Resolves to" dice en cada caso. Estan juntos para que la
# fila del shot y las de locations digan lo mismo.
REAL_EMPTY = "—"
REAL_INVALID = "invalid path"
REAL_ABSOLUTE = "absolute"
REAL_NOT_FOUND = "not found"


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


def _card_font(base):
    """La fuente con la que se dibuja -y se mide- el texto de una tarjeta."""
    fuente = QtGui.QFont(base)
    familia = UIStyle.font_family()
    if familia:
        fuente.setFamily(familia)
    fuente.setPixelSize(CARD_FONT_SIZE)
    return fuente


def _apply_column(widget, columna):
    """Le da a un widget el ancho de su columna."""
    fijo, _estira, minimo = columna
    if fijo is not None:
        widget.setFixedWidth(fijo)
    else:
        widget.setMinimumWidth(minimo)


def _add_column(layout, widget, columna):
    _apply_column(widget, columna)
    layout.addWidget(widget, columna[1])


def real_text(resolution):
    """El texto de la columna 'Resolves to' para un resultado."""
    if resolution is None:
        return REAL_EMPTY
    if resolution.kind == paths.EMPTY:
        return REAL_EMPTY
    if resolution.kind == paths.INVALID:
        return REAL_INVALID
    if resolution.kind == paths.ABSOLUTE:
        return REAL_ABSOLUTE
    if not resolution.folders:
        return REAL_NOT_FOUND
    if len(resolution.folders) == 1:
        return os.path.basename(resolution.folders[0].rstrip("/")) or resolution.folders[0]
    return "%d folders" % len(resolution.folders)


def real_tooltip(resolution):
    """El detalle, que en la columna no entra."""
    if resolution is None or resolution.kind == paths.EMPTY:
        return TOOLTIPS["real_empty"]
    if resolution.kind == paths.INVALID:
        return TOOLTIPS["real_invalid"]
    if not resolution.folders:
        return TOOLTIPS["real_none"]
    if len(resolution.folders) == 1:
        return TOOLTIPS["real_one"] % resolution.folders[0]
    # La ruta COMPLETA de cada match y no solo el nombre: con dos carpetas
    # homonimas en ramas distintas, el nombre solo no las diferencia.
    detalle = "\n".join(resolution.folders[:12])
    if len(resolution.folders) > 12:
        detalle += "\n..."
    return TOOLTIPS["real_many"] + "\n" + detalle


def real_is_problem(resolution):
    """Si el resultado hay que mostrarlo en rojo."""
    if resolution is None:
        return False
    return resolution.kind == paths.INVALID or (
        resolution.kind in (paths.RELATIVE, paths.ABSOLUTE) and not resolution.folders
    )


class GripLabel(QLabel):
    """
    El agarre para arrastrar una fila.

    El arrastre se maneja aca y no con el drag&drop de Qt: la lista es un
    QVBoxLayout de widgets propios, asi que mover una fila es moverla de
    posicion en el layout, y armar un QDrag para eso es dar toda la vuelta.
    """

    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.setCursor(Qt.OpenHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.setToolTip(TOOLTIPS["grip"])
        self._activo = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._activo = True
            self.setCursor(Qt.ClosedHandCursor)
            self.row.drag_started.emit(self.row)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._activo:
            # La posicion global, porque el cursor se va del propio grip en
            # cuanto la fila se mueve.
            self.row.drag_moved.emit(self.row, self._global_y(event))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._activo:
            self._activo = False
            self.setCursor(Qt.OpenHandCursor)
            self.row.drag_finished.emit(self.row)
        super().mouseReleaseEvent(event)

    def _global_y(self, event):
        # Qt5 tiene globalY(); Qt6 lo saco a favor de globalPosition().
        try:
            return int(event.globalPosition().y())
        except AttributeError:
            return event.globalY()


class TrashButton(QPushButton):
    """
    La papelera de una fila.

    El icono cambia de color al pasar por encima, y eso no se puede pedir por
    QSS: el color de un QIcon no lo hereda el widget, hay que rearmar el SVG
    con el hex nuevo. Por eso el hover se atiende aca y no en la hoja.
    """

    def __init__(self, parent=None):
        super().__init__("", parent)
        self._icono = None
        self._icono_hover = None

    def set_icons(self, normal, hover):
        self._icono = normal
        self._icono_hover = hover
        self.setIcon(normal)

    def enterEvent(self, event):
        if self._icono_hover is not None:
            self.setIcon(self._icono_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._icono is not None:
            self.setIcon(self._icono)
        super().leaveEvent(event)


class ShortcutField(QLineEdit):
    """Un solo caracter, en mayuscula, y solo letra o numero."""

    def __init__(self, letra, parent=None):
        super().__init__(letra or "", parent)
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignCenter)
        # Alto propio, igual que la pastilla "Alt" de al lado: sin fijarlo el
        # campo se estira a todo el alto de la fila y los dos dejan de leerse
        # como un par de teclas.
        self.setFixedSize(KEY_MIN_WIDTH, KEY_HEIGHT)
        self.textChanged.connect(self._limpiar)

    def _limpiar(self, texto):
        limpio = re.sub(r"[^A-Za-z0-9]", "", texto).upper()
        if limpio != texto:
            self.blockSignals(True)
            self.setText(limpio)
            self.blockSignals(False)


class LocationRow(QFrame):
    """
    Una fila de la tabla: nombre, ruta, a que resuelve, Scan, Copy to, atajo.

    Es un QFrame y no un QWidget pelado a proposito: la fila tiene fondo,
    separador y linea de destino propios, y un QWidget comun ignora el
    background y el border del QSS salvo que se le escriba un paintEvent.

    La fila del shot folder es la misma clase en modo `shot`: comparte grilla,
    alto y fondo con las demas para que se lean como lo mismo, y se diferencia
    por lo que NO tiene -grip, Copy to, atajo y papelera- y porque su etiqueta
    va en bold.
    """

    changed = Signal()
    # Cualquier tecla, sin recalcular nada. Lo escucha solo el estado de
    # Cancel y Save: el resto de la fila se recalcula recien al soltar el
    # campo, que es lo que evita tocar disco por tecla.
    edited = Signal()
    path_changed = Signal(object)
    remove_requested = Signal(object)
    drag_started = Signal(object)
    drag_moved = Signal(object, int)
    drag_finished = Signal(object)

    # Un numero propio y creciente por fila. No se usa id(): CPython reusa el
    # id de un objeto liberado, asi que una fila nueva podia recibir el
    # "Resolves to" de la que el usuario acababa de borrar.
    _next_uid = 0

    def __init__(self, data, shot=False, parent=None):
        super().__init__(parent)
        # El fondo, el separador y la linea de destino se pintan por QSS con
        # este id: el selector tiene que ganarle al QWidget generico que la
        # caja de la tabla usa para dejar transparentes a todos sus hijos.
        self.setObjectName("lgaRow")
        # Sin esto el QSS NO pinta ni fondo ni borde. Qt solo dibuja el fondo
        # de la hoja cuando el widget tiene WA_StyledBackground, y a una
        # subclase propia no se lo pone solo: el separador entre filas y el
        # hover quedaban escritos en la hoja y sin dibujarse nunca.
        self.setAttribute(Qt.WA_StyledBackground, True)
        # El marco lo dibuja el QSS, no el estilo nativo.
        self.setFrameShape(QFrame.NoFrame)
        LocationRow._next_uid += 1
        self.uid = LocationRow._next_uid
        self.shot = shot
        self.data = dict(data)
        self._resolution = None
        self._small_css = ""
        # El tema con el que se pinto la fila, para poder repintar el fondo
        # y el separador sin volver a pasar por apply_theme entera.
        self._UI = None
        # La ultima fila no lleva separador: abajo ya esta el borde de la caja.
        self._is_last = False
        # La fila sobre la que va a caer la que se esta arrastrando.
        self._drop_target = False
        # Los campos con un problema de validacion, para pintarlos de rojo.
        self.field_errors = set()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(COLUMN_SPACING)

        # --- primera columna: grip, o el encendido del shot ----------------
        if shot:
            # El checkbox va en la columna del NOMBRE, donde las otras filas
            # tienen el icono de carpeta, no aca: asi la primera cosa
            # clickeable de cada fila cae siempre en la misma vertical.
            hueco = QLabel("")
            _add_column(layout, hueco, COL_GRIP)
            self.grip = None
        else:
            self.grip = GripLabel(self)
            _add_column(layout, self.grip, COL_GRIP)

        # --- nombre --------------------------------------------------------
        nombre_caja = QWidget(self)
        nombre_layout = QHBoxLayout(nombre_caja)
        nombre_layout.setContentsMargins(0, 0, 0, 0)
        nombre_layout.setSpacing(RANURA_GAP)

        # La ranura mide 18 y no 17: es lo que necesita el indicador del
        # checkbox del shot -16 de cuadro mas 1 de borde por lado- para no
        # quedar recortado. Qt acota un item alineado al ancho de su celda, asi
        # que con 17 se dibujaban 15 de los 18 px. Con 18, el icono de carpeta
        # de las otras filas (17) y el indicador quedan los dos centrados en 9,
        # y el gap baja a 8 para que RANURA_WIDTH + RANURA_GAP siga siendo 26 y
        # "Shot folder" arranque donde arrancan los nombres.
        if shot:
            self.enabled_check = QCheckBox("")
            self.enabled_check.setChecked(bool(self.data.get("enabled", True)))
            self.enabled_check.setToolTip(TOOLTIPS["shot_enabled"])
            self.enabled_check.stateChanged.connect(self._shot_toggled)
            self.ranura = self.enabled_check
            self.name_edit = None
            self.name_label = QLabel("Shot folder")
        else:
            self.enabled_check = None
            self.ranura = QLabel("")
            self.name_label = None
            self.name_edit = QLineEdit(self.data.get("name", ""))
            self.name_edit.setPlaceholderText("Name")
            self.name_edit.setToolTip(TOOLTIPS["name"])
            self.name_edit.textChanged.connect(lambda _t: self.changed.emit())

        if shot:
            # El checkbox va SIN el padding de la hoja comun: con el pide 22 px
            # y la celda le da 18, y Qt acota el item alineado al ancho de la
            # celda, asi que le recortaba el indicador. Sin padding pide 18
            # justos. La regla va por id para que le gane a Style.CHECKBOX.
            self.enabled_check.setObjectName("lgaShotCheck")
            ranura_caja = QWidget(self)
            ranura_layout = QHBoxLayout(ranura_caja)
            ranura_layout.setContentsMargins(0, 0, 0, 0)
            ranura_layout.addWidget(self.ranura, 0, Qt.AlignCenter)
            ranura_caja.setFixedWidth(RANURA_WIDTH)
            nombre_layout.addWidget(ranura_caja)
        else:
            self.ranura.setFixedWidth(RANURA_WIDTH)
            nombre_layout.addWidget(self.ranura)
        nombre_layout.addWidget(self.name_label or self.name_edit, 1)

        _add_column(layout, nombre_caja, COL_NAME)

        # --- ruta ----------------------------------------------------------
        self.path_edit = QLineEdit(self.data.get("path", ""))
        self.path_edit.setPlaceholderText("../*folder*")
        self.path_edit.setToolTip(
            TOOLTIPS["shot_path"] if shot else TOOLTIPS["path"]
        )
        # editingFinished y NO textChanged: resolver la ruta contra disco toca
        # IO, y recalcular las inclusiones en cada tecla ademas redibuja la
        # fila mientras se escribe y el foco salta.
        self.path_edit.editingFinished.connect(lambda: self.path_changed.emit(self))
        # El aviso liviano SI va por tecla. Sin el, escribir una ruta y hacer
        # click directo en Save no guardaba nada: Save estaba deshabilitado, un
        # widget deshabilitado no acepta el click ni el foco, asi que
        # editingFinished no llegaba a dispararse nunca y el boton no se
        # encendia.
        self.path_edit.textChanged.connect(lambda _t: self.edited.emit())
        _add_column(layout, self.path_edit, COL_PATH)

        # --- a que resuelve -------------------------------------------------
        self.real_label = QLabel(REAL_EMPTY)
        self.real_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        _add_column(layout, self.real_label, COL_REAL)

        # --- Scan ------------------------------------------------------------
        scan_caja = QWidget(self)
        scan_layout = QHBoxLayout(scan_caja)
        scan_layout.setContentsMargins(0, 0, 0, 0)
        self.scan_check = QCheckBox("")
        if shot:
            # No es una location que se prenda aparte: el shot se escanea
            # siempre que este activo, y se apaga con la fila.
            self.scan_check.setChecked(True)
            self.scan_check.setEnabled(False)
        else:
            self.scan_check.setChecked(bool(self.data.get("scan", True)))
            self.scan_check.setToolTip(TOOLTIPS["scan"])
            self.scan_check.stateChanged.connect(self._scan_toggled)
        scan_layout.addWidget(self.scan_check, 0, Qt.AlignCenter)
        _add_column(layout, scan_caja, COL_SCAN)

        # --- Copy to ---------------------------------------------------------
        copy_caja = QWidget(self)
        copy_layout = QHBoxLayout(copy_caja)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        if shot:
            self.copy_check = None
            copy_layout.addWidget(QLabel(""))
        else:
            self.copy_check = QCheckBox("")
            self.copy_check.setChecked(bool(self.data.get("copy_to", False)))
            self.copy_check.setToolTip(TOOLTIPS["copy_to"])
            self.copy_check.stateChanged.connect(self._copy_toggled)
            copy_layout.addWidget(self.copy_check, 0, Qt.AlignCenter)
        _add_column(layout, copy_caja, COL_COPY)

        # --- atajo ------------------------------------------------------------
        key_caja = QWidget(self)
        key_layout = QHBoxLayout(key_caja)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(6)
        if shot:
            self.alt_label = None
            self.plus_label = None
            self.key_edit = None
            self.dash_label = None
            key_layout.addWidget(QLabel(""))
        else:
            self.alt_label = QLabel("Alt")
            self.alt_label.setProperty("lgaKey", True)
            # Alto y ancho minimo propios: un QLabel adentro de un QHBoxLayout
            # se estira a todo el alto de la fila, y la pastilla quedaba de 44
            # px de alto en vez de 28, o sea una columna violeta y no una tecla.
            self.alt_label.setFixedHeight(KEY_HEIGHT)
            self.alt_label.setMinimumWidth(KEY_MIN_WIDTH)
            self.alt_label.setAlignment(Qt.AlignCenter)
            self.plus_label = QLabel("+")
            self.key_edit = ShortcutField(self.data.get("shortcut", ""))
            self.key_edit.setToolTip(TOOLTIPS["shortcut"])
            self.key_edit.textChanged.connect(lambda _t: self.changed.emit())
            self.dash_label = QLabel("—")
            # Centrado, con aire de los dos lados. Con un solo stretch al final
            # el par de teclas se pegaba a la izquierda de su columna y todo el
            # sobrante caia junto del lado de la papelera, que era lo que las
            # dejaba tan separadas.
            key_layout.addStretch()
            key_layout.addWidget(self.alt_label, 0, Qt.AlignVCenter)
            key_layout.addWidget(self.plus_label, 0, Qt.AlignVCenter)
            key_layout.addWidget(self.key_edit, 0, Qt.AlignVCenter)
            key_layout.addWidget(self.dash_label, 0, Qt.AlignVCenter)
            key_layout.addStretch()
        _add_column(layout, key_caja, COL_KEY)

        # --- papelera ----------------------------------------------------------
        trash_caja = QWidget(self)
        trash_layout = QHBoxLayout(trash_caja)
        trash_layout.setContentsMargins(0, 0, 0, 0)
        if shot:
            self.trash_button = None
            trash_layout.addWidget(QLabel(""))
        else:
            self.trash_button = TrashButton(self)
            self.trash_button.setFixedSize(30, 30)
            self.trash_button.setToolTip(TOOLTIPS["remove"])
            self.trash_button.setFocusPolicy(Qt.NoFocus)
            self.trash_button.clicked.connect(
                lambda: self.remove_requested.emit(self)
            )
            trash_layout.addWidget(self.trash_button, 0, Qt.AlignCenter)
        _add_column(layout, trash_caja, COL_TRASH)

        if shot:
            self._shot_toggled()
        else:
            self._copy_toggled()

    # ------------------------------------------------------------- estado ---
    def _shot_toggled(self, *_):
        prendido = self.enabled_check.isChecked()
        self.path_edit.setEnabled(prendido)
        self.scan_check.setChecked(prendido)
        # Nombre, ruta y carpeta resuelta bajan de intensidad. La carpeta
        # resuelta NO se borra: apagada sigue diciendo a que apuntaba, que es
        # lo que hace falta para decidir si volver a prenderla.
        for widget in (self.name_label, self.path_edit, self.real_label):
            if widget is not None:
                efecto = QtWidgets.QGraphicsOpacityEffect(widget)
                efecto.setOpacity(1.0 if prendido else 0.45)
                widget.setGraphicsEffect(efecto)
        # La carpeta resuelta NO se borra al apagar: apagada sigue diciendo a
        # que apuntaba, que es lo que hace falta para decidir si reactivarla.
        self.changed.emit()

    def _scan_toggled(self, *_):
        self.data["scan"] = self.scan_check.isChecked()
        self.changed.emit()

    def _copy_toggled(self, *_):
        prendido = bool(self.copy_check and self.copy_check.isChecked())
        # La letra NO se borra del modelo al apagar Copy to: si el usuario lo
        # vuelve a prender, vuelve su letra.
        for widget in (self.alt_label, self.plus_label, self.key_edit):
            if widget is not None:
                widget.setVisible(prendido)
        if self.dash_label is not None:
            self.dash_label.setVisible(not prendido)
        self.changed.emit()

    def set_scan_inherited(self, padre):
        """
        La cubre otra location que ya se escanea entera.

        Queda TILDADA y deshabilitada, no destildada: la carpeta se escanea,
        solo que no es esta fila la que lo decide.
        """
        if self.shot:
            return
        if padre is None:
            self.scan_check.setEnabled(True)
            self.scan_check.blockSignals(True)
            self.scan_check.setChecked(bool(self.data.get("scan", True)))
            self.scan_check.blockSignals(False)
            self.scan_check.setToolTip(TOOLTIPS["scan"])
            return
        self.scan_check.blockSignals(True)
        self.scan_check.setChecked(True)
        self.scan_check.blockSignals(False)
        self.scan_check.setEnabled(False)
        nombre = padre.get("name") or padre.get("path") or ""
        self.scan_check.setToolTip("%s\n(%s)" % (TOOLTIPS["scan_inherited"], nombre))

    def set_resolution(self, resolution, UI):
        self._resolution = resolution
        # La flecha va SIEMPRE y apagada: es lo que hace leer la celda como
        # "esta ruta llega aca" y no como una segunda columna de texto suelto.
        # El nombre cambia de color segun el resultado: normal si resuelve a
        # una, fuerte si resuelve a varias -es un dato que hay que mirar- y
        # rojo si no resuelve a ninguna o la ruta es invalida.
        if real_is_problem(resolution):
            color = UI.Color.DOT_ERROR
        elif resolution is not None and len(resolution.folders) > 1:
            color = UI.Color.TEXT_STRONG
        else:
            color = UI.Color.TEXT
        self.real_label.setText(
            '<span style="color:%s;">&rarr;</span>&nbsp;'
            '<span style="color:%s;">%s</span>'
            % (UI.Color.TEXT_DIM, color,
               real_text(resolution).replace("&", "&amp;").replace("<", "&lt;"))
        )
        self.real_label.setToolTip(real_tooltip(resolution))
        self.real_label.setStyleSheet(
            "background: transparent; %s" % self._small_css
        )

    def resolution(self):
        return self._resolution

    def set_field_errors(self, campos, UI, font_size):
        """Los campos que hay que pintar de rojo. Repinta solo si cambiaron."""
        campos = set(campos)
        if campos == self.field_errors:
            return
        self.field_errors = campos
        self.apply_theme(UI, font_size)

    # ------------------------------------------------------- estado visual ---
    def set_last(self, es_ultima):
        """La ultima fila no lleva separador: abajo ya esta el borde de la caja."""
        if es_ultima == self._is_last:
            return
        self._is_last = es_ultima
        self._apply_row_sheet()

    def set_drop_target(self, es_destino):
        """
        Marca el borde por el que va a entrar la fila que se arrastra.

        La linea se dibuja abajo de la fila de ARRIBA del hueco y no arriba de
        la que se mueve, que es donde la pone el prototipo: la que se mueve va
        atenuada al 35% y sobre ella la linea de acento tambien se atenuaba y
        no se veia. Son los mismos pixeles, en el mismo borde.
        """
        if es_destino == self._drop_target:
            return
        self._drop_target = es_destino
        self._apply_row_sheet()

    def set_dragging(self, arrastrando):
        """Atenua la fila mientras se la arrastra."""
        if not arrastrando:
            self.setGraphicsEffect(None)
            return
        efecto = QtWidgets.QGraphicsOpacityEffect(self)
        efecto.setOpacity(DRAG_OPACITY)
        self.setGraphicsEffect(efecto)

    def _apply_row_sheet(self):
        """La hoja de la fila: fondo, hover, separador y linea de destino."""
        UI = self._UI
        if UI is None:
            return
        if self._drop_target:
            borde = "border-bottom: %dpx solid %s;" % (
                DROP_LINE_WIDTH, UI.Color.ACCENT_HOVER
            )
        elif self._is_last:
            borde = "border-bottom: none;"
        else:
            borde = "border-bottom: 1px solid %s;" % UI.Color.BORDER
        # El campo inline va sin caja hasta que se lo toca: en reposo es texto
        # sobre la fila, y la caja aparece al hover y al foco. Con la hoja
        # generica de formulario cada fila mostraba cinco cajas grises.
        self.setStyleSheet(
            (
                "#lgaRow { background-color: transparent; border: none; %(borde)s }"
                "#lgaRow:hover { background-color: %(hover)s; }"
                "QWidget { background-color: transparent; }"
                "QLabel { background: transparent; color: %(text)s; }"
                "QLineEdit {"
                " background: transparent; border: 1px solid transparent;"
                " border-radius: %(radius)dpx; padding: 6px 8px;"
                " color: %(text_strong)s;"
                " selection-background-color: %(accent)s; }"
                "QLineEdit:hover {"
                " border-color: %(border_strong)s; background-color: %(field)s; }"
                "QLineEdit:focus {"
                " border-color: %(accent_hover)s; background-color: %(field)s; }"
                "QLineEdit:disabled { color: %(text_dim)s; }"
                % {
                    "borde": borde,
                    "hover": UI.Color.ROW_LINE,
                    "text": UI.Color.TEXT,
                    "text_strong": UI.Color.TEXT_STRONG,
                    "text_dim": UI.Color.TEXT_DIM,
                    "border_strong": UI.Color.BORDER_STRONG,
                    "accent": UI.Color.ACCENT,
                    "accent_hover": UI.Color.ACCENT_HOVER,
                    "field": UI.Color.FIELD_BG,
                    "radius": UIStyle.Metric.RADIUS_FIELD,
                }
            )
            + UI.Style.CHECKBOX
            # El checkbox del shot va sin el padding de la hoja comun: con el
            # pide 22 px y su celda mide 18, y Qt acota al ancho de la celda un
            # item alineado, asi que le recortaba 3 px del indicador. Va por id
            # para ganarle a la regla generica de arriba.
            + "#lgaShotCheck { padding: 0px; }"
        )

    # -------------------------------------------------------------- datos ---
    def path(self):
        return self.path_edit.text().strip()

    def to_dict(self):
        if self.shot:
            return {
                "enabled": self.enabled_check.isChecked(),
                "path": self.path() or DEFAULT_SHOT["path"],
            }
        return {
            "name": self.name_edit.text().strip(),
            "path": self.path(),
            # Se guarda SIEMPRE el scan explicito, nunca el efectivo: si se
            # guardara el efectivo, al borrar la location padre las hijas
            # quedarian tildadas de una forma que el usuario nunca eligio.
            "scan": bool(self.data.get("scan", self.scan_check.isChecked())),
            "copy_to": bool(self.copy_check.isChecked()),
            "shortcut": self.key_edit.text().strip().upper(),
        }

    # -------------------------------------------------------------- estilo ---
    def apply_theme(self, UI, font_size):
        self._UI = UI
        alto = font_size + ROW_EXTRA
        self.setFixedHeight(alto)
        self._apply_row_sheet()

        # El path va un punto mas grande que el resto de la tabla, y con menos
        # padding vertical: la mono ya trae una caja de linea mas alta.
        self.path_edit.setStyleSheet(
            "QLineEdit { color: %s; font-family: '%s'; font-size: %dpx;"
            " padding: 4px 8px; }"
            % (UI.Color.PATH_FIELD, UIStyle.mono_family() or UIStyle.font_family(),
               font_size + UIStyle.Metric.PATH_FONT_OFFSET)
        )
        chico = "font-size: %dpx;" % max(9, int(round(font_size - 0.5)))
        self._small_css = chico
        self.set_resolution(self._resolution, UI)
        if self.name_edit is not None:
            self.name_edit.setStyleSheet("QLineEdit { %s }" % chico)
        if self.name_label is not None:
            # El mismo padding que el campo de nombre de las filas de abajo,
            # para que "Shot folder" arranque en la misma vertical.
            self.name_label.setStyleSheet(
                "color: %s; %s padding-left: %dpx; %s"
                % (UI.Color.TEXT_STRONG, UIStyle.semibold_css(),
                   FIELD_BORDER + FIELD_PADDING_H, chico)
            )
        if self.grip is not None:
            # El grip va en el gris de borde y no en el del texto: es un
            # agarre, no contenido de la fila.
            self.grip.setPixmap(
                tinted_icon("grip-vertical", UI.Color.BORDER_HOVER, 18).pixmap(18, 18)
            )
        if self.ranura is not None and not self.shot:
            self.ranura.setPixmap(
                tinted_icon("folder", UI.Color.TEXT_DIM, 17).pixmap(17, 17)
            )
        if self.trash_button is not None:
            # En reposo el icono va apagado; al pasar por encima se enciende
            # en rojo sobre su propio fondo. El color del icono no lo puede
            # dar el QSS, asi que van los dos armados de antemano.
            self.trash_button.set_icons(
                tinted_icon("trash-2", UI.Color.TEXT_DIM, 17),
                tinted_icon("trash-2", UI.Color.DANGER_ICON_HOVER, 17),
            )
            # Sin caja hasta el hover: con el boton de icono comun, cada fila
            # mostraba un recuadro gris apoyado sobre el fondo de la tabla.
            self.trash_button.setStyleSheet(
                "QPushButton { background-color: transparent;"
                " border: 1px solid transparent; border-radius: %dpx; }"
                "QPushButton:hover { background-color: %s; }"
                % (UIStyle.Metric.RADIUS_FIELD, UI.Color.DANGER_BG_HOVER)
            )
        if self.alt_label is not None:
            self.alt_label.setStyleSheet(
                "background-color: %s; border: 1px solid %s; border-radius: %dpx;"
                " padding: 0 9px; color: %s; %s font-size: %dpx;"
                % (UI.Color.SURFACE_RAISED, UI.Color.BORDER_STRONG,
                   UIStyle.Metric.RADIUS_FIELD, UI.Color.TEXT_STRONG,
                   UIStyle.semibold_css(), KEY_FONT)
            )
            self.plus_label.setStyleSheet(
                "color: %s; font-size: %dpx;" % (UI.Color.TEXT_DIM, KEY_FONT)
            )
            # Sin padding: el guion vive entre los dos stretch de su columna,
            # asi que ya cae centrado. Los 12 px que tenia lo corrian 6,5 a la
            # derecha del centro, o sea que prender Copy to movia el marcador.
            self.dash_label.setStyleSheet("color: %s;" % UI.Color.TEXT_DIM)
        if self.key_edit is not None:
            # Borde de acento SIEMPRE y no solo al foco: es el unico campo de
            # la fila que espera una sola tecla, y sin marcarlo no se ve que
            # sea editable.
            self.key_edit.setStyleSheet(
                "QLineEdit { border: 1px solid %s; border-radius: %dpx;"
                " background-color: %s; color: %s; padding: 0px;"
                " font-size: %dpx; %s }"
                "QLineEdit:hover { border-color: %s; }"
                "QLineEdit:focus { background-color: %s; }"
                % (UI.Color.ACCENT_HOVER, UIStyle.Metric.RADIUS_FIELD,
                   UI.Color.SURFACE_RAISED, UI.Color.TEXT_STRONG, KEY_FONT,
                   UIStyle.semibold_css(),
                   UI.Color.ACCENT_HOVER, UI.Color.ACCENT)
            )

        # El rojo va al final para que le gane a la hoja del campo, que ya
        # quedo escrita arriba. Se reconstruye entero en cada pasada, asi que
        # sacar el error tambien saca el borde.
        for campo in self.field_errors:
            widget = {"name": self.name_edit, "path": self.path_edit,
                      "shortcut": self.key_edit}.get(campo)
            if widget is not None:
                widget.setStyleSheet(
                    widget.styleSheet()
                    + " QLineEdit { border: 1px solid %s; }" % UI.Color.ERROR_TEXT
                )


class FontSizeField(QLineEdit):
    """
    El campo del stepper del tamano de letra.

    Es un QLineEdit y no un QSpinBox por lo mismo que ya estaba resuelto en la
    version anterior: el spinbox nativo mide 20 px contra los 30 de un campo,
    asi que sus flechas quedan de 7 px, y al enfocarlo macOS lo pinta con su
    anillo amarillo mientras el resto del pack se pone violeta.
    """

    value_changed = Signal(int)

    def __init__(self, valor, parent=None):
        super().__init__(str(valor), parent)
        self.setValidator(
            QtGui.QIntValidator(UIStyle.Metric.TABLE_FONT_SIZE_MIN,
                                UIStyle.Metric.TABLE_FONT_SIZE_MAX, self)
        )
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(56)
        self.editingFinished.connect(self._commit)

    def _commit(self):
        # El texto se reescribe con el valor ACOTADO: sin esto el campo
        # quedaba en 200 mientras se aplicaba y se guardaba 20.
        acotado = self.value()
        if self.text() != str(acotado):
            self.setText(str(acotado))
        self.value_changed.emit(acotado)

    def value(self):
        # Se acota aca y no solo en step(): QIntValidator da por intermedio
        # cualquier numero mas corto que el minimo, asi que deja tipear un 0.
        try:
            escrito = int(self.text())
        except ValueError:
            return UIStyle.Metric.TABLE_FONT_SIZE
        return max(UIStyle.Metric.TABLE_FONT_SIZE_MIN,
                   min(UIStyle.Metric.TABLE_FONT_SIZE_MAX, escrito))

    def step(self, delta):
        nuevo = max(UIStyle.Metric.TABLE_FONT_SIZE_MIN,
                    min(UIStyle.Metric.TABLE_FONT_SIZE_MAX, self.value() + delta))
        self.setText(str(nuevo))
        self.value_changed.emit(nuevo)

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


class SettingsWindow(QWidget):
    """La ventana de ajustes del Media Manager."""

    # Al guardar, para que la ventana principal relea el .ini y rehaga el
    # menu Copy to: sin esto, una location agregada aca no aparece hasta
    # reabrir la herramienta.
    settings_saved = Signal()
    # Tema y tamano de letra mientras la ventana esta abierta, para poder
    # verlos sobre la tabla de atras. Cancel manda los guardados de vuelta.
    appearance_previewed = Signal(object)

    def __init__(self, settings, nk_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Media Manager Settings")
        # Sin esto Qt resuelve la hoja de la ventana y no pinta su fondo: la
        # ventana arranca con el color que le toque del host y, peor, cambiar
        # de tema no repinta nada. Es la misma trampa que dejaba la tabla sin
        # caja.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        # Sin minimo de ancho propio: el que vale es el que calcula el layout
        # con los minimos de cada columna. Escrito a mano quedaba mas ancho que
        # lo que el contenido necesita, o sea que la ventana no se podia
        # achicar hasta donde la tabla lo permitia.
        self.setMinimumHeight(WINDOW_MIN_HEIGHT)

        self.nk_dir = nk_dir or ""
        self.settings = settings or {}
        self.load_error = self.settings.get("load_error") or ""
        # La apariencia guardada, para poder revertir con Cancel.
        self.saved_appearance = dict(
            self.settings.get("appearance") or DEFAULT_APPEARANCE
        )
        self.appearance = dict(self.saved_appearance)
        self.UI = UIStyle.theme(self.appearance.get("theme"))

        self.rows = []
        self._worker = None
        self._dragging = None
        self._resolve_timer = QTimer(self)
        self._resolve_timer.setSingleShot(True)
        self._resolve_timer.setInterval(150)
        self._resolve_timer.timeout.connect(self._resolve_now)

        # La fuente del pack va ANTES de armar. Dos razones: sin ella el
        # `font-weight` de las hojas no encuentra una cara real y macOS
        # sintetiza la negrita -todo lo que el disenio pide en 600 sale con el
        # peso de una 700 falsa-, y ademas lo que se mide al armar hay que
        # medirlo con la fuente definitiva. Qt la propaga a los hijos que se
        # creen despues.
        UIStyle.apply_ui_font(self)
        self._build()
        self._load_rows()
        # El punto de comparacion de Cancel y Save. Se toma de las filas recien
        # cargadas y no del .ini: asi los dos lados de la comparacion salen del
        # mismo lugar y una normalizacion que la lectura haga -una ruta sin
        # espacios, un atajo en mayuscula- no cuenta como un cambio del usuario.
        self._baseline = self._editable_state()
        self.apply_appearance()
        self.refresh()

        # El alto sale de medir el contenido: con un tamano fijo, la tabla
        # abria cortada o sobraba media ventana vacia segun cuantas
        # locations tuviera el usuario.
        self.adjustSize()

        if self.load_error:
            # El .ini existe y no se pudo leer, asi que lo que se esta
            # mostrando son los valores de fabrica y NO la configuracion del
            # usuario. Guardar encima la destruye.
            QMessageBox.warning(
                self,
                "Media Manager",
                "The settings file could not be read, so these are the "
                "factory defaults and not your configuration.\n\n%s\n\n"
                "Saving now would overwrite your settings file."
                % self.load_error,
            )

    # --------------------------------------------------------------- armado --
    def _build(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(26, 20, 26, 22)
        raiz.setSpacing(0)

        # --- encabezado ------------------------------------------------------
        cabeza = QHBoxLayout()
        titulos = QVBoxLayout()
        self.title_label = QLabel("Scan locations")
        self.subtitle_label = QLabel(
            "Define which folders will be scanned for media.\n"
            "Paths are relative to the current .nk file unless absolute."
        )
        titulos.addWidget(self.title_label)
        titulos.addWidget(self.subtitle_label)
        cabeza.addLayout(titulos, 1)
        self.card_wildcard = self._info_card(
            "Wildcard * matches any folder name.\n"
            "Example: ../*assets* matches 0_assets, _assets, my_assets, etc."
        )
        cabeza.addWidget(self.card_wildcard)
        raiz.addLayout(cabeza)
        raiz.addSpacing(20)

        # --- la caja de la tabla ----------------------------------------------
        # La tabla es UN bloque: borde, esquinas redondeadas y la cabecera
        # adentro. Son QFrame y no QWidget porque un QWidget pelado ignora el
        # background y el border del QSS salvo que se le escriba un paintEvent.
        self.table_box = QFrame(self)
        self.table_box.setObjectName("lgaTableBox")
        # Qt solo dibuja el fondo y el borde de la hoja cuando el widget tiene
        # WA_StyledBackground. Sin el atributo, la regla #lgaTableBox se aplica
        # igual -y hasta gana en especificidad- pero no se pinta nunca: la
        # tabla quedaba sin caja, sin esquinas y con la cabecera del color del
        # cuerpo. El frame va en NoFrame para que el borde lo dibuje el QSS y
        # no el estilo nativo del host.
        self.table_box.setAttribute(Qt.WA_StyledBackground, True)
        self.table_box.setFrameShape(QFrame.NoFrame)
        caja = QVBoxLayout(self.table_box)
        # 1 px por lado para no taparle el borde a la caja con los hijos.
        caja.setContentsMargins(1, 1, 1, 1)
        caja.setSpacing(0)

        # --- encabezado de la tabla ------------------------------------------
        self.head_row = QFrame(self.table_box)
        self.head_row.setObjectName("lgaTableHead")
        self.head_row.setAttribute(Qt.WA_StyledBackground, True)
        self.head_row.setFrameShape(QFrame.NoFrame)
        self.head_layout = QHBoxLayout(self.head_row)
        # El margen derecho lo escribe _fit_table con el ancho de la barra de
        # scroll, para que el encabezado y las filas repartan lo mismo.
        self.head_layout.setContentsMargins(0, 0, 0, 0)
        self.head_layout.setSpacing(COLUMN_SPACING)
        head = self.head_layout
        self.head_labels = []
        for texto, columna, sangria in (
            ("", COL_GRIP, 0),
            ("Name", COL_NAME, HEAD_INDENT_NAME),
            ("Path", COL_PATH, HEAD_INDENT_PATH),
            ("Resolves to", COL_REAL, HEAD_INDENT_REAL),
            ("Scan", COL_SCAN, 0), ("Copy to", COL_COPY, 0),
            ("Copy Shortcut", COL_KEY, 0), ("", COL_TRASH, 0),
        ):
            etiqueta = QLabel(texto)
            # Las tres de la derecha van centradas, igual que su contenido.
            # "Copy Shortcut" quedaba pegado a la izquierda mientras el par de
            # teclas de abajo caia al medio, o sea que el titulo no señalaba
            # su propia columna.
            if columna in (COL_SCAN, COL_COPY, COL_KEY):
                etiqueta.setAlignment(Qt.AlignCenter)
            # Las tres de la izquierda se sangran lo mismo que su contenido.
            # El encabezado pone un label pelado y la fila pone widgets con
            # estructura -una ranura, el borde y el padding de un campo- asi
            # que sin esto "Name" arrancaba 35 px antes que los nombres y
            # "Path" 9 px antes que las rutas. Va por contentsMargins y no por
            # hoja de estilo para no tener que repetirle el color y el tamano
            # que ya le pone la regla del encabezado.
            elif sangria:
                etiqueta.setContentsMargins(sangria, 0, 0, 0)
            _add_column(head, etiqueta, columna)
            self.head_labels.append(etiqueta)
        # El encabezado vive AFUERA del area scrolleable, asi que cuando
        # aparece la barra vertical las columnas elasticas de las filas se
        # corren respecto de el y hay que reservarle ese ancho. Se reserva con
        # el MARGEN DERECHO de la fila y no con un widget de ancho cero al
        # final:
        #
        #   un QHBoxLayout pone su espaciado ENTRE items, sin mirar cuanto mide
        #   cada uno. Un noveno item de 0 px de ancho igual sumaba los 9 px de
        #   espaciado que van antes, o sea que el encabezado tenia 9 px menos
        #   para repartir entre sus columnas elasticas que las filas. Como las
        #   elasticas van primero, TODO lo que viene despues -Scan, Copy to,
        #   Copy Shortcut- quedaba corrido 9 px a la izquierda respecto de su
        #   propio contenido. Se veia como si los titulos no estuvieran
        #   centrados, y estaban: centrados en una columna corrida.
        #
        # Lo pone _fit_table, que es quien sabe si la barra esta o no.
        caja.addWidget(self.head_row)

        # --- filas -------------------------------------------------------------
        self.rows_host = QWidget(self)
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.addStretch()

        self.scroll = QScrollArea(self)
        self.scroll.setWidget(self.rows_host)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setMaximumHeight(TABLE_MAX_HEIGHT)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Solo cuando hace falta: con las filas de fabrica entran todas y una
        # barra vacia al costado de la tabla no existe en el disenio. La
        # alineacion la mantiene el hueco del encabezado, que se prende y se
        # apaga junto con la barra en _fit_table.
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # La reserva del encabezado se rehace cuando el VIEWPORT cambia de
        # tamano, que es exactamente cuando la barra aparece o se va. Deducirlo
        # de cuantas filas hay fallaba con la ventana achicada.
        self.scroll.viewport().installEventFilter(self)
        caja.addWidget(self.scroll)
        # El minimo de la caja reserva tambien el ancho de la barra de scroll.
        # Sin eso, con la ventana en su ancho minimo Y la barra visible, a las
        # filas les quedaban 8 px menos que a sus propias columnas y el ultimo
        # widget -la papelera- se comia esa diferencia. El encabezado, que vive
        # afuera del area scrolleable, no la sufria: otro desfasaje entre los
        # dos por el mismo motivo de siempre.
        self.table_box.setMinimumWidth(
            sum(col[2] for col in COLUMNS)
            + COLUMN_SPACING * (len(COLUMNS) - 1)
            + UIStyle.Metric.SCROLLBAR_WIDTH
            + 2  # el borde de la caja, 1 px por lado
        )
        raiz.addWidget(self.table_box)

        # --- agregar + tarjeta ---------------------------------------------------
        bajo = QHBoxLayout()
        bajo.setSpacing(18)
        self.add_button = QPushButton("  Add location")
        self.add_button.setFixedHeight(44)
        self.add_button.setToolTip(TOOLTIPS["add"])
        self.add_button.clicked.connect(self._add_empty_row)
        bajo.addWidget(self.add_button)
        self.card_included = self._info_card(
            "Locations included by another scan path remain checked but "
            "disabled.\nDisable or remove the parent path to edit them."
        )
        bajo.addWidget(self.card_included)
        bajo.addStretch()
        raiz.addSpacing(14)
        raiz.addLayout(bajo)

        # --- apariencia -----------------------------------------------------------
        raiz.addSpacing(20)
        self.appearance_sep = self._separator()
        raiz.addWidget(self.appearance_sep)
        raiz.addSpacing(16)

        apariencia = QHBoxLayout()
        apariencia.setSpacing(34)

        tema_caja = QHBoxLayout()
        tema_caja.setSpacing(10)
        self.theme_label = QLabel("Theme")
        tema_caja.addWidget(self.theme_label)
        self.theme_buttons = {}
        for theme_id in UIStyle.theme_ids():
            spec = UIStyle.get_theme(theme_id)
            boton = QPushButton(spec["label"])
            # Mas chato y con menos aire que un boton de accion: son seis en
            # fila y con el padding del boton normal la tira no entraba.
            boton.setFixedHeight(THEME_BUTTON_HEIGHT)
            boton.setToolTip(TOOLTIPS["theme"])
            boton.setFocusPolicy(Qt.NoFocus)
            boton.clicked.connect(lambda _c=False, t=theme_id: self._pick_theme(t))
            tema_caja.addWidget(boton)
            self.theme_buttons[theme_id] = boton
        apariencia.addLayout(tema_caja)

        fuente_caja = QHBoxLayout()
        fuente_caja.setSpacing(8)
        self.font_label = QLabel("Table font size")
        fuente_caja.addWidget(self.font_label)
        self.font_minus = QPushButton("-")
        self.font_plus = QPushButton("+")
        self.font_field = FontSizeField(
            self.appearance.get("table_font_size", UIStyle.Metric.TABLE_FONT_SIZE)
        )
        self.font_field.value_changed.connect(self._pick_font_size)
        for boton, delta, tip in ((self.font_minus, -1, "font_minus"),
                                  (self.font_plus, 1, "font_plus")):
            boton.setFixedSize(UIStyle.Metric.CLOSE_BUTTON_SIZE,
                               UIStyle.Metric.CLOSE_BUTTON_SIZE)
            boton.setFocusPolicy(Qt.NoFocus)
            boton.setToolTip(TOOLTIPS[tip])
            boton.clicked.connect(lambda _c=False, d=delta: self.font_field.step(d))
        fuente_caja.addWidget(self.font_minus)
        fuente_caja.addWidget(self.font_field)
        fuente_caja.addWidget(self.font_plus)
        # El aire va ENTRE los dos grupos y no despues, asi "Table font size"
        # queda pegado a su stepper -son una sola cosa- y separado de la tira
        # de temas. Antes el hueco caia justo al medio del grupo de la fuente:
        # `addStretch()` sin argumento agrega un espaciador de factor CERO, que
        # no se lleva el sobrante, asi que se lo repartia lo unico elastico que
        # quedaba, que era el propio QLabel de la etiqueta.
        apariencia.addStretch(1)
        apariencia.addLayout(fuente_caja)
        raiz.addLayout(apariencia)

        # --- pie ------------------------------------------------------------------
        raiz.addSpacing(20)
        self.footer_sep = self._separator()
        raiz.addWidget(self.footer_sep)
        raiz.addSpacing(16)

        pie = QHBoxLayout()
        # Los dos botones de accion van separados, no pegados: sin espaciado
        # propio el layout usa el del host -que en macOS es 0- y Cancel y Save
        # quedaban compartiendo el borde, leyendose como un solo control
        # partido al medio. El stretch de antes se come el resto.
        pie.setSpacing(FOOTER_BUTTON_GAP)
        version = get_tool_version()
        self.version_label = QLabel(
            "Media Manager v%s  ·  Developed by Lega" % version
            if version
            else "Media Manager  ·  Developed by Lega"
        )
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.clicked.connect(self._cancel)
        self.save_button = QPushButton("Save Settings")
        self.save_button.setFixedHeight(40)
        self.save_button.clicked.connect(self.save)
        pie.addWidget(self.version_label)
        pie.addStretch()
        pie.addWidget(self.cancel_button)
        pie.addWidget(self.save_button)
        raiz.addLayout(pie)

    def _separator(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        return linea

    def _info_card(self, texto):
        """
        Una tarjeta de ayuda: icono a la izquierda y el texto al lado.

        El ancho lo decide el RENGLON MAS LARGO del texto, medido. El texto ya
        trae escritos sus propios saltos de linea, asi que una tarjeta mas
        angosta que su renglon mas largo lo parte al medio y aparece un renglon
        que nadie escribio. Con un ancho a ojo eso vuelve cada vez que cambia
        el texto o la fuente, y volvio: 360 se quedaba corto por 10 px.
        """
        tarjeta = QWidget(self)
        layout = QHBoxLayout(tarjeta)
        layout.setContentsMargins(CARD_PADDING, 13, CARD_PADDING, 13)
        layout.setSpacing(CARD_ICON_GAP)
        icono = QLabel("")
        icono.setFixedSize(CARD_ICON_SIZE, CARD_ICON_SIZE)
        icono.setProperty("lgaCardIcon", True)
        cuerpo = QLabel(texto)
        cuerpo.setWordWrap(True)
        # La fuente definitiva se le pone ACA, al QFont, y no por hoja de
        # estilo: el ancho de la tarjeta se decide preguntandole a este label
        # como envuelve, asi que tiene que estar ya con la letra con la que se
        # va a dibujar. Por eso la hoja de la tarjeta no declara font-size.
        cuerpo.setFont(_card_font(cuerpo.font()))
        layout.addWidget(icono, 0, Qt.AlignTop)
        layout.addWidget(cuerpo, 1)
        tarjeta.setFixedWidth(self._card_width(texto, cuerpo))
        tarjeta.icono = icono
        tarjeta.cuerpo = cuerpo
        return tarjeta

    @staticmethod
    def _card_width(texto, cuerpo):
        """
        El ancho mas chico con el que la tarjeta NO parte ningun renglon.

        No se calcula con QFontMetrics: se le PREGUNTA AL PROPIO LABEL, con
        heightForWidth(), y se agranda hasta que el alto que pide entra en la
        cantidad de renglones que el texto declara. Medir el ancho del texto a
        mano y confiar en que Qt va a envolverlo igual ya fallo dos veces -una
        por medir con otra fuente, otra por un par de pixeles de redondeo-, y
        el sintoma siempre es el mismo: un renglon de mas. El que envuelve es
        Qt, asi que el que tiene que decidir es Qt.

        El label ya tiene puesta su fuente definitiva cuando esto corre: se la
        pone _info_card antes de llamar.
        """
        renglones = texto.count("\n") + 1
        metrica = QtGui.QFontMetrics(cuerpo.font())
        # Medio renglon de tolerancia, para no depender del redondeo del alto.
        alto_maximo = metrica.lineSpacing() * (renglones + 0.5)
        chrome = CARD_PADDING * 2 + CARD_ICON_SIZE + CARD_ICON_GAP

        ancho = CARD_MIN_WIDTH
        while ancho < CARD_MAX_WIDTH:
            if cuerpo.heightForWidth(ancho - chrome) <= alto_maximo:
                return ancho
            ancho += CARD_WIDTH_STEP
        # Ni al maximo entra: mejor una tarjeta ancha que una ventana que no
        # entra en la pantalla. Envuelve, pero no se lleva puesta la ventana.
        return CARD_MAX_WIDTH

    # ---------------------------------------------------------------- filas --
    def _load_rows(self):
        shot = dict(self.settings.get("shot") or DEFAULT_SHOT)
        self.shot_row = LocationRow(shot, shot=True, parent=self.rows_host)
        self.shot_row.changed.connect(self.refresh)
        self.shot_row.edited.connect(self._update_actions_enabled)
        self.shot_row.path_changed.connect(self._path_edited)
        self.rows_layout.insertWidget(0, self.shot_row)

        for location in self.settings.get("locations") or ():
            self._add_row(location)

    def _add_row(self, location):
        fila = LocationRow(location, shot=False, parent=self.rows_host)
        fila.changed.connect(self.refresh)
        fila.edited.connect(self._update_actions_enabled)
        fila.path_changed.connect(self._path_edited)
        fila.remove_requested.connect(self._remove_row)
        fila.drag_started.connect(self._drag_started)
        fila.drag_moved.connect(self._drag_moved)
        fila.drag_finished.connect(self._drag_finished)
        # -1 es el stretch final; las filas van antes.
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, fila)
        self.rows.append(fila)
        return fila

    def _add_empty_row(self):
        fila = self._add_row(
            {"name": "", "path": "", "scan": True, "copy_to": False, "shortcut": ""}
        )
        # La tabla entera y no solo la fila nueva: agregar una cambia cual es
        # la ultima, y la que lo era se queda con su separador de mas.
        self.apply_appearance()
        fila.name_edit.setFocus()
        self.refresh()
        # Y se la lleva a la vista. Si la tabla ya llegaba a su alto maximo, la
        # fila nueva nace ABAJO del area visible: quedaba creada, con el foco
        # puesto y sin que se viera, o sea que escribir el nombre parecia no
        # hacer nada. Va diferido porque recien despues de que el layout corra
        # la fila tiene geometria y el scroll sabe adonde ir.
        QTimer.singleShot(0, lambda: self._mostrar_fila(fila))

    def _mostrar_fila(self, fila):
        """Scrollea el area de filas hasta que esa fila se vea entera."""
        if fila is None or fila not in self.rows:
            return
        self.scroll.ensureWidgetVisible(fila, 0, ROW_REVEAL_MARGIN)

    def _remove_row(self, fila):
        if fila not in self.rows:
            return
        nombre = fila.name_edit.text().strip() or fila.path() or "this location"
        respuesta = QMessageBox.question(
            self, "Media Manager",
            "Remove %s?" % nombre,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        self.rows.remove(fila)
        self.rows_layout.removeWidget(fila)
        fila.setParent(None)
        fila.deleteLater()
        # Igual que al agregar: borrar cambia cual es la ultima fila.
        self.apply_appearance()
        self.refresh()

    # -------------------------------------------------------------- arrastre --
    def _drag_started(self, fila):
        self._dragging = fila
        # La que se mueve va atenuada, y una linea de acento marca el borde
        # por el que va a entrar. Antes solo se le aclaraba el texto, que no
        # decia nada de adonde caia.
        fila.set_dragging(True)
        self._update_drop_indicator(fila)

    def _drag_moved(self, fila, global_y):
        if self._dragging is not fila or len(self.rows) < 2:
            return
        actual = self.rows.index(fila)
        # Cuantas filas quedan ARRIBA del cursor: ese es el lugar donde cae.
        destino = 0
        for otra in self.rows:
            if otra is fila:
                continue
            if global_y > otra.mapToGlobal(otra.rect().center()).y():
                destino += 1
        if destino != actual:
            self.rows.pop(actual)
            self.rows.insert(destino, fila)
            self.rows_layout.removeWidget(fila)
            # +1 porque la fila del shot va siempre primera y no esta en
            # self.rows.
            self.rows_layout.insertWidget(destino + 1, fila)
            self._update_row_flags()
        self._update_drop_indicator(fila)

    def _update_drop_indicator(self, fila):
        """
        Pinta la linea de acento en el borde por el que entra la fila.

        Va abajo de la fila de ARRIBA del hueco y no arriba de la que se
        arrastra: esa esta atenuada al 35% y la linea se atenuaba con ella.
        Es el mismo borde, asi que se ve en el mismo lugar. Arriba siempre hay
        una fila, porque la del shot va primera y no se mueve.
        """
        arriba = None
        if fila is not None and fila in self.rows:
            indice = self.rows.index(fila)
            arriba = self.rows[indice - 1] if indice > 0 else self.shot_row
        for otra in [self.shot_row] + self.rows:
            otra.set_drop_target(otra is arriba)

    def _drag_finished(self, fila):
        self._dragging = None
        fila.set_dragging(False)
        self._update_drop_indicator(None)
        fila.apply_theme(self.UI, self.font_size())
        self.refresh()

    # ------------------------------------------------------------ apariencia --
    def font_size(self):
        return self.font_field.value() if hasattr(self, "font_field") else \
            UIStyle.Metric.TABLE_FONT_SIZE

    def _pick_theme(self, theme_id):
        if theme_id == self.appearance.get("theme"):
            return
        self.appearance["theme"] = theme_id
        self.UI = UIStyle.theme(theme_id)
        self.apply_appearance()
        self.appearance_previewed.emit(dict(self.appearance))
        self._persist_theme(theme_id)

    def _persist_theme(self, theme_id):
        """
        Guarda el tema SOLO, apenas se lo elige.

        El tema se aplica en vivo sobre las dos ventanas, asi que pedir Save
        despues de haberlo visto puesto no significa nada: lo que se ve ya es
        el resultado. Es la unica preferencia que se guarda sola.

        Lo que se escribe es lo GUARDADO con el tema nuevo encima, nunca lo que
        hay en pantalla: las locations, el shot y el tamano de letra siguen
        necesitando Save, y este atajo no puede colarlos a medio editar.
        """
        if self.load_error:
            # Lo que hay en memoria son los valores de fabrica y no la
            # configuracion del usuario: escribirla la destruiria. Eso solo
            # pasa desde Save, que lo pregunta.
            debug_print("Tema no guardado: el .ini no se pudo leer")
            return
        guardado = {
            "shot": dict(self.settings.get("shot") or DEFAULT_SHOT),
            "locations": [dict(l) for l in (self.settings.get("locations") or ())],
            # El tamano de letra sale del GUARDADO y no de self.appearance, que
            # trae el que se esta previsualizando.
            "appearance": dict(self.saved_appearance, theme=theme_id),
        }
        ok, ruta = save_settings(guardado)
        if not ok:
            debug_print("No se pudo guardar el tema en %s" % (ruta or "ningun lado"))
            return
        self.settings["appearance"] = dict(guardado["appearance"])
        # Sin esto closeEvent ve una apariencia distinta de la guardada y le
        # devuelve a la ventana principal el tema viejo al cerrar.
        self.saved_appearance["theme"] = theme_id
        debug_print("Tema %s guardado en %s" % (theme_id, ruta))

    def _pick_font_size(self, valor):
        self.appearance["table_font_size"] = valor
        self.apply_appearance()
        # La fila crece con la letra, asi que la caja y la ventana tienen que
        # volver a medirse: sin esto la ultima fila queda cortada.
        self._fit_table()
        self.adjustSize()
        self.appearance_previewed.emit(dict(self.appearance))
        # A diferencia del tema, el tamano de letra SI necesita Save: cambia
        # el alto de cada fila de la tabla principal, o sea cuanto entra en
        # pantalla, y eso no es una preferencia que convenga dejar puesta de
        # rebote por haberla probado.
        self._update_actions_enabled()

    def apply_appearance(self):
        """Repinta la ventana entera con el tema y el tamano elegidos."""
        UI = self.UI
        fs = self.font_size()
        self.appearance["table_font_size"] = fs
        # Los dos altos se derivan del tamano de letra, asi que un .ini con
        # otro numero baja la tabla entera sin que se note de donde viene.
        # Queda logueado para poder medirlo en vez de estimarlo contra una
        # captura.
        debug_print(
            "Apariencia: tema %s, fondo %s, letra %d, fila %d, cabecera %d"
            % (self.appearance.get("theme"), UI.Color.WINDOW, fs,
               fs + ROW_EXTRA, fs + HEAD_EXTRA)
        )

        self.setStyleSheet(
            UI.Style.WINDOW + UI.Style.FORM + UI.Style.TOOLTIP + UI.Style.SCROLLBAR
        )
        self.title_label.setStyleSheet(
            "color: %s; font-size: 27px; font-weight: 700;" % UI.Color.TEXT_STRONG
        )
        self.subtitle_label.setStyleSheet(
            "color: %s; font-size: 13px;" % UI.Color.TEXT
        )
        # La tabla es un bloque: borde, esquinas redondeadas y la cabecera con
        # fondo propio adentro. El fondo lo pinta la CAJA y todo lo que tiene
        # adentro va transparente, si no cada contenedor intermedio se lleva
        # el gris de ventana y la caja no se ve.
        radio_interno = max(0, UIStyle.Metric.RADIUS_CARD - 1)
        self.head_row.setFixedHeight(fs + HEAD_EXTRA)
        self.table_box.setStyleSheet(
            (
                "#lgaTableBox { background-color: %(surface)s;"
                " border: 1px solid %(border)s;"
                " border-radius: %(radio)dpx; }"
                "#lgaTableHead { background-color: %(header)s; border: none;"
                " border-bottom: 1px solid %(border)s;"
                " border-top-left-radius: %(radio_int)dpx;"
                " border-top-right-radius: %(radio_int)dpx; }"
                "#lgaTableHead QLabel { background: transparent; color: %(text)s;"
                " font-size: %(head_fs)dpx; %(semibold)s }"
                "QScrollArea { background: transparent; border: none; }"
                "QWidget { background-color: transparent; }"
                % {
                    "surface": UI.Color.SURFACE,
                    "border": UI.Color.BORDER,
                    "header": UI.Color.SURFACE_HEADER,
                    "text": UI.Color.TEXT_HEADER,
                    "radio": UIStyle.Metric.RADIUS_CARD,
                    "radio_int": radio_interno,
                    "head_fs": max(9, fs + HEAD_FONT_OFFSET),
                    "semibold": UIStyle.semibold_css(),
                }
            )
            # Va al final para que le gane al QWidget transparente de arriba,
            # que tiene la misma especificidad.
            + UI.Style.SCROLLBAR
            # El riel de la barra va transparente: la hoja comun lo pinta del
            # gris de VENTANA, que adentro de la caja de la tabla dibujaba una
            # franja oscura al costado de todas las filas.
            + "QScrollBar:vertical { background: transparent; }"
        )
        # El letter-spacing de la cabecera no existe como propiedad de QSS:
        # se setea sobre el QFont del label. Va despues de la hoja porque el
        # tamano de letra sale de ahi y el QFont hay que leerlo ya resuelto.
        # El enum va por el camino plano en Qt5 y por el anidado en Qt6. Se
        # resuelve una vez y no en cada vuelta del bucle, y si no estuviera en
        # ninguno de los dos lados la cabecera se dibuja sin el espaciado en
        # vez de voltear la ventana entera por medio pixel de aire.
        espaciado = getattr(QtGui.QFont, "AbsoluteSpacing", None)
        if espaciado is None:
            espaciado = getattr(
                getattr(QtGui.QFont, "SpacingType", None), "AbsoluteSpacing", None
            )
        if espaciado is not None:
            for etiqueta in self.head_labels:
                fuente = etiqueta.font()
                fuente.setLetterSpacing(espaciado, HEAD_LETTER_SPACING)
                etiqueta.setFont(fuente)

        for tarjeta in (self.card_wildcard, self.card_included):
            tarjeta.setStyleSheet(
                "QWidget { background-color: %s; border: 1px solid %s;"
                " border-radius: %dpx; }"
                # Sin font-size: la letra de la tarjeta la lleva su propio
                # QFont, que es con el que se midio el ancho. Declararla en los
                # dos lados es volver a poder medir con una y dibujar con otra.
                "QLabel { border: none; color: %s; }"
                % (UI.Color.SURFACE, UI.Color.BORDER, UIStyle.Metric.RADIUS,
                   UI.Color.TEXT)
            )
            tarjeta.icono.setPixmap(
                tinted_icon("info", UI.Color.ACCENT_HOVER, 20).pixmap(20, 20)
            )

        self.add_button.setStyleSheet(UI.Style.BTN_SECONDARY)
        self.add_button.setIcon(tinted_icon("plus", UI.Color.TEXT, 17))
        self.cancel_button.setStyleSheet(UI.Style.BTN_SECONDARY)
        self.save_button.setStyleSheet(UI.Style.BTN_PRIMARY)
        # Los botones y el campo del stepper llevan el radio del campo inline,
        # no el de los botones de accion: son la misma pieza de tres partes y
        # con dos radios distintos el campo del medio no cierra con los lados.
        stepper = (
            "QPushButton { background-color: %(raised)s;"
            " border: 1px solid %(borde)s; border-radius: %(radius)dpx;"
            " color: %(fuerte)s; }"
            "QPushButton:hover { background-color: %(hover)s;"
            " border-color: %(borde_hover)s; }"
            % {
                "raised": UI.Color.SURFACE_RAISED,
                "borde": UI.Color.BORDER_STRONG,
                "borde_hover": UI.Color.BORDER_HOVER,
                "hover": UI.Color.SURFACE_HOVER,
                "fuerte": UI.Color.TEXT_STRONG,
                "radius": UIStyle.Metric.RADIUS_FIELD,
            }
        )
        self.font_minus.setStyleSheet(stepper)
        self.font_plus.setStyleSheet(stepper)
        self.font_field.setStyleSheet(
            "QLineEdit { background-color: %s; border: 1px solid %s;"
            " border-radius: %dpx; color: %s; %s }"
            % (UI.Color.SURFACE, UI.Color.BORDER_STRONG,
               UIStyle.Metric.RADIUS_FIELD, UI.Color.TEXT_STRONG,
               UIStyle.semibold_css())
        )
        self.version_label.setStyleSheet(
            "color: %s; font-size: 12px;" % UI.Color.TEXT_DIM
        )
        for etiqueta in (self.theme_label, self.font_label):
            etiqueta.setStyleSheet("color: %s;" % UI.Color.TEXT)
        for linea in (self.appearance_sep, self.footer_sep):
            linea.setStyleSheet("background-color: %s; border: none;" % UI.Color.BORDER)

        elegido = self.appearance.get("theme")
        for theme_id, boton in self.theme_buttons.items():
            boton.setStyleSheet(self._theme_button_css(theme_id == elegido))

        # El separador de la ultima fila se saca ANTES de pintar: abajo ya
        # esta el borde de la caja y quedaban dos lineas pegadas.
        self._update_row_flags()
        self.shot_row.apply_theme(UI, fs)
        for fila in self.rows:
            fila.apply_theme(UI, fs)
        self._fit_table()

    def _theme_button_css(self, elegido):
        """
        El boton de un tema.

        No usa BTN_PRIMARY/BTN_SECONDARY: esos son botones de accion, con 18
        px de padding y negrita, y una tira de seis quedaba el doble de gorda
        que la del disenio. El elegido se marca con el borde de acento, no
        pintandolo entero de violeta.
        """
        UI = self.UI
        return (
            "QPushButton { background-color: %(fondo)s;"
            " border: 1px solid %(borde)s; border-radius: %(radius)dpx;"
            " color: %(texto)s; padding: 0 %(pad)dpx; font-size: %(fs)dpx; }"
            "QPushButton:hover { background-color: %(raised)s; color: %(fuerte)s; }"
            % {
                "fondo": UI.Color.SURFACE_RAISED if elegido else UI.Color.SURFACE,
                "borde": UI.Color.ACCENT_HOVER if elegido else UI.Color.BORDER_STRONG,
                "texto": UI.Color.TEXT_STRONG if elegido else UI.Color.TEXT,
                "raised": UI.Color.SURFACE_RAISED,
                "fuerte": UI.Color.TEXT_STRONG,
                "radius": UIStyle.Metric.RADIUS,
                "pad": THEME_BUTTON_PADDING,
                "fs": THEME_BUTTON_FONT,
            }
        )

    def _update_row_flags(self):
        """Marca cual es la ultima fila, que es la que no lleva separador."""
        ultima = self.rows[-1] if self.rows else self.shot_row
        for fila in [self.shot_row] + self.rows:
            fila.set_last(fila is ultima)

    def _fit_table(self):
        """
        Le da al area de filas el alto que necesita, hasta el tope.

        Sin esto el area se queda con el minimo que le toque al repartir el
        alto de la ventana y la tabla abre cortada a la mitad, con scroll,
        aunque haya lugar de sobra abajo.
        """
        alto_fila = self.font_size() + ROW_EXTRA
        filas = len(self.rows) + 1  # +1 por la del shot
        contenido = filas * alto_fila + 4
        alto = min(TABLE_MAX_HEIGHT, contenido)
        # El alto que la tabla PIDE es el de su contenido, y ese va de tope: si
        # sobran filas se corta en TABLE_MAX_HEIGHT y aparece la barra, y si no
        # sobran, agrandar la ventana no estira una tabla que ya no tiene mas
        # que mostrar.
        self.scroll.setMaximumHeight(alto)
        # El piso es de unas pocas filas y no el alto entero del contenido.
        # Puesto en el contenido, la tabla no se podia comprimir y con ella la
        # ventana tampoco: no habia forma de achicarla aunque el usuario
        # estuviera dispuesto a scrollear.
        self.scroll.setMinimumHeight(
            min(alto, TABLE_MIN_ROWS * alto_fila + 4)
        )
        # El hueco del encabezado sigue a la barra: el area nunca pasa del
        # tope, asi que la barra aparece exactamente cuando el contenido lo
        # supera. Reservando el ancho siempre, las veces que NO hay barra el
        # encabezado quedaba corrido 10 px contra las filas.
        self._sync_head_margin()

    def _sync_head_margin(self):
        """
        Le reserva al encabezado el ancho que la barra de scroll le come a las
        filas.

        Se mide la diferencia REAL entre el encabezado y el viewport, no se
        deduce de si el contenido pasa el alto maximo. Deducirlo estaba mal
        desde que la ventana se puede achicar: con pocas filas pero la ventana
        baja, la barra aparece igual -el area de filas se comprime hasta dos
        filas- y el encabezado no reservaba nada, asi que las columnas de la
        derecha volvian a quedar corridas 10 px. Es el mismo desfasaje que el
        del item de ancho cero, entrando por la otra puerta.
        """
        if getattr(self, "head_layout", None) is None:
            return
        falta = max(0, self.head_row.width() - self.scroll.viewport().width())
        margenes = self.head_layout.contentsMargins()
        if margenes.right() != falta:
            self.head_layout.setContentsMargins(0, 0, falta, 0)

    # ------------------------------------------------------------- resolucion --
    def _path_edited(self, _fila):
        self.refresh()

    def refresh(self):
        """Recalcula inclusiones y validacion, y pide resolver contra disco."""
        self._update_inheritance()
        self._update_field_errors()
        self._update_actions_enabled()
        self._resolve_timer.start()

    # --------------------------------------------------------- cambios sin guardar --
    def _editable_state(self):
        """
        Todo lo que Cancel descarta y Save escribe, en una forma comparable.

        El TEMA no entra: se guarda solo al elegirlo, asi que no es ni algo que
        Save tenga que escribir ni algo que Cancel tenga que devolver.

        Las filas van SIN filtrar las que estan a medias. Al guardar se
        descartan, pero una fila recien agregada es un cambio en pantalla que
        Cancel si descarta, y con la lista filtrada el boton quedaba apagado
        justo cuando habia algo para cancelar.
        """
        return {
            "shot": self.shot_row.to_dict(),
            "locations": [fila.to_dict() for fila in self.rows],
            "font_size": self.font_size(),
        }

    def _is_dirty(self):
        return self._editable_state() != self._baseline

    def _update_actions_enabled(self):
        """
        Cancel y Save se encienden juntos, y solo si hay algo que hacer.

        Es un solo estado porque son la misma pregunta vista de los dos lados:
        si nada cambio desde que se abrio la ventana, Save escribiria el
        archivo identico y Cancel no tendria nada que descartar. Un boton
        habilitado que no hace nada miente, que es la misma regla que ya sigue
        la barra de la ventana principal.
        """
        activos = self._is_dirty()
        self.cancel_button.setEnabled(activos)
        self.save_button.setEnabled(activos)

    def _update_field_errors(self):
        """Marca en rojo los campos repetidos o con un atajo que no sirve."""
        nombres = {}
        rutas = {}
        atajos = {}
        for fila in self.rows:
            datos = fila.to_dict()
            if datos["name"]:
                nombres.setdefault(datos["name"].lower(), []).append(fila)
            if datos["path"]:
                rutas.setdefault(datos["path"].lower(), []).append(fila)
            if datos["copy_to"] and datos["shortcut"]:
                atajos.setdefault(datos["shortcut"], []).append(fila)

        errores = {f.uid: set() for f in self.rows}
        for grupo, campo in ((nombres, "name"), (rutas, "path")):
            for filas in grupo.values():
                if len(filas) > 1:
                    for fila in filas:
                        errores[fila.uid].add(campo)
        for letra, filas in atajos.items():
            # Las cinco de la barra no se pueden usar aunque no las repita
            # nadie: Qt no dispararia ni el boton ni la location.
            if len(filas) > 1 or letra in RESERVED_SHORTCUTS:
                for fila in filas:
                    errores[fila.uid].add("shortcut")

        for fila in self.rows:
            fila.set_field_errors(errores[fila.uid], self.UI, self.font_size())

    def _update_inheritance(self):
        """
        Marca las locations que ya cubre otra que se escanea entera.

        Se mira el scan EXPLICITO de las otras filas y no el efectivo: con el
        efectivo, dos rutas que se incluyen mutuamente se apagarian la una a
        la otra en loop y ninguna terminaria escaneandose.
        """
        # El shot NO entra en la cuenta. Define el limite del shot, no de
        # donde se busca: eso lo dice la tabla de locations. Metiendolo,
        # cualquier location relativa cae adentro de "../.." y las cuatro
        # filas quedaban tildadas y deshabilitadas de entrada, o sea que la
        # tabla entera dejaba de poder editarse.
        candidatas = [{"name": fila.name_edit.text().strip(),
                       "path": fila.path(),
                       "scan": bool(fila.data.get("scan", True))}
                      for fila in self.rows]

        for i, fila in enumerate(self.rows):
            fila.set_scan_inherited(paths.scanning_parent(candidatas, i, self.nk_dir))

    def _resolve_now(self):
        if not self.nk_dir:
            # Sin .nk guardado no hay contra que resolver: la columna entera
            # se queda en "—" en vez de mentir.
            for fila in [self.shot_row] + self.rows:
                fila.set_resolution(None, self.UI)
            return

        if self._worker is not None:
            self._worker.cancel()
        pedidos = [(fila.uid, fila.path()) for fila in [self.shot_row] + self.rows]
        self._worker = PathResolveWorker(pedidos, self.nk_dir)
        self._worker.signals.resolved.connect(self._resolved)
        QThreadPool.globalInstance().start(self._worker)

    def _resolved(self, resultados):
        self._worker = None
        for fila in [self.shot_row] + self.rows:
            if fila.uid in resultados:
                fila.set_resolution(resultados[fila.uid], self.UI)

    # ------------------------------------------------------------- validacion --
    def problems(self):
        """Los problemas que impiden guardar, en texto."""
        avisos = []
        nombres = {}
        rutas = {}
        atajos = {}

        for fila in self.rows:
            datos = fila.to_dict()
            if not datos["name"] and not datos["path"]:
                continue  # fila vacia: se descarta al guardar, no es un error
            if not datos["name"] or not datos["path"]:
                avisos.append("A location has an empty name or path.")
                continue
            nombres.setdefault(datos["name"].lower(), []).append(datos["name"])
            rutas.setdefault(datos["path"].lower(), []).append(datos["path"])
            if datos["copy_to"] and datos["shortcut"]:
                atajos.setdefault(datos["shortcut"], []).append(datos["name"])

        for clave, iguales in nombres.items():
            if len(iguales) > 1:
                avisos.append("Two locations are named \"%s\"." % iguales[0])
        for clave, iguales in rutas.items():
            if len(iguales) > 1:
                avisos.append("Two locations point to \"%s\"." % iguales[0])
        for letra, duenos in atajos.items():
            if len(duenos) > 1:
                avisos.append(
                    "Shortcut Alt+%s is used by %s." % (letra, " and ".join(duenos))
                )
            if letra in RESERVED_SHORTCUTS:
                avisos.append(
                    "Shortcut Alt+%s is already used by the toolbar; "
                    "Qt would fire neither." % letra
                )

        # Un destino de Copy to tiene que resolver a UNA carpeta: con cero no
        # hay adonde copiar -"../*assets*" no es un nombre de carpeta que se
        # pueda crear- y con varias habria que elegir por el usuario.
        for fila in self.rows:
            datos = fila.to_dict()
            if not datos["copy_to"] or not datos["path"]:
                continue
            etiqueta = datos["name"] or datos["path"]
            resolution = fila.resolution()
            if resolution is None:
                # Todavia no volvio el worker, o el .nk no esta guardado. No
                # se deja pasar en silencio: sin resolver no se sabe si el
                # destino existe, y el aviso es justamente lo que se decidio.
                if self.nk_dir:
                    avisos.append(
                        "\"%s\" has not been checked against disk yet; "
                        "try again in a moment." % etiqueta
                    )
                continue
            if resolution.kind == paths.INVALID:
                avisos.append("\"%s\" is not a valid path." % etiqueta)
            elif not resolution.folders:
                avisos.append(
                    "\"%s\" is a Copy to destination but does not match any "
                    "existing folder." % etiqueta
                )
            elif len(resolution.folders) > 1:
                avisos.append(
                    "\"%s\" is a Copy to destination but matches %d folders."
                    % (etiqueta, len(resolution.folders))
                )
        return avisos

    # ---------------------------------------------------------------- guardar --
    def collect(self):
        """Lo que hay en pantalla, en el formato que espera el modulo de config."""
        locations = [f.to_dict() for f in self.rows]
        return {
            "shot": self.shot_row.to_dict(),
            # La fila a medias se descarta, igual que en el formato viejo.
            "locations": [l for l in locations if l["name"] and l["path"]],
            "appearance": dict(self.appearance),
        }

    def save(self):
        avisos = self.problems()
        if avisos:
            QMessageBox.warning(
                self, "Media Manager",
                "The settings were not saved:\n\n• " + "\n• ".join(avisos),
            )
            return

        if self.load_error:
            respuesta = QMessageBox.question(
                self, "Media Manager",
                "Your settings file could not be read, so what is shown here "
                "are the factory defaults.\n\nSave anyway and overwrite it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if respuesta != QMessageBox.Yes:
                return

        datos = self.collect()
        ruta = get_write_path()
        if not ruta:
            QMessageBox.warning(
                self, "Media Manager",
                "The settings could not be saved: no writable config folder "
                "was found.",
            )
            return
        if not write_ini(ruta, format_ini(datos)):
            QMessageBox.warning(
                self, "Media Manager",
                "The settings could not be saved to:\n%s" % ruta,
            )
            return

        debug_print("Configuracion guardada en %s" % ruta)
        self.saved_appearance = dict(self.appearance)
        # Lo guardado pasa a ser el punto de comparacion, asi que Cancel y Save
        # se vuelven a apagar. La ventana se cierra a continuacion, pero el
        # estado no puede quedar mintiendo mientras tanto: _persist_theme
        # escribe sobre self.settings y tiene que ver lo que hay en disco.
        self.settings["shot"] = dict(datos["shot"])
        self.settings["locations"] = [dict(l) for l in datos["locations"]]
        self.settings["appearance"] = dict(datos["appearance"])
        self._baseline = self._editable_state()
        self._update_actions_enabled()
        self.settings_saved.emit()
        self.close()

    def _cancel(self):
        self.close()

    def closeEvent(self, event):
        # La reversion va aca y no en _cancel: Escape pasa por _cancel pero
        # la X de la ventana y Alt+F4 no, y por ahi se salia dejando aplicado
        # un tema que no se guardo nunca.
        if self.appearance != self.saved_appearance:
            self.appearance_previewed.emit(dict(self.saved_appearance))
            self.appearance = dict(self.saved_appearance)
        if self._worker is not None:
            self._worker.cancel()
            self._worker = None
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        """
        El viewport avisa cuando aparece o se va la barra de scroll.

        Es el unico momento confiable: la barra la decide Qt segun el alto real
        del area, que cambia tanto al agregar filas como al achicar la ventana.
        """
        if (
            getattr(self, "scroll", None) is not None
            and obj is self.scroll.viewport()
            and event.type() == QtCore.QEvent.Resize
        ):
            self._sync_head_margin()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)
