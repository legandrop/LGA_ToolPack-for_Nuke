"""
____________________________________________________________________

  LGA_ToolPack_Hiero_menu v1.00 | Lega

  Menu TP del pack en Hiero y Nuke Studio.

  El pack es de composicion y en esos hosts no carga entero: solo
  entran las tools de HIERO_TOOLS. Para habilitar otra, se agrega
  una entrada a esa lista y su runner; para sacarla, se borra.

  El menu se arma DIFERIDO: cuando corre menu.py el modulo C de
  Hiero (_fnpython) todavia no esta cargado e `import hiero` falla.
  Por eso aca no se importa hiero a nivel de modulo.

  Log de cada corrida: logs/DebugPy_LGA_ToolPack_Hiero_menu.log.

  v1.00: Version inicial. Solo Reset Workspace.
____________________________________________________________________
"""

import os
import sys


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
PY_DIR = os.path.join(ROOT_DIR, "py")
ICON_PATH = os.path.join(PY_DIR, "icons", "LGA.png").replace("\\", "/")

MENU_TITLE = "TP"

# Reintentos mientras hiero no se pueda importar: 120 x 250 ms = 30 s. No hay
# medicion de cuanto tarda Studio; el log registra en que intento quedo listo.
RETRY_INTERVAL_MS = 250
MAX_ATTEMPTS = 120

# Consola apagada por default; el log a archivo se escribe siempre.
DEBUG = False
LOG_PATH = os.path.join(ROOT_DIR, "logs", "DebugPy_LGA_ToolPack_Hiero_menu.log")

# `py/` no se registra con pluginAddPath en estos hosts —el pack entero no
# carga—, asi que se agrega solo a sys.path, para el adapter de Qt y para
# leer el estado de Enable Tools.
if PY_DIR not in sys.path:
    sys.path.append(PY_DIR)


def _write_log(message, mode="a"):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, mode, encoding="utf-8", newline="\n") as log_file:
            log_file.write(message + "\n")
    except OSError:
        pass


def _log(message, error=False):
    """Registra en el log; a consola solo con DEBUG o si es un error final."""
    _write_log(message)
    if DEBUG or error:
        print("LGA_ToolPack: %s" % message)


# Cada corrida pisa el log anterior.
_write_log("LGA_ToolPack_Hiero_menu: inicio, python %s" % sys.version.split()[0], "w")


# --- Runners -----------------------------------------------------------------


def _reset_workspace_runner():
    import hiero.ui

    hiero.ui.resetCurrentWorkspace()


# --- Lista blanca --------------------------------------------------------------
# Cada entrada es una tool que SI carga en Hiero y Nuke Studio. `key` es la
# misma clave de Enable Tools que usa el menu de Nuke, asi que apagarla desde
# ese panel la apaga en los dos hosts.
HIERO_TOOLS = [
    {
        "key": "Reset_Workspace",
        "label": "Reset Workspace",
        "runner": _reset_workspace_runner,
        "shortcut": "Ctrl+Alt+W",
    },
]


# --- Estado de Enable Tools ----------------------------------------------------


def _load_enabled_config():
    """Modulo de Enable Tools, o None si no carga."""
    try:
        import LGA_ToolPack_Enabled

        return LGA_ToolPack_Enabled
    except Exception as error:
        # Mismo criterio que el menu de Nuke: sin config se muestra todo.
        _log("no se pudo cargar LGA_ToolPack_Enabled: %s" % error, error=True)
        return None


def _is_enabled(config, key):
    if config is None:
        return True
    try:
        return config.is_enabled(key)
    except Exception:
        return True


# --- Armado del menu -----------------------------------------------------------


def _find_or_create_menu(menu_bar):
    """Reusa el menu TP si ya existe, para no duplicarlo en un reload."""
    for action in menu_bar.actions():
        if action.text() == MENU_TITLE and action.menu() is not None:
            return action.menu()
    menu = menu_bar.addMenu(MENU_TITLE)
    # El icono es cosmetico: si el adapter no carga, el menu va sin icono.
    try:
        from LGA_QtAdapter_ToolPack import QtGui

        menu.setIcon(QtGui.QIcon(ICON_PATH))
    except Exception:
        pass
    return menu


def build_menu():
    import hiero.ui

    menu_bar = hiero.ui.menuBar()
    if menu_bar is None:
        _log("hiero.ui.menuBar() devolvio None, menu sin armar", error=True)
        return

    config = _load_enabled_config()
    tools = [tool for tool in HIERO_TOOLS if _is_enabled(config, tool["key"])]
    if not tools:
        _log("ninguna tool habilitada en Enable Tools, sin menu TP")
        return

    menu = _find_or_create_menu(menu_bar)
    existing = {action.objectName() for action in menu.actions()}
    for tool in tools:
        object_name = "LGA_ToolPack.%s" % tool["key"]
        if object_name in existing:
            continue
        action = hiero.ui.createMenuAction(tool["label"], tool["runner"])
        action.setObjectName(object_name)
        if tool.get("shortcut"):
            action.setShortcut(tool["shortcut"])
        # registerAction la expone en el editor de atajos de Hiero.
        hiero.ui.registerAction(action)
        menu.addAction(action)
        _log("agregada: %s (%s)" % (tool["label"], tool.get("shortcut") or "sin atajo"))


def _try_build(attempt=1):
    """Arma el menu cuando hiero ya se pueda importar; si no, reintenta."""
    try:
        import hiero.ui  # noqa: F401
    except Exception as error:
        if attempt == 1:
            _log("hiero todavia no importable (%s), reintentando" % error)
        if attempt >= MAX_ATTEMPTS:
            _log(
                "hiero no disponible tras %d intentos, menu sin armar: %s"
                % (attempt, error),
                error=True,
            )
            return
        from LGA_QtAdapter_ToolPack import QtCore

        QtCore.QTimer.singleShot(
            RETRY_INTERVAL_MS, lambda: _try_build(attempt + 1)
        )
        return
    _log("hiero importable en el intento %d" % attempt)
    try:
        build_menu()
    except Exception as error:
        _log("no se pudo armar el menu de Hiero: %s" % error, error=True)


def schedule():
    """Difiere el armado al loop de eventos: ahi Hiero ya termino de arrancar."""
    try:
        from LGA_QtAdapter_ToolPack import QtCore, QApplication

        if QApplication.instance() is None:
            # Sin GUI (modo terminal) no hay menu que armar.
            _log("sin QApplication (modo terminal), no se arma menu")
            return
        QtCore.QTimer.singleShot(0, _try_build)
    except Exception as error:
        _log("no se pudo programar el menu de Hiero: %s" % error, error=True)


schedule()
