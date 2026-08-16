"""
_______________________________________

  LGA_MediaManager_config v2.25 | Lega
  Donde vive la configuracion del Media Manager

  v2.25: Modulo nuevo. El .ini pasa a la carpeta de datos del
         usuario; el que viaja dentro del pack queda solo como
         semilla de la primera instalacion.
_______________________________________

"""

import os
import platform
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
