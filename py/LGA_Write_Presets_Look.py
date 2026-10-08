"""
____________________________________________________________________

  LGA_Write_Presets_Look v2.86 | Lega

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
       y el working space de cada uno. Sin .amf: el .cdl suelto (si hay) y
       UN LMT, que es el .clf y, si no hay, el .cube (nunca los dos).

  COPIA de LGA_ApplyAMF (repo LGA_ToolPack-B): la busqueda de Look_Files y
  la lectura del .amf son las de v0.13; match_colorspace_option y el chequeo
  de hasError de configure_node son los de v0.15; el .cube (cube_working_space,
  parse_lut_name, scan_look_entries, el plan fijo .cdl + LMT) es el de v0.16. Los repos no pueden
  importarse entre si, asi que esta logica viaja por copia: un arreglo en
  la busqueda de Look_Files, en la lectura del .amf o en el matcheo del
  working space se aplica en los dos archivos en la misma pasada.
  Lo propio de aca: plate_from_read() y resolve_look_plan().

  v2.86: Reconoce el .cube de Look_Files como LMT del shot. Sin .amf el plan
         fijo es el .cdl suelto y UN LMT: el .clf y, si no hay, el .cube
         (nunca los dos). Su working space sale del nombre del archivo (por
         defecto ACEScct). Con varios .cube (distinto nombre sin _vNNN) se
         pregunta cual. El nodo LMT del preset recibe el LMT del shot sea
         .clf o .cube, y tambien un OCIOFileTransform con ruta fija a un .cube
         o .clf (presets armados a mano: los guardados ya no traen rutas).
  v2.85: Los configs OCIO v2 de Foundry de Nuke 17 listan cada colorspace como
         'ACEScct<TAB>Colorspaces/...<TAB><TAB>alias': match_colorspace_option
         devolvia la cadena entera, el nodo quedaba con error y el look sin
         aplicar, sin aviso. Ahora matchea y devuelve el nombre corto (lo
         anterior al TAB) y deja los alias de aces_1.2 para el final. Un nodo
         que queda con error (archivo vacio, corrupto o inexistente) sube al
         cartel de problemas de look.
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

# Un .cube es un LUT 1D/3D pelado: no trae metadata, ni siquiera dice en que
# espacio de color espera su entrada. Se deduce del nombre del archivo y, sin
# pista, se asume ACEScct, que es la convencion de los LMT de ACES (un LMT en
# un OCIOFileTransform con working space ACEScct es la forma en que el estudio
# arma el look del shot). El nombre que se pide es el LOGICO ('ACEScct'): el
# nombre real del colorspace lo resuelve match_colorspace_option contra el
# config OCIO activo, porque cambia de config en config ('ACEScct' a secas o
# 'ACES - ACEScct').
CUBE_EXTENSION = ".cube"
CUBE_DEFAULT_SPACE = "ACEScct"

# Pista del nombre -> espacio logico. 'linear' se lee como lineal ACES (AP0),
# no como cualquier lineal: el .cube de un LMT de ACES que dice 'Linear' habla
# de ACES2065-1. Los lookahead evitan que 'acescc' matchee adentro de
# 'acescct' y que 'linear' matchee adentro de 'nonlinear'.
_CUBE_SPACE_HINTS = {
    "acescct": "ACEScct",
    "acescc": "ACEScc",
    "acescg": "ACEScg",
    "ap1": "ACEScg",
    "aces2065": "ACES2065-1",
    "ap0": "ACES2065-1",
    "linear": "ACES2065-1",
}
_CUBE_SPACE_RE = re.compile(
    r"(?<![a-z0-9])(%s)(?![a-z])"
    % "|".join(sorted(_CUBE_SPACE_HINTS, key=len, reverse=True))
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


_LUT_VERSION_RE = re.compile(r"^(?P<base>.+)_v(?P<version>\d+)$", re.IGNORECASE)


def parse_lut_name(basename):
    """Devuelve (nombre sin version, version) de un .cube, o (None, None).

    A diferencia de un .amf, el token que precede a '_vNNN' NO identifica un
    plate: en 'PROJA_Preview_LMT_v001.cube' y 'PROJA_Final_LMT_v001.cube' los
    dos terminan en 'LMT' y son LUT distintos. Por eso la clave de agrupado es el
    nombre ENTERO sin el '_vNNN' final: las versiones de un mismo LUT colapsan
    en una entrada y dos LUT distintos quedan separados para el cartel.
    """
    stem = os.path.splitext(basename)[0]
    match = _LUT_VERSION_RE.match(stem)
    if not match:
        return None, None
    return match.group("base"), int(match.group("version"))


def scan_look_entries(look_dir, extension):
    """Los archivos de esa extension, agrupados por plate y con la version mas alta.

    Un shot tipico trae un .amf por version de cada plate
    (aPlate_v001, cbPlate_v001..v004). Ofrecer las cinco versiones no ayuda:
    lo que se aplica es el plate, y de cada plate la ultima version. Los
    archivos cuyo nombre no matchea el patron se ofrecen igual, cada uno como
    su propia entrada, para no esconderlos.

    Sirve para .amf y para .cube. En un .amf el token anterior a '_vNNN' es el
    plate; en un .cube se agrupa por el nombre entero sin el '_vNNN' final (ver
    parse_lut_name).

    Devuelve una lista de dicts {plate, version, path, name}, ordenada por
    nombre de plate.
    """
    if not look_dir:
        return []

    try:
        amf_files = [
            entry.path
            for entry in os.scandir(look_dir)
            if entry.is_file() and entry.name.lower().endswith(extension)
        ]
    except OSError as e:
        debug_print("  [ERROR] No se pudo listar '%s': %s" % (look_dir, e))
        return []

    por_plate = {}
    sueltos = []
    for path in sorted(amf_files):
        nombre = os.path.basename(path)
        if extension == CUBE_EXTENSION:
            plate, version = parse_lut_name(nombre)
        else:
            plate, version = parse_plate_name(nombre)
        if plate is None:
            sueltos.append(
                {
                    "plate": os.path.splitext(nombre)[0],
                    "version": None,
                    "path": _slash(path),
                    "name": nombre,
                }
            )
            continue
        clave = plate.lower()
        anterior = por_plate.get(clave)
        if anterior is None or version > anterior["version"]:
            por_plate[clave] = {
                "plate": plate,
                "version": version,
                "path": _slash(path),
                "name": nombre,
            }

    entradas = sorted(por_plate.values(), key=lambda e: e["plate"].lower())
    entradas.extend(sueltos)
    return entradas


def scan_amf_entries(look_dir):
    """Los .amf de la carpeta (ver scan_look_entries)."""
    return scan_look_entries(look_dir, ".amf")


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
    (PROJA_1013_0800_WAN_APLATE_V002), asi que se compara sin distinguir
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


def build_effect_plan(look_dir, amf_path=None, cube_path=None):
    """Lista de specs {type, file, cccid, working_space} en orden de cadena.

    `cube_path` es el .cube ya elegido; solo se usa en el plan fijo sin .amf.
    """
    if not amf_path:
        debug_print("  [AVISO] El shot no trae .amf: plan fijo por extension.")
        return _fallback_plan(look_dir, cube_path)
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


def _fallback_plan(look_dir, cube_path=None):
    """Sin .amf: el .cdl suelto (working space sin tocar) y UN LMT.

    El LMT es el .clf (en ACES2065-1) y, si no hay, el `cube_path` (working
    space por el nombre, ver cube_working_space). Nunca los dos: son ambos el
    LMT del shot y aplicarlos juntos dobla el look.
    """
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
    hay_lmt = any(spec["type"] == "OCIOFileTransform" for spec in plan)
    if cube_path and not hay_lmt:
        plan.append(cube_spec(cube_path))
    elif cube_path:
        debug_print("  [INFO] Hay .clf y .cube: se usa el .clf como LMT.")
    return plan


# ============================
# .cube como look del shot
# ============================


def has_look_file(look_dir, extension):
    """True si la carpeta trae al menos un archivo de esa extension."""
    if not look_dir:
        return False
    try:
        for entry in os.scandir(look_dir):
            if entry.is_file() and entry.name.lower().endswith(extension):
                return True
    except OSError as e:
        debug_print("  [WARN] No se pudo listar '%s': %s" % (look_dir, e))
    return False


def cube_working_space(cube_path):
    """Espacio de color en el que corre el .cube. Devuelve (espacio, origen).

    Un .cube no declara su espacio de entrada, asi que se lee del nombre
    (ACEScct, ACEScc, ACEScg, AP1, ACES2065, AP0, Linear; sin distinguir
    mayusculas ni exigir un separador concreto) y, sin pista, se asume
    CUBE_DEFAULT_SPACE. Si el nombre trae mas de un espacio ('ACEScg_to_ACEScct')
    gana el PRIMERO, que por convencion es el de entrada, y queda avisado en el
    log. El espacio devuelto es el nombre logico: configure_node lo resuelve
    contra el config OCIO real.

    `origen` es 'nombre' o 'default', para el log.
    """
    stem = os.path.splitext(os.path.basename(cube_path))[0].lower()
    hallados = [m.group(1) for m in _CUBE_SPACE_RE.finditer(stem)]
    if not hallados:
        return CUBE_DEFAULT_SPACE, "default"

    espacios = []
    for pista in hallados:
        espacio = _CUBE_SPACE_HINTS[pista]
        if espacio not in espacios:
            espacios.append(espacio)
    if len(espacios) > 1:
        debug_print(
            "  [AVISO] El nombre del .cube menciona varios espacios (%s): "
            "se usa el primero." % ", ".join(espacios)
        )
    return espacios[0], "nombre"


def pick_cube(look_dir, ask_plate):
    """Elige el .cube a usar. Devuelve (ruta, cancelado).

    Con uno solo no se pregunta. Con varios se agrupan por nombre sin version
    (scan_look_entries) y, si queda mas de uno, se usa el cartel de eleccion
    (`ask_plate(entradas, ".cube")`). Sin ningun .cube devuelve (None, False).
    """
    entradas = scan_look_entries(look_dir, CUBE_EXTENSION)
    debug_print("  .cube por nombre:", [e["name"] for e in entradas])
    if not entradas:
        return None, False
    if len(entradas) == 1:
        return entradas[0]["path"], False
    elegido = ask_plate(entradas, CUBE_EXTENSION)
    if elegido is None:
        debug_print("  Eleccion de .cube cancelada")
        return None, True
    return elegido["path"], False


def cube_spec(cube_path):
    """El .cube como eslabon LMT: un OCIOFileTransform con su working space."""
    espacio, origen = cube_working_space(cube_path)
    debug_print(
        "    [APLICAR] LUT -> %s (working space: %s, segun %s)"
        % (os.path.basename(cube_path), espacio, origen)
    )
    return {
        "type": "OCIOFileTransform",
        "file": _slash(cube_path),
        "cccid": None,
        "working_space": espacio,
        "label": "LMT",
    }


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
    """Encuentra en el enum del knob la opcion que corresponde a `wanted`.

    El nombre exacto del espacio depende del OCIO config del proyecto: el
    mismo ACEScct puede figurar como 'ACEScct' o 'ACES - ACEScct'. Por eso no
    se hardcodea el string, se busca contra las opciones reales del knob.

    Cada opcion del enum de Nuke 17 trae el nombre del colorspace seguido de
    campos separados por TAB: en aces_1.2 'ACES - ACEScct<TAB>Colorspaces/ACES/ACES -
    ACEScct', y en los configs v2 de Foundry (fn-nuke_cg-config-v2.2.0_aces-v1.3,
    studio v2.2.0, los v3.0.0 de ACES 2.0) 'ACEScct<TAB>Colorspaces/ACES/ACEScct<TAB><TAB>ACES -
    ACEScct,acescct_ap1'. El knob ACEPTA la cadena entera, pero el nodo queda con
    hasError=True y el LUT no se aplica (pixel 0.0), sin ningun aviso. Lo valido
    es SOLO el primer campo, asi que se matchea contra el y se devuelve ese.
    """
    if not wanted:
        return None

    try:
        options = list(node[knob_name].values())
    except Exception as e:
        debug_print("    [WARN] No se pudieron leer las opciones de %s: %s" % (knob_name, e))
        return None

    target = _normalize(wanted)

    # Cada opcion es (cadena entera, nombre corto). El nombre corto es lo que va
    # antes del primer TAB; sin TAB (otras versiones de Nuke) es la cadena entera
    # y todo sigue como antes. Se matchea contra el nombre corto y no contra la
    # cadena larga: esa trae la ruta y los alias del colorspace, y 'acescc'
    # aparece adentro de los de 'ACEScct'. Se DEVUELVE el corto.
    pares = [(str(o), str(o).split("\t")[0]) for o in options]

    # Los alias van al final. aces_1.2 trae una familia 'Utility/Aliases' con
    # nombres en minuscula ('acescct', 'acescg'...) que son colorspaces validos
    # pero no son el nombre del espacio: con el matcheo por nombre corto ganarian
    # por igualdad exacta y el nodo quedaria con 'acescct' en vez de
    # 'ACES - ACEScct'. Solo se usan si nada mas sirve.
    sin_alias = [par for par in pares if "/aliases/" not in par[0].lower()]

    # Tres pasadas: primero los espacios nombrados DIRECTO (sin alias), despues
    # los demas sin alias, y recien al final todo. Los ROLES del config aparecen
    # en versiones viejas del enum con formato 'scene_linear (ACES - ACEScg)' y son
    # una INDIRECCION: pidiendo ACES2065-1 matchean 'ACES - ACES2065-1' y
    # 'default (ACES - ACES2065-1)', y cual gana depende del orden del enum. La
    # segunda pasada no es un adorno: hay colorspaces directos con parentesis en
    # su propio nombre -en aces_1.2 hay 34, del tipo 'Input - ARRI - V3 LogC
    # (EI160) - Wide Gamut'-, y descartarlos de una dejaria sin resolver a quien
    # pida uno de esos. Un rol o un alias solo gana si NADA directo sirve.
    directas = [par for par in sin_alias if "(" not in par[1]]

    for candidatas in (directas, sin_alias, pares):
        # De mas estricto a mas laxo. El orden importa: buscando 'ACEScc'
        # primero por igualdad y sufijo se evita que matchee 'ACEScct' por
        # contencion.
        for _entera, corto in candidatas:
            if _normalize(corto) == target:
                return corto
        for _entera, corto in candidatas:
            if _normalize(corto).endswith(target):
                return corto
        for _entera, corto in candidatas:
            if target in _normalize(corto):
                return corto

    debug_print("    [WARN] '%s' no figura entre las opciones de %s" % (wanted, knob_name))
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

    # Un archivo vacio, corrupto o inexistente deja el nodo con error y sin
    # ningun aviso: el setValue del knob file sale bien igual. Se mira DESPUES
    # de configurar todo. El motivo sube al mismo cartel que los demas.
    try:
        con_error = bool(node.hasError())
    except Exception as e:
        con_error = False
        debug_print("    [WARN] No se pudo leer hasError de %s: %s" % (node.name(), e))
    if con_error:
        aviso_archivo = "%s: could not load '%s'" % (
            node.name(),
            os.path.basename(str(spec["file"])),
        )
        debug_print("    [ERROR] " + aviso_archivo)
        motivo = aviso_archivo if not motivo else "%s; %s" % (motivo, aviso_archivo)
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

    # El .cube es el LMT cuando no hay .amf (manda el .amf) ni .clf (el .clf y el
    # .cube son los dos LMT: se usa uno solo y gana el .clf). Se elige ACA y no
    # adentro del plan porque con varios .cube abre el cartel de eleccion.
    cube_path = None
    if not entries:
        if has_look_file(look_dir, ".clf"):
            if has_look_file(look_dir, CUBE_EXTENSION):
                debug_print("  Hay .clf y .cube: se usa el .clf como LMT")
        else:
            cube_path, cancelado = pick_cube(look_dir, ask_plate)
            if cancelado:
                return None, None

    plan = build_effect_plan(look_dir, amf_path, cube_path)
    if not plan:
        return [], "No .cdl, .clf or .cube was found in %s." % look_dir
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
                quedo = "unchanged" if node["file"].toScript().strip('" ') else "empty"
                problemas.append("%s: the shot has no matching look file, left %s" % (node.name(), quedo))
                continue
            motivo = configure_node(node, specs[i])
            if motivo:
                problemas.append(motivo)
    return problemas
