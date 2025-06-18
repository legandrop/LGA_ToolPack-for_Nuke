import nuke

def print_knobs():
    # Obtener el nodo seleccionado
    selected_node = nuke.selectedNode()
    
    if not selected_node:
        nuke.message("Por favor, selecciona un nodo.")
        return
    
    # Obtener todos los knobs del nodo seleccionado
    knobs = selected_node.knobs()
    
    # Imprimir los nombres de todos los knobs
    print("Knobs del nodo seleccionado:")
    for knob_name in knobs:
        print(knob_name)

# Ejecutar la funcion
print_knobs()
