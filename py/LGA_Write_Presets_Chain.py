"""
_____________________________________________________________________________

  LGA_Write_Presets_Chain v2.84 | Lega

  Presets de cadena de Write Presets: guarda los nodos seleccionados (un
  Write y lo que tenga arriba: OCIO, textos, groups, backdrops) como un
  pedazo de .nk, y despues lo pega colgando del nodo seleccionado.

  Se guardan en la carpeta de datos del usuario, nunca adentro del pack:
  el instalador reemplaza el pack entero en cada actualizacion.
    Windows  %APPDATA%/LGA/ToolPack/WritePresets/<nombre>.nk
    macOS    ~/Library/Application Support/LGA/ToolPack/WritePresets/
    respaldo <.nuke>/LGA_Settings/ToolPack/WritePresets/

  Al guardar:
    - Los Read de la seleccion quedan afuera: un preset de salida no
      trae media.
    - Se suman solos los backdrops que encierran nodos seleccionados y
      no tienen adentro ningun nodo sin seleccionar (tambien anidados).
    - Se saca el rango de frames propio (first/last/use_limit) de los
      Write de primer nivel: era el del shot donde se armo.
    - No se guarda ninguna ruta fija: los knobs de archivo con una ruta
      sin TCL se vacian. Las rutas con TCL quedan, porque se resuelven
      solas en cada shot.

  Al pegar: con un nodo seleccionado la cadena se cuelga de el y se ubica
  debajo; sin ninguno se pega suelta y se encuadra; con varios se avisa y
  no se pega. Soltar un .nk sobre la ventana de Shift+W lo agrega como
  preset, limpio igual que al guardar. Los OCIOCDLTransform y OCIOFileTransform vacios se completan
  con el CDL, el LMT y el working space del .amf del shot
  (LGA_Write_Presets_Look). Los backdrops quedan como LGA_backdrop y por
  encima de lo que ya hay (LGA_Write_Presets_Backdrop). Borrar un preset lo manda a la papelera.

  v2.83: Ofrece limitar los MOV/MXF nuevos al TimeClip del EditRef.
  v2.82: import_preset_files() agrega los .nk soltados en la ventana, con la
         misma limpieza que Alt+Shift+W (se pegan en el root con el undo
         apagado, se copian sin Read y se borran). Las limpiezas de texto
         recorren el .nk por estructura (_walk_nk) y no por sangria:
         nodeCopy a veces escribe los knobs sin el espacio adelante.
  v2.80: Los backdrops del preset se pegan como LGA_backdrop y con el z
         order calculado sobre los backdrops que ya hay.
  v2.79: Sin rutas fijas: al guardar se vacian en vez de ofrecer pasarlas
         a relativas, que solo servia desde un script dentro del shot. Al
         pegar, el look se toma del .amf del shot. Los Read quedan afuera.
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

# Clases que no entran en un preset: traen media del shot donde se armo.
EXCLUDED_CLASSES = ("Read", "DeepRead", "ReadGeo", "ReadGeo2")

LOOK_NODE_CLASSES = ("OCIOCDLTransform", "OCIOFileTransform")

_INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Una linea "knob valor" de un .nk, sin TCL en el valor.
_KNOB_LINE = re.compile(r'^(?P<indent>\s*)(?P<knob>\w+) (?P<q>"?)(?P<value>[^"\n\[]+)(?P=q)\s*$')
# La linea que abre un nodo: las clases empiezan en mayuscula y los knobs no.
_NODE_LINE = re.compile(r"^\s*(?P<clase>[A-Z]\w*) \{\s*$")
# Para contar llaves de una linea sin las escapadas ni las de un string.
_NK_ESCAPED = re.compile(r"\\.")
_NK_QUOTED = re.compile(r'"[^"]*"')


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


def _html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    """(nodos, reads_excluidos). nodos es None si no hay ningun Write.

    Los Read quedan afuera. Los backdrops que encierran la seleccion se suman
    en una pasada que se repite hasta que no cambie nada: un backdrop grande
    que encierra a uno chico entra recien cuando entro el chico. Un Read
    excluido igual cuenta como "seleccionado" para esto: no es un nodo que el
    usuario haya dejado afuera.
    """
    seleccion = nuke.selectedNodes()
    excluidos = [n for n in seleccion if n.Class() in EXCLUDED_CLASSES]
    elegidos = [n for n in seleccion if n.Class() not in EXCLUDED_CLASSES]
    if not any(n.Class() == "Write" for n in elegidos):
        return None, excluidos
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
    return elegidos, excluidos


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


def _brace_delta(linea):
    """Llaves que abre menos las que cierra la linea (sin escapadas ni strings)."""
    limpia = _NK_QUOTED.sub("", _NK_ESCAPED.sub("", linea))
    return limpia.count("{") - limpia.count("}")


def _walk_nk(text):
    """Recorre un .nk linea por linea.

    Devuelve tuplas (linea, clase, es_knob, nivel_de_grupo): `clase` es la
    del nodo en el que esta la linea, `es_knob` dice si es un knob de ese
    nodo (y no una linea de adentro del valor de un knob de varias lineas),
    y `nivel_de_grupo` cuantos Group abiertos la contienen.

    No depende de la sangria: nodeCopy a veces escribe los knobs con un
    espacio adelante y a veces sin. Se sigue la estructura: un nodo abre con
    "Clase {" y cierra con "}" balanceando las llaves de sus knobs; los hijos
    de un Group van despues de su bloque, hasta "end_group".
    """
    clase = None
    profundidad = 0
    grupo = 0
    for linea in text.split("\n"):
        limpia = linea.strip()
        if profundidad == 0:
            nodo = _NODE_LINE.match(linea)
            if nodo:
                clase = nodo.group("clase")
                profundidad = 1
                yield linea, clase, False, grupo
                continue
            if limpia == "end_group":
                grupo = max(0, grupo - 1)
            yield linea, None, False, grupo
            continue
        if profundidad == 1 and limpia == "}":
            profundidad = 0
            yield linea, clase, False, grupo
            if clase == "Group":
                grupo += 1
            continue
        yield linea, clase, profundidad == 1, grupo
        profundidad = max(1, profundidad + _brace_delta(limpia))


def strip_write_frame_range(text):
    """Saca first/last/use_limit de los Write de primer nivel del .nk."""
    salida = []
    quitadas = 0
    for linea, clase, es_knob, grupo in _walk_nk(text):
        if es_knob and clase == "Write" and grupo == 0:
            knob = linea.strip().split(" ", 1)[0]
            if knob in FRAME_RANGE_KNOBS:
                quitadas += 1
                continue
        salida.append(linea)
    _log("Knobs de rango quitados:", quitadas)
    return "\n".join(salida)


def _is_path_knob(knob):
    knob = knob.lower()
    return knob in ("file", "proxy", "path") or knob.endswith("_file") or knob.endswith("_path")


def strip_fixed_paths(text):
    """Vacia los knobs de archivo con una ruta sin TCL.

    Devuelve (texto, quitadas), con quitadas una lista de (clase, knob, ruta).
    La linea se borra entera: el knob vuelve a su default, que es vacio. Las
    rutas con TCL no entran en el regex (no puede haber '[' en el valor).
    """
    salida = []
    quitadas = []
    for linea, clase, es_knob, _grupo in _walk_nk(text):
        if es_knob:
            match = _KNOB_LINE.match(linea)
            if match and _is_path_knob(match.group("knob")):
                valor = re.sub(r"\\(.)", r"\1", match.group("value"))
                if "/" in valor or "\\" in valor:
                    quitadas.append((clase, match.group("knob"), valor))
                    continue
        salida.append(linea)
    _log("Rutas fijas quitadas:", quitadas)
    return "\n".join(salida), quitadas


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


def _saved_notes(excluidos, quitadas):
    """Lo que el cartel final cuenta que se dejo afuera del preset."""
    notas = []
    if excluidos:
        notas.append(
            "Left out (Reads are not saved in presets): %s."
            % ", ".join(_html(n if isinstance(n, str) else n.name()) for n in excluidos)
        )
    look = [q for q in quitadas if q[0] in LOOK_NODE_CLASSES]
    otras = [q for q in quitadas if q[0] not in LOOK_NODE_CLASSES]
    if look:
        notas.append(
            "CDL and LUT files are not saved: when pasting, they are loaded "
            "from the shot's .amf in _input/Look_Files."
        )
    if otras:
        notas.append(
            "These fixed paths were cleared, presets only keep TCL paths:<br>%s"
            % "<br>".join("%s %s: %s" % (_html(c or "?"), _html(k), _html(r)) for c, k, r in otras)
        )
    return "".join("<br><br>" + n for n in notas)


def save_selection_as_preset():
    """Alt+Shift+W: guarda la seleccion como preset de cadena."""
    from LGA_Write_Presets_Dialogs import ask_question, show_error, show_info, show_warning
    from LGA_Write_Presets import show_name_input_dialog

    from LGA_Write_Presets_Dialogs import set_dialog_center

    set_dialog_center()
    _log_start("Guardar preset de cadena")
    nodes, excluidos = collect_preset_nodes()
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
    _log("Reads excluidos:", ", ".join(n.name() for n in excluidos))

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

    try:
        texto = _copy_nodes_to_text(nodes)
        texto = strip_write_frame_range(texto)
        texto, quitadas = strip_fixed_paths(texto)
        _write_atomic(destino, texto)
    except Exception as exc:
        _log("ERROR al guardar:", repr(exc))
        show_error(None, "Write Presets", "Could not save the preset:<br>%s" % _html(exc))
        return

    _log("Guardado OK")
    show_info(
        None,
        "Write Presets",
        "Preset <b>%s</b> saved.<br>Open Write Presets (Shift+W) to use it.%s"
        % (_html(nombre), _saved_notes(excluidos, quitadas)),
    )


# ---------------------------------------------------------------------------
# Compartir: importar archivos soltados en la ventana
# ---------------------------------------------------------------------------


def _clean_external_preset(src_path):
    """Limpia un .nk ajeno igual que Alt+Shift+W limpia una seleccion.

    Se pega en el root, se le sacan los Read, se vuelve a copiar con
    nodeCopy y se borra todo lo pegado; despues pasan las mismas limpiezas
    de texto que al guardar. Con el undo apagado y la seleccion del usuario
    restaurada, el script queda como estaba.

    No se pega adentro de un Group temporal: ahi nodeCopy escribe los knobs
    sin sangria (las limpiezas no los reconocen) y con posiciones
    disparatadas, porque el Group esta vacio.

    Devuelve (texto, reads_excluidos, rutas_quitadas), con texto None si el
    archivo no trae ningun Write.
    """
    seleccion_previa = nuke.selectedNodes()
    antes = set(n.fullName() for n in nuke.allNodes())
    undo = nuke.Undo()
    undo.disable()
    pegados = []
    try:
        for n in seleccion_previa:
            n.setSelected(False)
        nuke.nodePaste(src_path.replace("\\", "/"))
        pegados = [n for n in nuke.allNodes() if n.fullName() not in antes]
        excluidos = [n.name() for n in pegados if n.Class() in EXCLUDED_CLASSES]
        nodos = [n for n in pegados if n.Class() not in EXCLUDED_CLASSES]
        if not any(n.Class() == "Write" for n in nodos):
            return None, excluidos, []
        for n in [n for n in pegados if n.Class() in EXCLUDED_CLASSES]:
            nuke.delete(n)
        pegados = nodos
        texto = _copy_nodes_to_text(nodos)
    finally:
        for n in pegados:
            try:
                nuke.delete(n)
            except Exception as exc:
                _log("Aviso: no se pudo borrar un nodo pegado para importar:", repr(exc))
        for n in seleccion_previa:
            try:
                n.setSelected(True)
            except Exception as exc:
                _log("Aviso: no se pudo restaurar la seleccion:", repr(exc))
        undo.enable()
    texto = strip_write_frame_range(texto)
    texto, quitadas = strip_fixed_paths(texto)
    return texto, excluidos, quitadas


def import_preset_files(paths):
    """Agrega como presets de cadena los .nk soltados en la ventana.

    El nombre del preset es el del archivo. Si ya hay uno con ese nombre se
    pregunta si reemplazarlo. Devuelve la lista de nombres importados; lo
    que no se pudo importar, y por que, sale en el cartel final.
    """
    from LGA_Write_Presets_Dialogs import ask_question, show_error, show_info, show_warning

    _log_start("Importar presets soltados")
    _log("Archivos:", paths)
    carpeta = get_writable_presets_dir()
    if not carpeta:
        show_error(
            None,
            "Write Presets",
            "There is no writable folder to save presets in:<br>%s"
            % "<br>".join(_html(c) for c in _candidate_dirs()),
        )
        return []

    importados, fallidos, excluidos, quitadas = [], [], [], []
    for src in paths:
        nombre = sanitize_preset_name(os.path.splitext(os.path.basename(src))[0])
        if not src.lower().endswith(PRESET_EXT) or not nombre:
            fallidos.append((os.path.basename(src), "it is not a .nk file"))
            continue
        destino = os.path.join(carpeta, nombre + PRESET_EXT)
        if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(destino)):
            _log("Ya es un preset propio, se saltea:", src)
            continue
        if os.path.exists(destino) and not ask_question(
            None,
            "Write Presets",
            "A preset named <b>%s</b> already exists. Replace it?" % _html(nombre),
            yes_text="Replace",
            no_text="Skip",
            recommended=False,
        ):
            _log("No se reemplaza:", nombre)
            continue
        try:
            texto, sin_reads, sin_rutas = _clean_external_preset(src)
            if texto is None:
                fallidos.append((os.path.basename(src), "it has no Write node"))
                continue
            _write_atomic(destino, texto)
        except Exception as exc:
            _log("ERROR al importar", src, repr(exc))
            fallidos.append((os.path.basename(src), str(exc)))
            continue
        importados.append(nombre)
        excluidos.extend(sin_reads)
        quitadas.extend(sin_rutas)
        _log("Importado:", nombre, "->", destino)

    if fallidos:
        show_warning(
            None,
            "Write Presets",
            "%sCould not import:<br>%s"
            % (
                ("Imported: <b>%s</b>.<br><br>" % _html(", ".join(importados))) if importados else "",
                "<br>".join("%s: %s" % (_html(n), _html(m)) for n, m in fallidos),
            ),
        )
    elif importados:
        show_info(
            None,
            "Write Presets",
            "Imported: <b>%s</b>.%s" % (_html(", ".join(importados)), _saved_notes(excluidos, quitadas)),
        )
    return importados


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


def _preset_has_look_nodes(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            texto = handle.read()
    except OSError:
        return False
    return re.search(r"^\s*(%s) \{$" % "|".join(LOOK_NODE_CLASSES), texto, re.M) is not None


def _empty_look_nodes(pasted):
    """Los nodos de look del preset que quedaron sin archivo (no los de TCL)."""
    vacios = []
    for n in pasted:
        if n.Class() in LOOK_NODE_CLASSES and not n["file"].value().strip():
            vacios.append(n)
    return vacios


def apply_chain_preset(preset):
    """Pega el preset colgando del nodo seleccionado, o suelto si no hay."""
    from LGA_Write_Presets_Dialogs import show_error, show_warning

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

    # El look se resuelve ANTES de abrir el undo: puede abrir un cartel.
    plan, problema = None, None
    if _preset_has_look_nodes(path):
        import LGA_Write_Presets_Look as look
        from LGA_Write_Presets_Dialogs import pick_plate

        look.set_logger(_log)
        _log("Resolviendo look del shot")
        plan, problema = look.resolve_look_plan(anchor, lambda entries: pick_plate(None, entries))
        _log("Plan de look:", plan, "| problema:", problema)

    problemas = []
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

        # Los backdrops del preset: LGA_backdrop y por encima de lo que ya hay.
        import LGA_Write_Presets_Backdrop as wp_backdrop

        wp_backdrop.set_logger(_log)
        backdrops = []
        for n in [n for n in pasted if n.Class() == "BackdropNode"]:
            nuevo = wp_backdrop.to_lga_backdrop(n)
            if nuevo is not n:
                nuevo.setSelected(True)
                pasted = [p for p in pasted if p is not n] + [nuevo]
            backdrops.append(nuevo)
        wp_backdrop.raise_backdrops(backdrops)

        vacios = _empty_look_nodes(pasted)
        if vacios and plan:
            import LGA_Write_Presets_Look as look

            problemas = look.apply_look_plan(vacios, plan)
        elif vacios and problema:
            problemas = [problema, "The CDL and LUT nodes were left empty."]
        import LGA_Write_Presets_Range as wp_range

        wp_range.offer_editref_range(pasted)
    except Exception as exc:
        _log("ERROR al pegar:", repr(exc))
        show_error(
            None,
            "Write Presets",
            "Could not paste the preset <b>%s</b>:<br>%s" % (_html(preset["name"]), _html(exc)),
        )
        return
    finally:
        undo.end()

    if problemas:
        _log("Problemas de look:", problemas)
        show_warning(
            None,
            "Write Presets",
            "The preset was pasted, but its look files need a check:<br><br>%s"
            % "<br>".join(_html(p) for p in problemas),
        )


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
    from LGA_Write_Presets_Dialogs import ask_question, show_error

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
        show_error(None, "Write Presets", "Could not delete the preset:<br>%s" % _html(exc))
        return False
    _log("A la papelera:", preset["path"])
    return True
