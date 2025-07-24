"""
_______________________________________

  LGA_mediaManager v2.00 | Lega
_______________________________________

"""

from PySide2.QtWidgets import (
    QApplication,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QToolButton,
    QSizePolicy,
    QFileDialog,
)
from PySide2.QtWidgets import (
    QItemDelegate,
    QStyle,
    QMessageBox,
    QCheckBox,
    QLabel,
    QHBoxLayout,
    QSpinBox,
    QFrame,
    QMenu,
    QAction,
    QProgressBar,
    QLineEdit,
)
from PySide2.QtGui import QBrush, QColor, QPalette, QMovie, QScreen, QIcon
from PySide2.QtCore import Qt, QTimer, QThread, Signal, QObject, QRunnable, Slot
import nuke
import os
import re
import subprocess
import time
import shutil
import sys
import configparser
import logging
from PySide2.QtCore import QThreadPool

# Importar el tiempo de inicio global del archivo principal
try:
    from LGA_mediaManager import _start_time
except ImportError:
    _start_time = time.time()

start_time = time.time()


def get_log_prefix(caller_class=None, caller_method=None):
    """
    Genera el prefijo para logs con formato [tiempo] [clase::metodo]
    """
    elapsed = time.time() - _start_time
    timestamp = f"[{elapsed:.3f}s]"

    if caller_class and caller_method:
        location = f"[{caller_class}::{caller_method}]"
        return f"{timestamp} {location}"
    else:
        return timestamp


def configure_logger():
    # Importar la configuracion centralizada del archivo principal
    try:
        from LGA_mediaManager import configure_logger as main_configure_logger

        return main_configure_logger()
    except ImportError:
        # Fallback en caso de problemas de importacion
        import logging

        logger = logging.getLogger("LGA_MediaManager")
        return logger


# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


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


class CopyThread(QThread):
    start_copying_signal = Signal(str, str)
    finishedCopying = Signal(str)  # Modificado para emitir el directorio especifico
    finishedCopyingUnico = Signal(str)
    errorOccurred = Signal(str)  # Senal para enviar mensajes de error
    confirmationNeeded = Signal(
        str, str, str, int, int, str, int, str, str
    )  # Anade los parametros necesarios para copy_sequence
    confirmationNeededUnico = Signal(str, str, str)  # Mensaje, destino, origen
    copyCancelled = Signal()  # senal de que tiene que cerrar ventana de Copying...
    copyCancelledUnico = Signal()

    def __init__(self, source_file_path, dest_folder, parent=None):
        super(CopyThread, self).__init__(parent)
        self.source_file_path = source_file_path
        self.start_copying_signal.connect(self.copy_single_file)
        self.dest_folder = dest_folder
        # Agregar atributos para almacenar informacion de la secuencia
        self.start_frame = None
        self.end_frame = None
        self.file_base = None
        self.frame_padding = None
        self.extension = None
        self.specific_dest_folder = None
        # Configurar logger
        self.logger = configure_logger()

    def copy_sequence(
        self,
        start_frame,
        end_frame,
        file_base,
        frame_padding,
        extension,
        specific_dest_folder,
    ):
        for frame in range(start_frame, end_frame + 1):
            frame_file = f"{file_base.replace('#' * frame_padding, str(frame).zfill(frame_padding))}{extension}"
            dest_file_path = os.path.join(
                specific_dest_folder, os.path.basename(frame_file)
            )
            try:
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"      Copied seq sobreescribir: {frame_file} to {dest_file_path}"
                    )
                )
                shutil.copy(frame_file, dest_file_path)
            except Exception as e:
                nuke.executeInMainThread(
                    lambda: self.logger.debug(f"      ++++Error copying: {e}")
                )

    def copy_single_file(self, source_path, dest_path):

        try:
            shutil.copy(source_path, dest_path)
            self.finishedCopyingUnico.emit(
                dest_path
            )  # Emite la senal indicando que la copia ha finalizado
        except Exception as e:
            self.errorOccurred.emit(f"Error while copying: {e}")

    def run(self):
        start_copy_time = time.time()
        nuke.executeInMainThread(
            lambda: self.logger.debug(
                f"  copy execution time start: {start_copy_time} seconds"
            )
        )

        nuke.executeInMainThread(
            lambda: self.logger.debug("  Copying in background thread")
        )
        # Normalizar las rutas de origen y destino
        normalized_source_path = os.path.normpath(self.source_file_path)
        normalized_dest_folder = os.path.normpath(self.dest_folder)
        # Inicializa el contador de archivos
        copied_files_count = 0

        if "#" in normalized_source_path:
            # Identificar el nombre de la carpeta contenedora
            source_folder = os.path.dirname(normalized_source_path)
            folder_name = os.path.basename(source_folder)

            # Verificar y crear la carpeta en el destino si no existe
            specific_dest_folder = os.path.join(normalized_dest_folder, folder_name)
            self.specific_dest_folder = (
                specific_dest_folder  # Establecer el atributo de la clase
            )

            if not os.path.exists(specific_dest_folder):
                os.makedirs(specific_dest_folder)
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"    Creating folder {specific_dest_folder}"
                    )
                )

            # Copiar los archivos de la secuencia
            frame_range_match = re.search(r"\[(\d+)-(\d+)\]", normalized_source_path)
            if frame_range_match:
                start_frame, end_frame = map(int, frame_range_match.groups())
                file_base = normalized_source_path.split("[")[0]
                extension = normalized_source_path.split("]")[1]
                hash_match = re.search(r"#+", file_base)
                frame_padding = len(hash_match.group()) if hash_match else 1
                # Almacenar los detalles de la secuencia
                self.start_frame = start_frame
                self.end_frame = end_frame
                self.file_base = file_base
                self.frame_padding = frame_padding
                self.extension = extension
                self.specific_dest_folder = specific_dest_folder

                # Solo verifica el primer archivo de la secuencia
                first_frame_file = f"{file_base.replace('#' * frame_padding, str(start_frame).zfill(frame_padding))}{extension}"
                if not os.path.exists(first_frame_file):
                    error_message = f"The file does not exist: {first_frame_file}"
                    self.errorOccurred.emit(error_message)
                    return  # No proceder si el primer archivo no existe

                # Comprobar si el primer archivo de la secuencia ya existe en el destino
                dest_first_frame_file_path = os.path.join(
                    specific_dest_folder, os.path.basename(first_frame_file)
                )
                if os.path.exists(dest_first_frame_file_path):
                    confirm_message = f"The sequence starting with {os.path.basename(first_frame_file)} already exists in the destination. Do you want to overwrite it?"
                    self.confirmationNeeded.emit(
                        confirm_message,
                        dest_first_frame_file_path,
                        first_frame_file,
                        start_frame,
                        end_frame,
                        file_base,
                        frame_padding,
                        extension,
                        specific_dest_folder,
                    )
                    # self.confirmationNeeded.emit(confirm_message, dest_first_frame_file_path, first_frame_file)
                    return  # Esperar confirmacion antes de proceder

                # Si el archivo no existe o si el usuario confirmo la sobrescritura, copiar la secuencia
                for frame in range(start_frame, end_frame + 1):
                    frame_file = f"{file_base.replace('#' * frame_padding, str(frame).zfill(frame_padding))}{extension}"
                    dest_file_path = os.path.join(
                        specific_dest_folder, os.path.basename(frame_file)
                    )
                    nuke.executeInMainThread(
                        lambda: self.logger.debug(
                            f"      Copied seq unico: {frame_file} to {dest_file_path}"
                        )
                    )
                    # try:
                    #    print(f"Copied seq unico: {frame_file} to {dest_file_path}")
                    shutil.copy(frame_file, dest_file_path)
                    copied_files_count += 1  # Incrementa el contador
                    # except Exception as e:
                    #    print(f"Error copying: {e}")
                self.finishedCopying.emit(
                    specific_dest_folder
                )  # Emite la senal indicando que la copia ha finalizado
        else:
            copied_files_count = 1
            # Para archivos unicos, verifica primero si el archivo existe
            if os.path.exists(normalized_source_path):
                self.specific_dest_folder = (
                    self.dest_folder
                )  # Esto deberia ser solo el directorio
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"        normalized_source_path: {normalized_source_path}"
                    )
                )
                dest_file_path = os.path.join(
                    self.specific_dest_folder, os.path.basename(normalized_source_path)
                )
                nuke.executeInMainThread(
                    lambda: self.logger.debug(
                        f"        Checking if FILE dest_file_path {dest_file_path} exists in destination..."
                    )
                )

                # Verifica si el archivo ya existe en el destino
                if os.path.exists(dest_file_path):
                    # Si existe, emite una senal para pedir confirmacion
                    confirm_message = f"The file {os.path.basename(normalized_source_path)} already exists in the destination. Do you want to overwrite it?"
                    self.confirmationNeededUnico.emit(
                        confirm_message,
                        self.specific_dest_folder,
                        normalized_source_path,
                    )

                # Si no existe, copia el archivo
                else:
                    dest_folder_path = os.path.dirname(dest_file_path)
                    self.start_copying_signal.emit(
                        normalized_source_path, dest_folder_path
                    )
            else:
                # Si el archivo no existe, muestra un mensaje de error
                error_message = f"The file does not exist: {normalized_source_path}"
                self.errorOccurred.emit(error_message)

        end_time = time.time()
        nuke.executeInMainThread(
            lambda: self.logger.debug(
                f"      Copied {copied_files_count} files in {end_time - start_copy_time} seconds."
            )
        )


class DeleteThread(QThread):
    deleteRow = Signal(int)
    # finishedDeleting = Signal()

    def __init__(self, file_path, main_window, parent=None):
        super(DeleteThread, self).__init__(parent)
        self.file_path = file_path
        self.main_window = (
            main_window  # Referencia a la instancia principal de FileScanner
        )

    def run(self):
        debug_print("--------------- run (delete) ----------------")
        normalized_file_path = self.main_window.normalize_sequence_path_for_comparison(
            self.file_path
        )
        # print(f"file_path: {self.file_path}")
        # print(f"normalized_file_path: {normalized_file_path}")
        found = False
        for row in range(self.main_window.table.rowCount()):
            table_file_path = (
                self.main_window.table.item(row, 0).text().replace("\\", "/").lower()
            )
            normalized_table_file_path = (
                self.main_window.normalize_sequence_path_for_comparison(table_file_path)
            )
            if normalized_table_file_path == normalized_file_path:
                # Verificar si el nombre del archivo en la tabla contiene '#'
                # print(f"table_file_path: {table_file_path}")
                if "#" in table_file_path:
                    # Es una secuencia de cuadros, expandir rango de frames
                    # print("es secuencia")
                    frame_range_match = re.search(r"\[(\d+)-(\d+)\]", table_file_path)
                    if frame_range_match:
                        start_frame, end_frame = map(int, frame_range_match.groups())
                        file_base = table_file_path.split("[")[0]
                        extension = table_file_path.split("]")[1]
                        hash_match = re.search(r"#+", file_base)
                        frame_padding = len(hash_match.group()) if hash_match else 1

                        all_frame_files = [
                            f"{file_base.replace('#' * frame_padding, str(frame).zfill(frame_padding))}{extension}"
                            for frame in range(start_frame, end_frame + 1)
                        ]
                else:
                    # No es una secuencia, es un archivo unico
                    all_frame_files = table_file_path.replace(
                        "/", "\\"
                    )  # Reemplazar barras normales con barras invertidas
                    # print(f"Delete file NO Seq: {all_frame_files}") # SOLO USAR PRINT COMENTANDO EL BORRADO O SE CUELGA!
                    send2trash.send2trash(all_frame_files)
                    # os.remove(all_frame_files)

                # Comprobar si la carpeta es borrable
                folder_delete_value = (
                    self.main_window.table.item(row, 3).text().lower() == "true"
                )
                if (
                    folder_delete_value and "#" in table_file_path
                ):  # Solo intentar borrar la carpeta si es una secuencia
                    folder_path = os.path.dirname(table_file_path).replace(
                        "/", "\\"
                    )  # Normalizar la ruta de la carpeta
                    # print(f"Delete folder Seq: {folder_path}")
                    send2trash.send2trash(folder_path)
                else:
                    # Borrado de archivos individualmente si la carpeta no se puede borrar
                    if "#" in table_file_path:
                        # Borrado de archivos de la secuencia
                        for frame_file in all_frame_files:
                            normalized_frame_file = frame_file.replace(
                                "/", "\\"
                            )  # Normalizar la ruta
                            # print(f"Delete file Seq: {normalized_frame_file}")
                            send2trash.send2trash(normalized_frame_file)

                self.deleteRow.emit(row)
                found = True
                break

        if not found:
            print(f"File path not found in the table: {normalized_file_path}")


class TransparentTextDelegate(QItemDelegate):
    # Clase para crear la interfaz de usuario
    def paint(self, painter, option, index):
        # Modificar el color del texto para todos los estados
        if index.column() == 0:  # Aplicar solo en la columna 'Footage'
            # Configurar el color del texto como transparente para esconderlo y que no se pise con el del QLabel
            option.palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0, 0))
            option.palette.setColor(QPalette.Text, QColor(0, 0, 0, 0))
            # Configurar el color de fondo de la seleccion
            if option.state & QStyle.State_Selected:
                option.palette.setColor(
                    QPalette.Highlight, QColor(62, 62, 62)
                )  # Un gris para la seleccion

        else:  # Para otras columnas, establece el color del texto para el estado seleccionado
            if option.state & QStyle.State_Selected:
                option.palette.setColor(
                    QPalette.Highlight, QColor(62, 62, 62)
                )  # Color de fondo de seleccion
                option.palette.setColor(
                    QPalette.HighlightedText, QColor(200, 200, 200)
                )  # Color del texto seleccionado

        super(TransparentTextDelegate, self).paint(painter, option, index)


class LoadingWindow(QWidget):
    # Clase que sirve para abrir las ventanas de Scanning, Copying, Deleting
    def __init__(self, message, parent=None):
        super(LoadingWindow, self).__init__(parent)
        self.setFixedSize(200, 50)  # Ajusta el tamano segun necesites
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Configura la hoja de estilos para la ventana y el texto
        self.setStyleSheet(
            "background-color: #282828; color: white; font-weight: bold;"
        )

        layout = QVBoxLayout(self)
        self.label = QLabel(message, self)
        self.label.setAlignment(Qt.AlignCenter)  # Centrar el texto
        layout.addWidget(self.label)

    def stop(self):
        self.close()


class StartupWindow(QWidget):
    def __init__(self, message, parent=None):
        super(StartupWindow, self).__init__(parent)
        self.setFixedSize(300, 100)
        self.setWindowTitle("Starting...")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Configura la hoja de estilos para la ventana y el texto
        self.setStyleSheet(
            "background-color: #282828; color: white; font-weight: bold;"
        )

        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #444;
                border-radius: 2px;
                text-align: center;
                background-color: #222;
            }
            QProgressBar::chunk {
                background-color: #666;
                width: 1px;
            }
        """
        )
        layout.addWidget(self.progressBar)

        self.setLayout(layout)

        # Configurar un temporizador para actualizar la barra de progreso
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgressBar)
        self.timer.start(100)  # Actualizar cada 100 milisegundos

    def updateProgressBar(self):
        current_value = self.progressBar.value()
        if current_value < 100:
            self.progressBar.setValue(current_value + 1)
        else:
            self.timer.stop()  # Detener el temporizador cuando llegue a 100

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def stop(self):
        self.timer.stop()  # Asegurarse de detener el temporizador
        self.close()


class ScannerSignals(QObject):
    progress = Signal(int)  # Para actualizar la barra de progreso
    finished = Signal()  # Para indicar que terminó el escaneo
    files_found = Signal(list)  # Para enviar los archivos encontrados


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

            root_items = os.listdir(self.file_scanner.project_folder)
            for item in root_items:
                item_path = os.path.join(self.file_scanner.project_folder, item)
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

            # Contar nodos Read para el cálculo del progreso
            read_nodes = nuke.allNodes("Read")
            total_reads = len(read_nodes)

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
                self.signals.progress.emit(progress)
                # Forzar el procesamiento de eventos de la UI
                QApplication.processEvents()
                # Pequeña pausa para permitir que la UI se actualice
                time.sleep(0.001)

            # Primera fase
            self.logger.debug(
                f"\n{self.get_timestamp()} Primera fase ({self.Etapa1_inicio}-{self.Etapa1_fin}%):"
            )
            processed_items = 0  # Reiniciar contador para la primera fase

            for item in root_items:
                item_path = os.path.join(self.file_scanner.project_folder, item)
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
            files_data = self.find_files(self.file_scanner.project_folder)
            find_files_time = time.time() - find_files_start

            # Segunda fase
            self.logger.debug(
                f"\n{self.get_timestamp()} Segunda fase ({self.Etapa3_inicio}-{self.Etapa3_fin}%):"
            )
            processed_items = 0  # Reiniciar contador para la segunda fase

            # Marcar inicio de search_unmatched_reads
            reads_start = time.time()
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
                self.signals.progress.emit(progress)
                QApplication.processEvents()

        # Log del inicio de la etapa 2
        self.logger.debug(
            f"\n{self.get_timestamp()} Segunda fase ({self.Etapa2_inicio}-{self.Etapa2_fin}%):"
        )

        for root, dirs, files in os.walk(folder):
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
