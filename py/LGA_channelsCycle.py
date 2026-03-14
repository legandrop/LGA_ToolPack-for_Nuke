"""
_____________________________________________________________________________________________________

  LGA_channelsCycle v1.1 - Lega
  Cambia el valor del knob 'channels' de un nodo seleccionado rotando entre 'rgb', 'alpha' y 'rgba'
_____________________________________________________________________________________________________

"""

import nuke

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def main():
    def change_channels_knob(node):
        if "channels" in node.knobs():
            channels_knob = node["channels"]
            current_value = channels_knob.value()

            # Lista de valores permitidos
            channels_values = ["rgb", "alpha", "rgba"]

            # Determina el siguiente valor en la rotacion
            if current_value in channels_values:
                next_value_index = (channels_values.index(current_value) + 1) % len(
                    channels_values
                )
                next_value = channels_values[next_value_index]
            else:
                # Si el valor actual no esta en la lista, se resetea a 'rgb'
                next_value = "rgb"

            # Asigna el siguiente valor
            channels_knob.setValue(next_value)
            debug_print(f"El knob 'channels' ha cambiado a: {next_value}")
            return True
        return False

    # Verifica si hay un nodo seleccionado
    selected_node = None
    try:
        selected_node = nuke.selectedNode()
    except ValueError:
        pass

    if selected_node:
        if change_channels_knob(selected_node):
            return
        else:
            debug_print("El nodo seleccionado no tiene un knob 'channels'.")

    # Si no hay nodo seleccionado o el nodo no tiene 'channels', busca en nodos abiertos en el panel de propiedades
    debug_print("Buscando en los nodos del panel de propiedades...")
    for node in nuke.allNodes():
        if node.shown():  # Verifica si el nodo esta en el panel de propiedades
            if change_channels_knob(node):
                return

    debug_print(
        "No se encontro ningun nodo con un knob 'channels' abierto en el panel de propiedades."
    )


# Ejecuta la funcion
# main()
