"""
_______________________________________________________________________

  LGA_MediaManager_FileScanner v2.43 | Lega

  Escaneo del proyecto, tabla de medias y relink de archivos offline.

  v2.43: Suma on_scan_failed: el cartel de que el escaneo se corto por
         un error, con el detalle y la referencia al log.
  v2.42: Sin cambios propios: acompana la version de la tool, que
         subio por el ImportError de TransparentTextDelegate.
  v2.41: Cinco defectos que salieron de revisar copy, delete y relink
         con seleccion multiple. repoint_read reescribia la tabla
         filtrando por la CARPETA de origen, asi que copiar una fila
         tambien reapuntaba las otras que vivian en esa carpeta y las
         marcaba Online sin haber copiado nada de ellas; y armaba el
         path nuevo cortando el texto por el largo del path del knob,
         que solo coincide con padding 4 -"%05d" son cuatro caracteres
         y "#####" son cinco-, asi que con cualquier otro padding
         salia roto. Ahora toca UNA fila, buscada por su ruta, y le
         cambia solo la carpeta.
         El reapuntado se aplicaba sin mirar `cancelado` ni `errores`:
         cancelar una copia de seis filas despues de la primera
         dejaba los seis Reads mirando el destino y cinco offline.
         Ahora se verifica contra disco, fila por fila.
         El relink no hacia nada -y no avisaba nada- en las filas con
         mas de un Read: la celda dice "Read1, Read2" y eso a
         nuke.toNode() le da None, con lo que se salteaba el bloque
         entero, incluido el path de la tabla. Ahora se reapuntan
         todos los Reads de la fila, y encontrar el archivo sin tener
         a que apuntarlo tambien se informa.
         closeEvent no marcaba la tanda de relink como cancelada, asi
         que cerrar el Media Manager durante una busqueda abria un
         "File not found." sobre una ventana ya cerrada.
         remove_duplicates borraba filas recorriendo hacia adelante,
         con el range() calculado antes de las bajas y los indices
         del diccionario apuntando a otras filas despues de cada una.
         Ademas: las tres operaciones se excluyen entre si y apagan la
         barra mientras corren -la ventana de progreso no es modal-;
         la carpeta que se manda entera a la papelera se revalida
         contra disco en el momento de borrar y no con el dato del
         escaneo; el resumen del borrado cuenta archivos reales y no
         entradas del worker; y los carteles pasan a ingles, que es
         el idioma de la UI.
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
  v2.39: delete_selected y copy_to se rehacen sobre el mismo patron:
         el hilo principal arma el plan y el worker solo toca disco.
         El borrado leia la tabla desde el worker y ademas hacia
         start() seguido de wait(), o sea un hilo que no servia para
         nada porque congelaba la ventana igual. La copia encadenaba
         una ventana por archivo con cinco caminos distintos para
         terminar; ahora la tanda entera va en un worker, porque no
         queda nada que preguntar entre archivo y archivo.
         La sobreescritura se pregunta UNA vez por tanda, con
         Overwrite / Skip: con diez filas eran diez carteles.
  v2.38: El icono de Rescan gira mientras dura el escaneo. Es lo
         unico que dice que la herramienta esta haciendo algo, y no
         hacia nada. Se redibuja rotado en cada cuadro con el painter
         girando alrededor del centro, no con transformed(): esa
         agranda la caja para que entre el rectangulo rotado, asi que
         el icono cambiaria de tamano en cada tick y el boton se
         movería con el.
  v2.36: Status suma 5 px. Read y Status ganan una perilla de ajuste
         fino -COL_READ_EXTRA y COL_STATUS_EXTRA- que se suma a lo
         medido: es el unico lugar donde retocar cuanto respiran, sin
         tener que meterse en el calculo.
  v2.35: El ancho de la columna del path se recalcula cuando avisa el
         VIEWPORT y no en el resizeEvent de la ventana: Qt le entrega
         el resize al padre antes de reacomodar a los hijos, asi que
         ahi el viewport todavia medía lo de antes y la columna se
         quedaba en su minimo con media ventana vacia al lado.
         Las cuatro columnas van en Fixed: ninguna se arrastra a
         mano. Los anchos los decide la herramienta, asi que un
         arrastre solo podia desarmarlos y dejar huecos. Se va
         tambien el resizeColumnsToContents, que devolvia algo que se
         pisaba dos lineas mas abajo y en miles de filas no es gratis.
  v2.34: La tabla deja de scrollear en horizontal y el que scrollea
         es el path adentro de su columna, con su propia barra. Con
         la de la tabla se iban de la vista tambien el numero de
         fila, el Read y el Status, que son con lo que se decide que
         hacer con la fila.
         Read y Status dejan de ser anchos fijos: se miden. Son las
         dos columnas cuyo contenido se conoce entero -"Read15",
         "Offline"- asi que un numero a ojo solo puede sobrar, y lo
         que sobra ahi se lo saca al path, que es la unica que de
         verdad necesita lugar. Status se mide sobre los CUATRO
         estados y no sobre los cargados, para que la columna no
         cambie de ancho segun lo que encuentre el escaneo.
  v2.33: El ancho de la ventana y el de la columna del path salen de
         medir el path MAS LARGO con la letra del delegado. La
         columna deja el modo Stretch, que llena el viewport siempre
         y por lo tanto encoge el path al achicar la ventana y lo
         recorta sin ofrecer scroll: pasa a Interactive y la maneja
         fit_path_column, que le da todo el sobrante pero nunca menos
         de lo que hace falta. Asi la barra horizontal aparece sola.
         El ancho de la ventana toma el mismo tope que el alto, el
         80% de la pantalla: sin el, un path largo la abria mas ancha
         que el monitor y no se podia ni mover.
  v2.32: El minimo de ancho de la ventana lo fija SOLO la barra de
         herramientas. Antes mandaba la mas ancha entre la barra y
         el pie, y el pie ganaba por varios cientos de pixeles: la
         ventana no se podia achicar aunque la tabla entrara comoda,
         porque el piso lo ponia una leyenda que es texto de ayuda.
         Ahora las explicaciones de la leyenda se esconden cuando no
         entran -el punto de color y el nombre del estado solos ya
         dicen lo mismo- en vez de cortarse a la mitad de una
         palabra.
  v2.31: Las lineas horizontales entre filas las dibuja cada
         delegado con paint_row_separator: se habian perdido al
         apagar la grilla de Qt, y la regla `QTableWidget::item`
         no alcanza porque las cuatro columnas tienen delegado
         propio y le pintan encima. Van en ROW_LINE, que es mas
         claro que la fila; la tabla de los ajustes usa BORDER, que
         es otro token, y en el prototipo tambien son distintos.
         El '#' deja de ser un id fijo de carga y pasa a contar lo
         que se ve: 1, 2, 3... de arriba hacia abajo, sin importar
         por que columna se ordene ni cuantas filas escondio el
         filtro. El orden de carga no se pierde, sigue en la clave
         de Qt.UserRole, que es por donde ordena la columna '#'.
  v2.30: Poner Inter no alcanzaba: sus tres caras NO forman una
         sola familia para Qt. La Regular y la Bold caen las dos en
         "Inter", pero la SemiBold cae en una familia PROPIA, "Inter
         SemiBold". Con eso, `font-weight: 600` sobre "Inter" no
         devuelve la SemiBold sino la cara mas cercana que si esta
         en esa familia: la Bold de 700. Por eso la etiqueta de los
         botones, la cabecera de la tabla, los contadores de las
         pastillas, la leyenda y Rescan seguian saliendo en negrita.
         Ahora el peso 600 se pide nombrando la familia.
  v2.29: Se le pone a la ventana la fuente del pack, que era la
         causa de que todo se viera mas pesado que el prototipo. Y se
         cierran las diferencias que quedaban contra el disenio:
         la grilla de Qt se apaga entera -dibujaba verticales que el
         disenio no tiene y pintaba las horizontales MAS OSCURAS que
         la fila, cuando van mas claras-, la tabla recupera su borde
         y sus esquinas redondeadas, y toma la barra de scroll del
         pack en vez de la nativa de macOS, que iba del doble de
         ancho y con flechas.
         El atajo deja de declararse con un '&' en el texto: Qt
         subrayaba la letra ADEMAS de dibujar el cartel "Alt + G" al
         costado, o sea la misma informacion dos veces. Ahora lo
         dispara un QShortcut. El cartel va sin peso propio y se
         apaga junto con el boton; el tacho de Delete sigue rojo
         cuando el boton esta deshabilitado, en vez de pasar al gris.
         La columna Read se alinea a la izquierda y en el gris de
         cuerpo, con una raya en las filas sin Read, y el numero de
         la fila SELECCIONADA deja de encenderse en blanco: es un id,
         no contenido. Los margenes de la ventana pasan a los 18 px
         del disenio -el default del host da 9- y el alto cierra en
         una fila entera en vez de dejar media contra el pie.
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
QScrollBar = QtWidgets.QScrollBar
QBrush = QtGui.QBrush
QColor = QtGui.QColor
QFont = QtGui.QFont
QFontMetrics = QtGui.QFontMetrics
QPainter = QtGui.QPainter
QPixmap = QtGui.QPixmap
QPalette = QtGui.QPalette
QMovie = QtGui.QMovie
QScreen = QtGui.QScreen
QIcon = QtGui.QIcon
QHeaderView = QtWidgets.QHeaderView
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QKeySequence = QtGui.QKeySequence
# QShortcut se mudo de QtWidgets a QtGui en Qt6. Se busca en los dos lados
# porque el pack corre en Nuke 15 (PySide2) y en Nuke 16/17 (PySide6).
try:
    QShortcut = QtGui.QShortcut
except AttributeError:  # pragma: no cover - depende del binding
    QShortcut = QtWidgets.QShortcut
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
    "path_scroll": (
        "Corre el path para ver el final.\n"
        "Aparece cuando el mas largo no entra en su columna"
    ),
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
# Los indices viven ahora en LGA_MediaManager_utils y se importan de ahi (ver
# el bloque de importaciones mas abajo): los delegados de ese modulo tambien
# los necesitan, y tenerlos escritos en los dos lados —aca por nombre y alla
# por numero pelado— es la forma segura de que se separen sin que nada avise.

# Anchos del disenio: `52 | 1fr (min 300) | 96 | 118`. El del path no se fija:
# es la que se estira.
COL_NUM_WIDTH = 52
# Read y Status ya no son anchos fijos: se miden sobre su contenido, que en las
# dos se conoce entero. Esto es solo el piso, para que una tabla vacia o un
# escaneo sin Reads no deje columnas de dos pixeles.
COL_READ_MIN_WIDTH = 60
COL_STATUS_MIN_WIDTH = 84
# ----------------------------------------------------------------------------
#  PERILLAS DE AJUSTE FINO de las dos columnas medidas. El ancho lo calculan
#  read_column_width() y status_column_width() sobre su contenido; estos dos
#  numeros se le SUMAN a esa cuenta. Suben o bajan de a pixel, y no hay que
#  tocar nada mas: son el unico lugar donde retocar cuanto respiran.
# ----------------------------------------------------------------------------
COL_READ_EXTRA = 0
COL_STATUS_EXTRA = 5
COL_PATH_MIN_WIDTH = 300
# Lo mas angosta que se deja la columna del path en pantalla. No es lo que el
# path NECESITA -eso se mide- sino hasta donde se la deja comprimir antes de
# que deje de ser legible; de ahi en mas la diferencia la cubre su barra.
COL_PATH_VIEW_MIN = 160
# Cuanto corre la barra del path por click en sus flechas o por rueda.
PATH_SCROLL_STEP = 24
# Hasta donde puede crecer la ventana para que entre el path mas largo. Mas
# alla de eso el path se corta y aparece el scroll horizontal: una ventana mas
# ancha que la pantalla no se puede ni mover.
WINDOW_MAX_SCREEN_RATIO = 0.80

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

# El aire entre el contenido y el borde de la ventana. Va explicito porque el
# default de un QVBoxLayout lo pone el estilo del host y en macOS son 9 px.
WINDOW_MARGIN = 18

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
# El giro del icono mientras dura el escaneo. 24 ms por cuadro y 11 grados dan
# una vuelta cada ~0,8 s, que es la del prototipo.
RESCAN_SPIN_MS = 24
RESCAN_SPIN_STEP = 11.0

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
    ReadCellDelegate,
    READ_CELL_PADDING,
    PATH_CELL_LEFT,
    PATH_CELL_RIGHT,
    paint_row_separator,
    RelinkSearchWorker,
    ScannerWorker,
    TransparentTextDelegate,
    CopyWorker,
    DeleteWorker,
    ProgressWindow,
    expand_sequence,
    COL_PATH,
    COL_READ,
    COL_STATUS,
    COL_FOLDER_DELETE,
    COL_SEQUENCE,
    COL_NUM,
    READ_NONE,
)

# Importar SettingsWindow desde settings
from LGA_MediaManager_settings import SettingsWindow


def _rango_original(read_node_name):
    """
    (origfirst, origlast) de un Read, o None si no se pudo leer.

    Va envuelto en executeInMainThreadWithResult porque lo llama el WORKER del
    escaneo: `nuke.toNode` y `getValue` desde un hilo del pool no son
    thread-safe, y el sintoma tipico con un script grande es un cuelgue duro de
    Nuke, no un error.
    """

    def leer():
        nodo = nuke.toNode(read_node_name)
        if nodo is None:
            return None
        try:
            return (
                int(nodo["origfirst"].getValue()),
                int(nodo["origlast"].getValue()),
            )
        except Exception:
            return None

    try:
        return nuke.executeInMainThreadWithResult(leer)
    except Exception:
        return None


def read_sort_key(texto):
    """
    La clave de orden de la columna Read.

    Se ordena NUMERICO -Read2 antes que Read12- y las filas sin Read van al
    final. Por texto, "Read12" caia antes que "Read2" y las filas sin Read se
    mezclaban en el medio con las que si tienen.
    """
    nombres = [n.strip() for n in (texto or "").split(",") if n.strip()]
    nombres = [n for n in nombres if n != READ_NONE]
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
            paint_row_separator(painter, option.rect, Paleta.ROW_LINE)
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
        # El separador cruza tambien la celda de estado: en el prototipo la
        # linea es del RENGLON, no de cada celda, asi que se ve por encima del
        # bloque de color igual que sobre el fondo gris.
        paint_row_separator(painter, option.rect, Paleta.ROW_LINE)

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
        # El peso lo resuelve el modulo de estilo. El try/except que habia aca
        # caia en setBold(True) apenas el binding no expusiera `QFont.DemiBold`
        # pelado, y bold es 700: la cabecera salia un escalon mas pesada que
        # los 600 del disenio.
        return UIStyle.semibold(fuente)

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
        # La tanda en curso -copia o borrado- y su ventana. Se guardan para
        # que el worker no lo destruya Python mientras su run() esta saliendo.
        self._batch_worker = None
        self._batch_window = None
        self._delete_paths = []
        self._delete_total = 0
        self._copy_reapuntar = []
        # Los nodos que toco la tanda de relink. Se juntan y el Node Graph se
        # enfoca UNA vez al final: hacerlo por fila destruye la seleccion del
        # usuario N veces y abre N paneles de propiedades.
        self._relink_tocados = []
        self.relink_sin_nodo = []
        self._relink_cancelado = False
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

        # El worker del escaneo lo crea scan_project(), que es quien lo conecta
        # y lo arranca. Aca se creaba OTRO que nadie conectaba nunca: recorria
        # el disco entero y llamaba a la API de Nuke en paralelo con el bueno,
        # tiraba su resultado a la basura, y encima era el que la X de la
        # ventana de escaneo cancelaba, asi que cancelar no paraba el que
        # estaba llenando la tabla.
        self.scanner_worker = None

        # Asumimos que la inicialización es exitosa
        self.initialization_successful = True

        # Inicializar la UI
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        # El aire alrededor del contenido. Sin fijarlo, el margen lo pone el
        # estilo del host: en macOS son 9 px y la barra, la tabla y la leyenda
        # quedaban casi tocando el borde de la ventana, con la mitad del aire
        # que pide el disenio.
        self.layout.setContentsMargins(
            WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN
        )

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
        # El atajo NO se declara con un '&' en el texto. Qt lo dibuja
        # subrayando la letra adentro de la etiqueta, y el disenio ya escribe
        # el atajo entero al costado: quedaban las dos cosas a la vez, o sea
        # la misma informacion dos veces y un subrayado que el prototipo no
        # tiene. La letra la dispara un QShortcut de ventana, que hace
        # exactamente lo mismo sin tocar el texto.
        self.go_to_read_button = self._make_toolbar_button(
            "Go to Read", "scan", "Alt + G", TOOLTIPS["go_to_read"]
        )
        # Antes se llamaba Explorer, con atajo Alt+E. El nombre nuevo dice lo
        # que hace y la letra acompania: Alt+R.
        self.reveal_button = self._make_toolbar_button(
            "Reveal", "folder-open", "Alt + R", TOOLTIPS["reveal"]
        )
        self.relink_button = self._make_toolbar_button(
            "Relink", "link-2", "Alt + L", TOOLTIPS["relink"]
        )
        self.copy_button = self._make_toolbar_button(
            "Copy to…", "folder-input", "Alt + C", TOOLTIPS["copy_to"]
        )
        self.delete_button = self._make_toolbar_button(
            "Delete", "trash-2", "Alt + D", TOOLTIPS["delete"], peligro=True
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

        # Los atajos, ahora que el texto no lleva mnemonico. Van con
        # `animateClick` y no llamando al handler directo para que el boton se
        # ilumine igual que si lo hubieran clickeado, y un QShortcut sobre un
        # boton deshabilitado no dispara nada, que es la misma regla que tenia
        # el mnemonico.
        for boton, letra in (
            (self.go_to_read_button, "G"),
            (self.reveal_button, "R"),
            (self.relink_button, "L"),
            (self.copy_button, "C"),
            (self.delete_button, "D"),
        ):
            atajo = QShortcut(QKeySequence("Alt+%s" % letra), self)
            atajo.setContext(Qt.WidgetWithChildrenShortcut)
            atajo.activated.connect(
                lambda b=boton: b.animateClick() if b.isEnabled() else None
            )

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
        # La tabla NUNCA scrollea en horizontal. Si lo hiciera, el numero de
        # fila, el Read y el Status se irian de la vista junto con el path, y
        # esos tres tienen que estar siempre: son con lo que se decide que
        # hacer con la fila. El que scrollea es el path adentro de su columna,
        # con su propia barra. Ver path_scroll y fit_path_column.
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Ninguna columna se arrastra a mano. Se fija al armar y no al medir la
        # ventana: entre una cosa y la otra el usuario ya podia agarrar un
        # divisor.
        cabecera = self.table.horizontalHeader()
        cabecera.setStretchLastSection(False)
        for columna in (COL_PATH, COL_NUM, COL_READ, COL_STATUS):
            cabecera.setSectionResizeMode(columna, QHeaderView.Fixed)
        # Al reordenar hay que rehacer el '#': cuenta lo que se ve, de arriba
        # hacia abajo. Va por layoutChanged y no por sortIndicatorChanged
        # porque ese se emite ANTES de que Qt mueva las filas, y renumerar
        # sobre el orden viejo no sirve de nada.
        self.table.model().layoutChanged.connect(self.renumber_visible_rows)
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

        # La barra del path. Va afuera de la tabla y no adentro porque no
        # scrollea la tabla: scrollea UNA columna. La de adentro moveria
        # tambien el numero de fila, el Read y el Status, que son con lo que se
        # decide que hacer con la fila y tienen que estar siempre a la vista.
        # Aparece sola cuando el path mas largo no entra en su columna.
        self.path_scroll = QScrollBar(Qt.Horizontal, self)
        self.path_scroll.setToolTip(TOOLTIPS["path_scroll"])
        self.path_scroll.hide()
        self.path_scroll.valueChanged.connect(self._scroll_path)
        self.layout.addWidget(self.path_scroll)

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

        # La columna Read tambien tiene delegado propio: va alineada a la
        # IZQUIERDA y en el gris de cuerpo -el item pelado la centraba y la
        # dibujaba en el gris fuerte-, y las filas sin Read muestran una raya
        # y no el guion corto que el modelo usa de centinela.
        self.read_delegate = ReadCellDelegate(self.table, self.UI, self.font_size)
        self.table.setItemDelegateForColumn(COL_READ, self.read_delegate)

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
        # La fuente del pack, DESPUES de armar: asi alcanza tambien a los hijos
        # que ya existen. Sin esto la ventana se dibuja con la del host y el
        # `font-weight: 600` de las hojas no encuentra una cara real, con lo
        # que macOS sintetiza la negrita y TODO el texto de la ventana sale
        # con el peso -y el ancho- de una 700 falsa.
        UIStyle.apply_ui_font(self)
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

        El cartel del atajo va en un QLabel gris adentro del layout del boton.
        NO sale de un mnemonico: en Qt el '&' subraya la letra dentro de la
        etiqueta pero no imprime "Alt + G" al costado, asi que declararlo
        dejaba las dos cosas a la vez -el subrayado y el cartel- o sea la
        misma informacion dos veces, y un subrayado que el disenio no tiene.
        La letra la dispara un QShortcut de ventana, que hace lo mismo sin
        tocar el texto.

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

    @staticmethod
    def _estilo_atajo(atajo_label, habilitado, Paleta):
        """
        La hoja del cartel "Alt + X" de un boton de la barra.

        Sale a un metodo porque la escriben dos: apply_toolbar_stylesheet -que
        la necesita ANTES de medir el ancho del boton- y refresh_toolbar_icons,
        que corre cada vez que cambia la seleccion. Escrita en una sola de las
        dos, el color quedaba viejo apenas el boton se prendia o se apagaba.

        Va sin peso propio: en 600 competia con la etiqueta del boton, que es
        lo que hay que leer primero. Y se apaga JUNTO con el boton: el disenio
        atenua el boton entero cuando esta deshabilitado, asi que ahi el atajo
        queda mas oscuro todavia que en reposo, no clavado en el mismo gris.
        """
        atajo_label.setStyleSheet(
            "QLabel { color: %s; font-size: %dpx; font-weight: normal;"
            " background: transparent; border: none; }"
            % (
                Paleta.TEXT_DIM if habilitado else Paleta.TEXT_DISABLED,
                TOOLBAR_SHORTCUT_FONT_SIZE,
            )
        )

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
                self._estilo_atajo(atajo_label, boton.isEnabled(), Paleta)
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
                " %(semibold)s"
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
                    "semibold": UIStyle.semibold_css(),
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
            habilitado = datos["boton"].isEnabled()
            if datos["peligro"]:
                # El unico icono con color propio: Delete es el que no se
                # puede deshacer. Apagado NO pasa al gris: el prototipo atenua
                # el boton entero y el tacho sigue leyendose rojo, que es lo
                # que hace que Delete se distinga del resto de la fila incluso
                # cuando no hay nada seleccionado. Pintandolo de TEXT_DIM se
                # volvia un boton mas.
                color = Paleta.DANGER_ICON if habilitado else Paleta.DANGER_ICON_DIM
            elif not habilitado:
                color = Paleta.TEXT_DISABLED
            else:
                color = Paleta.TEXT
            datos["icono_label"].setPixmap(
                tinted_icon(datos["icono"], color, TOOLBAR_ICON_SIZE).pixmap(
                    TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE
                )
            )
            # El cartel del atajo baja de intensidad con el boton, y este
            # metodo es el que corre en cada cambio de seleccion.
            if datos["atajo_label"] is not None:
                self._estilo_atajo(datos["atajo_label"], habilitado, Paleta)

    def update_minimum_width(self):
        """
        Lo mas angosta que puede quedar la ventana: lo que mide la barra.

        Manda SOLO la barra de herramientas. Es la unica fila que de verdad no
        se puede achicar: son seis botones de ancho fijo que no envuelven, y si
        no entran el ultimo -justamente el de los ajustes- se va de la vista.

        El pie ya NO cuenta. Contaba, y era la fila mas ancha de las dos por
        varios cientos de pixeles, asi que la ventana no bajaba de ahi aunque
        la tabla entrara comoda: el minimo lo fijaba una leyenda que es texto
        de ayuda. Ahora la leyenda se adapta -ver fit_footer_legend- y deja de
        ser un piso.
        """
        if not getattr(self, "toolbar_buttons", None):
            return
        ancho = sum(datos["boton"].width() for datos in self.toolbar_buttons)
        # Los cinco espacios entre botones, mas el del separador.
        ancho += BUTTON_SPACING * (len(self.toolbar_buttons) + 1)
        ancho += 1  # el separador vertical

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
        El ancho que necesita el pie con las explicaciones puestas.

        No es un minimo de la ventana: es el umbral a partir del cual la
        leyenda tiene que dejar de mostrar las explicaciones. Se mide sobre los
        labels y no con el sizeHint del layout porque el pie se arma antes de
        que la ventana tenga geometria, y ahi el layout todavia no sabe cuanto
        mide.
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

    def fit_footer_legend(self):
        """
        Esconde las explicaciones de la leyenda cuando no entran.

        Con la ventana angosta la alternativa era cortar cada frase a la mitad
        de una palabra ("File is outside the sho..."), que es peor que no
        mostrarla: el punto de color y el nombre del estado solos ya dicen lo
        mismo, y la explicacion es texto de ayuda que se lee una vez.

        Es lo que le permite a la ventana achicarse: antes esta fila era la mas
        ancha de todas y fijaba el minimo de la ventana entera.
        """
        # Alcanza con mirar la leyenda: se arma despues del layout raiz, asi
        # que si hay entradas, self.layout ya es el QVBoxLayout y no el metodo
        # layout() de QWidget, que es lo que devolveria un getattr temprano.
        entradas = getattr(self, "legend_entries", None)
        if not entradas:
            return
        margenes = self.layout.contentsMargins()
        disponible = self.width() - margenes.left() - margenes.right()
        # El umbral se mide con sizeHint(), que un label escondido sigue
        # informando igual: asi no se mueve al esconderlo y no hay parpadeo
        # entre mostrar y esconder alrededor del limite.
        mostrar = disponible >= self.footer_minimum_width()
        for entrada in entradas:
            if entrada["texto"].isVisible() != mostrar:
                entrada["texto"].setVisible(mostrar)

    def resizeEvent(self, event):
        super(FileScanner, self).resizeEvent(event)
        self.fit_footer_legend()
        # El path NO se ajusta aca: lo hace el filtro de eventos del viewport,
        # que es el unico lugar donde ya se sabe cuanto mide.

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
        # Solo toma el foco si lo clickean. Es el primer widget enfocable de
        # la ventana, asi que Qt se lo daba al abrir y el campo aparecia con
        # su anillo violeta puesto sin que nadie lo hubiera tocado: la ventana
        # abria pareciendo que el usuario ya estaba escribiendo un filtro.
        self.search_field.setFocusPolicy(Qt.ClickFocus)
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
                "QLabel { color: %s; font-size: %dpx; %s"
                " background: transparent; border: none; }"
                % (Paleta.TEXT_STRONG, PILL_FONT_SIZE, UIStyle.semibold_css())
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
        Crea las celdas de la columna '#' y les deja su orden de CARGA.

        Ese orden va en Qt.UserRole y es lo que se ordena al clickear la
        columna: asi '#' devuelve la tabla al orden en que se cargo. Lo que se
        MUESTRA no es ese numero sino la posicion visual, que la escribe
        renumber_visible_rows() cada vez que la tabla se reordena o se filtra.
        Se corre con el orden apagado, antes del primer sortByColumn.
        """
        if getattr(self, "table", None) is None:
            return
        Paleta = (getattr(self, "UI", None) or UIStyle.theme(None)).Color
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_NUM)
            if item is None:
                # SortKeyItem para que ordene por la clave y no por el texto:
                # por texto, "10" caia antes que "9".
                item = SortKeyItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, COL_NUM, item)
            item.setData(Qt.UserRole, row + 1)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QBrush(QColor(Paleta.TEXT_DIM)))
        self.renumber_visible_rows()

    def renumber_visible_rows(self):
        """
        Deja la columna '#' leyendose 1, 2, 3... de arriba hacia abajo.

        La numeracion es de lo que se VE: arranca siempre en 1 y no salta, sin
        importar por que columna se este ordenando ni cuantas filas escondio el
        filtro. Antes el numero era un id fijo de carga, y ordenando por
        cualquier otra columna la primera fila podia decir 31 y la siguiente
        42, que se lee como si faltaran filas.

        El orden de carga NO se pierde: sigue en Qt.UserRole, que es por donde
        ordena la propia columna '#'.
        """
        if getattr(self, "table", None) is None:
            return
        # Escribir en las celdas con el orden prendido dispara otra pasada de
        # ordenamiento, que vuelve a llamar aca: sin el guard es un bucle.
        if getattr(self, "_renumerando", False):
            return
        self._renumerando = True
        try:
            visible = 0
            for row in range(self.table.rowCount()):
                if self.table.isRowHidden(row):
                    continue
                visible += 1
                item = self.table.item(row, COL_NUM)
                if item is not None:
                    item.setText(str(visible))
        finally:
            self._renumerando = False

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
        # El '#' cuenta lo que se VE: al esconder filas los numeros se corren.
        self.renumber_visible_rows()
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
                # El ancho del path se recalcula ACA y no en el resizeEvent de
                # la ventana. Qt le entrega el resize al padre ANTES de
                # reacomodar a los hijos, asi que ahi el viewport todavia mide
                # lo de antes: la columna se quedaba con el minimo y sobraba
                # media ventana vacia a la derecha. Este evento llega cuando el
                # viewport ya tiene su tamano nuevo.
                self.fit_path_column()
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
                "QLabel { color: %s; font-size: %dpx; %s"
                " background: transparent; }"
                % (Paleta.TEXT_STRONG, PILL_FONT_SIZE, UIStyle.semibold_css())
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
                " %(semibold)s"
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
                    "semibold": UIStyle.semibold_css(),
                }
            )
            color_icono = (
                Paleta.TEXT if self.rescan_button.isEnabled() else Paleta.TEXT_DIM
            )
            self.rescan_icon.setStyleSheet(
                "QLabel { background: transparent; border: none; }"
            )
            # El pixmap base se guarda: es el que rota el giro del escaneo.
            self._rescan_pixmap = tinted_icon(
                "refresh-cw", color_icono, RESCAN_ICON_SIZE
            ).pixmap(RESCAN_ICON_SIZE, RESCAN_ICON_SIZE)
            self.rescan_icon.setPixmap(self._rescan_pixmap)
            self.rescan_button.setFixedWidth(self.rescan_button.sizeHint().width())
            # Repintar con el tema nuevo resetea el dibujo a la posicion cero;
            # si el escaneo sigue corriendo, el giro se retoma solo.
            if getattr(self, "_rescan_timer", None) is not None:
                self._pintar_rescan()

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

    # ----------------------------------------------------------------------
    #                       El giro del icono de Rescan
    # ----------------------------------------------------------------------
    # Gira mientras dura el escaneo, no un tiempo fijo: es lo unico que dice
    # que la herramienta esta haciendo algo. El prototipo lo anima por CSS;
    # aca el icono es un pixmap adentro de un QLabel, asi que se redibuja
    # rotado en cada tick.

    def _spin_rescan(self, girando):
        """Prende y apaga el giro del icono."""
        if getattr(self, "rescan_icon", None) is None:
            return
        timer = getattr(self, "_rescan_timer", None)
        if girando:
            if timer is not None:
                return
            self._rescan_angle = 0.0
            self._rescan_timer = QTimer(self)
            self._rescan_timer.timeout.connect(self._girar_rescan)
            self._rescan_timer.start(RESCAN_SPIN_MS)
            return
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            self._rescan_timer = None
        self._rescan_angle = 0.0
        self._pintar_rescan()

    def _girar_rescan(self):
        self._rescan_angle = (
            getattr(self, "_rescan_angle", 0.0) + RESCAN_SPIN_STEP
        ) % 360.0
        self._pintar_rescan()

    def _pintar_rescan(self):
        """
        Dibuja el icono rotado sobre un pixmap del MISMO tamano.

        No se usa QPixmap.transformed(): esa agranda la caja para que entre el
        rectangulo rotado, asi que el icono cambiaria de tamano en cada tick y
        el boton se movería con el. Rotando el painter alrededor del centro, la
        caja no se toca.
        """
        base = getattr(self, "_rescan_pixmap", None)
        if base is None or base.isNull():
            return
        angulo = getattr(self, "_rescan_angle", 0.0)
        if not angulo:
            self.rescan_icon.setPixmap(base)
            return
        escala = base.devicePixelRatio() or 1.0
        lado = base.width() / escala
        salida = QPixmap(base.size())
        salida.setDevicePixelRatio(escala)
        salida.fill(Qt.transparent)
        painter = QPainter(salida)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.translate(lado / 2.0, lado / 2.0)
        painter.rotate(angulo)
        painter.translate(-lado / 2.0, -lado / 2.0)
        painter.drawPixmap(0, 0, base)
        painter.end()
        self.rescan_icon.setPixmap(salida)

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
        # Tampoco con una copia, un borrado o un relink en curso: el Rescan
        # vacia la tabla y la operacion termina buscando filas que ya no
        # existen.
        if self.operacion_en_curso() is not None:
            debug_print("Hay una operacion en curso: se ignora el Rescan")
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
        """El o los nodos Read de una fila. READ_NONE cuando no hay ninguno."""
        item = self.table.item(row, COL_READ)
        return item.text() if item is not None else READ_NONE

    def row_status(self, row):
        """El estado de una fila: Offline, Outside, Unused u Online."""
        item = self.table.item(row, COL_STATUS)
        return item.text() if item is not None else ""

    def find_row_by_path(self, ruta):
        """
        La fila cuya ruta es EXACTAMENTE esta, o None.

        Por igualdad y no por `ruta_a in ruta_b`: la subcadena tomaba
        cualquier fila cuyo path fuera prefijo de otro, y las tandas guardan
        rutas justamente para poder volver a encontrar SU fila despues de que
        la tabla se reordeno.
        """
        for fila in range(self.table.rowCount()):
            celda = self.table.item(fila, COL_PATH)
            if celda is not None and celda.text() == ruta:
                return fila
        return None

    def focus_nodes(self, nodos):
        """
        Deja seleccionados en el Node Graph los nodos que toco la operacion.

        Se llama UNA vez por tanda, nunca por fila: con seis filas
        seleccionadas, hacerlo adentro del bucle destruia la seleccion del
        usuario seis veces y apilaba seis paneles de propiedades.
        """
        if not nodos:
            return
        nuke.selectAll()
        nuke.invertSelection()
        for nodo in nodos:
            nodo.setSelected(True)
        nuke.zoomToFitSelected()
        # El panel solo con uno: con varios serian varios paneles apilados.
        if len(nodos) == 1:
            nodos[0].showControlPanel()

    def operacion_en_curso(self):
        """
        Que hay corriendo ahora mismo, o None.

        Las tres operaciones se excluyen entre si y no solo cada una de si
        misma: la ventana de progreso no es modal, asi que con un relink
        recorriendo un servidor nada impedia apretar Delete y mandar a la
        papelera justo el archivo al que el relink iba a apuntar.
        """
        if getattr(self, "_scan_running", False):
            return "scan"
        if getattr(self, "_batch_worker", None) is not None:
            return "batch"
        if getattr(self, "relink_worker", None) is not None or self.relink_queue:
            return "relink"
        return None

    def row_read_names(self, row):
        """Los nombres de nodo de una fila, ya separados y sin el centinela."""
        texto = self.row_read(row)
        if not texto or texto == READ_NONE:
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

        # Con algo corriendo la barra se apaga entera. Antes los botones
        # quedaban prendidos y el guard de adentro de cada handler se limitaba
        # a un debug_print: el usuario apretaba y no pasaba nada, sin ninguna
        # explicacion.
        if self.operacion_en_curso() is not None:
            for datos in self.toolbar_buttons:
                datos["boton"].setEnabled(False)
            self.refresh_toolbar_icons()
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
        # La grilla de Qt se apaga entera. Dibujaba lineas VERTICALES entre
        # columnas, que el disenio no tiene -las columnas se separan por el
        # espacio y por el bloque de color de Status-, y ademas pintaba las
        # horizontales con su gris propio, MAS OSCURO que la fila: el disenio
        # las quiere mas CLARAS, un divisor que suma en vez de una reja negra.
        #
        # La linea horizontal que SI va la dibuja cada delegado, con
        # paint_row_separator. Por hoja de estilo no se puede: la regla
        # `QTableWidget::item { border-bottom }` se aplica pero no se ve,
        # porque las cuatro columnas tienen delegado propio y pintan la celda
        # entera ellos, tapandola.
        self.table.setShowGrid(False)
        if getattr(self, "path_scroll", None) is not None:
            # La misma barra fina del pack, sobre el fondo de la ventana: vive
            # afuera de la caja de la tabla, no adentro.
            self.path_scroll.setStyleSheet(UI.Style.SCROLLBAR)
        self.table.setStyleSheet(
            (
                # La tabla es una caja con borde y esquinas redondeadas, igual
                # que la de la ventana de ajustes. Sin esto quedaba un
                # rectangulo al ras, sin borde y con las esquinas rectas.
                "QTableWidget { background-color: %(surface)s;"
                " font-size: %(letra)dpx;"
                " border: 1px solid %(borde)s;"
                " border-radius: %(radio)dpx; }"
                # La seleccion se deja transparente a proposito: si la hoja
                # define un background para 'item:selected' le gana al
                # setBackground() del item y a la paleta del delegado, y la
                # columna Status pierde su color justo cuando esta
                # seleccionada. De eso se encarga TransparentTextDelegate, que
                # sabe que celdas tienen color propio.
                "QTableWidget::item:selected { background-color: transparent; }"
                % {
                    "surface": UI.Color.SURFACE,
                    "letra": self.font_size,
                    "borde": UI.Color.BORDER,
                    "radio": UIStyle.Metric.RADIUS_CARD,
                }
            )
            # La barra de scroll del pack: fina, redondeada y sin flechas. Sin
            # esto la tabla se quedaba con la nativa de macOS, del doble de
            # ancho, con botones de flecha arriba y abajo y con el patron de
            # puntitos en el pulgar.
            + UI.Style.SCROLLBAR
            # El riel va transparente: la hoja comun lo pinta del gris de
            # VENTANA, que adentro de la caja de la tabla dibuja una franja
            # oscura al costado de todas las filas. La horizontal aparece
            # cuando el path mas largo no entra, asi que necesita lo mismo.
            + "QScrollBar:vertical, QScrollBar:horizontal"
            " { background: transparent; }"
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
        # El path se dibuja con la letra derivada de esta, asi que lo que medi
        # antes ya no vale: se descarta para que se vuelva a medir.
        self._path_width = None
        # El alto de la cabecera tambien se deriva del tamano: fs + 25.
        if getattr(self, "header", None) is not None:
            self.header.set_font_size(tamano)
        # El path lo dibuja el delegado con su propia fuente -un punto mas
        # grande que el resto de la tabla-, asi que la hoja no lo alcanza.
        self.refresh_path_delegate()
        # La columna Read tambien se dibuja a mano, con la letra un punto mas
        # chica: sin avisarle, se quedaba con el tamano y el tema anteriores.
        if getattr(self, "read_delegate", None) is not None:
            self.read_delegate.set_theme(self.UI, tamano)

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
        # Los dos delegados que dibujan texto a mano no los alcanza la hoja:
        # sin avisarles, se quedan con los colores del tema anterior.
        if getattr(self, "read_delegate", None) is not None:
            self.read_delegate.set_theme(self.UI, self.font_size)
        if getattr(self, "status_delegate", None) is not None:
            self.status_delegate.set_theme(self.UI)
        tamano = self.appearance.get(
            "table_font_size", UIStyle.Metric.TABLE_FONT_SIZE
        )
        self.table_font_size = max(
            UIStyle.Metric.TABLE_FONT_SIZE_MIN,
            min(UIStyle.Metric.TABLE_FONT_SIZE_MAX, int(tamano)),
        )
        self.update_table_font_size(self.table_font_size)

    def nk_dir(self):
        """
        La carpeta del .nk abierto, contra la que se resuelve todo.

        Cacheada: la llama tambien el worker del escaneo -por
        resolve_shot_folder- y nuke.root() desde un hilo del pool no es
        thread-safe. El valor se refresca en refresh_nk_dir(), que corre en el
        hilo principal antes de arrancar cada escaneo; el .nk no cambia de
        nombre en el medio de uno.
        """
        cacheado = getattr(self, "_nk_dir", None)
        if cacheado is None:
            cacheado = self.refresh_nk_dir()
        return cacheado

    def refresh_nk_dir(self):
        """Relee la carpeta del .nk. Solo desde el hilo principal."""
        project_path = nuke.root().name()
        self._nk_dir = os.path.dirname(project_path) if project_path else ""
        return self._nk_dir

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

    def closeEvent(self, event):
        """
        Al cerrar la ventana se corta TODO lo que este corriendo.

        Sin esto, cerrar el Media Manager con un borrado de tres mil frames en
        curso dejaba al worker mandando archivos a la papelera sin nada que lo
        mostrara ni forma de pararlo: la ventana de progreso es hija de esta y
        desaparecia con ella.
        """
        for atributo in ("_batch_worker", "relink_worker", "scanner_worker"):
            worker = getattr(self, atributo, None)
            if worker is not None:
                try:
                    worker.cancel()
                except (RuntimeError, AttributeError):
                    pass
        # La bandera hace falta ademas de vaciar la cola, por lo mismo que en
        # _cancel_relink: el worker cortado emite finished("") y eso es
        # indistinguible de "no lo encontre". Sin marcarla, cerrar el Media
        # Manager durante un relink terminaba abriendo un cartel de
        # "File not found." sobre una ventana que el usuario ya habia cerrado.
        self._relink_cancelado = True
        self.relink_queue = []
        self.relink_missing = []
        self.relink_sin_nodo = []
        self._relink_tocados = []
        super(FileScanner, self).closeEvent(event)

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

        # Los cuatro anchos los decide la herramienta: '#' es fijo, Read y
        # Status se miden sobre su contenido y el path se lleva el resto. No se
        # llama a resizeColumnsToContents: lo que devolveria se pisa entero dos
        # lineas mas abajo, y en una tabla de miles de filas no es gratis.
        self.apply_column_widths()

        # El ancho sale de que entre el path MAS LARGO sin cortarse. Se lo pone
        # a la columna antes de sumar, si no se estaria midiendo el ancho que
        # la columna tenia de antes.
        self.table.setColumnWidth(COL_PATH, self.path_column_width(recalcular=True))
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
            widget = item.widget()
            if widget is self.table:
                continue
            # Lo escondido no ocupa lugar. La barra del path esta oculta
            # mientras el path mas largo entre en su columna, pero su sizeHint
            # sigue informando alto: sumarlo dejaba la ventana con una franja
            # vacia abajo justo en el caso normal.
            if widget is not None and widget.isHidden():
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

        # El ancho tiene el MISMO tope que el alto: 80% de la pantalla. Sin el,
        # un path largo abria la ventana mas ancha que el monitor y no se podia
        # ni mover. Cortada ahi, el path no se recorta: la columna conserva lo
        # que necesita y aparece el scroll horizontal.
        max_width = int(
            QApplication.primaryScreen().geometry().width() * WINDOW_MAX_SCREEN_RATIO
        )
        final_width = min(width, max_width)
        # El minimo de la ventana -que lo pone la barra de herramientas- manda
        # sobre el tope: si la barra no entra en el 80%, la ventana no puede
        # ser mas angosta que ella igual.
        final_width = max(final_width, self.minimumWidth())
        self.logger.debug(
            "[Ancho] Pedido %d, tope 80%% %d, minimo %d, final %d"
            % (width, max_width, self.minimumWidth(), final_width)
        )

        # Usar el menor entre la altura calculada y el maximo permitido
        final_height = min(height, max_height)
        # Cuando el tope recorta, el alto que queda no cae en un limite de
        # fila y la ultima entra a medias: una franja de media fila contra el
        # pie. Se le saca el sobrante para que el area de filas cierre en un
        # multiplo exacto del alto de fila, que es lo que hace el disenio.
        # Solo cuando el tope recorto: si la ventana entra entera, el alto ya
        # es la suma exacta de las filas.
        if height > max_height:
            alto_fila = self.table.verticalHeader().defaultSectionSize()
            # Todo lo que en `height` no son filas: cabecera, pastillas,
            # barra, pie, margenes y espaciados.
            alto_sin_filas = height - sum(
                self.table.rowHeight(i) for i in range(self.table.rowCount())
            )
            if alto_fila > 0:
                sobra = int(final_height - alto_sin_filas) % alto_fila
                if 0 < sobra < final_height:
                    final_height -= sobra
                    self.logger.debug(
                        f"[Altura] Recorte para cerrar en fila entera: {sobra}"
                    )
        self.logger.debug(f"[Altura] Alto final aplicado: {final_height}")
        self.logger.debug(f"[Altura] El limite maximo recorto el alto: {height > max_height}")

        # La que crece es File Path y NO la ultima. Con la ultima, el bloque de
        # color de Status crecia hasta el borde de la ventana y el path -que es
        # lo largo y lo que se lee- quedaba cortado con el resto vacio al lado.
        #
        # NINGUNA columna se arrastra a mano: las cuatro van en Fixed, que
        # bloquea al usuario pero deja que setColumnWidth siga valiendo. Los
        # anchos los decide la herramienta -tres medidos sobre su contenido y
        # el path con todo el sobrante-, asi que un arrastre solo podia
        # desarmar eso y dejar huecos.
        #
        # Stretch tampoco sirve para el path: llena el viewport SIEMPRE, o sea
        # que al achicar la ventana encoge la columna y recorta el path sin
        # ofrecer forma de llegar al final. El ancho lo pone fit_path_column y
        # lo que no entra lo cubre la barra del path.
        encabezado = self.table.horizontalHeader()
        encabezado.setStretchLastSection(False)
        for columna in (COL_PATH, COL_NUM, COL_READ, COL_STATUS):
            encabezado.setSectionResizeMode(columna, QHeaderView.Fixed)

        # Ajustar el tamano de la ventana
        self.resize(final_width, final_height)
        # Explicito y no solo por resizeEvent: si el alto y el ancho que se
        # acaban de pedir son los que la ventana ya tenia, Qt no emite resize
        # y la columna del path se quedaria con el ancho de la medicion en vez
        # del que le toca en pantalla.
        self.fit_path_column()
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
        Los anchos de las columnas que no son el path.

        Read y Status se MIDEN: son las dos columnas cuyo contenido se conoce
        entero -"Read15", "Offline"- asi que un ancho a ojo solo puede sobrar.
        Y lo que sobra ahi se lo saca al path, que es la unica que de verdad
        necesita lugar.
        """
        if getattr(self, "table", None) is None:
            return
        self.table.setColumnWidth(COL_NUM, COL_NUM_WIDTH)
        self.table.setColumnWidth(COL_READ, self.read_column_width())
        self.table.setColumnWidth(COL_STATUS, self.status_column_width())

    def read_column_width(self):
        """Lo que mide el Read mas largo, con el aire de la celda."""
        if getattr(self, "table", None) is None:
            return COL_READ_MIN_WIDTH
        fuente = QFont(self.table.font())
        fuente.setPixelSize(max(1, self.font_size - 1))
        metrica = QFontMetrics(fuente)
        ancho = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_READ)
            if item is not None:
                ancho = max(ancho, horizontal_advance(metrica, item.text()))
        # El mismo padding a los dos lados que usa ReadCellDelegate, mas la
        # perilla de ajuste fino.
        return max(
            COL_READ_MIN_WIDTH,
            ancho + READ_CELL_PADDING * 2 + COL_READ_EXTRA,
        )

    def status_column_width(self):
        """
        Lo que mide el estado mas largo, con su punto y sus paddings.

        Se mide sobre los CUATRO estados y no sobre los que haya cargados: si
        no, la columna cambiaba de ancho segun lo que el escaneo encontrara.
        """
        fuente = QFont(self.table.font()) if getattr(self, "table", None) else QFont()
        fuente.setPixelSize(max(1, self.font_size - 1))
        metrica = QFontMetrics(fuente)
        texto = max(
            (horizontal_advance(metrica, estado) for estado in STATUS_ORDER),
            default=0,
        )
        ancho = (
            STATUS_CELL_PADDING * 2
            + STATUS_DOT_SIZE
            + STATUS_CELL_GAP
            + texto
            + COL_STATUS_EXTRA
        )
        return max(COL_STATUS_MIN_WIDTH, ancho)

    # ----------------------------------------------------------------------
    #                       Ancho de la columna del path
    # ----------------------------------------------------------------------
    # La politica es: la ventana abre con el ancho JUSTO para que entre el path
    # mas largo sin cortarse, y si eso pasa el 80% del ancho de la pantalla se
    # corta ahi. Pero cortada la ventana, el path NO se recorta: la columna
    # conserva el ancho que necesita y aparece el scroll horizontal, porque no
    # poder leer un path completo es justamente lo que esta herramienta viene a
    # resolver.

    def path_column_width(self, recalcular=False):
        """
        Lo que mide el path MAS LARGO de la tabla, dibujado como se dibuja.

        Se mide con la fuente del delegado -un punto mas grande que el resto de
        la tabla- y no con la de la tabla: con la chica el calculo daba de
        menos y el path mas largo terminaba cortado igual.

        El resultado se cachea. Recorrer miles de filas midiendo texto es
        barato una vez y caro en cada resize, que es de donde se llama.
        """
        if getattr(self, "table", None) is None:
            return COL_PATH_MIN_WIDTH
        if not recalcular and getattr(self, "_path_width", None) is not None:
            return self._path_width

        fuente = QFont(self.table.font())
        fuente.setPixelSize(self.font_size + UIStyle.Metric.PATH_FONT_OFFSET)
        metrica = QFontMetrics(fuente)
        ancho = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_PATH)
            if item is None:
                continue
            ancho = max(ancho, horizontal_advance(metrica, item.text()))
        # El aire que el delegado usa de los dos lados sin dibujar texto.
        ancho += PATH_CELL_LEFT + PATH_CELL_RIGHT
        self._path_width = max(COL_PATH_MIN_WIDTH, ancho)
        return self._path_width

    def fit_path_column(self):
        """
        El path ocupa TODO el sobrante, y si no le alcanza, se scrollea el.

        La columna nunca se pasa del viewport: la tabla no tiene scroll
        horizontal, asi que el numero de fila, el Read y el Status quedan
        siempre a la vista. Cuando el path mas largo no entra en lo que le
        toca, la diferencia la cubre `path_scroll`, una barra que corre el
        dibujo del path adentro de su propia columna.
        """
        if getattr(self, "table", None) is None:
            return
        otras = (
            COL_NUM_WIDTH
            + self.table.columnWidth(COL_READ)
            + self.table.columnWidth(COL_STATUS)
        )
        sobrante = max(COL_PATH_VIEW_MIN, self.table.viewport().width() - otras)
        self.table.setColumnWidth(COL_PATH, sobrante)

        barra = getattr(self, "path_scroll", None)
        if barra is None:
            return
        faltante = max(0, self.path_column_width() - sobrante)
        barra.setRange(0, faltante)
        barra.setPageStep(max(1, sobrante))
        barra.setSingleStep(PATH_SCROLL_STEP)
        # La barra solo existe cuando hay algo que alcanzar. Con rango cero
        # seria un riel muerto debajo de la tabla.
        barra.setVisible(faltante > 0)
        if not faltante:
            barra.setValue(0)

    def _scroll_path(self, valor):
        """Corre el dibujo del path y repinta solo lo que se ve."""
        delegado = getattr(self, "path_delegate", None)
        if delegado is not None and delegado.set_offset(valor):
            self.table.viewport().update()

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

        # Una operacion por vez, y contra TODAS: con una copia o un borrado
        # en curso, el relink termina reapuntando Reads a archivos que la otra
        # tanda esta moviendo o mandando a la papelera.
        if self.operacion_en_curso() is not None:
            debug_print("Hay una operacion en curso: se ignora el Relink")
            return

        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not directory:
            return

        self.relink_directory = directory
        self._relink_cancelado = False
        self.relink_queue = [self.row_path(fila) for fila in filas]
        self.relink_queue = [ruta for ruta in self.relink_queue if ruta]
        self.relink_missing = []
        self.relink_sin_nodo = []
        self._relink_tocados = []
        self.update_button_states()
        self._relink_next()

    def _relink_next(self):
        """Arranca la busqueda del proximo archivo de la tanda, si queda alguno."""
        if self.relink_queue:
            ruta = self.relink_queue.pop(0)
            try:
                self.search_file_in_directory(self.relink_directory, ruta)
                return
            except Exception as problema:
                # Si armar la busqueda falla, la tanda se corta pero no se
                # queda colgada: con la cola llena, Relink no se podia volver
                # a apretar nunca. Y NO se vuelve con un return: hay que pasar
                # por el cierre de abajo, que es el que vuelve a prender la
                # barra de herramientas.
                debug_print("No se pudo buscar %s: %s" % (ruta, problema))
                self.relink_queue = []
                self.relink_missing = []
                self.relink_sin_nodo = []

        # Terminada la tanda: el Node Graph se enfoca UNA vez, con todo lo que
        # se toco, y el aviso sale UNA vez, en vez de un cartel por archivo que
        # habria que cerrar de a uno.
        self.focus_nodes(self._relink_tocados)
        self._relink_tocados = []
        self.update_button_states()

        faltantes = self.relink_missing
        sin_nodo = self.relink_sin_nodo
        self.relink_missing = []
        self.relink_sin_nodo = []
        partes = []
        if faltantes:
            if len(faltantes) == 1:
                partes.append("File not found.")
            else:
                partes.append(
                    "%d files were not found:\n%s"
                    % (len(faltantes), "\n".join(faltantes[:12]))
                )
        # Encontrar el archivo y no tener a que apuntarlo tambien hay que
        # decirlo: antes ese caso no hacia nada y no avisaba nada, asi que el
        # usuario esperaba la busqueda entera para no enterarse de nada.
        if sin_nodo:
            partes.append(
                "%d file(s) were found but have no Read node to update:\n%s"
                % (len(sin_nodo), "\n".join(sin_nodo[:12]))
            )
        if partes:
            QMessageBox.information(self, "Relink", "\n\n".join(partes))

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
        self.relink_loading_window = ProgressWindow("Searching...", self)
        self.center_window(self.relink_loading_window)
        # La X corta la busqueda Y la tanda entera: cancelar una sola de N
        # busquedas y seguir con la siguiente no es lo que nadie espera de una
        # cruz. La barra va indeterminada porque un os.walk no sabe cuanto le
        # falta hasta que termina.
        self.relink_loading_window.progressBar.setRange(0, 0)
        self.relink_loading_window.cancelled.connect(self._cancel_relink)
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

    def _cancel_relink(self):
        """Corta la busqueda en curso y descarta lo que quedaba de la tanda."""
        # La bandera hace falta aparte de vaciar la cola: el worker cortado
        # emite `finished("")`, que es lo mismo que emite cuando no encontro el
        # archivo. Sin distinguirlas, cancelar terminaba abriendo un cartel de
        # "File not found." justo despues de apretar la X.
        self._relink_cancelado = True
        if self.relink_worker is not None:
            self.relink_worker.cancel()
        self.relink_queue = []
        self.relink_missing = []

    def on_relink_search_finished(self, file_name, found_path):
        """Aplica el resultado de la busqueda. Corre en el hilo principal."""
        self.relink_worker = None

        # El walk puede tardar minutos: si el usuario cerro la ventana mientras
        # tanto, los widgets ya no existen del lado de C++ aunque Python siga
        # teniendo la referencia viva por el lambda de la conexion.
        try:
            if self.relink_loading_window is not None:
                self.relink_loading_window.close()
                # deleteLater y no solo close: es hija del Media Manager, asi
                # que sin esto se acumula una ventana escondida por busqueda.
                self.relink_loading_window.deleteLater()
                self.relink_loading_window = None

            if getattr(self, "_relink_cancelado", False):
                # Cancelado: ni se aplica el resultado ni se acumula como
                # faltante ni se sigue con el proximo de la tanda.
                self._relink_cancelado = False
                self._relink_tocados = []
                self.update_button_states()
                return

            if found_path:
                tocados, con_nodo = self.update_read_node(file_name, found_path)
                self._relink_tocados.extend(tocados)
                if not con_nodo:
                    self.relink_sin_nodo.append(os.path.basename(file_name))
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
            self.relink_sin_nodo = []
            self._relink_tocados = []
            return

        self._relink_next()

    def update_read_node(self, original_file_name, new_file_path):
        """
        Aplica a su fila el archivo que encontro la busqueda del relink.

        Devuelve (nodos_tocados, hubo_nodo). Los nodos los enfoca quien llama,
        una sola vez al final de la tanda.

        Reapunta TODOS los Reads de la fila, no el primero. La celda de Reads
        se arma con ", ".join(nodes), asi que en una fila con dos nodos el
        texto es "Read1, Read2": pasarselo entero a nuke.toNode() devuelve
        None y el bloque entero se salteaba. Con eso, ni se reapuntaba el
        nodo, ni se actualizaba el path de la tabla, ni cambiaba el estado, ni
        salia ningun cartel. La fila simplemente no se relinkeaba y nadie se
        enteraba.
        """
        new_file_path = new_file_path.replace("\\", "/")

        fila = self.find_row_by_path(original_file_name)
        if fila is None:
            return [], True
        celda = self.table.item(fila, COL_PATH)
        if celda is None:
            return [], True

        carpeta_nueva = os.path.dirname(new_file_path)

        tocados = []
        for nombre in self.row_read_names(fila):
            nodo = nuke.toNode(nombre)
            if nodo is None:
                continue
            # El nombre lo pone el nodo y la carpeta la busqueda: el archivo
            # encontrado puede ser otro frame de la misma secuencia, asi que su
            # nombre no sirve para el knob.
            ruta_nodo = os.path.join(
                carpeta_nueva, os.path.basename(nodo["file"].getValue())
            ).replace("\\", "/")
            nodo["file"].setValue(ruta_nodo)
            tocados.append(nodo)

        # La fila se actualiza aunque no haya ningun Read: el archivo se
        # encontro igual y la tabla tiene que decir donde esta.
        nueva_ruta_tabla = os.path.join(
            carpeta_nueva, os.path.basename(celda.text())
        ).replace("\\", "/")
        celda.setText(nueva_ruta_tabla)
        # El path lo repinta el delegado a partir del dato de la fila: no hay
        # label que actualizar.

        # Verificar si la nueva ruta esta dentro de la carpeta del proyecto.
        # Se usa commonpath sobre rutas normalizadas: commonprefix compara
        # caracter por caracter y falla por mayusculas o por carpetas
        # hermanas con el mismo prefijo (proj vs proj2).
        normi_new_directory = normalize_path_for_comparison(carpeta_nueva)
        normi_project_folder = normalize_path_for_comparison(self.project_folder)
        try:
            common_path = os.path.commonpath(
                [normi_new_directory, normi_project_folder]
            )
        except ValueError:
            # Rutas en unidades distintas: no hay path comun posible
            common_path = ""

        # El estado, su color y su clave de orden salen del mismo lugar que en
        # el escaneo.
        if common_path.replace("\\", "/") == normi_project_folder:
            self.set_row_status(fila, "Online")
        else:
            self.set_row_status(fila, "Outside")
        self.update_status_counts()

        return tocados, bool(tocados)

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
                                # Envuelto: esto corre en el worker del
                                # escaneo, y toNode/getValue desde un hilo del
                                # pool no son thread-safe.
                                rango = _rango_original(read_node_name)
                                if rango:
                                    orig_first, orig_last = rango
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
                            rango = _rango_original(read_node_name)
                            if rango:
                                orig_first, orig_last = rango
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
        
        # ------------------------------------------------------------------
        # TODA la API de Nuke se toca adentro del lambda, o sea en el hilo
        # PRINCIPAL, y lo que sale de ahi son datos de Python. Antes solo se
        # envolvia el allNodes() y despues se leian los knobs de los nodos
        # devueltos desde el hilo del worker, con lo cual el wrapper no servia
        # de nada: allNodes/toNode/getValue no son thread-safe y el sintoma
        # tipico es un cuelgue duro con un script grande.
        # ------------------------------------------------------------------
        def foto_del_script():
            """Corre en el hilo principal. Devuelve datos, no nodos."""
            ruta = nuke.root().name()
            carpeta = os.path.dirname(ruta) if ruta else ""
            lecturas = []
            for tipo in node_types:
                for nodo in nuke.allNodes(tipo):
                    lecturas.append(
                        (nodo.name(), nodo["file"].getValue().replace("\\", "/"))
                    )
            copycats = []
            for nodo in nuke.allNodes("CopyCat"):
                copycats.append(
                    (
                        nodo.name(),
                        nodo["dataDirectory"].getValue().replace("\\", "/")
                        if nodo.knob("dataDirectory")
                        else "",
                        nodo["checkpointFile"].getValue().replace("\\", "/")
                        if nodo.knob("checkpointFile")
                        else "",
                    )
                )
            return carpeta, lecturas, copycats

        project_folder, lecturas, copycats = nuke.executeInMainThreadWithResult(
            foto_del_script
        )

        for nombre, file_path in lecturas:
            resolved_path = resolve_relative_path(file_path, project_folder)
            if resolved_path not in read_files:
                read_files[resolved_path] = []
            read_files[resolved_path].append(nombre)

        # Los CopyCat ya vienen en la foto: aca solo se resuelven las rutas.
        logger = configure_logger()
        logger.debug(
            f"[READ_COPYCAT] Encontrados {len(copycats)} nodos CopyCat en el proyecto"
        )
        for nombre, data_dir, checkpoint_file in copycats:
            logger.debug(f"[READ_COPYCAT] Procesando nodo CopyCat: {nombre}")
            for etiqueta, crudo in (
                ("dataDirectory", data_dir),
                ("checkpointFile", checkpoint_file),
            ):
                if not crudo:
                    logger.debug(f"[READ_COPYCAT]   - Sin knob {etiqueta}")
                    continue
                resuelto = resolve_relative_path(crudo, project_folder)
                logger.debug(f"[READ_COPYCAT]   - {etiqueta} original: '{crudo}'")
                logger.debug(f"[READ_COPYCAT]   - {etiqueta} resuelto: '{resuelto}'")
                if not resuelto:
                    continue
                read_files.setdefault(resuelto, []).append(nombre)
                logger.debug(
                    f"[READ_COPYCAT]   - Agregado {etiqueta} al read_files: "
                    f"{resuelto} -> {nombre}"
                )

        return read_files

    def scan_project(self):
        # Esta función ahora solo configura el worker y lo inicia
        project_path = nuke.root().name()
        if not project_path:
            nuke.message("Please save the script before running this tool.")
            return

        # La carpeta del shot y las carpetas a escanear las resuelve el
        # WORKER, no esta funcion: resolver un comodin es un os.scandir por
        # nivel y por rama, y contra un servidor eso cuelga Nuke entero.

        # La carpeta del .nk se relee ACA, en el hilo principal: el worker la
        # necesita y nuke.root() no se puede llamar desde el pool.
        self.refresh_nk_dir()

        # Un escaneo por vez: dos workers escribiendo sobre la misma tabla se
        # pisan las filas.
        self._scan_running = True
        self._spin_rescan(True)
        if getattr(self, "rescan_button", None) is not None:
            self.rescan_button.setEnabled(False)
            self.apply_footer_stylesheet()

        # Mientras se puebla la tabla el orden va apagado: con el orden activo,
        # el setItem de la columna 0 mueve la fila en el acto y todo lo que se
        # escribe despues para esa fila cae en otra.
        self.table.setSortingEnabled(False)

        # El worker vigente se guarda en self.scanner_worker: es el que la X de
        # la ventana de escaneo tiene que poder cancelar. Antes era una variable
        # local y la X terminaba cancelando otro worker.
        self.scanner_worker = ScannerWorker(self)
        self.scanner_worker.signals.files_found.connect(self.on_files_found)
        self.scanner_worker.signals.failed.connect(self.on_scan_failed)
        self.scanner_worker.signals.finished.connect(self.on_scan_finished)
        QThreadPool.globalInstance().start(self.scanner_worker)
        return self.scanner_worker

    def on_scan_failed(self, detalle):
        """
        El escaneo se corto por un error. Corre en el hilo principal.

        Se avisa y no se disimula: una tabla vacia por un error se lee igual
        que una tabla vacia porque no hay media, y el usuario no tiene forma
        de distinguirlas. El detalle va tambien al log, que es donde se puede
        ver que fallo.
        """
        debug_print("El escaneo fallo: %s" % detalle)
        QMessageBox.warning(
            self,
            "Scan failed",
            "The scan stopped because of an error, so the list is "
            "incomplete:\n\n%s\n\nSee logs/LGA_mediaManager.log for the "
            "full traceback." % detalle,
        )

    def on_scan_finished(self):
        """
        Cierre del escaneo: orden, medidas, contadores y filtro.

        Cada paso va en su propia linea y no en una lista adentro de un
        lambda: ahi, una excepcion en el primero se llevaba puestos a todos
        los demas sin dejar rastro.
        """
        self._scan_running = False
        self._spin_rescan(False)

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
                status = READ_NONE
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
                            self.table.setItem(row_position, COL_READ, read_item)
                            state = "Outside"

                else:
                    # Si file_path no esta en read_files, asumir que el archivo esta Offline (no deberia pasar nunca!)
                    debug_print(
                        "file_path no esta en read_files: no deberia pasar nunca"
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
            texto_read = (
                read_existente.text() if read_existente is not None else READ_NONE
            )
            read_item = SortKeyItem(texto_read)
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
        """
        Deja una sola fila por path, prefiriendo la que este Online.

        Se decide TODO primero y se saca despues, al reves. Antes se borraba
        adentro del mismo recorrido que iba hacia adelante, y eso rompia de
        tres formas a la vez: al sacar una fila las de abajo se corren, asi
        que la siguiente vuelta se saltaba una; el range() se calculo con el
        rowCount original, asi que las ultimas vueltas indexaban filas que ya
        no existian; y los indices guardados en el diccionario quedaban
        apuntando a otras filas despues de cada baja, con lo cual la rama que
        borra "la fila previa" borraba cualquier otra.
        """
        vistos = {}  # path normalizado -> fila que se queda
        a_sacar = set()
        for fila in range(self.table.rowCount()):
            celda = self.table.item(fila, COL_PATH)
            estado_item = self.table.item(fila, COL_STATUS)
            if celda is None or estado_item is None:
                continue
            # Usar la funcion de normalizacion centralizada
            file_path = normalize_path_for_comparison(celda.text())
            estado = estado_item.text()
            previa = vistos.get(file_path)
            if previa is None:
                vistos[file_path] = fila
                continue
            estado_previo_item = self.table.item(previa, COL_STATUS)
            estado_previo = (
                estado_previo_item.text() if estado_previo_item is not None else ""
            )
            if estado != "Online":
                a_sacar.add(fila)
            elif estado_previo != "Online":
                a_sacar.add(previa)
                vistos[file_path] = fila
            else:
                # Las dos Online: se queda la primera, que es la que ya estaba.
                a_sacar.add(fila)

        # De abajo hacia arriba: sacando de arriba, cada baja corre los
        # indices que faltan sacar.
        for fila in sorted(a_sacar, reverse=True):
            self.table.removeRow(fila)

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
    # ======================================================================
    #                         Borrado y copia
    # ======================================================================
    # Las dos siguen la misma forma, y es a proposito:
    #
    #   1. Aca, en el hilo principal, se arma el PLAN: se lee la tabla, se
    #      expanden las secuencias a archivos reales y se hacen TODAS las
    #      preguntas.
    #   2. El worker recibe el plan ya decidido y solo toca disco.
    #
    # Antes no era asi y las dos consecuencias eran graves: el borrado leia la
    # tabla desde el hilo worker -tocar widgets de Qt fuera del hilo principal
    # es comportamiento indefinido- y ademas lo arrancaba con start() seguido
    # de wait(), o sea que congelaba la ventana igual; y la copia terminaba
    # corriendo shutil.copy en el hilo principal, porque la senal que la
    # disparaba estaba conectada a un slot del propio objeto, que vive ahi.

    def _run_batch(self, worker, titulo, al_terminar):
        """
        Lanza una tanda con su ventana de progreso y su X para abortar.

        Comun a la copia y al borrado: las dos muestran lo mismo, se cancelan
        igual y terminan igual. Lo unico que cambia es el worker.
        """
        ventana = ProgressWindow(titulo, self)
        self.center_window(ventana)
        ventana.set_progress(0, max(1, len(worker.items)))
        ventana.cancelled.connect(worker.cancel)
        worker.signals.progress.connect(ventana.set_progress)
        # Con `ventana` como contexto: si la ventana muere -por ejemplo porque
        # se cerro el Media Manager- Qt desconecta sola. Con un lambda pelado
        # la conexion sobrevive y el slot corre sobre un widget destruido.
        worker.signals.item.connect(
            ventana,
            lambda nombre: ventana.set_message("%s\n%s" % (titulo, nombre)),
        )

        def cerrar(hechos, salteados, errores, cancelado):
            # El trabajo de cierre va PRIMERO. Cerrando antes, un RuntimeError
            # de la ventana ya destruida se llevaba puesto al callback: los
            # archivos quedaban copiados pero los Reads sin reapuntar, y
            # _batch_worker nunca volvia a None, con lo que Copy to y Delete
            # quedaban muertos para el resto de la sesion.
            try:
                al_terminar(hechos, salteados, errores, cancelado)
            finally:
                try:
                    ventana.stop()
                    ventana.deleteLater()
                except RuntimeError:
                    pass
                # Red de seguridad: si al_terminar se cayo, la barra quedaria
                # apagada hasta que el usuario toque algo. El worker ya volvio
                # a None ahi adentro, asi que esto la prende.
                try:
                    self.update_button_states()
                except RuntimeError:
                    pass

        worker.signals.finished.connect(cerrar)
        # La referencia se guarda: sin ella, el worker y sus senales se pueden
        # destruir mientras el hilo del pool todavia esta saliendo de run().
        self._batch_window = ventana
        self._batch_worker = worker
        # Con la tanda en curso la barra se apaga: es lo que evita lanzar un
        # Relink o un Rescan encima de una copia.
        self.update_button_states()
        ventana.show()
        QApplication.processEvents()
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def _resumen_tanda(hechos, salteados, errores, cancelado, verbo):
        """El texto del cartel final. Uno solo por tanda, nunca uno por archivo.

        En ingles como toda la UI: este cartel estaba en castellano, que por
        regla del pack es el idioma de los comentarios y los tooltips, no el
        de lo que ve el usuario.
        """
        partes = ["%d file(s) %s." % (hechos, verbo)]
        if cancelado and salteados:
            partes.append("%d left unprocessed after cancelling." % salteados)
        if errores:
            partes.append("%d failed:" % len(errores))
            partes.append("\n".join(errores[:10]))
            if len(errores) > 10:
                partes.append("...")
        return "\n".join(partes)

    # ------------------------------------------------------------ borrado ---
    def delete_selected(self):
        """
        Manda a la papelera los archivos de TODAS las filas seleccionadas.

        Siempre a la papelera: es la unica red que le queda al usuario si se
        equivoco de seleccion, y aca se borra media de proyectos.
        """
        filas = self.selected_rows()
        if not filas:
            return
        if self.operacion_en_curso() is not None:
            debug_print("Hay una operacion en curso: se ignora el Delete")
            return

        # Offline no se puede borrar: el archivo no esta, asi que no hay nada
        # que mandar a la papelera. Se corta la operacion entera y no solo esa
        # fila, para no borrar la mitad de lo que el usuario pidio.
        if any(self.row_status(fila) == "Offline" for fila in filas):
            QMessageBox.warning(
                self, "Cannot Delete", "Cannot delete an offline file."
            )
            return

        # El plan: de cada fila salen sus archivos REALES, y de las carpetas
        # borrables su carpeta. Se arma aca, en el hilo principal, que es el
        # unico que puede leer la tabla.
        plan = []
        carpetas = []
        # Cuantos archivos se van a la papelera de verdad. No es len(plan): una
        # secuencia que se borra por carpeta son mil archivos y UNA entrada.
        total = 0
        for fila in filas:
            ruta = self.row_path(fila)
            archivos = expand_sequence(ruta)
            if not archivos:
                continue
            total += len(archivos)
            item_carpeta = self.table.item(fila, COL_FOLDER_DELETE)
            borrable = (
                item_carpeta is not None and item_carpeta.text().lower() == "true"
            )
            carpeta_seq = ""
            if borrable and "#" in ruta:
                carpeta_seq = os.path.normpath(os.path.dirname(archivos[0]))
                # El dato viene del ESCANEO y puede tener minutos: entre medio
                # pudo entrar un render en esa carpeta. Se revalida ahora, que
                # es una llamada a disco, contra el riesgo de llevarse a la
                # papelera archivos que nadie selecciono.
                if not self._carpeta_tiene_solo(carpeta_seq, archivos):
                    debug_print(
                        "La carpeta %s ya no tiene solo la secuencia: se borran"
                        " los archivos de a uno" % carpeta_seq
                    )
                    carpeta_seq = ""
            if carpeta_seq:
                # La secuencia tiene su carpeta para ella sola: se manda la
                # carpeta y no los N archivos, que es una operacion en vez de
                # miles y ademas deja la papelera prolija.
                # Sin deduplicar, dos filas cuya secuencia vive en la misma
                # carpeta la mandaban dos veces: el segundo send2trash falla y
                # el usuario ve un error que no existe.
                if carpeta_seq not in carpetas:
                    carpetas.append(carpeta_seq)
            else:
                plan.extend(archivos)

        if not plan and not carpetas:
            return

        # Un solo cartel de confirmacion por tanda, con el total real.
        en_uso = [f for f in filas if self.row_read_names(f)]
        aviso = ""
        if en_uso:
            # Cuenta FILAS y lo dice: con una secuencia de mil frames, decir
            # "1 archivo" seria mentir por tres ordenes de magnitud.
            aviso = "\n\n%d of them %s used by a Read in Nuke." % (
                len(en_uso),
                "is" if len(en_uso) == 1 else "are",
            )
        respuesta = QMessageBox.question(
            self,
            "Confirm delete",
            "Send %d file(s) to the trash?\n%d row(s) selected.%s"
            % (total, len(filas), aviso),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return

        # Las carpetas van al final: si se borrara la carpeta primero, los
        # archivos de adentro que todavia estan en la lista ya no existirian.
        worker = DeleteWorker(plan + carpetas)
        # El total en ARCHIVOS reales, para que el resumen final hable en la
        # misma unidad que el cartel de confirmacion. Las entradas del worker
        # no sirven: una secuencia borrada por carpeta es una sola entrada y
        # mil archivos, asi que el resumen decia "1 enviado a la papelera"
        # despues de borrar mil frames.
        self._delete_total = total
        # Se guardan las RUTAS y no los indices de fila. La ventana de progreso
        # no es modal, asi que durante la tanda el usuario puede ordenar la
        # tabla y los indices pasan a apuntar a otras filas: se terminaba
        # sacando la fila equivocada.
        self._delete_paths = [self.row_path(f) for f in filas]
        self._run_batch(worker, "Deleting...", self._on_delete_finished)

    def _on_delete_finished(self, hechos, salteados, errores, cancelado):
        """Saca de la tabla las filas cuyos archivos ya no estan."""
        self._batch_worker = None
        # La fila se busca AHORA por su ruta: entre que arranco la tanda y
        # ahora, la tabla pudo reordenarse. Se recorre al reves para que los
        # indices de las que faltan sacar no se corran al ir sacandolas.
        pedidas = set(getattr(self, "_delete_paths", []))
        borrados = 0
        for fila in range(self.table.rowCount() - 1, -1, -1):
            ruta = self.row_path(fila)
            if ruta not in pedidas:
                continue
            archivos = expand_sequence(ruta)
            # La fila se saca solo si su archivo REALMENTE dejo de estar: con
            # la tanda cancelada a la mitad, sacar todas las filas mostraria
            # como borrado lo que sigue en disco.
            if archivos and not os.path.exists(archivos[0]):
                borrados += len(archivos)
                self.table.removeRow(fila)
        total = getattr(self, "_delete_total", 0)
        self._delete_paths = []
        self._delete_total = 0
        self.renumber_visible_rows()
        self.update_status_counts()
        self.update_button_states()
        if errores or cancelado:
            QMessageBox.information(
                self,
                "Delete",
                self._resumen_tanda(
                    borrados,
                    max(0, total - borrados) if cancelado else 0,
                    errores,
                    cancelado,
                    "sent to the trash",
                ),
            )

    # -------------------------------------------------------------- copia ---
    def copy_to(self, location):
        """
        Copia a la location elegida TODAS las filas seleccionadas.

        La tanda entera va en UN worker y no encadenada de a una: no hay nada
        que preguntar entre archivo y archivo -las sobreescrituras se resuelven
        antes de arrancar- asi que encadenar solo agregaba una ventana por
        archivo y cinco caminos distintos para terminar.
        """
        filas = self.selected_rows()
        if not filas:
            return
        if self.operacion_en_curso() is not None:
            debug_print("Hay una operacion en curso: se ignora el Copy to")
            return

        # Guard de siempre, sobre TODAS las filas: Copy to es traerse adentro
        # del shot algo que esta afuera, y copiar de nuevo algo que ya esta
        # adentro no significa nada.
        if any(self.row_status(fila) != "Outside" for fila in filas):
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                "The copy operation is limited to 'Outside' files",
            )
            return

        # El destino sale de la ruta de la location, resuelta contra disco. Un
        # comodin puede abrir cero o varias carpetas, y en los dos casos elegir
        # por el usuario seria adivinar.
        resultado = mm_paths.resolve(location.get("path", ""), self.nk_dir())
        etiqueta = location.get("name") or location.get("path", "")
        if len(resultado.folders) > 1:
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                '"%s" matches %d folders, so there is no single '
                "destination:\n\n%s"
                % (etiqueta, len(resultado.folders), "\n".join(resultado.folders[:8])),
            )
            return
        if not resultado.folders:
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                '"%s" does not match any existing folder.' % etiqueta,
            )
            return

        destino_base = resultado.folders[0]
        plan, conflictos, colisiones, reapuntar = self._plan_copy(filas, destino_base)
        if not plan:
            return

        # Dos origenes distintos que caen en el mismo destino no es algo que se
        # pueda resolver eligiendo: uno de los dos se perderia sin que nadie se
        # entere. Se corta y se dice cuales son.
        if colisiones:
            detalle = "\n".join(
                "%s\n%s\n  -> %s" % (a, b, d) for a, b, d in colisiones[:5]
            )
            QMessageBox.warning(
                self,
                "Copy Not Allowed",
                "%d file(s) from different folders would end up at the same "
                "destination, so one would overwrite the other:\n\n%s"
                % (len(colisiones), detalle),
            )
            return

        # UNA sola pregunta por tanda. Preguntando archivo por archivo, con
        # diez filas eran diez carteles seguidos.
        if conflictos:
            caja = QMessageBox(self)
            caja.setIcon(QMessageBox.Warning)
            caja.setWindowTitle("Files already exist")
            caja.setText(
                "%d of the selected files already exist in \"%s\"."
                % (len(conflictos), etiqueta)
            )
            caja.setInformativeText("What do you want to do with them?")
            boton_sobre = caja.addButton("Overwrite all", QMessageBox.AcceptRole)
            boton_saltear = caja.addButton("Skip them", QMessageBox.DestructiveRole)
            caja.addButton(QMessageBox.Cancel)
            caja.setDefaultButton(boton_saltear)
            caja.exec_()
            elegido = caja.clickedButton()
            if elegido is boton_saltear:
                en_conflicto = set(conflictos)
                plan = [par for par in plan if par[1] not in en_conflicto]
            elif elegido is not boton_sobre:
                return
            if not plan:
                return

        self._copy_reapuntar = reapuntar
        worker = CopyWorker(plan)
        self._run_batch(worker, "Copying...", self._on_copy_finished)

    def _plan_copy(self, filas, destino_base):
        """
        Que archivo va a donde, y cuales ya existen.

        Devuelve (plan, conflictos, colisiones, reapuntar):
          plan        pares (origen, destino) de archivos REALES
          conflictos  destinos que ya existen
          colisiones  dos origenes distintos que caen en el mismo destino
          reapuntar   una entrada POR FILA, con la ruta de la fila, su nodo,
                      la carpeta destino y los destinos de esa fila. Es una
                      lista de filas y no un {nodo: carpeta} porque despues de
                      copiar hay que saber QUE fila corresponde a cada nodo:
                      sin eso, el reapuntado no podia mirar si esa fila se
                      copio de verdad ni encontrar su fila en la tabla

        Se arma entero antes de arrancar el worker: es lo que permite hacer
        una sola pregunta por la sobreescritura en vez de una por archivo, y
        lo que deja al worker sin nada que consultarle a la ventana.
        """
        plan = []
        conflictos = []
        colisiones = []
        vistos = {}
        reapuntar = []
        for fila in filas:
            ruta = self.row_path(fila)
            archivos = expand_sequence(ruta)
            if not archivos:
                continue
            # Una secuencia se copia con su carpeta contenedora, para no
            # desparramar miles de frames sueltos en el destino.
            if "#" in ruta:
                carpeta = os.path.join(
                    destino_base, os.path.basename(os.path.dirname(archivos[0]))
                )
            else:
                carpeta = destino_base
            destinos_fila = []
            for origen in archivos:
                destino = os.path.join(carpeta, os.path.basename(origen))
                # Dos filas distintas pueden dar el MISMO destino: dos versiones
                # del mismo plano en carpetas distintas se llaman igual. Sin
                # detectarlo, la segunda pisaba a la primera y el resumen
                # informaba las dos como copiadas. os.path.exists no lo ve:
                # cuando se planifica, el destino todavia no existe.
                if destino in vistos:
                    colisiones.append((vistos[destino], origen, destino))
                    continue
                vistos[destino] = origen
                plan.append((origen, destino))
                destinos_fila.append(destino)
                if os.path.exists(destino):
                    conflictos.append(destino)
            if not destinos_fila:
                continue
            # Con varios Reads sobre la misma media se reapunta el primero:
            # los demas siguen apuntando al original hasta que el usuario los
            # relinkee. El original sigue existiendo, asi que no quedan rotos.
            nodos = self.row_read_names(fila)
            reapuntar.append(
                {
                    "ruta": ruta,
                    "nodo": nodos[0] if nodos else "",
                    "carpeta": carpeta,
                    "destinos": destinos_fila,
                }
            )
        return plan, conflictos, colisiones, reapuntar

    def _on_copy_finished(self, hechos, salteados, errores, cancelado):
        """Reapunta los Reads de las filas que SI se copiaron."""
        self._batch_worker = None
        tocados = []
        for registro in getattr(self, "_copy_reapuntar", []) or []:
            # Se verifica contra DISCO y no contra el plan. Antes se reapuntaba
            # todo lo planificado sin mirar `cancelado` ni `errores`: cancelar
            # una copia de seis filas despues de la primera dejaba los seis
            # Reads mirando el destino y cinco de ellos offline.
            if not self._copia_completa(registro["destinos"]):
                continue
            try:
                nodo = self.repoint_read(registro)
            except Exception as problema:
                debug_print(
                    "No se pudo reapuntar %s: %s" % (registro["ruta"], problema)
                )
                continue
            if nodo is not None:
                tocados.append(nodo)
        self._copy_reapuntar = []
        self.focus_nodes(tocados)
        self.update_status_counts()
        self.update_button_states()
        if errores or cancelado:
            QMessageBox.information(
                self,
                "Copy to",
                self._resumen_tanda(hechos, salteados, errores, cancelado, "copied"),
            )

    @staticmethod
    def _carpeta_tiene_solo(carpeta, archivos):
        """
        Si en esa carpeta no hay nada mas que estos archivos.

        Es la condicion para mandar la CARPETA a la papelera en vez de sus N
        archivos. La calcula tambien el escaneo, pero ese dato es una foto: lo
        que decide un borrado se vuelve a mirar en el momento de borrar.
        """
        try:
            adentro = os.listdir(carpeta)
        except OSError as problema:
            debug_print("No se pudo revisar %s: %s" % (carpeta, problema))
            return False
        return len(adentro) == len(archivos)

    @staticmethod
    def _copia_completa(destinos):
        """
        Si esta fila llego entera al destino.

        Se miran el primero y el ultimo, no los mil del medio: una tanda se
        corta siempre al final -la cancelacion es una bandera que el worker
        mira entre archivo y archivo- asi que si el ultimo esta, estan todos.
        Mil llamadas a disco por fila costarian mas que la copia.
        """
        if not destinos:
            return False
        return os.path.exists(destinos[0]) and os.path.exists(destinos[-1])

    def repoint_read(self, registro):
        """
        Deja el Read de UNA fila apuntando a la copia, y su fila al dia.

        Devuelve el nodo tocado, o None: el Node Graph lo enfoca quien llama,
        una sola vez por tanda.

        Toca exactamente la fila que se copio, buscada por su ruta. La version
        anterior recorria la tabla quedandose con toda fila cuyo path empezara
        con la carpeta de ORIGEN, asi que copiar una fila reescribia tambien
        las otras siete que vivian en esa carpeta y las marcaba Online sin que
        se hubiera copiado nada de ellas.

        Corre en el hilo principal -lo llama el `finished` del worker- asi que
        toca la API de Nuke y la tabla sin ceremonia.
        """
        carpeta = registro["carpeta"]
        nombre_nodo = registro["nodo"]

        nodo = nuke.toNode(nombre_nodo) if nombre_nodo else None
        if nodo is not None and nodo.Class() == "Read":
            original = nodo["file"].getValue()
            nuevo = os.path.join(carpeta, os.path.basename(original))
            nodo["file"].setValue(nuevo.replace("\\", "/"))
        else:
            nodo = None

        fila = self.find_row_by_path(registro["ruta"])
        if fila is None:
            return nodo
        celda = self.table.item(fila, COL_PATH)
        if celda is None:
            return nodo
        # Se cambia SOLO la carpeta, dejando el nombre tal como esta escrito
        # en la tabla. Antes se armaba cortando el texto por el largo del path
        # del knob, y los dos largos solo coinciden con padding 4: el knob trae
        # "%05d" -cuatro caracteres- donde la tabla tiene "#####", que son
        # cinco, asi que con cualquier otro padding el corte quedaba corrido y
        # el path salia roto ("...exrr[1001-1100]").
        nuevo_tabla = os.path.join(carpeta, os.path.basename(celda.text()))
        celda.setText(nuevo_tabla.replace("\\", "/"))
        # El archivo se trajo adentro del shot: deja de estar Outside.
        estado = self.table.item(fila, COL_STATUS)
        if estado is not None and estado.text() == "Outside":
            self.set_row_status(fila, "Online")
        return nodo
