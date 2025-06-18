import os
import nuke


# Parte del LGA_viewer_SnapShot_Buttons
def OnViewerCreate():
    """Callback que se ejecuta cuando se crea un viewer"""
    import LGA_viewer_SnapShot_Buttons

    LGA_viewer_SnapShot_Buttons.launch()


# Registrar el callback para cuando se cree un viewer
nuke.addOnCreate(OnViewerCreate, nodeClass="Viewer")
