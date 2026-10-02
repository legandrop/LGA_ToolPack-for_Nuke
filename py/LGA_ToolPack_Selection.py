"""
____________________________________________________________________

  LGA_ToolPack_Selection v1.00 | Lega

  El nodo seleccionado del grafo en el que esta parado el usuario.

  nuke.selectedNode() solo no alcanza: tambien devuelve un nodo que quedo
  seleccionado ADENTRO de un grupo o gizmo (medido: el GizmoControl de un
  DespillMadness), aunque en el Node Graph no haya nada seleccionado. Las
  tools que lo usan de ancla creaban sus nodos en la posicion de ese nodo
  interno, siempre en el mismo lugar, y los conectaban a un nodo de otro
  grupo. Con un nodo seleccionado en el grafo actual, selectedNode() si
  devuelve ese.

  selected_node() es un reemplazo directo de nuke.selectedNode(): mismo
  contrato, incluido el ValueError cuando no hay seleccion, asi el
  try/except de cada tool queda igual.

  v1.00: Modulo nuevo.
____________________________________________________________________
"""

import nuke


def selected_node():
    """El ultimo nodo seleccionado del grafo actual. ValueError si no hay."""
    seleccion = nuke.selectedNodes()
    if not seleccion:
        raise ValueError("No node selected")
    try:
        ultimo = nuke.selectedNode()
    except ValueError:
        return seleccion[0]
    nombres = set(n.fullName() for n in seleccion)
    return ultimo if ultimo.fullName() in nombres else seleccion[0]
