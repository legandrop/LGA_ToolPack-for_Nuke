"""
____________________________________________________________________

  LGA_ToolPack_EnabledPanel v1.06 | Lega

  Panel para activar y desactivar las herramientas del pack.

  Lee la lista de tools del manifiesto que viaja en el pack y guarda
  la eleccion del usuario fuera del pack, para que sobreviva a los
  updates.

  Modulos de esta tool (todos van con la misma version):
    LGA_ToolPack_EnabledPanel.py   <- este, el principal (la ventana)
    LGA_ToolPack_Enabled.py        <- el core que lee y guarda los flags

  Donde mas se ve esta version, y hay que moverla junto con el header:
    - El titulo de la seccion "Enable Tools" del README.md, que es a
      mano y no lo actualiza nada. La ventana no muestra version.

  v1.06: El subrayado del path ya no queda enganchado al salir del
         hover: era rich text con `<a>` y `linkHovered`, y reescribir
         el HTML al entrar movia el ancla debajo del mouse, asi que la
         salida muchas veces no se emitia. Ahora es un QLabel propio,
         PathLink, con enterEvent y leaveEvent, que son del widget y no
         del contenido. El texto ademas queda de verdad en 14 px: en
         v1.05 la fuente se le ponia a la ventana y los hijos no la
         heredaban por tener hoja de estilo.
  v1.05: La ventana usa la fuente del pack en 13 px -antes heredaba la
         del host, que en Nuke sale mucho mas chica que el indicador
         del checkbox-, el nombre de la tool deja de estar pegado al
         cuadrito, y el path de la config va en un solo color y se
         clickea para mostrarlo en el Finder / Explorer. El arcoiris
         de colorize_path sirve para comparar dos rutas, y aca no hay
         nada que comparar.
  v1.04: La ventana abre con el alto que necesita el contenido. Estaba
         clavada en 620x620 y siempre mostraba scrollbar aunque faltaran
         veinte pixeles; ademas ese alto se desactualizaba al agregar o
         sacar una tool del manifiesto.
  v1.03: El look sale de LGA_UI_Style_ToolPack: grupos con marco y
         titulo, botones del pack y el path de la config coloreado.
  v1.02: Se corrige el tooltip de Reset, que decia lo contrario de
         lo que hace, y aclara que despues hay que guardar.
  v1.01: Tooltips por LGA_tooltip_helper y aviso claro si el
         manifiesto del pack no se puede leer.
  v1.00: Version inicial.
____________________________________________________________________
"""

import os
import subprocess
import sys

from LGA_QtAdapter_ToolPack import QtWidgets, QtCore
from LGA_UI_Style_ToolPack import Color, Metric, Style, apply_ui_font

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
    "path": (
        "Archivo donde se guarda tu eleccion, fuera del pack.\n"
        "Clic para mostrarlo en el explorador de archivos"
    ),
}


def _pretty(key):
    """`Show_in_Flow` -> `Show in Flow`."""
    return key.replace("_", " ")


def reveal_in_file_browser(path):
    """
    Muestra `path` en el Finder / Explorer, seleccionado si existe.

    El ini todavia puede no existir -recien se crea al primer Save-, asi que
    cuando no esta se abre la carpeta que lo va a contener en vez de no hacer
    nada: el usuario igual queria llegar ahi.
    """
    if not path:
        return False
    target = path if os.path.exists(path) else ""
    folder = os.path.dirname(path)
    if not target and not os.path.isdir(folder):
        return False
    try:
        if sys.platform == "win32":
            if target:
                # La coma pegada al path es la sintaxis de explorer, no un
                # error: con espacio despues de la coma abre Documentos.
                subprocess.Popen('explorer /select,"%s"' % target.replace("/", "\\"))
            else:
                os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", target] if target else ["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception:
        return False
    return True


class PathLink(QtWidgets.QLabel):
    """
    El path del ini, en texto plano, que se subraya al pasarle por encima.

    Empezo como rich text con un `<a>` y la senal `linkHovered`, y el
    subrayado quedaba enganchado: al entrar se reescribia el HTML, y
    reescribirlo mueve el ancla debajo del mouse, asi que la salida muchas
    veces no llegaba a emitirse. `enterEvent` y `leaveEvent` no dependen del
    contenido: son del widget.

    El widget se achica al ancho de su texto -por el size policy- para que el
    area sensible sea el path y no la franja entera del pie de la ventana.
    """

    HOJA = (
        "QLabel { color: %s; font-size: %dpx; text-decoration: %s; }"
    )

    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self._path = path
        self.setCursor(Qt.PointingHandCursor)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed
        )
        self._pintar(False)

    def _pintar(self, encima):
        self.setStyleSheet(
            self.HOJA
            % (
                Color.TEXT if encima else Color.TEXT_DIM,
                Metric.FORM_PATH_FONT_SIZE,
                "underline" if encima else "none",
            )
        )

    def enterEvent(self, event):
        self._pintar(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._pintar(False)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            reveal_in_file_browser(self._path)
        super().mouseReleaseEvent(event)


class EnabledPanel(QtWidgets.QWidget):
    """Grilla de checkboxes, una por herramienta, agrupada como el menu."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LGA ToolPack - Enable Tools")
        self.setToolTip(TOOLTIPS["window"])
        self.setStyleSheet(Style.FORM)
        self._checkboxes = {}
        self._scroll = None
        self._config_path = ""
        self._defaults = enabled_config.read_defaults()
        self._build_ui()
        # Despues de armar la ventana, para que alcance a los hijos que ya
        # existen. Sin esto la ventana se dibujaba con la fuente del host: en
        # Nuke sale varios puntos mas chica que el indicador del checkbox, y
        # el nombre de la tool se leia diminuto al lado de su propio cuadrito.
        apply_ui_font(self, Metric.FORM_FONT_SIZE)

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
        self._scroll = scroll
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
                # Aire entre el cuadrito y el nombre. Va por propiedad: la
                # hoja del pack no separa por default porque un checkbox sin
                # texto reserva esa separacion igual y queda descentrado.
                checkbox.setProperty("lgaLabeled", True)
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

        root.addWidget(self._build_path_label())
        root.addLayout(self._build_buttons())

    def _build_path_label(self):
        """
        El path de la config, en un solo color y clickeable.

        Antes salia por colorize_path, que es la paleta por nivel de carpeta:
        sirve para COMPARAR dos rutas -de donde a donde copia algo- y aca no
        hay nada que comparar, asi que el arcoiris solo pesa mas que el
        contenido de la ventana. Va como link porque para eso se muestra:
        para poder llegar al archivo.
        """
        self._config_path = enabled_config.get_user_path() or ""
        if not self._config_path:
            return QtWidgets.QLabel()
        label = PathLink(self._config_path)
        label.setToolTip(TOOLTIPS["path"])
        return label

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

    # Ancho minimo de apertura: dos columnas de nombres de tools con aire.
    MIN_WIDTH = 620

    def preferred_size(self):
        """
        Tamano de apertura: el que necesita el contenido, con techo de
        pantalla.

        Antes abria clavada en 620x620 y siempre mostraba scrollbar aunque
        faltaran veinte pixeles. El alto sale de medir el contenido del area
        scrolleable, no de estimarlo: agregar o sacar una tool del manifiesto
        cambia ese alto y un numero fijo se desactualiza al primer cambio.
        """
        if self._scroll is None:
            return self.MIN_WIDTH, 620

        content = self._scroll.widget()
        content_size = content.sizeHint()

        extra = self.height() - self._scroll.viewport().height()
        width = content_size.width() + self._scroll.frameWidth() * 2
        width += self.width() - self._scroll.viewport().width()
        # Piso de ancho: el sizeHint del contenido es el MINIMO en el que las
        # dos columnas entran, y a ese ancho los nombres quedan apretados
        # contra el borde del grupo.
        width = max(width, self.MIN_WIDTH)
        height = content_size.height() + self._scroll.frameWidth() * 2 + extra

        screen = QtWidgets.QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(width, int(available.width() * 0.9))
            height = min(height, int(available.height() * 0.9))
        return width, height

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
        panel_instance.show()
        # Despues del show(): antes de eso los layouts todavia no
        # calcularon nada y el sizeHint del contenido miente.
        panel_instance.resize(*panel_instance.preferred_size())
    else:
        panel_instance.raise_()
        panel_instance.activateWindow()


if __name__ == "__main__":
    main()
