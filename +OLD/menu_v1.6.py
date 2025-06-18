"""
____________________________________________

  LGA_ToolPack v1.6 - 2024 - Lega Pugliese
____________________________________________

"""

import os


def _get_icon(name):
    icons_root = os.path.join(os.path.dirname(__file__), "icons")
    path = os.path.join(icons_root, name) + ".png"
    return path.replace("\\", "/")


# -----------------------------------------------------------------------------
#                              READ n WRITE TOOLS
# -----------------------------------------------------------------------------

# Crea el menu "TP" (ToolPack)
n = nuke.menu("Nuke").addMenu("TP", icon=_get_icon("LGA"))
# Agrega el comando "NODE GRAPH" al menu "TP"
n.addCommand("READ n WRITE", lambda: None)


# Importar el LGA_mediaManager
import LGA_mediaManager

n.addCommand("  Media Manager", "LGA_mediaManager.main()", "ctrl+m", shortcutContext=2)


# Importar el LGA_mediaPathReplacer
import LGA_mediaPathReplacer

n.addCommand(
    "  Media Path Replacer",
    "LGA_mediaPathReplacer.show_search_replace_widget()",
    "ctrl+alt+m",
    shortcutContext=2,
)


# Importar el LGA_mediaMissingFrames
import LGA_mediaMissingFrames

n.addCommand(
    "  Media Missing Frames",
    "LGA_mediaMissingFrames.main()",
    "ctrl+alt+shift+m",
    shortcutContext=2,
)


# Importar el readFromWrite
import readFromWrite

n.addCommand(
    "  Read from Write", "readFromWrite.ReadFromWrite()", "shift+r", shortcutContext=2
)


# Importar el LGA_Write_RenderComplete y el LGA_Write_SendMail
import LGA_Write_RenderComplete
import LGA_Write_SendMail


def add_send_mail_to_all_writes():
    LGA_Write_SendMail.add_send_mail_checkbox()


n.addCommand(
    "  Write Send Mail", "add_send_mail_to_all_writes()", "shift+w", shortcutContext=2
)


# Importar el LGA_reloadAllReads
import LGA_reloadAllReads

n.addCommand(
    "  Reload all Reads",
    "LGA_reloadAllReads.reload_all_read_nodes()",
    "ctrl+alt+shift+r",
    shortcutContext=2,
)


# Importar el LGA_revealExplorer
import LGA_revealExplorer

n.addCommand(
    "  Reveal in Explorer",
    "LGA_revealExplorer.LGA_revealExplorer()",
    "shift+e",
    shortcutContext=2,
)


# Importar el LGA_revealFlow
import LGA_revealFlow

n.addCommand(
    "  Reveal in Flow", "LGA_revealFlow.main()", "ctrl+shift+e", shortcutContext=2
)


# Importar el LGA_renameWritesFromReads
import LGA_renameWritesFromReads

n.addCommand(
    "  Rename Writes from Reads",
    "LGA_renameWritesFromReads.renameWrite()",
    "F2",
    shortcutContext=2,
)


# Importar el LGA_ocio_RnW
import LGA_ocio_RnW

n.addCommand(
    "  OCIO Output Transform", "LGA_ocio_RnW.main()", "shift+o", shortcutContext=2
)


# -----------------------------------------------------------------------------
#                                FRAME RANGE
# -----------------------------------------------------------------------------
# Crear separador
n.addSeparator()
n.addCommand("FRAME RANGE", lambda: None)


# Importar el LGA_fr_Read_to_FrameRange
import LGA_fr_Read_to_FrameRange

n.addCommand(
    "  Read -> FrameRange",
    "LGA_fr_Read_to_FrameRange.set_frame_range_from_read()",
    "ctrl+alt+f",
    shortcutContext=2,
)


# Importar el LGA_fr_Read_to_Write
import LGA_fr_Read_to_Write

n.addCommand("  Read -> Write", "LGA_fr_Read_to_Write.Writes_FrameRange()")


# Importar el LGA_fr_Read_to_Project
import LGA_fr_Read_to_Project

n.addCommand(
    "  Read -> Project", "LGA_fr_Read_to_Project.main()", "shift+f", shortcutContext=2
)


# Importar el LGA_fr_TimeClip_to_Write
import LGA_fr_TimeClip_to_Write

n.addCommand(
    "  TimeClip -> Write",
    "LGA_fr_TimeClip_to_Write.set_write_from_timeclip()",
    "ctrl+t",
    shortcutContext=2,
)


# -----------------------------------------------------------------------------
#                                   OCIO
# -----------------------------------------------------------------------------
# Crear separador
n.addSeparator()
n.addCommand("OCIO", lambda: None)


# Importar el LGA_viewerRec709
import LGA_viewerRec709

n.addCommand(
    "  Rec709 | Viewer", "LGA_viewerRec709.main()", "shift+v", shortcutContext=2
)


# -----------------------------------------------------------------------------
#                              ROTATE TRANSFORM
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("ROTATE TRANSFORM", lambda: None)


# Importar el Lg_Rotate_Shortcut
import LGA_rotateShortcuts

n.addCommand(
    "  Rotate - Left (0.1)", "LGA_rotateShortcuts.increment_rotate(0.1)", "Ctrl+/"
)
n.addCommand(
    "  Rotate - Left (1)", "LGA_rotateShortcuts.increment_rotate(1)", "Ctrl+Shift+/"
)
n.addCommand(
    "  Rotate - Right (-0.1)", "LGA_rotateShortcuts.increment_rotate(-0.1)", "Ctrl+*"
)
n.addCommand(
    "  Rotate - Right (-1)", "LGA_rotateShortcuts.increment_rotate(-1)", "Ctrl+Shift+*"
)


# -----------------------------------------------------------------------------
#                                 VA TOOLS
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("VA", lambda: None)


# Importar el LGA_switchMergeOperations
import LGA_switchMergeOperations

n.addCommand(
    "  Switch Merge Ops",
    "LGA_switchMergeOperations.update_merge_operations()",
    "shift+m",
    shortcutContext=2,
)

# Importar cargar el PasteToSelected
import pasteToSelected

n.addCommand(
    "  Paste To Selected",
    "pasteToSelected.pasteToSelected()",
    "ctrl+shift+v",
    shortcutContext=2,
)


# Importar cargar el duplicateWithInputs
import duplicateWithInputs

n.addCommand(
    "  Copy with inputs",
    "duplicateWithInputs.copyWithInputs()",
    "ctrl+alt+c",
    shortcutContext=2,
)
n.addCommand(
    "  Paste with inputs",
    "duplicateWithInputs.pasteWithInputs()",
    "ctrl+alt+v",
    shortcutContext=2,
)
n.addCommand(
    "  Duplicate with inputs",
    "duplicateWithInputs.duplicateWithInputs()",
    "ctrl+alt+k",
    shortcutContext=2,
)


# Shortcut para Reset Workspace
n.addCommand(
    "  Reset Workspace", "import hiero; hiero.ui.resetCurrentWorkspace()", "ctrl+alt+w"
)


# Importar el MultiKnobTool con shortcut F12
import wbMultiKnobEdit

n.addCommand("  Multi Knob Edit", "wbMultiKnobEdit.multiEditExec()", "F12")


# Importar Performance timers en el menu TP y como un Panel
import perf_time

n.addCommand("  Performance Timers", "perf_time.show_panel()")
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

n.addCommand("  Edit Keyboard Shortcuts", gui)


# Importar Default (para definir los valores por defecto de los Nodos)
from default.default import default_main
from default.default import helper
from default.default import about

n.addCommand("  Edit Default Knobs Values", default_main.show_defaults_window)
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


# Importar el animation maker
import AnimationMaker


# Importar el cmdLaunch
import cmdLaunch


# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()
n.addCommand("v1.6", lambda: nuke.message("ToolPack v1.6 - Lega - 2024"))
