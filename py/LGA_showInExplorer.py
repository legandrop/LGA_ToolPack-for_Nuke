"""
__________________________________________________________________________________

  LGA_showInExplorer v1.0 | Lega
  Reveals the file location of a selected Read or Write node in Windows Explorer
  Reveals the nuke script if no node is selected
__________________________________________________________________________________

"""

import nuke
import sys
import os


def launch(directory):
    # Open folder
    # print('Attempting to open folder: ' + directory)
    if os.path.exists(directory):
        if sys.platform == "win32":
            os.startfile(directory)
        elif sys.platform == "darwin":
            os.system('open "' + directory + '"')
    else:
        nuke.message("Path does not exist:\n" + directory)


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
            nuke.message("No node selected.")
        except NameError:
            nuke.message("You must select a Read node or a Write node.")
    else:
        # Si no hay nodos seleccionados, abre la ubicacion del proyecto .nk
        projectPath = nuke.root().name()
        if projectPath == "Root":
            nuke.message("No project file found.")
        else:
            projectDirectory = os.path.dirname(projectPath)
            launch(projectDirectory)
