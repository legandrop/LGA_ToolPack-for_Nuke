"""
__________________________________________________________

  LGA_build_iteration v1.23 | Lega
  Genera un arbol de nodos usado para generar variaciones
  de una imagen.

  Si no hay nodo seleccionado, crea el árbol de nodos
  en la posición del cursor.
__________________________________________________________

"""

import nuke
from qt_compat import QtGui, QtWidgets, QtCore

QCursor = QtGui.QCursor
QMouseEvent = QtGui.QMouseEvent
QApplication = QtWidgets.QApplication
Qt = QtCore.Qt
QEvent = QtCore.QEvent
QPoint = QtCore.QPoint

# Variable global para activar o desactivar los prints
DEBUG = False

# Valor predeterminado por si el nodo preferences no existe
DEFAULT_DOT_WIDTH = 12


def debug_print(message):
    if DEBUG:
        print(message)


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


def gen_iteration():
    # Distancia entre nodos
    distanciaY = 70
    distanciaY_columna_lateral = (
        30  # Distancia vertical entre nodos en la columna lateral
    )
    distanciaX = -140  # Distancia fija a la izquierda (versión lejana)

    # Intentar obtener dot_width desde las preferencias, usar valor predeterminado si falla
    prefs_node = nuke.toNode("preferences")
    if prefs_node and "dot_node_scale" in prefs_node.knobs():
        dot_width = int(prefs_node["dot_node_scale"].value() * 12)
    else:
        dot_width = DEFAULT_DOT_WIDTH  # Usar valor predeterminado

    # Obtener el nodo seleccionado
    selected_node = None
    no_op = None

    try:
        selected_node = nuke.selectedNode()
    except ValueError:
        # Si no hay nodo seleccionado, simular click en el DAG antes de crear el NoOp
        simulate_dag_click()

        # Crear un NoOp en la posición del cursor, pero más arriba para que el dot quede en la posición del cursor
        no_op = nuke.createNode("NoOp")

        # Ajustar la posición vertical del NoOp para que el dot quede cerca de donde estaba el cursor
        no_op.setYpos(no_op.ypos() - distanciaY)

        selected_node = no_op

    debug_print(f"Nodo seleccionado/creado: {selected_node.name()}")

    pos_tolerance = 120  # Tolerancia para la posicion en X
    current_node_center_x = selected_node.xpos() + (selected_node.screenWidth() / 2)
    current_node_center_y = selected_node.ypos() + (selected_node.screenHeight() / 2)

    # Buscar el primer nodo que este debajo del nodo seleccionado con una tolerancia en X
    all_nodes = [
        n
        for n in nuke.allNodes()
        if n != selected_node and n.Class() != "Root" and n.Class() != "BackdropNode"
    ]
    nodo_siguiente_en_columna = None
    distMedia_NodoSiguiente = float("inf")

    for node in all_nodes:
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        # Verifica si el nodo esta dentro de la tolerancia y en la direccion correcta (debajo del nodo actual)
        if (
            abs(node_center_x - current_node_center_x) <= pos_tolerance
            and node_center_y > current_node_center_y
        ):
            distance = node_center_y - current_node_center_y
            if distance > 0 and distance < distMedia_NodoSiguiente:
                distMedia_NodoSiguiente = distance
                nodo_siguiente_en_columna = node
                debug_print(
                    f"Nodo siguiente en la misma columna encontrado: {nodo_siguiente_en_columna.name()} a distancia {distMedia_NodoSiguiente}"
                )

    # Ajuste de la distancia Y si es necesario
    if distMedia_NodoSiguiente != float("inf"):
        if distMedia_NodoSiguiente < distanciaY * 2:
            distanciaY = distMedia_NodoSiguiente / 2 - (dot_width / 2) - 6
        debug_print(f"Distancia Y ajustada a: {distanciaY}")

    # Calcular la posicion Y del dot
    new_y_pos = int(selected_node.ypos() + selected_node.screenHeight() + distanciaY)
    debug_print(f"Posicion Y del nuevo Dot: {new_y_pos}")

    # Crear un nuevo nodo de Dot debajo del nodo seleccionado
    dot_node = nuke.nodes.Dot()

    # Calcular la posicion X para centrar el Dot horizontalmente
    dot_xpos = int(
        selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2)
    )

    # Establecer la nueva posicion del nodo Dot
    dot_node.setXpos(dot_xpos)
    dot_node.setYpos(new_y_pos)

    # Conectar el nodo seleccionado al nodo de Dot
    dot_node.setInput(0, selected_node)
    debug_print(
        f"Nuevo Dot creado y conectado al nodo seleccionado: {selected_node.name()}"
    )

    # Guardar la conexión original del nodo siguiente antes de modificarla
    next_node_input_index = -1
    if (
        nodo_siguiente_en_columna
        and selected_node in nodo_siguiente_en_columna.dependencies(nuke.INPUTS)
    ):
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == selected_node:
                # Reconectar la entrada del nodo siguiente al dot principal
                nodo_siguiente_en_columna.setInput(i, dot_node)
                next_node_input_index = i  # Guardamos el indice donde estaba conectado
                debug_print(
                    f"Nodo siguiente en la columna conectado al nuevo Dot principal: {nodo_siguiente_en_columna.name()}"
                )
                break

    # Crear un nuevo nodo de Dot a la izquierda del Dot recien creado
    dot_side = nuke.nodes.Dot()
    dot_side.setXpos(dot_node.xpos() + distanciaX)
    dot_side.setYpos(dot_node.ypos())
    dot_side.setInput(0, dot_node)
    debug_print(f"Nuevo Dot lateral creado y conectado al Dot principal")

    # Crear un nodo TimeOffset debajo del dot lateral
    timeoffset = nuke.nodes.TimeOffset()
    timeoffset.setXpos(
        dot_side.xpos() - (timeoffset.screenWidth() // 2) + (dot_width // 2)
    )
    timeoffset.setYpos(
        dot_side.ypos() + dot_side.screenHeight() + distanciaY_columna_lateral
    )
    timeoffset.setInput(0, dot_side)
    timeoffset["time_offset"].setValue(-1)
    debug_print(f"Nuevo TimeOffset creado y conectado al Dot lateral")

    # Crear un nodo Transform debajo del TimeOffset
    transform = nuke.nodes.Transform()
    transform.setXpos(timeoffset.xpos())
    transform.setYpos(
        timeoffset.ypos() + timeoffset.screenHeight() + distanciaY_columna_lateral
    )
    transform.setInput(0, timeoffset)
    debug_print(f"Nuevo Transform creado y conectado al TimeOffset")

    # Crear un dot debajo del Transform
    dot_transform = nuke.nodes.Dot()
    # Calcular la posición X para centrar el Dot horizontalmente respecto al Transform
    dot_transform_xpos = int(
        transform.xpos() + (transform.screenWidth() / 2) - (dot_width / 2)
    )
    dot_transform.setXpos(dot_transform_xpos)
    dot_transform.setYpos(
        transform.ypos() + transform.screenHeight() + distanciaY_columna_lateral
    )
    dot_transform.setInput(0, transform)
    debug_print(f"Nuevo Dot creado debajo del Transform y conectado a él")

    # Crear un nodo Merge debajo del dot principal
    merge = nuke.nodes.Merge2()

    # Posicionar el Merge debajo del dot principal y alineado verticalmente con el último dot
    merge.setXpos(dot_node.xpos() - (merge.screenWidth() // 2) + (dot_width // 2))

    # Calculamos la posición Y del Merge para alinear su centro con el centro del último dot
    # Obtenemos el centro del dot_transform
    dot_transform_center_y = dot_transform.ypos() + (dot_transform.screenHeight() // 2)
    # Posicionamos el Merge para que su centro coincida con el centro del dot
    merge.setYpos(dot_transform_center_y - (merge.screenHeight() // 2))

    # Configurar el nodo Merge
    merge["operation"].setValue("over")
    merge["bbox"].setValue("union")

    # Conectar el dot principal al input B (input 0) del Merge
    merge.setInput(0, dot_node)
    # Conectar el último dot (debajo del Transform) al input A (input 1) del Merge
    merge.setInput(1, dot_transform)

    debug_print(
        f"Nuevo Merge creado y conectado al Dot principal en el input B y al último dot en el input A"
    )

    # Reconectar el nodo siguiente (si existia y estaba conectado al dot principal) a la salida del Merge
    if nodo_siguiente_en_columna and next_node_input_index != -1:
        # Verificamos si la entrada sigue conectada al dot_node (podria haber cambiado por otra operacion)
        if nodo_siguiente_en_columna.input(next_node_input_index) == dot_node:
            nodo_siguiente_en_columna.setInput(next_node_input_index, merge)
            debug_print(
                f"Nodo siguiente en la columna reconectado a la salida del Merge: {nodo_siguiente_en_columna.name()}"
            )

    # Deseleccionar todos los nodos existentes
    for n in nuke.allNodes():
        n["selected"].setValue(False)

    # Al final de la función, seleccionar solo los nuevos nodos
    dot_node["selected"].setValue(True)
    dot_side["selected"].setValue(True)
    timeoffset["selected"].setValue(True)
    transform["selected"].setValue(True)
    dot_transform["selected"].setValue(True)
    merge["selected"].setValue(True)

    # Eliminar el NoOp si fue creado
    if no_op:
        nuke.delete(no_op)
        debug_print("NoOp temporal eliminado")


def gen_iteration_simple():
    # Distancia entre nodos
    distanciaY = 70
    distanciaY_columna_lateral = (
        30  # Distancia vertical entre nodos en la columna lateral
    )
    distanciaX = -200  # Distancia fija a la izquierda (versión lejana)

    # Intentar obtener dot_width desde las preferencias, usar valor predeterminado si falla
    prefs_node = nuke.toNode("preferences")
    if prefs_node and "dot_node_scale" in prefs_node.knobs():
        dot_width = int(prefs_node["dot_node_scale"].value() * 12)
    else:
        dot_width = DEFAULT_DOT_WIDTH  # Usar valor predeterminado

    # Obtener el nodo seleccionado
    selected_node = None
    no_op = None

    try:
        selected_node = nuke.selectedNode()
    except ValueError:
        # Si no hay nodo seleccionado, simular click en el DAG antes de crear el NoOp
        simulate_dag_click()

        # Crear un NoOp en la posición del cursor, pero más arriba para que el dot quede en la posición del cursor
        no_op = nuke.createNode("NoOp")

        # Ajustar la posición vertical del NoOp para que el dot quede cerca de donde estaba el cursor
        no_op.setYpos(no_op.ypos() - distanciaY)

        selected_node = no_op

    debug_print(f"Nodo seleccionado/creado: {selected_node.name()}")

    pos_tolerance = 120  # Tolerancia para la posicion en X
    current_node_center_x = selected_node.xpos() + (selected_node.screenWidth() / 2)
    current_node_center_y = selected_node.ypos() + (selected_node.screenHeight() / 2)

    # Buscar el primer nodo que este debajo del nodo seleccionado con una tolerancia en X
    all_nodes = [
        n
        for n in nuke.allNodes()
        if n != selected_node and n.Class() != "Root" and n.Class() != "BackdropNode"
    ]
    nodo_siguiente_en_columna = None
    distMedia_NodoSiguiente = float("inf")

    for node in all_nodes:
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        # Verifica si el nodo esta dentro de la tolerancia y en la direccion correcta (debajo del nodo actual)
        if (
            abs(node_center_x - current_node_center_x) <= pos_tolerance
            and node_center_y > current_node_center_y
        ):
            distance = node_center_y - current_node_center_y
            if distance > 0 and distance < distMedia_NodoSiguiente:
                distMedia_NodoSiguiente = distance
                nodo_siguiente_en_columna = node
                debug_print(
                    f"Nodo siguiente en la misma columna encontrado: {nodo_siguiente_en_columna.name()} a distancia {distMedia_NodoSiguiente}"
                )

    # Ajuste de la distancia Y si es necesario
    if distMedia_NodoSiguiente != float("inf"):
        if distMedia_NodoSiguiente < distanciaY * 2:
            distanciaY = distMedia_NodoSiguiente / 2 - (dot_width / 2) - 6
        debug_print(f"Distancia Y ajustada a: {distanciaY}")

    # Calcular la posicion Y del dot
    new_y_pos = int(selected_node.ypos() + selected_node.screenHeight() + distanciaY)
    debug_print(f"Posicion Y del nuevo Dot: {new_y_pos}")

    # Crear un nuevo nodo de Dot debajo del nodo seleccionado
    dot_node = nuke.nodes.Dot()

    # Calcular la posicion X para centrar el Dot horizontalmente
    dot_xpos = int(
        selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2)
    )

    # Establecer la nueva posicion del nodo Dot
    dot_node.setXpos(dot_xpos)
    dot_node.setYpos(new_y_pos)

    # Conectar el nodo seleccionado al nodo de Dot
    dot_node.setInput(0, selected_node)
    debug_print(
        f"Nuevo Dot creado y conectado al nodo seleccionado: {selected_node.name()}"
    )

    # Guardar la conexión original del nodo siguiente antes de modificarla
    next_node_input_index = -1
    if (
        nodo_siguiente_en_columna
        and selected_node in nodo_siguiente_en_columna.dependencies(nuke.INPUTS)
    ):
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == selected_node:
                # Reconectar la entrada del nodo siguiente al dot principal
                nodo_siguiente_en_columna.setInput(i, dot_node)
                next_node_input_index = i  # Guardamos el indice donde estaba conectado
                debug_print(
                    f"Nodo siguiente en la columna conectado al nuevo Dot principal: {nodo_siguiente_en_columna.name()}"
                )
                break

    # Crear un nuevo nodo de Dot a la izquierda del Dot recien creado
    dot_side = nuke.nodes.Dot()
    dot_side.setXpos(dot_node.xpos() + distanciaX)
    dot_side.setYpos(dot_node.ypos())
    dot_side.setInput(0, dot_node)
    debug_print(f"Nuevo Dot lateral creado y conectado al Dot principal")

    # Crear un dot debajo del Dot lateral
    dot_transform = nuke.nodes.Dot()
    # Calcular la posición X para centrar el Dot horizontalmente respecto al Dot lateral
    dot_transform_xpos = int(
        dot_side.xpos() + (dot_side.screenWidth() / 2) - (dot_width / 2)
    )
    dot_transform.setXpos(dot_transform_xpos)
    dot_transform.setYpos(dot_side.ypos() + dot_side.screenHeight() + 140)
    dot_transform.setInput(0, dot_side)
    debug_print(f"Nuevo Dot creado debajo del Dot lateral y conectado a él")

    # Crear un nodo Merge debajo del dot principal
    merge = nuke.nodes.Merge2()

    # Posicionar el Merge debajo del dot principal y alineado verticalmente con el último dot
    merge.setXpos(dot_node.xpos() - (merge.screenWidth() // 2) + (dot_width // 2))

    # Calculamos la posición Y del Merge para alinear su centro con el centro del último dot
    # Obtenemos el centro del dot_transform
    dot_transform_center_y = dot_transform.ypos() + (dot_transform.screenHeight() // 2)
    # Posicionamos el Merge para que su centro coincida con el centro del dot
    merge.setYpos(dot_transform_center_y - (merge.screenHeight() // 2))

    # Configurar el nodo Merge
    merge["operation"].setValue("over")
    merge["bbox"].setValue("union")

    # Conectar el dot principal al input B (input 0) del Merge
    merge.setInput(0, dot_node)
    # Conectar el último dot (debajo del Dot lateral) al input A (input 1) del Merge
    merge.setInput(1, dot_transform)

    debug_print(
        f"Nuevo Merge creado y conectado al Dot principal en el input B y al último dot en el input A"
    )

    # Reconectar el nodo siguiente (si existia y estaba conectado al dot principal) a la salida del Merge
    if nodo_siguiente_en_columna and next_node_input_index != -1:
        # Verificamos si la entrada sigue conectada al dot_node (podria haber cambiado por otra operacion)
        if nodo_siguiente_en_columna.input(next_node_input_index) == dot_node:
            nodo_siguiente_en_columna.setInput(next_node_input_index, merge)
            debug_print(
                f"Nodo siguiente en la columna reconectado a la salida del Merge: {nodo_siguiente_en_columna.name()}"
            )

    # Deseleccionar todos los nodos existentes
    for n in nuke.allNodes():
        n["selected"].setValue(False)

    # Al final de la función, seleccionar solo los nuevos nodos
    dot_node["selected"].setValue(True)
    dot_side["selected"].setValue(True)
    dot_transform["selected"].setValue(True)
    merge["selected"].setValue(True)

    # Eliminar el NoOp si fue creado
    if no_op:
        nuke.delete(no_op)
        debug_print("NoOp temporal eliminado")


# gen_iteration()
