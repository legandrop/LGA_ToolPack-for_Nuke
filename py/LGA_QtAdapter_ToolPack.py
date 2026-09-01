"""
Compatibilidad Qt para Nuke 15/16.
"""

from typing import Optional

try:  # PySide6 primero (Nuke 16)
    from PySide6 import QtWidgets, QtGui, QtCore
    from PySide6.QtGui import QAction, QShortcut, QGuiApplication
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    PYSIDE_VER = 6
except ImportError:  # PySide2 (Nuke 15)
    from PySide2 import QtWidgets, QtGui, QtCore
    from PySide2.QtCore import Qt

    try:
        from PySide2.QtGui import QAction, QShortcut  # Qt5 a veces lo expone aqui
    except ImportError:
        from PySide2.QtWidgets import QAction, QShortcut  # fallback QtWidgets
    from PySide2.QtGui import QGuiApplication
    from PySide2.QtWidgets import QApplication

    PYSIDE_VER = 2


def horizontal_advance(metrics: QtGui.QFontMetrics, text: str) -> int:
    """
    Ancho de texto compatible (Qt6 usa horizontalAdvance).
    """
    if hasattr(metrics, "horizontalAdvance"):
        return metrics.horizontalAdvance(text)
    return metrics.width(text)


def primary_screen_geometry(pos: Optional[QtCore.QPoint] = None) -> QtCore.QRect:
    """
    Geometry del monitor principal o del monitor bajo pos.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        return QtCore.QRect(0, 0, 1920, 1080)

    screen = None
    if pos is not None and hasattr(QGuiApplication, "screenAt"):
        screen = QGuiApplication.screenAt(pos)
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    geo = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1920, 1080)
    return geo


def set_layout_margin(layout: QtWidgets.QLayout, margin: int) -> None:
    """
    Establecer margen de layout compatible Qt5/Qt6.
    En Qt6 usa setContentsMargins, en Qt5 usa setMargin.
    """
    if hasattr(layout, "setContentsMargins"):
        layout.setContentsMargins(margin, margin, margin, margin)
    else:
        layout.setMargin(margin)


# ----------------------------------------------------------------------
# Widgets vivos: guarda contra wrappers de objetos C++ ya destruidos
# ----------------------------------------------------------------------
# QApplication.allWidgets() devuelve wrappers Python de TODOS los widgets del
# proceso, incluidos los que Qt ya destruyo del lado C++ y los que estan
# encolados por deleteLater(). Tocar uno de esos (windowTitle(), objectName(),
# toolTip()) puede tocar un wrapper ya invalidado: en Windows la llamada
# (0xc0000374) al abrir un script, o como access violation dentro de
# QWidget::~QWidget en cualquier garbage collect posterior. Antes de tocar un
# widget ajeno hay que preguntarle a shiboken si el objeto C++ sigue existiendo.

try:  # shiboken viaja con PySide: 6 en Nuke 16/17, 2 en Nuke 15
    if PYSIDE_VER >= 6:
        import shiboken6 as _shiboken
    else:
        import shiboken2 as _shiboken
except ImportError:  # build de Nuke sin shiboken expuesto
    _shiboken = None


def is_widget_alive(widget) -> bool:
    """
    True si el objeto C++ detras del wrapper de PySide sigue vivo.
    Sin shiboken cae a un acceso de prueba: PySide tira RuntimeError cuando el
    C++ ya murio.
    """
    if widget is None:
        return False
    if _shiboken is not None:
        try:
            return bool(_shiboken.isValid(widget))
        except Exception:
            return False
    # Sin shiboken no hay forma de preguntar si el C++ sigue vivo sin tocar el
    # widget, y tocarlo es justamente lo que crashea. Se asume vivo y se deja
    # que los try/except de safe_widget_call absorban lo que puedan.
    return True


def safe_widget_call(widget, method_name: str, default=None):
    """
    Llama a un metodo sin argumentos del widget (objectName, windowTitle,
    toolTip, isVisible) y devuelve default si el widget ya murio.
    """
    if not is_widget_alive(widget):
        return default
    try:
        method = getattr(widget, method_name, None)
        if method is None:
            return default
        return method()
    except Exception:
        return default



def widget_property(widget, name, default=""):
    """
    Lee una propiedad dinamica de un widget ajeno revalidando antes el objeto
    C++. safe_widget_call solo cubre metodos sin argumentos, y property() lleva
    uno.
    """
    if not is_widget_alive(widget):
        return default
    try:
        value = widget.property(name)
    except Exception:
        return default
    return default if value is None else str(value)

def iter_live_widgets(only_top_level: bool = False):
    """
    Itera los widgets de la aplicacion descartando los que ya murieron en C++.

    NO usa QApplication.allWidgets(). Esa llamada es la que corrompia el heap
    (STATUS_HEAP_CORRUPTION, 0xc0000374) al abrir un script: materializa de
    golpe un wrapper de PySide por cada widget del proceso, justo mientras Nuke
    esta creando y destruyendo widgets. Envolverla en guardas no alcanzaba,
    porque el crash pasa adentro de allWidgets(), antes de que la guarda llegue
    a mirar nada.

    En su lugar baja desde topLevelWidgets(): todo QWidget o es top level o
    desciende de uno, asi que el conjunto es el mismo, pero se arma de a poco y
    validando cada paso.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        return
    try:
        raices = list(QtWidgets.QApplication.topLevelWidgets())
    except Exception:
        return
    for raiz in raices:
        if not is_widget_alive(raiz):
            continue
        if only_top_level:
            yield raiz
            continue
        for widget in iter_live_children(raiz):
            yield widget


def iter_live_children(root, include_root: bool = True):
    """
    Recorre en anchura el arbol de widgets colgado de root, salteando los
    muertos. Menos superficie de riesgo que barrer allWidgets() entero.
    """
    if not is_widget_alive(root):
        return
    queue = [root]
    while queue:
        widget = queue.pop(0)
        if not is_widget_alive(widget):
            continue
        if include_root or widget is not root:
            yield widget
        try:
            children = list(widget.children())
        except Exception:
            continue
        for child in children:
            if isinstance(child, QtWidgets.QWidget) and is_widget_alive(child):
                queue.append(child)


__all__ = [
    "QtWidgets",
    "QtGui",
    "QtCore",
    "QAction",
    "QShortcut",
    "QGuiApplication",
    "Qt",
    "QApplication",
    "PYSIDE_VER",
    "horizontal_advance",
    "primary_screen_geometry",
    "set_layout_margin",
    "is_widget_alive",
    "safe_widget_call",
    "widget_property",
    "iter_live_widgets",
    "iter_live_children",
]
