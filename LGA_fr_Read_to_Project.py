"""
________________________________________________________________

  LGA_fr_Read_to_Project v1.0 | Lega
  Copia el frame range del nodo Read seleccionado al proyecto.
________________________________________________________________


"""

import nuke


def main():
    # Obtener el nodo Read seleccionado
    selected_node = nuke.selectedNode()

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
