"""
_______________________________________

  LGA_MediaManager_config v2.32 | Lega
  Donde vive la configuracion del Media Manager, y que tiene adentro

  v2.28: El tema de fabrica pasa de "lga" a "pack": la herramienta
         abre por primera vez con el aspecto del resto del ToolPack y
         desde ahi el usuario elige. El .ini semilla va igual.
  v2.26: Suma el esquema de la configuracion, que antes estaba
         repartido entre la ventana de ajustes y el FileScanner.
         El .ini pasa a tener [ShotFolder], [Locations] y
         [Appearance]: el project_folder_depth se convierte en una
         ruta de shot explicita y los destinos de [CopyOptions]
         pasan a ser locations, con el atajo en su propio campo en
         vez de embebido en el nombre con un '&'.
         La migracion se hace en memoria y no se escribe hasta el
         primer guardado, asi un .ini viejo no se toca si algo sale
         mal. El depth se traduce como depth-1 saltos: contaba
         dirname() sobre la RUTA DEL ARCHIVO .nk y no sobre su
         carpeta, asi que el default historico de 3 es "../..".
         Cuida la configuracion que ya tenia el usuario: conserva el
         nombre si habia renombrado un destino, no le inventa atajos
         duplicados ni de los que ya usa la barra, no rebasa una ruta
         absoluta ni rompe una UNC, y lee todos los indices que haya
         en vez de contar 1..N -con un hueco se borraba en silencio
         todo lo que venia despues-. Si el archivo existe y no se
         puede leer lo dice en load_error, para que la ventana no
         guarde los valores de fabrica encima.
  v2.25: Modulo nuevo. El .ini pasa a la carpeta de datos del
         usuario; el que viaja dentro del pack queda solo como
         semilla de la primera instalacion.
_______________________________________

"""

import configparser
import os
import platform
import re
import tempfile


# El .ini que viaja adentro del pack. Sirve UNA vez: la primera, para
# sembrar la config del usuario. Despues nadie mas lo escribe, porque el
# instalador reemplaza la carpeta del pack entera en cada actualizacion y
# ahi se perderian los destinos que el usuario haya configurado.
PACK_INI_NAME = "LGA_mediaManagerSettings.ini"

# Misma carpeta de usuario que usa Enable Tools, para que toda la config del
# pack quede junta y se pueda respaldar de una.
USER_DIR_PARTS = ("LGA", "ToolPack")
USER_INI_NAME = "MediaManager.ini"

# Si no hay carpeta de datos del sistema, o no se puede escribir en ella,
# la config cae adentro del .nuke, al lado del pack pero no dentro: el
# instalador reemplaza la carpeta del pack y esta la deja en paz.
FALLBACK_DIR_NAME = "LGA_Settings"

PY_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PY_DIR)


def get_user_config_dir():
    """Carpeta de datos del usuario segun el sistema. None si no se puede."""
    system = platform.system()
    if system == "Windows":
        return os.getenv("APPDATA")
    if system == "Darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.path.expanduser("~/.config")


def get_nuke_dir():
    """La carpeta .nuke REAL donde quedo instalado el pack.

    No se usa expanduser("~"): el instalador acepta un .nuke en cualquier
    ruta, y ahi el home del usuario no tiene nada. El pack siempre vive en
    <NukeDir>/LGA_ToolPack.
    """
    return os.path.dirname(ROOT_DIR)


def get_pack_ini_path():
    """El .ini de fabrica, el que viaja adentro del pack."""
    return os.path.join(PY_DIR, PACK_INI_NAME)


def get_fallback_dir():
    """Donde va la config si la carpeta de datos del sistema no sirve."""
    return os.path.join(get_nuke_dir(), FALLBACK_DIR_NAME, USER_DIR_PARTS[-1])


def get_user_ini_path(create_dir=False):
    """
    El .ini del usuario, el unico que se escribe.

    Con create_dir se prueban las dos carpetas candidatas en orden y se
    devuelve la primera que se pueda crear. Devuelve None si ninguna: no hay
    tercera opcion, porque escribir adentro del pack seria perder la config
    en la proxima actualizacion, que es justo lo que este modulo evita.
    """
    candidatas = []
    base = get_user_config_dir()
    if base:
        candidatas.append(os.path.join(base, *USER_DIR_PARTS))
    candidatas.append(get_fallback_dir())

    if not create_dir:
        return os.path.join(candidatas[0], USER_INI_NAME)

    for user_dir in candidatas:
        try:
            os.makedirs(user_dir, exist_ok=True)
        except OSError:
            continue
        if os.access(user_dir, os.W_OK):
            return os.path.join(user_dir, USER_INI_NAME)
    return None


def get_read_path():
    """
    De donde se lee la configuracion.

    Manda el .ini del usuario. El del pack solo se usa mientras ese no
    exista, o sea hasta el primer guardado.
    """
    user_ini = get_user_ini_path()
    if user_ini and os.path.isfile(user_ini):
        return user_ini
    return get_pack_ini_path()


def get_write_path():
    """
    A donde se escribe. Siempre al del usuario, o None si no hay donde.

    Nunca devuelve el del pack: escribir ahi es perder la configuracion en
    la proxima actualizacion. Quien llama tiene que avisarle al usuario que
    no se pudo guardar, en vez de guardar en un lugar que se va a borrar.
    """
    return get_user_ini_path(create_dir=True)


def write_ini(path, contenido):
    """
    Escribe el .ini de forma atomica. Devuelve True si quedo guardado.

    Se escribe a un temporal en la misma carpeta y recien ahi se reemplaza:
    un `open(path, "w")` trunca primero, asi que dos Nukes guardando a la vez
    -o un cierre a destiempo- pueden dejar el archivo a medias o vacio.
    """
    carpeta = os.path.dirname(path)
    descriptor = None
    temporal = None
    try:
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp")
        with os.fdopen(descriptor, "w", newline="\n", encoding="utf-8") as archivo:
            descriptor = None  # lo cierra el context manager
            archivo.write(contenido)
        os.replace(temporal, path)
        return True
    except OSError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporal and os.path.exists(temporal):
            try:
                os.remove(temporal)
            except OSError:
                pass
        return False


# ---------------------------------------------------------------------------
#                          Esquema de la configuracion
# ---------------------------------------------------------------------------
# El bloque de arriba dice DONDE vive el .ini. Este dice QUE tiene adentro.
# No sabe nada de Nuke ni de Qt: se puede probar sin abrir el host.


# Las locations de fabrica. Son las mismas tres del .ini historico mas Publish,
# reescritas como patrones relativos a la carpeta del .nk.
DEFAULT_LOCATIONS = (
    {"name": "Input", "path": "../../*input*", "scan": True, "copy_to": True, "shortcut": "I"},
    {"name": "Assets", "path": "../*assets*", "scan": True, "copy_to": True, "shortcut": "A"},
    {"name": "Prerenders", "path": "../*prerenders*", "scan": True, "copy_to": True, "shortcut": "P"},
    {"name": "Publish", "path": "../*publish*", "scan": True, "copy_to": False, "shortcut": ""},
)

# El shot folder: el limite del shot. De el sale el estado Outside, y con el la
# razon de ser de Copy to. Reemplaza al project_folder_depth.
DEFAULT_SHOT = {"enabled": True, "path": "../.."}

# El tema de fabrica es el del pack, el mismo que reciben las demas ventanas
# migradas: la herramienta abre por primera vez con el aspecto del resto del
# ToolPack y desde ahi el usuario elige. Es tambien el primero de la tira de
# botones de la ventana de ajustes.
DEFAULT_APPEARANCE = {"theme": "pack", "table_font_size": 13}

FONT_SIZE_MIN = 9
FONT_SIZE_MAX = 20

# Las letras que ya usan los mnemonicos de la barra de herramientas. Si una
# location toma una de estas, Qt no dispara ninguno de los dos y avisa por
# consola con "ambiguous shortcut".
RESERVED_SHORTCUTS = ("G", "R", "L", "C", "D")

# Los tres destinos que traia el .ini historico, mapeados a la location de
# fabrica que los reemplaza. Se comparan por la ruta vieja normalizada porque
# son valores conocidos y fijos, no texto libre: asi al usuario que nunca los
# toco no se le duplican las tres filas.
LEGACY_EQUIVALENTS = {
    "_input": "Input",
    "comp/0_assets": "Assets",
    "comp/2_prerenders": "Prerenders",
}


# --------------------------------------------------------------- helpers ---
def _unquote(valor):
    """
    Saca UN par de comillas envolventes, no todas.

    Con strip('"') un nombre que termina en comilla perdia una por lectura y
    se iba comiendo sola a lo largo de los guardados.
    """
    texto = "" if valor is None else str(valor).strip()
    if len(texto) >= 2 and texto[0] == '"' and texto[-1] == '"':
        return texto[1:-1]
    return texto


def _to_bool(valor, por_defecto=False):
    """Lee un booleano del .ini sin explotar con basura."""
    if valor is None:
        return por_defecto
    return _unquote(valor).lower() in ("1", "true", "yes", "on")


def _to_int(valor, por_defecto):
    try:
        return int(_unquote(valor))
    except (TypeError, ValueError):
        return por_defecto


def _clamp_font_size(valor):
    """
    Acota el tamano de letra. Se usa al LEER y al ESCRIBIR.

    Al leer tambien, no solo al escribir: un .ini editado a mano con un 200
    deja la ventana inusable y sin forma de volver desde la propia UI.
    """
    return max(FONT_SIZE_MIN, min(FONT_SIZE_MAX,
                                  _to_int(valor, DEFAULT_APPEARANCE["table_font_size"])))


def _one_line(valor):
    """
    Un valor de .ini es UNA linea. Todo lo que pueda cortarla se aplana.

    Sin esto, un salto de linea pegado en el campo de nombre o de ruta partia
    el archivo en dos y ConfigParser no lo podia volver a leer: el usuario
    quedaba con un "no se pudo leer la configuracion" permanente, que solo se
    arregla editando el .ini a mano. Y con el texto elegido se podia escribir
    una seccion entera que esa fila no controla.
    """
    return re.sub(r"[\r\n]+", " ", "" if valor is None else str(valor)).strip()


def _clean_shortcut(valor):
    """Una sola letra o numero, en mayuscula. Vacio si no hay nada usable."""
    return re.sub(r"[^A-Za-z0-9]", "", _unquote(valor))[:1].upper()


def is_absolute(ruta):
    """
    Si la ruta NO es relativa al .nk.

    No alcanza con os.path.isabs: el .ini se comparte entre las dos maquinas,
    asi que una ruta de Windows tiene que reconocerse tambien corriendo en Mac.
    """
    texto = (ruta or "").strip()
    if not texto:
        return False
    return (
        texto.startswith("/")
        or texto.startswith("\\\\")          # UNC
        or bool(re.match(r"^[A-Za-z]:", texto))
        # Una ruta que arranca con una variable o con ~ tampoco es relativa al
        # .nk: anteponerle ".." la convierte en basura. En un pipeline de Nuke
        # son comunes.
        or texto[0] in "~$%"
    )


def _to_slashes(ruta):
    """Barras normales y sin repetir, conservando el prefijo UNC."""
    texto = (ruta or "").replace("\\", "/")
    unc = texto.startswith("//")
    texto = re.sub(r"/{2,}", "/", texto)
    return ("/" + texto) if unc else texto


def _normalize_legacy_path(ruta):
    return _to_slashes(_unquote(ruta)).strip("/").lower()


def _split_legacy_name(texto):
    """
    Parte un nombre historico en (nombre limpio, letra del atajo).

    En el formato viejo el atajo iba embebido en el propio nombre con un '&',
    que es el mnemonico de Qt: "&Assets" se disparaba con Alt+A. Ahora la letra
    tiene su propio campo, asi que el nombre queda legible y el atajo se puede
    cambiar sin renombrar el destino.

    Un '&&' es un '&' literal para Qt, no un mnemonico: "R&&D" es la marca
    R&D y no un atajo a la D.
    """
    texto = _unquote(texto)
    letra = ""
    salida = []
    i = 0
    while i < len(texto):
        if texto[i] == "&":
            if i + 1 < len(texto) and texto[i + 1] == "&":
                salida.append("&")
                i += 2
                continue
            if not letra and i + 1 < len(texto):
                letra = _clean_shortcut(texto[i + 1])
            i += 1
            continue
        salida.append(texto[i])
        i += 1
    return "".join(salida).strip(), letra


def _assign_shortcut(letra, tomadas):
    """
    Devuelve la letra si se puede usar, o "" si no.

    Se descartan las que ya tomo otra location y las cinco de los mnemonicos
    de la barra: si dos acciones comparten Alt+X, Qt no dispara NINGUNA y avisa
    por consola. Es mejor quedarse sin atajo -que se ve y se corrige en un
    segundo- que con dos que no andan.
    """
    letra = _clean_shortcut(letra)
    if not letra or letra in RESERVED_SHORTCUTS or letra in tomadas:
        return ""
    tomadas.add(letra)
    return letra


def _indices(seccion, patron):
    """
    Los indices presentes en una seccion, en orden.

    Se juntan los que HAY en vez de contar 1..N: con un hueco -un guardado
    interrumpido, o el .ini editado a mano- contar cortaba en el primer indice
    faltante y borraba en silencio todo lo que venia despues.
    """
    encontrados = set()
    for clave in seccion:
        match = re.match(patron, clave)
        if match:
            encontrados.add(int(match.group(1)))
    return sorted(encontrados)


# ----------------------------------------------------------- lectura ---
def _read_locations(config):
    """Las locations del formato nuevo, en orden. None si la seccion no esta."""
    if "Locations" not in config:
        return None
    seccion = config["Locations"]
    locations = []
    for indice in _indices(seccion, r"location_(\d+)_name$"):
        locations.append({
            "name": _unquote(seccion.get("location_%d_name" % indice)),
            "path": _unquote(seccion.get("location_%d_path" % indice)),
            "scan": _to_bool(seccion.get("location_%d_scan" % indice), True),
            "copy_to": _to_bool(seccion.get("location_%d_copy_to" % indice)),
            "shortcut": _clean_shortcut(seccion.get("location_%d_shortcut" % indice)),
        })
    return locations


def _read_shot(config):
    """El shot folder, o None si la seccion no esta."""
    if "ShotFolder" not in config:
        return None
    shot = dict(DEFAULT_SHOT)
    shot["enabled"] = _to_bool(config["ShotFolder"].get("enabled"), True)
    ruta = _unquote(config["ShotFolder"].get("path"))
    if ruta:
        shot["path"] = ruta
    return shot


def _known_theme_ids():
    """Los temas que existen, o None si el modulo de estilo no esta a mano."""
    try:
        from LGA_UI_Style_ToolPack import theme_ids
        return tuple(theme_ids())
    except Exception:
        return None


def _read_appearance(config, theme_ids=None):
    apariencia = dict(DEFAULT_APPEARANCE)
    if theme_ids is None:
        theme_ids = _known_theme_ids()
    if "Appearance" not in config:
        return apariencia
    tema = _unquote(config["Appearance"].get("theme"))
    # Se valida contra los temas que existen: un id de una version mas nueva
    # del pack, o un typo, tiene que caer al default y no viajar hacia adelante.
    if tema and (theme_ids is None or tema in theme_ids):
        apariencia["theme"] = tema
    apariencia["table_font_size"] = _clamp_font_size(
        config["Appearance"].get("table_font_size"))
    return apariencia


# ---------------------------------------------------------- migracion ---
def _shot_jumps(shot_path):
    """Cuantas carpetas sube una ruta de shot relativa. None si no aplica."""
    if not shot_path or is_absolute(shot_path):
        return None
    partes = [p for p in _to_slashes(shot_path).split("/") if p and p != "."]
    return len(partes) if all(p == ".." for p in partes) else None


def _legacy_depth(config):
    """Los saltos de carpeta que decia el .ini viejo, desde la carpeta del .nk.

    El project_folder_depth era la cantidad de dirname() a aplicar sobre la
    RUTA DEL ARCHIVO .nk, no sobre su carpeta: con depth=1 se llegaba a la
    carpeta del propio .nk. Asi que subir N carpetas desde ahi es depth-1, y el
    default historico de 3 equivale a "../..", que es el default nuevo.
    Traducirlo como depth deja el shot un nivel mas arriba, para todos.
    """
    depth = 3
    if "LGA_mediaManagerSettings" in config:
        depth = _to_int(
            config["LGA_mediaManagerSettings"].get("project_folder_depth"), 3)
    return max(0, max(1, min(10, depth)) - 1)


def _rebase_legacy_path(ruta, saltos):
    """Pasa una ruta relativa a la carpeta del shot a relativa al .nk."""
    limpia = _to_slashes(_unquote(ruta))
    # Una ruta absoluta no se rebasa: anteponerle ".." la convertia en basura
    # del tipo "../../C:/shared/rnd".
    if is_absolute(limpia):
        return limpia
    limpia = limpia.strip("/")
    return "/".join([".."] * saltos + [limpia]) if saltos else limpia


def _migrate_locations(config, saltos):
    """
    Los destinos de [CopyOptions] convertidos en locations.

    Se respeta el ORDEN del usuario: sus destinos salen primero y en el mismo
    orden que tenian, porque ese es el orden del menu Copy to. Las locations de
    fabrica que el usuario no tenia van al final y con Copy to APAGADO: si las
    habia sacado del menu fue a proposito, y devolverselas prendidas es
    deshacerle una decision. Se agregan igual, con Scan prendido, porque como
    carpetas a escanear son nuevas: eso no existia en el formato viejo.
    """
    de_fabrica = {l["name"]: dict(l) for l in DEFAULT_LOCATIONS}
    orden_fabrica = [l["name"] for l in DEFAULT_LOCATIONS]

    if "CopyOptions" not in config:
        return [dict(l) for l in DEFAULT_LOCATIONS]

    seccion = config["CopyOptions"]
    locations = []
    usadas = set()
    pendientes = []   # (location, atajo pedido), para asignar atajos al final

    for indice in _indices(seccion, r"copy_(\d+)_button_text$"):
        nombre, atajo = _split_legacy_name(seccion.get("copy_%d_button_text" % indice))
        ruta = _unquote(seccion.get("copy_%d_subdirectory" % indice))
        if not ruta or (not nombre and not atajo):
            continue
        equivalente = LEGACY_EQUIVALENTS.get(_normalize_legacy_path(ruta))

        if equivalente and equivalente not in usadas:
            # Uno de los tres de fabrica: se conserva su patron con comodin y
            # su Scan, pero manda lo que el usuario le haya cambiado.
            location = de_fabrica[equivalente]
            if nombre and nombre != equivalente:
                location["name"] = nombre
            usadas.add(equivalente)
        else:
            # Un destino propio. Su ruta era relativa a la carpeta del shot;
            # ahora todo es relativo al .nk, asi que se le anteponen los saltos.
            location = {
                "name": nombre or ruta.strip("/").split("/")[-1],
                "path": _rebase_legacy_path(ruta, saltos),
                "scan": False,   # era un destino de copia, no una carpeta a escanear
                "copy_to": True,
                "shortcut": "",
            }
        locations.append(location)
        pendientes.append((location, atajo))

    # Las de fabrica que el usuario no tenia, al final y sin Copy to.
    for nombre in orden_fabrica:
        if nombre in usadas:
            continue
        location = de_fabrica[nombre]
        location["copy_to"] = False
        location["shortcut"] = ""
        locations.append(location)

    # Los atajos se reparten al final y por orden de aparicion: el que el
    # usuario tenia gana, y el que choca se queda sin atajo en vez de dejar dos
    # acciones peleando la misma tecla -con eso Qt no dispara ninguna-.
    tomadas = set()
    for location, atajo in pendientes:
        location["shortcut"] = _assign_shortcut(atajo, tomadas)

    return locations


def _has_legacy(config):
    return "CopyOptions" in config or (
        "LGA_mediaManagerSettings" in config
        and "project_folder_depth" in config["LGA_mediaManagerSettings"]
    )


# ------------------------------------------------------------ API ---
def _parse(ruta):
    """
    Lee el .ini. Devuelve (config, error).

    error es "" si se leyo bien, o el motivo si no. Quien llama TIENE que
    mirarlo antes de guardar: un archivo ilegible se degrada a los valores de
    fabrica, y si despues se guarda encima, la configuracion del usuario se
    pierde de verdad.
    """
    # interpolation=None: por default ConfigParser interpreta el '%' y explota
    # con InterpolationSyntaxError, y no al leer sino al pedir el valor, asi
    # que un try alrededor del read() no lo ataja. Un '%' no es raro: %04d es
    # la notacion de secuencias de Nuke y "100%_final" es un nombre de carpeta
    # normal. Peor: format_ini lo escribe crudo, o sea que la herramienta
    # generaba un .ini que despues no podia leer.
    config = configparser.ConfigParser(interpolation=None)
    if not os.path.isfile(ruta):
        return config, ""

    for encoding in ("utf-8", "latin-1"):
        intento = configparser.ConfigParser(interpolation=None)
        try:
            with open(ruta, "r", encoding=encoding) as archivo:
                intento.read_file(archivo)
            return intento, ""
        except UnicodeDecodeError:
            continue  # el .ini de un Windows viejo puede no ser UTF-8
        except (configparser.Error, OSError) as problema:
            return config, "%s: %s" % (type(problema).__name__, problema)
    return config, "no se pudo decodificar el archivo"


def load_settings(path=None, theme_ids=None):
    """
    Toda la configuracion del Media Manager, ya normalizada.

    Devuelve siempre un dict completo, con las claves shot / locations /
    appearance / load_error. Si el archivo no existe, esta a medias o viene del
    formato viejo, se completa con los valores de fabrica.

    load_error trae el motivo si habia un archivo y no se pudo leer. En ese
    caso lo demas son los defaults, NO la configuracion del usuario, asi que
    quien llama no puede guardar encima sin preguntar.
    """
    ruta = path or get_read_path()
    config, error = _parse(ruta)

    shot = _read_shot(config)
    locations = _read_locations(config)
    # Los saltos para rebasar una ruta vieja salen del shot explicito si lo
    # hay: con [ShotFolder] al lado de un [CopyOptions] sin migrar, usar el
    # depth dejaba los destinos un nivel mas arriba del shot declarado.
    saltos = None
    if shot is not None:
        saltos = _shot_jumps(shot.get("path"))
    if saltos is None:
        saltos = _legacy_depth(config)

    # Cada seccion se resuelve por su cuenta: antes el shot se leia solo si
    # ademas habia [Locations], asi que un .ini a medio editar perdia los dos
    # valores del shot sin decir nada.
    if locations is None:
        locations = _migrate_locations(config, saltos) if _has_legacy(config) \
            else [dict(l) for l in DEFAULT_LOCATIONS]
    if shot is None:
        # Si ya existe [ShotFolder] manda ese, aunque quede un [CopyOptions]
        # viejo al lado: significa que la migracion ya paso.
        shot = ({"enabled": True, "path": "/".join([".."] * saltos) if saltos else "."}
                if _has_legacy(config) else dict(DEFAULT_SHOT))
    # Ojo con la diferencia: la seccion AUSENTE significa "nunca se configuro"
    # y ahi van los defaults; presente y VACIA significa "las borre todas", y
    # devolverselas es deshacerle lo que hizo.
    if locations is None:
        locations = []

    return {
        "shot": shot,
        "locations": locations,
        "appearance": _read_appearance(config, theme_ids),
        "load_error": error,
    }


def format_ini(settings):
    """El texto del .ini, listo para escribir."""
    shot = settings.get("shot") or dict(DEFAULT_SHOT)
    apariencia = settings.get("appearance") or dict(DEFAULT_APPEARANCE)

    # Los valores van SIN comillas. El formato viejo las usaba y la lectura las
    # sigue aceptando, pero escribirlas obligaba a escapar las que trae el
    # propio valor, y sin escapar un nombre entrecomillado perdia un caracter
    # por guardado.
    lineas = [
        "[ShotFolder]",
        "enabled = %s" % ("true" if shot.get("enabled", True) else "false"),
        "path = %s" % _one_line(shot.get("path") or DEFAULT_SHOT["path"]),
        "",
        "[Appearance]",
        "theme = %s" % _one_line(apariencia.get("theme") or DEFAULT_APPEARANCE["theme"]),
        "table_font_size = %d" % _clamp_font_size(apariencia.get("table_font_size")),
        "",
        "[Locations]",
    ]

    # Se reindexa al guardar para que el archivo quede prolijo, aunque la
    # lectura ya no dependa de que la numeracion sea continua.
    posicion = 0
    for location in settings.get("locations") or ():
        nombre = _one_line(location.get("name"))
        ruta = _one_line(location.get("path"))
        if not nombre or not ruta:
            continue   # fila a medias: no se guarda
        posicion += 1
        lineas += [
            "location_%d_name = %s" % (posicion, nombre),
            "location_%d_path = %s" % (posicion, ruta),
            "location_%d_scan = %s" % (posicion, "true" if location.get("scan") else "false"),
            "location_%d_copy_to = %s" % (posicion, "true" if location.get("copy_to") else "false"),
            "location_%d_shortcut = %s" % (posicion, _clean_shortcut(location.get("shortcut"))),
            "",
        ]

    # Con newline final: el .ini semilla esta trackeado y sin el, cada guardado
    # deja un "\ No newline at end of file" en el diff.
    return "\n".join(lineas).rstrip() + "\n"


def save_settings(settings):
    """
    Guarda. Devuelve (True, ruta) o (False, ruta_intentada_o_None).

    No avisa nada: quien llama sabe si esta en una ventana o en un proceso sin
    UI. Tampoco chequea load_error, que es una decision de quien llama.
    """
    ruta = get_write_path()
    if not ruta:
        return False, None
    return write_ini(ruta, format_ini(settings)), ruta


def copy_destinations(locations):
    """Las locations que van al menu Copy to, en orden."""
    return [l for l in (locations or ()) if l.get("copy_to") and l.get("name") and l.get("path")]
