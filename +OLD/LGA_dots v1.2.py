#------------------------------------------------------------#
#   LGA_dots v1.3 - 2024 - Lega Pugliese                     #
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
        nuke.message("Por favor, selecciona un nodo primero.")
        return
    
    # Verificar si el nodo seleccionado esta conectado a otro nodo
    connected_nodes = selected_node.dependent()
    if connected_nodes:
        # Obtener el primer nodo conectado
        connected_node = connected_nodes[0]
        
        # Crear un nuevo nodo de Dot sin mostrar sus propiedades
        dot_node = nuke.createNode("Dot", inpanel=False)
        
        # Calcular la posicion X para centrar el Dot horizontalmente
        size_of_dots = nuke.toNode('preferences').knob('dot_node_scale').value()
        dot_width = 12 * size_of_dots
        dot_xpos = int(selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2))

        # Establecer la posicion del nuevo nodo entre el nodo seleccionado y el nodo conectado
        dot_node.setXpos(dot_xpos)
        dot_node.setYpos(int(selected_node.ypos() + distanciaY))
        
        # Conectar el nodo seleccionado al nodo de Dot
        dot_node.setInput(0, selected_node)
        
        # Conectar el nodo B al nodo de Dot
        connected_node.setInput(0, dot_node)
        
        # Crear un nuevo nodo de Dot a la izquierda o derecha del Dot recien creado sin mostrar sus propiedades
        dot_side = nuke.createNode("Dot", inpanel=False)
        dot_side.setXpos(dot_node.xpos() + distanciaX)
        dot_side.setYpos(dot_node.ypos())
        dot_side.setInput(0, dot_node)
        
    else:
        # Crear un nuevo nodo de Dot debajo del nodo seleccionado sin mostrar sus propiedades
        dot_node = nuke.createNode("Dot", inpanel=False)
        
        # Calcular la posicion X para centrar el Dot horizontalmente
        size_of_dots = nuke.toNode('preferences').knob('dot_node_scale').value()
        dot_width = 12 * size_of_dots
        dot_xpos = int(selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2))
        
        # Establecer la posicion del nuevo nodo debajo del nodo seleccionado y centrado horizontalmente
        dot_node.setXpos(dot_xpos)
        dot_node.setYpos(int(selected_node.ypos() + distanciaY))
        
        # Conectar el nodo seleccionado al nodo de Dot
        dot_node.setInput(0, selected_node)
        
        # Crear un nuevo nodo de Dot a la izquierda o derecha del Dot recien creado sin mostrar sus propiedades
        dot_side = nuke.createNode("Dot", inpanel=False)
        dot_side.setXpos(dot_node.xpos() + distanciaX)
        dot_side.setYpos(dot_node.ypos())
        dot_side.setInput(0, dot_node)
