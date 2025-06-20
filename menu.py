"""
_____________________________________

  LGA_ToolPack v2.37 | Lega
  Colección de herramientas de Nuke
_____________________________________

"""

import nuke
import nukescripts

# Importar iconos de la carpeta icons
import os


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


# Importar el LGA_mediaManager
import LGA_mediaManager

n.addCommand(
    "  Media Manager",
    "LGA_mediaManager.main()",
    "ctrl+m",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_mediaPathReplacer
import LGA_mediaPathReplacer

n.addCommand(
    "  Media Path Replacer",
    "LGA_mediaPathReplacer.show_search_replace_widget()",
    "ctrl+alt+m",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el readFromWrite
import readFromWrite

n.addCommand(
    "  Read from Write",
    "readFromWrite.ReadFromWrite()",
    "shift+r",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_Write_Presets
import LGA_Write_Presets

n.addCommand(
    "  Write Presets",
    "LGA_Write_Presets.main()",
    "shift+w",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_Write_Focus
import LGA_Write_Focus

n.addCommand(
    "  Write Focus",
    "LGA_Write_Focus.main()",
    "ctrl+alt+shift+w",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_Write_RenderComplete y el LGA_Write_SendMail
import LGA_Write_RenderComplete
import LGA_Write_SendMail


def add_send_mail_to_all_writes():
    LGA_Write_SendMail.add_send_mail_checkbox()


n.addCommand(
    "  Write - Add Send Mail option",
    "add_send_mail_to_all_writes()",
    "ctrl+shift+w",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_showInExplorer
import LGA_showInExplorer

n.addCommand(
    "  Show in Explorer",
    "LGA_showInExplorer.main()",
    "shift+e",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_showInlFlow
import LGA_showInlFlow

n.addCommand(
    "  Show in Flow",
    "LGA_showInlFlow.main()",
    "ctrl+shift+e",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_RnW_ColorSpace_Favs
import LGA_RnW_ColorSpace_Favs

n.addCommand(
    "  Color Space Favs",
    "LGA_RnW_ColorSpace_Favs.main()",
    "shift+c",
    shortcutContext=2,
    icon=icon_RnW,
)


# -----------------------------------------------------------------------------
#                              FRAME RANGE TOOLS
# -----------------------------------------------------------------------------
# Crear separador
n.addSeparator()
n.addCommand("FRAME RANGE", lambda: None)
# Define el icono para los items de Frame Range
icon_FR = _get_icon("TP_FR")


# Importar el LGA_fr_Read_to_Project
import LGA_fr_Read_to_Project

n.addCommand(
    "  Read -> Project",
    "LGA_fr_Read_to_Project.main()",
    "shift+f",
    shortcutContext=2,
    icon=icon_FR,
)


# Importar el LGA_fr_Read_to_Project_Res
import LGA_fr_Read_to_Project_Res

n.addCommand(
    "  Read -> Project (+Res)",
    "LGA_fr_Read_to_Project_Res.main()",
    "ctrl+shift+f",
    shortcutContext=2,
    icon=icon_FR,
)


# -----------------------------------------------------------------------------
#                           ROTATE TRANSFORM SHORTCUTS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("ROTATE TRANSFORM", lambda: None)
# Define el icono para los items del Rotate Transform
icon_RT = _get_icon("TP_RotateTransform")


# Importar el Lg_Rotate_Shortcut
import LGA_rotateShortcuts

n.addCommand(
    "  Rotate - Left (0.1)",
    "LGA_rotateShortcuts.increment_rotate(0.1)",
    "Ctrl+/",
    icon=icon_RT,
)
n.addCommand(
    "  Rotate - Left (1)",
    "LGA_rotateShortcuts.increment_rotate(1)",
    "Ctrl+Shift+/",
    icon=icon_RT,
)
n.addCommand(
    "  Rotate - Right (-0.1)",
    "LGA_rotateShortcuts.increment_rotate(-0.1)",
    "Ctrl+*",
    icon=icon_RT,
)
n.addCommand(
    "  Rotate - Right (-1)",
    "LGA_rotateShortcuts.increment_rotate(-1)",
    "Ctrl+Shift+*",
    icon=icon_RT,
)


# -----------------------------------------------------------------------------
#                              COPY n PASTE TOOLS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("COPY n PASTE", lambda: None)
# Define el icono para los items de Frame Range
icon_CnP = _get_icon("TP_CnP")


# Importar cargar el PasteToSelected
import pasteToSelected

n.addCommand(
    "  Paste To Selected",
    "pasteToSelected.pasteToSelected()",
    "ctrl+shift+v",
    shortcutContext=2,
    icon=icon_CnP,
)


# Importar cargar el duplicateWithInputs
import duplicateWithInputs

n.addCommand(
    "  Copy with inputs",
    "duplicateWithInputs.copyWithInputs()",
    "ctrl+alt+c",
    shortcutContext=2,
    icon=icon_CnP,
)
n.addCommand(
    "  Paste with inputs",
    "duplicateWithInputs.pasteWithInputs()",
    "ctrl+alt+v",
    shortcutContext=2,
    icon=icon_CnP,
)
n.addCommand(
    "  Duplicate with inputs",
    "duplicateWithInputs.duplicateWithInputs()",
    "ctrl+alt+k",
    shortcutContext=2,
    icon=icon_CnP,
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


# Importar el LGA_build_iteration
import LGA_build_iteration

n.addCommand(
    "  Build Iteration",
    "LGA_build_iteration.gen_iteration_simple()",
    "shift+i",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Importar el LGA_build_Roto
import LGA_build_Roto

n.addCommand(
    "  Build Roto + Blur in input mask",
    "LGA_build_Roto.main()",
    "shift+o",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Importar el LGA_build_Merge
import LGA_build_Merge

n.addCommand(
    "  Build Merge (mask) | Switch ops",
    "LGA_build_Merge.main()",
    "shift+m",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Importar el LGA_build_Grade
import LGA_build_Grade

n.addCommand(
    "  Build Grade",
    "LGA_build_Grade.gradeMask()",
    "shift+G",
    shortcutContext=2,
    icon=icon_Knobs,
)
n.addCommand(
    "  Build Grade Highlights",
    "LGA_build_Grade.gradeHI()",
    "ctrl+shift+G",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Añadir sección KNOBS
n.addCommand("KNOBS", lambda: None)


# Importar el LGA_channelsCycle
import LGA_channelsCycle

n.addCommand(
    "  Channels Cycle",
    "LGA_channelsCycle.main()",
    "ctrl+alt+shift+a",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Importar el LGA_disable_A_B
import LGA_disable_A_B

n.addCommand(
    "  Disable A-B",
    "LGA_disable_A_B.main()",
    "Shift+D",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Channel_HotBox
import channel_hotbox

n.addCommand("  Channel &HotBox", "channel_hotbox.start()", "shift+H", icon=icon_Knobs)


# -----------------------------------------------------------------------------
#                                 VA TOOLS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("VA", lambda: None)
# Define el icono para los items de Frame Range
icon_VA = _get_icon("TP_VA")


# Importar el LGA_viewerRec709
import LGA_viewerRec709

n.addCommand(
    "  Viewer Rec709",
    "LGA_viewerRec709.main()",
    "shift+v",
    shortcutContext=2,
    icon=icon_VA,
)


# Importar el LGA_viewer_SnapShot para los shortcuts
import LGA_viewer_SnapShot

n.addCommand(
    "  Take Snapshot",
    "LGA_viewer_SnapShot.take_snapshot(save_to_gallery=True)",
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


# Shortcut para Reset Workspace
n.addCommand(
    "  Reset Workspace",
    "import hiero; hiero.ui.resetCurrentWorkspace()",
    "ctrl+alt+w",
    icon=icon_VA,
)


# Importar el LGA_restartNukeX
import LGA_restartNukeX

n.addCommand(
    "  Restart NukeX",
    "LGA_restartNukeX.check_and_exit(1)",
    "ctrl+alt+shift+Q",
    icon=icon_VA,
)


# -----------------------------------------------------------------------------
#                                 Settings
# -----------------------------------------------------------------------------
n.addSeparator()
import LGA_ToolPack_settings

try:
    icon_Settings = _get_icon("TP_Settings")
except Exception:
    icon_Settings = ""
n.addCommand("Settings", "LGA_ToolPack_settings.main()", icon=icon_Settings)


# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
import webbrowser
import nuke

TP_script_dir = os.path.dirname(os.path.realpath(__file__))
TP_pdf_path = os.path.join(TP_script_dir, "LGA_ToolPack.pdf")

n.addCommand("v2.38", lambda: webbrowser.open("file://" + TP_pdf_path))
