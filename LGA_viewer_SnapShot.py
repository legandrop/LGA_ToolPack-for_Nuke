"""
______________________________________________________________________________

  LGA_viewer_SnapShot v0.64 - Lega
  Crea un snapshot de la imagen actual del viewer y lo copia al portapapeles
______________________________________________________________________________

"""

import nuke
import nukescripts
import os
import tempfile

try:
    # nuke <11
    import PySide.QtGui as QtGui
    import PySide.QtCore as QtCore
    import PySide.QtWidgets as QtWidgets
    from PySide.QtGui import QImage, QClipboard
    from PySide.QtWidgets import QApplication
    from PySide.QtCore import QTimer, QEventLoop
except:
    # nuke>=11
    import PySide2.QtGui as QtGui
    import PySide2.QtCore as QtCore
    import PySide2.QtWidgets as QtWidgets
    from PySide2.QtGui import QImage, QClipboard
    from PySide2.QtWidgets import QApplication
    from PySide2.QtCore import QTimer, QEventLoop

DEBUG = True

# Variable global para mantener el estado del snapshot hold
_lga_snapshot_hold_state = None


def debug_print(*message):
    if DEBUG:
        print(*message)


def get_next_snapshot_number():
    """
    Obtiene el siguiente numero para el snapshot verificando los archivos existentes.
    Retorna el numero siguiente al mas alto encontrado.
    """
    import glob
    import re

    temp_dir = tempfile.gettempdir()
    pattern = os.path.join(temp_dir, "LGA_snapshot_*.jpg")
    existing_files = glob.glob(pattern)

    if not existing_files:
        debug_print("No hay snapshots existentes, empezando con numero 1")
        return 1

    # Extraer numeros de los archivos existentes
    numbers = []
    for file_path in existing_files:
        filename = os.path.basename(file_path)
        match = re.search(r"LGA_snapshot_(\d+)\.jpg", filename)
        if match:
            numbers.append(int(match.group(1)))

    if numbers:
        next_number = max(numbers) + 1
        debug_print(
            f"Snapshots existentes: {sorted(numbers)}, siguiente numero: {next_number}"
        )
        return next_number
    else:
        debug_print("No se encontraron numeros validos, empezando con numero 1")
        return 1


def cleanup_old_snapshots(current_number):
    """
    Elimina todos los snapshots con numero menor al actual.
    """
    import glob
    import re

    temp_dir = tempfile.gettempdir()
    pattern = os.path.join(temp_dir, "LGA_snapshot_*.jpg")
    existing_files = glob.glob(pattern)

    deleted_count = 0
    for file_path in existing_files:
        filename = os.path.basename(file_path)
        match = re.search(r"LGA_snapshot_(\d+)\.jpg", filename)
        if match:
            file_number = int(match.group(1))
            if file_number < current_number:
                try:
                    os.remove(file_path)
                    debug_print(f"Eliminado snapshot antiguo: {filename}")
                    deleted_count += 1
                except Exception as e:
                    debug_print(f"Error al eliminar {filename}: {e}")

    if deleted_count > 0:
        debug_print(f"Se eliminaron {deleted_count} snapshots antiguos")
    else:
        debug_print("No habia snapshots antiguos para eliminar")


def get_latest_snapshot_path():
    """
    Obtiene la ruta del snapshot con el numero mas alto.
    Retorna None si no encuentra ninguno.
    """
    import glob
    import re

    temp_dir = tempfile.gettempdir()
    pattern = os.path.join(temp_dir, "LGA_snapshot_*.jpg")
    existing_files = glob.glob(pattern)

    if not existing_files:
        debug_print("No se encontraron snapshots existentes")
        return None

    # Encontrar el archivo con el numero mas alto
    max_number = 0
    latest_file = None

    for file_path in existing_files:
        filename = os.path.basename(file_path)
        match = re.search(r"LGA_snapshot_(\d+)\.jpg", filename)
        if match:
            file_number = int(match.group(1))
            if file_number > max_number:
                max_number = file_number
                latest_file = file_path

    if latest_file:
        debug_print(
            f"Snapshot mas reciente encontrado: {os.path.basename(latest_file)} (numero {max_number})"
        )
        return latest_file
    else:
        debug_print("No se encontraron snapshots con numeracion valida")
        return None


def get_project_info():
    """
    Obtiene informacion del proyecto actual de Nuke.
    Retorna tupla (project_name_without_version, full_project_name)
    """
    try:
        script_path = nuke.root().name()
        if not script_path or script_path == "Root":
            debug_print("No hay proyecto guardado, usando nombre generico")
            return "untitled_project", "untitled_project"

        # Obtener solo el nombre del archivo sin extension
        project_name = os.path.splitext(os.path.basename(script_path))[0]
        debug_print(f"Nombre del proyecto: {project_name}")

        # Separar por guiones bajos
        parts = project_name.split("_")

        # Verificar si el ultimo bloque es un numero de version (vXX)
        if (
            len(parts) > 1
            and parts[-1].lower().startswith("v")
            and parts[-1][1:].isdigit()
        ):
            # Hay numero de version
            project_name_without_version = "_".join(parts[:-1])
            debug_print(
                f"Proyecto con version detectado. Sin version: {project_name_without_version}"
            )
        else:
            # No hay numero de version
            project_name_without_version = project_name
            debug_print(
                f"Proyecto sin version detectado: {project_name_without_version}"
            )

        return project_name_without_version, project_name

    except Exception as e:
        debug_print(f"Error al obtener info del proyecto: {e}")
        return "untitled_project", "untitled_project"


def get_next_gallery_number(project_dir, project_name):
    """
    Obtiene el siguiente numero para el archivo en la galeria del proyecto.
    """
    try:
        import glob
        import re

        # Buscar archivos existentes con el patron del proyecto
        pattern = os.path.join(project_dir, f"{project_name}_*.jpg")
        existing_files = glob.glob(pattern)

        if not existing_files:
            debug_print(
                f"No hay archivos existentes para {project_name}, empezando con numero 1"
            )
            return 1

        # Extraer numeros de los archivos existentes
        numbers = []
        for file_path in existing_files:
            filename = os.path.basename(file_path)
            # Buscar el patron: project_name_numero.jpg
            match = re.search(rf"{re.escape(project_name)}_(\d+)\.jpg$", filename)
            if match:
                numbers.append(int(match.group(1)))

        if numbers:
            next_number = max(numbers) + 1
            debug_print(
                f"Archivos existentes para {project_name}: {sorted(numbers)}, siguiente numero: {next_number}"
            )
            return next_number
        else:
            debug_print(
                f"No se encontraron numeros validos para {project_name}, empezando con numero 1"
            )
            return 1

    except Exception as e:
        debug_print(f"Error al obtener siguiente numero: {e}")
        return 1


def save_snapshot_to_gallery(snapshot_path):
    """
    Guarda una copia del snapshot en la carpeta snapshot_gallery.
    Crea subcarpetas por proyecto y numera los archivos secuencialmente.
    """
    try:
        # Obtener informacion del proyecto
        project_name_without_version, full_project_name = get_project_info()

        # Obtener la carpeta del script actual
        script_dir = os.path.dirname(__file__)
        gallery_dir = os.path.join(script_dir, "snapshot_gallery")

        # Crear carpeta de galeria principal si no existe
        if not os.path.exists(gallery_dir):
            os.makedirs(gallery_dir)
            debug_print(f"Carpeta de galeria principal creada: {gallery_dir}")

        # Crear subcarpeta del proyecto si no existe
        project_dir = os.path.join(gallery_dir, project_name_without_version)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            debug_print(f"Subcarpeta de proyecto creada: {project_dir}")

        # Obtener el siguiente numero para este proyecto
        next_number = get_next_gallery_number(project_dir, full_project_name)

        # Generar nombre del archivo
        gallery_filename = f"{full_project_name}_{next_number}.jpg"
        gallery_path = os.path.join(project_dir, gallery_filename)

        # Copiar el archivo a la galeria
        import shutil

        shutil.copy2(snapshot_path, gallery_path)

        debug_print(f"✅ Snapshot guardado en galeria: {gallery_filename}")
        print(
            f"📸 Snapshot guardado en galeria: {project_name_without_version}/{gallery_filename}"
        )

        return gallery_path

    except Exception as e:
        error_msg = f"Error al guardar snapshot en galeria: {str(e)}"
        debug_print(f"ERROR: {error_msg}")
        print(f"❌ {error_msg}")
        return None


def check_render_complete_module():
    """
    Verifica si el modulo LGA_Write_RenderComplete esta disponible y si el sonido esta activado.
    Retorna True si ambas condiciones se cumplen, False en caso contrario.
    """
    try:
        # Intentar importar las funciones necesarias del modulo RenderComplete
        from LGA_Write_RenderComplete import (
            get_sound_enabled_from_config,
            get_wav_path_from_config,
            save_wav_path_to_config,
        )

        # Verificar si el sonido esta activado en la configuracion
        sound_enabled = get_sound_enabled_from_config()
        debug_print(f"RenderComplete encontrado. Sonido activado: {sound_enabled}")
        return sound_enabled

    except ImportError as e:
        debug_print(f"Modulo LGA_Write_RenderComplete no encontrado: {e}")
        return False
    except Exception as e:
        debug_print(f"Error al verificar RenderComplete: {e}")
        return False


def set_silence_wav_temporarily():
    """
    Guarda el wav actual y lo reemplaza temporalmente por el archivo de silencio.
    Retorna el path del wav original para poder restaurarlo despues.
    """
    try:
        from LGA_Write_RenderComplete import (
            get_wav_path_from_config,
            save_wav_path_to_config,
        )

        # Obtener el wav actual
        original_wav_path = get_wav_path_from_config()
        debug_print(f"WAV original: {original_wav_path}")

        # Crear el path del archivo de silencio (en la misma carpeta que este script)
        silence_wav_path = os.path.join(
            os.path.dirname(__file__), "LGA_Write_RenderComplete_silence.wav"
        )

        # Verificar que el archivo de silencio existe
        if not os.path.exists(silence_wav_path):
            debug_print(f"Archivo de silencio no encontrado: {silence_wav_path}")
            return original_wav_path

        # Guardar temporalmente el wav de silencio
        save_wav_path_to_config(silence_wav_path)
        debug_print(f"WAV cambiado temporalmente a: {silence_wav_path}")

        return original_wav_path

    except Exception as e:
        debug_print(f"Error al configurar wav de silencio: {e}")
        return None


def restore_original_wav(original_wav_path):
    """
    Restaura el wav original en la configuracion.
    """
    if not original_wav_path:
        debug_print("No hay wav original para restaurar")
        return

    try:
        from LGA_Write_RenderComplete import save_wav_path_to_config

        save_wav_path_to_config(original_wav_path)
        debug_print(f"WAV restaurado a: {original_wav_path}")

    except Exception as e:
        debug_print(f"Error al restaurar wav original: {e}")


def get_viewer_info():
    """
    Obtiene informacion del viewer activo y el nodo conectado.
    Retorna una tupla (viewer, view_node, input_index, input_node) o None si hay error.
    """
    viewer = nuke.activeViewer()
    if viewer is None:
        debug_print("ERROR: No hay viewer activo.")
        return None

    view_node = viewer.node()
    if view_node is None:
        debug_print("ERROR: El viewer no está mostrando ningún nodo.")
        return None

    input_index = viewer.activeInput()
    if not isinstance(input_index, int):
        debug_print(
            f"ERROR: viewer.activeInput() devolvió un tipo inesperado: {type(input_index)}"
        )
        return None

    input_node = view_node.input(input_index)
    if input_node is None:
        debug_print("ERROR: No hay nodo conectado al viewer en la entrada activa.")
        return None

    return viewer, view_node, input_index, input_node


def get_viewer_info_for_show():
    """
    Obtiene informacion del viewer activo para mostrar snapshot.
    Permite trabajar sin nodo conectado al viewer.
    Retorna una tupla (viewer, view_node, input_index, input_node) donde input_node puede ser None.
    """
    viewer = nuke.activeViewer()
    if viewer is None:
        debug_print("ERROR: No hay viewer activo.")
        return None

    view_node = viewer.node()
    if view_node is None:
        debug_print("ERROR: El viewer no está mostrando ningún nodo.")
        return None

    input_index = viewer.activeInput()

    # Si activeInput() devuelve None (viewer sin nodos), usar input 0 por defecto
    if input_index is None:
        debug_print("INFO: activeInput() es None, usando input 0 por defecto")
        input_index = 0
    elif not isinstance(input_index, int):
        debug_print(
            f"ERROR: viewer.activeInput() devolvió un tipo inesperado: {type(input_index)}"
        )
        return None

    # Para show snapshot, permitimos que input_node sea None
    input_node = view_node.input(input_index)
    if input_node is None:
        debug_print(
            f"INFO: No hay nodo conectado al viewer en input {input_index}, pero se puede mostrar snapshot."
        )

    return viewer, view_node, input_index, input_node


def take_snapshot(save_to_gallery=False):
    # --- Comprobaciones iniciales del viewer de Nuke ---
    viewer_info = get_viewer_info()
    if viewer_info is None:
        nuke.message(
            "No hay viewer activo o nodo conectado. Por favor, conecta un nodo al viewer antes de tomar un snapshot."
        )
        return

    viewer, view_node, input_index, input_node = viewer_info

    # CRÍTICO: Verificar que el nodo tiene canales válidos ANTES de cualquier procesamiento
    try:
        # Obtener los canales del nodo conectado al viewer
        channels = input_node.channels()
        debug_print(f"Canales disponibles en {input_node.name()}: {channels}")

        if not channels:
            error_msg = f"El nodo {input_node.name()} no tiene canales válidos para generar snapshot"
            debug_print(f"ERROR: {error_msg}")
            nuke.message(error_msg)
            return

        # Verificar que hay al menos un canal de color (rgba, rgb, etc.)
        color_channels = [
            ch
            for ch in channels
            if any(
                color in ch.lower()
                for color in ["red", "green", "blue", "rgba", "rgb", ".r", ".g", ".b"]
            )
        ]
        if not color_channels:
            error_msg = f"El nodo {input_node.name()} no tiene canales de color válidos (RGB/RGBA) para generar snapshot"
            debug_print(f"ERROR: {error_msg}")
            nuke.message(error_msg)
            return

        debug_print(f"✅ Canales de color válidos encontrados: {color_channels}")

    except Exception as e:
        error_msg = f"Error al verificar canales del nodo {input_node.name()}: {str(e)}"
        debug_print(f"ERROR: {error_msg}")
        nuke.message(error_msg)
        return

    # --- Una vez que las comprobaciones iniciales son satisfactorias, proceder con la lógica RenderComplete ---
    render_complete_active = check_render_complete_module()
    original_wav_path = None

    # Si RenderComplete esta activo, cambiar temporalmente el wav
    if render_complete_active:
        original_wav_path = set_silence_wav_temporarily()

    try:
        # Obtener el siguiente numero para el snapshot
        snapshot_number = get_next_snapshot_number()
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"LGA_snapshot_{snapshot_number}.jpg")

        frame = int(nuke.frame())

        # Obtener la posicion del nodo de entrada
        input_node_xpos = input_node.xpos()
        input_node_ypos = input_node.ypos()

        # 1. Recordar el nodo seleccionado actualmente
        originally_selected_nodes = list(nuke.selectedNodes())
        debug_print(
            f"Nodos originalmente seleccionados: {[n.name() for n in originally_selected_nodes]}"
        )

        try:
            # 2. Deseleccionar todos los nodos y seleccionar solo el nodo conectado al viewer
            for node in nuke.allNodes():
                node.setSelected(False)
            input_node.setSelected(True)
            debug_print(f"Nodo seleccionado temporalmente: {input_node.name()}")

            # Calcular el offset Y basado en la altura del nodo de entrada
            dynamic_y_offset = input_node.screenHeight() + 10
            debug_print(f"Offset Y dinamico: {dynamic_y_offset}")

            # 3. Crear el Write temporal (ahora se creara conectado al nodo correcto)
            write_node = nuke.createNode(
                "Write",
                "file_type jpeg postage_stamp false hide_input true label 'LGA_TEMP'",
                inpanel=False,
            )

            # Mover el nodo Write a la posicion del nodo de entrada
            write_node.setXpos(input_node_xpos)
            write_node.setYpos(input_node_ypos + dynamic_y_offset)

            # Blindaje: convertir path a forward slashes para evitar problemas de escapes
            safe_path = output_path.replace("\\", "/")
            write_node["file"].setValue(safe_path)

            debug_print("Generando snapshot temporal en:", safe_path)

            try:
                nuke.execute(write_node, frame, frame)
            except Exception as e:
                # Mejorar el manejo de errores del Write
                error_msg = f"Error al ejecutar el Write: {str(e)}"
                debug_print(f"ERROR: {error_msg}")

                # Limpiar el nodo Write antes de mostrar error
                if nuke.exists(write_node.name()):
                    nuke.delete(write_node)

                nuke.message(error_msg)
                return
            finally:
                # Asegurar que el nodo Write se elimine incluso si hay error
                if nuke.exists(write_node.name()):
                    nuke.delete(write_node)
                    debug_print("Nodo Write temporal eliminado correctamente")

        finally:
            # 4. Restaurar la seleccion original
            for node in nuke.allNodes():
                node.setSelected(False)
            for node in originally_selected_nodes:
                if node and nuke.exists(node.name()):
                    node.setSelected(True)
                debug_print(
                    f"Seleccion restaurada: {[n.name() for n in originally_selected_nodes if n]}"
                )

        if not os.path.exists(output_path):
            nuke.message(
                "Error: el archivo del snapshot no se generó. Por favor, verifica los permisos o la ruta temporal."
            )
            return

        # Cargar el JPEG como QImage
        qimage = QtGui.QImage(output_path)
        if qimage.isNull():
            nuke.message(
                "Error al leer el snapshot generado. El archivo de imagen temporal está vacío o corrupto."
            )
            return

        debug_print("Snapshot size:", qimage.width(), "×", qimage.height())

        # Copiar al portapapeles
        app = QApplication.instance()
        if not app:
            app = QApplication([])

        clipboard = app.clipboard()
        clipboard.setImage(qimage)

        debug_print("✅ Imagen copiada al portapapeles.")

        # Si se presiono Shift, guardar en la galeria
        if save_to_gallery:
            gallery_path = save_snapshot_to_gallery(output_path)
            if gallery_path:
                print(f"✅ Snapshot guardado en galeria con Shift")
            else:
                print(f"❌ Error al guardar en galeria")

        # Limpiar snapshots antiguos después del guardado exitoso
        cleanup_old_snapshots(snapshot_number)

        # NO eliminar el archivo temporal - lo necesitamos para show_snapshot()
        debug_print(f"Archivo temporal mantenido para show_snapshot: {output_path}")

    finally:
        # Restaurar el wav original si se cambio temporalmente
        if render_complete_active and original_wav_path:
            restore_original_wav(original_wav_path)


def show_snapshot_hold(start):
    """
    Muestra el snapshot mientras el botón está presionado y lo oculta al soltar.
    Versión simplificada sin QTimer para evitar problemas de timing.

    Args:
        start (bool): True para mostrar el snapshot, False para ocultarlo
    """
    global _lga_snapshot_hold_state

    if start:
        # 1. Obtener el snapshot mas reciente
        snapshot_path = get_latest_snapshot_path()

        if not snapshot_path:
            debug_print("ERROR: No se encontro ningun snapshot en la carpeta temporal")
            print("❌ No hay snapshot disponible para mostrar")
            return

        debug_print(f"Snapshot mas reciente encontrado: {snapshot_path}")

        # 2. Verificar viewer (permite trabajar sin nodo conectado)
        viewer_info = get_viewer_info_for_show()
        if viewer_info is None:
            debug_print("ERROR: No se pudo obtener informacion del viewer")
            print("❌ Error: No hay viewer activo")
            return

        viewer, view_node, input_index, input_node = viewer_info

        if input_node:
            debug_print(
                f"Viewer activo: {view_node.name()}, nodo conectado: {input_node.name()}"
            )
        else:
            debug_print(f"Viewer activo: {view_node.name()}, sin nodo conectado")

        # 3. Guardar estado original
        originally_selected_nodes = list(nuke.selectedNodes())
        debug_print(
            f"Nodos originalmente seleccionados: {[n.name() for n in originally_selected_nodes]}"
        )

        # Obtener posicion para el nodo Read
        viewer_node_xpos = view_node.xpos()
        viewer_node_ypos = view_node.ypos()
        input_node_xpos = viewer_node_xpos
        input_node_ypos = viewer_node_ypos - 100  # Arriba del viewer
        dynamic_y_offset = 0

        debug_print(
            f"Posicion para Read: ({input_node_xpos}, {input_node_ypos + dynamic_y_offset})"
        )

        read_node = None
        try:
            # 4. Deseleccionar todos los nodos y seleccionar el nodo conectado (si existe)
            for node in nuke.allNodes():
                node.setSelected(False)
            if input_node:
                input_node.setSelected(True)

            # 5. Crear nodo Read temporal
            safe_path = snapshot_path.replace("\\", "/")
            read_node = nuke.createNode(
                "Read",
                f"file {{{safe_path}}} label 'LGA_SNAPSHOT_HOLD'",
                inpanel=False,
            )

            # Posicionar el nodo Read
            read_node.setXpos(input_node_xpos)
            read_node.setYpos(input_node_ypos + dynamic_y_offset)

            debug_print(
                f"Nodo Read creado: {read_node.name()} en posicion ({read_node.xpos()}, {read_node.ypos()})"
            )

            # 6. Conectar el Read al viewer
            view_node.setInput(input_index, read_node)
            debug_print(f"Read conectado al viewer en input {input_index}")
            debug_print("✅ No se necesita reload - cada snapshot tiene nombre unico")

            # CRÍTICO: Permitir que la UI procese eventos para evitar bloqueos
            app = QApplication.instance()
            if app:
                app.processEvents()

            # Guardar referencias para poder restaurar despues
            _lga_snapshot_hold_state = {
                "read_node": read_node,
                "original_input_node": input_node,
                "viewer": view_node,
                "input_index": input_index,
                "originally_selected_nodes": list(
                    originally_selected_nodes
                ),  # Convertir a lista
            }

            print("🔽 HOLD SNAPSHOT: Mostrando snapshot")
            debug_print("✅ Estado guardado correctamente para hold")

            # CRÍTICO: Procesar eventos nuevamente después de guardar estado
            if app:
                app.processEvents()

        except Exception as e:
            debug_print(f"Error al mostrar snapshot hold: {e}")
            print(f"❌ Error al mostrar snapshot: {e}")

    else:
        # Restaurar estado original (igual que el finally de show_snapshot)
        debug_print("🔄 Iniciando proceso de restauracion...")

        # CRÍTICO: Procesar eventos antes de restaurar
        app = QApplication.instance()
        if app:
            app.processEvents()

        try:
            if _lga_snapshot_hold_state:
                debug_print("📋 Estado encontrado, procediendo a restaurar...")
                state = _lga_snapshot_hold_state
                read_node = state["read_node"]
                input_node = state["original_input_node"]
                view_node = state["viewer"]
                input_index = state["input_index"]
                originally_selected_nodes = state["originally_selected_nodes"]

                # Verificar que el nodo Read aun existe
                if read_node and nuke.exists(read_node.name()):
                    if input_node:
                        debug_print(
                            f"🔗 Reconectando nodo original: {input_node.name()}"
                        )
                        # Reconectar el nodo original al viewer
                        view_node.setInput(input_index, input_node)
                        debug_print(
                            f"Nodo original {input_node.name()} reconectado al viewer"
                        )
                    else:
                        debug_print("🔗 Desconectando viewer (no habia nodo original)")
                        # Desconectar el viewer ya que no habia nodo original
                        view_node.setInput(input_index, None)

                    # CRÍTICO: Procesar eventos después de reconectar
                    if app:
                        app.processEvents()

                    debug_print(f"🗑️ Eliminando nodo temporal: {read_node.name()}")
                    # Eliminar el nodo Read temporal
                    nuke.delete(read_node)
                    debug_print("Nodo Read temporal eliminado")

                    # CRÍTICO: Procesar eventos después de eliminar
                    if app:
                        app.processEvents()

                # Restaurar seleccion original
                debug_print("🎯 Restaurando seleccion original...")
                for node in nuke.allNodes():
                    node.setSelected(False)
                if originally_selected_nodes:
                    for node in originally_selected_nodes:
                        if node and nuke.exists(node.name()):
                            node.setSelected(True)
                    debug_print(
                        f"Seleccion restaurada: {[n.name() for n in originally_selected_nodes if n]}"
                    )
                else:
                    debug_print("No habia nodos seleccionados originalmente")

                # CRÍTICO: Procesar eventos después de restaurar selección
                if app:
                    app.processEvents()

                # Limpiar el estado
                debug_print("🧹 Limpiando estado...")
                _lga_snapshot_hold_state = None

                print("🔼 HOLD SNAPSHOT: Snapshot ocultado y estado restaurado")
                debug_print("✅ Proceso de restauracion completado exitosamente")

                # CRÍTICO: Procesar eventos finales
                if app:
                    app.processEvents()
            else:
                debug_print("⚠️ No hay estado para restaurar")
                print("⚠️ No hay estado para restaurar")

        except Exception as e:
            debug_print(f"Error al restaurar estado original: {e}")
            print(f"❌ Error al ocultar snapshot: {e}")
            import traceback

            debug_print(f"Traceback completo: {traceback.format_exc()}")
