"""
_______________________________________________________________________

  LGA_mediaManager v2.31 | Lega

  Ventana del Media Manager: escaneo del shot, estado de cada media,
  relink, copia de archivos y borrado.

  Modulos de esta tool (todos van con la misma version):
    LGA_mediaManager.py              <- este, el principal
    LGA_MediaManager_FileScanner.py  ventana, tabla y relink
    LGA_MediaManager_utils.py        workers de escaneo, copia y borrado
    LGA_MediaManager_settings.py     ventana de ajustes
    LGA_MediaManager_config.py       donde vive el .ini del usuario
    LGA_MediaManager_paths.py        resolucion de rutas e inclusiones
    LGA_MediaManager_logging.py      logger a logs/LGA_mediaManager.log

  Version visible en la UI: la muestra la ventana de ajustes, abajo a
  la izquierda. Sale de leer ESTE header con get_tool_version() de
  LGA_MediaManager_settings.py, asi que no hay ningun numero escrito a
  mano en la interfaz.

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
    TransparentTextDelegate,
    LoadingWindow,
    StartupWindow,
    ScannerSignals,
    ScannerWorker,
    CopyThread,
    DeleteThread,
)
from LGA_MediaManager_settings import SettingsWindow
from LGA_MediaManager_FileScanner import FileScanner


def main():
    configure_logger(reset=True)
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

        # Usar el scanner_worker de window.scan_project()
        window.scanner_worker.signals.progress.connect(startup_window.updateProgress)
        window.scanner_worker.signals.finished.connect(on_scan_complete)

        # Iniciar el escaneo en segundo plano usando el worker existente
        QThreadPool.globalInstance().start(window.scanner_worker)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication([])
    window = FileScanner()
    window.show()
