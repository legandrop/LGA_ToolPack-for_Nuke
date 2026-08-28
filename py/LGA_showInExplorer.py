"""
__________________________________________________________________________________

  LGA_showInExplorer v1.01 | Lega
  Reveals the file location of a selected Read or Write node in Windows Explorer
  Reveals the nuke script if no node is selected

  v1.01: Los nuke.message pasan al helper LGA_UI_MessageBox_ToolPack
         (show_warning), con fallback a nuke.message.
__________________________________________________________________________________

"""

import nuke
import sys
import os


def _aviso(texto):
    """Cartel estilado del pack; si el helper falla cae a nuke.message."""
    try:
        from LGA_UI_MessageBox_ToolPack import show_warning

        show_warning(None, "Show in Explorer", texto)
    except Exception:
        nuke.message(texto)


def launch(directory):
    # Open folder
    # print('Attempting to open folder: ' + directory)
    if os.path.exists(directory):
        if sys.platform == "win32":
            os.startfile(directory)
        elif sys.platform == "darwin":
            os.system('open "' + directory + '"')
    else:
        _aviso("Path does not exist:\n" + directory)


def main():
    # Verifica si hay algun nodo seleccionado
    if nuke.selectedNodes():
        try:
            selectedNodeFilePath = nuke.callbacks.filenameFilter(
                nuke.selectedNode()["file"].evaluate()
            )
            folderPath = selectedNodeFilePath[: selectedNodeFilePath.rfind("/")]
            launch(folderPath)
        except ValueError:
            _aviso("No node selected.")
        except NameError:
            _aviso("You must select a Read node or a Write node.")
    else:
        # Si no hay nodos seleccionados, abre la ubicacion del proyecto .nk
        projectPath = nuke.root().name()
        if projectPath == "Root":
            _aviso("No project file found.")
        else:
            projectDirectory = os.path.dirname(projectPath)
            launch(projectDirectory)
