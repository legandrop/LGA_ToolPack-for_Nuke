"""
_______________________________________

  LGA_restartNukeX v1.2 | Lega
_______________________________________

"""

import nuke
import os
import subprocess
import time


def is_nuke_ready_to_exit():
    # Verifica si no hay cambios no guardados
    return not nuke.Root().modified()


def close_script():
    # Cerrar el script actual de Nuke
    nuke.scriptClose()


def check_and_exit(XS):
    # Cierra el script actual
    close_script()

    # Verifica cada medio segundo si Nuke esta listo para cerrarse
    while not is_nuke_ready_to_exit():
        time.sleep(0.5)

    # Cerrar Nuke y abrir una nueva instancia de NukeX
    defineNuke = '"' + nuke.env["ExecutablePath"] + '"'
    if XS == 1:
        defineNuke += " --nukex"
    elif XS == 2:
        defineNuke += " --studio"

    try:
        subprocess.Popen(defineNuke, shell=True)
    except Exception as e:
        print(f"Failed to open NukeX: {e}")

    nuke.scriptExit()


# Evitar que el script se ejecute al ser importado
if __name__ == "__main__":
    # Solo ejecutar el script si se llama directamente
    check_and_exit(1)
