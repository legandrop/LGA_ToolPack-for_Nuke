"""
____________________________________________________________________

  LGA_ToolPack_WhatsNew v1.00 | Lega

  Ventana "What's new" del menu TP: las notas para el usuario de
  cada version del pack, de la mas nueva a la mas vieja.

  Lee whats_new.json de la raiz instalada del pack. Ese archivo lo
  genera el script de release (build_whats_new) y viaja en el zip:
  en el repo no existe hasta el proximo release, y en ese caso la
  ventana avisa que las notas van a aparecer con la proxima version.

  Solo se lee al abrir la ventana. El menu registra la entrada y
  nada mas, asi que el JSON nunca se toca al arrancar Nuke.

  La logica (leer, validar, filtrar) no importa Qt: se puede probar
  con cualquier Python. Qt y el modulo de estilo se importan recien
  al armar la ventana.

  Log de cada apertura: py/logs/DebugPy_LGA_ToolPack_WhatsNew.log.

  v1.00: Version inicial.
____________________________________________________________________
"""

import json
import os
import re
import sys
import time

PACK_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
NOTES_PATH = os.path.join(PACK_ROOT, "whats_new.json")
DEFAULT_NAME = "LGA ToolPack"

# Formato que escribe build_whats_new. Otro numero es un formato que esta
# version del pack no conoce: se trata como "sin notas" antes que mostrar
# algo mal interpretado.
SCHEMA_VERSION = 1

# Orden y titulo de los grupos dentro de cada version. Un kind que no este
# aca se ignora: no hay donde mostrarlo.
KINDS = (("new", "New"), ("improved", "Improved"), ("fixed", "Fixed"))

# Este pack no tiene ediciones (Studio/Client): no se filtra por edicion.
EDITION = None

EMPTY_MESSAGE = "Release notes will appear here starting with the next update."
NO_CHANGES_MESSAGE = "No user-facing changes in this version."

DEBUG = False
LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "logs",
    "DebugPy_LGA_ToolPack_WhatsNew.log",
)

_log_lines = []
_window = None


# ----------------------------------------------------------------------
# Log: una apertura = una corrida, el .log se pisa en cada una
# ----------------------------------------------------------------------
def _log(message):
    _log_lines.append(message)
    if DEBUG:
        print("LGA_ToolPack_WhatsNew: %s" % message)


def _flush_log():
    """Escribe el log de la corrida. Nunca rompe la ventana."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("Fecha: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
            handle.write("\n".join(_log_lines) + "\n")
    except Exception:
        pass
    del _log_lines[:]


# ----------------------------------------------------------------------
# Logica: leer, validar y filtrar. Sin Qt.
# ----------------------------------------------------------------------
def current_platform():
    """La plataforma con los nombres del WhatsNew.md: win, mac o linux."""
    if sys.platform.startswith("win"):
        return "win"
    if sys.platform == "darwin":
        return "mac"
    return "linux"


def load_notes(path=None):
    """
    El contenido de whats_new.json, o None si no hay notas que mostrar.

    None cubre todo lo que no sea un archivo valido: que no exista (el caso
    normal en el repo), que no se pueda leer, que el JSON este roto o que el
    schemaVersion no sea el que esta version conoce. Nunca levanta: un
    archivo de notas roto no puede tirarle una excepcion a Nuke.
    """
    path = path or NOTES_PATH
    if not os.path.isfile(path):
        _log("sin archivo de notas: %s" % path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as error:
        # Exception y no solo ValueError: un JSON muy anidado tira
        # RecursionError, y un disco que falla, OSError.
        _log("no se pudo leer %s: %s" % (path, error))
        return None
    if not isinstance(data, dict):
        _log("el JSON no es un objeto")
        return None
    schema = data.get("schemaVersion")
    # type() y no isinstance(): True == 1 en Python, y un "schemaVersion":
    # true no es el formato 1.
    if type(schema) is not int or schema != SCHEMA_VERSION:
        _log("schemaVersion desconocido: %r" % (schema,))
        return None
    if not isinstance(data.get("versions"), list):
        _log("el JSON no trae una lista de versiones")
        return None
    return data


def product_name(data):
    """Nombre del producto para el titulo; el del pack si el JSON no lo trae."""
    if isinstance(data, dict):
        name = data.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return DEFAULT_NAME


def _allowed(item, key, value):
    """
    Si el item se muestra para ese valor de plataforma o edicion.

    Un item sin la clave vale para todos. value None significa que esa
    dimension no se filtra (un pack sin ediciones muestra todo).
    """
    if value is None:
        return True
    allowed = item.get(key)
    if allowed is None:
        return True
    if isinstance(allowed, str):
        allowed = [allowed]
    if not isinstance(allowed, list):
        return False
    return value in allowed


def _version_key(version):
    """2.66 -> (2, 66), para ordenar por numero y no alfabeticamente."""
    return tuple(int(part) for part in re.findall(r"\d+", version))


def visible_versions(data, platform, edition=None):
    """
    Las versiones a mostrar, de la mas nueva a la mas vieja.

    Cada una es {"version", "date", "groups"}, con groups una lista de
    (titulo, [textos]) en el orden New / Improved / Fixed. Los items de
    otra plataforma o edicion se descartan; una version que se queda sin
    items se muestra igual, con groups vacio. Lo que venga mal formado se
    saltea sin cortar el resto.
    """
    if not isinstance(data, dict) or not isinstance(data.get("versions"), list):
        return []
    result = []
    for entry in data["versions"]:
        if not isinstance(entry, dict):
            continue
        version = entry.get("version")
        if not isinstance(version, str) or not version.strip():
            continue
        items = entry.get("items")
        if not isinstance(items, list):
            items = []
        items = [
            item
            for item in items
            if isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and item["text"].strip()
            and _allowed(item, "platform", platform)
            and _allowed(item, "edition", edition)
        ]
        groups = []
        for kind, title in KINDS:
            texts = [item["text"].strip() for item in items if item.get("kind") == kind]
            if texts:
                groups.append((title, texts))
        date = entry.get("date")
        result.append(
            {
                "version": version.strip(),
                "date": date.strip() if isinstance(date, str) else "",
                "groups": groups,
            }
        )
    result.sort(key=lambda entry: _version_key(entry["version"]), reverse=True)
    return result


# ----------------------------------------------------------------------
# Ventana
# ----------------------------------------------------------------------
def _escape(text):
    """El texto va en rich text: un & o un < de una nota no es marcado."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _version_header(entry):
    from LGA_QtAdapter_ToolPack import QtWidgets
    from LGA_UI_Style_ToolPack import Color, Metric, semibold_css

    row = QtWidgets.QHBoxLayout()
    row.setSpacing(Metric.SPACING)
    version = QtWidgets.QLabel("v%s" % entry["version"])
    # El numero de version es lo que se busca al recorrer la lista: va en
    # blanco y en 600, el mismo peso que el resto de lo enfatizado del pack.
    version.setStyleSheet(
        "QLabel { color: %s; %s }" % (Color.TEXT_STRONG, semibold_css())
    )
    row.addWidget(version)
    if entry["date"]:
        date = QtWidgets.QLabel(entry["date"])
        date.setStyleSheet("color: %s;" % Color.TEXT_DIM)
        row.addWidget(date)
    row.addStretch(1)
    return row


def _item_row(text):
    """Una nota con su vineta. La vineta va aparte para que las lineas
    siguientes de una nota larga queden alineadas con el texto y no con
    la vineta."""
    from LGA_QtAdapter_ToolPack import QtWidgets, Qt
    from LGA_UI_Style_ToolPack import Color

    row = QtWidgets.QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    bullet = QtWidgets.QLabel("\u2022")
    bullet.setStyleSheet("color: %s;" % Color.TEXT_DIM)
    bullet.setAlignment(Qt.AlignTop)
    label = QtWidgets.QLabel(_escape(text))
    label.setTextFormat(Qt.RichText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    row.addWidget(bullet, 0, Qt.AlignTop)
    row.addWidget(label, 1)
    return row


def _version_block(entry):
    from LGA_QtAdapter_ToolPack import QtWidgets
    from LGA_UI_Style_ToolPack import Color, Metric

    block = QtWidgets.QVBoxLayout()
    block.setContentsMargins(0, 0, 0, 0)
    block.setSpacing(4)
    block.addLayout(_version_header(entry))
    if not entry["groups"]:
        empty = QtWidgets.QLabel(NO_CHANGES_MESSAGE)
        empty.setStyleSheet("color: %s;" % Color.TEXT_DIM)
        block.addWidget(empty)
        return block
    for title, texts in entry["groups"]:
        block.addSpacing(Metric.SPACING // 2)
        group = QtWidgets.QLabel(title)
        group.setStyleSheet("color: %s;" % Color.TEXT_DIM)
        block.addWidget(group)
        for text in texts:
            block.addLayout(_item_row(text))
    return block


def _separator():
    from LGA_QtAdapter_ToolPack import QtWidgets

    # Style.FORM pinta las HLine de 1 px con el color de borde.
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    return line


def build_window(name, versions, parent=None):
    """Arma la ventana. versions vacio muestra el aviso de 'sin notas'."""
    from LGA_QtAdapter_ToolPack import QtWidgets, Qt
    from LGA_UI_Style_ToolPack import Metric, Style, apply_ui_font

    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName("LGA_ToolPack_WhatsNew")
    dialog.setWindowTitle("What's new in %s" % name)
    dialog.setStyleSheet(Style.FORM)

    root = QtWidgets.QVBoxLayout(dialog)
    root.setContentsMargins(*([Metric.WINDOW_MARGIN] * 4))
    root.setSpacing(Metric.SPACING)

    title = QtWidgets.QLabel("What's new in %s" % name)
    title.setProperty("lgaTitle", True)
    root.addWidget(title)

    if versions:
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(content)
        # Aire a la derecha para que la scrollbar no se apoye en el texto.
        column.setContentsMargins(0, 0, Metric.SPACING, 0)
        column.setSpacing(Metric.SPACING)
        for index, entry in enumerate(versions):
            if index:
                column.addWidget(_separator())
            column.addLayout(_version_block(entry))
        column.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
    else:
        message = QtWidgets.QLabel(EMPTY_MESSAGE)
        message.setWordWrap(True)
        root.addWidget(message)
        root.addStretch(1)

    buttons = QtWidgets.QHBoxLayout()
    buttons.addStretch(1)
    close = QtWidgets.QPushButton("Close")
    # Close no es una accion: va en secundario y no hay ningun violeta.
    close.setStyleSheet(Style.BTN_SECONDARY)
    close.setFixedHeight(Metric.BUTTON_HEIGHT)
    close.setDefault(True)
    close.clicked.connect(dialog.close)
    buttons.addWidget(close)
    root.addLayout(buttons)

    # Ultimo paso del armado: recorre los hijos que ya existen.
    apply_ui_font(dialog, Metric.FORM_FONT_SIZE)
    if versions:
        dialog.resize(640, 560)
    else:
        dialog.resize(Metric.DIALOG_MIN_WIDTH, dialog.sizeHint().height())
    return dialog


def _host_window():
    """La ventana principal activa, para que el dialogo quede encima de Nuke."""
    try:
        from LGA_QtAdapter_ToolPack import QtWidgets

        return QtWidgets.QApplication.activeWindow()
    except Exception:
        return None


def show_whats_new(parent=None, notes_path=None):
    """Abre la ventana. Es lo que llama la entrada What's new del menu."""
    global _window
    _log("pack: %s" % PACK_ROOT)
    platform = current_platform()
    try:
        data = load_notes(notes_path)
        versions = visible_versions(data, platform, EDITION) if data else []
        _log(
            "plataforma %s, %d versiones a mostrar" % (platform, len(versions))
        )
        if _window is not None:
            try:
                _window.close()
                _window.deleteLater()
            except Exception:
                pass
            _window = None
        _window = build_window(
            product_name(data), versions, parent or _host_window()
        )
        _window.show()
        _window.raise_()
        _window.activateWindow()
    except Exception as error:
        _log("error al abrir la ventana: %s" % error)
        print("LGA_ToolPack_WhatsNew: no se pudo abrir la ventana: %s" % error)
    finally:
        _flush_log()
