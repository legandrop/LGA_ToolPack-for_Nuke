"""
_______________________________________________

  LGA_mediaPathReplacer v2.06 | Lega
  Search and replace for Read and Write nodes

  v2.06 - Los cinco checkboxes con texto llevan lgaLabeled: sin la
          propiedad la hoja del pack deja el texto pegado al cuadrito
          (spacing 0).
  v2.05 - El look sale de LGA_UI_Style_ToolPack. La ventana pasa al
          fondo de la app: iba mas clara que su propia tabla, asi que
          la tabla se veia hundida. Textos de UI al ingles.
  v2.04 - Seleccion de texto en path original
  v2.03 - Checkboxes persistentes

_______________________________________________

"""

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore
from LGA_UI_Style_ToolPack import Color, Metric, Style

QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QLineEdit = QtWidgets.QLineEdit
QPushButton = QtWidgets.QPushButton
QCheckBox = QtWidgets.QCheckBox
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QTableWidget = QtWidgets.QTableWidget
QFrame = QtWidgets.QFrame
QComboBox = QtWidgets.QComboBox
QListView = QtWidgets.QListView
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QStyle = QtWidgets.QStyle
QHeaderView = QtWidgets.QHeaderView
QKeySequence = QtGui.QKeySequence
Qt = QtCore.Qt

import configparser
import os
import re

import nuke

# Solo se necesita una instancia de QApplication por script
app = QApplication.instance() or QApplication([])


_PRESET_TRASH_W = 26
_PRESET_PLACEHOLDER_NOMATCH = "----"
_PRESET_PLACEHOLDER_EMPTY = "(no presets)"
_STAGE_COLORS = {
    1: Color.MATCH_A,  # Search & Replace 1
    2: Color.MATCH_B,  # Search & Replace 2
}
_PRESET_FIELDS = (
    "sr1_search",
    "sr1_replace",
    "sr1_case",
    "sr2_search",
    "sr2_replace",
    "sr2_case",
)
_OPTIONS_SR_COL_WIDTH = 455
_OPTIONS_PRESET_COL_WIDTH = 310
_WINDOW_WIDTH = 1360

# Todo el look sale de LGA_UI_Style_ToolPack. Los alias conservan los nombres
# con los que el resto del archivo ya llamaba a cada estilo.
_TABLE_STYLE = Style.TABLE
_BTN_PRIMARY = Style.BTN_PRIMARY
_BTN_SMALL = Style.BTN_SMALL
_BTN_SMALL_TIGHT = Style.BTN_ICON
_COMBO_STYLE = Style.COMBO


def _section_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: %s; font-weight: bold; padding-top: 4px;" % Color.TEXT_STRONG
    )
    return lbl


def _separator(orientation="h"):
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine if orientation == "h" else QFrame.VLine)
    sep.setFrameShadow(QFrame.Plain)
    sep.setStyleSheet("color: %s; margin: 0px;" % Color.BORDER_HOVER)
    return sep


def _html_escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _colorize_with_map(text, color_by_index):
    if not text:
        return ""
    chunks = []
    cur_chars = []
    cur_color = None

    for i, ch in enumerate(text):
        c = color_by_index.get(i)
        if c != cur_color:
            if cur_chars:
                raw = "".join(cur_chars)
                if cur_color:
                    chunks.append(
                        "<span style='color:%s; font-weight:600;'>%s</span>"
                        % (cur_color, _html_escape(raw))
                    )
                else:
                    chunks.append("<span style='color:%s;'>%s</span>" % (Color.TEXT, _html_escape(raw)))
            cur_chars = [ch]
            cur_color = c
        else:
            cur_chars.append(ch)

    if cur_chars:
        raw = "".join(cur_chars)
        if cur_color:
            chunks.append(
                "<span style='color:%s; font-weight:600;'>%s</span>"
                % (cur_color, _html_escape(raw))
            )
        else:
            chunks.append("<span style='color:%s;'>%s</span>" % (Color.TEXT, _html_escape(raw)))

    return "".join(chunks)


def _cell_html_label(html, bg=Color.SURFACE):
    lbl = QLabel()
    lbl.setTextFormat(Qt.RichText)
    lbl.setText(html)
    lbl.setStyleSheet("background:%s; padding:2px 6px;" % bg)
    lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    return lbl


def _path_preview_cell(original_html, renamed_html, bg=Color.SURFACE):
    w = QWidget()
    w.setStyleSheet("background:%s;" % bg)

    layout = QtWidgets.QGridLayout(w)
    layout.setContentsMargins(6, 2, 6, 2)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)

    original_lbl = QLabel(
        "<span style='color:%s; font-weight:600;'>Original:</span>" % Color.TEXT
    )
    original_lbl.setTextFormat(Qt.RichText)
    original_lbl.setStyleSheet("background:%s;" % bg)
    original_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    renamed_lbl = QLabel(
        "<span style='color:%s; font-weight:600;'>Renamed:</span>" % Color.TEXT
    )
    renamed_lbl.setTextFormat(Qt.RichText)
    renamed_lbl.setStyleSheet("background:%s;" % bg)
    renamed_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    original_path_lbl = QLabel(original_html)
    original_path_lbl.setTextFormat(Qt.RichText)
    original_path_lbl.setStyleSheet(
        "background:%s; selection-background-color:%s; selection-color:%s;"
        % (bg, Color.ACCENT, Color.TEXT_STRONG)
    )
    original_path_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    original_path_lbl.setCursor(Qt.IBeamCursor)

    renamed_path_lbl = QLabel(renamed_html)
    renamed_path_lbl.setTextFormat(Qt.RichText)
    renamed_path_lbl.setStyleSheet("background:%s;" % bg)
    renamed_path_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    spacer_top = QWidget()
    spacer_top.setFixedWidth(20)
    spacer_top.setStyleSheet("background:%s;" % bg)
    spacer_bottom = QWidget()
    spacer_bottom.setFixedWidth(20)
    spacer_bottom.setStyleSheet("background:%s;" % bg)

    layout.addWidget(original_lbl, 0, 0)
    layout.addWidget(spacer_top, 0, 1)
    layout.addWidget(original_path_lbl, 0, 2)
    layout.addWidget(renamed_lbl, 1, 0)
    layout.addWidget(spacer_bottom, 1, 1)
    layout.addWidget(renamed_path_lbl, 1, 2)
    layout.setColumnStretch(2, 1)
    return w


def _show_save_preset_dialog(parent=None):
    """Diálogo estilo Import Shots para nombrar preset."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Save Preset")
    dlg.setMinimumWidth(Metric.DIALOG_MIN_WIDTH)
    dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    dlg.setStyleSheet(
        "QDialog { background-color:%s; border:1px solid %s; }"
        "QLabel  { color:%s; background: transparent; }"
        % (Color.WINDOW, Color.BORDER_STRONG, Color.TEXT)
    )
    dlg.setAttribute(Qt.WA_DeleteOnClose, True)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(*([Metric.DIALOG_MARGIN] * 4))
    layout.setSpacing(Metric.SPACING)

    header_row = QHBoxLayout()
    title_lbl = QLabel("Save path preset")
    title_lbl.setStyleSheet(
        "color:%s; font-size:13px; font-weight:bold;" % Color.TEXT_STRONG
    )
    header_row.addWidget(title_lbl)
    header_row.addStretch()
    layout.addLayout(header_row)

    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("background:%s;" % Color.BORDER_STRONG)
    sep.setFixedHeight(1)
    layout.addWidget(sep)

    name_prompt = QLabel("Preset name:")
    name_prompt.setStyleSheet("color:%s; font-size:11px;" % Color.TEXT)
    layout.addWidget(name_prompt)

    line = QLineEdit()
    line.setPlaceholderText("e.g. Comp path swap")
    line.setStyleSheet(Style.LINE_EDIT)
    layout.addWidget(line)

    layout.addSpacing(8)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    btn_cancel = QPushButton("Cancel")
    btn_save = QPushButton("Save")
    btn_cancel.setStyleSheet(Style.BTN_SECONDARY)
    btn_save.setStyleSheet(Style.BTN_PRIMARY)
    btn_save.setEnabled(False)
    btn_row.addWidget(btn_cancel)
    btn_row.addSpacing(8)
    btn_row.addWidget(btn_save)
    layout.addLayout(btn_row)

    line.textChanged.connect(lambda t: btn_save.setEnabled(bool(t.strip())))

    result = [None]

    def _do_save():
        result[0] = line.text().strip()
        dlg.accept()

    btn_cancel.clicked.connect(dlg.reject)
    btn_save.clicked.connect(_do_save)
    line.returnPressed.connect(lambda: _do_save() if btn_save.isEnabled() else None)

    dlg.exec_()
    return result[0]


def _preset_is_deletable(text):
    t = (text or "").strip()
    if not t:
        return False
    if t == _PRESET_PLACEHOLDER_NOMATCH:
        return False
    if t == _PRESET_PLACEHOLDER_EMPTY:
        return False
    return True


class _PresetListView(QListView):
    """ListView para dropdown de presets con zona clickable de papelera."""

    def __init__(self, on_delete_cb, parent=None):
        super(_PresetListView, self).__init__(parent)
        self._on_delete = on_delete_cb
        self._hovered_trash_row = -1
        self.setMouseTracking(True)

    def showEvent(self, event):
        super(_PresetListView, self).showEvent(event)
        vp = self.viewport()
        if vp:
            vp.setMouseTracking(True)
            vp.installEventFilter(self)

    def hideEvent(self, event):
        super(_PresetListView, self).hideEvent(event)
        self._hovered_trash_row = -1

    def _in_trash_zone(self, row, pos):
        model = self.model()
        if not model:
            return False
        rect = self.visualRect(model.index(row, 0))
        return pos.x() >= rect.right() - _PRESET_TRASH_W

    def _update_hover(self, pos):
        model = self.model()
        if not model:
            return

        idx = self.indexAt(pos)
        row = idx.row() if idx.isValid() else -1
        new_hover = -1
        if row >= 0:
            text = model.data(model.index(row, 0)) or ""
            if _preset_is_deletable(text) and self._in_trash_zone(row, pos):
                new_hover = row

        if new_hover != self._hovered_trash_row:
            old = self._hovered_trash_row
            self._hovered_trash_row = new_hover
            vp = self.viewport()
            for r in (old, new_hover):
                if r >= 0:
                    vp.update(self.visualRect(model.index(r, 0)))

    def eventFilter(self, obj, event):
        vp = self.viewport()
        if obj is vp:
            etype = event.type()
            if etype == QtCore.QEvent.MouseMove:
                self._update_hover(event.pos())
            elif etype == QtCore.QEvent.Leave:
                old = self._hovered_trash_row
                self._hovered_trash_row = -1
                model = self.model()
                if model and old >= 0:
                    vp.update(self.visualRect(model.index(old, 0)))
            elif etype == QtCore.QEvent.MouseButtonRelease:
                model = self.model()
                if model:
                    idx = self.indexAt(event.pos())
                    row = idx.row() if idx.isValid() else -1
                    if row >= 0:
                        text = model.data(model.index(row, 0)) or ""
                        if _preset_is_deletable(text) and self._in_trash_zone(
                            row, event.pos()
                        ):
                            self._on_delete(row)
                            return True
        return super(_PresetListView, self).eventFilter(obj, event)


class _PresetDelegate(QStyledItemDelegate):
    """Delegate del combo de presets con icono trash."""

    def __init__(self, list_view, pix_trash, pix_hover, parent=None):
        super(_PresetDelegate, self).__init__(parent)
        self._view = list_view
        self._pix_trash = pix_trash
        self._pix_hover = pix_hover

    def paint(self, painter, option, index):
        painter.save()

        bg = (
            QtGui.QColor(Color.SURFACE_SELECTED)
            if (option.state & QStyle.State_Selected)
            else QtGui.QColor(Color.SURFACE_HEADER)
        )
        painter.fillRect(option.rect, bg)

        text = index.data() or ""
        deletable = _preset_is_deletable(text)
        text_rect = option.rect.adjusted(
            6, 0, -(_PRESET_TRASH_W + 4) if deletable else -4, 0
        )

        painter.setPen(QtGui.QColor(Color.TEXT))
        painter.drawText(
            text_rect,
            Qt.AlignVCenter | Qt.AlignLeft,
            text,
        )

        if deletable:
            hovered = self._view._hovered_trash_row == index.row()
            pix = (
                self._pix_hover
                if hovered and self._pix_hover and not self._pix_hover.isNull()
                else self._pix_trash
            )
            if pix and not pix.isNull():
                icon_size = 14
                tx = (
                    option.rect.right()
                    - _PRESET_TRASH_W
                    + (_PRESET_TRASH_W - icon_size) // 2
                )
                ty = option.rect.top() + (option.rect.height() - icon_size) // 2
                scaled = pix.scaled(
                    icon_size,
                    icon_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                painter.drawPixmap(tx, ty, scaled)

        painter.restore()

    def sizeHint(self, option, index):
        sh = super(_PresetDelegate, self).sizeHint(option, index)
        return sh.expandedTo(QtCore.QSize(0, 24))


class SearchAndReplaceWidget(QWidget):
    def __init__(self, nodes):
        super(SearchAndReplaceWidget, self).__init__()
        self.nodes = nodes
        self.normalized_nodes = [node["file"].getValue().lower() for node in self.nodes]
        self.ini_path = self.get_ini_path()
        self.icon_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")
        self.pix_read = QtGui.QPixmap(os.path.join(self.icon_dir, "node_read.svg"))
        self.pix_write = QtGui.QPixmap(os.path.join(self.icon_dir, "node_write.svg"))
        self.presets = []
        self._applying_preset = False
        self.filter_list_enabled = True
        self.reads_enabled = True
        self.writes_enabled = True
        self.loadPresets()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Search and Replace in Paths")
        # La ventana va al fondo de la app. Antes iba en #2B2B2B, que es mas
        # CLARO que el #272727 de la tabla: la tabla quedaba hundida respecto
        # de su ventana y la jerarquia se leia al reves.
        self.setStyleSheet(Style.WINDOW)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        # Tabla superior (filas dobles): Node / Type / Paths (Original + New)
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["Node", "Type", "Paths"])
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.preview_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.preview_table.setFocusPolicy(Qt.NoFocus)
        self.preview_table.setShowGrid(True)
        self.preview_table.setStyleSheet(_TABLE_STYLE)
        self.preview_table.setMinimumHeight(160)

        header = self.preview_table.horizontalHeader()
        header.setMinimumSectionSize(1)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.preview_table.setColumnWidth(0, 160)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.preview_table.setColumnWidth(1, 80)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        self.preview_table.setColumnWidth(2, 860)
        header.setStretchLastSection(True)
        for col_idx in range(3):
            hdr_item = self.preview_table.horizontalHeaderItem(col_idx)
            if hdr_item:
                hdr_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout.addWidget(self.preview_table, 1)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(
            "color:%s; padding:2px 6px;" % Color.TEXT_DIM
        )
        self.layout.addWidget(self.summary_label)

        self.layout.addWidget(_separator())

        line_style = Style.LINE_EDIT

        # Bloque de opciones
        opts_row = QHBoxLayout()
        opts_row.setSpacing(20)

        # Columna 1: Search & Replace 1
        col_sr1 = QVBoxLayout()
        col_sr1.setSpacing(6)
        col_sr1.addWidget(_section_label("Search & Replace 1"))
        sr1_row = QHBoxLayout()
        self.sr1_search_input = QLineEdit(self)
        self.sr1_search_input.setPlaceholderText("Search")
        self.sr1_search_input.setStyleSheet(line_style)
        self.sr1_replace_input = QLineEdit(self)
        self.sr1_replace_input.setPlaceholderText("Replace")
        self.sr1_replace_input.setStyleSheet(line_style)
        self.sr1_case_checkbox = QCheckBox("Case Sensitive")
        # lgaLabeled: aire entre el cuadrito y el texto (default spacing 0)
        self.sr1_case_checkbox.setProperty("lgaLabeled", True)
        self.sr1_case_checkbox.setFocusPolicy(Qt.NoFocus)
        self.sr1_case_checkbox.setStyleSheet(Style.CHECKBOX)
        sr1_swap = QPushButton("⇄")
        sr1_swap.setStyleSheet(Style.BTN_ICON)
        sr1_swap.setFixedWidth(28)
        sr1_swap.setFocusPolicy(Qt.NoFocus)
        sr1_swap.clicked.connect(
            lambda: self._swap_sr(self.sr1_search_input, self.sr1_replace_input)
        )
        sr1_row.addWidget(self.sr1_search_input, 1)
        sr1_row.addWidget(sr1_swap, 0)
        sr1_row.addWidget(self.sr1_replace_input, 1)
        sr1_row.addWidget(self.sr1_case_checkbox, 0)
        col_sr1.addLayout(sr1_row)
        col_sr1.addStretch()
        col_sr1_wrap = QWidget(self)
        col_sr1_wrap.setLayout(col_sr1)
        col_sr1_wrap.setFixedWidth(_OPTIONS_SR_COL_WIDTH)
        opts_row.addWidget(col_sr1_wrap, 0)

        opts_row.addWidget(_separator("v"))

        # Columna 2: Search & Replace 2
        col_sr2 = QVBoxLayout()
        col_sr2.setSpacing(6)
        col_sr2.addWidget(_section_label("Search & Replace 2"))
        sr2_row = QHBoxLayout()
        self.sr2_search_input = QLineEdit(self)
        self.sr2_search_input.setPlaceholderText("Search")
        self.sr2_search_input.setStyleSheet(line_style)
        self.sr2_replace_input = QLineEdit(self)
        self.sr2_replace_input.setPlaceholderText("Replace")
        self.sr2_replace_input.setStyleSheet(line_style)
        self.sr2_case_checkbox = QCheckBox("Case Sensitive")
        # lgaLabeled: aire entre el cuadrito y el texto (default spacing 0)
        self.sr2_case_checkbox.setProperty("lgaLabeled", True)
        self.sr2_case_checkbox.setFocusPolicy(Qt.NoFocus)
        self.sr2_case_checkbox.setStyleSheet(Style.CHECKBOX)
        sr2_swap = QPushButton("⇄")
        sr2_swap.setStyleSheet(Style.BTN_ICON)
        sr2_swap.setFixedWidth(28)
        sr2_swap.setFocusPolicy(Qt.NoFocus)
        sr2_swap.clicked.connect(
            lambda: self._swap_sr(self.sr2_search_input, self.sr2_replace_input)
        )
        sr2_row.addWidget(self.sr2_search_input, 1)
        sr2_row.addWidget(sr2_swap, 0)
        sr2_row.addWidget(self.sr2_replace_input, 1)
        sr2_row.addWidget(self.sr2_case_checkbox, 0)
        col_sr2.addLayout(sr2_row)
        col_sr2.addStretch()
        col_sr2_wrap = QWidget(self)
        col_sr2_wrap.setLayout(col_sr2)
        col_sr2_wrap.setFixedWidth(_OPTIONS_SR_COL_WIDTH)
        opts_row.addWidget(col_sr2_wrap, 0)

        opts_row.addWidget(_separator("v"))

        # Columna 3: Presets (dropdown + Save en la misma fila)
        col_preset = QVBoxLayout()
        col_preset.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(10)
        preset_lbl = QLabel("Preset:")
        preset_lbl.setStyleSheet("color:%s;" % Color.TEXT)
        preset_row.addWidget(preset_lbl)
        self.preset_combo = QComboBox()
        self.preset_combo.setStyleSheet(_COMBO_STYLE)
        self.preset_combo.setMinimumWidth(120)
        self.preset_combo.setFocusPolicy(Qt.NoFocus)
        pix_trash = QtGui.QPixmap(os.path.join(self.icon_dir, "trash.svg"))
        pix_hover = QtGui.QPixmap(os.path.join(self.icon_dir, "trash_hover.svg"))
        self.preset_list_view = _PresetListView(self._onPresetDelete)
        self.preset_combo.setView(self.preset_list_view)
        self.preset_list_view.setItemDelegate(
            _PresetDelegate(self.preset_list_view, pix_trash, pix_hover)
        )
        preset_row.addWidget(self.preset_combo, 1)
        self.save_preset_button = QPushButton("Save Preset", self)
        self.save_preset_button.setStyleSheet(_BTN_SMALL_TIGHT)
        self.save_preset_button.setFixedWidth(104)
        self.save_preset_button.setFocusPolicy(Qt.NoFocus)
        self.save_preset_button.clicked.connect(self.savePreset)
        preset_row.addWidget(self.save_preset_button, 0)
        col_preset.addLayout(preset_row)

        self.reset_values_button = QPushButton("Reset Values", self)
        self.reset_values_button.setStyleSheet(_BTN_SMALL_TIGHT)
        self.reset_values_button.setFixedWidth(104)
        self.reset_values_button.setFocusPolicy(Qt.NoFocus)
        self.reset_values_button.clicked.connect(self.resetValues)
        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_row.addWidget(self.reset_values_button, 0)
        col_preset.addLayout(reset_row)

        col_preset.addStretch()
        col_preset_wrap = QWidget(self)
        col_preset_wrap.setLayout(col_preset)
        col_preset_wrap.setFixedWidth(_OPTIONS_PRESET_COL_WIDTH)
        opts_row.addWidget(col_preset_wrap, 0)

        self.layout.addLayout(opts_row)

        self.layout.addWidget(_separator())

        # Footer: checkboxes + boton principal
        footer = QHBoxLayout()
        footer.setSpacing(12)

        self.filter_checkbox = QCheckBox("Filter List")
        # lgaLabeled: aire entre el cuadrito y el texto (default spacing 0)
        self.filter_checkbox.setProperty("lgaLabeled", True)
        self.filter_checkbox.setChecked(self.filter_list_enabled)
        self.filter_checkbox.setToolTip("Filter rows by search text.")
        footer.addWidget(self.filter_checkbox)

        footer.addWidget(_separator("v"))

        self.read_checkbox = QCheckBox("Reads")
        self.read_checkbox.setProperty("lgaLabeled", True)
        self.read_checkbox.setChecked(self.reads_enabled)
        self.read_checkbox.setToolTip("Include Read nodes in search and replace.")
        footer.addWidget(self.read_checkbox)

        self.write_checkbox = QCheckBox("Writes")
        self.write_checkbox.setProperty("lgaLabeled", True)
        self.write_checkbox.setChecked(self.writes_enabled)
        self.write_checkbox.setToolTip("Include Write nodes in search and replace.")
        footer.addWidget(self.write_checkbox)

        footer.addStretch()

        self.run_button = QPushButton("Replace Paths", self)
        self.run_button.setStyleSheet(_BTN_PRIMARY)
        self.run_button.setFocusPolicy(Qt.NoFocus)
        self.run_button.clicked.connect(self.replacePaths)
        footer.addWidget(self.run_button)

        self.layout.addLayout(footer)

        # Conexiones de UI
        self.sr1_search_input.textChanged.connect(self._onSettingsChanged)
        self.sr1_replace_input.textChanged.connect(self._onSettingsChanged)
        self.sr1_case_checkbox.stateChanged.connect(self._onSettingsChanged)
        self.sr2_search_input.textChanged.connect(self._onSettingsChanged)
        self.sr2_replace_input.textChanged.connect(self._onSettingsChanged)
        self.sr2_case_checkbox.stateChanged.connect(self._onSettingsChanged)
        self.filter_checkbox.stateChanged.connect(self._onFooterOptionsChanged)
        self.read_checkbox.stateChanged.connect(self._onFooterOptionsChanged)
        self.write_checkbox.stateChanged.connect(self._onFooterOptionsChanged)
        self.preset_combo.currentIndexChanged.connect(self.onPresetSelected)

        self.run_button.setShortcut(QKeySequence(Qt.Key_Return))
        self.sr1_search_input.setFocus()

        self.refreshPresetCombo()
        self.resize(_WINDOW_WIDTH, 640)
        self.setMinimumSize(960, 420)
        self.updatePreviews()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super(SearchAndReplaceWidget, self).keyPressEvent(event)

    def get_ini_path(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(dir_path, "LGA_mediaPathReplacer_presets.ini")

    def loadPresets(self):
        config = configparser.ConfigParser()
        config.read(self.ini_path)

        self.filter_list_enabled = self._configBool(
            config, "Options", "filter_list", True
        )
        self.reads_enabled = self._configBool(config, "Options", "reads", True)
        self.writes_enabled = self._configBool(config, "Options", "writes", True)

        presets_by_index = {}
        if config.has_section("Presets"):
            for key, value in config.items("Presets"):
                match = re.match(
                    r"^(name|search|replace|sr1_search|sr1_replace|sr1_case|sr2_search|sr2_replace|sr2_case)_preset_(\d+)$",
                    key.lower(),
                )
                if not match:
                    continue
                field = match.group(1)
                index = int(match.group(2))
                if index not in presets_by_index:
                    presets_by_index[index] = {
                        "name": "",
                        "sr1_search": "",
                        "sr1_replace": "",
                        "sr1_case": "false",
                        "sr2_search": "",
                        "sr2_replace": "",
                        "sr2_case": "false",
                    }
                if field == "search":
                    presets_by_index[index]["sr1_search"] = value
                elif field == "replace":
                    presets_by_index[index]["sr1_replace"] = value
                else:
                    presets_by_index[index][field] = value

        self.presets = []
        for index in sorted(presets_by_index.keys()):
            if not presets_by_index[index].get("name", "").strip():
                presets_by_index[index]["name"] = "Preset %d" % index
            self.presets.append(presets_by_index[index])

    @staticmethod
    def _configBool(config, section, option, default):
        if not config.has_option(section, option):
            return default
        try:
            return config.getboolean(section, option)
        except ValueError:
            return default

    def _writeOptions(self, config):
        config.add_section("Options")
        if hasattr(self, "filter_checkbox"):
            self.filter_list_enabled = self.filter_checkbox.isChecked()
            self.reads_enabled = self.read_checkbox.isChecked()
            self.writes_enabled = self.write_checkbox.isChecked()
        config.set("Options", "filter_list", str(self.filter_list_enabled).lower())
        config.set("Options", "reads", str(self.reads_enabled).lower())
        config.set("Options", "writes", str(self.writes_enabled).lower())

    def _writePresets(self):
        config = configparser.ConfigParser()
        self._writeOptions(config)
        config.add_section("Presets")
        for i, preset in enumerate(self.presets, 1):
            config.set("Presets", "name_preset_%d" % i, preset.get("name", "Preset %d" % i))
            for field in _PRESET_FIELDS:
                config.set("Presets", "%s_preset_%d" % (field, i), preset.get(field, ""))
            # Compatibilidad con presets antiguos:
            config.set("Presets", "search_preset_%d" % i, preset.get("sr1_search", ""))
            config.set("Presets", "replace_preset_%d" % i, preset.get("sr1_replace", ""))
        with open(self.ini_path, "w", encoding="utf-8") as config_file:
            config.write(config_file)

    def _currentPresetData(self):
        return {
            "sr1_search": self.sr1_search_input.text(),
            "sr1_replace": self.sr1_replace_input.text(),
            "sr1_case": str(self.sr1_case_checkbox.isChecked()).lower(),
            "sr2_search": self.sr2_search_input.text(),
            "sr2_replace": self.sr2_replace_input.text(),
            "sr2_case": str(self.sr2_case_checkbox.isChecked()).lower(),
        }

    def _presetMatchesCurrent(self, preset):
        current = self._currentPresetData()
        for field in _PRESET_FIELDS:
            if preset.get(field, "") != current.get(field, ""):
                return False
        return True

    def refreshPresetCombo(self, selected_preset_index=None):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        if not self.presets:
            self.preset_combo.addItem(_PRESET_PLACEHOLDER_EMPTY)
            self.preset_combo.setEnabled(False)
            self.preset_combo.blockSignals(False)
            return

        self.preset_combo.setEnabled(True)
        self.preset_combo.addItem(_PRESET_PLACEHOLDER_NOMATCH)
        for idx, preset in enumerate(self.presets):
            preset_name = preset.get("name", "").strip() or ("Preset %d" % (idx + 1))
            self.preset_combo.addItem(preset_name)

        if selected_preset_index is None:
            self.preset_combo.setCurrentIndex(0)
        else:
            combo_idx = max(
                1, min(selected_preset_index + 1, self.preset_combo.count() - 1)
            )
            self.preset_combo.setCurrentIndex(combo_idx)
        self.preset_combo.blockSignals(False)
        self._updatePresetComboSelection()

    def _updatePresetComboSelection(self):
        if not self.preset_combo.isEnabled():
            return
        match_idx = None
        for idx, preset in enumerate(self.presets):
            if self._presetMatchesCurrent(preset):
                match_idx = idx
                break
        target_combo_idx = (match_idx + 1) if match_idx is not None else 0
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(target_combo_idx)
        self.preset_combo.blockSignals(False)

    def onPresetSelected(self, combo_index):
        if combo_index <= 0:
            return
        preset_index = combo_index - 1
        if preset_index >= len(self.presets):
            return
        preset = self.presets[preset_index]
        self._applying_preset = True
        self.sr1_search_input.setText(preset.get("sr1_search", ""))
        self.sr1_replace_input.setText(preset.get("sr1_replace", ""))
        self.sr1_case_checkbox.setChecked(
            preset.get("sr1_case", "false").lower() == "true"
        )
        self.sr2_search_input.setText(preset.get("sr2_search", ""))
        self.sr2_replace_input.setText(preset.get("sr2_replace", ""))
        self.sr2_case_checkbox.setChecked(
            preset.get("sr2_case", "false").lower() == "true"
        )
        self._applying_preset = False
        self.updatePreviews()
        self._updatePresetComboSelection()

    def savePreset(self):
        data = self._currentPresetData()
        if not any(
            (
                data["sr1_search"],
                data["sr1_replace"],
                data["sr2_search"],
                data["sr2_replace"],
            )
        ):
            print("Search/Replace fields must not be all empty.")
            return
        preset_name = _show_save_preset_dialog(parent=self)
        if not preset_name:
            return
        data["name"] = preset_name
        self.presets.append(data)
        self._writePresets()
        self.refreshPresetCombo(selected_preset_index=len(self.presets) - 1)

    def _onPresetDelete(self, combo_row):
        if combo_row <= 0:
            return
        preset_index = combo_row - 1
        if preset_index < 0 or preset_index >= len(self.presets):
            return
        del self.presets[preset_index]
        self._writePresets()
        self.preset_combo.hidePopup()
        self.refreshPresetCombo()
        self.updatePreviews()

    def resetValues(self):
        self.sr1_search_input.setText("")
        self.sr1_replace_input.setText("")
        self.sr2_search_input.setText("")
        self.sr2_replace_input.setText("")

    def _onSettingsChanged(self, *_):
        self.updatePreviews()
        if not self._applying_preset:
            self._updatePresetComboSelection()

    def _onFooterOptionsChanged(self, *_):
        self.updatePreviews()
        self._writePresets()

    def _swap_sr(self, search_edit, replace_edit):
        a = search_edit.text()
        b = replace_edit.text()
        search_edit.setText(b)
        replace_edit.setText(a)

    def _isNodeAllowedByFilters(self, node):
        if node.Class() == "Read":
            return self.read_checkbox.isChecked()
        if node.Class() == "Write":
            return self.write_checkbox.isChecked()
        return False

    @staticmethod
    def _containsLiteral(text, normalized_text, needle, case_sensitive):
        if not needle:
            return False
        if case_sensitive:
            return needle in text
        return needle.lower() in normalized_text

    @staticmethod
    def _findLiteral(haystack, needle, start_idx, case_sensitive):
        if case_sensitive:
            return haystack.find(needle, start_idx)
        return haystack.lower().find(needle.lower(), start_idx)

    @staticmethod
    def _applySearchReplaceStageMeta(
        cur_text,
        cur_orig_map,
        cur_tags,
        search_text,
        replace_text,
        case_sensitive,
        stage_id,
    ):
        if not search_text:
            return cur_text, cur_orig_map, cur_tags, set()

        out_text_parts = []
        out_map = []
        out_tags = []
        changed_orig = set()
        idx = 0

        while True:
            pos = SearchAndReplaceWidget._findLiteral(
                cur_text, search_text, idx, case_sensitive
            )
            if pos < 0:
                break
            end = pos + len(search_text)

            out_text_parts.append(cur_text[idx:pos])
            out_map.extend(cur_orig_map[idx:pos])
            out_tags.extend([set(x) for x in cur_tags[idx:pos]])

            src_slice_map = cur_orig_map[pos:end]
            src_slice_tags = [set(x) for x in cur_tags[pos:end]]
            matched_text = cur_text[pos:end]
            if replace_text == matched_text:
                out_text_parts.append(matched_text)
                out_map.extend(src_slice_map)
                out_tags.extend(src_slice_tags)
            else:
                for oi in src_slice_map:
                    if oi is not None:
                        changed_orig.add(oi)
                out_text_parts.append(replace_text)
                out_map.extend([None] * len(replace_text))
                out_tags.extend([{stage_id} for _ in replace_text])
            idx = end

        out_text_parts.append(cur_text[idx:])
        out_map.extend(cur_orig_map[idx:])
        out_tags.extend([set(x) for x in cur_tags[idx:]])
        return "".join(out_text_parts), out_map, out_tags, changed_orig

    def _computePathPreview(self, original_path):
        cur_text = original_path
        cur_orig_map = list(range(len(cur_text)))
        cur_tags = [set() for _ in cur_text]
        orig_stage_marks = {1: set(), 2: set()}

        cur_text, cur_orig_map, cur_tags, changed_orig = self._applySearchReplaceStageMeta(
            cur_text,
            cur_orig_map,
            cur_tags,
            self.sr1_search_input.text(),
            self.sr1_replace_input.text(),
            self.sr1_case_checkbox.isChecked(),
            stage_id=1,
        )
        orig_stage_marks[1].update(changed_orig)

        cur_text, cur_orig_map, cur_tags, changed_orig = self._applySearchReplaceStageMeta(
            cur_text,
            cur_orig_map,
            cur_tags,
            self.sr2_search_input.text(),
            self.sr2_replace_input.text(),
            self.sr2_case_checkbox.isChecked(),
            stage_id=2,
        )
        orig_stage_marks[2].update(changed_orig)

        orig_colors = {}
        for stage_id in (1, 2):
            color = _STAGE_COLORS.get(stage_id)
            if not color:
                continue
            for oi in orig_stage_marks.get(stage_id, ()):
                orig_colors[oi] = color

        renamed_colors = {}
        for idx, tags in enumerate(cur_tags):
            if not tags:
                continue
            stage_id = sorted(tags)[-1]
            color = _STAGE_COLORS.get(stage_id)
            if color:
                renamed_colors[idx] = color

        original_html = _colorize_with_map(original_path, orig_colors)
        renamed_html = _colorize_with_map(cur_text, renamed_colors)
        return cur_text, original_html, renamed_html

    def _buildNewPath(self, original_path):
        new_path, _orig_html, _ren_html = self._computePathPreview(original_path)
        return new_path

    def _rowPassesFilter(self, original_path, normalized_path):
        if not self.filter_checkbox.isChecked():
            return True

        sr1_search = self.sr1_search_input.text()
        sr2_search = self.sr2_search_input.text()
        if not sr1_search and not sr2_search:
            return True

        if self._containsLiteral(
            original_path,
            normalized_path,
            sr1_search,
            self.sr1_case_checkbox.isChecked(),
        ):
            return True
        if self._containsLiteral(
            original_path,
            normalized_path,
            sr2_search,
            self.sr2_case_checkbox.isChecked(),
        ):
            return True
        return False

    def _buildNodeCell(self, node_name, node_type):
        w = QWidget()
        w.setStyleSheet("background-color:%s;" % Color.SURFACE)
        layout = QHBoxLayout(w)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setStyleSheet("background-color:%s;" % Color.SURFACE)
        pix = self.pix_read if node_type == "Read" else self.pix_write
        if pix and not pix.isNull():
            icon_lbl.setPixmap(
                pix.scaled(
                    18,
                    18,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(icon_lbl, 0)

        txt_lbl = QLabel(node_name)
        txt_lbl.setStyleSheet(
            "color:%s; background-color:%s;" % (Color.TEXT, Color.SURFACE)
        )
        txt_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(txt_lbl, 1)
        return w

    def replacePaths(self):
        changed_count = 0
        nuke.Undo().begin("Replace All Paths")
        try:
            for node in self.nodes:
                if not self._isNodeAllowedByFilters(node):
                    continue
                original_path = node["file"].getValue()
                new_path = self._buildNewPath(original_path)
                if new_path != original_path:
                    node["file"].setValue(new_path)
                    changed_count += 1
        finally:
            nuke.Undo().end()

        self.normalized_nodes = [node["file"].getValue().lower() for node in self.nodes]
        self.updatePreviews()
        print("Updated %d node paths." % changed_count)

    def updateNodes(self, new_nodes):
        self.nodes = new_nodes
        self.normalized_nodes = [node["file"].getValue().lower() for node in self.nodes]

    def updatePreviews(self):
        preview_rows = []
        for node, normalized_path in zip(self.nodes, self.normalized_nodes):
            if not self._isNodeAllowedByFilters(node):
                continue

            original_path = node["file"].getValue()
            if not self._rowPassesFilter(original_path, normalized_path):
                continue

            new_path, original_html, renamed_html = self._computePathPreview(original_path)
            changed = new_path != original_path
            preview_rows.append(
                {
                    "node_name": node.name(),
                    "node_type": node.Class(),
                    "original_html": original_html,
                    "renamed_html": renamed_html,
                    "changed": changed,
                }
            )

        self.preview_table.setRowCount(len(preview_rows))
        changed_count = 0
        for row_idx, row_data in enumerate(preview_rows):
            if row_data["changed"]:
                changed_count += 1
            self.preview_table.setCellWidget(
                row_idx,
                0,
                self._buildNodeCell(row_data["node_name"], row_data["node_type"]),
            )
            self.preview_table.setCellWidget(
                row_idx,
                1,
                _cell_html_label(
                    "<span style='color:%s;'>%s</span>"
                    % (Color.TEXT, _html_escape(row_data["node_type"]))
                ),
            )
            self.preview_table.setCellWidget(
                row_idx,
                2,
                _path_preview_cell(row_data["original_html"], row_data["renamed_html"]),
            )
            self.preview_table.setRowHeight(row_idx, 46)

        self.summary_label.setText(
            "Rows: %d | With changes: %d | Nodes total: %d"
            % (len(preview_rows), changed_count, len(self.nodes))
        )


def show_search_replace_widget():
    selected_nodes = nuke.selectedNodes("Read") + nuke.selectedNodes("Write")
    if not selected_nodes:
        selected_nodes = nuke.allNodes("Read") + nuke.allNodes("Write")

    global search_replace_widget
    search_replace_widget = SearchAndReplaceWidget(selected_nodes)
    search_replace_widget.show()


if __name__ == "__main__":
    # Permite ejecutar/pegar el script completo en Script Editor y abrir la ventana.
    show_search_replace_widget()
