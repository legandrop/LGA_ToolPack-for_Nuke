"""
____________________________________

  LGA_preRender v1.0 | 2024 | Lega  
____________________________________

"""

import nuke
import sys
import os

# Agrega la ruta del directorio donde se encuentra este script al sys.path
script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)

# Intentar importar el modulo LGA_oz_backdropReplacer
try:
    import LGA_oz_backdropReplacer
    oz_backdrop_available = True
except ImportError:
    oz_backdrop_available = False
    nuke.tprint("El modulo LGA_oz_backdropReplacer no esta disponible. Continuando sin reemplazar el backdrop.")

def align_write_to_dot(dot_node, write_node):
    dot_center_y = dot_node.ypos() + dot_node.screenHeight() / 2
    write_center_y = write_node.ypos() + write_node.screenHeight() / 2
    y_offset = dot_center_y - write_center_y
    if y_offset != 0:
        write_node.setYpos(int(write_node.ypos() + y_offset))
    #print(f"Posicion Y final centrada del nodo {dot_node.name()}: {dot_center_y}")
    #print(f"Posicion Y final centrada del nodo {write_node.name()}: {write_center_y}")

def get_unique_node_name(base_name):
    node_name = base_name
    index = 1
    while nuke.toNode(node_name):
        node_name = f"{base_name}{index}"
        index += 1
    return node_name

def main():
    # Iniciar el grupo de deshacer
    nuke.Undo().begin("LGA_preRender")

    # Verificar si hay un nodo seleccionado
    try:
        selected_node = nuke.selectedNode()
        node_was_selected = True
    except ValueError:
        # Si no hay ningun nodo seleccionado, crear un NoOp y seleccionarlo
        selected_node = nuke.nodes.NoOp(name="tempNoOp")
        selected_node['selected'].setValue(True)
        node_was_selected = False

    # Variables para posicionamiento
    dot_width = int(nuke.toNode("preferences")['dot_node_scale'].value() * 12)
    distanciaX = 180  # Distancia horizontal para el nodo Write
    distanciaY = 80   # Distancia vertical entre nodos

    # Crear un Dot debajo del nodo seleccionado
    dot_node = nuke.nodes.Dot()
    dot_node.setInput(0, selected_node)
    dot_node.setXpos(int(selected_node.xpos() + (selected_node.screenWidth() / 2) - (dot_width / 2)))
    dot_node.setYpos(selected_node.ypos() + selected_node.screenHeight() + distanciaY * 2)

    # Si se creo un NoOp temporal, eliminarlo despues de crear el Dot
    if not node_was_selected:
        nuke.delete(selected_node)

    # Crear un Switch debajo del Dot con 'which' en 1 y deshabilitado
    switch_node = nuke.nodes.Switch()
    switch_node.setInput(0, dot_node)  # Input 0 conectado al Dot
    switch_node.setInput(1, None)      # Input 1 sin conectar
    switch_node['which'].setValue(1)   # Selecciona Input 1 (sin conectar)
    switch_node['disable'].setValue(True)
    switch_node.setXpos(dot_node.xpos() - (switch_node.screenWidth() // 2) + (dot_width // 2))
    switch_node.setYpos(dot_node.ypos() + distanciaY)

    # Crear un Write alineado verticalmente con el Dot
    write_node = nuke.nodes.Write()
    write_node.setInput(0, dot_node)
    write_node.setXpos(int(dot_node.xpos() + (dot_width / 2) - (write_node.screenWidth() // 2) - distanciaX))
    write_node.setYpos(dot_node.ypos())  # Posicion inicial en Y

    # Configurar los ajustes del nodo Write
    write_node['channels'].setValue('rgba')
    write_node['file'].setValue("[file dirname [value root.name]]/../2_prerenders/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]Pre_v01/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01_%04d.exr")
    write_node['file_type'].setValue('exr')
    write_node['compression'].setValue('DWAA')
    write_node['dw_compression_level'].setValue(60)
    write_node['first_part'].setValue('rgba')
    write_node['create_directories'].setValue(True)
    write_node['checkHashOnRead'].setValue(False)
    write_node['version'].setValue(4)
    write_node['colorspace'].setValue('ACES - ACES2065-1')
    # Obtener un nombre unico para el nodo Write
    unique_write_name = get_unique_node_name('Write_PreRender')
    write_node['name'].setValue(unique_write_name)

    # Anadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob('User', 'User'))
    write_node.addKnob(nuke.String_Knob('render_time', 'Render Time'))
    write_node['render_time'].setValue("00:18:27")

    # Reconectar nodos descendentes al Switch
    if node_was_selected:
        downstream_nodes = selected_node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False)
        for node in downstream_nodes:
            for i in range(node.inputs()):
                if node.input(i) == selected_node:
                    node.setInput(i, switch_node)

    # Crear el BackdropNode detras de los tres nodos
    nodes = [write_node, dot_node, switch_node]

    # Ajustes de margenes segun tus especificaciones
    margen_izquierdo = 64  # Antes era 50
    margen_superior = 115  # Antes era 100
    margen_derecho = 63    # Antes era 50
    margen_inferior = 50   # Antes era 100

    bd_x = min(node.xpos() for node in nodes) - margen_izquierdo
    bd_y = min(node.ypos() for node in nodes) - margen_superior
    bd_w = max(node.xpos() + node.screenWidth() for node in nodes) - bd_x + margen_derecho
    bd_h = max(node.ypos() + node.screenHeight() for node in nodes) - bd_y + margen_inferior

    backdrop_node = nuke.nodes.BackdropNode(
        xpos = bd_x,
        ypos = bd_y,
        bdwidth = bd_w,
        bdheight = bd_h,
        tile_color = int('0xAFAF00FF', 16),
        note_font = "Verdana Bold",
        note_font_size = 50,
        label = "preRender",
        z_order = 4,
        name = "Backdrop_preRender"
    )
    backdrop_node['selected'].setValue(True)  # Seleccionar el backdrop

    # Ejecutar la alineacion directamente
    align_write_to_dot(dot_node, write_node)

    # Deseleccionar el backdrop antes de reemplazarlo
    backdrop_node['selected'].setValue(False)

    # Si el modulo LGA_oz_backdropReplacer esta disponible, llamar a la funcion replace_with_oz_backdrop
    if oz_backdrop_available:
        LGA_oz_backdropReplacer.replace_with_oz_backdrop()
    else:
        nuke.tprint("No se reemplazo el backdrop porque LGA_oz_backdropReplacer no esta disponible.")

    # Finalizar el grupo de deshacer
    nuke.Undo().end()

# Ejecutar la funcion principal
#main()
