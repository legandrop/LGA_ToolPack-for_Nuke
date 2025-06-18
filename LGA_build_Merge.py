"""
_____________________________________________________________________________

  LGA_build_Merge v1.6 | Lega

  Crea nodos Merge con configuración de máscara predefinida.
  Soporta creación desde un nodo seleccionado o desde la posición del cursor.
  Incluye un Roto y un Blur conectados como máscara al Merge.

  Si hay nodos Merge seleccionados, rota sus operaciones entre:
  over -> mask -> stencil -> over
_____________________________________________________________________________

"""

import nuke
from PySide2.QtGui import QCursor, QMouseEvent
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, QEvent, QPoint


def get_common_variables():
    distanciaY = 30  # Espacio libre entre nodos en la columna derecha
    distanciaX = 130
    dot_width = int(nuke.toNode("preferences")["dot_node_scale"].value() * 12)
    return distanciaX, distanciaY, dot_width


def get_selected_node():
    try:
        selected_node = nuke.selectedNode()
        return selected_node
    except ValueError:
        return None


def simulate_dag_click():
    """Simula un click en el DAG en la posición actual del cursor"""
    widget = QApplication.widgetAt(QCursor.pos())
    if widget:
        cursor_pos = QCursor.pos()
        local_pos = widget.mapFromGlobal(cursor_pos)

        # Mouse press
        press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            local_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        QApplication.sendEvent(widget, press_event)

        # Mouse release
        release_event = QMouseEvent(
            QEvent.MouseButtonRelease,
            local_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        QApplication.sendEvent(widget, release_event)


def find_next_node_in_column(current_node, tolerance_x=120):
    current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
    current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

    all_nodes = [
        n
        for n in nuke.allNodes()
        if n != current_node and n.Class() != "Root" and n.Class() != "BackdropNode"
    ]
    nodo_siguiente_en_columna = None
    distMedia_NodoSiguiente = float("inf")

    for node in all_nodes:
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        if (
            abs(node_center_x - current_node_center_x) <= tolerance_x
            and node_center_y > current_node_center_y
        ):
            distance = node_center_y - current_node_center_y
            if distance > 0 and distance < distMedia_NodoSiguiente:
                distMedia_NodoSiguiente = distance
                nodo_siguiente_en_columna = node

    return nodo_siguiente_en_columna, distMedia_NodoSiguiente


def createMerge():
    # Obtener las variables comunes
    distanciaX, distanciaY, dot_width = get_common_variables()

    # Obtener el nodo seleccionado
    selected_node = get_selected_node()

    # Si no hay nodo seleccionado, simular click en el DAG antes de crear el NoOp
    if selected_node is None:
        simulate_dag_click()

    # Obtener el nodo seleccionado o crear un NoOp si no hay nodo seleccionado
    if selected_node:
        current_node = selected_node
        no_op = None
    if selected_node is None:
        no_op = nuke.createNode("NoOp")
        current_node = no_op

    # Deseleccionar todos los nodos existentes
    for n in nuke.allNodes():
        n.setSelected(False)

    # Crear un nodo Roto a la derecha del nodo seleccionado
    roto = nuke.nodes.Roto()
    roto.setXpos(current_node.xpos() + distanciaX)
    if no_op:
        roto.setYpos(current_node.ypos() + current_node.screenHeight() - distanciaY * 2)
    else:
        roto.setYpos(current_node.ypos() + current_node.screenHeight() + distanciaY * 1)

    # Abrir las propiedades del nodo Roto
    nuke.show(roto)

    # Crear un nodo Blur debajo del Roto
    blur = nuke.nodes.Blur()
    blur.setXpos(roto.xpos())
    blur.setYpos(roto.ypos() + roto.screenHeight() + distanciaY)
    blur.setInput(0, roto)
    blur["channels"].setValue("alpha")
    blur["size"].setValue(7)
    blur["label"].setValue("[value size]")

    # Crear un Dot debajo del Blur
    dot_right = nuke.nodes.Dot()
    dot_right.setXpos(blur.xpos() - (dot_width // 2) + (blur.screenWidth() // 2))
    dot_right.setYpos(blur.ypos() + blur.screenHeight() + distanciaY)
    dot_right.setInput(0, blur)

    # Buscar el nodo siguiente en la columna principal
    nodo_siguiente_en_columna, _ = find_next_node_in_column(current_node)

    # Crear un nodo Merge alineado con el nodo seleccionado en la columna principal
    merge = nuke.nodes.Merge2()
    merge.setXpos(
        current_node.xpos()
        - (merge.screenWidth() // 2)
        + (current_node.screenWidth() // 2)
    )
    merge.setYpos(
        int(
            dot_right.ypos()
            + (dot_right.screenHeight() // 2)
            - (merge.screenHeight() // 2)
        )
    )
    merge["operation"].setValue("mask")
    merge["bbox"].setValue("A")

    # Conectar el nodo Merge al nodo seleccionado
    merge.setInput(0, current_node)

    # Si hay un nodo siguiente en la columna, conectar el nodo Merge entre el nodo seleccionado y el nodo siguiente
    if nodo_siguiente_en_columna:
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == current_node:
                nodo_siguiente_en_columna.setInput(i, merge)
                break

    # Conectar la mascara del nodo Merge al Dot de la columna derecha
    merge.setInput(1, dot_right)

    # Al final de la función, seleccionar solo los nuevos nodos
    roto["selected"].setValue(True)
    blur["selected"].setValue(True)
    dot_right["selected"].setValue(True)
    merge["selected"].setValue(True)

    # Eliminar el NoOp si existe
    if no_op:
        nuke.delete(no_op)


def switch_merge_operations(merge_nodes):
    for node in merge_nodes:
        current_operation = node["operation"].value()

        if current_operation == "over":
            node["operation"].setValue("mask")
            node["bbox"].setValue("A")
        elif current_operation == "mask":
            node["operation"].setValue("stencil")
            node["bbox"].setValue("B")
        elif current_operation == "stencil":
            node["operation"].setValue("over")
            node["bbox"].setValue("B")


def main():
    # Obtener todos los nodos seleccionados
    selected_nodes = nuke.selectedNodes()

    # Filtrar los nodos Merge seleccionados
    merge_nodes = [node for node in selected_nodes if node.Class() == "Merge2"]

    if merge_nodes:
        switch_merge_operations(merge_nodes)
    else:
        createMerge()


# Ejecuta la funcion
# update_merge_operations()
