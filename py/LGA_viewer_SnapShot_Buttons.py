"""
______________________________________________________

  LGA_viewer_SnapShot_Buttons v1.06 | Lega

  Crea botones en el viewer para snapshots

  Donde mas se ve esta version, y hay que moverla junto con el header:
    - El titulo de la seccion "Take/Show Snapshot" del README.md, a mano.

  v1.06: Los tres contenedores pasan de QDialog a QWidget. Un QDialog metido
         en el layout del toolbar del viewer se sigue portando como dialogo:
         con el foco puesto, un Escape le dispara reject() y se esconde solo.
         El widget quedaba vivo y en el layout pero invisible, o sea que el
         boton "desaparecia" despues de usarlo. Los botones ademas dejan de
         tomar foco de teclado, asi que ya no se comen los atajos del viewer.
  v1.03: Shift+Click pasa a componer con el snapshot anterior en vez de
         saltear la galeria. Sin Shift arranca una tira nueva, y todo lo
         que se captura va a la galeria.
  v1.02: El boton de tomar snapshot detecta Ctrl y en ese caso usa el motor
         viejo, el del Write temporal. Va escondido a proposito: no se nombra
         en el tooltip. Sin Ctrl usa capture(), que toma lo que se ve.
  v1.01: Se deja de barrer QApplication.allWidgets() a pelo. Los wrappers
         de widgets ya destruidos en C++ hacian crashear a Nuke con heap
         corruption. Ahora se itera con iter_live_widgets() y se leen los
         metodos con safe_widget_call(). El reintento del timer tiene tope.
  v1.00: Version inicial documentada.
______________________________________________________

"""

import nuke
import os
from LGA_QtAdapter_ToolPack import (
    QtGui,
    QtCore,
    QtWidgets,
    is_widget_alive,
    iter_live_children,
    iter_live_widgets,
    safe_widget_call,
)

# A logs/LGA_viewer_SnapShot.log. La insercion y el borrado de los botones son
# justo lo que no se podia ver cuando uno desaparecia.
from LGA_viewer_SnapShot_logging import debug_print, log_error

# Obtener la ruta de los iconos
KS_DIR = os.path.dirname(__file__)
icons_path = os.path.join(KS_DIR, "icons")

QImage = QtGui.QImage
QClipboard = QtGui.QClipboard
QIcon = QtGui.QIcon
QApplication = QtWidgets.QApplication
QPushButton = QtWidgets.QPushButton
# Los tres botones eran QDialog. Un QDialog metido en el layout de un toolbar
# sigue comportandose como dialogo: con el foco puesto, un Escape le dispara
# reject() y se esconde solo. Verificado con Qt 6.5.3: el widget queda vivo y
# en el layout, pero invisible, que es como "desaparecia" el boton del snapshot
# despues de clickearlo y apretar Escape. QWidget no tiene ese comportamiento.
QWidget = QtWidgets.QWidget
QHBoxLayout = QtWidgets.QHBoxLayout
QSlider = QtWidgets.QSlider
try:
    QAction = QtGui.QAction
except Exception:
    QAction = None

BTN_NAME_TAKE = "LGA_Snapshot_Take"
BTN_NAME_SHOW = "LGA_Snapshot_Show"
BTN_NAME_GALLERY = "LGA_Snapshot_Gallery"


# Tope de reintentos del timer que espera a que el viewer exista.
# 20 x 500 ms = 10 segundos. Sin tope, cada reintento barria la lista de
# widgets del proceso para siempre, que es justo lo que terminaba crasheando.
MAX_LAUNCH_RETRIES = 20


def launch(_retry=0):
    """Funcion principal que inserta los botones en el viewer"""

    class CustomButton(QPushButton):
        def __init__(self, _text, parent=None):
            super(CustomButton, self).__init__()
            self.setText(_text)
            # Sin foco de teclado: si no, despues de clickearlo se queda con el
            # foco y se come los atajos que el usuario le manda al viewer.
            self.setFocusPolicy(QtCore.Qt.NoFocus)
            self.setAcceptDrops(True)
            self.mineData = None
            self._parent = parent

    class Take_SnapShotButton(QWidget):
        """Boton para tomar snapshot"""

        def __init__(self):
            super(Take_SnapShotButton, self).__init__()
            self.setObjectName(BTN_NAME_TAKE)
            self.generalLayout = QHBoxLayout(self)
            self.generalLayout.setContentsMargins(0, 0, 0, 0)
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
                "(Shift+F9) Take snapshot and save to gallery - Shift+Click to append it to the right of the previous one"
            )
            self.addShortcutButton.setFlat(True)
            self.generalLayout.addWidget(self.addShortcutButton)

        def take_snapshot(self):
            """Ejecuta la funcion take_snapshot del script LGA_viewer_SnapShot.py"""
            try:
                # Detectar si se presiono Shift, y si se presiono Ctrl
                app = QApplication.instance()
                modifiers = app.keyboardModifiers()
                shift_pressed = modifiers & QtCore.Qt.ShiftModifier
                # Ctrl es el atajo escondido del motor viejo: no se documenta
                # en el tooltip a proposito.
                ctrl_pressed = modifiers & QtCore.Qt.ControlModifier

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

                        # Shift pega la captura a la derecha de la anterior; sin
                        # Shift arranca una tira nueva. Las dos van a la galeria.
                        module.take_snapshot(
                            save_to_gallery=True,
                            use_write=bool(ctrl_pressed),
                            compare=bool(shift_pressed),
                        )
                    else:
                        nuke.message("Error: No se pudo cargar el modulo de SnapShot")
                else:
                    nuke.message(f"Error: Script no encontrado en {script_path}")
            except Exception as e:
                import traceback

                log_error(f"Error en take_snapshot: {e}")
                log_error(traceback.format_exc())
                nuke.message(f"Error al ejecutar SnapShot: {str(e)}")

    class Show_SnapShotButton(QWidget):
        """Boton para mostrar snapshot mientras se mantiene presionado"""

        def __init__(self):
            super(Show_SnapShotButton, self).__init__()
            self.setObjectName(BTN_NAME_SHOW)
            self.generalLayout = QHBoxLayout(self)
            self.generalLayout.setContentsMargins(0, 0, 0, 0)
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

    class Gallery_SnapShotButton(QWidget):
        """Boton para abrir la galeria de snapshots"""

        def __init__(self):
            super(Gallery_SnapShotButton, self).__init__()
            self.setObjectName(BTN_NAME_GALLERY)
            self.generalLayout = QHBoxLayout(self)
            self.generalLayout.setContentsMargins(0, 0, 0, 0)
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
                nombre_activo = active_viewer.node().name()
                for widget in iter_live_widgets():
                    if safe_widget_call(widget, "windowTitle") == nombre_activo:
                        debug_print(
                            f"✅ Encontrado widget del viewer activo: {nombre_activo}"
                        )
                        return widget

            # Si no hay activeViewer, buscar cualquier viewer widget
            debug_print("⚠️ No hay activeViewer, buscando viewers disponibles...")
            # Los nombres de los nodos Viewer se resuelven una sola vez: antes
            # se consultaba nuke.allNodes() adentro del bucle, por widget.
            nombres_viewer = [node.name() for node in nuke.allNodes("Viewer")]
            for widget in iter_live_widgets():
                titulo = safe_widget_call(widget, "windowTitle", "") or ""
                if not titulo:
                    continue
                # Buscar widgets que parezcan viewers (contienen "viewer" o son nodos Viewer)
                if "viewer" in titulo.lower() or titulo in nombres_viewer:
                    debug_print(f"✅ Encontrado widget de viewer: {titulo}")
                    return widget

        except Exception as e:
            debug_print(f"❌ Error en find_viewer: {e}")

        debug_print("⚠️ No se pudo encontrar ningún widget de viewer")
        return False

    def is_frameslider_widget(w):
        """Detecta el control de frame slider en diferentes versiones de Nuke/Qt."""
        if not is_widget_alive(w):
            return False
        tt = (safe_widget_call(w, "toolTip", "") or "").lower()
        name = (safe_widget_call(w, "objectName", "") or "").lower()
        cls_name = w.__class__.__name__.lower()
        if "frameslider" in tt or "frame slider" in tt:
            return True
        if "frameslider" in name or "frame slider" in name:
            return True
        if "frameslider" in cls_name or "frame slider" in cls_name:
            return True
        try:
            if isinstance(w, QSlider):
                return True
        except Exception:
            pass
        return False

    def find_framerange(root):
        """Busca el frameslider y agrega los botones (Nuke 15/16)."""
        # iter_live_children recorre en anchura salteando los widgets cuyo
        # objeto C++ ya murio, y filtra QAction y layouts por si solo.
        for c in iter_live_children(root):
            try:
                if not is_frameslider_widget(c):
                    continue
                parent = c.parentWidget()
                if not is_widget_alive(parent):
                    continue
                layout = parent.layout()
                if not layout:
                    continue

                take_snapshot_btn = Take_SnapShotButton()
                show_snapshot_btn = Show_SnapShotButton()
                gallery_snapshot_btn = Gallery_SnapShotButton()

                # Remover instancias previas de nuestros botones por objectName
                removidos = []
                for w in list(parent.children()):
                    if not is_widget_alive(w):
                        continue
                    try:
                        nombre = safe_widget_call(w, "objectName")
                        if nombre in (
                            BTN_NAME_TAKE,
                            BTN_NAME_SHOW,
                            BTN_NAME_GALLERY,
                        ):
                            layout.removeWidget(w)
                            w.deleteLater()
                            removidos.append(nombre)
                    except Exception as e:
                        debug_print(f"No se pudo remover un boton previo: {e}")
                        continue
                if removidos:
                    debug_print(f"Botones previos removidos: {removidos}")

                layout.addWidget(take_snapshot_btn)
                layout.addWidget(show_snapshot_btn)
                layout.addWidget(gallery_snapshot_btn)

                debug_print(
                    f"Botones agregados al viewer (Take, Show, Gallery) sobre "
                    f"{parent.metaObject().className()}"
                )
                return c
            except Exception as e:
                debug_print(f"⚠️ Error buscando frame slider: {e}")
        return None

    # Ejecutar la insercion de botones
    debug_print(f"launch() intento {_retry}")
    viewer_widget = find_viewer()
    if viewer_widget:
        if find_framerange(viewer_widget) is None:
            log_error(
                "Se encontro el viewer pero no su frame slider: los botones "
                "NO se insertaron"
            )
    elif _retry >= MAX_LAUNCH_RETRIES:
        # Rendirse: seguir reintentando barria la lista de widgets del proceso
        # cada 500 ms para siempre, aun con el viewer cerrado.
        log_error(
            f"⚠️ No se encontro el widget del viewer despues de "
            f"{MAX_LAUNCH_RETRIES} intentos - se abandona"
        )
    else:
        debug_print(
            f"⚠️ No se pudo encontrar el widget del viewer - reintento "
            f"{_retry + 1}/{MAX_LAUNCH_RETRIES} en 500ms..."
        )
        # Reintentar despues de mas tiempo si no se encontro
        QtCore.QTimer.singleShot(500, lambda: launch(_retry + 1))
