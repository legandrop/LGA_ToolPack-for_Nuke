"""
_____________________________________________________________________________

  LGA_build_Roto v1.13 | Lega

  Crea nodos Roto, Blur y Dot conectados al input mask del nodo Merge (llamado Merge2 en Nuke) o al input 1 de cualquier otro nodo.
  Requiere que haya un nodo seleccionado para funcionar.
  Diseñado para añadir rápidamente máscaras a nodos existentes.
_____________________________________________________________________________

"""

import nuke
from qt_compat import QtGui, QtWidgets, QtCore

QCursor = QtGui.QCursor
QMouseEvent = QtGui.QMouseEvent
QApplication = QtWidgets.QApplication
Qt = QtCore.Qt
QEvent = QtCore.QEvent
QPoint = QtCore.QPoint


def get_common_variables():
    distanciaY = 30  # Espacio libre entre nodos en la columna derecha
    distanciaX = 130
    # Evitar error de "None is not subscriptable"
    try:
        preferences = nuke.toNode("preferences")
        if preferences and preferences.knob("dot_node_scale"):
            dot_width = int(preferences["dot_node_scale"].value() * 12)
        else:
            dot_width = 12  # Valor por defecto si no podemos obtener las preferencias
    except:
        dot_width = 12  # Valor por defecto en caso de error
    return distanciaX, distanciaY, dot_width


def get_selected_node():
    try:
        selected_node = nuke.selectedNode()
        return selected_node
    except ValueError:
        return None


def get_mask_input_and_prepare(node):
    """
    Si el nodo es Merge2, asegura que los inputs B y A estén ocupados (crea NoOps temporales si es necesario)
    y devuelve el índice del input mask (2). Para cualquier otro nodo, devuelve 1 (input clásico de máscara).
    Devuelve: (mask_input_index, lista_noops_temporales)
    """
    if node.Class() == "Merge2":
        temp_nodes = []
        # Si B está vacío, conectar un NoOp temporal
        if node.input(0) is None:
            temp_b = nuke.nodes.NoOp()
            temp_b.setXpos(node.xpos() - 100)
            temp_b.setYpos(node.ypos() - 100)
            node.setInput(0, temp_b)
            temp_nodes.append((0, temp_b))
        # Si A está vacío, conectar un NoOp temporal
        if node.input(1) is None:
            temp_a = nuke.nodes.NoOp()
            temp_a.setXpos(node.xpos() + 100)
            temp_a.setYpos(node.ypos() - 100)
            node.setInput(1, temp_a)
            temp_nodes.append((1, temp_a))
        return 2, temp_nodes
    elif node.Class() == "Keymix":
        return 2, []
    else:
        return 1, []


def create_roto_chain():
    """Crea una cadena de nodos Roto, Blur y Dot conectada al input adecuado del nodo seleccionado"""
    distanciaX, distanciaY, dot_width = get_common_variables()
    selected_node = get_selected_node()
    if not selected_node:
        nuke.message("Selecciona un nodo primero")
        return

    for n in nuke.allNodes():
        n.setSelected(False)

    dot_right = nuke.nodes.Dot()
    dot_right.setXpos(
        selected_node.xpos()
        + distanciaX
        + (selected_node.screenWidth() // 2)
        - (dot_width // 2)
    )
    dot_right.setYpos(
        selected_node.ypos()
        + (selected_node.screenHeight() // 2)
        - (dot_right.screenHeight() // 2)
    )

    blur = nuke.nodes.Blur()
    blur.setXpos(dot_right.xpos() - (blur.screenWidth() // 2) + (dot_width // 2))
    blur.setYpos(dot_right.ypos() - blur.screenHeight() - distanciaY)
    blur["channels"].setValue("alpha")
    blur["size"].setValue(7)
    blur["label"].setValue("[value size]")
    dot_right.setInput(0, blur)

    roto = nuke.nodes.Roto()
    roto.setXpos(blur.xpos())
    roto.setYpos(blur.ypos() - roto.screenHeight() - distanciaY)
    blur.setInput(0, roto)
    nuke.show(roto)

    # Selección de input y preparación especial para Merge2
    mask_input, temp_nodes = get_mask_input_and_prepare(selected_node)
    selected_node.setInput(mask_input, dot_right)

    # Borrar NoOps temporales si siguen conectados
    for idx, temp_node in temp_nodes:
        if selected_node.input(idx) == temp_node:
            selected_node.setInput(idx, None)
            nuke.delete(temp_node)

    roto["selected"].setValue(True)
    blur["selected"].setValue(True)
    dot_right["selected"].setValue(True)


def main():
    create_roto_chain()


# Ejecuta la funcion
# main()
