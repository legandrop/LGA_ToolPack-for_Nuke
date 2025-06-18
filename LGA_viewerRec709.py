"""
______________________________________

  LGA_viewerRec709 v1.0 | Lega
______________________________________

"""

import nuke


def main():
    # Obtener todos los viewers del proyecto
    viewers = [node for node in nuke.allNodes() if node.Class() == "Viewer"]

    if not viewers:
        # nuke.message("No se encontraron viewers en el proyecto.")
        return

    # Iterar sobre cada viewer y establecer el view transform a Rec.709 (ACES)
    for viewer in viewers:
        viewer["viewerProcess"].setValue("Rec.709 (ACES)")


# Ejecutar la funcion
# main()
