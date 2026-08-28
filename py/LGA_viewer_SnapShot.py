"""
______________________________________________________________________________

  LGA_viewer_SnapShot v1.06 | Lega

  Crea un snapshot de lo que se ve en el viewer, lo copia al portapapeles y
  puede guardarlo en la galeria del proyecto.

  Modulos de esta tool (todos van con la misma version):
    LGA_viewer_SnapShot.py          <- este, el principal
    LGA_viewer_SnapShot_Buttons.py
    LGA_viewer_SnapShot_Gallery.py
    LGA_viewer_SnapShot_logging.py

  Donde mas se ve esta version, y hay que moverla junto con el header:
    - El titulo de la seccion "Take/Show Snapshot" del README.md, que es a mano.

  v1.05: El snapshot se publica en el portapapeles como CF_DIB con
         SetClipboardData en vez de dejarselo a Qt. Qt lo hace por OLE con
         renderizado diferido, y como justo despues venian el guardado en la
         galeria y la limpieza —las dos IO sincronica—, el hilo no volvia al
         event loop a tiempo: medido, con 0.3 s de bloqueo la entrada del
         historial de Windows se pierde y el portapapeles queda con los datos
         en NULL. Con CF_DIB los bytes quedan materializados en 10 ms. El
         camino de Qt sigue como respaldo, y la copia pasa a ser lo ultimo.
  v1.03: take_snapshot() suma compare=True, que pega la captura nueva a la
         derecha del snapshot anterior. Como la compo se guarda como el
         snapshot siguiente, encadenar es volver a pedir compare y la tira
         crece de a una captura: sirve para armar de a un shortcut la
         comparacion plate / trabajo / propuesta que antes se hacia a mano en
         Photoshop. El alto lo manda la mas alta y la mas baja se ancla abajo.
         Se va la opcion de capturar sin guardar en galeria: ahora Shift
         significa componer, y todo lo que se captura va a la galeria.
  v1.02: El snapshot pasa a tomarse con view_node.capture(), que devuelve el
         framebuffer del viewer: sale con el viewerProcess, el gain y el gamma
         aplicados, y respetando el encuadre que tenga el usuario. Antes se
         renderizaba un Write temporal, que salia lineal y siempre con la
         imagen entera. Como capture() entrega el viewport completo, se le
         miden las bandas de fondo y se recortan borde por borde. El motor
         viejo queda accesible con Ctrl, porque es el unico que da resolucion
         completa del proyecto. Los tres modulos venian con versiones
         distintas (0.65 / 1.01 / 0.56) y se unifican aca.
______________________________________________________________________________

"""

import nuke
import nukescripts
import os
import struct
import sys
import tempfile
from LGA_QtAdapter_ToolPack import QtGui, QtCore, QtWidgets

# El debug va a logs/LGA_viewer_SnapShot.log. Antes era un print a consola con
# DEBUG = False, o sea que cuando algo fallaba no quedaba rastro de nada.
from LGA_viewer_SnapShot_logging import debug_print, log_error

QImage = QtGui.QImage
QClipboard = QtGui.QClipboard
QApplication = QtWidgets.QApplication
QTimer = QtCore.QTimer
QEventLoop = QtCore.QEventLoop

# Variable global para mantener el estado del snapshot hold
_lga_snapshot_hold_state = None


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


# ---------------------------------------------------------------------------
# Motor de captura del viewer
#
# view_node.capture(path) escribe el framebuffer del viewport tal como se ve:
# con el viewerProcess, el gain, el gamma y el encuadre que tenga puesto el
# usuario, y sin renderizar nada. Es lo mismo que hace el boton Capture del
# viewer (ver nukescripts/captureViewer.py adentro de Nuke), pero sin tocar el
# knob 'file' del Viewer ni pasar por executeMultiple: medido, da un archivo
# identico byte a byte y tarda cinco veces menos.
#
# Lo que devuelve es el VIEWPORT entero, asi que cuando la imagen no lo llena
# quedan bandas de fondo alrededor. Esas bandas se miden y se recortan borde
# por borde. La regla es una sola y no hay que adivinar si el usuario quiso ver
# la imagen entera o esta zoomeando: se recorta el vacio que sobre en cada eje.
# En fit sobra y se recorta; zoomeado no sobra y queda el viewport, que es
# justo lo que se esta viendo.
# ---------------------------------------------------------------------------

# Cuanto puede desviarse un canal y seguir contando como fondo.
CROP_TOLERANCIA = 3
# Menos de esto es el redondeo del viewer, no una banda de fondo.
CROP_UMBRAL_BANDA = 3
# Se mira un pixel cada N a lo largo de la linea.
CROP_PASO = 4
# Una banda no puede pasar de esta fraccion de la dimension.
CROP_LIMITE = 0.45
# Diferencia admitida entre el zoom deducido en X y el deducido en Y.
CROP_TOL_ZOOM = 0.02


def _rgb(pixel):
    return ((pixel >> 16) & 255, (pixel >> 8) & 255, pixel & 255)


def _mismo_color(a, b):
    return (
        abs(a[0] - b[0]) <= CROP_TOLERANCIA
        and abs(a[1] - b[1]) <= CROP_TOLERANCIA
        and abs(a[2] - b[2]) <= CROP_TOLERANCIA
    )


def _parece_uniforme(qimage, muestras=24):
    """
    Mira una grilla rala: si TODO el viewport es del color del borde, no hay
    imagen que medir.

    Sirve para dos cosas. Una, evitar el recorte absurdo de un frame plano
    —fundido a negro, un Constant, el viewer todavia sin renderizar—. La otra
    es de velocidad: sin este corte, un viewport 4K uniforme obliga al escaneo
    fino a recorrer el 45% de cada borde a mano, medido casi dos segundos con
    la UI congelada.
    """
    ancho, alto = qimage.width(), qimage.height()
    fondo = _rgb(qimage.pixel(0, 0))
    for i in range(muestras):
        x = int(i * (ancho - 1) / float(muestras - 1)) if muestras > 1 else 0
        for j in range(muestras):
            y = int(j * (alto - 1) / float(muestras - 1)) if muestras > 1 else 0
            if not _mismo_color(_rgb(qimage.pixel(x, y)), fondo):
                return False
    return True


def _medir_bandas(qimage):
    """Cuenta las filas y columnas de fondo uniforme pegadas a cada borde."""
    ancho, alto = qimage.width(), qimage.height()
    fondo = _rgb(qimage.pixel(0, 0))

    def fila_es_fondo(y):
        for x in range(0, ancho, CROP_PASO):
            if not _mismo_color(_rgb(qimage.pixel(x, y)), fondo):
                return False
        return True

    def columna_es_fondo(x):
        for y in range(0, alto, CROP_PASO):
            if not _mismo_color(_rgb(qimage.pixel(x, y)), fondo):
                return False
        return True

    tope_vertical = int(alto * CROP_LIMITE)
    tope_horizontal = int(ancho * CROP_LIMITE)
    arriba = abajo = izquierda = derecha = 0
    while arriba < tope_vertical and fila_es_fondo(arriba):
        arriba += 1
    while abajo < tope_vertical and fila_es_fondo(alto - 1 - abajo):
        abajo += 1
    while izquierda < tope_horizontal and columna_es_fondo(izquierda):
        izquierda += 1
    while derecha < tope_horizontal and columna_es_fondo(ancho - 1 - derecha):
        derecha += 1
    return arriba, abajo, izquierda, derecha


def _rect_visible(qimage, format_w, format_h, pixel_aspect):
    """
    Devuelve el (x, y, ancho, alto) de la imagen adentro del viewport.

    La medicion se valida sola, porque el zoom del viewer es UN solo numero
    para los dos ejes: si hay banda en los dos, el zoom deducido de cada uno
    tiene que dar igual; y si hay banda en uno solo, ese zoom tiene que
    predecir que el otro eje desborda el viewport, que es por lo que ese otro
    eje no tiene banda.

    Cuando la cuenta no cierra, lo que se midio como vacio era negro del propio
    material —un plate con letterbox quemado, un fundido a negro— y entonces no
    se recorta nada, que es el resultado seguro: deja algo de fondo de mas, en
    vez de comerse media imagen.
    """
    ancho, alto = qimage.width(), qimage.height()
    viewport_entero = (0, 0, ancho, alto)

    if _parece_uniforme(qimage):
        debug_print("El viewport es de un solo color: no se recorta nada")
        return viewport_entero

    arriba, abajo, izquierda, derecha = _medir_bandas(qimage)
    debug_print(
        f"Bandas de fondo -> arriba {arriba}, abajo {abajo}, "
        f"izq {izquierda}, der {derecha}"
    )

    # Si una banda llego al tope, no se encontro el borde de la imagen: se
    # freno el escaneo. Recortar con esa medida da un recorte inventado, y
    # ademas puede pasar la validacion de zoom de casualidad cuando el
    # viewport y el material tienen el mismo aspecto, porque los dos ejes se
    # cortan en la misma proporcion.
    tope_vertical = int(alto * CROP_LIMITE)
    tope_horizontal = int(ancho * CROP_LIMITE)
    if (
        arriba >= tope_vertical
        or abajo >= tope_vertical
        or izquierda >= tope_horizontal
        or derecha >= tope_horizontal
    ):
        debug_print("Una banda llego al tope: la medicion no sirve, no se recorta")
        return viewport_entero
    hay_banda_vertical = arriba >= CROP_UMBRAL_BANDA and abajo >= CROP_UMBRAL_BANDA
    hay_banda_horizontal = (
        izquierda >= CROP_UMBRAL_BANDA and derecha >= CROP_UMBRAL_BANDA
    )
    if not hay_banda_vertical and not hay_banda_horizontal:
        debug_print("La imagen desborda el viewport, no se recorta nada")
        return viewport_entero

    x = izquierda if hay_banda_horizontal else 0
    y = arriba if hay_banda_vertical else 0
    rect_ancho = (ancho - izquierda - derecha) if hay_banda_horizontal else ancho
    rect_alto = (alto - arriba - abajo) if hay_banda_vertical else alto

    if not format_w or not format_h:
        debug_print("Sin formato del input: se recorta sin poder validar")
        return (x, y, rect_ancho, rect_alto)

    # Un PAR en cero o negativo es un dato corrupto y dividiria por cero. Se
    # asume 1.0, que es lo que tiene casi todo, en vez de saltear la validacion.
    if not pixel_aspect or pixel_aspect <= 0:
        debug_print(f"PAR invalido ({pixel_aspect}), se asume 1.0")
        pixel_aspect = 1.0

    zoom_x = rect_ancho / float(format_w * pixel_aspect) if hay_banda_horizontal else None
    zoom_y = rect_alto / float(format_h) if hay_banda_vertical else None

    if zoom_x is not None and zoom_y is not None:
        diferencia = abs(zoom_x - zoom_y) / max(zoom_x, zoom_y)
        debug_print(
            f"zoom_x {zoom_x:.4f} / zoom_y {zoom_y:.4f} -> difieren {diferencia:.2%}"
        )
        if diferencia > CROP_TOL_ZOOM:
            debug_print("Los dos ejes no dan el mismo zoom: no se recorta")
            return viewport_entero
    else:
        zoom = zoom_x if zoom_x is not None else zoom_y
        if zoom_x is not None:
            previsto, real, eje = format_h * zoom, alto, "alto"
        else:
            previsto, real, eje = format_w * pixel_aspect * zoom, ancho, "ancho"
        debug_print(f"zoom {zoom:.4f} -> el {eje} daria {previsto:.0f} de {real}")
        if previsto < real - 2:
            debug_print("Ese eje deberia tener banda y no la tiene: no se recorta")
            return viewport_entero

    return (x, y, rect_ancho, rect_alto)


def _snapshot_con_capture(output_path, view_node, input_node):
    """
    Motor nuevo: le pide al viewer su propio framebuffer y le saca el vacio.

    Sale a la resolucion del viewport y con el look del viewer. No crea nodos,
    no toca la seleccion y no dispara ningun callback de render.
    """
    safe_path = output_path.replace("\\", "/")
    try:
        view_node.capture(safe_path)
    except Exception as e:
        error_msg = f"Error al capturar el viewer: {str(e)}"
        debug_print(f"ERROR: {error_msg}")
        nuke.message(error_msg)
        return False

    if not os.path.exists(output_path):
        nuke.message(
            "Error: el archivo del snapshot no se generó. Por favor, verifica los permisos o la ruta temporal."
        )
        return False

    qimage = QImage(output_path)
    if qimage.isNull():
        nuke.message(
            "Error al leer el snapshot generado. El archivo de imagen temporal está vacío o corrupto."
        )
        return False

    format_w = format_h = None
    pixel_aspect = 1.0
    try:
        formato = input_node.format()
        format_w, format_h = formato.width(), formato.height()
        pixel_aspect = formato.pixelAspect()
        debug_print(f"Formato del input: {format_w}x{format_h} PAR {pixel_aspect}")
    except Exception as e:
        debug_print(f"No se pudo leer el formato de {input_node.name()}: {e}")

    x, y, ancho, alto = _rect_visible(qimage, format_w, format_h, pixel_aspect)
    if (ancho, alto) == (qimage.width(), qimage.height()):
        debug_print(f"Snapshot sin recorte: {ancho} x {alto}")
        return True

    # Se pisa el mismo archivo con el recorte. Es una segunda pasada de JPEG
    # sobre lo que capture() ya escribio en JPEG, pero a calidad 95 no se nota,
    # y evita el PNG intermedio, que medido tarda veinte veces mas.
    recorte = qimage.copy(x, y, ancho, alto)
    if not recorte.save(safe_path, "JPEG", 95):
        nuke.message("Error al guardar el snapshot recortado.")
        return False

    debug_print(f"Snapshot recortado a {ancho} x {alto} desde ({x}, {y})")
    return True


def _componer_con_anterior(anterior_path, nueva_path, salida_path):
    """
    Pega la captura nueva a la DERECHA de la anterior y guarda el resultado.

    Sirve para ir armando de a un shortcut la tira que despues va al vendor:
    plate, lo que hizo, lo que haria. Como la compo se guarda como el snapshot
    siguiente, el proximo Shift vuelve a componer contra ella y la tira crece
    sola, sin ningun archivo de estado aparte.

    El alto lo manda la mas alta de las dos. La mas baja se ancla ABAJO, asi
    que el relleno negro queda arriba.
    """
    anterior = QImage(anterior_path)
    nueva = QImage(nueva_path)
    if anterior.isNull() or nueva.isNull():
        debug_print("No se pudo leer alguna de las dos imagenes a componer")
        return False

    ancho = anterior.width() + nueva.width()
    alto = max(anterior.height(), nueva.height())
    if ancho <= 0 or alto <= 0:
        debug_print("Medidas invalidas para la compo")
        return False

    compo = QImage(ancho, alto, QImage.Format_RGB32)
    compo.fill(QtGui.QColor(0, 0, 0))

    painter = QtGui.QPainter(compo)
    try:
        painter.drawImage(0, alto - anterior.height(), anterior)
        painter.drawImage(anterior.width(), alto - nueva.height(), nueva)
    finally:
        # Si el painter sigue activo, el QImage no se puede guardar.
        painter.end()

    # Calidad 100: la parte vieja se re-comprime en cada paso de la cadena, y
    # a la tercera o cuarta captura la perdida acumulada ya se notaria.
    if not compo.save(salida_path.replace("\\", "/"), "JPEG", 100):
        debug_print(f"No se pudo guardar la compo en {salida_path}")
        # Qt crea el archivo ANTES de fallar y lo deja en cero bytes. Si queda,
        # pasa a ser el snapshot mas alto: el Hold intentaria leerlo y la
        # proxima compo se armaria contra un JPEG vacio. Se borra siempre.
        try:
            if os.path.exists(salida_path):
                os.remove(salida_path)
        except Exception as e:
            debug_print(f"No se pudo borrar la compo fallida: {e}")
        return False

    debug_print(
        f"Compo: {anterior.width()}x{anterior.height()} + "
        f"{nueva.width()}x{nueva.height()} -> {ancho}x{alto}"
    )
    return True


def _snapshot_con_write(output_path, input_node):
    """
    Motor viejo, escondido detras de Ctrl y sin documentar en los tooltips.

    Renderiza con un Write temporal el nodo conectado al viewer. Es mas lento y
    no respeta el encuadre, pero sale a la resolucion completa del proyecto, y
    por eso se mantiene.
    """
    # CRÍTICO: Verificar que el nodo tiene canales válidos ANTES de cualquier procesamiento
    try:
        # Obtener los canales del nodo conectado al viewer
        channels = input_node.channels()
        debug_print(f"Canales disponibles en {input_node.name()}: {channels}")

        if not channels:
            error_msg = f"El nodo {input_node.name()} no tiene canales válidos para generar snapshot"
            debug_print(f"ERROR: {error_msg}")
            nuke.message(error_msg)
            return False

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
            return False

        debug_print(f"✅ Canales de color válidos encontrados: {color_channels}")

    except Exception as e:
        error_msg = f"Error al verificar canales del nodo {input_node.name()}: {str(e)}"
        debug_print(f"ERROR: {error_msg}")
        nuke.message(error_msg)
        return False

    # --- Una vez que las comprobaciones iniciales son satisfactorias, proceder con la lógica RenderComplete ---
    render_complete_active = check_render_complete_module()
    original_wav_path = None

    # Si RenderComplete esta activo, cambiar temporalmente el wav
    if render_complete_active:
        original_wav_path = set_silence_wav_temporarily()

    try:
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
                return False
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
            return False

        return True

    finally:
        # Restaurar el wav original si se cambio temporalmente
        if render_complete_active and original_wav_path:
            restore_original_wav(original_wav_path)


# ---------------------------------------------------------------------------
# Portapapeles
#
# Qt publica el portapapeles por OLE con renderizado DIFERIDO: anuncia los
# formatos pero no materializa los bytes hasta que alguien se los pide, y para
# contestar necesita que el proceso vuelva al event loop. Si despues de copiar
# el hilo sigue ocupado —aca mismo venian el guardado en la galeria y la
# limpieza de temporales, las dos IO sincronica—, el servicio del historial de
# Windows no llega a leer nada.
#
# Medido: con 0.3 s de hilo bloqueado despues del setImage, el snapshot ya no
# entra al historial, y el portapapeles queda con los formatos anunciados y los
# datos en NULL. Mientras dura el bloqueo, cualquier otra app que intente pegar
# recibe ACCESS_DENIED. Eso explicaba que el historial se "borrara" a veces: no
# se borraba, se rompia la entrada.
#
# Publicando CF_DIB con SetClipboardData los bytes quedan materializados en el
# acto y no dependen de que el proceso conteste nada. Es lo mismo que hace
# ShareX, que por eso nunca falla. Windows sintetiza CF_BITMAP y CF_DIBV5 solo,
# asi que alcanza con publicar CF_DIB.
# ---------------------------------------------------------------------------

GMEM_MOVEABLE = 0x0002
CF_DIB = 8
BITMAPINFOHEADER_SIZE = 40

_clipboard_api = None
_clipboard_api_buscada = False


def _get_clipboard_api():
    """
    Devuelve (ctypes, user32, kernel32) con las firmas declaradas, o None si
    no es Windows o algo falla.

    Declarar argtypes/restype no es cosmetico: sin eso ctypes asume int de 32
    bits y en un Windows de 64 trunca los handles.
    """
    global _clipboard_api, _clipboard_api_buscada
    if _clipboard_api_buscada:
        return _clipboard_api

    _clipboard_api_buscada = True
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE

        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.restype = wintypes.HGLOBAL
        kernel32.Sleep.argtypes = [wintypes.DWORD]
        kernel32.Sleep.restype = None

        _clipboard_api = (ctypes, user32, kernel32)
    except Exception as e:
        debug_print(f"No se pudo preparar la API de portapapeles: {e}")
        _clipboard_api = None
    return _clipboard_api


def _copiar_como_dib(qimage, reintentos=5, espera_ms=20):
    """
    Publica el QImage como CF_DIB ya materializado.

    No levanta excepciones: devuelve False y el llamador cae al metodo de Qt.
    Tarda del orden de 10 ms en HD y 35 ms en 4K, asi que no molesta en la UI.

    Va en el HILO DE GUI. EmptyClipboard le manda un WM_DESTROYCLIPBOARD a la
    ventana que tenia el portapapeles por OLE, y desde un worker ese SendMessage
    se puede quedar esperando al hilo principal.
    """
    api = _get_clipboard_api()
    if api is None:
        return False
    ctypes, user32, kernel32 = api

    hmem = None
    try:
        # A 32 bits opacos: es lo que espera un DIB BI_RGB de 32bpp.
        if qimage.format() != QImage.Format_RGB32:
            qimage = qimage.convertToFormat(QImage.Format_RGB32)
        # El DIB clasico es bottom-up, asi que va espejado en vertical.
        img = qimage.mirrored(False, True)

        ancho, alto = img.width(), img.height()
        if ancho <= 0 or alto <= 0:
            return False
        stride = ancho * 4
        bytes_por_linea = img.bytesPerLine()
        n_pixeles = stride * alto

        hmem = kernel32.GlobalAlloc(
            GMEM_MOVEABLE, BITMAPINFOHEADER_SIZE + n_pixeles
        )
        if not hmem:
            return False
        ptr = kernel32.GlobalLock(hmem)
        if not ptr:
            kernel32.GlobalFree(hmem)
            hmem = None
            return False
        try:
            cabecera = struct.pack(
                "<IiiHHIIiiII",
                BITMAPINFOHEADER_SIZE,
                ancho,
                alto,  # positivo = bottom-up
                1,  # biPlanes
                32,  # biBitCount
                0,  # biCompression = BI_RGB
                n_pixeles,
                2835,  # ~72 dpi
                2835,
                0,
                0,
            )
            ctypes.memmove(ptr, cabecera, BITMAPINFOHEADER_SIZE)

            crudo = bytes(img.constBits())
            if bytes_por_linea == stride:
                ctypes.memmove(ptr + BITMAPINFOHEADER_SIZE, crudo, n_pixeles)
            else:
                # Qt puede alinear las filas a 4 bytes. Hoy no pasa, porque
                # mirrored() devuelve el stride ya normalizado, pero la rama
                # queda por si eso cambia o si alguien saca el espejado.
                for y in range(alto):
                    ctypes.memmove(
                        ptr + BITMAPINFOHEADER_SIZE + y * stride,
                        crudo[y * bytes_por_linea : y * bytes_por_linea + stride],
                        stride,
                    )
        finally:
            kernel32.GlobalUnlock(hmem)

        # Otra app puede tener el portapapeles tomado un instante. El tope de
        # espera es corto a proposito: esto corre en el hilo de GUI y Sleep no
        # bombea mensajes, asi que cada ms de mas es Nuke congelado.
        abierto = False
        for _ in range(reintentos):
            if user32.OpenClipboard(None):
                abierto = True
                break
            kernel32.Sleep(espera_ms)
        if not abierto:
            debug_print("No se pudo abrir el portapapeles")
            kernel32.GlobalFree(hmem)
            hmem = None
            return False

        try:
            if not user32.EmptyClipboard():
                debug_print("EmptyClipboard fallo")
            if not user32.SetClipboardData(CF_DIB, hmem):
                kernel32.GlobalFree(hmem)
                hmem = None
                return False
            # Con SetClipboardData OK el duenio del HGLOBAL pasa a ser el
            # sistema. Se suelta el handle ACA MISMO, y no al salir: si algo de
            # lo que sigue —un print, el CloseClipboard— llegara a tirar, el
            # except de abajo lo liberaria y seria un doble free sobre memoria
            # que ya no es nuestra. La proxima app que pegue leeria memoria
            # liberada.
            hmem = None
            debug_print(f"Portapapeles: CF_DIB de {ancho}x{alto} publicado")
            return True
        finally:
            # Un portapapeles abierto cuelga a las demas apps. Se cierra si o si.
            user32.CloseClipboard()

    except Exception as e:
        debug_print(f"Fallo la copia por CF_DIB: {e}")
        try:
            if hmem:
                kernel32.GlobalFree(hmem)
        except Exception:
            pass
        return False


def _copiar_al_portapapeles(qimage):
    """Copia con CF_DIB y, si no se puede, cae al camino de Qt."""
    if _copiar_como_dib(qimage):
        debug_print("Portapapeles OK por CF_DIB")
        return

    log_error(
        "El camino de CF_DIB fallo: se cae a QClipboard.setImage(), que es "
        "diferido y puede perder la entrada del historial de Windows"
    )
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    app.clipboard().setImage(qimage)


def take_snapshot(save_to_gallery=True, use_write=False, compare=False):
    """
    Toma el snapshot, lo copia al portapapeles y, si se pide, lo guarda en la
    galeria del proyecto.

    use_write=True usa el motor viejo, el del Write temporal: resolucion
    completa del proyecto en vez de la del viewport. Va escondido detras de
    Ctrl y no se documenta en los tooltips.

    compare=True pega la captura nueva a la derecha del snapshot anterior, para
    ir armando la tira de comparacion. Como el resultado se guarda como el
    snapshot siguiente, encadenar es volver a pedir compare: la tira crece de a
    una captura por vez. Una captura sin compare arranca una tira nueva.
    """
    # --- Comprobaciones iniciales del viewer de Nuke ---
    viewer_info = get_viewer_info()
    if viewer_info is None:
        nuke.message(
            "No hay viewer activo o nodo conectado. Por favor, conecta un nodo al viewer antes de tomar un snapshot."
        )
        return

    viewer, view_node, input_index, input_node = viewer_info
    debug_print(
        f"take_snapshot: motor={'write' if use_write else 'capture'} "
        f"compare={bool(compare)} galeria={bool(save_to_gallery)} "
        f"viewer={view_node.name()} input={input_node.name()}"
    )

    # El anterior hay que resolverlo ANTES de generar nada, o el nuevo pasa a
    # ser el mas reciente y la compo se armaria contra si misma.
    anterior_path = get_latest_snapshot_path() if compare else None
    if compare and not anterior_path:
        debug_print("No hay snapshot anterior: la captura arranca la tira")

    # Obtener el siguiente numero para el snapshot
    snapshot_number = get_next_snapshot_number()
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"LGA_snapshot_{snapshot_number}.jpg")

    # Cuando hay que componer, la captura va a un temporal y el numero de
    # snapshot queda para la compo, que es la que sigue la tira. El nombre esta
    # fuera del patron LGA_snapshot_N.jpg a proposito, para no meterse ni en la
    # numeracion ni en la limpieza.
    componer = bool(compare and anterior_path)
    captura_path = (
        os.path.join(temp_dir, "LGA_capture_tmp.jpg") if componer else output_path
    )
    debug_print(
        f"Motor: {'write' if use_write else 'capture'}"
        f"{' + compo' if componer else ''} -> {output_path}"
    )

    # El temporal tiene nombre fijo, asi que puede haber quedado de una corrida
    # anterior que fallo. Si no se borra, el os.path.exists() de los motores lo
    # daria por bueno y la tira se armaria con una captura vieja.
    if componer and os.path.exists(captura_path):
        try:
            os.remove(captura_path)
        except Exception as e:
            debug_print(f"No se pudo borrar el temporal viejo: {e}")

    try:
        if use_write:
            generado = _snapshot_con_write(captura_path, input_node)
        else:
            generado = _snapshot_con_capture(captura_path, view_node, input_node)
        if not generado:
            return

        if componer:
            compuesto = _componer_con_anterior(
                anterior_path, captura_path, output_path
            )
            if not compuesto:
                # No se pudo componer —la tira llego a un tamano que el JPEG ya
                # no banca, o el anterior quedo ilegible—. La captura no se
                # tira: pasa a ser el snapshot nuevo y arranca una tira limpia.
                rescatada = False
                try:
                    os.replace(captura_path, output_path)
                    rescatada = True
                except Exception as e:
                    debug_print(f"No se pudo rescatar la captura: {e}")
                nuke.message(
                    "No se pudo componer con el snapshot anterior; probablemente la tira ya es demasiado ancha.\n\n"
                    + (
                        "La captura queda sola y empieza una tira nueva."
                        if rescatada
                        else "Ademas no se pudo guardar la captura."
                    )
                )
                if not rescatada:
                    return
    finally:
        # Pase lo que pase, el temporal no queda dando vueltas.
        if componer and os.path.exists(captura_path):
            try:
                os.remove(captura_path)
            except Exception as e:
                debug_print(f"No se pudo borrar la captura temporal: {e}")

    # Cargar el JPEG como QImage
    qimage = QImage(output_path)
    if qimage.isNull():
        # Qt no lee imagenes que superen su limite de memoria por archivo (256 MB
        # en Qt 6.5), y una tira larga llega ahi antes que a cualquier otro tope.
        # El archivo esta bien: lo que falla es cargarlo de vuelta.
        pesa = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        nuke.message(
            "El snapshot se guardó pero no se pudo volver a leer, así que no va "
            "al portapapeles. Si venías encadenando capturas, la tira ya es "
            f"demasiado grande ({pesa / (1024 * 1024):.1f} MB): tomá una captura "
            "suelta para empezar una tira nueva."
        )
        return

    debug_print(
        f"Snapshot final: {qimage.width()}x{qimage.height()} -> {output_path}"
    )

    # Guardar en la galeria del proyecto
    if save_to_gallery:
        gallery_path = save_snapshot_to_gallery(output_path)
        if not gallery_path:
            print("❌ Error al guardar en galeria")

    # Limpiar snapshots antiguos después del guardado exitoso
    cleanup_old_snapshots(snapshot_number)

    # El portapapeles va ULTIMO, despues de toda la IO. Con CF_DIB ya no hace
    # falta, porque los bytes quedan materializados, pero si por lo que sea se
    # cae al camino de Qt —que es diferido— dejar IO despues de copiar le
    # arruina la entrada del historial de Windows.
    _copiar_al_portapapeles(qimage)

    # NO eliminar el archivo temporal - lo necesitamos para show_snapshot()
    debug_print(f"Archivo temporal mantenido para show_snapshot: {output_path}")


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
