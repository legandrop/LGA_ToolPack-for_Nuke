"""
_______________________________________

  LGA_CopyCat_Cleaner v1.0 | Lega
  Verifica que los nodos Inference usen el .cat mas alto en su carpeta
_______________________________________

"""

from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QProgressBar,
    QLabel,
    QPushButton,
)
from PySide2.QtWidgets import QStyledItemDelegate, QStyle
from PySide2.QtGui import QColor, QBrush, QPalette, QFont
from PySide2.QtCore import Qt, QObject, Signal, QThread
import nuke
import os
import re
import sys
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple, Set


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def normalize_path_for_comparison(file_path: str) -> str:
    """Normaliza path para comparacion (case-insensitive y separadores normalizados)."""
    if not file_path:
        return ""
    return file_path.replace("\\", "/").lower()


def extract_model_key_from_name(file_name: str) -> Optional[Tuple[int, int, int]]:
    """
    Intenta extraer clave numerica del nombre de archivo CopyCat.
    Se espera algo como: Training_YYMMDD_HHMMSS.micros.cat
    Devuelve tupla (YYMMDD, HHMMSS, micros) para ordenar. Si falla, None.
    """
    base = os.path.basename(file_name)
    m = re.search(r"_(\d{6})_(\d{6})\.(\d+)(?:\.cat)?$", base)
    if m:
        try:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        except Exception:
            return None
    return None


def pick_highest_cat_file(cat_files: List[str]) -> Optional[str]:
    """
    Devuelve el .cat con clave mas alta segun nombre. Si no se puede parsear ninguno,
    se usa mtime para decidir el mas reciente.
    """
    if not cat_files:
        return None

    keyed: List[Tuple[Tuple[int, int, int], str]] = []
    unkeyed: List[str] = []
    for f in cat_files:
        key = extract_model_key_from_name(f)
        if key is not None:
            keyed.append((key, f))
        else:
            unkeyed.append(f)

    if keyed:
        keyed.sort(key=lambda x: x[0])
        return keyed[-1][1]

    # fallback por mtime si no hay nombres parseables
    try:
        unkeyed.sort(key=lambda p: os.path.getmtime(p))
        return unkeyed[-1]
    except Exception:
        return unkeyed[0] if unkeyed else None


def list_cat_files_in_folder(folder_path: str) -> List[str]:
    """Lista todos los archivos .cat en una carpeta (no recursivo)."""
    try:
        if not folder_path or not os.path.isdir(folder_path):
            return []
        return [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".cat")
            and os.path.isfile(os.path.join(folder_path, f))
        ]
    except Exception:
        return []


# --------------------------------------------------------------------------------------
# Worker en background
# --------------------------------------------------------------------------------------


class ScanWorker(QObject):
    """Escanea nodos Inference y determina el .cat mas alto por carpeta."""

    finished = Signal(list)  # lista de dicts con resultados
    progress = Signal(int, int)  # current, total

    def run(self):
        try:
            inference_nodes = list(nuke.allNodes("Inference"))
        except Exception:
            inference_nodes = []

        total = len(inference_nodes)
        results: List[Dict[str, str]] = []

        for idx, node in enumerate(inference_nodes):
            node_name = node.name() if hasattr(node, "name") else "Inference"
            model_path = ""
            try:
                model_path = node["modelFile"].value()
            except Exception:
                model_path = ""

            status = "Missing"
            latest_path = ""
            note = ""

            if model_path and os.path.isfile(model_path):
                folder = os.path.dirname(model_path)
                cat_files = list_cat_files_in_folder(folder)
                latest_path = pick_highest_cat_file(cat_files) or ""

                if latest_path:
                    if normalize_path_for_comparison(
                        latest_path
                    ) == normalize_path_for_comparison(model_path):
                        status = "Latest"
                        note = "Current model is the highest in folder"
                    else:
                        status = "Outdated"
                        note = "A higher model exists in folder"
                else:
                    status = "Missing"
                    note = "No .cat files found in folder"
            else:
                if model_path:
                    status = "Missing"
                    note = "Model file not found on disk"
                else:
                    status = "Missing"
                    note = "Model file knob is empty"

            results.append(
                {
                    "node_name": node_name,
                    "current_model": model_path or "",
                    "latest_model": latest_path or "",
                    "status": status,
                    "note": note,
                }
            )

            self.progress.emit(idx + 1, total)

        self.finished.emit(results)


# --------------------------------------------------------------------------------------
# UI de resultados (estilo similar a CompareEXR)
# --------------------------------------------------------------------------------------


class ColorMixDelegate(QStyledItemDelegate):
    """Delegado para mezclar colores en selecciones (mismo enfoque que CompareEXR)."""

    def __init__(
        self, table_widget, background_colors, mix_color=(88, 88, 88), parent=None
    ):
        super(ColorMixDelegate, self).__init__(parent)
        self.table_widget = table_widget
        self.background_colors = background_colors
        self.mix_color = mix_color

    def paint(self, painter, option, index):
        row = index.row()
        column = index.column()
        if option.state & QStyle.State_Selected:
            original_color = QColor(self.background_colors[row][column])
            mixed_color = self.mix_colors(
                (original_color.red(), original_color.green(), original_color.blue()),
                self.mix_color,
            )
            option.palette.setColor(QPalette.Highlight, QColor(*mixed_color))
        else:
            original_color = QColor(self.background_colors[row][column])
            option.palette.setColor(QPalette.Base, original_color)
        super(ColorMixDelegate, self).paint(painter, option, index)

    def mix_colors(self, original_color, mix_color):
        r1, g1, b1 = original_color
        r2, g2, b2 = mix_color
        return ((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2)


class ResultsWindow(QWidget):
    """Tabla de resultados de CopyCat Inference."""

    def __init__(self, parent=None):
        super(ResultsWindow, self).__init__(parent)
        self.row_background_colors: List[List[str]] = []
        self.project_folder: str = ""
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("CopyCat Model Checker - Results")
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(
            [
                "Inference Node",
                "Current Model",
                "Latest Model",
                "Status",
                "Clean",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # Desactivar seleccion visual; usaremos click para enfocar nodo
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet(
            """
            QTableView::item:selected {
                color: black;
                background-color: transparent;
            }
        """
        )

        delegate = ColorMixDelegate(self.table, self.row_background_colors)
        self.table.setItemDelegate(delegate)

        font = QFont()
        font.setBold(True)
        self.table.horizontalHeader().setFont(font)

        layout.addWidget(self.table)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.setLayout(layout)

    def set_project_folder(self, project_folder: str):
        # Define la carpeta de proyecto para colorear coincidencias
        self.project_folder = project_folder or ""

    def _get_color_for_level(self, level: int) -> str:
        # Colores copiados del Media Manager
        colors = {
            0: "#ffff66",  # Amarillo
            1: "#28b5b5",  # Verde Cian
            2: "#ff9a8a",  # Naranja pastel
            3: "#0088ff",  # Rojo coral
            4: "#ffd369",  # Amarillo mostaza
            5: "#28b5b5",  # Verde Cian
            6: "#ff9a8a",  # Naranja pastel
            7: "#6bc9ff",  # Celeste
            8: "#ffd369",  # Amarillo mostaza
            9: "#28b5b5",  # Verde Cian
            10: "#ff9a8a",  # Naranja pastel
            11: "#6bc9ff",  # Celeste
        }
        return colors.get(level, "#000000")

    def _build_colored_path_html(self, full_path: str) -> str:
        # Normaliza y colorea cada parte del path; resalta coincidencias con project_folder
        if not full_path:
            return "-"
        parts = full_path.lower().replace("\\", "/").split("/")
        project_parts = (
            self.project_folder.lower().replace("\\", "/").split("/")
            if self.project_folder
            else []
        )

        colored_parts: List[str] = []
        for i, part in enumerate(parts[:-1]):
            if i < len(project_parts) and part == project_parts[i]:
                text_color = (
                    "#c56cf0"  # mismo color que usa Media Manager para el proyecto
                )
            else:
                text_color = self._get_color_for_level(i)
            colored_parts.append(f"<span style='color: {text_color};'>{part}</span>")

        file_name = f"<b style='color: rgb(200, 200, 200);'>{parts[-1]}</b>"
        colored_parts.append(file_name)
        colored_text = '<span style="color: white;">/</span>'.join(colored_parts)
        return colored_text

    def add_result(
        self, node_name: str, current_model: str, latest_model: str, status: str
    ):
        row = self.table.rowCount()
        self.table.insertRow(row)

        node_item = QTableWidgetItem(node_name)
        # Current Model: usar QLabel con HTML coloreado y padding
        current_label = QLabel()
        current_label.setTextFormat(Qt.RichText)
        current_label.setText(self._build_colored_path_html(current_model or ""))
        current_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        current_label.setStyleSheet("padding-left: 6px; padding-right: 6px;")
        latest_display = os.path.basename(latest_model) if latest_model else "-"
        # Latest Model: aplicar mismo estilo de filename que Current (negrita y blanco)
        latest_label = QLabel(
            f"<b style='color: rgb(200, 200, 200);'>{latest_display}</b>"
        )
        latest_label.setTextFormat(Qt.RichText)
        latest_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        latest_label.setStyleSheet("padding-left: 6px; padding-right: 6px;")
        # Status como QLabel para padding
        status_label = QLabel(status)
        status_label.setAlignment(Qt.AlignCenter)
        # Clean button
        clean_button = QPushButton("Clean")
        clean_button.setCursor(Qt.PointingHandCursor)
        clean_button.setStyleSheet(
            "QPushButton { padding: 4px 8px; font-weight: bold; background-color: #443a91; color: white; border: 0px; }"
            "QPushButton:hover { background-color: #7d3ff8; }"
        )

        # status_label ya centrado via alignment y con padding

        # colores por estado
        if status == "Latest":
            status_color = "#244c19"  # verde oscuro
        elif status == "Outdated":
            status_color = "#8a4500"  # naranja oscuro
        else:
            status_color = "#660000"  # rojo oscuro (missing u otros)

        status_bg_color = QColor(status_color)
        status_text_css = self._text_color_for_bg(status_bg_color)
        status_label.setStyleSheet(
            f"padding-left: 6px; padding-right: 6px; background-color: {status_color}; color: {status_text_css};"
        )

        self.table.setItem(row, 0, node_item)
        self.table.setCellWidget(row, 1, current_label)
        self.table.setCellWidget(row, 2, latest_label)
        self.table.setCellWidget(row, 3, status_label)
        self.table.setCellWidget(row, 4, clean_button)

        # colores para delegado (una por columna)
        row_colors = ["#8a8a8a", "#8a8a8a", "#8a8a8a", status_color, "#8a8a8a"]
        self.row_background_colors.append(row_colors)

        self.table.resizeColumnsToContents()

        # conectar boton Clean con callback y datos de la fila
        def _on_clean_clicked():
            folder = os.path.dirname(current_model) if current_model else ""
            self._emit_clean_requested(folder, current_model or "")

        clean_button.clicked.connect(_on_clean_clicked)

    # Senal al controlador para que haga el clean de manera centralizada
    cleanRequested = Signal(str, str)  # folder_path, current_model

    def _emit_clean_requested(self, folder_path: str, current_model: str):
        self.cleanRequested.emit(folder_path, current_model)

    def _on_cell_clicked(self, row: int, column: int):
        # Al hacer click en cualquier celda, enfocar el nodo Inference de esa fila
        try:
            node_item = self.table.item(row, 0)
            if not node_item:
                return
            node_name = node_item.text()
            self._focus_inference_node(node_name)
        except Exception:
            pass

    def _focus_inference_node(self, node_name: str):
        try:
            node = nuke.toNode(node_name)
            if not node:
                return
            # Deseleccionar todo
            nuke.selectAll()
            nuke.invertSelection()
            # Seleccionar y centrar como en Media Manager
            node.setSelected(True)
            try:
                nuke.zoomToFitSelected()
            except Exception:
                try:
                    import nukescripts

                    nukescripts.zoomToFitSelected()
                except Exception:
                    pass
            try:
                node.showControlPanel()
            except Exception:
                try:
                    nuke.show(node)
                except Exception:
                    pass
        except Exception:
            pass

    def _text_color_for_bg(self, color: QColor) -> str:
        # calcula luminancia para elegir blanco o negro
        lum = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        return "#ffffff" if lum < 128 else "#000000"

    def adjust_window_size(self):
        # mismo enfoque de ajuste que CompareEXR
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.resizeColumnsToContents()
        width = self.table.verticalHeader().width() - 30
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i) + 20
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        max_width = screen_rect.width() * 0.8
        final_width = min(width, max_width)
        height = self.table.horizontalHeader().height() + 20
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i) + 4
        max_height = screen_rect.height() * 0.8
        final_height = min(height, max_height)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.resize(final_width, final_height)
        self.move(
            (screen_rect.width() - final_width) // 2,
            (screen_rect.height() - final_height) // 2,
        )


class ProgressWindow(QWidget):
    """Ventana simple de progreso para el escaneo."""

    def __init__(self, parent=None):
        super(ProgressWindow, self).__init__(parent)
        self.setWindowTitle("CopyCat Model Checker - Scanning")
        layout = QVBoxLayout(self)
        self.label = QLabel("Scanning Inference nodes...", self)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)  # indeterminado hasta conocer total
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    def set_progress(self, current: int, total: int):
        if total <= 0:
            self.progress.setRange(0, 0)
            self.label.setText("Scanning Inference nodes...")
        else:
            self.progress.setRange(0, total)
            self.progress.setValue(current)
            self.label.setText(f"Scanning {current}/{total}...")


# --------------------------------------------------------------------------------------
# Controller
# --------------------------------------------------------------------------------------


class CopyCatCleanerController(QObject):
    """Controla worker y ventanas para orquestar el flujo."""

    def __init__(self):
        super(CopyCatCleanerController, self).__init__()
        self.thread: Optional[QThread] = None
        self.worker: Optional[ScanWorker] = None
        self.progress_window: Optional[ProgressWindow] = None
        self.results_window: Optional[ResultsWindow] = None
        # cache de inferencias: carpeta -> set de modelos usados
        self.folder_to_used_models: Dict[str, Set[str]] = {}

    def start(self):
        # crear y mostrar progreso
        self.progress_window = ProgressWindow()
        self._center_widget(self.progress_window)
        self.progress_window.show()

        # configurar worker en QThread
        self.thread = QThread()
        self.worker = ScanWorker()
        thread = self.thread
        worker = self.worker
        worker.moveToThread(thread)

        # assert para el analizador estatico
        assert thread is not None
        assert worker is not None

        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.start()

    def _on_progress(self, current: int, total: int):
        if self.progress_window:
            self.progress_window.set_progress(current, total)

    def _on_finished(self, results: List[Dict[str, str]]):
        # cerrar progreso
        if self.progress_window:
            self.progress_window.close()
            self.progress_window = None

        # crear ventana de resultados
        self.results_window = ResultsWindow()
        # establecer project_folder desde el script actual de Nuke
        try:
            project_path = nuke.root().name()
            project_folder = os.path.dirname(project_path) if project_path else ""
            self.results_window.set_project_folder(project_folder)
        except Exception:
            self.results_window.set_project_folder("")
        # conectar clean
        self.results_window.cleanRequested.connect(self._on_clean_requested)
        for r in results:
            self.results_window.add_result(
                r.get("node_name", ""),
                r.get("current_model", ""),
                r.get("latest_model", ""),
                r.get("status", ""),
            )
            # poblar cache de modelos usados por carpeta
            current_model = r.get("current_model", "")
            if current_model:
                folder = os.path.dirname(current_model)
                self.folder_to_used_models.setdefault(folder, set()).add(
                    normalize_path_for_comparison(current_model)
                )

        self.results_window.adjust_window_size()
        self.results_window.show()

    # -------------------- Clean logic --------------------
    def _on_clean_requested(self, folder_path: str, current_model: str):
        if not folder_path:
            return
        # Recolectar todos los modelos usados por todos los Inference en esa carpeta (comparacion normalizada)
        target_folder_norm = normalize_path_for_comparison(folder_path)
        used_models_in_folder: Set[str] = set()
        try:
            for node in nuke.allNodes("Inference"):
                try:
                    model_path = node["modelFile"].value()
                except Exception:
                    model_path = ""
                if not model_path:
                    continue
                if (
                    normalize_path_for_comparison(os.path.dirname(model_path))
                    == target_folder_norm
                ):
                    used_models_in_folder.add(normalize_path_for_comparison(model_path))
        except Exception:
            pass

        # Asegurar incluir el modelo actual (por si cambio luego)
        if current_model:
            used_models_in_folder.add(normalize_path_for_comparison(current_model))

        # Lanzar worker en thread para no bloquear UI
        self._start_clean_worker(folder_path, used_models_in_folder)

    def _start_clean_worker(self, folder_path: str, used_models_norm: Set[str]):
        # Ventana de progreso
        self.progress_window = ProgressWindow()
        self.progress_window.setWindowTitle("CopyCat Model Cleaner - Cleaning")
        self.progress_window.label.setText("Cleaning non-used .cat files...")
        self.progress_window.progress.setRange(0, 0)
        self.progress_window.show()

        # Crear thread y worker
        self.clean_thread = QThread()
        self.clean_worker = _CleanWorker(folder_path, used_models_norm)
        self.clean_worker.moveToThread(self.clean_thread)
        self.clean_thread.started.connect(self.clean_worker.run)
        self.clean_worker.finished.connect(self._on_clean_finished)
        self.clean_worker.finished.connect(self.clean_thread.quit)
        self.clean_worker.finished.connect(self.clean_worker.deleteLater)
        self.clean_thread.finished.connect(self.clean_thread.deleteLater)
        self.clean_thread.start()

    def _on_clean_finished(
        self, clean_folder: str, moved_count: int, error_message: str
    ):
        if self.progress_window:
            self.progress_window.close()
            self.progress_window = None

        if error_message:
            QMessageBox.warning(None, "Clean error", error_message)
            return

        # Mensaje de exito con opcion a abrir la carpeta
        msg = QMessageBox()
        msg.setWindowTitle("Clean complete")
        msg.setText(self._format_clean_summary(clean_folder))
        go_btn = msg.addButton("Open Clean Folder", QMessageBox.ActionRole)
        msg.addButton("Close", QMessageBox.RejectRole)
        msg.exec_()
        if msg.clickedButton() == go_btn:
            self._open_in_os(clean_folder)

    def _open_in_os(self, path: str):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _format_clean_summary(self, clean_folder: str) -> str:
        cats = 0
        pngs = 0
        total_bytes = 0
        try:
            for f in os.listdir(clean_folder):
                full = os.path.join(clean_folder, f)
                if not os.path.isfile(full):
                    continue
                lower = f.lower()
                if lower.endswith(".cat"):
                    cats += 1
                elif lower.endswith(".png"):
                    pngs += 1
                try:
                    total_bytes += os.path.getsize(full)
                except Exception:
                    pass
        except Exception:
            pass
        # Mostrar GB si corresponde
        if total_bytes >= 1024.0 * 1024.0 * 1024.0:
            size_str = f"{(total_bytes / (1024.0 * 1024.0 * 1024.0)):.2f} GB"
        else:
            size_str = f"{(total_bytes / (1024.0 * 1024.0)):.2f} MB"
        return (
            f"Clean process finished.\n"
            f"Moved: {cats} .cat, {pngs} .png\n"
            f"Clean folder size: {size_str}"
        )

    def _center_widget(self, widget: QWidget):
        screen = QApplication.primaryScreen().geometry()
        widget.adjustSize()
        widget.move(
            screen.center().x() - widget.width() // 2,
            screen.center().y() - widget.height() // 2,
        )


class _CleanWorker(QObject):
    finished = Signal(str, int, str)  # clean_folder, moved_count, error_message

    def __init__(self, folder_path: str, used_models_norm: Set[str]):
        super().__init__()
        self.folder_path = folder_path
        self.used_models_norm = used_models_norm

    def run(self):
        try:
            folder_path = self.folder_path
            used_models_norm = self.used_models_norm
            clean_folder = folder_path + "_clean"
            if not os.path.exists(clean_folder):
                os.makedirs(clean_folder)
            moved_count = 0
            for f in os.listdir(folder_path):
                full = os.path.join(folder_path, f)
                lower = f.lower()
                try:
                    if lower.endswith(".cat"):
                        # mover solo si no es usado por ningun Inference
                        norm = normalize_path_for_comparison(full)
                        if norm in used_models_norm:
                            continue
                        dest = os.path.join(clean_folder, f)
                        shutil.move(full, dest)
                        moved_count += 1
                    elif lower.endswith(".png"):
                        # mover siempre todos los PNG
                        dest = os.path.join(clean_folder, f)
                        shutil.move(full, dest)
                        moved_count += 1
                except Exception:
                    continue
            self.finished.emit(clean_folder, moved_count, "")
        except Exception as e:
            self.finished.emit("", 0, str(e))

    def _center_widget(self, widget: QWidget):
        screen = QApplication.primaryScreen().geometry()
        widget.adjustSize()
        widget.move(
            screen.center().x() - widget.width() // 2,
            screen.center().y() - widget.height() // 2,
        )


# --------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------


_controller_instance: Optional[CopyCatCleanerController] = None


def run_copycat_cleaner():
    """Punto de entrada: lanza el escaneo en background y muestra resultados."""
    global _controller_instance
    app = QApplication.instance() or QApplication(sys.argv)

    _controller_instance = CopyCatCleanerController()
    _controller_instance.start()


if __name__ == "__main__":
    run_copycat_cleaner()
