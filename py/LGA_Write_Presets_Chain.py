"""
_____________________________________________________________________________

  LGA_Write_Presets_Chain v2.78 | Lega

  Presets de cadena de Write Presets: guarda los nodos seleccionados (un
  Write y lo que tenga arriba: OCIO, textos, groups, backdrops) como un
  pedazo de .nk, y despues lo pega colgando del nodo seleccionado.

  Se guardan en la carpeta de datos del usuario, nunca adentro del pack:
  el instalador reemplaza el pack entero en cada actualizacion.
    Windows  %APPDATA%/LGA/ToolPack/WritePresets/<nombre>.nk
    macOS    ~/Library/Application Support/LGA/ToolPack/WritePresets/
    respaldo <.nuke>/LGA_Settings/ToolPack/WritePresets/

  Al guardar:
    - Se suman solos los backdrops que encierran nodos seleccionados y
      no tienen adentro ningun nodo sin seleccionar (tambien anidados).
    - Se saca el rango de frames propio (first/last/use_limit) de los
      Write de primer nivel: era el del shot donde se armo.
    - Si hay rutas absolutas en knobs de archivo (una LUT, un CDL) se
      ofrece pasarlas a relativas a la carpeta del script. Las de red
      (UNC) quedan siempre absolutas.

  Al pegar: con un nodo seleccionado la cadena se cuelga de el y se ubica
  debajo; sin ninguno se pega suelta y se encuadra; con varios se avisa y
  no se pega. Borrar un preset lo manda a la papelera.

  v2.78: Modulo nuevo.
_____________________________________________________________________________

"""

import datetime
import os
import platform
import re
import sys
import tempfile

import nuke

DEBUG = False

PRESETS_DIR_NAME = "WritePresets"
USER_DIR_PARTS = ("LGA", "ToolPack")
FALLBACK_DIR_NAME = "LGA_Settings"
PRESET_EXT = ".nk"

PY_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PY_DIR)
LOG_PATH = os.path.join(PY_DIR, "logs", "DebugPy_LGA_Write_Presets_Chain.log")

# Espacio entre el nodo de arriba y el primero de la cadena pegada.
PASTE_GAP_Y = 40

# Knobs de rango que se le sacan a los Write al guardar.
FRAME_RANGE_KNOBS = ("first", "last", "use_limit")

# Solo se miran knobs de archivo: un label o un message que empiece con una
# ruta es texto del usuario y no se reescribe.
PATH_KNOB_WORDS = ("file", "path", "lut")

_INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Una linea "knob valor" de un .nk, sin TCL en el valor.
_KNOB_LINE = re.compile(r'^(?P<indent>\s+)(?P<knob>\w+) (?P<q>"?)(?P<value>[^"\n\[]+)(?P=q)\s*$')
_DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


# ---------------------------------------------------------------------------
# Log de la corrida
# ---------------------------------------------------------------------------

_log_lines = []


def _log_start(accion):
    del _log_lines[:]
    _log("%s | %s" % (accion, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def _log(*partes):
    texto = " ".join(str(p) for p in partes)
    _log_lines.append(texto)
    if DEBUG:
        print("[Write_Presets_Chain]", texto)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "w", newline="\n", encoding="utf-8") as handle:
            handle.write("\n".join(_log_lines) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Carpeta de presets
# ---------------------------------------------------------------------------


def _user_config_dir():
    system = platform.system()
    if system == "Windows":
        return os.getenv("APPDATA")
    if system == "Darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.path.expanduser("~/.config")


def _candidate_dirs():
    """Carpetas posibles, en orden: la del sistema y el respaldo en .nuke."""
    candidatas = []
    base = _user_config_dir()
    if base:
        candidatas.append(os.path.join(base, *(USER_DIR_PARTS + (PRESETS_DIR_NAME,))))
    nuke_dir = os.path.dirname(ROOT_DIR)
    candidatas.append(
        os.path.join(nuke_dir, FALLBACK_DIR_NAME, USER_DIR_PARTS[-1], PRESETS_DIR_NAME)
    )
    return candidatas


def get_writable_presets_dir():
    """La primera carpeta que se puede crear y escribir. None si ninguna."""
    for carpeta in _candidate_dirs():
        try:
            os.makedirs(carpeta, exist_ok=True)
        except OSError:
            continue
        if os.access(carpeta, os.W_OK):
            return carpeta
    return None


def list_chain_presets():
    """Presets de cadena de todas las carpetas, sin repetir nombre.

    Devuelve una lista de dicts {"name", "path"} ordenada por nombre. Si el
    mismo nombre esta en las dos carpetas, manda la del sistema.
    """
    vistos = {}
    for carpeta in _candidate_dirs():
        if not os.path.isdir(carpeta):
            continue
        try:
            archivos = os.listdir(carpeta)
        except OSError:
            continue
        for archivo in archivos:
            nombre, ext = os.path.splitext(archivo)
            if ext.lower() != PRESET_EXT or nombre.lower() in vistos:
                continue
            vistos[nombre.lower()] = {
                "name": nombre,
                "path": os.path.join(carpeta, archivo),
            }
    return sorted(vistos.values(), key=lambda p: p["name"].lower())


def sanitize_preset_name(name):
    limpio = _INVALID_NAME_CHARS.sub("_", (name or "").strip())
    return limpio.strip(" .")


# ---------------------------------------------------------------------------
# Guardar
# ---------------------------------------------------------------------------


def _node_rect(node):
    w = node.screenWidth() or 80
    h = node.screenHeight() or 20
    return node.xpos(), node.ypos(), w, h


def _nodes_inside_backdrop(backdrop, candidatos):
    bx, by = backdrop.xpos(), backdrop.ypos()
    bw, bh = backdrop["bdwidth"].value(), backdrop["bdheight"].value()
    adentro = []
    for node in candidatos:
        if node.fullName() == backdrop.fullName():
            continue
        x, y, w, h = _node_rect(node)
        cx, cy = x + w / 2.0, y + h / 2.0
        if bx <= cx <= bx + bw and by <= cy <= by + bh:
            adentro.append(node)
    return adentro


def collect_preset_nodes():
    """Seleccion + backdrops que la encierran. None si no hay ningun Write.

    Se repite hasta que no cambie nada: un backdrop grande que encierra a uno
    chico entra recien cuando entro el chico.
    """
    seleccion = nuke.selectedNodes()
    if not any(n.Class() == "Write" for n in seleccion):
        return None
    elegidos = list(seleccion)
    nombres = set(n.fullName() for n in seleccion)
    todos = nuke.allNodes()
    backdrops = nuke.allNodes("BackdropNode")
    cambio = True
    while cambio:
        cambio = False
        for backdrop in backdrops:
            if backdrop.fullName() in nombres:
                continue
            adentro = _nodes_inside_backdrop(backdrop, todos)
            if adentro and all(n.fullName() in nombres for n in adentro):
                elegidos.append(backdrop)
                nombres.add(backdrop.fullName())
                cambio = True
                _log("Backdrop sumado solo:", backdrop.name())
    return elegidos


def _copy_nodes_to_text(nodes):
    """Copia los nodos con nodeCopy a un temporal y devuelve el texto.

    El temporal va a la carpeta temp del sistema y no a la de presets: si
    no se pudiera borrar, ahi apareceria como un preset mas.
    """
    seleccion_previa = nuke.selectedNodes()
    fd, tmp_path = tempfile.mkstemp(suffix=".nk", prefix="LGA_WritePreset_")
    os.close(fd)
    try:
        for n in seleccion_previa:
            n.setSelected(False)
        for n in nodes:
            n.setSelected(True)
        nuke.nodeCopy(tmp_path.replace("\\", "/"))
        with open(tmp_path, "r", encoding="utf-8") as handle:
            texto = handle.read()
    finally:
        for n in nodes:
            n.setSelected(False)
        for n in seleccion_previa:
            n.setSelected(True)
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    if "{" not in texto:
        raise RuntimeError("Nuke did not copy any node.")
    return texto


def strip_write_frame_range(text):
    """Saca first/last/use_limit de los Write de primer nivel del .nk."""
    salida = []
    en_write = False
    quitadas = 0
    for linea in text.split("\n"):
        if linea == "Write {":
            en_write = True
        elif en_write and linea == "}":
            en_write = False
        elif en_write and linea.startswith(" ") and not linea.startswith("  "):
            knob = linea[1:].split(" ", 1)[0]
            if knob in FRAME_RANGE_KNOBS:
                quitadas += 1
                continue
        salida.append(linea)
    _log("Knobs de rango quitados:", quitadas)
    return "\n".join(salida)


def _unescape_nk(value):
    """Valor tal como lo lee Nuke: el .nk escapa \\ { } $ [ y comillas."""
    return re.sub(r"\\(.)", r"\1", value)


def _escape_nk(value):
    """Valor listo para ir entre comillas en un .nk (como lo escribe Nuke)."""
    return re.sub(r'([\\"\[{}$])', r"\\\1", value)


def _path_kind(path):
    if path.startswith("//") or path.startswith("\\\\"):
        return "unc"
    if _DRIVE_PATH.match(path):
        return "drive"
    if path.startswith("/"):
        return "posix"
    return None


def _parse_path_line(linea):
    """(match, ruta) si la linea es un knob de archivo con ruta absoluta."""
    match = _KNOB_LINE.match(linea)
    if not match:
        return None, None
    knob = match.group("knob").lower()
    if not any(palabra in knob for palabra in PATH_KNOB_WORDS):
        return None, None
    ruta = _unescape_nk(match.group("value"))
    if not _path_kind(ruta):
        return None, None
    return match, ruta


def find_absolute_paths(text):
    """Rutas absolutas sin TCL en los knobs de archivo. Lista de (knob, ruta)."""
    encontradas = []
    for linea in text.split("\n"):
        match, ruta = _parse_path_line(linea)
        if match:
            encontradas.append((match.group("knob"), ruta))
    return encontradas


def _script_dir():
    nombre = nuke.root().name()
    if not nombre or nombre == "Root":
        return None
    return os.path.dirname(nombre)


def relative_expression(path, script_dir):
    """La ruta como expresion relativa al script, o None si no se puede."""
    if _path_kind(path) == "unc":
        # Una ruta de red no tiene relativa confiable desde una unidad local.
        return None
    try:
        rel = os.path.relpath(path, script_dir)
    except ValueError:
        # Otra unidad: no hay relativa posible.
        return None
    return "[file dir [value root.name]]/" + rel.replace("\\", "/")


def make_paths_relative(text, script_dir):
    """Reemplaza las rutas absolutas por expresiones relativas al script."""
    salida = []
    for linea in text.split("\n"):
        match, ruta = _parse_path_line(linea)
        if match:
            expr = relative_expression(ruta, script_dir)
            if expr:
                linea = '%s%s "%s"' % (match.group("indent"), match.group("knob"), _escape_nk(expr))
                _log("Ruta relativa:", ruta, "->", expr)
        salida.append(linea)
    return "\n".join(salida)


def _write_atomic(path, text):
    carpeta = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=carpeta)
    try:
        with os.fdopen(fd, "w", newline="\n", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def _default_name(nodes):
    for n in nodes:
        if n.Class() == "Write":
            return re.sub(r"\d+$", "", n.name()) or n.name()
    return ""


def _html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _ask_relative(paths, script_dir):
    from LGA_UI_MessageBox_ToolPack import ask_question

    filas = []
    for knob, ruta in paths:
        expr = relative_expression(ruta, script_dir)
        filas.append(
            "%s: %s<br>&nbsp;&nbsp;&rarr; %s"
            % (_html(knob), _html(ruta), _html(expr) if expr else "stays absolute")
        )
    texto = (
        "This preset has absolute paths. They will point to the same files "
        "in every shot.<br><br>%s<br><br>"
        "Make them relative to the script folder instead?" % "<br><br>".join(filas)
    )
    return ask_question(
        None,
        "Absolute paths",
        texto,
        yes_text="Make relative",
        no_text="Keep absolute",
        recommended=False,
    )


def save_selection_as_preset():
    """Alt+Shift+W: guarda la seleccion como preset de cadena."""
    from LGA_UI_MessageBox_ToolPack import ask_question, show_error, show_info, show_warning
    from LGA_Write_Presets import show_name_input_dialog

    _log_start("Guardar preset de cadena")
    nodes = collect_preset_nodes()
    if not nodes:
        _log("Cancelado: no hay ningun Write en la seleccion")
        show_warning(
            None,
            "Write Presets",
            "Select a Write node, and the nodes above it you want to keep, "
            "to save them as a preset.",
        )
        return
    _log("Nodos:", ", ".join(n.name() for n in nodes))

    carpeta = get_writable_presets_dir()
    if not carpeta:
        _log("Sin carpeta escribible:", _candidate_dirs())
        show_error(
            None,
            "Write Presets",
            "There is no writable folder to save presets in:<br>%s"
            % "<br>".join(_html(c) for c in _candidate_dirs()),
        )
        return

    esc_exit, nombre = show_name_input_dialog(
        _default_name(nodes), title="Preset Name", width=320
    )
    if esc_exit or nombre is None:
        _log("Cancelado en el nombre")
        return
    nombre = sanitize_preset_name(nombre)
    if not nombre:
        _log("Cancelado: nombre vacio")
        show_warning(None, "Write Presets", "The preset needs a name. Nothing was saved.")
        return
    destino = os.path.join(carpeta, nombre + PRESET_EXT)
    _log("Destino:", destino)

    if os.path.exists(destino) and not ask_question(
        None,
        "Write Presets",
        "A preset named <b>%s</b> already exists. Replace it?" % _html(nombre),
        yes_text="Replace",
        no_text="Cancel",
        recommended=False,
    ):
        _log("Cancelado: no se reemplaza el existente")
        return

    nota = ""
    try:
        texto = _copy_nodes_to_text(nodes)
        texto = strip_write_frame_range(texto)

        absolutas = find_absolute_paths(texto)
        _log("Rutas absolutas:", absolutas)
        script_dir = _script_dir()
        if absolutas and not script_dir:
            _log("Script sin guardar: las rutas quedan absolutas")
            nota = (
                "<br><br>Its paths stay absolute: save the script first "
                "to be able to make them relative."
            )
        elif absolutas and _ask_relative(absolutas, script_dir):
            texto = make_paths_relative(texto, script_dir)

        _write_atomic(destino, texto)
    except Exception as exc:
        _log("ERROR al guardar:", repr(exc))
        show_error(None, "Write Presets", "Could not save the preset:<br>%s" % _html(str(exc)))
        return

    _log("Guardado OK")
    show_info(
        None,
        "Write Presets",
        "Preset <b>%s</b> saved.<br>Open Write Presets (Shift+W) to use it.%s"
        % (_html(nombre), nota),
    )


# ---------------------------------------------------------------------------
# Usar
# ---------------------------------------------------------------------------


def _place_below(anchor, pasted):
    """Mueve la cadena pegada para que arranque justo debajo del ancla."""
    nodos = [n for n in pasted if n.Class() != "BackdropNode"]
    if not nodos:
        return
    ancla = anchor.fullName()
    conectados = [
        n
        for n in nodos
        if any(n.input(i) is not None and n.input(i).fullName() == ancla for i in range(n.inputs()))
    ]
    if not conectados:
        _log("Aviso: ningun nodo pegado quedo conectado al ancla")
    top = conectados[0] if conectados else min(nodos, key=lambda n: n.ypos())

    ax, ay, aw, ah = _node_rect(anchor)
    tx, _ty, tw, _th = _node_rect(top)
    min_y = min(n.ypos() for n in pasted)
    dx = int(ax + aw / 2.0 - (tx + tw / 2.0))
    dy = int(ay + ah + PASTE_GAP_Y - min_y)
    for n in pasted:
        n.setXYpos(n.xpos() + dx, n.ypos() + dy)
    _log("Cadena movida", dx, dy, "debajo de", anchor.name())


def apply_chain_preset(preset):
    """Pega el preset colgando del nodo seleccionado, o suelto si no hay."""
    from LGA_UI_MessageBox_ToolPack import show_error, show_warning

    _log_start("Usar preset de cadena")
    path = preset["path"]
    _log("Preset:", preset["name"], path)
    if not os.path.isfile(path):
        show_error(
            None, "Write Presets", "The preset file no longer exists:<br>%s" % _html(path)
        )
        return

    seleccion = nuke.selectedNodes()
    if len(seleccion) > 1:
        _log("Cancelado: hay %d nodos seleccionados" % len(seleccion))
        show_warning(
            None,
            "Write Presets",
            "Select the one node the preset should hang from, or none to "
            "paste it unconnected.",
        )
        return
    anchor = seleccion[0] if seleccion else None
    _log("Ancla:", anchor.name() if anchor else None)

    undo = nuke.Undo()
    undo.begin("Write Preset: %s" % preset["name"])
    try:
        if anchor:
            anchor.setSelected(True)
        nuke.nodePaste(path.replace("\\", "/"))
        pasted = nuke.selectedNodes()
        if anchor:
            pasted = [n for n in pasted if n.fullName() != anchor.fullName()]
        _log("Pegados:", ", ".join(n.name() for n in pasted))
        if not pasted:
            raise RuntimeError("The preset file has no nodes.")
        if anchor:
            _place_below(anchor, pasted)
        else:
            # Sin ancla quedan en las coordenadas del script donde se guardo:
            # se encuadran para que se vean.
            nuke.zoomToFitSelected()
    except Exception as exc:
        _log("ERROR al pegar:", repr(exc))
        show_error(
            None,
            "Write Presets",
            "Could not paste the preset <b>%s</b>:<br>%s"
            % (_html(preset["name"]), _html(str(exc))),
        )
    finally:
        undo.end()


def _send_to_trash(path):
    """Manda el archivo a la papelera con el send2trash que viaja en el pack."""
    send2trash_dir = os.path.join(PY_DIR, "Send2Trash-1.8.2")
    if send2trash_dir not in sys.path:
        sys.path.append(send2trash_dir)
    import send2trash

    # send2trash quiere separadores nativos.
    send2trash.send2trash(os.path.normpath(path))


def delete_chain_preset(preset):
    """Manda el preset a la papelera, previa confirmacion. True si lo hizo."""
    from LGA_UI_MessageBox_ToolPack import ask_question, show_error

    _log_start("Borrar preset de cadena")
    if not ask_question(
        None,
        "Write Presets",
        "Move the preset <b>%s</b> to the trash?" % _html(preset["name"]),
        yes_text="Move to Trash",
        no_text="Cancel",
        recommended=False,
    ):
        _log("Cancelado")
        return False
    try:
        _send_to_trash(preset["path"])
    except Exception as exc:
        _log("ERROR al borrar:", repr(exc))
        show_error(
            None, "Write Presets", "Could not delete the preset:<br>%s" % _html(str(exc))
        )
        return False
    _log("A la papelera:", preset["path"])
    return True
