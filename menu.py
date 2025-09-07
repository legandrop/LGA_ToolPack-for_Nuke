"""
_____________________________________

  LGA_ToolPack v2.44 | Lega
  Colección de herramientas de Nuke
_____________________________________

"""

import nuke
import nukescripts

# Importar iconos de la carpeta icons
import os

# --- Config loader & helpers -------------------------------------------
import configparser, importlib


def _ini_paths():
    # user-level
    home = os.path.expanduser("~")
    user_ini = os.path.join(home, ".nuke", "_LGA_ToolPack_Enabled.ini")
    # package-level (junto a este archivo)
    pkg_ini = os.path.join(os.path.dirname(__file__), "_LGA_ToolPack_Enabled.ini")
    return user_ini, pkg_ini


_TOOL_FLAGS = None  # cache


def load_tool_flags():
    """Lee el INI (user pisa a package). Si falta o hay error => todo True."""
    global _TOOL_FLAGS
    if _TOOL_FLAGS is not None:
        return _TOOL_FLAGS

    cfg = configparser.ConfigParser()
    cfg.optionxform = str  # respeta mayúsculas en claves
    user_ini, pkg_ini = _ini_paths()

    read_ok = False
    for path in [pkg_ini, user_ini]:
        if os.path.isfile(path):
            try:
                cfg.read(path, encoding="utf-8")
                read_ok = True
            except Exception:
                pass

    flags = {}
    if read_ok and cfg.has_section("Tools"):
        for key, val in cfg.items("Tools"):
            v = str(val).strip().lower()
            flags[key] = v in ("1", "true", "yes", "on")
    else:
        # sin archivo/section => defaults vacíos (=> True por defecto)
        flags = {}

    _TOOL_FLAGS = flags
    return _TOOL_FLAGS


def is_enabled(key: str) -> bool:
    """Si no está en INI => True (default)."""
    flags = load_tool_flags()
    return flags.get(key, True)


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
    icons_root = os.path.join(os.path.dirname(__file__), "icons")
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
    label="  CopyCat Cleaner",
    key="CopyCat_Cleaner",
    module="LGA_CopyCat_Cleaner",
    attr="run_copycat_cleaner",
    icon=icon_RnW,
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
#                              COPY n PASTE TOOLS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("COPY n PASTE", lambda: None)
# Define el icono para los items de Frame Range
icon_CnP = _get_icon("TP_CnP")


add_tool(
    n,
    label="  Paste To Selected",
    key="Paste_To_Selected",
    module="pasteToSelected",
    attr="pasteToSelected",
    shortcut="ctrl+shift+v",
    icon=icon_CnP,
    context=2,
)


add_tool(
    n,
    label="  Copy with inputs",
    key="Copy_with_inputs",
    module="duplicateWithInputs",
    attr="copyWithInputs",
    shortcut="ctrl+alt+c",
    icon=icon_CnP,
    context=2,
)
add_tool(
    n,
    label="  Paste with inputs",
    key="Paste_with_inputs",
    module="duplicateWithInputs",
    attr="pasteWithInputs",
    shortcut="ctrl+alt+v",
    icon=icon_CnP,
    context=2,
)
add_tool(
    n,
    label="  Duplicate with inputs",
    key="Duplicate_with_inputs",
    module="duplicateWithInputs",
    attr="duplicateWithInputs",
    shortcut="ctrl+alt+k",
    icon=icon_CnP,
    context=2,
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


if is_enabled("Snapshot_Tools"):
    n.addCommand(
        "  Take Snapshot",
        _take_snapshot_runner,
        "shift+F9",
        shortcutContext=2,
        icon=icon_VA,
    )

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
    try:
        from PySide2.QtCore import QTimer
    except:
        from PySide.QtCore import QTimer

    _f9_menu_timer = QTimer()
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

    n.addCommand(
        "  Show Snapshot (Hold)",
        "menu_f9_hold()",
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

if is_enabled("Settings"):
    n.addCommand("Settings", _settings_runner, icon=icon_Settings)


# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()


def _documentation_runner():
    import webbrowser

    TP_script_dir = os.path.dirname(os.path.realpath(__file__))
    TP_pdf_path = os.path.join(TP_script_dir, "LGA_ToolPack.pdf")
    webbrowser.open("file://" + TP_pdf_path)


n.addCommand("Documentation v2.42", _documentation_runner)
