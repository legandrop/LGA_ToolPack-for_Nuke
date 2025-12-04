"""
______________________________________________________

  LGA_NKS_SnapSho_Buttons - Lega
  Crea botones en el viewer para snapshots
______________________________________________________

"""

import nuke
import os

# Obtener la ruta de los iconos
KS_DIR = os.path.dirname(__file__)
icons_path = os.path.join(KS_DIR, "icons")

try:
    # nuke <11
    import PySide.QtGui as QtGui
    import PySide.QtCore as QtCore
    import PySide.QtWidgets as QtWidgets
    from PySide.QtGui import QImage, QClipboard, QIcon
    from PySide.QtWidgets import QApplication, QPushButton, QDialog, QHBoxLayout
except:
    # nuke>=11
    import PySide2.QtGui as QtGui
    import PySide2.QtCore as QtCore
    import PySide2.QtWidgets as QtWidgets
    from PySide2.QtGui import QImage, QClipboard, QIcon
    from PySide2.QtWidgets import QApplication, QPushButton, QDialog, QHBoxLayout


DEBUG = True


def debug_print(*message):
    if DEBUG:
        print(*message)


def launch():
    """Funcion principal que inserta los botones en el viewer"""

    class CustomButton(QPushButton):
        def __init__(self, _text, parent=None):
            super(CustomButton, self).__init__()
            self.setText(_text)
            self.setAcceptDrops(True)
            self.mineData = None
            self._parent = parent

    class Take_SnapShotButton(QDialog):
        """Boton para tomar snapshot"""

        def __init__(self):
            super(Take_SnapShotButton, self).__init__()
            self.generalLayout = QHBoxLayout(self)
            self.generalLayout.setMargin(0)
            self.generalLayout.setSpacing(0)
            self.addShortcutButton = CustomButton("", self)
            self.icon_size = 20
            self.btn_size = 30
            self.qt_icon_size = QtCore.QSize(self.icon_size, self.icon_size)
            self.qt_btn_size = QtCore.QSize(self.btn_size, self.btn_size)

            # Configurar icono y propiedades del boton
            icon_path = os.path.join(icons_path, "snap_camera.png")
            self.addShortcutButton.setIcon(QtGui.QIcon(icon_path))
            self.addShortcutButton.setIconSize(self.qt_icon_size)
            self.addShortcutButton.setFixedSize(self.qt_btn_size)
            self.addShortcutButton.clicked.connect(self.take_snapshot)
            self.addShortcutButton.setFixedWidth(30)
            self.addShortcutButton.setToolTip(
                "(Shift+F9) Take snapshot and save to gallery - Shift+Click to NOT save to gallery"
            )
            self.addShortcutButton.setFlat(True)
            self.generalLayout.addWidget(self.addShortcutButton)

        def take_snapshot(self):
            """Ejecuta la funcion take_snapshot del script LGA_viewer_SnapShot.py"""
            try:
                # Detectar si se presiono Shift
                app = QApplication.instance()
                modifiers = app.keyboardModifiers()
                shift_pressed = modifiers & QtCore.Qt.ShiftModifier

                # Importar y ejecutar el script de snapshot
                script_path = os.path.join(
                    os.path.dirname(__file__), "LGA_viewer_SnapShot.py"
                )
                if os.path.exists(script_path):
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(
                        "LGA_viewer_SnapShot", script_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Llamar a la funcion take_snapshot del script con el parametro shift invertido
                        # Sin shift = guarda en galeria, Con shift = NO guarda en galeria
                        module.take_snapshot(save_to_gallery=not shift_pressed)
                    else:
                        nuke.message("Error: No se pudo cargar el modulo de SnapShot")
                else:
                    nuke.message(f"Error: Script no encontrado en {script_path}")
            except Exception as e:
                nuke.message(f"Error al ejecutar SnapShot: {str(e)}")
                debug_print(f"Error en take_snapshot: {e}")

    class Show_SnapShotButton(QDialog):
        """Boton para mostrar snapshot mientras se mantiene presionado"""

        def __init__(self):
            super(Show_SnapShotButton, self).__init__()
            self.generalLayout = QHBoxLayout(self)
            self.generalLayout.setMargin(0)
            self.generalLayout.setSpacing(0)
            self.addShortcutButton = CustomButton("", self)
            self.icon_size = 20
            self.btn_size = 30
            self.qt_icon_size = QtCore.QSize(self.icon_size, self.icon_size)
            self.qt_btn_size = QtCore.QSize(self.btn_size, self.btn_size)

            # Configurar icono y propiedades del boton
            icon_path = os.path.join(icons_path, "sanp_picture.png")
            self.addShortcutButton.setIcon(QtGui.QIcon(icon_path))
            self.addShortcutButton.setIconSize(self.qt_icon_size)
            self.addShortcutButton.setFixedSize(self.qt_btn_size)
            self.addShortcutButton.setFixedWidth(30)
            self.addShortcutButton.setToolTip("(F9) Show last snapshot in viewer")
            self.addShortcutButton.setFlat(True)
            self.generalLayout.addWidget(self.addShortcutButton)

            # Conectar eventos de press y release
            self.addShortcutButton.pressed.connect(self.on_pressed)
            self.addShortcutButton.released.connect(self.on_released)

            # CRÍTICO: Importar el módulo UNA SOLA VEZ al crear el botón
            self.snapshot_module = None
            self._import_snapshot_module()

        def _import_snapshot_module(self):
            """Importa el módulo de snapshot UNA SOLA VEZ"""
            try:
                script_path = os.path.join(
                    os.path.dirname(__file__), "LGA_viewer_SnapShot.py"
                )
                if os.path.exists(script_path):
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(
                        "LGA_viewer_SnapShot", script_path
                    )
                    if spec and spec.loader:
                        self.snapshot_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(self.snapshot_module)
                        debug_print("✅ Módulo SnapShot importado correctamente")
                    else:
                        debug_print("❌ Error: No se pudo cargar el módulo de SnapShot")
                else:
                    debug_print(f"❌ Error: Script no encontrado en {script_path}")
            except Exception as e:
                debug_print(f"❌ Error al importar módulo SnapShot: {str(e)}")

        def on_pressed(self):
            """Se ejecuta cuando se presiona el boton"""
            debug_print("🔽 Boton presionado - mostrando snapshot")
            self.call_show_snapshot(start=True)

        def on_released(self):
            """Se ejecuta cuando se suelta el boton"""
            debug_print("🔼 Boton liberado - ocultando snapshot")
            self.call_show_snapshot(start=False)

        def call_show_snapshot(self, start):
            """Llama a la funcion show_snapshot_hold del script LGA_viewer_SnapShot.py"""
            try:
                if self.snapshot_module:
                    # USAR EL MÓDULO YA IMPORTADO - NO REIMPORTAR
                    self.snapshot_module.show_snapshot_hold(start)
                else:
                    debug_print("❌ Error: Módulo SnapShot no está disponible")
            except Exception as e:
                debug_print(f"❌ Error al ejecutar show_snapshot_hold: {str(e)}")
                import traceback

                debug_print(f"Traceback: {traceback.format_exc()}")

    class Gallery_SnapShotButton(QDialog):
        """Boton para abrir la galeria de snapshots"""

        def __init__(self):
            super(Gallery_SnapShotButton, self).__init__()
            self.generalLayout = QHBoxLayout(self)
            self.generalLayout.setMargin(0)
            self.generalLayout.setSpacing(0)
            self.addShortcutButton = CustomButton("", self)
            self.icon_size = 20
            self.btn_size = 30
            self.qt_icon_size = QtCore.QSize(self.icon_size, self.icon_size)
            self.qt_btn_size = QtCore.QSize(self.btn_size, self.btn_size)

            # Configurar icono y propiedades del boton
            icon_path = os.path.join(icons_path, "sanp_gallery.png")
            self.addShortcutButton.setIcon(QtGui.QIcon(icon_path))
            self.addShortcutButton.setIconSize(self.qt_icon_size)
            self.addShortcutButton.setFixedSize(self.qt_btn_size)
            self.addShortcutButton.clicked.connect(self.open_gallery)
            self.addShortcutButton.setFixedWidth(30)
            self.addShortcutButton.setToolTip("Open snapshot gallery")
            self.addShortcutButton.setFlat(True)
            self.generalLayout.addWidget(self.addShortcutButton)

        def open_gallery(self):
            """Ejecuta la funcion open_snapshot_gallery del script LGA_viewer_SnapShot_Gallery.py"""
            try:
                # Importar y ejecutar el script de galeria
                script_path = os.path.join(
                    os.path.dirname(__file__), "LGA_viewer_SnapShot_Gallery.py"
                )
                if os.path.exists(script_path):
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(
                        "LGA_viewer_SnapShot_Gallery", script_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Llamar a la funcion open_snapshot_gallery del script
                        module.open_snapshot_gallery()
                    else:
                        nuke.message("Error: No se pudo cargar el modulo de Gallery")
                else:
                    nuke.message(f"Error: Script no encontrado en {script_path}")
            except Exception as e:
                nuke.message(f"Error al ejecutar Gallery: {str(e)}")
                debug_print(f"Error en open_gallery: {e}")

    def find_viewer():
        """Encuentra el widget del viewer activo"""
        try:
            # Primero intentar con el activeViewer
            active_viewer = nuke.activeViewer()
            if active_viewer:
                for widget in QApplication.allWidgets():
                    if (
                        hasattr(widget, "windowTitle")
                        and widget.windowTitle() == active_viewer.node().name()
                    ):
                        debug_print(
                            f"✅ Encontrado widget del viewer activo: {widget.windowTitle()}"
                        )
                        return widget

            # Si no hay activeViewer, buscar cualquier viewer widget
            debug_print("⚠️ No hay activeViewer, buscando viewers disponibles...")
            for widget in QApplication.allWidgets():
                if hasattr(widget, "windowTitle") and widget.windowTitle():
                    title = widget.windowTitle().lower()
                    # Buscar widgets que parezcan viewers (contienen "viewer" o son nodos Viewer)
                    if "viewer" in title or any(
                        node.name() == widget.windowTitle()
                        for node in nuke.allNodes("Viewer")
                    ):
                        debug_print(
                            f"✅ Encontrado widget de viewer: {widget.windowTitle()}"
                        )
                        return widget

        except Exception as e:
            debug_print(f"❌ Error en find_viewer: {e}")

        debug_print("⚠️ No se pudo encontrar ningún widget de viewer")
        return False

    def find_framerange(qtObject):
        """Busca el frameslider y agrega los botones"""
        for c in qtObject.children():
            found = find_framerange(c)
            if found:
                return found
            try:
                tt = c.toolTip().lower()
                if tt.startswith("frameslider range"):
                    # Crear los tres botones
                    take_snapshot_btn = Take_SnapShotButton()
                    show_snapshot_btn = Show_SnapShotButton()
                    gallery_snapshot_btn = Gallery_SnapShotButton()

                    # Limpiar botones existentes si los hay
                    wdgets = c.parentWidget().children()
                    if len(wdgets) >= 3:
                        for x in range(3, len(wdgets)):
                            widget_to_remove = c.parentWidget().children()[x]
                            c.parentWidget().layout().removeWidget(widget_to_remove)
                            widget_to_remove.deleteLater()

                    # Agregar los tres botones al layout
                    c.parentWidget().layout().addWidget(take_snapshot_btn)
                    c.parentWidget().layout().addWidget(show_snapshot_btn)
                    c.parentWidget().layout().addWidget(gallery_snapshot_btn)

                    debug_print(
                        "✅ Botones LGA SnapShot agregados al viewer (Take, Show y Gallery)"
                    )
                    return c
            except:
                pass
        return None

    # Ejecutar la insercion de botones
    viewer_widget = find_viewer()
    if viewer_widget:
        find_framerange(viewer_widget)
        debug_print("✅ Botones agregados exitosamente al viewer")
    else:
        debug_print(
            "⚠️ No se pudo encontrar el widget del viewer - reintentando en 500ms..."
        )
        # Reintentar despues de mas tiempo si no se encontro
        try:
            from PySide2.QtCore import QTimer
        except:
            from PySide.QtCore import QTimer
        QTimer.singleShot(500, launch)
