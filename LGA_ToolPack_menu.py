"""
_____________________________________

  LGA_ToolPack | Lega
  Colección de herramientas de Nuke
_____________________________________

"""

import nuke
import nukescripts

# Importar iconos de la carpeta icons
import os

# --- Config loader & helpers -------------------------------------------
import importlib


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
PY_DIR = os.path.join(ROOT_DIR, "py")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")


def _read_product_version():
    """Lee la version publicada desde la fuente unica VERSION."""
    version_path = os.path.join(ROOT_DIR, "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as version_file:
            return version_file.read().strip()
    except (OSError, UnicodeError) as error:
        nuke.warning("No se pudo leer VERSION de LGA_ToolPack: %s" % error)
        return "unknown"


PRODUCT_VERSION = _read_product_version()

# Carga los modulos runtime desde py/
nuke.pluginAddPath(PY_DIR.replace("\\", "/"))


# El estado de las tools lo resuelve LGA_ToolPack_Enabled, que lo lee de la
# carpeta de datos del usuario y no de adentro del pack. Vive en py/ para que
# el panel de Enable Tools use exactamente la misma logica que el menu.
# `except Exception` y no `except ImportError`: un SyntaxError o un fallo de
# encoding al importar no son ImportError, se propagarian y Nuke arrancaria sin
# el menu TP entero, que es exactamente lo que se quiere evitar.
try:
    import LGA_ToolPack_Enabled as _enabled_config
except Exception as _enabled_error:
    # Si el modulo no carga, el menu tiene que armarse igual y con todo
    # visible: es preferible mostrar de mas a dejar al usuario sin
    # herramientas y sin forma de recuperarlas.
    nuke.warning("No se pudo cargar LGA_ToolPack_Enabled: %s" % _enabled_error)
    _enabled_config = None
else:
    # Siembra la config del usuario la primera vez, rescatando lo que hubiera
    # configurado antes de que esa ubicacion existiera. Va en su propio try
    # por el mismo motivo: sembrar es una comodidad, no una condicion para
    # que exista el menu.
    try:
        _enabled_config.ensure_user_ini()
    except Exception as _seed_error:
        nuke.warning("No se pudo sembrar la config de LGA ToolPack: %s" % _seed_error)


def load_tool_flags():
    """Estado efectivo de las tools. {} si el modulo de config no cargo.

    Se conserva por compatibilidad: es un nombre publico desde versiones
    anteriores del pack y puede haber scripts de usuario apoyados en el.
    """
    if _enabled_config is None:
        return {}
    return _enabled_config.load_flags()


def is_enabled(key: str) -> bool:
    """Si no está en ninguna capa => True (default)."""
    if _enabled_config is None:
        return True
    return _enabled_config.is_enabled(key)


def add_tool(menu, label, key, module, attr, shortcut=None, icon=None, context=2):
    """Registra una tool si está habilitada y la importa tarde (lazy)."""
    if not is_enabled(key):
        try:
            import nuke

            nuke.warning(f"Tool disabled: {key}")
        except Exception:
            pass
        return

    def _runner():
        m = importlib.import_module(module)
        func = getattr(m, attr)
        return func()

    kwargs = {}
    if shortcut:
        kwargs["shortcut"] = shortcut
    if icon:
        kwargs["icon"] = icon
    if context is not None:
        kwargs["shortcutContext"] = context

    menu.addCommand(label, _runner, **kwargs)


def any_enabled(keys):
    return any(is_enabled(k) for k in keys)


# --- End config helpers ---------------------------------------------------------


def _get_icon(name):
    icons_root = os.path.join(PY_DIR, "icons")
    path = os.path.join(icons_root, name) + ".png"
    return path.replace("\\", "/")


# Crea el menu "TP" (ToolPack)
n = nuke.menu("Nuke").addMenu("TP", icon=_get_icon("LGA"))


# -----------------------------------------------------------------------------
#                              READ n WRITE TOOLS
# -----------------------------------------------------------------------------
# Agrega el comando "READ n WRITE" al menu "TP" y "TP2"
n.addCommand("READ n WRITE", lambda: None)
# Define el icono para los items de Read n Write
icon_RnW = _get_icon("TP_RnW")


add_tool(
    n,
    label="  Media Manager",
    key="Media_Manager",
    module="LGA_mediaManager",
    attr="main",
    shortcut="ctrl+m",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Media Path Replacer",
    key="Media_Path_Replacer",
    module="LGA_mediaPathReplacer",
    attr="show_search_replace_widget",
    shortcut="ctrl+alt+m",
    icon=icon_RnW,
    context=2,
)

add_tool(
    n,
    label="  Paths to Relative",
    key="Paths_To_Relative",
    module="LGA_RnW_PathsToRelative",
    attr="main",
    icon=icon_RnW,
    context=None,
)

add_tool(
    n,
    label="  Read from Write",
    key="Read_From_Write",
    module="readFromWrite",
    attr="ReadFromWrite",
    shortcut="shift+r",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Open in Shot Player",
    key="Open_in_Shot_Player",
    module="LGA_OpenInShotPlayer",
    attr="main",
    # Nuke interpreta Ctrl como Command en macOS (PortableText propio).
    shortcut="ctrl+alt+shift+p",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Duplicate Publish",
    key="Duplicate_Publish",
    module="LGA_RnW_DuplicatePublish",
    attr="main",
    icon=icon_RnW,
    context=None,
)


add_tool(
    n,
    label="  Write Presets",
    key="Write_Presets",
    module="LGA_Write_Presets",
    attr="main",
    shortcut="shift+w",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Write Focus",
    key="Write_Focus",
    module="LGA_Write_Focus",
    attr="main",
    shortcut="ctrl+alt+shift+w",
    icon=icon_RnW,
    context=2,
)


def _add_send_mail_runner():
    import LGA_Write_SendMail

    LGA_Write_SendMail.add_send_mail_checkbox()


if is_enabled("Write_Add_Send_Mail"):
    n.addCommand(
        "  Write - Add Send Mail option",
        _add_send_mail_runner,
        "ctrl+shift+w",
        shortcutContext=2,
        icon=icon_RnW,
    )


add_tool(
    n,
    label="  Show in Explorer",
    key="Show_in_Explorer",
    module="LGA_showInExplorer",
    attr="main",
    shortcut="shift+e",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Show in Flow",
    key="Show_in_Flow",
    module="LGA_showInlFlow",
    attr="main",
    shortcut="ctrl+shift+e",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Show Flow Notes",
    key="Show_Flow_Notes",
    module="LGA_showFlowNotes",
    attr="main",
    shortcut="ctrl+alt+shift+f",
    icon=icon_RnW,
    context=2,
)


add_tool(
    n,
    label="  Color Space Favs",
    key="Color_Space_Favs",
    module="LGA_RnW_ColorSpace_Favs",
    attr="main",
    shortcut="shift+c",
    icon=icon_RnW,
    context=2,
)


# -----------------------------------------------------------------------------
#                              FRAME RANGE TOOLS
# -----------------------------------------------------------------------------
# Crear separador
n.addSeparator()
n.addCommand("FRAME RANGE", lambda: None)
# Define el icono para los items de Frame Range
icon_FR = _get_icon("TP_FR")


add_tool(
    n,
    label="  Read -> Project",
    key="FR_Read_to_Project",
    module="LGA_fr_Read_to_Project",
    attr="main",
    shortcut="shift+f",
    icon=icon_FR,
    context=2,
)


add_tool(
    n,
    label="  Read -> Project (+Res)",
    key="FR_Read_to_Project_Res",
    module="LGA_fr_Read_to_Project_Res",
    attr="main",
    shortcut="ctrl+shift+f",
    icon=icon_FR,
    context=2,
)


# -----------------------------------------------------------------------------
#                           ROTATE TRANSFORM SHORTCUTS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("ROTATE TRANSFORM", lambda: None)
# Define el icono para los items del Rotate Transform
icon_RT = _get_icon("TP_RotateTransform")


def _rotate_left_01_runner():
    import LGA_rotateShortcuts

    LGA_rotateShortcuts.increment_rotate(0.1)


def _rotate_left_1_runner():
    import LGA_rotateShortcuts

    LGA_rotateShortcuts.increment_rotate(1)


def _rotate_right_01_runner():
    import LGA_rotateShortcuts

    LGA_rotateShortcuts.increment_rotate(-0.1)


def _rotate_right_1_runner():
    import LGA_rotateShortcuts

    LGA_rotateShortcuts.increment_rotate(-1)


if is_enabled("Rotate_Commands"):
    n.addCommand(
        "  Rotate - Left (0.1)", _rotate_left_01_runner, "Ctrl+/", icon=icon_RT
    )

    n.addCommand(
        "  Rotate - Left (1)", _rotate_left_1_runner, "Ctrl+Shift+/", icon=icon_RT
    )

    n.addCommand(
        "  Rotate - Right (-0.1)", _rotate_right_01_runner, "Ctrl+*", icon=icon_RT
    )

    n.addCommand(
        "  Rotate - Right (-1)", _rotate_right_1_runner, "Ctrl+Shift+*", icon=icon_RT
    )


# -----------------------------------------------------------------------------
#                                 KNOBS TOOLS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
# Define el icono para los items
icon_Knobs = _get_icon("TP_Knobs")

# -----------------------------------------------------------------------------
#                                 NODE BUILDS
# -----------------------------------------------------------------------------
n.addCommand("NODE BUILDS", lambda: None)


add_tool(
    n,
    label="  Build Iteration",
    key="Build_Iteration",
    module="LGA_build_iteration",
    attr="gen_iteration_simple",
    shortcut="shift+i",
    icon=icon_Knobs,
    context=2,
)


add_tool(
    n,
    label="  Build Roto + Blur in input mask",
    key="Build_Roto_BlurMask",
    module="LGA_build_Roto",
    attr="main",
    shortcut="shift+o",
    icon=icon_Knobs,
    context=2,
)


add_tool(
    n,
    label="  Build Merge (mask) | Switch ops",
    key="Build_Merge_SwitchOps",
    module="LGA_build_Merge",
    attr="main",
    shortcut="shift+m",
    icon=icon_Knobs,
    context=2,
)


add_tool(
    n,
    label="  Build Grade",
    key="Build_Grade",
    module="LGA_build_Grade",
    attr="gradeMask",
    shortcut="shift+G",
    icon=icon_Knobs,
    context=2,
)
add_tool(
    n,
    label="  Build Grade Highlights",
    key="Build_Grade_Highlights",
    module="LGA_build_Grade",
    attr="gradeHI",
    shortcut="ctrl+shift+G",
    icon=icon_Knobs,
    context=2,
)


# Añadir sección KNOBS
n.addCommand("KNOBS", lambda: None)


add_tool(
    n,
    label="  Disable A-B",
    key="Disable_A_B",
    module="LGA_disable_A_B",
    attr="main",
    shortcut="Shift+D",
    icon=icon_Knobs,
    context=2,
)


add_tool(
    n,
    label="  Channels Cycle",
    key="Channels_Cycle",
    module="LGA_channelsCycle",
    attr="main",
    shortcut="ctrl+alt+shift+a",
    icon=icon_Knobs,
    context=2,
)


add_tool(
    n,
    label="  Channel HotBox",
    key="Channel_HotBox",
    module="channel_hotbox",
    attr="start",
    shortcut="shift+H",
    icon=icon_Knobs,
)


# -----------------------------------------------------------------------------
#                                 VA TOOLS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("VA", lambda: None)
# Define el icono para los items de Frame Range
icon_VA = _get_icon("TP_VA")


add_tool(
    n,
    label="  Viewer Rec709",
    key="Viewer_Rec709",
    module="LGA_viewerRec709",
    attr="main",
    shortcut="shift+v",
    icon=icon_VA,
    context=2,
)


def _take_snapshot_runner():
    import LGA_viewer_SnapShot

    LGA_viewer_SnapShot.take_snapshot(save_to_gallery=True)


def _take_snapshot_compare_runner():
    """Pega la captura a la derecha de la anterior, para armar la tira."""
    import LGA_viewer_SnapShot

    LGA_viewer_SnapShot.take_snapshot(save_to_gallery=True, compare=True)


if is_enabled("Snapshot_Tools"):
    n.addCommand(
        "  Take Snapshot",
        _take_snapshot_runner,
        "shift+F9",
        shortcutContext=2,
        icon=icon_VA,
    )

    n.addCommand(
        "  Take Snapshot and Append",
        _take_snapshot_compare_runner,
        "alt+shift+F9",
        shortcutContext=2,
        icon=icon_VA,
    )

    # El motor viejo (el del Write, a resolucion completa) no tiene atajo a
    # proposito: se llega con Ctrl+Click en el boton del viewer. En Nuke un
    # shortcut necesita un item de menu, y un item escondido con setVisible
    # pierde el shortcut —Qt le da de baja la accion—, asi que no hay forma de
    # tenerlo con atajo y escondido a la vez. Se eligio escondido.

# Variables para el estado del F9 hold global
_f9_menu_pressed = False
_f9_menu_timer = None


def menu_f9_hold():
    """Maneja el comportamiento hold de F9 desde el menu"""
    global _f9_menu_pressed, _f9_menu_timer

    if not _f9_menu_pressed:
        # Primera activacion - mostrar snapshot
        print("F9 menu presionado - mostrando snapshot")
        import LGA_viewer_SnapShot

        LGA_viewer_SnapShot.show_snapshot_hold(start=True)
        _f9_menu_pressed = True

    # Cancelar timer anterior si existe
    if _f9_menu_timer:
        _f9_menu_timer.stop()
        _f9_menu_timer = None

    # Crear nuevo timer para detectar release - USAR QTimer en lugar de threading.Timer
    from LGA_QtAdapter_ToolPack import QtCore

    _f9_menu_timer = QtCore.QTimer()
    _f9_menu_timer.setSingleShot(True)
    _f9_menu_timer.timeout.connect(menu_f9_release)
    _f9_menu_timer.start(400)


def menu_f9_release():
    """Se ejecuta cuando se detecta release de F9 desde el menu"""
    global _f9_menu_pressed, _f9_menu_timer

    if _f9_menu_pressed:
        print("F9 menu liberado - ocultando snapshot")
        import LGA_viewer_SnapShot

        LGA_viewer_SnapShot.show_snapshot_hold(start=False)
        _f9_menu_pressed = False

    if _f9_menu_timer:
        _f9_menu_timer.stop()
        _f9_menu_timer = None


if is_enabled("Snapshot_Tools"):
    # Este addCommand estaba indentado adentro de menu_f9_release(), asi que no
    # se ejecutaba nunca y el atajo F9 no llegaba a registrarse. Ademas el
    # comando iba como string, que se evalua en __main__ y aca no existe: va la
    # referencia a la funcion, como el resto de los comandos del archivo.
    n.addCommand(
        "  Show Snapshot (Hold)",
        menu_f9_hold,
        "F9",
        shortcutContext=2,
        icon=icon_VA,
    )


def _reset_workspace_runner():
    import hiero

    hiero.ui.resetCurrentWorkspace()


if is_enabled("Reset_Workspace"):
    n.addCommand(
        "  Reset Workspace", _reset_workspace_runner, "ctrl+alt+w", icon=icon_VA
    )


def _restart_nukex_runner():
    import LGA_restartNukeX

    LGA_restartNukeX.check_and_exit(1)


if is_enabled("Restart_NukeX"):
    n.addCommand(
        "  Restart NukeX", _restart_nukex_runner, "ctrl+alt+shift+Q", icon=icon_VA
    )


# -----------------------------------------------------------------------------
#                                 Settings
# -----------------------------------------------------------------------------
n.addSeparator()


def _settings_runner():
    import LGA_ToolPack_settings

    LGA_ToolPack_settings.main()


try:
    icon_Settings = _get_icon("TP_Settings")
except Exception:
    icon_Settings = ""

# Settings ya no pasa por is_enabled(): es la configuracion del pack y tiene
# que estar siempre. Apagarla dejaba al usuario sin acceso a los ajustes de
# Write Focus, Show in Flow, Color Space Favs y el resto.
n.addCommand("Settings", _settings_runner, icon=icon_Settings)


def _enable_tools_runner():
    import LGA_ToolPack_EnabledPanel

    LGA_ToolPack_EnabledPanel.main()


# Por el mismo motivo, y ademas porque es el unico camino de vuelta: un panel
# que se puede desactivar a si mismo deja al usuario sin forma de reactivar
# nada sin editar archivos a mano.
n.addCommand("Enable Tools", _enable_tools_runner, icon=icon_Settings)


# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()


def _documentation_runner():
    import webbrowser

    webbrowser.open("https://github.com/legandrop/LGA_ToolPack-for_Nuke")


n.addCommand("Documentation v%s" % PRODUCT_VERSION, _documentation_runner)
