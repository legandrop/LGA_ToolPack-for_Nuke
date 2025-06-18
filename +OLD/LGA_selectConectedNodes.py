#------------------------------------------------------------#
#    LGA_selectConnectedNodes v1.0 - 2024 - Lega Pugliese    #
#    Busca y selecciona nodos conectados en cualquier        #
#    direccion con tolerancia de 30px, ignorando el flujo    #
#------------------------------------------------------------#

import nuke

def selectConnectedNodes(direction):
    pos_tolerance = 30  # Tolerancia para la posicion en X y Y

    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        return

    current_node = selected_nodes[0]
    if current_node.Class() == 'Root':
        return

    while current_node:
        # Calcula el centro del nodo actual
        current_node_center_x = current_node.xpos() + (current_node.screenWidth() / 2)
        current_node_center_y = current_node.ypos() + (current_node.screenHeight() / 2)

        current_node['selected'].setValue(True)

        # Lista para mantener los nodos conectados tanto aguas arriba como aguas abajo
        search_nodes = [current_node.input(i) for i in range(current_node.inputs()) if current_node.input(i)]
        search_nodes += current_node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS)
        search_nodes = list(set(search_nodes))  # Elimina duplicados y None

        connected_node = None
        for node in search_nodes:
            if node.Class() == 'Root':
                continue

            # Calcula el centro del nodo conectado
            node_center_x = node.xpos() + (node.screenWidth() / 2)
            node_center_y = node.ypos() + (node.screenHeight() / 2)

            # Verifica la direccion y si el nodo conectado esta dentro de la tolerancia y en la direccion correcta
            if direction == 'l' and abs(node_center_y - current_node_center_y) <= pos_tolerance and node_center_x < current_node_center_x:
                connected_node = node
            elif direction == 'r' and abs(node_center_y - current_node_center_y) <= pos_tolerance and node_center_x > current_node_center_x:
                connected_node = node
            elif direction == 't' and abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y < current_node_center_y:
                connected_node = node
            elif direction == 'b' and abs(node_center_x - current_node_center_x) <= pos_tolerance and node_center_y > current_node_center_y:
                connected_node = node

        if connected_node:
            connected_node['selected'].setValue(True)
            current_node = connected_node
        else:
            break

