from PySide2.QtWidgets import QMessageBox, QApplication, QPushButton
from PySide2.QtCore import Qt
import nuke
import os

app = QApplication.instance() or QApplication([])

def is_path_inside_project(read_path, project_folder):
    read_path_norm = os.path.normpath(read_path).lower()
    project_folder_norm = os.path.normpath(project_folder).lower()
    return read_path_norm.startswith(project_folder_norm)

def reveal_in_node_graph(node_name):
    node = nuke.toNode(node_name)
    if node:
        nuke.selectAll()
        nuke.invertSelection()
        node['selected'].setValue(True)
        nuke.zoomToFitSelected()

def custom_ask_dialog(node):
    global continue_process

    file_path = node['file'].value()
    directory = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)  # Get the file name
    node_name = node.name()

    # Automatically reveal the node in the Node Graph
    reveal_in_node_graph(node_name)

    while True:  # Keep the dialog open until "Next" or "Quit" is selected
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Reads Path Checker")
        msg_box.setText(f"The node <b><span style='color:#ffaa0a;'>{node_name}</span></b> is referencing a file outside of the project folder:")
        # Adjusted message format with added line breaks for clarity
        msg_box.setInformativeText(f"<b><span style='color:#ede57a;'>{directory}</span></b><br><br><b><span style='color:#3498db;'>{file_name}</span></b>")
        msg_box.setStyleSheet("QMessageBox { background-color: #2a2a2a; color: #f0f0f0; }")
        msg_box.setTextFormat(Qt.RichText)

        quit_button = QPushButton('Quit')
        quit_button.setShortcut('Esc')
        next_button = QPushButton('Next')
        next_button.setShortcut('Space')
        reveal_button = QPushButton('Reveal in Explorer')

        msg_box.addButton(quit_button, QMessageBox.RejectRole)
        msg_box.addButton(next_button, QMessageBox.NoRole)
        msg_box.addButton(reveal_button, QMessageBox.YesRole)

        response = msg_box.exec_()

        if msg_box.clickedButton() == quit_button:
            continue_process = False
            break
        elif msg_box.clickedButton() == reveal_button:
            if os.path.exists(directory):
                os.startfile(directory)
            else:
                directory_does_not_exist_dialog(node_name)
                break  # Exit the loop after showing the directory not found message
        elif msg_box.clickedButton() == next_button:
            break  # Exit the loop and continue with the next node



def directory_does_not_exist_dialog(node_name):
    global continue_process

    node = nuke.toNode(node_name)
    file_path = node['file'].value() if node else "Ruta desconocida"
    directory = os.path.dirname(file_path)

    # Mostrar automaticamente el nodo en el Node Graph
    reveal_in_node_graph(node_name)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("Asset Path Scanner")
    msg_box.setText(f"El directorio para el nodo <b><span style='color:#ffaa0a;'>{node_name}</span></b> no existe:")
    msg_box.setInformativeText(f"<span style='color:#ede57a;'>{directory}</span>")
    msg_box.setStyleSheet("QMessageBox { background-color: #2a2a2a; color: #f0f0f0; }")
    msg_box.setTextFormat(Qt.RichText)

    quit_button = QPushButton('Quit')
    quit_button.setShortcut('Esc')
    next_button = QPushButton('Next')
    next_button.setShortcut('Enter')

    msg_box.addButton(quit_button, QMessageBox.RejectRole)
    msg_box.addButton(next_button, QMessageBox.AcceptRole)

    response = msg_box.exec_()

    if msg_box.clickedButton() == quit_button:
        continue_process = False


def check_read_nodes():
    global continue_process
    continue_process = True

    project_path = nuke.root().name()
    if not project_path:
        custom_message_box("Por favor guarda el script antes de ejecutar este script.")
        return

    project_folder = os.path.dirname(os.path.dirname(os.path.dirname(project_path)))

    for node in nuke.allNodes('Read'):
        if not continue_process:
            break
        file_path = node['file'].value()
        if not is_path_inside_project(file_path, project_folder):
            custom_ask_dialog(node)

#check_read_nodes()