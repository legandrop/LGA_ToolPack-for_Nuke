import re
import nuke
import os

def renameWrite():
    # Function to get the file name without extension from the given file path
    def get_file_name_without_extension(file_path):
        # Use os.path.basename to get the file name from the path
        file_name_with_extension = os.path.basename(file_path)
        # Use os.path.splitext to split the file name and extension
        file_name, file_extension = os.path.splitext(file_name_with_extension)
        return file_name

    # Function to remove padding after the last underscore
    def remove_padding(file_name):
        if "_" in file_name:
            return "_".join(file_name.split("_")[:-1])  # Join all parts except the last one after the last underscore
        else:
            return file_name

    # Function to find the topmost Read node in the node's upstream dependencies
    def find_top_read_node(node):
        if node.Class() == 'Read':
            return node

        for input_node in node.dependencies():
            return find_top_read_node(input_node)

        return None

    # Get the selected Write node
    write_node = nuke.selectedNode()      
    if not write_node or not write_node.Class() == 'Write':
        nuke.message("Please select a Write node.")
    else:
        # Find the topmost Read node connected to the Write node
        read_node = find_top_read_node(write_node)

        if not read_node:
            nuke.message("No Read node connected to the selected Write node.")
        else:
            # Get the file path from the Read node and extract the file name without extension
            file_path = read_node['file'].value()
            file_name = get_file_name_without_extension(file_path)
            file_name_no_padding = remove_padding(file_name)

            # Get the selected nodes and reverse the order
            # This will ensure that the Write node is renamed first (if selected) and then other selected nodes
            selected_nodes = nuke.selectedNodes()
            selected_nodes.reverse()
            
            if selected_nodes:
                for node in selected_nodes:
                    node.setName(file_name_no_padding)
