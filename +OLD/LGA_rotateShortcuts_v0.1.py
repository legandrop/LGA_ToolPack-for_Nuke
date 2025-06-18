"""
_____________________________________________________________

  LGA_rotateShorcut v1.0 | 2023 | Lega   
  Rotates selected Transform nodes by a user-defined amount  
_____________________________________________________________

"""


import nuke

def increment_rotate(increment):
    selected_node = nuke.selectedNode()
    if selected_node and selected_node.name().startswith("Transform"):
        rotate_knob = selected_node.knob("rotate")
        if rotate_knob:
            rotate_value = rotate_knob.value()
            rotate_knob.setValue(rotate_value + increment)
        else:
            print("El nodo seleccionado no tiene el knob 'Rotate'.")
    else:
        print("Por favor, selecciona un nodo que comience con 'Transform'.")