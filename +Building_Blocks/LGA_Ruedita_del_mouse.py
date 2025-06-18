import nuke
from PySide2 import QtWidgets, QtCore, QtGui


class MiddleClickInterceptor(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.start_pos = None  # Guarda la posición inicial del clic

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.MiddleButton:
                widget = QtWidgets.QApplication.instance().widgetAt(QtGui.QCursor.pos())
                if not self.is_dag_widget(widget):
                    return False  # Ignora clicks fuera del DAG
                self.start_pos = event.pos()
                return False

        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.MiddleButton and self.start_pos:
                widget = QtWidgets.QApplication.instance().widgetAt(QtGui.QCursor.pos())
                if not self.is_dag_widget(widget):
                    self.start_pos = None
                    return False  # Ignora releases fuera del DAG

                end_pos = event.pos()
                distance = (end_pos - self.start_pos).manhattanLength()

                if distance < 5:
                    self.start_pos = None
                    QtCore.QTimer.singleShot(10, self.force_mouse_release)
                    QtCore.QTimer.singleShot(
                        50, lambda: nuke.message("Ruedita del mouse apretada")
                    )
                    return True

                self.start_pos = None
                return False

        return False

    def is_dag_widget(self, widget):
        """Devuelve True si el widget es el DAG o un hijo del DAG."""
        while widget:
            if widget.objectName() == "DAG.1":
                return True
            widget = widget.parent()
        return False

    def force_mouse_release(self):
        """Envía manualmente un evento de liberación del botón del medio."""
        widget = QtWidgets.QApplication.instance().widgetAt(
            QtGui.QCursor.pos()
        )  # Obtiene el widget actual
        if widget:
            release_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonRelease,
                QtGui.QCursor.pos(),  # Usa la posición actual del cursor
                QtCore.Qt.MiddleButton,
                QtCore.Qt.NoButton,
                QtCore.Qt.NoModifier,
            )
            QtWidgets.QApplication.sendEvent(widget, release_event)  # Envía el evento


# Instalar el filtro en la aplicación de Nuke
app = QtWidgets.QApplication.instance()
if app:
    interceptor = MiddleClickInterceptor()
    app.installEventFilter(interceptor)
