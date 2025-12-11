"""
Capa de compatibilidad PySide6 ↔ PySide2 para Nuke 15/16.
Importa QtWidgets, QtGui, QtCore, QAction y QGuiApplication con fallback.
"""

try:
    from PySide6 import QtWidgets, QtGui, QtCore  # type: ignore
    from PySide6.QtGui import QAction, QGuiApplication  # type: ignore
    PYSIDE_VERSION = 6
except ImportError:  # PySide2 (Nuke ≤15)
    from PySide2 import QtWidgets, QtGui, QtCore  # type: ignore
    try:
        from PySide2.QtGui import QAction  # type: ignore
    except ImportError:
        from PySide2.QtWidgets import QAction  # type: ignore
    from PySide2.QtGui import QGuiApplication  # type: ignore
    PYSIDE_VERSION = 2

__all__ = ["QtWidgets", "QtGui", "QtCore", "QAction", "QGuiApplication", "PYSIDE_VERSION"]


