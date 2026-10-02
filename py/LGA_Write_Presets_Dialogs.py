"""
____________________________________________________________________

  LGA_Write_Presets_Dialogs v2.82 | Lega

  Cartel para elegir el plate cuando se pega un preset de cadena en un
  shot con varios .amf y el Read de arriba no dice cual es.

  COPIA del cartel 1 de LGA_ApplyAMF_Dialogs v1.04 (repo
  LGA_ToolPack-B), con el modulo de estilo y el adapter de este pack. Un
  cambio de forma en uno se replica en el otro.

  pick_plate(parent, entries) -> entry|None
      Filas numeradas, una por plate. La fila ES la accion: click o la
      tecla del numero confirma. Esc o cerrar cancela (None). Con 0 o 1
      entradas no se muestra nada.

  v2.79: Modulo nuevo.
____________________________________________________________________
"""

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, Qt, QShortcut as _QShortcut
from LGA_UI_Style_ToolPack import Style, Color, Metric, apply_ui_font, semibold


# No hay hoja para un "chip numerado": se arma con tokens, nunca con un hex.
_BADGE_SIZE = 22
_BADGE_FONT_SIZE = 11

_BADGE_STYLE = """
QLabel#lgaWpBadge {
    background-color: %(accent)s;
    color: %(on_accent)s;
    border: 1px solid %(accent)s;
    border-radius: %(radius)dpx;
}
""" % {
    "accent": Color.ACCENT,
    "on_accent": Color.TEXT_ON_ACCENT,
    "radius": Metric.RADIUS_SMALL,
}

_ROW_STYLE = """
#lgaWpRow { background-color: transparent; border: none; }
#lgaWpRow:hover { background-color: %(hover)s; }
""" % {"hover": Color.SURFACE_HOVER}

_LIST_FRAME_STYLE = """
#lgaWpListFrame {
    background-color: %(surface)s;
    border: 1px solid %(border)s;
    border-radius: %(radius)dpx;
}
""" % {
    "surface": Color.SURFACE,
    "border": Color.BORDER,
    "radius": Metric.RADIUS_CARD,
}


def _make_badge(number, parent=None):
    badge = QtWidgets.QLabel(str(number), parent)
    badge.setObjectName("lgaWpBadge")
    badge.setAlignment(Qt.AlignCenter)
    badge.setFixedSize(_BADGE_SIZE, _BADGE_SIZE)
    badge.setStyleSheet(_BADGE_STYLE)
    badge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    return badge


def _finalize_fonts(dialog):
    """Tamano y peso de badges y hint DESPUES de apply_ui_font, que los pisa."""
    for badge in dialog.findChildren(QtWidgets.QLabel, "lgaWpBadge"):
        font = badge.font()
        font.setPixelSize(_BADGE_FONT_SIZE)
        semibold(font)
        badge.setFont(font)
    for hint in dialog.findChildren(QtWidgets.QLabel, "lgaWpHint"):
        font = hint.font()
        font.setPixelSize(Metric.FORM_PATH_FONT_SIZE)
        hint.setFont(font)


def _make_hairline(parent=None):
    """Separador: el color lo pone Style.FORM por cascada."""
    line = QtWidgets.QFrame(parent)
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFixedHeight(1)
    return line


def _fit_height(dialog):
    """Alto de apertura despues de que el layout corrio (labels con wrap)."""
    layout = dialog.layout()
    if layout is None:
        return
    layout.activate()
    if layout.hasHeightForWidth():
        height = layout.totalHeightForWidth(dialog.width())
    else:
        height = dialog.sizeHint().height()
    dialog.setFixedHeight(height)


class _RowWidget(QtWidgets.QWidget):
    """Fila clickeable con badge + nombre."""

    def __init__(self, index, text, on_activate, parent=None):
        super(_RowWidget, self).__init__(parent)
        self._on_activate = on_activate
        self.setObjectName("lgaWpRow")
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(_ROW_STYLE)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(10)
        layout.addWidget(_make_badge(index + 1, self), 0, Qt.AlignVCenter)

        label = QtWidgets.QLabel(text, self)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(label, 1, Qt.AlignVCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._on_activate:
            event.accept()
            self._on_activate()
            return
        super(_RowWidget, self).mousePressEvent(event)


class _PickPlateDialog(QtWidgets.QDialog):
    def __init__(self, parent, entries):
        super(_PickPlateDialog, self).__init__(parent)
        self.selected_entry = None
        self._entries = entries
        self._height_fitted = False

        self.setWindowTitle("Select Plate")
        self.setModal(True)
        self.setStyleSheet(Style.FORM)
        self.setMinimumWidth(Metric.DIALOG_MIN_WIDTH)

        self._build_ui()
        self._install_shortcuts()
        apply_ui_font(self)
        _finalize_fonts(self)

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(
            Metric.DIALOG_MARGIN, Metric.DIALOG_MARGIN, Metric.DIALOG_MARGIN, Metric.DIALOG_MARGIN
        )
        root.setSpacing(Metric.SPACING + 4)

        title = QtWidgets.QLabel("Select Plate", self)
        title.setProperty("lgaTitle", True)
        root.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "This shot has more than one .amf. Choose which plate's CDL and LUT "
            "the preset should load.",
            self,
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: %s;" % Color.TEXT_DIM)
        root.addWidget(subtitle)

        list_frame = QtWidgets.QFrame(self)
        list_frame.setObjectName("lgaWpListFrame")
        list_frame.setAttribute(Qt.WA_StyledBackground, True)
        list_frame.setStyleSheet(_LIST_FRAME_STYLE)
        list_layout = QtWidgets.QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        for index, entry in enumerate(self._entries):
            list_layout.addWidget(
                _RowWidget(index, _plate_label(entry), self._make_activator(entry), list_frame)
            )
            if index < len(self._entries) - 1:
                list_layout.addWidget(_make_hairline(list_frame))
        root.addWidget(list_frame)

        hint = QtWidgets.QLabel(self)
        hint.setObjectName("lgaWpHint")
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.RichText)
        hint.setText(
            "Press <span style='color:%s'><b>1</b></span>-"
            "<span style='color:%s'><b>%d</b></span> to choose a plate.<br/>"
            "Press <span style='color:%s'><b>Esc</b></span> to leave the look nodes empty."
            % (Color.ACCENT_HOVER, Color.ACCENT_HOVER, min(9, len(self._entries)), Color.ACCENT_HOVER)
        )
        hint.setStyleSheet("color: %s;" % Color.TEXT_DIM)
        root.addWidget(hint)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        cancel_button = QtWidgets.QPushButton("Cancel (esc)", self)
        cancel_button.setStyleSheet(Style.BTN_SECONDARY)
        cancel_button.setAutoDefault(False)
        cancel_button.setDefault(False)
        cancel_button.clicked.connect(self.reject)
        button_row.addWidget(cancel_button)
        root.addLayout(button_row)

    def _make_activator(self, entry):
        def _activar():
            self.selected_entry = entry
            self.accept()

        return _activar

    def _install_shortcuts(self):
        for i in range(min(9, len(self._entries))):
            shortcut = _QShortcut(QtGui.QKeySequence(str(i + 1)), self)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self._make_activator(self._entries[i]))

    def showEvent(self, event):
        super(_PickPlateDialog, self).showEvent(event)
        if self._height_fitted:
            return
        self._height_fitted = True
        _fit_height(self)


def _plate_label(entry):
    if entry.get("version") is None:
        return entry["plate"]
    return "%s v%03d" % (entry["plate"], entry["version"])


def pick_plate(parent, entries):
    """Devuelve la entrada elegida, o None si se cancelo."""
    if not entries:
        return None
    if len(entries) == 1:
        return entries[0]
    dialog = _PickPlateDialog(parent, entries)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return dialog.selected_entry
    return None
