"""
________________________________

  LGA_grade v1.3 | 2024 | Lega  
________________________________

"""

import nuke


# Variables comunes
def get_common_variables():
    distanciaY = 20  # Espacio libre entre nodos en la columna derecha
    distanciaX = 180
    dot_width = int(nuke.toNode("preferences")['dot_node_scale'].value() * 12)
    return distanciaX, distanciaY, dot_width

# Funcion para obtener el nodo seleccionado
def get_selected_node():
    try:
        selected_node = nuke.selectedNode()
        return selected_node, None
    except ValueError:
        no_op = nuke.createNode("NoOp")
        return no_op, no_op


    

# Funcion para encontrar el nodo siguiente en la columna
def find_next_node_in_column(current_node, tolerance_x=120):
    current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
    current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

    all_nodes = [n for n in nuke.allNodes() if n != current_node and n.Class() != 'Root' and n.Class() != 'BackdropNode']
    nodo_siguiente_en_columna = None
    distMedia_NodoSiguiente = float('inf')

    for node in all_nodes:
        node_center_x = node.xpos() + (node.screenWidth() / 2)
        node_center_y = node.ypos() + (node.screenHeight() / 2)

        if abs(node_center_x - current_node_center_x) <= tolerance_x and node_center_y > current_node_center_y:
            distance = node_center_y - current_node_center_y
            if distance > 0 and distance < distMedia_NodoSiguiente:
                distMedia_NodoSiguiente = distance
                nodo_siguiente_en_columna = node

    return nodo_siguiente_en_columna, distMedia_NodoSiguiente

# Funcion principal GradeHI
def gradeHI():
    # Obtener las variables comunes
    distanciaX, distanciaY, dot_width = get_common_variables()

    selected_node, no_op = get_selected_node()

    current_node = selected_node

    # Buscar el primer nodo que este debajo del nodo seleccionado con una tolerancia en X
    nodo_siguiente_en_columna, distMedia_NodoSiguiente = find_next_node_in_column(current_node)

    # Ajustar la distancia Y si es necesario
    if distMedia_NodoSiguiente != float('inf') and distMedia_NodoSiguiente < distanciaY * 2:
        distanciaY = distMedia_NodoSiguiente / 2 - (dot_width / 2) - 6

    # Crear el Dot a la derecha del primer Dot
    dot_below = nuke.nodes.Dot()
    dot_below.setXpos(int(current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2)))
    if no_op:
        dot_below.setYpos(int(current_node.ypos() + current_node.screenHeight() - distanciaY * 2))
    else:
        dot_below.setYpos(int(current_node.ypos() + current_node.screenHeight() + distanciaY * 3))

    dot_below.setInput(0, current_node)

    if nodo_siguiente_en_columna and current_node in nodo_siguiente_en_columna.dependencies(nuke.INPUTS):
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
    keyer.setYpos(dot_right.ypos() + dot_right.screenHeight() + distanciaY)
    keyer.setInput(0, dot_right)

    # Crear un Shuffle debajo del Keyer
    shuffle = nuke.nodes.Shuffle2(label="[value in1] --> [value out1]")
    shuffle.setXpos(keyer.xpos())
    shuffle.setYpos(keyer.ypos() + keyer.screenHeight() + distanciaY)
    shuffle.setInput(0, keyer)

    # Definir las nuevas conexiones (mappings)
    mappings = [
        ('rgba.alpha', 'rgba.red'),
        ('rgba.alpha', 'rgba.green'),
        ('rgba.alpha', 'rgba.blue'),
        ('rgba.alpha', 'rgba.alpha')
    ]
    # Aplicar las conexiones al nodo Shuffle
    shuffle['mappings'].setValue(mappings)

    # Crear un Dot debajo del Shuffle
    dot_bottom = nuke.nodes.Dot()
    dot_bottom.setXpos(shuffle.xpos() - (dot_width // 2) + (shuffle.screenWidth() // 2))
    dot_bottom.setYpos(shuffle.ypos() + shuffle.screenHeight() + distanciaY)
    dot_bottom.setInput(0, shuffle)

    # Crear un Grade debajo del primer Dot y conectarlo
    grade = nuke.nodes.Grade()
    grade.setXpos(dot_below.xpos() - (grade.screenWidth() // 2) + (dot_width // 2))
    grade.setYpos(int(dot_bottom.ypos() + (dot_bottom.screenHeight() // 2) - (grade.screenHeight() // 2)))
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


def gradeMask():
    # Obtener las variables comunes
    distanciaX, distanciaY, dot_width = get_common_variables()

    # Obtener el nodo seleccionado o crear un NoOp si no hay nodo seleccionado 
    selected_node, no_op = get_selected_node()

    current_node = selected_node

    # Crear un nodo Roto a la derecha del nodo seleccionado
    roto = nuke.nodes.Roto()
    roto.setXpos(current_node.xpos() + distanciaX)
    if no_op:
        roto.setYpos(current_node.ypos() + current_node.screenHeight() - distanciaY *2)
    else:
        roto.setYpos(int(current_node.ypos() + current_node.screenHeight() + distanciaY))

    # Crear un nodo Blur debajo del Roto
    blur = nuke.nodes.Blur()
    blur.setXpos(roto.xpos())
    blur.setYpos(roto.ypos() + roto.screenHeight() + distanciaY)
    blur.setInput(0, roto)
    blur['channels'].setValue("alpha")
    blur['size'].setValue(7)
    blur['label'].setValue("[value size]")    

    # Crear un Dot debajo del Blur
    dot_right = nuke.nodes.Dot()
    dot_right.setXpos(blur.xpos() - (dot_width // 2) + (blur.screenWidth() // 2))
    dot_right.setYpos(blur.ypos() + blur.screenHeight() + distanciaY)
    dot_right.setInput(0, blur)

    # Buscar el nodo siguiente en la columna principal
    nodo_siguiente_en_columna, _ = find_next_node_in_column(current_node)

    # Crear un nodo Grade alineado con el nodo seleccionado en la columna principal
    grade = nuke.nodes.Grade()
    grade.setXpos(current_node.xpos() - (grade.screenWidth() // 2) + (current_node.screenWidth() // 2))
    grade.setYpos(int(dot_right.ypos() + (dot_right.screenHeight() // 2) - (grade.screenHeight() // 2)))

    # Conectar el nodo Grade al nodo seleccionado
    grade.setInput(0, current_node)
    
    # Si hay un nodo siguiente en la columna, conectar el nodo Grade entre el nodo seleccionado y el nodo siguiente
    if nodo_siguiente_en_columna:
        for i in range(nodo_siguiente_en_columna.inputs()):
            if nodo_siguiente_en_columna.input(i) == current_node:
                nodo_siguiente_en_columna.setInput(i, grade)
                break

    # Conectar la mascara del nodo Grade al Dot de la columna derecha
    grade.setInput(1, dot_right)

    # Borrar noOp si existe                
    if no_op:
        nuke.delete(no_op)



