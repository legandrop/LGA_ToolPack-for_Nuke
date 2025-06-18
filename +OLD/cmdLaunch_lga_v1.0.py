'''
cmdLaunch v1.2 - mod lega v1.0
Relaunch Nuke with terminal to display and keep log of error messages.

Added list of terminals, now compatible with different linux distros
'''
import nuke
import os
import subprocess
from platform import system
from distutils.spawn import find_executable

def isNot_exec(name):
    #check whether terminal program exists
    return find_executable(name) is None

def findTerminal():
    termList = ["x-terminal-emulator", "konsole", "gnome-terminal", "urxvt", "rxvt", "termit", "terminator", "Eterm", "aterm", "uxterm", "xterm", "roxterm", "xfce4-terminal", "termite", "lxterminal", "mate-terminal", "terminology", "st", "qterminal", "lilyterm", "tilix", "terminix", "kitty", "guake", "tilda", "alacritty", "hyper"]
    #list taken from https://github.com/i3/i3/blob/next/i3-sensible-terminal
    for term in termList:
        if not isNot_exec(term):
            return term
    return None

def NOcmdLaunch(XS):
    defineNuke = '"' + nuke.env["ExecutablePath"] + '"'
    if XS == 1:
        defineNuke += " --nukex"
    elif XS == 2:
        defineNuke += " --studio"

    try:
        subprocess.Popen(defineNuke, shell=True)
    except Exception as e:
        print(f"Failed to open NukeX: {e}")

    # Cerrar Nuke actual
    nuke.scriptExit()

# Ejecutar la funcion cmdLaunch con XS = 1 para abrir NukeX
#NOcmdLaunch(1)
