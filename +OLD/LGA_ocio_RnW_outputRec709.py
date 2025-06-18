"""
______________________________________________

  LGA_outputRec709 v1.0 - 2024 - Lega Pugliese
______________________________________________

"""

import nuke

def change_color_space(node):
    # Verificar si el nodo es un Read o un Write
    if node.Class() == 'Read':
        node['colorspace'].setValue('Output - Rec.709')
    elif node.Class() == 'Write':
        node['colorspace'].setValue('Output - Rec.709')
    else:
        #print("El nodo seleccionado no es un nodo Read ni Write.")
        pass

def main():
    # Obtener el nodo seleccionado
    selected_nodes = nuke.selectedNodes()

    if selected_nodes:
        for node in selected_nodes:
            change_color_space(node)