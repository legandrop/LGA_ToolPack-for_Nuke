"""
____________________________________________________________________

  LGA_RnW_PathsToRelative v1.01 | Lega

  Convierte a rutas relativas las rutas absolutas de los nodos que
  apuntan a archivos. Nuke resuelve los relativos contra el Project
  Directory del Root, asi que las rutas se calculan contra ese knob.

  Si hay nodos seleccionados actua solo sobre esos; si no, recorre
  todo el script. Nunca toca knobs con expresiones TCL o Python.

  v1.01: Las rutas se calculan contra el Project Directory y no contra
         la carpeta del script. Si ese knob esta vacio los relativos no
         resuelven, asi que se ofrece dejarlo en
         [python {nuke.script_directory()}].
  v1.00: Version inicial.
____________________________________________________________________
"""

import os
import re

import nuke

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore

QApplication = QtWidgets.QApplication
QDialog = QtWidgets.QDialog
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QCheckBox = QtWidgets.QCheckBox
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QHeaderView = QtWidgets.QHeaderView
QAbstractItemView = QtWidgets.QAbstractItemView
QColor = QtGui.QColor
Qt = QtCore.Qt


# Variable global para activar o desactivar los debug_prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print("[LGA_RnW_PathsToRelative]", *message)


# ---------------------------------------------------------------------------
#                               Configuracion
# ---------------------------------------------------------------------------
# Clases sobre las que trabaja la tool. Dentro de cada nodo se recorren todos
# sus File_Knob, asi que quedan cubiertos "file", "proxy" y equivalentes.
TARGET_CLASSES = (
    "Read",
    "Write",
    "DeepRead",
    "DeepWrite",
    "ReadGeo",
    "ReadGeo2",
    "WriteGeo",
    "Precomp",
    "Vectorfield",
    "OCIOFileTransform",
)

# A partir de cuantos "../" se marca la ruta como profunda (amarillo)
DEEP_LEVEL_WARNING = 3

# Expresion que usa el boton "Script Directory" de Project Settings. Es la que
# hace que Nuke resuelva los relativos contra la carpeta del script.
PROJECT_DIRECTORY_EXPRESSION = "[python {nuke.script_directory()}]"

# Estado del knob project_directory
PROJECT_DIR_EMPTY = "empty"
PROJECT_DIR_OK = "ok"
PROJECT_DIR_UNRESOLVED = "unresolved"

# Estados de cada fila
STATUS_CONVERT = "convert"
STATUS_DEEP = "deep"
STATUS_BLOCKED = "blocked"

# Motivos por los que un knob no entra en la tabla
SKIP_RELATIVE = "already relative"
SKIP_EXPRESSION = "expression"
SKIP_EMPTY = "empty"


# ---------------------------------------------------------------------------
#                                  Estilos
# ---------------------------------------------------------------------------
COLOR_WINDOW_BG = "#212121"
COLOR_TEXT = "#a7a7a7"
COLOR_TEXT_DIM = "#6e6e6e"
COLOR_TITLE = "#E8E8E8"
COLOR_CONVERT = "#6a9960"
COLOR_DEEP = "#b09040"
COLOR_BLOCKED = "#a06060"

TABLE_STYLE = """
QTableWidget {
    background-color: #272727;
    border: 1px solid #333333;
    color: #a7a7a7;
    gridline-color: #333333;
    outline: none;
}
QHeaderView::section {
    background-color: #2B2B2B;
    color: #999999;
    padding: 4px 8px;
    border: 0px;
    border-bottom: 1px solid #444444;
    font-weight: bold;
}
QTableWidget::item { padding-left: 6px; padding-right: 6px; }
QScrollBar:vertical {
    background: #242424;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #444444;
    min-height: 24px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal {
    background: #242424;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #444444;
    min-width: 24px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

BTN_PRIMARY = """
QPushButton {
    background-color: #443a91;
    border: none;
    color: #B2B2B2;
    padding: 7px 18px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover { background-color: #774dcb; color: #ffffff; }
QPushButton:disabled { background-color: #2a2540; color: #666666; }
"""

BTN_CANCEL = """
QPushButton {
    background-color: #2a2a2a;
    border: none;
    color: #cccccc;
    padding: 7px 18px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover { background-color: #383838; }
"""

BTN_SMALL = """
QPushButton {
    background-color: #2e2e2e;
    border: 1px solid #444444;
    color: #999999;
    padding: 3px 12px;
    border-radius: 3px;
    font-size: 11px;
}
QPushButton:hover { background-color: #383838; color: #cccccc; }
"""


# ---------------------------------------------------------------------------
#                            Helpers de rutas
# ---------------------------------------------------------------------------
# Unidad de Windows al principio del path (T:/ o T:\)
DRIVE_RE = re.compile(r"^[a-zA-Z]:[\\/]")


def is_expression_value(value):
    """
    True si el knob tiene una expresion TCL/Python en vez de una ruta literal.
    Los Writes creados con Write Presets caen aca y no se tocan nunca.
    """
    return "[" in value or "]" in value


def is_absolute_path(value):
    """True si la ruta es absoluta en cualquiera de las dos plataformas."""
    if not value:
        return False
    if DRIVE_RE.match(value):
        return True
    if value.startswith("//") or value.startswith("\\\\"):
        return True
    return os.path.isabs(value)


def to_relative(path, anchor_dir):
    """
    Convierte una ruta absoluta en relativa al directorio ancla.

    Retorna (relative_path, up_levels). Si no existe ruta relativa posible
    (otra unidad o mount) retorna (None, 0).
    """
    try:
        relative = os.path.relpath(path, anchor_dir)
    except ValueError:
        return None, 0

    relative = relative.replace("\\", "/")

    up_levels = 0
    for part in relative.split("/"):
        if part == "..":
            up_levels += 1
        else:
            break

    return relative, up_levels


def get_project_directory_knob():
    """Devuelve el knob project_directory del Root, o None."""
    try:
        return nuke.root()["project_directory"]
    except Exception as error:
        debug_print("No se pudo leer project_directory: %s" % error)
        return None


def resolve_anchor(script_dir):
    """
    Determina contra que directorio se calculan las rutas relativas.

    Nuke NO resuelve los paths relativos contra la ubicacion del script sino
    contra el Project Directory del Root. Si ese knob esta vacio, los resuelve
    contra el working directory del proceso y los relativos no funcionan.

    Retorna (anchor_dir, raw_value, state).
    """
    knob = get_project_directory_knob()

    raw_value = ""
    if knob is not None:
        try:
            raw_value = (knob.getValue() or "").strip()
        except Exception:
            raw_value = ""

    if not raw_value:
        return script_dir, "", PROJECT_DIR_EMPTY

    evaluated = ""
    try:
        evaluated = (knob.evaluate() or "").strip()
    except Exception as error:
        debug_print("No se pudo evaluar project_directory: %s" % error)

    evaluated = evaluated.replace("\\", "/").rstrip("/")

    if evaluated and is_absolute_path(evaluated):
        return evaluated, raw_value, PROJECT_DIR_OK

    # Tiene algo cargado pero no resuelve a una carpeta real: no se pisa solo
    return script_dir, raw_value, PROJECT_DIR_UNRESOLVED


def set_project_directory():
    """Deja el Project Directory apuntando a la carpeta del script."""
    knob = get_project_directory_knob()
    if knob is None:
        return False
    knob.setValue(PROJECT_DIRECTORY_EXPRESSION)
    return True


def knob_raw_value(knob):
    """Devuelve el texto crudo del knob, sin evaluar expresiones."""
    try:
        value = knob.getValue()
    except Exception:
        value = knob.value()
    return (value or "").strip()


def file_knobs(node):
    """Devuelve [(nombre, knob)] de todos los File_Knob del nodo."""
    result = []
    try:
        knobs = node.knobs()
    except Exception as error:
        debug_print("No se pudieron leer los knobs de %s: %s" % (node.name(), error))
        return result

    for knob_name, knob in knobs.items():
        try:
            if isinstance(knob, nuke.File_Knob):
                result.append((knob_name, knob))
        except Exception:
            continue

    result.sort(key=lambda item: item[0])
    return result


def node_location(node):
    """Devuelve donde vive el nodo: "Root" o la ruta del Group que lo contiene."""
    try:
        full_name = node.fullName()
    except Exception:
        return "Root"
    if "." in full_name:
        return full_name.rsplit(".", 1)[0].replace(".", "/")
    return "Root"


def collect_nodes():
    """
    Junta los nodos a procesar. Si hay seleccion, trabaja solo sobre ella.

    No entra en Precomps ni LiveGroups: sus nodos internos vienen de otro .nk
    y modificarlos aca no tiene efecto real. El nodo Precomp si se procesa,
    porque su propio knob apunta a un archivo.
    """
    selected = [
        node for node in nuke.selectedNodes() if node.Class() in TARGET_CLASSES
    ]
    if selected:
        debug_print("Trabajando sobre la seleccion: %d nodos" % len(selected))
        return selected, True

    collected = []
    _walk_group(nuke.root(), collected)
    debug_print("Trabajando sobre todo el script: %d nodos" % len(collected))
    return collected, False


def _walk_group(group, collected):
    """Recorre el grupo y sus Groups anidados juntando nodos objetivo."""
    try:
        children = group.nodes()
    except Exception as error:
        debug_print("No se pudo recorrer el grupo: %s" % error)
        return

    for node in children:
        node_class = node.Class()
        if node_class in TARGET_CLASSES:
            collected.append(node)
        if node_class == "Group":
            _walk_group(node, collected)


def build_rows(nodes, anchor_dir):
    """
    Arma las filas de la tabla y cuenta lo que queda afuera.

    Retorna (rows, skipped) donde skipped es un dict motivo -> cantidad.
    """
    rows = []
    skipped = {SKIP_RELATIVE: 0, SKIP_EXPRESSION: 0, SKIP_EMPTY: 0}

    for node in nodes:
        for knob_name, knob in file_knobs(node):
            value = knob_raw_value(knob)

            if not value:
                skipped[SKIP_EMPTY] += 1
                continue

            if is_expression_value(value):
                skipped[SKIP_EXPRESSION] += 1
                continue

            if not is_absolute_path(value):
                skipped[SKIP_RELATIVE] += 1
                continue

            relative, up_levels = to_relative(value, anchor_dir)

            if relative is None:
                status = STATUS_BLOCKED
                target = "path is on another drive"
            elif up_levels >= DEEP_LEVEL_WARNING:
                status = STATUS_DEEP
                target = relative
            else:
                status = STATUS_CONVERT
                target = relative

            rows.append(
                {
                    "node": node,
                    "knob": knob_name,
                    "location": node_location(node),
                    "current": value.replace("\\", "/"),
                    "relative": relative,
                    "target_text": target,
                    "up_levels": up_levels,
                    "status": status,
                }
            )

    return rows, skipped


def apply_rows(rows, set_project_dir=False):
    """
    Escribe las rutas relativas en los knobs y, si corresponde, deja el
    Project Directory apuntando al script. Todo en un solo bloque de undo.

    Retorna (aplicadas, errores, project_dir_aplicado).
    """
    applied = 0
    errors = []
    project_dir_applied = False

    nuke.Undo().begin("Paths to Relative")
    try:
        if set_project_dir:
            try:
                project_dir_applied = set_project_directory()
            except Exception as error:
                errors.append("project_directory: %s" % error)

        for row in rows:
            try:
                row["node"][row["knob"]].setValue(row["relative"])
                applied += 1
            except Exception as error:
                errors.append("%s.%s: %s" % (row["node"].name(), row["knob"], error))
    finally:
        nuke.Undo().end()

    return applied, errors, project_dir_applied


def format_skipped(skipped):
    """Texto con lo que quedo afuera de la tabla."""
    parts = []
    if skipped.get(SKIP_RELATIVE):
        parts.append("%d already relative" % skipped[SKIP_RELATIVE])
    if skipped.get(SKIP_EXPRESSION):
        parts.append("%d with expressions" % skipped[SKIP_EXPRESSION])
    if skipped.get(SKIP_EMPTY):
        parts.append("%d empty" % skipped[SKIP_EMPTY])
    return " · ".join(parts)


# ---------------------------------------------------------------------------
#                                  Ventanas
# ---------------------------------------------------------------------------
_app = None


def ensure_app():
    """Garantiza que exista una QApplication antes de crear ventanas."""
    global _app
    _app = QApplication.instance()
    if _app is None:
        _app = QApplication([])
    return _app


class InfoDialog(QDialog):
    """
    Ventana simple de aviso. Si se pasa confirm_label suma un boton de accion
    y el resultado del exec_ indica si el usuario acepto.
    """

    def __init__(self, title, message_html, confirm_label=None, parent=None):
        super(InfoDialog, self).__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle(title)
        self.setStyleSheet(
            "background-color: %s; border-radius: 10px;" % COLOR_WINDOW_BG
        )
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        message_label = QLabel(message_html)
        message_label.setStyleSheet("font-size:13px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        close_button = QPushButton("Cancel" if confirm_label else "OK")
        close_button.setStyleSheet(BTN_CANCEL)
        close_button.clicked.connect(self.reject if confirm_label else self.accept)
        buttons_layout.addWidget(close_button)

        if confirm_label:
            confirm_button = QPushButton(confirm_label)
            confirm_button.setStyleSheet(BTN_PRIMARY)
            confirm_button.clicked.connect(self.accept)
            buttons_layout.addWidget(confirm_button)

        layout.addLayout(buttons_layout)

        self.setMinimumWidth(460)
        self.adjustSize()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        else:
            super(InfoDialog, self).keyPressEvent(event)


def show_info(title, message_html):
    ensure_app()
    dialog = InfoDialog(title, message_html)
    dialog.exec_()


def ask_info(title, message_html, confirm_label):
    """Aviso con boton de accion. True si el usuario confirma."""
    ensure_app()
    dialog = InfoDialog(title, message_html, confirm_label)
    return dialog.exec_() == QDialog.Accepted


class PathsToRelativeWindow(QDialog):
    """Preview con checkbox por fila antes de escribir los knobs."""

    COL_BAR = 0
    COL_CHECK = 1
    COL_NODE = 2
    COL_KNOB = 3
    COL_IN = 4
    COL_CURRENT = 5
    COL_ARROW = 6
    COL_TARGET = 7

    def __init__(
        self,
        rows,
        skipped,
        from_selection,
        anchor_dir,
        project_state,
        project_raw,
        parent=None,
    ):
        super(PathsToRelativeWindow, self).__init__(parent)
        self.rows = rows
        self.skipped = skipped
        self.from_selection = from_selection
        self.anchor_dir = anchor_dir
        self.project_state = project_state
        self.project_raw = project_raw
        self.checkboxes = {}
        self.project_checkbox = None
        self.applied_count = 0

        self.setWindowTitle("Paths to Relative")
        self.setStyleSheet("background-color: %s;" % COLOR_WINDOW_BG)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_table())

        project_widget = self._build_project_directory_row()
        if project_widget is not None:
            layout.addWidget(project_widget)

        layout.addLayout(self._build_footer())

        self.resize(1150, 580)
        self._update_status()

    # --- Construccion -----------------------------------------------------
    def _build_header(self):
        scope = "selected nodes" if self.from_selection else "the whole script"
        text = (
            "<span style='color:%s; font-size:13px;'>Paths made relative to the "
            "Project Directory, in %s.</span><br>"
            "<span style='color:%s; font-size:12px;'>%s</span>"
        ) % (COLOR_TITLE, scope, COLOR_TEXT_DIM, self.anchor_dir)
        label = QLabel(text)
        label.setStyleSheet("font-size:13px;")
        return label

    def _build_project_directory_row(self):
        """
        Aviso y opcion para dejar seteado el Project Directory. Nuke resuelve
        los relativos contra ese knob: si esta vacio, no resuelven.
        """
        if self.project_state == PROJECT_DIR_OK:
            return None

        container = QWidget()
        container.setStyleSheet("background-color: #292929; border-radius: 6px;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 10, 12, 10)
        container_layout.setSpacing(4)

        if self.project_state == PROJECT_DIR_EMPTY:
            warning = (
                "<span style='color:%s; font-weight:bold;'>The Project Directory is "
                "empty.</span><span style='color:%s;'> Nuke resolves relative paths "
                "against it, not against the script location, so relative paths will "
                "not resolve until it is set.</span>"
            ) % (COLOR_DEEP, COLOR_TEXT)
            checked = True
        else:
            warning = (
                "<span style='color:%s; font-weight:bold;'>The Project Directory does "
                "not resolve to a folder.</span><span style='color:%s;'> Current "
                "value: %s. Paths below were made relative to the script folder.</span>"
            ) % (COLOR_BLOCKED, COLOR_TEXT, self.project_raw)
            checked = False

        warning_label = QLabel(warning)
        warning_label.setStyleSheet("font-size:12px; background: transparent;")
        warning_label.setWordWrap(True)
        container_layout.addWidget(warning_label)

        self.project_checkbox = QCheckBox(
            "Set Project Directory to %s" % PROJECT_DIRECTORY_EXPRESSION
        )
        self.project_checkbox.setChecked(checked)
        self.project_checkbox.setStyleSheet(
            "color:%s; padding:2px; background: transparent;" % COLOR_TEXT
        )
        container_layout.addWidget(self.project_checkbox)

        return container

    def _build_table(self):
        headers = ["", "", "Node", "Knob", "In", "Current path", "", "Relative path"]

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.rows))
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.setStyleSheet(TABLE_STYLE)

        header = table.horizontalHeader()
        header.setMinimumSectionSize(1)
        header.setSectionResizeMode(self.COL_BAR, QHeaderView.Fixed)
        table.setColumnWidth(self.COL_BAR, 5)
        header.setSectionResizeMode(self.COL_CHECK, QHeaderView.Fixed)
        table.setColumnWidth(self.COL_CHECK, 28)
        header.setSectionResizeMode(self.COL_NODE, QHeaderView.Interactive)
        table.setColumnWidth(self.COL_NODE, 150)
        header.setSectionResizeMode(self.COL_KNOB, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_IN, QHeaderView.Interactive)
        table.setColumnWidth(self.COL_IN, 110)
        header.setSectionResizeMode(self.COL_CURRENT, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_ARROW, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_TARGET, QHeaderView.Stretch)

        for row_index, row in enumerate(self.rows):
            self._fill_row(table, row_index, row)

        table.cellClicked.connect(self._on_cell_clicked)
        self.table = table
        return table

    def _fill_row(self, table, row_index, row):
        status = row["status"]
        blocked = status == STATUS_BLOCKED

        if status == STATUS_CONVERT:
            bar_color = COLOR_CONVERT
        elif status == STATUS_DEEP:
            bar_color = COLOR_DEEP
        else:
            bar_color = COLOR_BLOCKED

        # Col 0: barra de color con el estado de la fila
        bar = QWidget()
        bar.setStyleSheet("background: %s;" % bar_color)
        table.setCellWidget(row_index, self.COL_BAR, bar)

        # Col 1: checkbox; las filas imposibles quedan deshabilitadas
        checkbox = QCheckBox()
        checkbox.setStyleSheet("padding:2px;")
        checkbox.setChecked(not blocked)
        checkbox.setEnabled(not blocked)
        checkbox.stateChanged.connect(self._update_status)
        self.checkboxes[row_index] = checkbox

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(checkbox)
        table.setCellWidget(row_index, self.COL_CHECK, container)

        text_color = QColor(COLOR_TEXT_DIM if blocked else COLOR_TEXT)

        node_item = QTableWidgetItem(row["node"].name())
        node_item.setForeground(text_color)
        table.setItem(row_index, self.COL_NODE, node_item)

        knob_item = QTableWidgetItem(row["knob"])
        knob_item.setForeground(QColor(COLOR_TEXT_DIM))
        table.setItem(row_index, self.COL_KNOB, knob_item)

        location_item = QTableWidgetItem(row["location"])
        location_item.setForeground(
            QColor(COLOR_TEXT_DIM if row["location"] == "Root" else COLOR_DEEP)
        )
        table.setItem(row_index, self.COL_IN, location_item)

        current_item = QTableWidgetItem(row["current"])
        current_item.setForeground(text_color)
        current_item.setToolTip(row["current"])
        table.setItem(row_index, self.COL_CURRENT, current_item)

        arrow_item = QTableWidgetItem("  ➜  ")
        arrow_item.setForeground(QColor(COLOR_TEXT_DIM))
        table.setItem(row_index, self.COL_ARROW, arrow_item)

        target_item = QTableWidgetItem(row["target_text"])
        target_item.setForeground(QColor(bar_color))
        target_item.setToolTip(row["target_text"])
        table.setItem(row_index, self.COL_TARGET, target_item)

        table.setRowHeight(row_index, 24)

    def _build_footer(self):
        footer = QHBoxLayout()
        footer.setSpacing(8)

        all_button = QPushButton("All")
        all_button.setStyleSheet(BTN_SMALL)
        all_button.clicked.connect(lambda: self._set_all(True))
        footer.addWidget(all_button)

        none_button = QPushButton("None")
        none_button.setStyleSheet(BTN_SMALL)
        none_button.clicked.connect(lambda: self._set_all(False))
        footer.addWidget(none_button)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size:12px;")
        footer.addWidget(self.status_label)

        footer.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(BTN_CANCEL)
        cancel_button.clicked.connect(self.reject)
        footer.addWidget(cancel_button)

        self.convert_button = QPushButton("Convert")
        self.convert_button.setStyleSheet(BTN_PRIMARY)
        self.convert_button.clicked.connect(self._on_convert)
        footer.addWidget(self.convert_button)

        return footer

    # --- Interaccion ------------------------------------------------------
    def _on_cell_clicked(self, row_index, column):
        # La barra de color y el checkbox manejan sus propios eventos
        if column <= self.COL_CHECK:
            return
        checkbox = self.checkboxes.get(row_index)
        if checkbox is not None and checkbox.isEnabled():
            checkbox.setChecked(not checkbox.isChecked())

    def _set_all(self, checked):
        for checkbox in self.checkboxes.values():
            if checkbox.isEnabled():
                checkbox.setChecked(checked)

    def selected_rows(self):
        return [
            row
            for index, row in enumerate(self.rows)
            if self.checkboxes[index].isChecked() and row["relative"]
        ]

    def _update_status(self, *_args):
        selected = len(self.selected_rows())
        text = "<span style='color:%s;'>%d of %d paths selected</span>" % (
            COLOR_TEXT,
            selected,
            len(self.rows),
        )
        skipped_text = format_skipped(self.skipped)
        if skipped_text:
            text += "<span style='color:%s;'> · %s (not modified)</span>" % (
                COLOR_TEXT_DIM,
                skipped_text,
            )
        self.status_label.setText(text)
        self.convert_button.setEnabled(selected > 0)

    def _on_convert(self):
        rows = self.selected_rows()
        if not rows:
            return

        set_project_dir = bool(
            self.project_checkbox is not None and self.project_checkbox.isChecked()
        )

        applied, errors, project_dir_applied = apply_rows(rows, set_project_dir)
        self.applied_count = applied
        debug_print("Rutas convertidas: %d" % applied)

        if errors:
            message = (
                "<span style='color:%s; font-weight:bold;'>%d paths converted, "
                "%d failed.</span><br><span style='color:%s;'>%s</span>"
            ) % (COLOR_DEEP, applied, len(errors), COLOR_TEXT, "<br>".join(errors))
        else:
            message = (
                "<span style='color:%s; font-weight:bold;'>%d paths converted to "
                "relative.</span>" % (COLOR_CONVERT, applied)
            )

        if project_dir_applied:
            message += (
                "<br><span style='color:%s;'>Project Directory set to %s</span>"
                % (COLOR_TEXT, PROJECT_DIRECTORY_EXPRESSION)
            )
        elif self.project_state == PROJECT_DIR_EMPTY and not set_project_dir:
            message += (
                "<br><span style='color:%s;'>The Project Directory is still empty, so "
                "these relative paths will not resolve.</span>" % COLOR_DEEP
            )

        self.accept()
        show_info("Paths to Relative", message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.accept()
        else:
            super(PathsToRelativeWindow, self).keyPressEvent(event)


# Referencia global para que la ventana no la junte el GC
_window = None


# ---------------------------------------------------------------------------
#                                   Entrada
# ---------------------------------------------------------------------------
def main():
    global _window

    ensure_app()

    script_path = nuke.root().name()
    if not script_path or script_path == "Root":
        show_info(
            "Paths to Relative",
            "<span style='color:%s; font-weight:bold;'>The Nuke script has not been "
            "saved yet.</span><br><span style='color:%s;'>Relative paths need the "
            "script folder as reference.</span>" % (COLOR_BLOCKED, COLOR_TEXT),
        )
        return

    script_dir = os.path.dirname(script_path)
    anchor_dir, project_raw, project_state = resolve_anchor(script_dir)
    debug_print("Directorio del script:", script_dir)
    debug_print("Ancla de los relativos:", anchor_dir, "| estado:", project_state)

    nodes, from_selection = collect_nodes()
    if not nodes:
        show_info(
            "Paths to Relative",
            "<span style='color:%s;'>No nodes with file paths were found.</span>"
            % COLOR_TEXT,
        )
        return

    rows, skipped = build_rows(nodes, anchor_dir)

    if not rows:
        _handle_nothing_to_convert(skipped, project_state, project_raw)
        return

    _window = PathsToRelativeWindow(
        rows, skipped, from_selection, anchor_dir, project_state, project_raw
    )
    _window.exec_()


def _handle_nothing_to_convert(skipped, project_state, project_raw):
    """
    No hay rutas absolutas, pero si el Project Directory esta vacio las rutas
    relativas que ya existen no resuelven. Ese caso se ofrece arreglar.
    """
    skipped_text = format_skipped(skipped)
    detail = (
        "<br><span style='color:%s;'>%s.</span>" % (COLOR_TEXT_DIM, skipped_text)
        if skipped_text
        else ""
    )
    base_message = (
        "<span style='color:%s; font-weight:bold;'>No absolute paths to "
        "convert.</span>%s" % (COLOR_CONVERT, detail)
    )

    if project_state == PROJECT_DIR_OK:
        show_info("Paths to Relative", base_message)
        return

    if project_state == PROJECT_DIR_UNRESOLVED:
        show_info(
            "Paths to Relative",
            base_message
            + (
                "<br><br><span style='color:%s; font-weight:bold;'>The Project "
                "Directory does not resolve to a folder.</span><span style='color:%s;'>"
                " Current value: %s</span>" % (COLOR_BLOCKED, COLOR_TEXT, project_raw)
            ),
        )
        return

    message = base_message + (
        "<br><br><span style='color:%s; font-weight:bold;'>The Project Directory is "
        "empty.</span><span style='color:%s;'> Nuke resolves relative paths against "
        "it, not against the script location, so the existing relative paths will "
        "not resolve until it is set.</span>" % (COLOR_DEEP, COLOR_TEXT)
    )

    if not ask_info("Paths to Relative", message, "Set Project Directory"):
        return

    nuke.Undo().begin("Set Project Directory")
    try:
        applied = set_project_directory()
    finally:
        nuke.Undo().end()

    if applied:
        show_info(
            "Paths to Relative",
            "<span style='color:%s; font-weight:bold;'>Project Directory set to "
            "%s</span>" % (COLOR_CONVERT, PROJECT_DIRECTORY_EXPRESSION),
        )


if __name__ == "__main__":
    main()
