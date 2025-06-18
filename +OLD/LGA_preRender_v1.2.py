"""
____________________________________

  LGA_preRender v1.1 | 2024 | Lega  
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

# Importar modulos de PySide2
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QFrame

def align_write_to_dot(dot_node, write_node):
    dot_center_y = dot_node.ypos() + dot_node.screenHeight() / 2
    write_center_y = write_node.ypos() + write_node.screenHeight() / 2
    y_offset = dot_center_y - write_center_y
    if y_offset != 0:
        write_node.setYpos(int(write_node.ypos() + y_offset))

def get_unique_node_name(base_name):
    node_name = base_name
    index = 1
    while nuke.exists(node_name):
        node_name = f"{base_name}{index}"
        index += 1
    return node_name

def create_text_dialog(initial_text=''):
    dialog = QtWidgets.QDialog()
    dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
    dialog.esc_exit = False  # Anadir una variable de instancia para esc_exit

    # Establecer el estilo del dialogo directamente
    dialog.setStyleSheet("QDialog { background-color: #242527; }")  # Color de fondo de la ventana

    layout = QtWidgets.QVBoxLayout(dialog)

    title = QtWidgets.QLabel("preRender Name")
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setStyleSheet("color: #AAAAAA; font-family: Verdana; font-weight: bold; font-size: 10pt;")
    layout.addWidget(title)

    # Usar QLineEdit en lugar de QTextEdit para una sola linea
    line_edit = QtWidgets.QLineEdit(dialog)
    line_edit.setFixedHeight(25)  # Altura adecuada para una sola linea
    line_edit.setFrame(False)  # Quitar el marco del QLineEdit
    line_edit.setStyleSheet("""
        background-color: #262626;  # Fondo de la caja de texto gris
        color: #FFFFFF;  # Texto blanco
    """)
    line_edit.setText(initial_text)  # Establecer el texto inicial
    layout.addWidget(line_edit)

    help_label = QtWidgets.QLabel('<span style="font-size:7pt; color:#AAAAAA;">Enter para confirmar</span>', dialog)
    help_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(help_label)

    dialog.setLayout(layout)
    dialog.resize(200, 100)

    # Mover el cursor al final del texto inicial
    line_edit.setCursorPosition(len(initial_text))

    def event_filter(widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                dialog.accept()
                return True
            elif event.key() == QtCore.Qt.Key_Escape:
                dialog.esc_exit = True  # Establecer esc_exit en True cuando se presiona ESC
                dialog.reject()
                return True
        return False

    line_edit.installEventFilter(dialog)
    dialog.eventFilter = event_filter

    line_edit.setFocus()  # Poner el cursor dentro de la caja de texto

    return dialog, line_edit

def show_text_dialog(initial_text=''):
    dialog, line_edit = create_text_dialog(initial_text)
    cursor_pos = QtGui.QCursor.pos()
    avail_space = QtWidgets.QDesktopWidget().availableGeometry(cursor_pos)
    posx = min(max(cursor_pos.x()-100, avail_space.left()), avail_space.right()-200)
    posy = min(max(cursor_pos.y()-80, avail_space.top()), avail_space.bottom()-150)
    dialog.move(QtCore.QPoint(posx, posy))

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return dialog.esc_exit, line_edit.text()
    else:
        return dialog.esc_exit, None

def get_selected_node():
    try:
        return nuke.selectedNode()
    except ValueError:
        return None

def main():
    # Mostrar el cuadro de dialogo de texto para obtener la etiqueta del backdrop del usuario
    esc_exit, user_text = show_text_dialog(initial_text='Pre-')
    if esc_exit or user_text is None:
        # El usuario cancelo el dialogo, salir de la funcion
        return

    # Iniciar el grupo de deshacer
    nuke.Undo().begin("LGA_preRender")

    # Variables para posicionamiento
    dot_width = int(nuke.toNode("preferences")['dot_node_scale'].value() * 12)
    distanciaX = 180  # Distancia horizontal para el nodo Write
    distanciaY = 80   # Distancia vertical entre nodos

    # Verificar si hay un nodo seleccionado
    selected_node = get_selected_node()

    if selected_node:
        current_node = selected_node
        no_op = None
    else:
        no_op = nuke.createNode("NoOp")
        current_node = no_op

    # Crear un Dot debajo del nodo actual
    dot_node = nuke.nodes.Dot()
    dot_node.setInput(0, current_node)
    dot_node.setXpos(int(current_node.xpos() + (current_node.screenWidth() / 2) - (dot_width / 2)))

    if no_op:
        dot_node.setYpos(current_node.ypos() + current_node.screenHeight() - distanciaY)
    else:
        dot_node.setYpos(current_node.ypos() + current_node.screenHeight() + distanciaY)

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

    # Cambiar esta linea segun tu solicitud
    original_file_value = "[file dir [value root.name]]/../2_prerenders/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01/[join [lrange [split [file tail [file rootname [value root.name]]] _ ] 0 4] _]_Pre_v01_%04d.exr"
    # Reemplazar 'Pre' por el texto ingresado por el usuario
    new_file_value = original_file_value.replace('Pre', user_text)
    write_node['file'].setValue(new_file_value)

    write_node['file_type'].setValue('exr')
    write_node['compression'].setValue('DWAA')
    write_node['dw_compression_level'].setValue(60)
    write_node['first_part'].setValue('rgba')
    write_node['create_directories'].setValue(True)
    write_node['checkHashOnRead'].setValue(False)
    write_node['version'].setValue(4)
    write_node['colorspace'].setValue('ACES - ACES2065-1')
    # Obtener un nombre unico para el nodo Write basado en el nombre del backdrop
    base_write_name = 'Write_' + user_text
    unique_write_name = get_unique_node_name(base_write_name)
    write_node['name'].setValue(unique_write_name)

    # Anadir knobs personalizados
    write_node.addKnob(nuke.Tab_Knob('User', 'User'))
    write_node.addKnob(nuke.String_Knob('render_time', 'Render Time'))
    write_node['render_time'].setValue("00:18:27")

    # Reconectar nodos descendentes al Switch
    if not no_op:
        downstream_nodes = current_node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False)
        for node in downstream_nodes:
            for i in range(node.inputs()):
                if node.input(i) == current_node:
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

    # Crear el BackdropNode con el nombre proporcionado por el usuario
    backdrop_node = nuke.nodes.BackdropNode(
        xpos = bd_x,
        ypos = bd_y,
        bdwidth = bd_w,
        bdheight = bd_h,
        tile_color = int('0x9F9000FF', 16),
        note_font = "Verdana Bold",
        note_font_size = 50,
        label = user_text,
        z_order = 4,
        name = "Backdrop_preRender"
    )
    backdrop_node['selected'].setValue(True)  # Seleccionar el backdrop

    # Ejecutar la alineacion directamente
    align_write_to_dot(dot_node, write_node)

    # Cerrar el panel de propiedades del Backdrop antes de reemplazarlo
    backdrop_node.hideControlPanel()

    # Deseleccionar el backdrop antes de reemplazarlo
    backdrop_node['selected'].setValue(False)

    # Si el modulo LGA_oz_backdropReplacer esta disponible, llamar a la funcion replace_with_oz_backdrop
    if oz_backdrop_available:
        LGA_oz_backdropReplacer.replace_with_oz_backdrop()
        # Obtener el nuevo backdrop_node despues del reemplazo
        selected_nodes = nuke.selectedNodes("BackdropNode")
        if selected_nodes:
            new_backdrop_node = selected_nodes[0]
            new_backdrop_node.hideControlPanel()
    else:
        nuke.tprint("No se reemplazo el backdrop porque LGA_oz_backdropReplacer no esta disponible.")

    # Si se creo un NoOp temporal, eliminarlo
    if no_op:
        nuke.delete(no_op)

    # Abrir las propiedades del Write node
    write_node.showControlPanel()

    # Seleccionar solo el nodo Write
    for node in nuke.allNodes():
        node['selected'].setValue(False)
    write_node['selected'].setValue(True)

    # Finalizar el grupo de deshacer
    nuke.Undo().end()

# Ejecutar la funcion principal
#main()
