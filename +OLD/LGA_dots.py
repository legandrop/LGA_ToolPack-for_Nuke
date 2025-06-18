#------------------------------------------------------------#
#   LGA_dots v1.4 - 2024 - Lega Pugliese                     #
#   Genera automaticamente un Dot debajo y otro a la         #
#   izquierda/derecha del nodo actual segun se especifique   #
#------------------------------------------------------------#

import nuke

# Definir la distancia vertical entre los nodos Dot
distanciaY = 70

def dotsAfter(direction='l'):
    # Determinar la direccion de creacion del Dot
    if direction == 'l':
        distanciaX = -140
    elif direction == 'r':
        distanciaX = 140
    else:
        #nuke.message("Direccion no valida. Use 'l' para izquierda o 'r' para derecha.")
        return

    # Obtener el nodo seleccionado
    selected_node = nuke.selectedNode()
    
    if selected_node is None:
        nuke.message("No node selected.")
        return
    
    # Calcular la nueva posicion Y, que es 70 pixeles debajo del borde inferior del nodo seleccionado
    new_y_pos = selected_node.ypos() + selected_node.screenHeight() + distanciaY

    # Verificar si el nodo seleccionado esta conectado a otro nodo
    connected_nodes = selected_node.dependent()
    if connected_nodes:
        # Crear un nuevo nodo de Dot
        dot_node = nuke.nodes.Dot()
        
        # Calcular la posicion X para centrar el Dot horizontalmente
        size_of_dots = nuke.toNode('preferences').knob('dot_node_scale').value()
        dot_width = 12 * size_of_dots
        dot_xpos = int(selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2))

        # Establecer la nueva posicion del nodo Dot
        dot_node.setXpos(dot_xpos)
        dot_node.setYpos(new_y_pos)
        
        # Conectar el nodo seleccionado al nodo de Dot
        dot_node.setInput(0, selected_node)

        # Obtener el primer nodo conectado
        connected_node = connected_nodes[0]
        
        # Conectar el nodo B al nodo de Dot
        connected_node.setInput(0, dot_node)
        
        # Crear un nuevo nodo de Dot a la izquierda o derecha del Dot recien creado
        dot_side = nuke.nodes.Dot()
        dot_side.setXpos(dot_node.xpos() + distanciaX)
        dot_side.setYpos(dot_node.ypos())
        dot_side.setInput(0, dot_node)

    else:
        # Crear un nuevo nodo de Dot debajo del nodo seleccionado
        dot_node = nuke.nodes.Dot()
        
        # Calcular la posicion X para centrar el Dot horizontalmente
        size_of_dots = nuke.toNode('preferences').knob('dot_node_scale').value()
        dot_width = 12 * size_of_dots
        dot_xpos = int(selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2))
        
        # Establecer la nueva posicion del nodo Dot
        dot_node.setXpos(dot_xpos)
        dot_node.setYpos(new_y_pos)
        
        # Conectar el nodo seleccionado al nodo de Dot
        dot_node.setInput(0, selected_node)
        
        # Crear un nuevo nodo de Dot a la izquierda o derecha del Dot recien creado
        dot_side = nuke.nodes.Dot()
        dot_side.setXpos(dot_node.xpos() + distanciaX)
        dot_side.setYpos(dot_node.ypos())
        dot_side.setInput(0, dot_node)
