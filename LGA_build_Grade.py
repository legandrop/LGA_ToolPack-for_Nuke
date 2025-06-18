"""
_____________________________________________________________________________

  LGA_build_Grade v1.62 | Lega

  Crea nodos Grade con diferentes configuraciones de máscaras.
  Soporta creación desde un nodo seleccionado o desde la posición del cursor.
  Incluye dos modos: Grade con máscara de luminancia y Grade con Roto.
_____________________________________________________________________________

"""

import nuke
from PySide2.QtGui import QCursor, QMouseEvent
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, QEvent, QPoint

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


# Variables comunes
def get_common_variables():
    distanciaY = 20  # Espacio libre entre nodos en la columna derecha
    distanciaX = 130
    # Valor predeterminado por si el nodo preferences no existe
    DEFAULT_DOT_WIDTH = 12
    # Intentar obtener dot_width desde las preferencias, usar valor predeterminado si falla
    prefs_node = nuke.toNode("preferences")
    if prefs_node and "dot_node_scale" in prefs_node.knobs():
        dot_width = int(prefs_node["dot_node_scale"].value() * 12)
    else:
        dot_width = DEFAULT_DOT_WIDTH  # Usar valor predeterminado
    return distanciaX, distanciaY, dot_width


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


# Funcion para obtener el nodo seleccionado
def get_selected_node():
    try:
        selected_node = nuke.selectedNode()
        debug_print(
            f"Nodo seleccionado: {selected_node.name()} ({selected_node.Class()}) id={id(selected_node)}"
        )
        return selected_node, None
    except ValueError:
        # Simular click en el DAG antes de crear el NoOp
        simulate_dag_click()
        no_op = nuke.createNode("NoOp")
        debug_print(
            f"No hay nodo seleccionado. Se crea NoOp temporal: {no_op.name()} id={id(no_op)}"
        )
        return no_op, no_op


# Funcion para encontrar el nodo siguiente en la columna
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

    if nodo_siguiente_en_columna:
        debug_print(
            f"Nodo siguiente en columna: {nodo_siguiente_en_columna.name()} ({nodo_siguiente_en_columna.Class()}) id={id(nodo_siguiente_en_columna)} a distancia {distMedia_NodoSiguiente}"
        )
    else:
        debug_print("No se encontro nodo siguiente en columna.")
    return nodo_siguiente_en_columna, distMedia_NodoSiguiente


# Funcion principal GradeHI
def gradeHI():
    # Obtener las variables comunes
    distanciaX, distanciaY, dot_width = get_common_variables()

    # Guardar el nodo seleccionado antes de deseleccionar todo
    selected_node, no_op = get_selected_node()

    # Deseleccionar todos los nodos
    for n in nuke.allNodes():
        n.setSelected(False)

    current_node = selected_node

    # Buscar el primer nodo que este debajo del nodo seleccionado con una tolerancia en X
    nodo_siguiente_en_columna, distMedia_NodoSiguiente = find_next_node_in_column(
        current_node
    )

    # Ajustar la distancia Y si es necesario
    if (
        distMedia_NodoSiguiente != float("inf")
        and distMedia_NodoSiguiente < distanciaY * 2
    ):
        distanciaY = distMedia_NodoSiguiente / 2 - (dot_width / 2) - 6

    # Crear el Dot a la derecha del primer Dot
    dot_below = nuke.nodes.Dot()
    dot_below.setXpos(
        int(current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2))
    )
    if no_op:
        dot_below.setYpos(
            int(current_node.ypos() + current_node.screenHeight() - distanciaY * 2)
        )
    else:
        dot_below.setYpos(
            int(current_node.ypos() + current_node.screenHeight() + distanciaY * 3)
        )

    dot_below.setInput(0, current_node)

    if (
        nodo_siguiente_en_columna
        and current_node in nodo_siguiente_en_columna.dependencies(nuke.INPUTS)
    ):
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == current_node:
                nodo_siguiente_en_columna.setInput(i, dot_below)
                break

    # Crear el Dot a la derecha del primer Dot
    dot_right = nuke.nodes.Dot()
    dot_right.setXpos(dot_below.xpos() + distanciaX)
    dot_right.setYpos(dot_below.ypos())
    dot_right.setInput(0, dot_below)

    # Crear un Keyer debajo del Dot derecho
    keyer = nuke.nodes.Keyer(operation="luminance key")
    keyer.setXpos(dot_right.xpos() - (keyer.screenWidth() // 2) + (dot_width // 2))
    keyer.setYpos(int(dot_right.ypos() + dot_right.screenHeight() + distanciaY))
    keyer.setInput(0, dot_right)

    # Crear un Shuffle debajo del Keyer
    shuffle = nuke.nodes.Shuffle2(label="[value in1] --> [value out1]")
    shuffle.setXpos(keyer.xpos())
    shuffle.setYpos(int(keyer.ypos() + keyer.screenHeight() + distanciaY))
    shuffle.setInput(0, keyer)

    # Definir las nuevas conexiones (mappings)
    mappings = [
        ("rgba.alpha", "rgba.red"),
        ("rgba.alpha", "rgba.green"),
        ("rgba.alpha", "rgba.blue"),
        ("rgba.alpha", "rgba.alpha"),
    ]
    # Aplicar las conexiones al nodo Shuffle
    shuffle["mappings"].setValue(mappings)

    # Crear un Dot debajo del Shuffle
    dot_bottom = nuke.nodes.Dot()
    dot_bottom.setXpos(shuffle.xpos() - (dot_width // 2) + (shuffle.screenWidth() // 2))
    dot_bottom.setYpos(int(shuffle.ypos() + shuffle.screenHeight() + distanciaY))
    dot_bottom.setInput(0, shuffle)

    # Crear un Grade debajo del primer Dot y conectarlo
    grade = nuke.nodes.Grade()
    grade.setXpos(dot_below.xpos() - (grade.screenWidth() // 2) + (dot_width // 2))
    grade.setYpos(
        int(
            dot_bottom.ypos()
            + (dot_bottom.screenHeight() // 2)
            - (grade.screenHeight() // 2)
        )
    )
    grade.setInput(0, dot_below)
    grade.setInput(1, dot_bottom)  # Conectar la mascara al ultimo Dot

    if nodo_siguiente_en_columna:
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == dot_below:
                nodo_siguiente_en_columna.setInput(i, grade)
                break

    # Borrar noOp si existe
    if no_op:
        nuke.delete(no_op)

    # Seleccionar los nodos creados
    for node in [dot_below, dot_right, keyer, shuffle, dot_bottom, grade]:
        node.setSelected(True)

    # Abrir el panel de propiedades del nodo Grade y Keyer
    grade.showControlPanel()
    keyer.showControlPanel()


def gradeMask():
    # Obtener las variables comunes
    distanciaX, distanciaY, dot_width = get_common_variables()

    # Guardar el nodo seleccionado antes de deseleccionar todo
    selected_node, no_op = get_selected_node()

    # Deseleccionar todos los nodos
    for n in nuke.allNodes():
        n.setSelected(False)

    current_node = selected_node
    debug_print(
        f"\n[gradeMask] Nodo base para arbol: {current_node.name()} ({current_node.Class()}) id={id(current_node)}"
    )

    # Crear un nodo Roto a la derecha del nodo seleccionado
    roto = nuke.nodes.Roto()
    roto.setXpos(current_node.xpos() + distanciaX)
    if no_op:
        roto.setYpos(current_node.ypos() + current_node.screenHeight() - distanciaY * 2)
    else:
        roto.setYpos(
            int(current_node.ypos() + current_node.screenHeight() + distanciaY)
        )

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

    # Crear un nodo Grade alineado con el nodo seleccionado en la columna principal
    grade = nuke.nodes.Grade()
    grade.setXpos(
        current_node.xpos()
        - (grade.screenWidth() // 2)
        + (current_node.screenWidth() // 2)
    )
    grade.setYpos(
        int(
            dot_right.ypos()
            + (dot_right.screenHeight() // 2)
            - (grade.screenHeight() // 2)
        )
    )

    debug_print(f"[gradeMask] Se crea Grade: {grade.name()} id={id(grade)}")
    debug_print(
        f"[gradeMask] Conectando input 0 del Grade a {current_node.name()} id={id(current_node)}"
    )
    grade.setInput(0, current_node)
    debug_print(
        f"[gradeMask] Grade input 0 ahora es: {grade.input(0).name() if grade.input(0) is not None else 'None'} id={id(grade.input(0)) if grade.input(0) is not None else 'None'}"
    )

    # Si hay un nodo siguiente en la columna, conectar el nodo Grade entre el nodo seleccionado y el nodo siguiente
    if nodo_siguiente_en_columna:
        debug_print(
            f"[gradeMask] Nodo siguiente detectado: {nodo_siguiente_en_columna.name()} ({nodo_siguiente_en_columna.Class()}) id={id(nodo_siguiente_en_columna)}"
        )
        for i in range(nodo_siguiente_en_columna.inputs()):
            input_node = nodo_siguiente_en_columna.input(i)
            debug_print(
                f"[gradeMask]   Input {i} del nodo siguiente es: {input_node.name() if input_node is not None else 'None'} id={id(input_node) if input_node is not None else 'None'}"
            )
            if input_node == current_node:
                debug_print(
                    f"[gradeMask]   Reemplazando input {i} del nodo siguiente por el Grade..."
                )
                nodo_siguiente_en_columna.setInput(i, grade)
                new_input = nodo_siguiente_en_columna.input(i)
                debug_print(
                    f"[gradeMask]   Ahora input {i} del nodo siguiente es: {new_input.name() if new_input is not None else 'None'} id={id(new_input) if new_input is not None else 'None'}"
                )
                break
    else:
        debug_print(
            "[gradeMask] No hay nodo siguiente en la columna para conectar el output del Grade."
        )

    # Conectar la mascara del nodo Grade al Dot de la columna derecha
    debug_print(
        f"[gradeMask] Conectando input 1 del Grade a {dot_right.name()} id={id(dot_right)}"
    )
    grade.setInput(1, dot_right)
    debug_print(
        f"[gradeMask] Grade input 1 ahora es: {grade.input(1).name() if grade.input(1) is not None else 'None'} id={id(grade.input(1)) if grade.input(1) is not None else 'None'}"
    )

    # Borrar noOp si existe
    if no_op:
        debug_print(
            f"[gradeMask] Borrando NoOp temporal: {no_op.name()} id={id(no_op)}"
        )
        nuke.delete(no_op)

    # Seleccionar los nodos creados
    for node in [roto, blur, dot_right, grade]:
        node.setSelected(True)

    # Abrir el panel de propiedades del nodo Grade y Roto
    grade.showControlPanel()
    roto.showControlPanel()
