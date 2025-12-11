"""
_______________________________________

  LGA_mediaManager v2.22 | Lega
_______________________________________

"""

from qt_compat import QtWidgets, QtGui, QtCore

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
import inspect

# Variables de estado globales para el tiempo de inicio
_start_time = time.time()

DEBUG = False


def configure_logger():
    # Si ya existe un logger configurado, lo retornamos sin crear uno nuevo
    if hasattr(configure_logger, "logger"):
        return configure_logger.logger

    # Crear un logger principal para toda la aplicacion
    logger = logging.getLogger("LGA_MediaManager")
    logger.setLevel(logging.DEBUG)

    # Eliminar cualquier manejador que ya este configurado en el logger
    if logger.hasHandlers():
        logger.handlers.clear()

    # Evitar que los mensajes se propaguen al logger raiz
    logger.propagate = False

    # Crear un handler para escribir en archivo
    log_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(log_dir, "LGA_mediaManager.log")

    # Limpiar el archivo al inicio
    with open(log_file, "w") as f:
        f.write("")  # Sobrescribe el contenido del archivo, limpiandolo

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Crear un formatter personalizado que incluya [tiempo] [clase::metodo]
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            elapsed = time.time() - _start_time

            # Obtener el frame de donde se llamo el log
            frame = inspect.currentframe()
            caller_frame = None
            caller_class = None
            caller_method = None

            # Recorrer los frames hasta encontrar el llamador real
            try:
                # Saltar los frames internos del logging
                while frame:
                    frame = frame.f_back
                    if frame is None:
                        break

                    # Saltear frames internos del logging
                    filename = frame.f_code.co_filename
                    if "logging" in filename.lower():
                        continue

                    # Obtener informacion del metodo
                    caller_method = frame.f_code.co_name

                    # Intentar obtener la clase
                    if "self" in frame.f_locals:
                        caller_class = frame.f_locals["self"].__class__.__name__
                    elif "cls" in frame.f_locals:
                        caller_class = frame.f_locals["cls"].__name__
                    else:
                        # Si no hay clase, usar el nombre del modulo
                        module_name = os.path.basename(filename).replace(".py", "")
                        if module_name.startswith("LGA_"):
                            caller_class = module_name
                        else:
                            caller_class = "Unknown"

                    break
            except:
                caller_class = "Unknown"
                caller_method = "unknown_method"

            # Formatear el mensaje
            timestamp = f"[{elapsed:.3f}s]"
            location = f"[{caller_class}::{caller_method}]"

            return f"{timestamp} {location} {record.getMessage()}"

    formatter = CustomFormatter()
    file_handler.setFormatter(formatter)

    # Agregar el handler al logger
    logger.addHandler(file_handler)

    # Guardar una referencia al logger para no duplicarlo
    configure_logger.logger = logger
    return logger


def debug_print(*message):
    if DEBUG:
        print(*message)


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
