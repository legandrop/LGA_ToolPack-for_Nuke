"""
_______________________________________________________________________

  LGA_mediaManager v2.46 | Lega

  Ventana del Media Manager: escaneo del shot, estado de cada media,
  relink, copia de archivos, borrado y descarga desde Wasabi.

  Modulos de esta tool (todos van con la misma version):
    LGA_mediaManager.py              <- este, el principal
    LGA_MediaManager_FileScanner.py  ventana, tabla y relink
    LGA_MediaManager_utils.py        workers de escaneo, copia y borrado
    LGA_MediaManager_settings.py     ventana de ajustes
    LGA_MediaManager_config.py       donde vive el .ini del usuario
    LGA_MediaManager_paths.py        resolucion de rutas e inclusiones
    LGA_MediaManager_logging.py      logger a logs/LGA_mediaManager.log
    LGA_MediaManager_download.py     deteccion de FileManager S3 /
                                     PipeSync y el comando de descarga

  Donde mas se ve esta version, y hay que moverla junto con el header:
    - La ventana de ajustes, abajo a la izquierda. Esa sale sola: la lee
      de ESTE header con get_tool_version() de
      LGA_MediaManager_settings.py, asi que no hay ningun numero
      escrito a mano en la interfaz.
    - El titulo de la seccion "Media manager" del README.md. Ese SI es
      un numero a mano y hay que cambiarlo en la misma pasada.

  v2.46: Download tambien descarga con PipeSync, que suma el mismo CLI
         que FileManager S3. Delete pasa a Alt+Backspace. El rango de
         frames de una secuencia va separado por un espacio y con el
         gradiente del browser de FileManager S3. El detalle esta en los
         headers de LGA_MediaManager_FileScanner, _download y _utils.
  v2.45: Boton Download (Alt+D): pide a Wasabi las filas seleccionadas
         con el CLI de FileManager S3, como el Download Clip de
         HieroTools pero sin buscar versiones mas altas. Aparece solo
         si al abrir la tool se encontro FileManager S3 o PipeSync
         studio. Delete pasa a Alt+T. El detalle esta en los headers de
         LGA_MediaManager_FileScanner y LGA_MediaManager_download.
  v2.44: Los carteles estandar pasan al helper
         LGA_UI_MessageBox_ToolPack, que los estila con el tema base
         del pack. El detalle esta en el header de
         LGA_MediaManager_FileScanner.
  v2.43: El escaneo volvia vacio por un NameError adentro del worker
         que el except se comia. El detalle esta en el header de
         LGA_MediaManager_utils.
  v2.42: Se sacan tres imports de LGA_MediaManager_utils que ya no
         existian -TransparentTextDelegate, CopyThread y DeleteThread-
         y hacian fallar la apertura con ImportError. Los dos Thread
         los reemplazaron CopyWorker y DeleteWorker en v2.40 y aca no
         se usaban; el delegado vuelve a existir en utils.
  v2.41: Copy to, Delete y Relink revisados con seleccion multiple.
         El detalle esta en los headers de LGA_MediaManager_FileScanner
         y LGA_MediaManager_utils.
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
  v2.39: Copia y borrado se rehacen enteros. Las dos andaban mal de
         hilos: el borrado leia la TABLA desde el hilo worker -tocar
         widgets de Qt fuera del principal es comportamiento
         indefinido- y encima arrancaba el hilo y lo esperaba en la
         linea siguiente, o sea que congelaba la ventana igual; y la
         copia terminaba corriendo shutil.copy en el hilo principal,
         porque la senal que la disparaba estaba conectada a un slot
         del propio objeto, que vive ahi. Ademas armaba las rutas con
         separadores de Windows escritos a mano, asi que en macOS le
         pasaba rutas rotas a send2trash.
         Ahora las dos siguen la misma forma: el hilo principal arma
         el PLAN -lee la tabla, expande las secuencias y hace TODAS
         las preguntas- y el worker recibe el plan decidido y solo
         toca disco. Las tres operaciones andan sobre varias filas,
         con una ventana de progreso que se puede abortar.
         Copying y Deleting pasan al tema, con la misma ventana que
         el escaneo. El borrado permanente, que estaba muerto, se va:
         todo va a la papelera.
  v2.38: La ventana del escaneo -la primera que ve el usuario- pasa
         al tema: esquinas redondeadas, la fuente del pack, sin
         negrita y la barra de progreso en el violeta de acento. Y
         suma una X arriba a la derecha que ABORTA el escaneo: sin
         marco no hay boton de cerrar del sistema, asi que contra un
         servidor lento lo unico que quedaba era esperar. El icono de
         Rescan gira mientras dura el escaneo, como en el prototipo.
         En los ajustes, Add location lleva la fila nueva a la vista:
         con la tabla en su alto maximo nacia abajo del area visible,
         con el foco puesto y sin que se viera.
  v2.37: Seis desalineaciones mas de la tabla de ajustes, medidas
         con Qt real en vez de estimadas. La mas grande: el titulo
         "Name" caia 35 px antes que los nombres, porque el
         encabezado pone un label pelado y la fila pone una ranura,
         un borde y un padding. Y la reserva de la barra de scroll se
         deducia de cuantas filas hay, que dejo de ser lo mismo que
         "hay barra" desde que la ventana se puede achicar: con pocas
         filas y la ventana baja, las columnas de la derecha volvian
         a correrse 10 px. Ahora se mide la diferencia real.
  v2.36: Aparece por que los titulos de la tabla de ajustes no
         caian sobre su contenido, despues de tres intentos de
         centrarlos: SI estaban centrados, pero en una columna
         corrida. El encabezado tenia un widget de ancho cero al
         final para reservar la barra de scroll, y un QHBoxLayout
         suma su espaciado ENTRE items sin mirar cuanto mide cada
         uno, asi que ese item de 0 px igual se llevaba 9. El
         encabezado repartia 9 px menos que las filas entre sus
         columnas elasticas, y como esas van primero, las tres de la
         derecha quedaban corridas 9 px. Se reserva con el margen del
         layout, que no agrega item.
         El ancho de las tarjetas se lo decide Qt y no una cuenta
         propia, y Status suma 5 px.
  v2.35: Fixes de lo de v2.34, que no se veia. La ventana principal
         abria con media pantalla vacia a la derecha: el ancho de la
         columna del path se recalculaba en el resizeEvent de la
         VENTANA, y ahi Qt todavia no reacomodo a los hijos, asi que
         el viewport medido era el de antes y la columna se quedaba
         en su minimo. Ahora se recalcula cuando el viewport avisa
         que cambio, que es el unico momento en que ya se sabe cuanto
         mide. Ninguna columna se puede arrastrar a mano.
         En los ajustes, el ancho de las tarjetas se medía con la
         fuente equivocada: el label todavia no tiene la familia del
         pack cuando se lo crea, y su tamano se lo pone recien la
         hoja de estilo. Medido con otra fuente, el calculo daba de
         menos y el renglon se partia igual.
  v2.34: El scroll horizontal pasa a ser de la COLUMNA del path y no
         de la tabla: el numero de fila, el Read y el Status quedan
         siempre a la vista. Read y Status dejan de tener ancho fijo
         y se miden sobre su contenido, que en las dos se conoce
         entero. En los ajustes, las tres columnas de la derecha se
         ajustan a lo que mide su encabezado y van centradas, titulo
         y contenido; y el ancho de las tarjetas de ayuda lo decide
         el renglon mas largo, medido.
  v2.33: La ventana principal abre con el ancho justo para que entre
         el path mas largo sin cortarse, con tope en el 80% del ancho
         de la pantalla. Pasado ese tope el path NO se recorta:
         aparece el scroll horizontal, porque no poder leer un path
         entero es justo lo que esta herramienta viene a resolver.
         En los ajustes, "Resolves to" recupera ancho: era la unica
         columna que no habia que tocar y quedo tan angosta que se
         comia el nombre de la carpeta resuelta.
  v2.32: Las dos ventanas se pueden achicar. El minimo de la
         principal lo fijaba la leyenda del pie, que es texto de
         ayuda y era la fila mas ancha de todas; ahora las
         explicaciones se esconden cuando no entran y el piso lo
         pone la barra, que es lo unico que de verdad no se puede
         comprimir. En los ajustes el minimo sale del contenido y no
         de un numero escrito a mano, la tabla se puede comprimir
         hasta dos filas, y las columnas se ajustan a lo que
         realmente usan.
  v2.31: Cinco ajustes sobre la ventana ya portada. Vuelven las
         lineas horizontales entre filas, que se habian perdido al
         apagar la grilla de Qt: las dibuja cada delegado, porque la
         regla de hoja no se ve cuando las cuatro columnas pintan la
         celda entera. La celda de Read se pinta con la seleccion
         -quedaba un bloque oscuro en el medio de la fila elegida,
         que es lo que cortaba el gris antes de llegar a Status-. El
         '#' pasa a contar lo que se VE: arranca siempre en 1 y no
         salta, ordene por la columna que ordene; el orden de carga
         sigue en la clave por la que ordena esa misma columna. Y en
         los ajustes "Table font size" se pega a su stepper.
  v2.30: Poner Inter no alcanzaba: sus tres caras NO forman una
         sola familia para Qt. La Regular y la Bold caen las dos en
         "Inter", pero la SemiBold cae en una familia PROPIA, "Inter
         SemiBold". Con eso, `font-weight: 600` sobre "Inter" no
         devuelve la SemiBold sino la cara mas cercana que si esta
         en esa familia: la Bold de 700. Por eso la etiqueta de los
         botones, la cabecera de la tabla, los contadores de las
         pastillas, la leyenda y Rescan seguian saliendo en negrita.
         Ahora el peso 600 se pide nombrando la familia.
  v2.29: La ventana se dibuja por fin con la fuente del pack. Inter se
         registraba desde v2.13 y nadie se la ponia a la ventana, asi
         que el `font-weight: 600` de las hojas no encontraba una cara
         real y macOS sintetizaba la negrita: TODO el texto salia con
         el peso -y el ancho- de una 700 falsa. De ahi tambien salia
         que la barra, la cabecera, la leyenda y el pie midieran entre
         un 8 y un 20% mas que en el prototipo.
         Con eso resuelto se corrige el resto de lo que separaba la
         ventana del disenio: la grilla vertical de Qt y el separador
         de fila oscuro, las esquinas y el borde de la caja de la
         tabla, la barra de scroll nativa, el subrayado de mnemonicos,
         los iconos borrosos en pantalla Retina, los margenes de la
         ventana, la columna Read y el numero de la fila elegida.
  v2.28: El tema de fabrica pasa a ser el del pack, que es el que ya
         usan las demas ventanas migradas. Se elige y se guarda solo:
         se aplica en vivo sobre las dos ventanas, asi que pedir Save
         despues de haberlo visto puesto no decia nada. El tamano de
         letra sigue necesitando Save -cambia el alto de las filas, o
         sea cuanto entra en pantalla- y Cancel y Save se apagan
         mientras no haya nada que guardar ni que descartar.
  v2.25: Las versiones de los seis modulos quedan sincronizadas. El
         .ini pasa a la carpeta de datos del usuario y la busqueda del
         relink sale del hilo principal.
  v2.24: fix altura de la ventana
  v2.23: se agrega el nuevo logging system
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

# Importar clases desde archivos auxiliares
from LGA_MediaManager_utils import (
    StartupWindow,
    ScannerSignals,
    ScannerWorker,
)
from LGA_MediaManager_settings import SettingsWindow
from LGA_MediaManager_FileScanner import FileScanner
from LGA_UI_MessageBox_ToolPack import show_warning


def main():
    configure_logger(reset=True)
    app = QApplication.instance() or QApplication(sys.argv)

    # Verificar si el script está guardado
    if not nuke.root().name() or nuke.root().name() == "Root":
        show_warning(
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

        # La X de la ventana de escaneo aborta de verdad. Sin esto, un escaneo
        # largo contra un servidor no se podia parar: la unica salida era
        # esperarlo entero.
        abortado = {"si": False}

        def on_cancel():
            abortado["si"] = True
            debug_print("Escaneo cancelado por el usuario")
            window.scanner_worker.cancel()
            # La ventana principal no se abre: el usuario dijo que no.
            window.close()

        def on_scan_complete():
            startup_window.stop()
            if abortado["si"]:
                return
            # Usar QTimer para retrasar la visualización
            QTimer.singleShot(100, delayed_show)  # 100ms de retraso

        startup_window.cancelled.connect(on_cancel)
        # El worker YA esta corriendo: lo arranco scan_project() desde initUI.
        # Aca solo se enganchan el progreso y el fin. Arrancarlo de nuevo -que
        # es lo que se hacia- ponia un segundo hilo a recorrer el disco sobre
        # la misma ventana.
        if window.scanner_worker is not None:
            window.scanner_worker.signals.progress.connect(
                startup_window.updateProgress
            )
            window.scanner_worker.signals.finished.connect(on_scan_complete)
        else:
            # Sin worker no hay escaneo que esperar: el .nk no estaba guardado.
            startup_window.stop()


if __name__ == "__main__":
    app = QApplication.instance() or QApplication([])
    window = FileScanner()
    window.show()
