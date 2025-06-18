"""
_______________________________________________

  LGA_switchMergeOperations v1.0 | 2024 | Lega  
_______________________________________________

"""

import nuke

def update_merge_operations():
    # Obtener todos los nodos seleccionados
    selected_nodes = nuke.selectedNodes()
    
    # Filtrar los nodos Merge seleccionados
    merge_nodes = [node for node in selected_nodes if node.Class() == 'Merge2']
    
    for node in merge_nodes:
        current_operation = node['operation'].value()
        
        if current_operation == 'over':
            node['operation'].setValue('mask')
            node['bbox'].setValue('A')
        elif current_operation == 'mask':
            node['operation'].setValue('stencil')
            node['bbox'].setValue('B')
        elif current_operation == 'stencil':
            node['operation'].setValue('over')
            node['bbox'].setValue('B')
    
# Ejecuta la funcion
#update_merge_operations()
