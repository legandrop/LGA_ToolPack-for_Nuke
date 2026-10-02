"""
____________________________________________________________________

  LGA_Write_Presets_Look v2.80 | Lega

  Resuelve los archivos de look (CDL y LMT) de un preset de cadena
  contra el shot donde se pega. Los presets se guardan sin rutas fijas;
  al pegarlos, los OCIOCDLTransform y OCIOFileTransform vacios se
  completan con lo que declara el .amf del shot:

    1. Ruta del .nk abierto -> carpeta del shot (la que tiene _input).
    2. <shot>/_input/Look_Files/ -> .amf agrupados por plate, version
       mas alta de cada uno.
    3. El plate: si hay uno solo, ese; si hay varios, el que nombra la
       ruta del Read que esta arriba del nodo donde se pega; si tampoco,
       el usuario elige (LGA_Write_Presets_Dialogs.pick_plate).
    4. Del .amf: el .cdl hermano con su cccid, el .clf que nombra el LMT,
       y el working space de cada uno. Sin .amf: un .cdl y un .clf por
       extension.

  COPIA de LGA_ApplyAMF v0.13 (repo LGA_ToolPack-B). Los repos no pueden
  importarse entre si, asi que esta logica viaja por copia: un arreglo en
  la busqueda de Look_Files, en la lectura del .amf o en el matcheo del
  working space se aplica en los dos archivos en la misma pasada.
  Lo propio de aca: plate_from_read() y resolve_look_plan().

  v2.79: Modulo nuevo.
____________________________________________________________________
"""

import os
import re
import xml.etree.ElementTree as ET

import nuke

INPUT_DIR_NAME = "_input"
LOOK_DIR_NAME = "Look_Files"

# La cadena de un .amf corre en ACES2065-1; el <cdlWorkingSpace> del CDL es
# la excepcion. Ver el header de LGA_ApplyAMF para el detalle.
AMF_WORKING_SPACE = "ACES2065-1"

FALLBACK_EFFECTS = (
    {"type": "OCIOCDLTransform", "extension": ".cdl"},
    {"type": "OCIOFileTransform", "extension": ".clf"},
)

LOOK_NODE_CLASSES = ("OCIOCDLTransform", "OCIOFileTransform")

# El log lo pone quien llama (LGA_Write_Presets_Chain), para que todo quede en
# el mismo .log de la corrida.
_logger = None


def set_logger(funcion):
    global _logger
    _logger = funcion


def debug_print(*message):
    if _logger:
        _logger(*message)


# ============================
# Helpers genericos
# ============================


def _find_subdir(parent_dir, wanted_name):
    """Subcarpeta por nombre sin distinguir mayusculas (macOS si distingue)."""
    if not parent_dir or not os.path.isdir(parent_dir):
        return None
    wanted = wanted_name.lower()
    try:
        for entry in os.scandir(parent_dir):
            if entry.is_dir() and entry.name.lower() == wanted:
                return entry.path
    except OSError as e:
        debug_print("  [WARN] No se pudo listar '%s': %s" % (parent_dir, e))
    return None


def _local_tag(element):
    """Tag sin namespace: los XML de ACES vienen como '{urn:...}lookTransform'."""
    return element.tag.split("}")[-1]


def _normalize(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def _slash(path):
    return re.sub(r"[\\/]+", "/", str(path))


# ============================
# Resolucion de rutas
# ============================


def get_script_path():
    """Ruta del .nk abierto, o None si el script nunca se guardo."""
    try:
        name = nuke.root().name()
    except Exception as e:
        debug_print("  [WARN] No se pudo leer el nombre del script: %s" % e)
        return None
    if not name or name == "Root":
        return None
    return _slash(name)


def resolve_shot_dir(script_path):
    """Sube por la ruta del .nk hasta el primer directorio que tenga _input.

    Por ESTRUCTURA y no por nombre: el .nk puede llevar otro vendor code que
    la carpeta del shot.
    """
    if not script_path:
        return None
    current = os.path.dirname(_slash(script_path))
    while current and current != os.path.dirname(current):
        if _find_subdir(current, INPUT_DIR_NAME):
            return _slash(current)
        current = os.path.dirname(current)
    return None


def resolve_look_dir(shot_dir):
    """<shot>/_input/Look_Files"""
    if not shot_dir:
        return None
    input_dir = _find_subdir(shot_dir, INPUT_DIR_NAME)
    if not input_dir:
        return None
    look_dir = _find_subdir(input_dir, LOOK_DIR_NAME)
    return _slash(look_dir) if look_dir else None


def find_look_file(look_dir, extension):
    """El primer archivo de esa extension en la carpeta de look."""
    if not look_dir:
        return None
    try:
        candidates = sorted(
            entry.path
            for entry in os.scandir(look_dir)
            if entry.is_file() and entry.name.lower().endswith(extension)
        )
    except OSError as e:
        debug_print("  [ERROR] No se pudo listar '%s': %s" % (look_dir, e))
        return None
    if not candidates:
        return None
    if len(candidates) > 1:
        debug_print(
            "  [AVISO] Hay %d archivos '%s', se usa el primero: %s"
            % (len(candidates), extension, os.path.basename(candidates[0]))
        )
    return _slash(candidates[0])


# ============================
# Plates
# ============================

# PROYECTO_SEQ_SHOT_VENDOR_aPlate_v001.amf: el plate es el anteultimo bloque.
_PLATE_RE = re.compile(r"^(?P<base>.*)_(?P<plate>[A-Za-z0-9]+)_v(?P<version>\d+)$")


def parse_plate_name(basename):
    stem = os.path.splitext(basename)[0]
    match = _PLATE_RE.match(stem)
    if not match:
        return None, None
    return match.group("plate"), int(match.group("version"))


def scan_amf_entries(look_dir):
    """Los .amf agrupados por plate, con la version mas alta de cada uno.

    Devuelve dicts {plate, version, path, name} ordenados por plate; los que
    no matchean el patron van al final, cada uno como su propia entrada.
    """
    if not look_dir:
        return []
    try:
        amf_files = [
            entry.path
            for entry in os.scandir(look_dir)
            if entry.is_file() and entry.name.lower().endswith(".amf")
        ]
    except OSError as e:
        debug_print("  [ERROR] No se pudo listar '%s': %s" % (look_dir, e))
        return []

    por_plate = {}
    sueltos = []
    for path in sorted(amf_files):
        nombre = os.path.basename(path)
        plate, version = parse_plate_name(nombre)
        if plate is None:
            sueltos.append(
                {"plate": os.path.splitext(nombre)[0], "version": None, "path": _slash(path), "name": nombre}
            )
            continue
        clave = plate.lower()
        anterior = por_plate.get(clave)
        if anterior is None or version > anterior["version"]:
            por_plate[clave] = {"plate": plate, "version": version, "path": _slash(path), "name": nombre}

    entradas = sorted(por_plate.values(), key=lambda e: e["plate"].lower())
    entradas.extend(sueltos)
    return entradas


def sibling_look_file(amf_path, extension):
    """'SHOT_aPlate_v001.amf' -> 'SHOT_aPlate_v001.cdl', sin distinguir mayusculas."""
    candidato = os.path.splitext(amf_path)[0] + extension
    if os.path.isfile(candidato):
        return _slash(candidato)
    carpeta = os.path.dirname(amf_path)
    buscado = os.path.basename(candidato).lower()
    try:
        for entry in os.scandir(carpeta):
            if entry.is_file() and entry.name.lower() == buscado:
                return _slash(entry.path)
    except OSError:
        pass
    return None


def read_cccid(cdl_path):
    """Atributo id del primer <ColorCorrection> del .cdl."""
    try:
        root = ET.parse(cdl_path).getroot()
    except Exception as e:
        debug_print("  [WARN] No se pudo parsear el .cdl: %s" % e)
        return None
    ids = [
        element.get("id")
        for element in root.iter()
        if _local_tag(element) == "ColorCorrection" and element.get("id")
    ]
    if not ids:
        debug_print("  [WARN] El .cdl no declara ningun ColorCorrection id")
        return None
    return ids[0]


def _upstream_read_paths(anchor):
    """Rutas de los Read que alimentan al ancla, subiendo por sus inputs."""
    rutas = []
    vistos = set()
    pendientes = [anchor] if anchor else []
    while pendientes and len(vistos) < 500:
        node = pendientes.pop()
        if node is None or node.fullName() in vistos:
            continue
        vistos.add(node.fullName())
        if node.Class() == "Read" and "file" in node.knobs():
            try:
                rutas.append(node["file"].evaluate() or node["file"].value())
            except Exception:
                rutas.append(node["file"].value())
        for i in range(node.inputs()):
            pendientes.append(node.input(i))
    return [r for r in rutas if r]


def plate_from_read(anchor, entries):
    """La entrada cuyo plate nombra la ruta de un Read de arriba, o None.

    Las carpetas de plate se nombran con el token en cualquier caja
    (ERSO_1013_0800_WAN_APLATE_V002), asi que se compara sin distinguir
    mayusculas y como bloque entero: 'aPlate' no debe matchear 'cbPlate'.
    """
    rutas = _upstream_read_paths(anchor)
    if not rutas:
        return None
    candidatas = []
    for entry in entries:
        if entry.get("version") is None:
            continue
        patron = re.compile(r"(^|[_/\\.])%s([_/\\.]|$)" % re.escape(entry["plate"]), re.IGNORECASE)
        if any(patron.search(ruta) for ruta in rutas):
            candidatas.append(entry)
    debug_print("  Plates nombrados por los Read de arriba:", [e["plate"] for e in candidatas])
    return candidatas[0] if len(candidatas) == 1 else None


# ============================
# Lectura del .amf
# ============================


def _target_space_from_transform_id(transform_id):
    if not transform_id:
        return None
    match = re.search(r"ACES_to_([A-Za-z0-9]+)", transform_id)
    return match.group(1) if match else None


def _target_space_from_description(description):
    if not description or " to " not in description:
        return None
    return description.split(" to ")[-1].strip() or None


def _read_look_transform(element):
    info = {
        "applied": (element.get("applied") or "").strip().lower() == "true",
        "description": None,
        "working_space": None,
        "file": None,
        "has_cdl": False,
    }
    for child in element.iter():
        tag = _local_tag(child)
        text = (child.text or "").strip() if child.text else ""
        if tag == "description" and not info["description"]:
            info["description"] = text
        elif tag == "file" and text:
            info["file"] = text
        elif tag in ("SOPNode", "SatNode", "SATNode", "cdlWorkingSpace"):
            info["has_cdl"] = True
    for child in element.iter():
        if _local_tag(child) != "toCdlWorkingSpace":
            continue
        for sub in child.iter():
            sub_tag = _local_tag(sub)
            sub_text = (sub.text or "").strip() if sub.text else ""
            if sub_tag == "transformId":
                info["working_space"] = _target_space_from_transform_id(sub_text)
            elif sub_tag == "description" and not info["working_space"]:
                info["working_space"] = _target_space_from_description(sub_text)
    return info


def read_amf(amf_path):
    try:
        root = ET.parse(amf_path).getroot()
    except Exception as e:
        debug_print("  [WARN] No se pudo parsear el .amf: %s" % e)
        return []
    return [
        _read_look_transform(element)
        for element in root.iter()
        if _local_tag(element) == "lookTransform"
    ]


def build_effect_plan(look_dir, amf_path=None):
    """Lista de specs {type, file, cccid, working_space} en orden de cadena."""
    if not amf_path:
        debug_print("  [AVISO] El shot no trae .amf: plan fijo por extension.")
        return _fallback_plan(look_dir)
    debug_print("  amf: %s" % amf_path)
    look_transforms = read_amf(amf_path)
    if not look_transforms:
        debug_print("  [AVISO] El .amf no declara lookTransform: plan fijo.")
        return _fallback_plan(look_dir)

    plan = []
    for index, info in enumerate(look_transforms, start=1):
        if info["applied"]:
            debug_print("    %d. [YA APLICADO] %s" % (index, info["description"]))
            continue
        if info["has_cdl"]:
            cdl_path = sibling_look_file(amf_path, ".cdl")
            if not cdl_path:
                debug_print("    %d. [ERROR] El .amf pide un CDL y no hay .cdl hermano" % index)
                continue
            plan.append(
                {
                    "type": "OCIOCDLTransform",
                    "file": cdl_path,
                    "cccid": read_cccid(cdl_path),
                    "working_space": info["working_space"] or AMF_WORKING_SPACE,
                }
            )
            continue
        if info["file"]:
            lmt_path = os.path.join(look_dir, info["file"])
            if not os.path.isfile(lmt_path):
                debug_print("    %d. [AVISO] El .amf nombra '%s' y no esta" % (index, info["file"]))
                lmt_path = find_look_file(look_dir, os.path.splitext(info["file"])[1])
                if not lmt_path:
                    continue
            plan.append(
                {
                    "type": "OCIOFileTransform",
                    "file": _slash(lmt_path),
                    "cccid": None,
                    "working_space": info["working_space"] or AMF_WORKING_SPACE,
                }
            )
            continue
        debug_print("    %d. [SALTEADO] Sin archivo asociado: %s" % (index, info["description"]))
    return plan


def _fallback_plan(look_dir):
    """Sin .amf: un .cdl (working space sin tocar) y un .clf en ACES2065-1."""
    plan = []
    for spec in FALLBACK_EFFECTS:
        file_path = find_look_file(look_dir, spec["extension"])
        if not file_path:
            continue
        es_cdl = spec["type"] == "OCIOCDLTransform"
        plan.append(
            {
                "type": spec["type"],
                "file": file_path,
                "cccid": read_cccid(file_path) if es_cdl else None,
                "working_space": None if es_cdl else AMF_WORKING_SPACE,
            }
        )
    return plan


# ============================
# Configuracion de nodos
# ============================


def _set_knob(node, knob_name, value):
    try:
        node[knob_name].setValue(value)
        debug_print("    [OK] %s.%s = %r" % (node.name(), knob_name, value))
        return True
    except Exception as e:
        debug_print("    [ERROR] No se pudo setear %s.%s: %s" % (node.name(), knob_name, e))
        return False


def match_colorspace_option(node, knob_name, wanted):
    """La opcion del enum que corresponde a `wanted` (ver LGA_ApplyAMF).

    Dos pasadas: primero los espacios nombrados directo y despues la lista
    entera, para que un ROL del config solo gane si nada directo sirve.
    """
    if not wanted:
        return None
    try:
        options = list(node[knob_name].values())
    except Exception as e:
        debug_print("    [WARN] No se pudieron leer las opciones de %s: %s" % (knob_name, e))
        return None
    target = _normalize(wanted)
    directas = [o for o in options if "(" not in str(o)]
    for candidatas in (directas, options):
        for opcion in candidatas:
            if _normalize(opcion) == target:
                return opcion
        for opcion in candidatas:
            if _normalize(opcion).endswith(target):
                return opcion
        for opcion in candidatas:
            if target in _normalize(opcion):
                return opcion
    return None


def configure_node(node, spec):
    """Carga archivo, cccid y working space. Devuelve un motivo si algo fallo."""
    motivo = None
    if spec["type"] == "OCIOCDLTransform":
        # read_from_file va PRIMERO: apagado, file y cccid se ignoran.
        _set_knob(node, "read_from_file", True)
        _set_knob(node, "file", spec["file"])
        if spec.get("cccid"):
            _set_knob(node, "cccid", spec["cccid"])
    else:
        _set_knob(node, "file", spec["file"])

    wanted = spec.get("working_space")
    if wanted:
        opcion = match_colorspace_option(node, "working_space", wanted)
        if opcion:
            _set_knob(node, "working_space", opcion)
        else:
            motivo = "%s: the project OCIO config has no '%s' colorspace" % (node.name(), wanted)
            debug_print("    [ERROR] " + motivo)
    return motivo


# ============================
# Lo propio de Write Presets
# ============================


def resolve_look_plan(anchor, ask_plate):
    """Plan de look para el shot del script abierto.

    Devuelve (plan, problema): plan es la lista de specs (puede estar vacia),
    problema un texto para el usuario o None. Si el usuario cancela la
    eleccion de plate devuelve (None, None).
    """
    script_path = get_script_path()
    if not script_path:
        return [], "The script is not saved, so there is no shot to take the look files from."
    look_dir = resolve_look_dir(resolve_shot_dir(script_path))
    debug_print("  Look_Files:", look_dir)
    if not look_dir:
        return [], "No <shot>/_input/Look_Files folder was found above the script."

    entries = scan_amf_entries(look_dir)
    debug_print("  .amf por plate:", [e["name"] for e in entries])
    amf_path = None
    if len(entries) == 1:
        amf_path = entries[0]["path"]
    elif len(entries) > 1:
        elegida = plate_from_read(anchor, entries)
        if elegida is None:
            elegida = ask_plate(entries)
            if elegida is None:
                debug_print("  Eleccion de plate cancelada")
                return None, None
        amf_path = elegida["path"]

    plan = build_effect_plan(look_dir, amf_path)
    if not plan:
        return [], "No .cdl or .clf was found in %s." % look_dir
    return plan, None


def apply_look_plan(look_nodes, plan):
    """Reparte los specs entre los nodos por tipo, en orden de cadena.

    Devuelve la lista de problemas para el cartel (vacia si todo bien).
    """
    problemas = []
    for clase in LOOK_NODE_CLASSES:
        nodos = sorted((n for n in look_nodes if n.Class() == clase), key=lambda n: n.ypos())
        specs = [s for s in plan if s["type"] == clase]
        for i, node in enumerate(nodos):
            if i >= len(specs):
                problemas.append("%s: the shot has no matching look file, left empty" % node.name())
                continue
            motivo = configure_node(node, specs[i])
            if motivo:
                problemas.append(motivo)
    return problemas
