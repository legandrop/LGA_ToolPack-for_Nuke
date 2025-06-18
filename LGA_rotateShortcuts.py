"""
_____________________________________________________________

  LGA_rotateShorcut v1.2 | Lega
  Rotates selected nodes by a user-defined amount if they have a 'rotate' knob
_____________________________________________________________

"""

import nuke


# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def increment_rotate(increment):
    def rotate_node(node):
        # Verifica si el nodo tiene el knob 'rotate'
        if "rotate" in node.knobs():
            rotate_knob = node["rotate"]
            rotate_value = rotate_knob.value()
            rotate_knob.setValue(rotate_value + increment)
            debug_print(f"El nodo {node.name()} ha sido rotado en {increment} grados.")
            return True
        return False

    # Verifica si hay un nodo seleccionado
    selected_node = None
    try:
        selected_node = nuke.selectedNode()
    except ValueError:
        pass

    if selected_node:
        if rotate_node(selected_node):
            return
        else:
            debug_print("El nodo seleccionado no tiene el knob 'Rotate'.")

    # Si no hay nodo seleccionado o el nodo no tiene 'Rotate', busca en los nodos abiertos en el panel de propiedades
    debug_print("Buscando en los nodos del panel de propiedades...")
    for node in nuke.allNodes():
        if node.shown():  # Verifica si el nodo esta en el panel de propiedades
            if rotate_node(node):
                return

    debug_print(
        "No se encontro ningun nodo con un knob 'Rotate' abierto en el panel de propiedades."
    )
