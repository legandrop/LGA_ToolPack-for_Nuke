"""
________________________________________________________________

  LGA_fr_Read_to_Project v1.01 | Lega
  Copia el frame range del nodo Read seleccionado al proyecto.

  v1.01: Sin nada seleccionado en el Node Graph ya no toma un nodo seleccionado
         adentro de un grupo o gizmo (LGA_ToolPack_Selection). Sin
         seleccion no hace nada, en vez de tirar un ValueError.
________________________________________________________________


"""

import nuke
from LGA_ToolPack_Selection import selected_node as graph_selected_node


def main():
    # Obtener el nodo Read seleccionado
    try:
        selected_node = graph_selected_node()
    except ValueError:
        selected_node = None

    if selected_node is None:
        # nuke.message("Por favor, selecciona un nodo Read.")
        return

    # Obtener el rango de frames del nodo Read seleccionado
    frame_range = selected_node["first"].value(), selected_node["last"].value()

    # Establecer el rango de frames del proyecto a partir del nodo Read seleccionado
    nuke.root()["first_frame"].setValue(frame_range[0])
    nuke.root()["last_frame"].setValue(frame_range[1])


# Ejecutar la funcion
# main()
