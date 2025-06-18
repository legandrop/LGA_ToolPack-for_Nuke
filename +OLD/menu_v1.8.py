"""
___________________________________

  LGA_ToolPack v1.8 | 2024 | Lega
___________________________________

"""

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
# Agrega el comando "NODE GRAPH" al menu "TP"
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


# Importar el LGA_mediaMissingFrames
import LGA_mediaMissingFrames

n.addCommand(
    "  Media Missing Frames",
    "LGA_mediaMissingFrames.main()",
    "ctrl+alt+shift+m",
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


# Importar el LGA_preRender
import LGA_preRender

n.addCommand(
    "  preRender", "LGA_preRender.main()", "shift+p", shortcutContext=2, icon=icon_RnW
)


# Importar el LGA_Write_RenderComplete y el LGA_Write_SendMail
import LGA_Write_RenderComplete
import LGA_Write_SendMail


def add_send_mail_to_all_writes():
    LGA_Write_SendMail.add_send_mail_checkbox()


n.addCommand(
    "  Write Send Mail",
    "add_send_mail_to_all_writes()",
    "shift+w",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_reloadAllReads
import LGA_reloadAllReads

n.addCommand(
    "  Reload all Reads",
    "LGA_reloadAllReads.main()",
    "ctrl+alt+shift+r",
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


# Importar el LGA_renameWritesFromReads
import LGA_renameWritesFromReads

n.addCommand(
    "  Rename Writes from Reads",
    "LGA_renameWritesFromReads.renameWrite()",
    "F2",
    shortcutContext=2,
    icon=icon_RnW,
)


# Importar el LGA_ocio_RnW
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


# Importar el LGA_fr_Read_to_FrameRange
import LGA_fr_Read_to_FrameRange

n.addCommand(
    "  Read -> FrameRange",
    "LGA_fr_Read_to_FrameRange.set_frame_range_from_read()",
    "ctrl+alt+f",
    shortcutContext=2,
    icon=icon_FR,
)


# Importar el LGA_fr_Read_to_Write
import LGA_fr_Read_to_Write

n.addCommand(
    "  Read -> Write",
    "LGA_fr_Read_to_Write.Writes_FrameRange()",
    shortcutContext=2,
    icon=icon_FR,
)


# Importar el LGA_fr_Read_to_Project
import LGA_fr_Read_to_Project

n.addCommand(
    "  Read -> Project",
    "LGA_fr_Read_to_Project.main()",
    "shift+f",
    shortcutContext=2,
    icon=icon_FR,
)


# Importar el LGA_fr_TimeClip_to_Write
import LGA_fr_TimeClip_to_Write

n.addCommand(
    "  TimeClip -> Write",
    "LGA_fr_TimeClip_to_Write.set_write_from_timeclip()",
    "ctrl+t",
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
n.addCommand("KNOBS", lambda: None)
# Define el icono para los items de Frame Range
icon_Knobs = _get_icon("TP_Knobs")


# Importar el LGA_merge
import LGA_merge

n.addCommand(
    "  Create Merge | Switch ops",
    "LGA_merge.main()",
    "shift+m",
    shortcutContext=2,
    icon=icon_Knobs,
)


# Importar el LGA_grade
import LGA_grade

n.addCommand(
    "  Create Grade + Mask",
    "LGA_grade.gradeMask()",
    "shift+G",
    shortcutContext=2,
    icon=icon_Knobs,
)
n.addCommand(
    "  Create Grade + High",
    "LGA_grade.gradeHI()",
    "ctrl+shift+G",
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


# Importar el animation maker
import AnimationMaker

n.addCommand(
    "  Animation Maker",
    lambda: nuke.message("Right click on any knob and select Animation Maker"),
    icon=icon_Knobs,
)


# Importar el MultiKnobTool con shortcut F12
import wbMultiKnobEdit

n.addCommand(
    "  Multi Knob Edit", "wbMultiKnobEdit.multiEditExec()", "F12", icon=icon_Knobs
)


# Importar Default (para definir los valores por defecto de los Nodos)
from default.default import default_main
from default.default import helper
from default.default import about

n.addCommand(
    "  Edit Default Knobs Values", default_main.show_defaults_window, icon=icon_Knobs
)
# Add commands to animation menu.
nuke.menu("Animation").addCommand(
    "default/set as new knobDefault", "default_main.create_default()"
)
nuke.menu("Animation").addCommand(
    "default/show knob list", "default_main.show_knob_list()"
)
nuke.menu("Animation").addCommand("default/reset", "default_main.reset_to_default()")
# Auto load knob defaults when launching.
helper.load_knob_defaults(init=True)


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


# Importar el LGA_CDL_CC_IP
import LGA_CDL_CC_IP

n.addCommand(
    "  CDL -> CC Input Process",
    "LGA_CDL_CC_IP.main()",
    "ctrl+alt+shift+i",
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


# Importar Performance timers en el menu TP y como un Panel
import perf_time

n.addCommand("  Performance Timers", "perf_time.show_panel()", icon=icon_VA)
pane_m = nuke.menu("Pane")
pane_m.addCommand("Performance Timers", perf_time.add_perf_time_panel)
nukescripts.registerPanel("com.lega.perfTime", perf_time.add_perf_time_panel)


# Importar el shortcut editor
try:
    import shortcuteditor

    shortcuteditor.nuke_setup()
except Exception:
    import traceback

    traceback.print_exc()
from shortcuteditor import gui

n.addCommand("  Edit Keyboard Shortcuts", gui, icon=icon_VA)


# Importar el LGA_restartNukeX
import LGA_restartNukeX

n.addCommand(
    "  Restart NukeX",
    "LGA_restartNukeX.check_and_exit(1)",
    "ctrl+alt+shift+Q",
    icon=icon_VA,
)


# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()

import webbrowser
import nuke

TP_script_dir = os.path.dirname(os.path.realpath(__file__))
TP_pdf_path = os.path.join(TP_script_dir, "LGA_ToolPack.pdf")

n.addCommand("v1.8", lambda: webbrowser.open("file://" + TP_pdf_path))
