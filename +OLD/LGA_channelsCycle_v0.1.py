import nuke

def main():
    # Verifica si hay un nodo seleccionado
    selected_node = nuke.selectedNode()
    
    if selected_node:
        # Intenta obtener el valor del knob "channels"
        if "channels" in selected_node.knobs():
            channels_knob = selected_node['channels']
            current_value = channels_knob.value()
            
            # Lista de valores permitidos
            channels_values = ['rgb', 'rgba', 'alpha']
            
            # Determina el siguiente valor en la rotacion
            if current_value in channels_values:
                next_value_index = (channels_values.index(current_value) + 1) % len(channels_values)
                next_value = channels_values[next_value_index]
            else:
                # Si el valor actual no esta en la lista, se resetea a 'rgb'
                next_value = 'rgb'
            
            # Asigna el siguiente valor
            channels_knob.setValue(next_value)
            print(f"El knob 'channels' ha cambiado a: {next_value}")
        else:
            print("El nodo seleccionado no tiene un knob 'channels'.")
    else:
        print("No hay ningun nodo seleccionado.")

# Ejecuta la funcion
#main()
