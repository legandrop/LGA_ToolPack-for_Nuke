import os
import nuke


# Parte del LGA_viewer_SnapShot_Buttons
def OnViewerCreate(node=None):
    """Callback que se ejecuta cuando se crea un viewer"""
    import LGA_viewer_SnapShot_Buttons

    # Usar un timer para retrasar la ejecucion hasta que el widget Qt este listo
    try:
        from PySide2.QtCore import QTimer
    except:
        from PySide.QtCore import QTimer

    # Ejecutar launch() despues de un pequeno delay para que el widget este listo
    QTimer.singleShot(100, LGA_viewer_SnapShot_Buttons.launch)


# Registrar el callback para cuando se cree un viewer
nuke.addOnCreate(OnViewerCreate, nodeClass="Viewer")
