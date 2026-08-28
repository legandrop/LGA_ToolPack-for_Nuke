"""
________________________________________________________________________________

  LGA_fr_Read_to_Project_Res v1.01 | Lega
  Copia el frame range y la resolucion del nodo Read seleccionado al proyecto.

  v1.01: Los nuke.message pasan al helper LGA_UI_MessageBox_ToolPack
         (show_warning), con fallback a nuke.message.
________________________________________________________________________________

"""

import nuke


def _aviso(texto):
    """Cartel estilado del pack; si el helper falla cae a nuke.message."""
    try:
        from LGA_UI_MessageBox_ToolPack import show_warning

        show_warning(None, "Read -> Project (+Res)", texto)
    except Exception:
        nuke.message(texto)


def main():
    try:
        # Obtener el nodo Read seleccionado
        selected_node = nuke.selectedNode()

        if selected_node.Class() != "Read":
            _aviso("Por favor, selecciona un nodo Read.")
            return

        # Obtener el rango de frames del nodo Read seleccionado
        frame_range = selected_node["first"].value(), selected_node["last"].value()

        # Obtener el formato del nodo Read
        read_format = selected_node.format()

        # Crear el formato si no existe
        format_name = f"{read_format.width()}x{read_format.height()}"
        format_string = f"{read_format.width()} {read_format.height()} 0 0 {read_format.width()} {read_format.height()} 1 {format_name}"

        # Agregar el formato si no existe ya
        if not nuke.exists(format_name):
            nuke.addFormat(format_string)

        # Establecer el rango de frames del proyecto
        nuke.root()["first_frame"].setValue(frame_range[0])
        nuke.root()["last_frame"].setValue(frame_range[1])

        # Establecer el formato del proyecto usando el nombre del formato
        nuke.root()["format"].setValue(format_name)

    except Exception as e:
        print(str(e))  # Para debug
        _aviso("Por favor, selecciona un nodo Read.")


# Ejecutar la funcion
# main()
