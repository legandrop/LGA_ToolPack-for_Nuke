"""
_______________________________________

  LGA_MediaManager_settings v2.27 | Lega
  Ventana de ajustes del Media Manager

  v2.27: Se rehace contra el esquema nuevo del .ini. El destino de
         Copy to y la carpeta a escanear pasan a ser la misma cosa
         -una location- asi que hay una sola tabla, con Scan y Copy
         to como dos casillas de la misma fila. El atajo sale de su
         propio campo y no del '&' embebido en el nombre.
         El Folder scan depth se va: la carpeta del shot es ahora
         una ruta explicita, y es la primera fila de la tabla.
         Cada fila muestra a que carpeta REAL llega su ruta, que se
         resuelve en un worker: un comodin contra un servidor
         resuelto en el hilo principal cuelga la ventana.
         Suma tema y tamano de letra, que se aplican en vivo y se
         revierten con Cancel.
  v2.25: Cada destino ocupa una sola fila -nombre y ruta al lado,
         encabezado de columna una vez- con los campos alineados. El
         depth se maneja con un stepper de botones a los costados en
         vez del spinbox nativo, que iba de 20 px y se enfocaba en
         amarillo. Muestra la version de la herramienta, leida del
         header del script principal. Guarda de forma atomica en el
         .ini de la carpeta de datos del usuario y avisa por senal.

  v2.13: El look sale de LGA_UI_Style_ToolPack. Cada widget repetia
         su propio bloque de QToolTip inline —el mismo, seis veces—
         y la ventana iba mas clara que sus propios campos, con la
         jerarquia al reves.
  v2.12: El header decia LGA_mediaManager, el nombre de la
         herramienta y no el de este modulo. Se sigue la numeracion
         que traian los helpers del Media Manager.
_______________________________________

"""

import os
import re

from LGA_QtAdapter_ToolPack import QtWidgets, QtGui, QtCore
import LGA_UI_Style_ToolPack as UIStyle
import LGA_MediaManager_paths as paths
from LGA_MediaManager_config import (
    DEFAULT_APPEARANCE,
    DEFAULT_SHOT,
    format_ini,
    get_write_path,
    write_ini,
)
from LGA_MediaManager_logging import debug_print
from LGA_MediaManager_utils import PathResolveWorker, tinted_icon

QWidget = QtWidgets.QWidget
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QPushButton = QtWidgets.QPushButton
QCheckBox = QtWidgets.QCheckBox
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QScrollArea = QtWidgets.QScrollArea
QFrame = QtWidgets.QFrame
QMessageBox = QtWidgets.QMessageBox
Qt = QtCore.Qt
Signal = QtCore.Signal
QTimer = QtCore.QTimer
QThreadPool = QtCore.QThreadPool


# --------------------------------------------------------------------------
#                              Medidas
# --------------------------------------------------------------------------
# Las columnas de la tabla. Cada fila y el encabezado usan EXACTAMENTE esta
# lista: si no salieran del mismo lugar se desalinean en cuanto una cambia.
# (ancho fijo o None, factor de estiramiento, ancho minimo)
COL_GRIP = (34, 0, 34)
COL_NAME = (None, 9, 150)
COL_PATH = (None, 14, 200)
COL_REAL = (None, 8, 120)
COL_SCAN = (76, 0, 76)
COL_COPY = (90, 0, 90)
COL_KEY = (170, 0, 170)
COL_TRASH = (50, 0, 50)
COLUMNS = (COL_GRIP, COL_NAME, COL_PATH, COL_REAL, COL_SCAN, COL_COPY,
           COL_KEY, COL_TRASH)

WINDOW_MIN_WIDTH = 1180
WINDOW_MIN_HEIGHT = 560
TABLE_MAX_HEIGHT = 420

# Los altos se DERIVAN del tamano de letra en vez de ser constantes: sin eso,
# subir la letra la corta contra el borde de la fila.
ROW_EXTRA = 31  # 44 con letra 13
HEAD_EXTRA = 29  # 42 con letra 13

# Las cinco letras que ya usan los botones de la barra principal. Si una
# location toma una de estas, Qt no dispara NINGUNO de los dos y tira un
# warning de "ambiguous shortcut", asi que se rechazan.
RESERVED_SHORTCUTS = ("G", "R", "L", "C", "D")


# Los tooltips van en castellano y salen de aca, no hardcodeados en el widget,
# para que la migracion a bilingue sea un cambio de datos.
TOOLTIPS = {
    "shot_enabled": (
        "Sin shot folder no hay adentro ni afuera: Outside pasa a\n"
        "medirse contra las scan locations"
    ),
    "shot_path": "Carpeta del shot, relativa al .nk. Define que esta adentro",
    "name": "Nombre que aparece en el menu Copy to",
    "path": "Carpeta, relativa al .nk. Acepta * como comodin",
    "scan": "Buscar media adentro de esta carpeta",
    "scan_inherited": "Ya la cubre otra location que se escanea entera",
    "copy_to": "Ofrecer esta carpeta en el menu Copy to",
    "shortcut": "Letra del atajo, se dispara con Alt + esa letra",
    "remove": "Quita esta location",
    "add": "Agrega una location",
    "grip": "Arrastra para cambiar el orden del menu Copy to",
    "theme": "Paleta de colores de las dos ventanas",
    "font_minus": "Una letra mas chica",
    "font_plus": "Una letra mas grande",
    # Los de la columna "Resolves to" tambien son tooltips y van por el dict,
    # no escritos adentro de la funcion que los arma.
    "real_empty": "Sin ruta",
    "real_invalid": "La ruta sube mas alto que la raiz",
    "real_none": "Ninguna carpeta coincide",
    "real_one": "Resuelve a %s",
    "real_many": "Coinciden:",
}

# Lo que la columna "Resolves to" dice en cada caso. Estan juntos para que la
# fila del shot y las de locations digan lo mismo.
REAL_EMPTY = "—"
REAL_INVALID = "invalid path"
REAL_ABSOLUTE = "absolute"
REAL_NOT_FOUND = "not found"


def get_tool_version():
    """
    Version de la herramienta, leida del header de LGA_mediaManager.py.

    Se lee el archivo en vez de importarlo para no depender del orden de
    importacion: este modulo lo carga el script principal. Si el header
    cambia de formato se devuelve vacio y la ventana no muestra version,
    que es mejor que mostrar una equivocada.
    """
    try:
        main_script = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "LGA_mediaManager.py"
        )
        with open(main_script, "r", encoding="utf-8") as handle:
            header = handle.read(600)
        match = re.search(r"LGA_mediaManager\s+v(\d+\.\d+)\s*\|", header)
        return match.group(1) if match else ""
    except Exception:
        return ""


def _apply_column(widget, columna):
    """Le da a un widget el ancho de su columna."""
    fijo, _estira, minimo = columna
    if fijo is not None:
        widget.setFixedWidth(fijo)
    else:
        widget.setMinimumWidth(minimo)


def _add_column(layout, widget, columna):
    _apply_column(widget, columna)
    layout.addWidget(widget, columna[1])


def real_text(resolution):
    """El texto de la columna 'Resolves to' para un resultado."""
    if resolution is None:
        return REAL_EMPTY
    if resolution.kind == paths.EMPTY:
        return REAL_EMPTY
    if resolution.kind == paths.INVALID:
        return REAL_INVALID
    if resolution.kind == paths.ABSOLUTE:
        return REAL_ABSOLUTE
    if not resolution.folders:
        return REAL_NOT_FOUND
    if len(resolution.folders) == 1:
        return os.path.basename(resolution.folders[0].rstrip("/")) or resolution.folders[0]
    return "%d folders" % len(resolution.folders)


def real_tooltip(resolution):
    """El detalle, que en la columna no entra."""
    if resolution is None or resolution.kind == paths.EMPTY:
        return TOOLTIPS["real_empty"]
    if resolution.kind == paths.INVALID:
        return TOOLTIPS["real_invalid"]
    if not resolution.folders:
        return TOOLTIPS["real_none"]
    if len(resolution.folders) == 1:
        return TOOLTIPS["real_one"] % resolution.folders[0]
    # La ruta COMPLETA de cada match y no solo el nombre: con dos carpetas
    # homonimas en ramas distintas, el nombre solo no las diferencia.
    detalle = "\n".join(resolution.folders[:12])
    if len(resolution.folders) > 12:
        detalle += "\n..."
    return TOOLTIPS["real_many"] + "\n" + detalle


def real_is_problem(resolution):
    """Si el resultado hay que mostrarlo en rojo."""
    if resolution is None:
        return False
    return resolution.kind == paths.INVALID or (
        resolution.kind in (paths.RELATIVE, paths.ABSOLUTE) and not resolution.folders
    )


class GripLabel(QLabel):
    """
    El agarre para arrastrar una fila.

    El arrastre se maneja aca y no con el drag&drop de Qt: la lista es un
    QVBoxLayout de widgets propios, asi que mover una fila es moverla de
    posicion en el layout, y armar un QDrag para eso es dar toda la vuelta.
    """

    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.setCursor(Qt.OpenHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.setToolTip(TOOLTIPS["grip"])
        self._activo = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._activo = True
            self.setCursor(Qt.ClosedHandCursor)
            self.row.drag_started.emit(self.row)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._activo:
            # La posicion global, porque el cursor se va del propio grip en
            # cuanto la fila se mueve.
            self.row.drag_moved.emit(self.row, self._global_y(event))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._activo:
            self._activo = False
            self.setCursor(Qt.OpenHandCursor)
            self.row.drag_finished.emit(self.row)
        super().mouseReleaseEvent(event)

    def _global_y(self, event):
        # Qt5 tiene globalY(); Qt6 lo saco a favor de globalPosition().
        try:
            return int(event.globalPosition().y())
        except AttributeError:
            return event.globalY()


class ShortcutField(QLineEdit):
    """Un solo caracter, en mayuscula, y solo letra o numero."""

    def __init__(self, letra, parent=None):
        super().__init__(letra or "", parent)
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(34)
        self.textChanged.connect(self._limpiar)

    def _limpiar(self, texto):
        limpio = re.sub(r"[^A-Za-z0-9]", "", texto).upper()
        if limpio != texto:
            self.blockSignals(True)
            self.setText(limpio)
            self.blockSignals(False)


class LocationRow(QWidget):
    """
    Una fila de la tabla: nombre, ruta, a que resuelve, Scan, Copy to, atajo.

    La fila del shot folder es la misma clase en modo `shot`: comparte grilla,
    alto y fondo con las demas para que se lean como lo mismo, y se diferencia
    por lo que NO tiene -grip, Copy to, atajo y papelera- y porque su etiqueta
    va en bold.
    """

    changed = Signal()
    path_changed = Signal(object)
    remove_requested = Signal(object)
    drag_started = Signal(object)
    drag_moved = Signal(object, int)
    drag_finished = Signal(object)

    # Un numero propio y creciente por fila. No se usa id(): CPython reusa el
    # id de un objeto liberado, asi que una fila nueva podia recibir el
    # "Resolves to" de la que el usuario acababa de borrar.
    _next_uid = 0

    def __init__(self, data, shot=False, parent=None):
        super().__init__(parent)
        LocationRow._next_uid += 1
        self.uid = LocationRow._next_uid
        self.shot = shot
        self.data = dict(data)
        self._resolution = None
        self._small_css = ""
        # Los campos con un problema de validacion, para pintarlos de rojo.
        self.field_errors = set()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        # --- primera columna: grip, o el encendido del shot ----------------
        if shot:
            # El checkbox va en la columna del NOMBRE, donde las otras filas
            # tienen el icono de carpeta, no aca: asi la primera cosa
            # clickeable de cada fila cae siempre en la misma vertical.
            hueco = QLabel("")
            _add_column(layout, hueco, COL_GRIP)
            self.grip = None
        else:
            self.grip = GripLabel(self)
            _add_column(layout, self.grip, COL_GRIP)

        # --- nombre --------------------------------------------------------
        nombre_caja = QWidget(self)
        nombre_layout = QHBoxLayout(nombre_caja)
        nombre_layout.setContentsMargins(0, 0, 0, 0)
        nombre_layout.setSpacing(9)

        # La ranura mide lo que el icono (17) para que "Shot folder" arranque
        # exactamente donde arrancan los nombres de las locations. El checkbox
        # es de 19 y desborda 1 px por lado, que con el gap de 9 no toca nada.
        if shot:
            self.enabled_check = QCheckBox("")
            self.enabled_check.setChecked(bool(self.data.get("enabled", True)))
            self.enabled_check.setToolTip(TOOLTIPS["shot_enabled"])
            self.enabled_check.stateChanged.connect(self._shot_toggled)
            self.ranura = self.enabled_check
            self.name_edit = None
            self.name_label = QLabel("Shot folder")
        else:
            self.enabled_check = None
            self.ranura = QLabel("")
            self.name_label = None
            self.name_edit = QLineEdit(self.data.get("name", ""))
            self.name_edit.setPlaceholderText("Name")
            self.name_edit.setToolTip(TOOLTIPS["name"])
            self.name_edit.textChanged.connect(lambda _t: self.changed.emit())

        if shot:
            # La ranura mide lo que el icono y el checkbox desborda 1 px por
            # lado: con el ancho fijo puesto sobre el propio checkbox, Qt le
            # recortaba el indicador.
            ranura_caja = QWidget(self)
            ranura_layout = QHBoxLayout(ranura_caja)
            ranura_layout.setContentsMargins(0, 0, 0, 0)
            ranura_layout.addWidget(self.ranura, 0, Qt.AlignCenter)
            ranura_caja.setFixedWidth(17)
            nombre_layout.addWidget(ranura_caja)
        else:
            self.ranura.setFixedWidth(17)
            nombre_layout.addWidget(self.ranura)
        nombre_layout.addWidget(self.name_label or self.name_edit, 1)

        _add_column(layout, nombre_caja, COL_NAME)

        # --- ruta ----------------------------------------------------------
        self.path_edit = QLineEdit(self.data.get("path", ""))
        self.path_edit.setPlaceholderText("../*folder*")
        self.path_edit.setToolTip(
            TOOLTIPS["shot_path"] if shot else TOOLTIPS["path"]
        )
        # editingFinished y NO textChanged: resolver la ruta contra disco toca
        # IO, y recalcular las inclusiones en cada tecla ademas redibuja la
        # fila mientras se escribe y el foco salta.
        self.path_edit.editingFinished.connect(lambda: self.path_changed.emit(self))
        _add_column(layout, self.path_edit, COL_PATH)

        # --- a que resuelve -------------------------------------------------
        self.real_label = QLabel(REAL_EMPTY)
        self.real_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        _add_column(layout, self.real_label, COL_REAL)

        # --- Scan ------------------------------------------------------------
        scan_caja = QWidget(self)
        scan_layout = QHBoxLayout(scan_caja)
        scan_layout.setContentsMargins(0, 0, 0, 0)
        self.scan_check = QCheckBox("")
        if shot:
            # No es una location que se prenda aparte: el shot se escanea
            # siempre que este activo, y se apaga con la fila.
            self.scan_check.setChecked(True)
            self.scan_check.setEnabled(False)
        else:
            self.scan_check.setChecked(bool(self.data.get("scan", True)))
            self.scan_check.setToolTip(TOOLTIPS["scan"])
            self.scan_check.stateChanged.connect(self._scan_toggled)
        scan_layout.addWidget(self.scan_check, 0, Qt.AlignCenter)
        _add_column(layout, scan_caja, COL_SCAN)

        # --- Copy to ---------------------------------------------------------
        copy_caja = QWidget(self)
        copy_layout = QHBoxLayout(copy_caja)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        if shot:
            self.copy_check = None
            copy_layout.addWidget(QLabel(""))
        else:
            self.copy_check = QCheckBox("")
            self.copy_check.setChecked(bool(self.data.get("copy_to", False)))
            self.copy_check.setToolTip(TOOLTIPS["copy_to"])
            self.copy_check.stateChanged.connect(self._copy_toggled)
            copy_layout.addWidget(self.copy_check, 0, Qt.AlignCenter)
        _add_column(layout, copy_caja, COL_COPY)

        # --- atajo ------------------------------------------------------------
        key_caja = QWidget(self)
        key_layout = QHBoxLayout(key_caja)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(6)
        if shot:
            self.alt_label = None
            self.plus_label = None
            self.key_edit = None
            self.dash_label = None
            key_layout.addWidget(QLabel(""))
        else:
            self.alt_label = QLabel("Alt")
            self.alt_label.setProperty("lgaKey", True)
            self.plus_label = QLabel("+")
            self.key_edit = ShortcutField(self.data.get("shortcut", ""))
            self.key_edit.setToolTip(TOOLTIPS["shortcut"])
            self.key_edit.textChanged.connect(lambda _t: self.changed.emit())
            self.dash_label = QLabel("—")
            key_layout.addWidget(self.alt_label)
            key_layout.addWidget(self.plus_label)
            key_layout.addWidget(self.key_edit)
            key_layout.addWidget(self.dash_label)
            key_layout.addStretch()
        _add_column(layout, key_caja, COL_KEY)

        # --- papelera ----------------------------------------------------------
        trash_caja = QWidget(self)
        trash_layout = QHBoxLayout(trash_caja)
        trash_layout.setContentsMargins(0, 0, 0, 0)
        if shot:
            self.trash_button = None
            trash_layout.addWidget(QLabel(""))
        else:
            self.trash_button = QPushButton("")
            self.trash_button.setFixedSize(30, 30)
            self.trash_button.setToolTip(TOOLTIPS["remove"])
            self.trash_button.setFocusPolicy(Qt.NoFocus)
            self.trash_button.clicked.connect(
                lambda: self.remove_requested.emit(self)
            )
            trash_layout.addWidget(self.trash_button, 0, Qt.AlignCenter)
        _add_column(layout, trash_caja, COL_TRASH)

        if shot:
            self._shot_toggled()
        else:
            self._copy_toggled()

    # ------------------------------------------------------------- estado ---
    def _shot_toggled(self, *_):
        prendido = self.enabled_check.isChecked()
        self.path_edit.setEnabled(prendido)
        self.scan_check.setChecked(prendido)
        # Nombre, ruta y carpeta resuelta bajan de intensidad. La carpeta
        # resuelta NO se borra: apagada sigue diciendo a que apuntaba, que es
        # lo que hace falta para decidir si volver a prenderla.
        for widget in (self.name_label, self.path_edit, self.real_label):
            if widget is not None:
                efecto = QtWidgets.QGraphicsOpacityEffect(widget)
                efecto.setOpacity(1.0 if prendido else 0.45)
                widget.setGraphicsEffect(efecto)
        # La carpeta resuelta NO se borra al apagar: apagada sigue diciendo a
        # que apuntaba, que es lo que hace falta para decidir si reactivarla.
        self.changed.emit()

    def _scan_toggled(self, *_):
        self.data["scan"] = self.scan_check.isChecked()
        self.changed.emit()

    def _copy_toggled(self, *_):
        prendido = bool(self.copy_check and self.copy_check.isChecked())
        # La letra NO se borra del modelo al apagar Copy to: si el usuario lo
        # vuelve a prender, vuelve su letra.
        for widget in (self.alt_label, self.plus_label, self.key_edit):
            if widget is not None:
                widget.setVisible(prendido)
        if self.dash_label is not None:
            self.dash_label.setVisible(not prendido)
        self.changed.emit()

    def set_scan_inherited(self, padre):
        """
        La cubre otra location que ya se escanea entera.

        Queda TILDADA y deshabilitada, no destildada: la carpeta se escanea,
        solo que no es esta fila la que lo decide.
        """
        if self.shot:
            return
        if padre is None:
            self.scan_check.setEnabled(True)
            self.scan_check.blockSignals(True)
            self.scan_check.setChecked(bool(self.data.get("scan", True)))
            self.scan_check.blockSignals(False)
            self.scan_check.setToolTip(TOOLTIPS["scan"])
            return
        self.scan_check.blockSignals(True)
        self.scan_check.setChecked(True)
        self.scan_check.blockSignals(False)
        self.scan_check.setEnabled(False)
        nombre = padre.get("name") or padre.get("path") or ""
        self.scan_check.setToolTip("%s\n(%s)" % (TOOLTIPS["scan_inherited"], nombre))

    def set_resolution(self, resolution, UI):
        self._resolution = resolution
        self.real_label.setText(real_text(resolution))
        self.real_label.setToolTip(real_tooltip(resolution))
        color = UI.Color.ERROR_TEXT if real_is_problem(resolution) else UI.Color.TEXT_DIM
        self.real_label.setStyleSheet(
            "color: %s; background: transparent; %s" % (color, self._small_css)
        )

    def resolution(self):
        return self._resolution

    def set_field_errors(self, campos, UI, font_size):
        """Los campos que hay que pintar de rojo. Repinta solo si cambiaron."""
        campos = set(campos)
        if campos == self.field_errors:
            return
        self.field_errors = campos
        self.apply_theme(UI, font_size)

    # -------------------------------------------------------------- datos ---
    def path(self):
        return self.path_edit.text().strip()

    def to_dict(self):
        if self.shot:
            return {
                "enabled": self.enabled_check.isChecked(),
                "path": self.path() or DEFAULT_SHOT["path"],
            }
        return {
            "name": self.name_edit.text().strip(),
            "path": self.path(),
            # Se guarda SIEMPRE el scan explicito, nunca el efectivo: si se
            # guardara el efectivo, al borrar la location padre las hijas
            # quedarian tildadas de una forma que el usuario nunca eligio.
            "scan": bool(self.data.get("scan", self.scan_check.isChecked())),
            "copy_to": bool(self.copy_check.isChecked()),
            "shortcut": self.key_edit.text().strip().upper(),
        }

    # -------------------------------------------------------------- estilo ---
    def apply_theme(self, UI, font_size):
        alto = font_size + ROW_EXTRA
        self.setFixedHeight(alto)
        self.setStyleSheet(UI.Style.FORM + UI.Style.CHECKBOX)

        # El path va un punto mas grande que el resto de la tabla, y con menos
        # padding vertical: la mono ya trae una caja de linea mas alta.
        self.path_edit.setStyleSheet(
            "QLineEdit { color: %s; font-family: '%s'; font-size: %dpx;"
            " padding: 4px 8px; }"
            % (UI.Color.PATH_FIELD, UIStyle.mono_family() or UIStyle.font_family(),
               font_size + UIStyle.Metric.PATH_FONT_OFFSET)
        )
        chico = "font-size: %dpx;" % max(9, int(round(font_size - 0.5)))
        self._small_css = chico
        self.set_resolution(self._resolution, UI)
        if self.name_edit is not None:
            self.name_edit.setStyleSheet("QLineEdit { %s }" % chico)
        if self.name_label is not None:
            self.name_label.setStyleSheet(
                "color: %s; font-weight: 600; %s" % (UI.Color.TEXT_STRONG, chico)
            )
        if self.grip is not None:
            self.grip.setPixmap(
                tinted_icon("grip-vertical", UI.Color.TEXT_DIM, 18).pixmap(18, 18)
            )
        if self.ranura is not None and not self.shot:
            self.ranura.setPixmap(
                tinted_icon("folder", UI.Color.TEXT_DIM, 17).pixmap(17, 17)
            )
        if self.trash_button is not None:
            self.trash_button.setIcon(tinted_icon("trash-2", UI.Color.TEXT_DIM, 17))
            self.trash_button.setStyleSheet(UI.Style.BTN_ICON)
        if self.alt_label is not None:
            self.alt_label.setStyleSheet(
                "background-color: %s; border: 1px solid %s; border-radius: %dpx;"
                " padding: 0 9px; color: %s; font-weight: 600;"
                % (UI.Color.SURFACE_RAISED, UI.Color.BORDER_STRONG,
                   UIStyle.Metric.RADIUS, UI.Color.TEXT)
            )
            self.plus_label.setStyleSheet("color: %s;" % UI.Color.TEXT_DIM)
            self.dash_label.setStyleSheet(
                "color: %s; padding-left: 12px;" % UI.Color.TEXT_DIM
            )
        if self.key_edit is not None:
            # Borde de acento SIEMPRE y no solo al foco: es el unico campo de
            # la fila que espera una sola tecla, y sin marcarlo no se ve que
            # sea editable.
            self.key_edit.setStyleSheet(
                "QLineEdit { border: 1px solid %s; border-radius: %dpx;"
                " background-color: %s; color: %s; }"
                "QLineEdit:focus { background-color: %s; }"
                % (UI.Color.ACCENT_HOVER, UIStyle.Metric.RADIUS,
                   UI.Color.SURFACE, UI.Color.TEXT_STRONG, UI.Color.ACCENT)
            )

        # El rojo va al final para que le gane a la hoja del campo, que ya
        # quedo escrita arriba. Se reconstruye entero en cada pasada, asi que
        # sacar el error tambien saca el borde.
        for campo in self.field_errors:
            widget = {"name": self.name_edit, "path": self.path_edit,
                      "shortcut": self.key_edit}.get(campo)
            if widget is not None:
                widget.setStyleSheet(
                    widget.styleSheet()
                    + " QLineEdit { border: 1px solid %s; }" % UI.Color.ERROR_TEXT
                )


class FontSizeField(QLineEdit):
    """
    El campo del stepper del tamano de letra.

    Es un QLineEdit y no un QSpinBox por lo mismo que ya estaba resuelto en la
    version anterior: el spinbox nativo mide 20 px contra los 30 de un campo,
    asi que sus flechas quedan de 7 px, y al enfocarlo macOS lo pinta con su
    anillo amarillo mientras el resto del pack se pone violeta.
    """

    value_changed = Signal(int)

    def __init__(self, valor, parent=None):
        super().__init__(str(valor), parent)
        self.setValidator(
            QtGui.QIntValidator(UIStyle.Metric.TABLE_FONT_SIZE_MIN,
                                UIStyle.Metric.TABLE_FONT_SIZE_MAX, self)
        )
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(56)
        self.editingFinished.connect(self._commit)

    def _commit(self):
        # El texto se reescribe con el valor ACOTADO: sin esto el campo
        # quedaba en 200 mientras se aplicaba y se guardaba 20.
        acotado = self.value()
        if self.text() != str(acotado):
            self.setText(str(acotado))
        self.value_changed.emit(acotado)

    def value(self):
        # Se acota aca y no solo en step(): QIntValidator da por intermedio
        # cualquier numero mas corto que el minimo, asi que deja tipear un 0.
        try:
            escrito = int(self.text())
        except ValueError:
            return UIStyle.Metric.TABLE_FONT_SIZE
        return max(UIStyle.Metric.TABLE_FONT_SIZE_MIN,
                   min(UIStyle.Metric.TABLE_FONT_SIZE_MAX, escrito))

    def step(self, delta):
        nuevo = max(UIStyle.Metric.TABLE_FONT_SIZE_MIN,
                    min(UIStyle.Metric.TABLE_FONT_SIZE_MAX, self.value() + delta))
        self.setText(str(nuevo))
        self.value_changed.emit(nuevo)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.step(1)
        elif event.key() == Qt.Key_Down:
            self.step(-1)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            self.step(1 if event.angleDelta().y() > 0 else -1)
        else:
            event.ignore()


class SettingsWindow(QWidget):
    """La ventana de ajustes del Media Manager."""

    # Al guardar, para que la ventana principal relea el .ini y rehaga el
    # menu Copy to: sin esto, una location agregada aca no aparece hasta
    # reabrir la herramienta.
    settings_saved = Signal()
    # Tema y tamano de letra mientras la ventana esta abierta, para poder
    # verlos sobre la tabla de atras. Cancel manda los guardados de vuelta.
    appearance_previewed = Signal(object)

    def __init__(self, settings, nk_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Media Manager Settings")
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self.setMinimumHeight(WINDOW_MIN_HEIGHT)

        self.nk_dir = nk_dir or ""
        self.settings = settings or {}
        self.load_error = self.settings.get("load_error") or ""
        # La apariencia guardada, para poder revertir con Cancel.
        self.saved_appearance = dict(
            self.settings.get("appearance") or DEFAULT_APPEARANCE
        )
        self.appearance = dict(self.saved_appearance)
        self.UI = UIStyle.theme(self.appearance.get("theme"))

        self.rows = []
        self._worker = None
        self._dragging = None
        self._resolve_timer = QTimer(self)
        self._resolve_timer.setSingleShot(True)
        self._resolve_timer.setInterval(150)
        self._resolve_timer.timeout.connect(self._resolve_now)

        self._build()
        self._load_rows()
        self.apply_appearance()
        self.refresh()

        # El alto sale de medir el contenido: con un tamano fijo, la tabla
        # abria cortada o sobraba media ventana vacia segun cuantas
        # locations tuviera el usuario.
        self.adjustSize()

        if self.load_error:
            # El .ini existe y no se pudo leer, asi que lo que se esta
            # mostrando son los valores de fabrica y NO la configuracion del
            # usuario. Guardar encima la destruye.
            QMessageBox.warning(
                self,
                "Media Manager",
                "The settings file could not be read, so these are the "
                "factory defaults and not your configuration.\n\n%s\n\n"
                "Saving now would overwrite your settings file."
                % self.load_error,
            )

    # --------------------------------------------------------------- armado --
    def _build(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(26, 20, 26, 22)
        raiz.setSpacing(0)

        # --- encabezado ------------------------------------------------------
        cabeza = QHBoxLayout()
        titulos = QVBoxLayout()
        self.title_label = QLabel("Scan locations")
        self.subtitle_label = QLabel(
            "Define which folders will be scanned for media.\n"
            "Paths are relative to the current .nk file unless absolute."
        )
        titulos.addWidget(self.title_label)
        titulos.addWidget(self.subtitle_label)
        cabeza.addLayout(titulos, 1)
        self.card_wildcard = self._info_card(
            "Wildcard * matches any folder name.\n"
            "Example: ../*assets* matches 0_assets, _assets, my_assets, etc."
        )
        cabeza.addWidget(self.card_wildcard)
        raiz.addLayout(cabeza)
        raiz.addSpacing(20)

        # --- encabezado de la tabla ------------------------------------------
        self.head_row = QWidget(self)
        head = QHBoxLayout(self.head_row)
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(9)
        self.head_labels = []
        for texto, columna in (
            ("", COL_GRIP), ("Name", COL_NAME), ("Path", COL_PATH),
            ("Resolves to", COL_REAL), ("Scan", COL_SCAN),
            ("Copy to", COL_COPY), ("Copy Shortcut", COL_KEY), ("", COL_TRASH),
        ):
            etiqueta = QLabel(texto)
            if columna in (COL_SCAN, COL_COPY):
                etiqueta.setAlignment(Qt.AlignCenter)
            _add_column(head, etiqueta, columna)
            self.head_labels.append(etiqueta)
        # El encabezado vive AFUERA del area scrolleable, asi que cuando
        # aparece la barra vertical las columnas elasticas de las filas se
        # corren respecto de el. Se le reserva ese ancho siempre.
        hueco_scroll = QLabel("")
        hueco_scroll.setFixedWidth(UIStyle.Metric.SCROLLBAR_WIDTH)
        head.addWidget(hueco_scroll)
        raiz.addWidget(self.head_row)

        # --- filas -------------------------------------------------------------
        self.rows_host = QWidget(self)
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.addStretch()

        self.scroll = QScrollArea(self)
        self.scroll.setWidget(self.rows_host)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setMaximumHeight(TABLE_MAX_HEIGHT)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Siempre visible, aunque sobre lugar: el encabezado esta afuera del
        # area y le reserva ese ancho fijo, asi que una barra que aparece y
        # desaparece corre las columnas de las filas contra las del titulo.
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        raiz.addWidget(self.scroll)

        # --- agregar + tarjeta ---------------------------------------------------
        bajo = QHBoxLayout()
        bajo.setSpacing(18)
        self.add_button = QPushButton("  Add location")
        self.add_button.setFixedHeight(44)
        self.add_button.setToolTip(TOOLTIPS["add"])
        self.add_button.clicked.connect(self._add_empty_row)
        bajo.addWidget(self.add_button)
        self.card_included = self._info_card(
            "Locations included by another scan path remain checked but "
            "disabled.\nDisable or remove the parent path to edit them."
        )
        bajo.addWidget(self.card_included)
        bajo.addStretch()
        raiz.addSpacing(14)
        raiz.addLayout(bajo)

        # --- apariencia -----------------------------------------------------------
        raiz.addSpacing(20)
        self.appearance_sep = self._separator()
        raiz.addWidget(self.appearance_sep)
        raiz.addSpacing(16)

        apariencia = QHBoxLayout()
        apariencia.setSpacing(34)

        tema_caja = QHBoxLayout()
        tema_caja.setSpacing(10)
        self.theme_label = QLabel("Theme")
        tema_caja.addWidget(self.theme_label)
        self.theme_buttons = {}
        for theme_id in UIStyle.theme_ids():
            spec = UIStyle.get_theme(theme_id)
            boton = QPushButton(spec["label"])
            boton.setFixedHeight(UIStyle.Metric.BUTTON_HEIGHT)
            boton.setToolTip(TOOLTIPS["theme"])
            boton.setFocusPolicy(Qt.NoFocus)
            boton.clicked.connect(lambda _c=False, t=theme_id: self._pick_theme(t))
            tema_caja.addWidget(boton)
            self.theme_buttons[theme_id] = boton
        apariencia.addLayout(tema_caja)

        fuente_caja = QHBoxLayout()
        fuente_caja.setSpacing(8)
        self.font_label = QLabel("Table font size")
        fuente_caja.addWidget(self.font_label)
        self.font_minus = QPushButton("-")
        self.font_plus = QPushButton("+")
        self.font_field = FontSizeField(
            self.appearance.get("table_font_size", UIStyle.Metric.TABLE_FONT_SIZE)
        )
        self.font_field.value_changed.connect(self._pick_font_size)
        for boton, delta, tip in ((self.font_minus, -1, "font_minus"),
                                  (self.font_plus, 1, "font_plus")):
            boton.setFixedSize(UIStyle.Metric.CLOSE_BUTTON_SIZE,
                               UIStyle.Metric.CLOSE_BUTTON_SIZE)
            boton.setFocusPolicy(Qt.NoFocus)
            boton.setToolTip(TOOLTIPS[tip])
            boton.clicked.connect(lambda _c=False, d=delta: self.font_field.step(d))
        fuente_caja.addWidget(self.font_minus)
        fuente_caja.addWidget(self.font_field)
        fuente_caja.addWidget(self.font_plus)
        apariencia.addLayout(fuente_caja)
        apariencia.addStretch()
        raiz.addLayout(apariencia)

        # --- pie ------------------------------------------------------------------
        raiz.addSpacing(20)
        self.footer_sep = self._separator()
        raiz.addWidget(self.footer_sep)
        raiz.addSpacing(16)

        pie = QHBoxLayout()
        version = get_tool_version()
        self.version_label = QLabel(
            "Media Manager v%s  ·  Developed by Lega" % version
            if version
            else "Media Manager  ·  Developed by Lega"
        )
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.clicked.connect(self._cancel)
        self.save_button = QPushButton("Save Settings")
        self.save_button.setFixedHeight(40)
        self.save_button.clicked.connect(self.save)
        pie.addWidget(self.version_label)
        pie.addStretch()
        pie.addWidget(self.cancel_button)
        pie.addWidget(self.save_button)
        raiz.addLayout(pie)

    def _separator(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFixedHeight(1)
        return linea

    def _info_card(self, texto):
        tarjeta = QWidget(self)
        layout = QHBoxLayout(tarjeta)
        layout.setContentsMargins(15, 13, 15, 13)
        layout.setSpacing(12)
        icono = QLabel("")
        icono.setFixedSize(20, 20)
        icono.setProperty("lgaCardIcon", True)
        cuerpo = QLabel(texto)
        cuerpo.setWordWrap(True)
        layout.addWidget(icono, 0, Qt.AlignTop)
        layout.addWidget(cuerpo, 1)
        tarjeta.setFixedWidth(360)
        tarjeta.icono = icono
        tarjeta.cuerpo = cuerpo
        return tarjeta

    # ---------------------------------------------------------------- filas --
    def _load_rows(self):
        shot = dict(self.settings.get("shot") or DEFAULT_SHOT)
        self.shot_row = LocationRow(shot, shot=True, parent=self.rows_host)
        self.shot_row.changed.connect(self.refresh)
        self.shot_row.path_changed.connect(self._path_edited)
        self.rows_layout.insertWidget(0, self.shot_row)

        for location in self.settings.get("locations") or ():
            self._add_row(location)

    def _add_row(self, location):
        fila = LocationRow(location, shot=False, parent=self.rows_host)
        fila.changed.connect(self.refresh)
        fila.path_changed.connect(self._path_edited)
        fila.remove_requested.connect(self._remove_row)
        fila.drag_started.connect(self._drag_started)
        fila.drag_moved.connect(self._drag_moved)
        fila.drag_finished.connect(self._drag_finished)
        # -1 es el stretch final; las filas van antes.
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, fila)
        self.rows.append(fila)
        return fila

    def _add_empty_row(self):
        fila = self._add_row(
            {"name": "", "path": "", "scan": True, "copy_to": False, "shortcut": ""}
        )
        fila.apply_theme(self.UI, self.font_size())
        fila.name_edit.setFocus()
        self._fit_table()
        self.refresh()

    def _remove_row(self, fila):
        if fila not in self.rows:
            return
        nombre = fila.name_edit.text().strip() or fila.path() or "this location"
        respuesta = QMessageBox.question(
            self, "Media Manager",
            "Remove %s?" % nombre,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        self.rows.remove(fila)
        self.rows_layout.removeWidget(fila)
        fila.setParent(None)
        fila.deleteLater()
        self._fit_table()
        self.refresh()

    # -------------------------------------------------------------- arrastre --
    def _drag_started(self, fila):
        self._dragging = fila
        fila.setStyleSheet(fila.styleSheet() + "QWidget { color: %s; }"
                           % self.UI.Color.TEXT_DIM)

    def _drag_moved(self, fila, global_y):
        if self._dragging is not fila or len(self.rows) < 2:
            return
        actual = self.rows.index(fila)
        # Cuantas filas quedan ARRIBA del cursor: ese es el lugar donde cae.
        destino = 0
        for otra in self.rows:
            if otra is fila:
                continue
            if global_y > otra.mapToGlobal(otra.rect().center()).y():
                destino += 1
        if destino == actual:
            return
        self.rows.pop(actual)
        self.rows.insert(destino, fila)
        self.rows_layout.removeWidget(fila)
        # +1 porque la fila del shot va siempre primera y no esta en self.rows.
        self.rows_layout.insertWidget(destino + 1, fila)

    def _drag_finished(self, fila):
        self._dragging = None
        fila.apply_theme(self.UI, self.font_size())
        self.refresh()

    # ------------------------------------------------------------ apariencia --
    def font_size(self):
        return self.font_field.value() if hasattr(self, "font_field") else \
            UIStyle.Metric.TABLE_FONT_SIZE

    def _pick_theme(self, theme_id):
        self.appearance["theme"] = theme_id
        self.UI = UIStyle.theme(theme_id)
        self.apply_appearance()
        self.appearance_previewed.emit(dict(self.appearance))

    def _pick_font_size(self, valor):
        self.appearance["table_font_size"] = valor
        self.apply_appearance()
        self.appearance_previewed.emit(dict(self.appearance))

    def apply_appearance(self):
        """Repinta la ventana entera con el tema y el tamano elegidos."""
        UI = self.UI
        fs = self.font_size()
        self.appearance["table_font_size"] = fs

        self.setStyleSheet(
            UI.Style.WINDOW + UI.Style.FORM + UI.Style.TOOLTIP + UI.Style.SCROLLBAR
        )
        self.title_label.setStyleSheet(
            "color: %s; font-size: 27px; font-weight: 700;" % UI.Color.TEXT_STRONG
        )
        self.subtitle_label.setStyleSheet(
            "color: %s; font-size: 13px;" % UI.Color.TEXT
        )
        cabecera = (
            "color: %s; background-color: %s; font-size: 12px; font-weight: 600;"
            % (UI.Color.TEXT_HEADER, UI.Color.SURFACE_HEADER)
        )
        self.head_row.setFixedHeight(fs + HEAD_EXTRA)
        self.head_row.setStyleSheet("QLabel { %s }" % cabecera)

        for tarjeta in (self.card_wildcard, self.card_included):
            tarjeta.setStyleSheet(
                "QWidget { background-color: %s; border: 1px solid %s;"
                " border-radius: %dpx; }"
                "QLabel { border: none; color: %s; font-size: 12px; }"
                % (UI.Color.SURFACE, UI.Color.BORDER, UIStyle.Metric.RADIUS,
                   UI.Color.TEXT)
            )
            tarjeta.icono.setPixmap(
                tinted_icon("info", UI.Color.ACCENT_HOVER, 20).pixmap(20, 20)
            )

        self.add_button.setStyleSheet(UI.Style.BTN_SECONDARY)
        self.add_button.setIcon(tinted_icon("plus", UI.Color.TEXT, 17))
        self.cancel_button.setStyleSheet(UI.Style.BTN_SECONDARY)
        self.save_button.setStyleSheet(UI.Style.BTN_PRIMARY)
        self.font_minus.setStyleSheet(UI.Style.BTN_ICON)
        self.font_plus.setStyleSheet(UI.Style.BTN_ICON)
        self.version_label.setStyleSheet(
            "color: %s; font-size: 12px;" % UI.Color.TEXT_DIM
        )
        for etiqueta in (self.theme_label, self.font_label):
            etiqueta.setStyleSheet("color: %s;" % UI.Color.TEXT)
        for linea in (self.appearance_sep, self.footer_sep):
            linea.setStyleSheet("background-color: %s; border: none;" % UI.Color.BORDER)

        elegido = self.appearance.get("theme")
        for theme_id, boton in self.theme_buttons.items():
            boton.setStyleSheet(
                UI.Style.BTN_PRIMARY if theme_id == elegido else UI.Style.BTN_SECONDARY
            )

        self.shot_row.apply_theme(UI, fs)
        for fila in self.rows:
            fila.apply_theme(UI, fs)
        self._fit_table()

    def _fit_table(self):
        """
        Le da al area de filas el alto que necesita, hasta el tope.

        Sin esto el area se queda con el minimo que le toque al repartir el
        alto de la ventana y la tabla abre cortada a la mitad, con scroll,
        aunque haya lugar de sobra abajo.
        """
        alto_fila = self.font_size() + ROW_EXTRA
        filas = len(self.rows) + 1  # +1 por la del shot
        alto = min(TABLE_MAX_HEIGHT, filas * alto_fila + 4)
        self.scroll.setMinimumHeight(alto)
        self.scroll.setMaximumHeight(TABLE_MAX_HEIGHT)

    # ------------------------------------------------------------- resolucion --
    def _path_edited(self, _fila):
        self.refresh()

    def refresh(self):
        """Recalcula inclusiones y validacion, y pide resolver contra disco."""
        self._update_inheritance()
        self._update_field_errors()
        self._resolve_timer.start()

    def _update_field_errors(self):
        """Marca en rojo los campos repetidos o con un atajo que no sirve."""
        nombres = {}
        rutas = {}
        atajos = {}
        for fila in self.rows:
            datos = fila.to_dict()
            if datos["name"]:
                nombres.setdefault(datos["name"].lower(), []).append(fila)
            if datos["path"]:
                rutas.setdefault(datos["path"].lower(), []).append(fila)
            if datos["copy_to"] and datos["shortcut"]:
                atajos.setdefault(datos["shortcut"], []).append(fila)

        errores = {f.uid: set() for f in self.rows}
        for grupo, campo in ((nombres, "name"), (rutas, "path")):
            for filas in grupo.values():
                if len(filas) > 1:
                    for fila in filas:
                        errores[fila.uid].add(campo)
        for letra, filas in atajos.items():
            # Las cinco de la barra no se pueden usar aunque no las repita
            # nadie: Qt no dispararia ni el boton ni la location.
            if len(filas) > 1 or letra in RESERVED_SHORTCUTS:
                for fila in filas:
                    errores[fila.uid].add("shortcut")

        for fila in self.rows:
            fila.set_field_errors(errores[fila.uid], self.UI, self.font_size())

    def _update_inheritance(self):
        """
        Marca las locations que ya cubre otra que se escanea entera.

        Se mira el scan EXPLICITO de las otras filas y no el efectivo: con el
        efectivo, dos rutas que se incluyen mutuamente se apagarian la una a
        la otra en loop y ninguna terminaria escaneandose.
        """
        # El shot NO entra en la cuenta. Define el limite del shot, no de
        # donde se busca: eso lo dice la tabla de locations. Metiendolo,
        # cualquier location relativa cae adentro de "../.." y las cuatro
        # filas quedaban tildadas y deshabilitadas de entrada, o sea que la
        # tabla entera dejaba de poder editarse.
        candidatas = [{"name": fila.name_edit.text().strip(),
                       "path": fila.path(),
                       "scan": bool(fila.data.get("scan", True))}
                      for fila in self.rows]

        for i, fila in enumerate(self.rows):
            fila.set_scan_inherited(paths.scanning_parent(candidatas, i, self.nk_dir))

    def _resolve_now(self):
        if not self.nk_dir:
            # Sin .nk guardado no hay contra que resolver: la columna entera
            # se queda en "—" en vez de mentir.
            for fila in [self.shot_row] + self.rows:
                fila.set_resolution(None, self.UI)
            return

        if self._worker is not None:
            self._worker.cancel()
        pedidos = [(fila.uid, fila.path()) for fila in [self.shot_row] + self.rows]
        self._worker = PathResolveWorker(pedidos, self.nk_dir)
        self._worker.signals.resolved.connect(self._resolved)
        QThreadPool.globalInstance().start(self._worker)

    def _resolved(self, resultados):
        self._worker = None
        for fila in [self.shot_row] + self.rows:
            if fila.uid in resultados:
                fila.set_resolution(resultados[fila.uid], self.UI)

    # ------------------------------------------------------------- validacion --
    def problems(self):
        """Los problemas que impiden guardar, en texto."""
        avisos = []
        nombres = {}
        rutas = {}
        atajos = {}

        for fila in self.rows:
            datos = fila.to_dict()
            if not datos["name"] and not datos["path"]:
                continue  # fila vacia: se descarta al guardar, no es un error
            if not datos["name"] or not datos["path"]:
                avisos.append("A location has an empty name or path.")
                continue
            nombres.setdefault(datos["name"].lower(), []).append(datos["name"])
            rutas.setdefault(datos["path"].lower(), []).append(datos["path"])
            if datos["copy_to"] and datos["shortcut"]:
                atajos.setdefault(datos["shortcut"], []).append(datos["name"])

        for clave, iguales in nombres.items():
            if len(iguales) > 1:
                avisos.append("Two locations are named \"%s\"." % iguales[0])
        for clave, iguales in rutas.items():
            if len(iguales) > 1:
                avisos.append("Two locations point to \"%s\"." % iguales[0])
        for letra, duenos in atajos.items():
            if len(duenos) > 1:
                avisos.append(
                    "Shortcut Alt+%s is used by %s." % (letra, " and ".join(duenos))
                )
            if letra in RESERVED_SHORTCUTS:
                avisos.append(
                    "Shortcut Alt+%s is already used by the toolbar; "
                    "Qt would fire neither." % letra
                )

        # Un destino de Copy to tiene que resolver a UNA carpeta: con cero no
        # hay adonde copiar -"../*assets*" no es un nombre de carpeta que se
        # pueda crear- y con varias habria que elegir por el usuario.
        for fila in self.rows:
            datos = fila.to_dict()
            if not datos["copy_to"] or not datos["path"]:
                continue
            etiqueta = datos["name"] or datos["path"]
            resolution = fila.resolution()
            if resolution is None:
                # Todavia no volvio el worker, o el .nk no esta guardado. No
                # se deja pasar en silencio: sin resolver no se sabe si el
                # destino existe, y el aviso es justamente lo que se decidio.
                if self.nk_dir:
                    avisos.append(
                        "\"%s\" has not been checked against disk yet; "
                        "try again in a moment." % etiqueta
                    )
                continue
            if resolution.kind == paths.INVALID:
                avisos.append("\"%s\" is not a valid path." % etiqueta)
            elif not resolution.folders:
                avisos.append(
                    "\"%s\" is a Copy to destination but does not match any "
                    "existing folder." % etiqueta
                )
            elif len(resolution.folders) > 1:
                avisos.append(
                    "\"%s\" is a Copy to destination but matches %d folders."
                    % (etiqueta, len(resolution.folders))
                )
        return avisos

    # ---------------------------------------------------------------- guardar --
    def collect(self):
        """Lo que hay en pantalla, en el formato que espera el modulo de config."""
        locations = [f.to_dict() for f in self.rows]
        return {
            "shot": self.shot_row.to_dict(),
            # La fila a medias se descarta, igual que en el formato viejo.
            "locations": [l for l in locations if l["name"] and l["path"]],
            "appearance": dict(self.appearance),
        }

    def save(self):
        avisos = self.problems()
        if avisos:
            QMessageBox.warning(
                self, "Media Manager",
                "The settings were not saved:\n\n• " + "\n• ".join(avisos),
            )
            return

        if self.load_error:
            respuesta = QMessageBox.question(
                self, "Media Manager",
                "Your settings file could not be read, so what is shown here "
                "are the factory defaults.\n\nSave anyway and overwrite it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if respuesta != QMessageBox.Yes:
                return

        datos = self.collect()
        ruta = get_write_path()
        if not ruta:
            QMessageBox.warning(
                self, "Media Manager",
                "The settings could not be saved: no writable config folder "
                "was found.",
            )
            return
        if not write_ini(ruta, format_ini(datos)):
            QMessageBox.warning(
                self, "Media Manager",
                "The settings could not be saved to:\n%s" % ruta,
            )
            return

        debug_print("Configuracion guardada en %s" % ruta)
        self.saved_appearance = dict(self.appearance)
        self.settings_saved.emit()
        self.close()

    def _cancel(self):
        self.close()

    def closeEvent(self, event):
        # La reversion va aca y no en _cancel: Escape pasa por _cancel pero
        # la X de la ventana y Alt+F4 no, y por ahi se salia dejando aplicado
        # un tema que no se guardo nunca.
        if self.appearance != self.saved_appearance:
            self.appearance_previewed.emit(dict(self.saved_appearance))
            self.appearance = dict(self.saved_appearance)
        if self._worker is not None:
            self._worker.cancel()
            self._worker = None
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)
