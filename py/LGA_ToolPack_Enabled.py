"""
____________________________________________________________________

  LGA_ToolPack_Enabled v1.03 | Lega

  Resuelve que herramientas del pack estan habilitadas.

  La config del usuario vive FUERA del pack, en la carpeta de datos
  del sistema, porque la carpeta del pack se borra en cada update.

  v1.03: `SIBLING_BACKUP_DIRS` es igual en los tres packs: la version
         derivada perdia `LGA_ToolPack_backup` y no rescataba de ahi.
  v1.02: Se desactiva la interpolacion de configparser: un `%` en un
         ini editado a mano dejaba a Nuke sin el menu entero, y se
         blinda tambien la lectura de claves.
  v1.01: El manifiesto ilegible ya no borra la config del usuario.
         Un solo parser para las claves, seccion [DEFAULT] ignorada,
         temporal unico por proceso y fallback propio sin %APPDATA%.
  v1.00: Version inicial. Migra el estado a la carpeta de usuario,
         guarda solo overrides y deja de depender del ini del pack.
____________________________________________________________________
"""

import os
import platform
import tempfile
import configparser


# Nombre del ini que viaja DENTRO del pack. Es la lista canonica de tools con
# su valor de fabrica: un manifiesto, no estado del usuario. El instalador lo
# pisa en cada update y esta bien que lo haga.
DEFAULT_INI_NAME = "Enabled.default.ini"

# Config del usuario: carpeta de datos del sistema, al lado de lo que ya
# escriben Write_Focus, ColorSpace_Favs y compania.
USER_DIR_PARTS = ("LGA", "ToolPack")
USER_INI_NAME = "Enabled.ini"

# Ubicacion historica: un ini suelto en la carpeta .nuke, que es lo que
# documentaba el PDF de instalacion viejo. Se usa para SEMBRAR la config del
# usuario la primera vez, y no se borra ni se renombra nunca: si alguien
# revierte a una version anterior del pack, ese codigo lo vuelve a leer.
LEGACY_INI_NAME = "_LGA_ToolPack_Enabled.ini"

# Legacies de los packs hermanos. Se miran al sembrar porque hay tools que
# cambiaron de pack: quien apago `CopyCat_Cleaner` cuando vivia en ToolPack
# tiene que seguir viendolo apagado ahora que vive en ToolPack-B.
SIBLING_LEGACY_INI_NAMES = (
    "_LGA_ToolPack_Enabled.ini",
    "_LGA_ToolPack-B_Enabled.ini",
    "_LGA_LayoutToolPack_Enabled.ini",
)

# Carpetas `<Pack>_backup` que deja el instalador. Se miran todas, no solo la
# propia, por la misma razon que los legacies hermanos. Esta tupla es
# IDENTICA en los tres packs: quien manda es el nombre del ini que hay
# adentro, no la carpeta. No renombrarla por pack.
SIBLING_BACKUP_DIRS = (
    "LGA_ToolPack_backup",
    "LGA_ToolPack-B_backup",
    "LGA_ToolPack-Layout_backup",
)

# Si no hay carpeta de datos del sistema, la config va aca adentro del .nuke.
# Es un archivo PROPIO y no el legacy: escribir el legacy en formato
# "solo overrides" le borraria al usuario los comentarios y las claves de
# otros packs que ese archivo pueda tener.
FALLBACK_DIR_NAME = "LGA_Settings"

SECTION = "Tools"
META_SECTION = "Meta"
SCHEMA_VERSION = "1"

_TRUE_VALUES = ("1", "true", "yes", "on")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def _warn(message):
    """Avisa por el canal de Nuke si existe, y si no por stdout."""
    try:
        import nuke

        nuke.warning(message)
    except Exception:
        print(message)


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------


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

    No se usa `expanduser("~")` porque el instalador acepta un `.nuke` en
    cualquier ruta (`-NukeDir`), y ahi el home del usuario no tiene nada.
    El pack siempre vive en `<NukeDir>/LGA_ToolPack`, asi que el padre de
    ROOT_DIR es el dato correcto.
    """
    return os.path.dirname(ROOT_DIR)


def get_default_path():
    """El manifiesto que viaja dentro del pack."""
    return os.path.join(ROOT_DIR, DEFAULT_INI_NAME)


def get_user_path(create_dir=False):
    """Config del usuario. Si no hay carpeta de datos, cae dentro del .nuke."""
    base = get_user_config_dir()
    if base:
        user_dir = os.path.join(base, *USER_DIR_PARTS)
    else:
        user_dir = os.path.join(get_nuke_dir(), FALLBACK_DIR_NAME, USER_DIR_PARTS[-1])

    if create_dir:
        try:
            os.makedirs(user_dir, exist_ok=True)
        except OSError as error:
            _warn("LGA ToolPack: no se pudo crear %s (%s)" % (user_dir, error))
            return None
    return os.path.join(user_dir, USER_INI_NAME)


def _legacy_dirs():
    """Carpetas donde puede haber un ini historico, sin repetir."""
    dirs = []
    for candidate in (
        os.path.join(os.path.expanduser("~"), ".nuke"),
        get_nuke_dir(),
    ):
        if candidate and candidate not in dirs:
            dirs.append(candidate)
    return dirs


def get_legacy_paths():
    """Inis historicos de ESTE pack, del mas generico al mas especifico."""
    return [os.path.join(d, LEGACY_INI_NAME) for d in _legacy_dirs()]


def get_sibling_legacy_paths():
    """Inis historicos de los packs hermanos, para rescatar tools migradas."""
    paths = []
    for directory in _legacy_dirs():
        for name in SIBLING_LEGACY_INI_NAMES:
            if name != LEGACY_INI_NAME:
                paths.append(os.path.join(directory, name))
    return paths


def get_backup_paths():
    """Inis que quedaron dentro de las carpetas `<Pack>_backup`.

    El instalador renombra la carpeta vieja y no la borra: recien la descarta
    al empezar la instalacion SIGUIENTE. Asi que en el primer arranque despues
    de un update todavia esta ahi, con la config que el usuario haya editado
    adentro del pack.

    OJO: dos instalaciones seguidas sin abrir Nuke en el medio se llevan ese
    backup puesto. Por eso el rescate es un extra y no la via principal: la
    via principal es el legacy de `.nuke`, que no lo toca nadie.

    Los devuelve de menor a mayor confianza, con el ini propio del pack
    ultimo: si el mismo switch aparece en el backup de un hermano y en el
    propio, manda el propio.
    """
    nuke_dir = get_nuke_dir()
    ajenos = []
    propios = []
    for backup_dir in SIBLING_BACKUP_DIRS:
        for ini_name in SIBLING_LEGACY_INI_NAMES:
            destino = propios if ini_name == LEGACY_INI_NAME else ajenos
            destino.append(os.path.join(nuke_dir, backup_dir, ini_name))
    return ajenos + propios


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------


def _read_ini(path, warn_if_unreadable=False):
    """Lee un ini y devuelve {clave: bool}. Nunca levanta."""
    if not path or not os.path.isfile(path):
        return {}

    # `interpolation=None` porque `cfg.items()` interpola: un `%` suelto en
    # cualquier valor levanta InterpolationSyntaxError FUERA del try de abajo,
    # y como `is_enabled()` corre al armar el menu, eso dejaria a Nuke sin el
    # menu entero. Los legacies de `.nuke` son archivos editados a mano.
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str  # respeta mayusculas en las claves
    try:
        # utf-8-sig y no utf-8: un ini editado a mano y guardado con BOM
        # rompe el parser con MissingSectionHeaderError.
        cfg.read(path, encoding="utf-8-sig")
    except Exception as error:
        if warn_if_unreadable:
            # Un archivo que existe y no se puede leer NO puede quedar
            # silenciado: es indistinguible de "no configure nada" y el
            # usuario arranca con todo habilitado sin enterarse.
            _warn("LGA ToolPack: no se pudo leer %s (%s)" % (path, error))
        return {}

    try:
        if not cfg.has_section(SECTION):
            return {}

        # `cfg.items(SECTION)` arrastra tambien las claves de `[DEFAULT]`, que
        # no son tools. Se filtran para que una seccion suelta no invente
        # switches.
        heredadas = set(cfg.defaults())
        flags = {}
        for key, value in cfg.items(SECTION):
            if key in heredadas:
                continue
            flags[key] = str(value).strip().lower() in _TRUE_VALUES
        return flags
    except Exception as error:
        # El contrato de esta funcion es no levantar nunca: la llama el menu
        # al armarse, y una excepcion aca deja a Nuke sin menu.
        if warn_if_unreadable:
            _warn("LGA ToolPack: no se pudo interpretar %s (%s)" % (path, error))
        return {}


def read_defaults():
    """Valores de fabrica del pack. Es la lista canonica de tools.

    Se avisa si el archivo esta y no se puede leer: un manifiesto vacio por
    error es indistinguible de un manifiesto sin tools, y de ese equivoco
    salen todos los caminos en los que se pierde la config del usuario.
    """
    return _read_ini(get_default_path(), warn_if_unreadable=True)


def read_default_groups():
    """Agrupa las claves del manifiesto por los comentarios `; === X ===`.

    Devuelve [(titulo, [claves...])]. Sirve para que el panel dibuje los
    checkboxes con la misma division que el menu.

    Las claves SIEMPRE salen de `read_defaults()`: el texto solo aporta orden
    y titulos. Tener dos parsers que pueden discrepar es justamente lo que
    permitiria que el panel dibuje tools que el resto del modulo no conoce.
    """
    defaults = read_defaults()
    if not defaults:
        return []

    groups = []
    current_title = ""
    current_keys = []
    vistas = set()

    try:
        with open(get_default_path(), "r", encoding="utf-8-sig") as handle:
            lines = handle.readlines()
    except OSError:
        return [("", sorted(defaults.keys()))]

    for raw in lines:
        line = raw.strip()
        if line.startswith(";"):
            marker = line.lstrip(";").strip()
            if marker.startswith("===") and marker.endswith("==="):
                if current_keys:
                    groups.append((current_title, current_keys))
                current_title = marker.strip("=").strip()
                current_keys = []
            continue
        if not line or line.startswith("["):
            continue
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in defaults and key not in vistas:
                current_keys.append(key)
                vistas.add(key)

    if current_keys:
        groups.append((current_title, current_keys))

    # Red de seguridad: si el texto no cubre alguna clave del manifiesto, esa
    # tool tiene que aparecer igual en el panel.
    sueltas = [k for k in sorted(defaults) if k not in vistas]
    if sueltas:
        groups.append(("OTHER", sueltas))
    return groups


_TOOL_FLAGS = None


def load_flags(force=False):
    """Estado efectivo de las tools: manifiesto del pack + config del usuario.

    El ini historico NO se lee aca. Es fuente de SIEMBRA (ver `ensure_user_ini`),
    no una capa viva, y la diferencia importa: como la config del usuario guarda
    solo overrides, una tool que el usuario vuelve a encender desaparece de ese
    archivo por ser igual al default. Si el legacy siguiera leyendose por debajo
    la volveria a apagar en el arranque siguiente, y el cambio hecho desde el
    panel se perderia en silencio.

    Si una clave no aparece en ninguna capa, la tool queda habilitada.
    """
    global _TOOL_FLAGS
    if _TOOL_FLAGS is not None and not force:
        return _TOOL_FLAGS

    flags = read_defaults()

    user_path = get_user_path()
    if user_path and os.path.isfile(user_path):
        flags.update(_read_ini(user_path, warn_if_unreadable=True))
    else:
        # Sin config de usuario —sembrado fallido, carpeta sin permiso de
        # escritura— el legacy es lo unico que tiene el usuario. Leerlo aca
        # es lo que evita que un fallo de escritura le encienda todo.
        for legacy in get_legacy_paths():
            flags.update(_read_ini(legacy, warn_if_unreadable=True))

    _TOOL_FLAGS = flags
    return _TOOL_FLAGS


def is_enabled(key):
    """Si la clave no esta en ninguna capa => habilitada."""
    return load_flags().get(key, True)


# --------------------------------------------------------------------------
# Escritura
# --------------------------------------------------------------------------


def write_user_overrides(flags):
    """Guarda SOLO lo que difiere del manifiesto. Devuelve True si pudo.

    Guardar el archivo completo lo fosiliza: entre versiones se agregan y se
    borran tools, y el ini del usuario termina con claves muertas y sin las
    nuevas. Guardando solo los overrides el archivo queda en pocas lineas,
    las tools nuevas aparecen habilitadas solas y resetear es borrarlo.
    """
    defaults = read_defaults()
    if not defaults:
        # Sin manifiesto no hay contra que comparar: TODO daria "igual al
        # default" y el archivo del usuario quedaria vacio, borrandole la
        # configuracion justo cuando cree que la esta guardando.
        _warn(
            "LGA ToolPack: no se pudo leer %s, no se guarda la configuracion "
            "para no perder la existente." % get_default_path()
        )
        return False

    path = get_user_path(create_dir=True)
    if not path:
        return False

    overrides = dict(
        (key, value)
        for key, value in flags.items()
        if key in defaults and defaults[key] != value
    )

    lines = [
        "; LGA ToolPack - Tools desactivadas por el usuario.",
        ";",
        "; Solo se listan las que difieren del valor de fabrica. Lo que no",
        "; figura aca queda como viene el pack. Borrar este archivo puede",
        "; no resetear: si quedo un ini viejo en .nuke, se vuelve a migrar.",
        "; Para volver a los valores de fabrica: boton Reset y despues Save,",
        "; en el menu TP > Enable Tools.",
        "",
        "[%s]" % META_SECTION,
        "schema = %s" % SCHEMA_VERSION,
        "",
        "[%s]" % SECTION,
    ]
    for key in sorted(overrides):
        lines.append("%s = %s" % (key, "True" if overrides[key] else "False"))
    lines.append("")

    # Escritura atomica: si Nuke se cae a mitad de camino, el archivo viejo
    # sigue entero en vez de quedar truncado. El temporal lleva nombre unico
    # porque puede haber dos Nukes guardando a la vez; `os.replace` es atomico
    # pero el temporal compartido no lo seria.
    handle_fd = None
    temp_path = None
    try:
        handle_fd, temp_path = tempfile.mkstemp(
            dir=os.path.dirname(path), prefix=".Enabled-", suffix=".tmp"
        )
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            handle_fd = None  # lo cierra el context manager
            handle.write("\n".join(lines))
        os.replace(temp_path, path)
        temp_path = None
    except OSError as error:
        _warn("LGA ToolPack: no se pudo guardar %s (%s)" % (path, error))
        if handle_fd is not None:
            try:
                os.close(handle_fd)
            except OSError:
                pass
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False

    global _TOOL_FLAGS
    _TOOL_FLAGS = None
    return True


def ensure_user_ini():
    """Siembra la config del usuario UNA sola vez, si todavia no existe.

    Junta todo lo que el usuario pueda haber configurado antes de que esta
    ubicacion existiera, y lo deja escrito como overrides. A partir de ahi el
    archivo es suyo y ningun update lo toca.

    De menor a mayor prioridad:
      1. legacies de los packs hermanos  (tools que cambiaron de pack)
      2. inis dentro de las `<Pack>_backup` (editados adentro del pack)
      3. los legacies propios de `.nuke`   (lo que documentaba el PDF)
    """
    path = get_user_path()
    if not path or os.path.isfile(path):
        return False

    defaults = read_defaults()
    if not defaults:
        # Sin manifiesto no hay contra que comparar: no sembrar nada antes
        # que sembrar un archivo que apague tools por error.
        return False

    merged = dict(defaults)

    # De los archivos ajenos solo se toman las claves que ESTE pack reconoce;
    # el resto es de otro pack y lo levanta el sembrado de ese otro pack.
    for foreign in get_sibling_legacy_paths() + get_backup_paths():
        for key, value in _read_ini(foreign).items():
            if key in defaults:
                merged[key] = value

    for legacy in get_legacy_paths():
        merged.update(_read_ini(legacy))

    # Se escribe siempre, aunque no haya overrides: el archivo vacio es lo que
    # marca "ya sembrado" y evita repetir el rescate en cada arranque.
    return write_user_overrides(merged)
