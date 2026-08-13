"""
____________________________________________________________________

  LGA_ToolPack_EnabledPanel v1.03 | Lega

  Panel para activar y desactivar las herramientas del pack.

  Lee la lista de tools del manifiesto que viaja en el pack y guarda
  la eleccion del usuario fuera del pack, para que sobreviva a los
  updates.

  v1.03: El look sale de LGA_UI_Style_ToolPack: grupos con marco y
         titulo, botones del pack y el path de la config coloreado.
  v1.02: Se corrige el tooltip de Reset, que decia lo contrario de
         lo que hace, y aclara que despues hay que guardar.
  v1.01: Tooltips por LGA_tooltip_helper y aviso claro si el
         manifiesto del pack no se puede leer.
  v1.00: Version inicial.
____________________________________________________________________
"""

import sys

from LGA_QtAdapter_ToolPack import QtWidgets, QtCore
from LGA_UI_Style_ToolPack import Color, Metric, Style, colorize_path

import LGA_ToolPack_Enabled as enabled_config

try:
    from LGA_tooltip_helper import apply_tooltip_stylesheet
except ImportError:
    # El panel funciona igual sin el helper; solo pierde el look estandar.
    def apply_tooltip_stylesheet(target=None):
        pass


QApplication = QtWidgets.QApplication
Qt = QtCore.Qt


# Los tooltips van en castellano y salen de aca, no hardcodeados en el widget,
# para que la migracion a bilingue sea un cambio de datos.
TOOLTIPS = {
    "window": "Elegi que herramientas aparecen en el menu",
    "checkbox": "Destildar oculta la herramienta del menu y evita que se cargue",
    "all_on": "Vuelve a activar todas las herramientas",
    "all_off": "Desactiva todas las herramientas",
    "reset": "Vuelve todo a los valores de fabrica; despues hay que guardar",
    "save": "Guarda y cierra. Los cambios se ven al reiniciar Nuke",
    "cancel": "Cierra sin guardar",
    "path": "Archivo donde se guarda tu eleccion, fuera del pack",
}


def _pretty(key):
    """`Show_in_Flow` -> `Show in Flow`."""
    return key.replace("_", " ")


class EnabledPanel(QtWidgets.QWidget):
    """Grilla de checkboxes, una por herramienta, agrupada como el menu."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LGA ToolPack - Enable Tools")
        self.setToolTip(TOOLTIPS["window"])
        self.setStyleSheet(Style.FORM)
        self._checkboxes = {}
        self._defaults = enabled_config.read_defaults()
        self._build_ui()

    # -- construccion ------------------------------------------------------

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(*([Metric.WINDOW_MARGIN] * 4))
        root.setSpacing(Metric.SPACING)
        apply_tooltip_stylesheet(self)

        groups = enabled_config.read_default_groups()
        if not groups:
            # Sin manifiesto no hay nada que dibujar, y dibujar una grilla
            # vacia seria peor: el usuario guardaria y creeria que apago todo.
            # Guardar tambien esta bloqueado del lado del core.
            self._build_error_ui(root)
            return

        header = QtWidgets.QLabel(
            "Untick a tool to hide it from the menu and skip loading it.\n"
            "Changes take effect after restarting Nuke."
        )
        header.setStyleSheet("color: %s;" % Color.TEXT_DIM)
        root.addWidget(header)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        content = QtWidgets.QWidget()
        columns = QtWidgets.QHBoxLayout(content)
        columns.setAlignment(Qt.AlignTop)

        current = enabled_config.load_flags()

        # Dos columnas para que la ventana no quede larguisima: se reparten los
        # grupos enteros, sin cortar un grupo por la mitad.
        column_layouts = []
        for _ in range(2):
            layout = QtWidgets.QVBoxLayout()
            layout.setAlignment(Qt.AlignTop)
            columns.addLayout(layout)
            column_layouts.append(layout)

        total = sum(len(keys) for _, keys in groups)
        placed = 0
        column_index = 0

        for title, keys in groups:
            if not keys:
                continue
            box = QtWidgets.QGroupBox(title or "TOOLS")
            box_layout = QtWidgets.QVBoxLayout(box)
            for key in keys:
                checkbox = QtWidgets.QCheckBox(_pretty(key))
                checkbox.setToolTip(TOOLTIPS["checkbox"])
                checkbox.setChecked(current.get(key, self._defaults.get(key, True)))
                box_layout.addWidget(checkbox)
                self._checkboxes[key] = checkbox
            column_layouts[column_index].addWidget(box)

            placed += len(keys)
            if column_index == 0 and placed >= total / 2.0:
                column_index = 1

        scroll.setWidget(content)
        root.addWidget(scroll)

        path = enabled_config.get_user_path()
        path_label = QtWidgets.QLabel(colorize_path(path) if path else "")
        path_label.setTextFormat(Qt.RichText)
        path_label.setStyleSheet("font-size: 10px;")
        path_label.setToolTip(TOOLTIPS["path"])
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(path_label)

        root.addLayout(self._build_buttons())

    def _build_error_ui(self, root):
        """Pantalla de error cuando el manifiesto del pack no se puede leer."""
        message = QtWidgets.QLabel(
            "Could not read the tool list shipped with the pack:\n\n%s\n\n"
            "Your saved configuration was left untouched.\n"
            "Reinstalling the pack should fix this." % enabled_config.get_default_path()
        )
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(message)

        close = QtWidgets.QPushButton("Close")
        close.setStyleSheet(Style.BTN_SECONDARY)
        close.clicked.connect(self.close)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _build_buttons(self):
        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(8)

        all_on = QtWidgets.QPushButton("All On")
        all_on.setStyleSheet(Style.BTN_SMALL)
        all_on.setToolTip(TOOLTIPS["all_on"])
        all_on.clicked.connect(lambda: self._set_all(True))

        all_off = QtWidgets.QPushButton("All Off")
        all_off.setStyleSheet(Style.BTN_SMALL)
        all_off.setToolTip(TOOLTIPS["all_off"])
        all_off.clicked.connect(lambda: self._set_all(False))

        reset = QtWidgets.QPushButton("Reset")
        reset.setStyleSheet(Style.BTN_SMALL)
        reset.setToolTip(TOOLTIPS["reset"])
        reset.clicked.connect(self._reset)

        save = QtWidgets.QPushButton("Save")
        save.setStyleSheet(Style.BTN_PRIMARY)
        save.setToolTip(TOOLTIPS["save"])
        save.setDefault(True)
        save.clicked.connect(self._save)

        cancel = QtWidgets.QPushButton("Cancel")
        cancel.setStyleSheet(Style.BTN_SECONDARY)
        cancel.setToolTip(TOOLTIPS["cancel"])
        cancel.clicked.connect(self.close)

        buttons.addWidget(all_on)
        buttons.addWidget(all_off)
        buttons.addWidget(reset)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        return buttons

    # -- acciones ----------------------------------------------------------

    def _set_all(self, value):
        for checkbox in self._checkboxes.values():
            checkbox.setChecked(value)

    def _reset(self):
        for key, checkbox in self._checkboxes.items():
            checkbox.setChecked(self._defaults.get(key, True))

    def _save(self):
        flags = dict(
            (key, checkbox.isChecked()) for key, checkbox in self._checkboxes.items()
        )
        if not enabled_config.write_user_overrides(flags):
            QtWidgets.QMessageBox.warning(
                self,
                "LGA ToolPack",
                "Could not save the configuration.\n"
                "Check the Script Editor for details.",
            )
            return

        # El menu ya se armo al arrancar Nuke y `add_tool` no registra las
        # tools apagadas, asi que no hay forma de reflejar el cambio en
        # caliente: hay que decirlo, no dejar que el usuario lo descubra.
        QtWidgets.QMessageBox.information(
            self,
            "LGA ToolPack",
            "Saved. Restart Nuke to apply the changes.",
        )
        self.close()

    def keyPressEvent(self, event):
        """Cerrar la ventana si se presiona ESC."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


panel_instance = None


def main():
    """Abre el panel y lo mantiene vivo."""
    global panel_instance
    app = QApplication.instance() or QApplication(sys.argv)
    if panel_instance is None or not panel_instance.isVisible():
        panel_instance = EnabledPanel()
        panel_instance.resize(620, 620)
        panel_instance.show()
    else:
        panel_instance.raise_()
        panel_instance.activateWindow()


if __name__ == "__main__":
    main()
