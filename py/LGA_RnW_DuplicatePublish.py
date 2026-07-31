"""
____________________________________________________________________

  LGA_RnW_DuplicatePublish v1.01 | Lega

  Duplica en disco la secuencia de un Read renombrandola con el
  numero de version del script actual. Sirve para re-renderizar solo
  un rango corto sin tener que volver a procesar la secuencia entera.

  v1.01: Cuando el rango del Read no coincide con los frames en disco
         se ofrecen tres opciones (Cancel, Copy read range, Copy disk
         range) en vez de asumir siempre el rango del disco.
  v1.00: Version inicial.
____________________________________________________________________
"""

import os
import re
import shutil
import time

import nuke

from LGA_QtAdapter_ToolPack import QtWidgets, QtCore

QApplication = QtWidgets.QApplication
QDialog = QtWidgets.QDialog
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QProgressBar = QtWidgets.QProgressBar
Qt = QtCore.Qt
QObject = QtCore.QObject
QThread = QtCore.QThread
QTimer = QtCore.QTimer
Signal = QtCore.Signal


# Variable global para activar o desactivar los debug_prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print("[LGA_RnW_DuplicatePublish]", *message)


# ---------------------------------------------------------------------------
#                                  Estilos
# ---------------------------------------------------------------------------
# Paleta compartida con el resto de las apps (LGA_Base_QT_C_Py)
COLOR_WINDOW_BG = "#212121"
COLOR_BLOCK_BG = "#292929"
COLOR_TITLE = "#E8E8E8"
COLOR_VALUE = "#AEAEAE"
COLOR_VIOLET = "#443a91"
COLOR_VIOLET_TRACK = "#393959"
COLOR_WARNING = "#ffd369"
COLOR_ERROR = "#ff6b6b"
COLOR_OK = "#6bc9ff"

BUTTON_STYLE = """
    QPushButton {
        background-color: #2a2a2a;
        color: #cccccc;
        border: none;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        padding: 8px 20px;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #443a91;
    }
    QPushButton:pressed {
        background-color: #2d265e;
    }
"""

PROGRESS_STYLE = """
    QProgressBar {
        background-color: %s;
        border: none;
        border-radius: 5px;
        text-align: center;
        color: #cccccc;
        font-size: 11px;
        min-height: 18px;
        max-height: 18px;
    }
    QProgressBar::chunk {
        background-color: %s;
        border-radius: 5px;
    }
""" % (
    COLOR_VIOLET_TRACK,
    COLOR_VIOLET,
)


# Coloreado de paths reutilizado de la ventana Write Path Review para mantener
# la misma lectura visual. Si el modulo no esta disponible se usa texto plano.
try:
    from LGA_Write_Presets_Check import (
        split_path_at_violet_end,
        get_shot_folder_parts,
    )
except Exception:  # pragma: no cover - fallback defensivo
    split_path_at_violet_end = None
    get_shot_folder_parts = None


# ---------------------------------------------------------------------------
#                          Helpers de paths y versiones
# ---------------------------------------------------------------------------
# Token de secuencia: %04d, %03d o ####
SEQUENCE_TOKEN_RE = re.compile(r"%0(\d+)d|#+")

# Token de version: se usa siempre la ultima coincidencia del nombre
VERSION_RE = re.compile(r"_v(\d+)", re.IGNORECASE)


def parse_sequence_path(path):
    """
    Descompone el path de una secuencia en sus partes.

    Retorna un dict con directory, prefix, token, suffix, frame_sep y seq_base,
    o None si el path no tiene patron de secuencia.
    """
    if not path:
        return None

    normalized = path.replace("\\", "/")
    directory = os.path.dirname(normalized)
    file_name = os.path.basename(normalized)

    matches = list(SEQUENCE_TOKEN_RE.finditer(file_name))
    if not matches:
        return None

    match = matches[-1]
    prefix = file_name[: match.start()]
    suffix = file_name[match.end() :]

    # El separador de frames puede ser "_" o "." y se preserva en el destino
    frame_sep = ""
    if prefix and prefix[-1] in "._":
        frame_sep = prefix[-1]
        seq_base = prefix[:-1]
    else:
        seq_base = prefix

    return {
        "directory": directory,
        "prefix": prefix,
        "token": match.group(0),
        "suffix": suffix,
        "frame_sep": frame_sep,
        "seq_base": seq_base,
    }


def scan_sequence_files(directory, prefix, suffix):
    """
    Lista los archivos de la secuencia presentes en disco.

    Retorna una lista de tuplas (frame, digits, file_name) ordenada por frame.
    Los digitos se guardan tal cual estan en disco para preservar el padding.
    """
    result = []
    if not directory or not os.path.isdir(directory):
        return result

    pattern = re.compile(
        r"^%s(\d+)%s$" % (re.escape(prefix), re.escape(suffix)), re.IGNORECASE
    )

    with os.scandir(directory) as entries:
        for entry in entries:
            match = pattern.match(entry.name)
            if not match:
                continue
            try:
                if not entry.is_file():
                    continue
            except OSError:
                continue
            result.append((int(match.group(1)), match.group(1), entry.name))

    result.sort(key=lambda item: item[0])
    return result


def find_version_token(name):
    """
    Devuelve (token, start, end) del ultimo _vNN del nombre, o None.
    """
    if not name:
        return None
    matches = list(VERSION_RE.finditer(name))
    if not matches:
        return None
    match = matches[-1]
    return match.group(0), match.start(), match.end()


def strip_version(name):
    """Devuelve el nombre sin su token de version."""
    found = find_version_token(name)
    if not found:
        return name
    _token, start, end = found
    return name[:start] + name[end:]


def replace_version(name, new_token):
    """Reemplaza el token de version del nombre por new_token."""
    found = find_version_token(name)
    if not found:
        return None
    _token, start, end = found
    return name[:start] + new_token + name[end:]


def format_frame_range(frames):
    """Texto legible del rango de una lista de frames."""
    if not frames:
        return "no frames found"
    first = frames[0][0]
    last = frames[-1][0]
    return "%d - %d (%d frames)" % (first, last, len(frames))


def has_missing_frames(frames):
    """True si hay huecos dentro del rango de la secuencia."""
    if len(frames) < 2:
        return False
    return len(frames) != (frames[-1][0] - frames[0][0] + 1)


def path_to_html(path):
    """
    Devuelve el path en HTML con el mismo coloreado que Write Path Review.
    """
    if not path:
        return "<span style='color:%s;'>-</span>" % COLOR_VALUE

    if split_path_at_violet_end is None or get_shot_folder_parts is None:
        return "<span style='color:%s;'>%s</span>" % (COLOR_VALUE, path)

    try:
        script_path = nuke.root().name()
        if not script_path or script_path == "Root":
            script_path = None
        shot_folder_parts = get_shot_folder_parts(script_path)
        parts = split_path_at_violet_end(path, shot_folder_parts, is_sequence=True)
        lines = [part for part in parts if part]
        if lines:
            return "<br>".join(lines)
    except Exception as error:
        debug_print("Error coloreando path:", error)

    return "<span style='color:%s;'>%s</span>" % (COLOR_VALUE, path)


def plain_value(text, color=None):
    """Envuelve un texto simple con el color de valor de los bloques."""
    return "<span style='color:%s;'>%s</span>" % (color or COLOR_VALUE, text)


def build_copy_jobs(context, source_frames):
    """
    Arma la lista de (origen, destino) preservando el padding de cada frame.
    """
    jobs = []
    for _frame, digits, file_name in source_frames:
        source_path = os.path.join(context["src_dir"], file_name)
        destination_name = "%s%s%s" % (
            context["dst_prefix"],
            digits,
            context["dst_suffix"],
        )
        destination_path = os.path.join(context["dst_dir"], destination_name)
        jobs.append((source_path, destination_path))
    return jobs


# ---------------------------------------------------------------------------
#                                  Ventanas
# ---------------------------------------------------------------------------
class BaseDialog(QDialog):
    """Dialogo base con el estilo visual de la ventana Write Path Review."""

    def __init__(self, title, parent=None):
        super(BaseDialog, self).__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle(title)
        self.setStyleSheet(
            "background-color: %s; border-radius: 10px;" % COLOR_WINDOW_BG
        )
        self.setModal(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(14)

    def add_block(self, title, value_html):
        """Agrega un bloque con titulo y valor sobre fondo propio."""
        content_widget = QWidget()
        content_widget.setStyleSheet(
            "QWidget { background-color: %s; border-radius: 6px; }" % COLOR_BLOCK_BG
        )

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(6)

        title_label = QLabel(
            "<span style='color:%s; font-size:13px; letter-spacing:0.5px;'>%s</span>"
            % (COLOR_TITLE, title.upper())
        )
        title_label.setStyleSheet("font-size:13px; padding-bottom:2px;")
        content_layout.addWidget(title_label)

        value_label = QLabel(value_html)
        value_label.setStyleSheet("font-size:13px; padding:4px 0px;")
        value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_layout.addWidget(value_label)

        self.main_layout.addWidget(content_widget)
        return value_label

    def add_note(self, html):
        """Agrega una linea de texto suelta debajo de los bloques."""
        label = QLabel(html)
        label.setStyleSheet("font-size:12px;")
        label.setWordWrap(True)
        self.main_layout.addWidget(label)
        return label

    def showEvent(self, event):
        super(BaseDialog, self).showEvent(event)
        self.activateWindow()
        self.raise_()
        self.setFocus()


class MessageDialog(BaseDialog):
    """Ventana de mensaje con bloques informativos y botones configurables."""

    def __init__(self, title, blocks=None, note_html=None, buttons=None, parent=None):
        super(MessageDialog, self).__init__(title, parent)

        for block_title, block_value in blocks or []:
            self.add_block(block_title, block_value)

        if note_html:
            self.add_note(note_html)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        for label, role in buttons or [("OK", "accept")]:
            button = QPushButton(label)
            button.setStyleSheet(BUTTON_STYLE)
            if role == "accept":
                button.clicked.connect(self.accept)
            else:
                button.clicked.connect(self.reject)
            buttons_layout.addWidget(button)

        self.main_layout.addLayout(buttons_layout)
        self.setMinimumWidth(500)
        self.adjustSize()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        else:
            super(MessageDialog, self).keyPressEvent(event)


# Codigo base de resultado para las opciones; 0 y 1 los usa QDialog
CHOICE_RESULT_OFFSET = 2


class ChoiceDialog(BaseDialog):
    """
    Ventana con varias opciones excluyentes mas Cancel.
    Cada opcion cierra el dialogo con su propio codigo de resultado.
    """

    def __init__(
        self,
        title,
        blocks=None,
        note_html=None,
        options=None,
        cancel_label="Cancel",
        parent=None,
    ):
        super(ChoiceDialog, self).__init__(title, parent)

        self.options = options or []

        for block_title, block_value in blocks or []:
            self.add_block(block_title, block_value)

        if note_html:
            self.add_note(note_html)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_button = QPushButton(cancel_label)
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        for index, option in enumerate(self.options):
            button = QPushButton(option[0])
            button.setStyleSheet(BUTTON_STYLE)
            code = index + CHOICE_RESULT_OFFSET
            button.clicked.connect(
                lambda _checked=False, result=code: self.done(result)
            )
            buttons_layout.addWidget(button)

        self.main_layout.addLayout(buttons_layout)
        self.setMinimumWidth(500)
        self.adjustSize()

    def keyPressEvent(self, event):
        # Enter no elige por el usuario: hay mas de una opcion valida
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.accept()
        else:
            super(ChoiceDialog, self).keyPressEvent(event)


class ProgressDialog(BaseDialog):
    """Ventana con barra de progreso violeta para las tareas en background."""

    cancelled = Signal()

    def __init__(self, title, message, show_cancel=True, parent=None):
        super(ProgressDialog, self).__init__(title, parent)

        self.cancel_requested = False
        self.closing_by_code = False

        self.message_label = QLabel(plain_value(message, COLOR_TITLE))
        self.message_label.setStyleSheet("font-size:13px;")
        self.main_layout.addWidget(self.message_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(PROGRESS_STYLE)
        self.progress_bar.setRange(0, 0)  # Indeterminada hasta el primer progreso
        self.progress_bar.setTextVisible(True)
        self.main_layout.addWidget(self.progress_bar)

        self.detail_label = QLabel(plain_value(""))
        self.detail_label.setStyleSheet("font-size:11px;")
        self.main_layout.addWidget(self.detail_label)

        if show_cancel:
            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.setStyleSheet(BUTTON_STYLE)
            self.cancel_button.clicked.connect(self.request_cancel)
            buttons_layout.addWidget(self.cancel_button)
            self.main_layout.addLayout(buttons_layout)
        else:
            self.cancel_button = None

        self.setMinimumWidth(460)
        self.adjustSize()

    def set_progress(self, done, total, detail):
        """Actualiza la barra y el detalle del frame en curso."""
        if self.progress_bar.maximum() != total:
            self.progress_bar.setRange(0, max(1, total))
        self.progress_bar.setValue(done)
        self.progress_bar.setFormat("%d / %d" % (done, total))
        if detail:
            self.detail_label.setText(plain_value(detail))

    def request_cancel(self):
        """Marca la cancelacion; el worker corta en el proximo frame."""
        if self.cancel_requested:
            return
        self.cancel_requested = True
        if self.cancel_button:
            self.cancel_button.setEnabled(False)
        self.detail_label.setText(plain_value("Cancelling...", COLOR_WARNING))
        self.cancelled.emit()

    def close_by_code(self):
        """Cierra la ventana sin interpretarlo como cancelacion del usuario."""
        self.closing_by_code = True
        self.close()

    def keyPressEvent(self, event):
        # Enter no cierra la ventana para no cortar la copia sin querer
        if event.key() == Qt.Key_Escape:
            self.request_cancel()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.accept()
        else:
            super(ProgressDialog, self).keyPressEvent(event)

    def closeEvent(self, event):
        if not self.closing_by_code:
            self.request_cancel()
        super(ProgressDialog, self).closeEvent(event)


# Referencia a la QApplication para que no la junte el GC fuera de Nuke
_app = None


def ensure_app():
    """Garantiza que exista una QApplication antes de crear ventanas."""
    global _app
    _app = QApplication.instance()
    if _app is None:
        _app = QApplication([])
    return _app


def show_message(title, blocks=None, note_html=None, ok_label="OK"):
    """Muestra una ventana informativa con un solo boton."""
    ensure_app()
    dialog = MessageDialog(title, blocks, note_html, [(ok_label, "accept")])
    dialog.exec_()


def ask_confirmation(title, blocks=None, note_html=None, confirm_label="Continue"):
    """Muestra una ventana de confirmacion. True si el usuario acepta."""
    ensure_app()
    dialog = MessageDialog(
        title,
        blocks,
        note_html,
        [("Cancel", "reject"), (confirm_label, "accept")],
    )
    return dialog.exec_() == QDialog.Accepted


def ask_choice(title, blocks=None, note_html=None, options=None, cancel_label="Cancel"):
    """
    Muestra una ventana con varias opciones. Devuelve el valor de la opcion
    elegida, o None si el usuario cancela.
    """
    ensure_app()
    options = options or []
    dialog = ChoiceDialog(title, blocks, note_html, options, cancel_label)
    result = dialog.exec_()
    index = result - CHOICE_RESULT_OFFSET
    if 0 <= index < len(options):
        return options[index][1]
    return None


def show_error(message_html, blocks=None):
    """Ventana de error con el mismo estilo que el resto."""
    note = "<span style='color:%s; font-weight:bold;'>%s</span>" % (
        COLOR_ERROR,
        message_html,
    )
    show_message("Duplicate Publish", blocks, note)


# ---------------------------------------------------------------------------
#                                  Workers
# ---------------------------------------------------------------------------
class ScanWorker(QThread):
    """Escanea origen y destino en disco fuera del hilo principal."""

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, context):
        super(ScanWorker, self).__init__()
        self.context = context

    def run(self):
        try:
            source_frames = scan_sequence_files(
                self.context["src_dir"],
                self.context["src_prefix"],
                self.context["src_suffix"],
            )
            destination_frames = scan_sequence_files(
                self.context["dst_dir"],
                self.context["dst_prefix"],
                self.context["dst_suffix"],
            )
            self.done.emit({"source": source_frames, "destination": destination_frames})
        except Exception as error:
            self.failed.emit(str(error))


class CopyWorker(QThread):
    """Copia la secuencia frame por frame reportando progreso."""

    progress = Signal(int, int, str)
    done = Signal(int, bool)
    failed = Signal(str)

    def __init__(self, jobs, destination_dir):
        super(CopyWorker, self).__init__()
        self.jobs = jobs
        self.destination_dir = destination_dir
        self.cancel_requested = False

    def request_cancel(self):
        self.cancel_requested = True

    def run(self):
        copied = 0
        try:
            if not os.path.isdir(self.destination_dir):
                os.makedirs(self.destination_dir)

            total = len(self.jobs)
            for source_path, destination_path in self.jobs:
                if self.cancel_requested:
                    self.done.emit(copied, True)
                    return
                shutil.copy2(source_path, destination_path)
                copied += 1
                self.progress.emit(copied, total, os.path.basename(destination_path))

            self.done.emit(copied, False)
        except Exception as error:
            self.failed.emit(str(error))


# ---------------------------------------------------------------------------
#                                Controlador
# ---------------------------------------------------------------------------
class DuplicateController(QObject):
    """
    Encadena scan, confirmaciones y copia manteniendo la UI libre.
    Todo el IO corre en QThreads y las ventanas se abren siempre en el
    hilo principal a traves de las senales de los workers.
    """

    def __init__(self, context):
        super(DuplicateController, self).__init__()
        self.context = context
        self.scan_worker = None
        self.copy_worker = None
        self.scan_dialog = None
        self.scan_timer = None
        self.progress_dialog = None
        self.start_time = 0.0

    def wait_for_workers(self):
        """Espera a que los threads terminen antes de soltar el controlador."""
        for worker in (self.scan_worker, self.copy_worker):
            try:
                if worker is not None and worker.isRunning():
                    worker.wait(5000)
            except Exception as error:
                debug_print("Error esperando al worker:", error)

    # --- Scan -------------------------------------------------------------
    def start(self):
        self.scan_worker = ScanWorker(self.context)
        self.scan_worker.done.connect(self._on_scan_done)
        self.scan_worker.failed.connect(self._on_scan_failed)

        # La ventana de scan aparece solo si el disco tarda en responder
        self.scan_timer = QTimer()
        self.scan_timer.setSingleShot(True)
        self.scan_timer.timeout.connect(self._show_scan_dialog)
        self.scan_timer.start(300)

        self.scan_worker.start()

    def _show_scan_dialog(self):
        if self.scan_dialog is not None:
            return
        self.scan_dialog = ProgressDialog(
            "Duplicate Publish", "Scanning sequence...", show_cancel=False
        )
        self.scan_dialog.show()

    def _close_scan_dialog(self):
        if self.scan_timer is not None:
            self.scan_timer.stop()
            self.scan_timer = None
        if self.scan_dialog is not None:
            self.scan_dialog.close_by_code()
            self.scan_dialog = None

    def _on_scan_failed(self, message):
        self._close_scan_dialog()
        show_error("Could not read the sequence folder:<br>%s" % message)
        _release_controller()

    def _on_scan_done(self, info):
        self._close_scan_dialog()

        source_frames = info["source"]
        destination_frames = info["destination"]

        if not source_frames:
            show_error(
                "No frames found on disk for the selected Read.",
                [("Sequence", path_to_html(self.context["src_display"]))],
            )
            _release_controller()
            return

        frames_to_copy = self._choose_frames(source_frames)
        if not frames_to_copy:
            _release_controller()
            return

        if not self._confirm_destination(destination_frames):
            _release_controller()
            return

        self._start_copy(frames_to_copy)

    # --- Confirmaciones ---------------------------------------------------
    def _choose_frames(self, source_frames):
        """
        Decide que frames se copian cuando el rango del Read no coincide con
        lo que hay en disco. Devuelve la lista elegida o None si se cancela.
        """
        read_first = self.context["read_first"]
        read_last = self.context["read_last"]
        disk_first = source_frames[0][0]
        disk_last = source_frames[-1][0]
        gaps = has_missing_frames(source_frames)

        if read_first == disk_first and read_last == disk_last and not gaps:
            return source_frames

        # Frames del disco que caen dentro del rango del Read
        frames_in_read_range = [
            item for item in source_frames if read_first <= item[0] <= read_last
        ]

        read_total = read_last - read_first + 1
        read_text = "%d - %d (%d frames)" % (read_first, read_last, read_total)
        if len(frames_in_read_range) != read_total:
            read_text += " - %d available on disk" % len(frames_in_read_range)

        disk_text = format_frame_range(source_frames)
        if gaps:
            disk_text += " - with missing frames inside the range"

        note = (
            "<span style='color:%s; font-weight:bold;'>The Read range does not match "
            "the frames on disk.</span><br>"
            "<span style='color:%s;'>Choose which frames to copy.</span>"
        ) % (COLOR_WARNING, COLOR_VALUE)

        options = []
        if frames_in_read_range:
            options.append(("Copy read range", "read"))
        options.append(("Copy disk range", "disk"))

        choice = ask_choice(
            "Duplicate Publish",
            [
                ("Read range", plain_value(read_text)),
                ("On disk", plain_value(disk_text)),
            ],
            note,
            options,
        )

        if choice == "read":
            return frames_in_read_range
        if choice == "disk":
            return source_frames
        return None

    def _confirm_destination(self, destination_frames):
        """Avisa si el destino ya tiene frames de esa version."""
        if not destination_frames:
            return True

        note = (
            "<span style='color:%s; font-weight:bold;'>The destination already "
            "contains %d frames.</span><br>"
            "<span style='color:%s;'>Existing files with the same frame numbers will "
            "be overwritten.</span>"
        ) % (COLOR_WARNING, len(destination_frames), COLOR_VALUE)

        return ask_confirmation(
            "Duplicate Publish",
            [
                ("Destination", path_to_html(self.context["dst_display"])),
                (
                    "Existing frames",
                    plain_value(format_frame_range(destination_frames)),
                ),
            ],
            note,
            confirm_label="Overwrite",
        )

    # --- Copia ------------------------------------------------------------
    def _start_copy(self, source_frames):
        jobs = build_copy_jobs(self.context, source_frames)

        self.progress_dialog = ProgressDialog(
            "Duplicate Publish",
            "Copying %d frames to %s" % (len(jobs), self.context["dst_seq_base"]),
        )
        self.progress_dialog.set_progress(0, len(jobs), "")

        self.copy_worker = CopyWorker(jobs, self.context["dst_dir"])
        self.copy_worker.progress.connect(self._on_copy_progress)
        self.copy_worker.done.connect(self._on_copy_done)
        self.copy_worker.failed.connect(self._on_copy_failed)
        self.progress_dialog.cancelled.connect(self.copy_worker.request_cancel)

        self.start_time = time.time()
        self.progress_dialog.show()
        self.copy_worker.start()

    def _close_progress_dialog(self):
        if self.progress_dialog is not None:
            self.progress_dialog.close_by_code()
            self.progress_dialog = None

    def _on_copy_progress(self, done, total, detail):
        if self.progress_dialog is not None:
            self.progress_dialog.set_progress(done, total, detail)

    def _on_copy_failed(self, message):
        self._close_progress_dialog()
        show_error("Error while copying the sequence:<br>%s" % message)
        _release_controller()

    def _on_copy_done(self, copied, was_cancelled):
        elapsed = time.time() - self.start_time
        self._close_progress_dialog()

        if was_cancelled:
            note = (
                "<span style='color:%s; font-weight:bold;'>Cancelled.</span><br>"
                "<span style='color:%s;'>%d frames were already copied and were not "
                "removed.</span>"
            ) % (COLOR_WARNING, COLOR_VALUE, copied)
            show_message(
                "Duplicate Publish",
                [("Destination", path_to_html(self.context["dst_display"]))],
                note,
            )
            _release_controller()
            return

        note = (
            "<span style='color:%s; font-weight:bold;'>Sequence created.</span><br>"
            "<span style='color:%s;'>%d frames copied in %.1f s.</span>"
        ) % (COLOR_OK, COLOR_VALUE, copied, elapsed)

        show_message(
            "Duplicate Publish",
            [("Created", path_to_html(self.context["dst_display"]))],
            note,
        )
        _release_controller()


# Referencia global para que el controlador y sus threads no los junte el GC
_controller = None


def _release_controller():
    """
    Suelta el controlador esperando primero a que sus threads terminen, para
    no destruir un QThread que todavia esta corriendo.
    """
    global _controller
    controller = _controller
    _controller = None
    if controller is not None:
        controller.wait_for_workers()


# ---------------------------------------------------------------------------
#                                   Entrada
# ---------------------------------------------------------------------------
def build_context():
    """
    Valida la seleccion y arma el contexto de la operacion.

    Retorna (context, error_html, error_blocks). Si context es None hay que
    mostrar el error y cortar.
    """
    script_path = nuke.root().name()
    if not script_path or script_path == "Root":
        return None, "The Nuke script has not been saved yet.", None

    script_base = os.path.splitext(os.path.basename(script_path))[0]
    script_version = find_version_token(script_base)
    if not script_version:
        return (
            None,
            "The script name has no version number (_vNN).",
            [("Script", plain_value(script_base))],
        )
    script_version_token = script_version[0]

    read_nodes = [node for node in nuke.selectedNodes() if node.Class() == "Read"]
    if len(read_nodes) != 1:
        return (
            None,
            "Select one Read node pointing at the sequence to duplicate.",
            None,
        )
    read_node = read_nodes[0]

    try:
        file_path = nuke.filename(read_node)
    except Exception as error:
        debug_print("Error obteniendo el filename del Read:", error)
        file_path = None
    if not file_path:
        file_path = read_node["file"].value()
    if not file_path:
        return None, "The selected Read has no file path.", None

    sequence = parse_sequence_path(file_path)
    if not sequence:
        return (
            None,
            "The selected Read is not a frame sequence.",
            [("Read file", plain_value(file_path.replace("\\", "/")))],
        )

    if not os.path.isdir(sequence["directory"]):
        return (
            None,
            "The sequence folder does not exist.",
            [("Folder", plain_value(sequence["directory"]))],
        )

    sequence_base = sequence["seq_base"]
    if not find_version_token(sequence_base):
        return (
            None,
            "The sequence name has no version number (_vNN).",
            [("Sequence", plain_value(sequence_base))],
        )

    destination_base = replace_version(sequence_base, script_version_token)
    destination_prefix = destination_base + sequence["frame_sep"]

    # Si la secuencia vive en una carpeta propia se crea la carpeta hermana de
    # la version nueva; si esta suelta entre otros archivos, se copia al lado.
    source_dir = sequence["directory"]
    source_dir_name = os.path.basename(source_dir)
    if source_dir_name == sequence_base:
        destination_dir = os.path.join(os.path.dirname(source_dir), destination_base)
    else:
        destination_dir = source_dir
    destination_dir = destination_dir.replace("\\", "/")

    source_file = sequence["prefix"] + sequence["token"] + sequence["suffix"]
    source_display = "%s/%s" % (source_dir, source_file)
    destination_file = destination_prefix + sequence["token"] + sequence["suffix"]
    destination_display = "%s/%s" % (destination_dir, destination_file)

    if destination_display == source_display:
        return (
            None,
            "The sequence is already at the script version (%s)."
            % script_version_token.lstrip("_"),
            [("Sequence", plain_value(sequence_base))],
        )

    context = {
        "script_base": script_base,
        "script_version": script_version_token,
        "seq_base": sequence_base,
        "src_dir": source_dir,
        "src_prefix": sequence["prefix"],
        "src_suffix": sequence["suffix"],
        "src_display": source_display,
        "dst_dir": destination_dir,
        "dst_prefix": destination_prefix,
        "dst_suffix": sequence["suffix"],
        "dst_seq_base": destination_base,
        "dst_display": destination_display,
        "read_first": int(read_node["first"].value()),
        "read_last": int(read_node["last"].value()),
    }
    return context, None, None


def confirm_basename(context):
    """
    Avisa cuando el nombre de la secuencia no coincide con el del script.
    Retorna True si se puede seguir adelante.
    """
    if strip_version(context["seq_base"]) == strip_version(context["script_base"]):
        return True

    note = (
        "<span style='color:%s; font-weight:bold;'>The sequence basename does not "
        "match the script.</span><br>"
        "<span style='color:%s;'>The selected sequence will be duplicated using the "
        "script version (%s).</span>"
    ) % (COLOR_WARNING, COLOR_VALUE, context["script_version"].lstrip("_"))

    return ask_confirmation(
        "Duplicate Publish",
        [
            ("Script", plain_value(context["script_base"])),
            ("Selected sequence", plain_value(context["seq_base"])),
            ("Will be created as", plain_value(context["dst_seq_base"], COLOR_OK)),
        ],
        note,
    )


def main():
    global _controller

    ensure_app()

    context, error_message, error_blocks = build_context()
    if context is None:
        show_error(error_message, error_blocks)
        return

    debug_print("Origen:", context["src_display"])
    debug_print("Destino:", context["dst_display"])

    if not confirm_basename(context):
        return

    _controller = DuplicateController(context)
    _controller.start()


if __name__ == "__main__":
    main()
