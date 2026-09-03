"""
_______________________________________________________________________

  LGA_MediaManager_download v2.46 | Lega

  Descarga desde Wasabi de las filas seleccionadas del Media Manager,
  a traves del CLI de FileManager S3 o, si no esta, del de PipeSync,
  que acepta los mismos flags. Y la deteccion de que apps LGA hay
  instaladas, que decide si el boton Download existe.

  La deteccion es la misma que usa el card de LGA Updates del Tools tab
  de PipeSync, en el mismo orden: primero el registro compartido de LGA
  (`<AppName>.json` en %APPDATA%/LGA o ~/Library/Application Support/
  LGA), despues la clave de desinstalacion de Windows del instalador, y
  por ultimo la carpeta de instalacion por defecto. Es la misma cadena
  que ya sigue LGA_OpenInShotPlayer para el Shot Player.

  El comando se arma como en LGA_NKS_FileManagerS3Launcher de HieroTools
  -exe directo en Windows, `open -na` en macOS-, pero sin --context: sin
  ese flag FileManager S3 usa el contexto por defecto de su edicion, que
  es lo que decide el edition.ini que dejo su instalador. Y sin
  --download-latest: se pide exactamente la version que muestra la fila.

  Sin Qt ni nuke a proposito: los helpers se prueban desde tests/.

  v2.46: PipeSync tambien descarga: mismo comando, otro ejecutable. Se
         va build_open_tools_tab_command.
  v2.45: Version inicial.
_______________________________________________________________________
"""

import json
import os
import re
import subprocess
import sys
from collections import namedtuple

try:
    from LGA_MediaManager_logging import debug_print
except ImportError:  # pragma: no cover - solo fuera del pack

    def debug_print(*message, level="info"):
        print("[LGA_MediaManager_download]", *message)


# Una app LGA que se puede buscar: sus perfiles del registro compartido, la
# clave de desinstalacion de Inno Setup, y sus carpetas por defecto. Los
# valores salen de UpdateCatalog.cpp de PipeSync, que es la fuente de verdad
# de donde instala cada instalador, mas lo que el catalogo no lista y si
# existe: el perfil y el bundle de la edicion Client de macOS (main.cpp y
# create_dmg.sh de FileManagerS3) y el nombre viejo del bundle que todavia
# contempla el launcher de HieroTools.
AppSpec = namedtuple(
    "AppSpec",
    "name profiles uninstall_key windows_defaults windows_executable mac_defaults",
)

# Una instalacion viva. `executable` es el .exe en Windows y el bundle .app en
# macOS, que es lo que recibe `open -na`. `source` dice quien la ubico:
# registry, uninstall o default.
LgaApp = namedtuple("LgaApp", "system name install_path executable version source")

# Con que se descarga. `kind` es "filemanagers3" o "pipesync": las dos apps
# entienden el mismo CLI (--download / --download-file), asi que el comando
# se arma igual y solo cambia el ejecutable.
DownloadTarget = namedtuple("DownloadTarget", "kind app")

# Lo que se le manda al CLI: carpetas de secuencias (--download), archivos
# sueltos (--download-file) y lo que se dejo afuera, con el motivo.
DownloadPlan = namedtuple("DownloadPlan", "folders files skipped")

FILEMANAGERS3 = AppSpec(
    name="FileManager S3",
    # En Windows las dos ediciones son el mismo exe y se registran como
    # FileManagerS3; el perfil Client existe solo en el bundle de macOS.
    profiles=("FileManagerS3", "FileManagerS3Client"),
    # `AppId=FileManagerS3` de su instalador.bat; Inno le agrega `_is1`.
    uninstall_key="FileManagerS3_is1",
    windows_defaults=(r"C:\Portable\LGA\FileManagerS3",),
    windows_executable="FileManagerS3.exe",
    mac_defaults=(
        "/Applications/LGA FileManager S3.app",
        "~/Applications/LGA FileManager S3.app",
        "/Applications/LGA FileManager S3 Client.app",
        "~/Applications/LGA FileManager S3 Client.app",
        # El nombre viejo del bundle, que HieroTools todavia contempla.
        "/Applications/FileManagerS3.app",
    ),
)

PIPESYNC_STUDIO = AppSpec(
    name="PipeSync",
    # Solo la edicion studio: la Client se registra como PipeSyncClient y no
    # cuenta, porque el Download es para maquinas del estudio.
    profiles=("PipeSync",),
    # `AppId=%APP_DISPLAY_NAME%` de su instalador.bat, o sea "PipeSync".
    uninstall_key="PipeSync_is1",
    windows_defaults=(r"C:\Portable\LGA\PipeSync",),
    windows_executable="PipeSync.exe",
    mac_defaults=(
        "/Applications/LGA PipeSync.app",
        "~/Applications/LGA PipeSync.app",
    ),
)

# Nombre del binario adentro del bundle, por si el registro apunta a el.
_MAC_CONTENTS = os.path.join("Contents", "MacOS")


# ---------------------------------------------------------------------------
#                         Plataforma y registro LGA
# ---------------------------------------------------------------------------
def _platform_name(system=None):
    """Normaliza el nombre de plataforma para que los helpers sean testeables."""
    value = (system or sys.platform).lower()
    if value.startswith("win"):
        return "windows"
    if value == "darwin" or value.startswith("mac"):
        return "macos"
    return "linux"


def registry_directory(system=None, env=None, home=None):
    """La carpeta del registro compartido de LGA, sin crearla."""
    platform = _platform_name(system)
    environment = os.environ if env is None else env
    user_home = os.path.expanduser("~" if home is None else home)
    if platform == "macos":
        return os.path.join(user_home, "Library", "Application Support", "LGA")
    if platform == "windows":
        appdata = environment.get("APPDATA", "").strip()
        return os.path.join(appdata, "LGA") if appdata else ""
    config_home = environment.get("XDG_CONFIG_HOME", "").strip()
    if not config_home:
        config_home = os.path.join(user_home, ".config")
    return os.path.join(config_home, "LGA")


def _read_json(path):
    """Un objeto JSON, o {} ante cualquier registro inutilizable."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, IOError, TypeError, ValueError, UnicodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _is_dev_tree(path, platform):
    """
    Replica el guard del registro: una salida build/deploy no es una
    instalacion. Se mira SOLO la carpeta que contiene la app, nunca la ruta
    entera, para no voltear una instalacion legitima en D:/Builds/Apps.
    """
    if not path:
        return True
    normalized = os.path.normpath(os.path.expanduser(path))
    if platform == "macos" and normalized.lower().endswith(".app"):
        container = os.path.basename(os.path.dirname(normalized))
    else:
        container = os.path.basename(normalized)
    lowered = container.lower()
    return "build" in lowered or "deploy" in lowered


def _install_from_folder(spec, platform, folder, version, source, executable_hint=""):
    """
    Convierte una carpeta candidata en una LgaApp, o None si no hay una app
    viva adentro. En Windows exige el .exe conocido de la app -el probe de
    PipeSync acepta cualquier .exe porque solo informa; aca hay que
    lanzarlo-, y si el registro nombro otro ejecutable dentro de la misma
    carpeta se respeta. En macOS la carpeta ES el bundle y tiene que tener
    Contents/MacOS.

    El guard de arbol build/deploy se aplica a las TRES fuentes, y no solo
    al registro compartido como en PipeSync: es a proposito, porque de aca
    sale un binario que se ejecuta y un build a medias es peor que ningun
    boton.
    """
    if not folder:
        return None
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isdir(folder) or _is_dev_tree(folder, platform):
        return None

    if platform == "macos":
        if not folder.lower().endswith(".app"):
            return None
        if not os.path.isdir(os.path.join(folder, _MAC_CONTENTS)):
            return None
        return LgaApp(platform, spec.name, folder, folder, version, source)

    if platform == "windows":
        executable = os.path.join(folder, spec.windows_executable)
        hint = os.path.abspath(executable_hint) if executable_hint else ""
        if (
            hint
            and os.path.dirname(hint).lower() == folder.lower()
            and os.path.isfile(hint)
        ):
            executable = hint
        if not os.path.isfile(executable):
            return None
        return LgaApp(platform, spec.name, folder, executable, version, source)

    # Linux no es plataforma publicada de estas apps; solo sirve un
    # ejecutable registrado que exista.
    if executable_hint and os.access(executable_hint, os.X_OK):
        return LgaApp(platform, spec.name, folder, executable_hint, version, source)
    return None


def _registry_entry(spec, platform, data, source="registry"):
    """La instalacion que describe un `<AppName>.json`, si sigue viva."""
    install_path = str(data.get("installPath", "") or "").strip()
    executable = str(data.get("executable", "") or "").strip()
    version = str(data.get("version", "") or "").strip()
    if not install_path:
        return None
    install_path = os.path.normpath(os.path.expanduser(install_path))
    if platform == "macos" and not install_path.lower().endswith(".app"):
        # Registros viejos dejaron Contents/MacOS o el binario como ruta.
        for candidato in (install_path, executable):
            while candidato and candidato != os.path.dirname(candidato):
                if candidato.lower().endswith(".app"):
                    install_path = candidato
                    break
                candidato = os.path.dirname(candidato)
            if install_path.lower().endswith(".app"):
                break
    elif platform == "windows" and os.path.isfile(install_path):
        # Algun registro puede apuntar al .exe en vez de a su carpeta.
        executable = executable or install_path
        install_path = os.path.dirname(install_path)
    return _install_from_folder(
        spec, platform, install_path, version, source, executable_hint=executable
    )


# ---------------------------------------------------------------------------
#                    Registro de desinstalacion de Windows
# ---------------------------------------------------------------------------
_UNINSTALL_ROOTS = (
    ("HKEY_CURRENT_USER", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (
        "HKEY_LOCAL_MACHINE",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
)


def read_windows_uninstall_entry(uninstall_key):
    """
    (DisplayVersion, InstallLocation) de la clave de desinstalacion de
    Inno Setup, o None si no esta. Lo escribe el INSTALADOR y no la app, asi
    que es la unica fuente cuando la app nunca se abrio y no se registro.

    Se miran las tres raices donde Inno puede haber escrito, la del usuario
    primero. Una clave sin DisplayVersion no sirve y se sigue buscando.
    """
    if not uninstall_key:
        return None
    try:
        import winreg
    except ImportError:
        return None

    hives = {
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    }
    for hive_name, base in _UNINSTALL_ROOTS:
        try:
            with winreg.OpenKey(hives[hive_name], base + "\\" + uninstall_key) as key:
                version = _registry_string(winreg, key, "DisplayVersion")
                if not version:
                    continue
                location = _registry_string(winreg, key, "InstallLocation")
                # Inno la escribe con la barra final.
                return version, os.path.normpath(location) if location else ""
        except OSError:
            continue
    return None


def _registry_string(winreg, key, name):
    try:
        value, _tipo = winreg.QueryValueEx(key, name)
    except OSError:
        return ""
    return str(value or "").strip()


# ---------------------------------------------------------------------------
#                              Resolucion
# ---------------------------------------------------------------------------
def resolve_lga_app(
    spec,
    system=None,
    env=None,
    home=None,
    read_uninstall=read_windows_uninstall_entry,
    default_paths=None,
):
    """
    Una instalacion viva de la app, o None. Las tres fuentes en el orden del
    probe de PipeSync: registro compartido, clave de desinstalacion (solo
    Windows) y carpetas por defecto. Cada una tiene que apuntar a una
    carpeta con la app adentro: una clave huerfana o un JSON viejo no
    cuentan.

    `default_paths` reemplaza las carpetas por defecto de la spec. Es para
    las pruebas, que corren en una maquina donde la app SI esta instalada
    en su lugar de siempre.
    """
    platform = _platform_name(system)
    registry = registry_directory(platform, env=env, home=home)
    if registry:
        for profile in spec.profiles:
            manifest = os.path.join(registry, profile + ".json")
            entry = _registry_entry(spec, platform, _read_json(manifest))
            if entry:
                return entry

    if platform == "windows":
        try:
            found = read_uninstall(spec.uninstall_key)
        except Exception as error:
            debug_print(
                "No se pudo leer la clave de desinstalacion de %s: %s"
                % (spec.name, error),
                level="warning",
            )
            found = None
        if found:
            version, location = found
            entry = _install_from_folder(spec, platform, location, version, "uninstall")
            if entry:
                return entry

    if default_paths is not None:
        candidates = tuple(default_paths)
    elif platform == "windows":
        candidates = spec.windows_defaults
    elif platform == "macos":
        candidates = spec.mac_defaults
    else:
        candidates = ()
    for candidate in candidates:
        if home is not None and candidate.startswith("~/"):
            candidate = os.path.join(os.path.expanduser(home), candidate[2:])
        entry = _install_from_folder(spec, platform, candidate, "", "default")
        if entry:
            return entry
    return None


# La deteccion corre al abrir el Media Manager por primera vez en la sesion
# y se cachea. Pero SOLO se recuerda el resultado bueno: si no se encontro
# FileManager S3, la proxima apertura vuelve a mirar, porque el camino
# tipico es "el boton dice que falta, el usuario lo instala desde PipeSync y
# reabre" -y un cache ciego lo dejaba mandando a instalar hasta reiniciar
# Nuke-. Volver a mirar cuesta un JSON, una clave y un par de isfile().
_cached_target = None
_cache_resolved = False


def resolve_download_target(force=False, **kwargs):
    """
    Con que se descarga, o None si no hay boton que mostrar.

    Primero FileManager S3 y, si no esta, PipeSync studio: los dos traen el
    mismo CLI de descarga. Sin ninguna de las dos no hay boton.
    """
    global _cached_target, _cache_resolved
    cache_es_definitivo = (
        _cached_target is not None and _cached_target.kind == "filemanagers3"
    )
    if _cache_resolved and cache_es_definitivo and not force and not kwargs:
        return _cached_target

    target = None
    app = resolve_lga_app(FILEMANAGERS3, **kwargs)
    if app is not None:
        target = DownloadTarget("filemanagers3", app)
        debug_print(
            "FileManager S3 encontrado por %s: %s (v%s)"
            % (app.source, app.executable, app.version or "?")
        )
    else:
        debug_print("FileManager S3 no esta instalado; se busca PipeSync studio")
        app = resolve_lga_app(PIPESYNC_STUDIO, **kwargs)
        if app is not None:
            target = DownloadTarget("pipesync", app)
            debug_print(
                "PipeSync studio encontrado por %s: %s (v%s)"
                % (app.source, app.executable, app.version or "?")
            )
        else:
            debug_print("PipeSync studio tampoco esta: sin boton Download")

    if not kwargs:
        _cached_target = target
        _cache_resolved = True
    return target


def reset_cache():
    """Olvida la deteccion. Para las pruebas."""
    global _cached_target, _cache_resolved
    _cached_target = None
    _cache_resolved = False


# ---------------------------------------------------------------------------
#                                El plan
# ---------------------------------------------------------------------------
def path_has_vfx_root(path):
    """True si alguna parte de la ruta empieza con 'VFX-', que exige el CLI."""
    parts = os.path.normpath(path).replace("\\", "/").split("/")
    return any(p.upper().startswith("VFX-") for p in parts)


# Un token de frame: uno o mas '#', o un `%d` / `%04d` de printf.
_SEQ_TOKEN_RE = re.compile(r"#+|%0?\d*d")


def _dedupe_preserve_order(paths):
    seen = set()
    out = []
    for p in paths:
        key = os.path.normpath(str(p)).replace("\\", "/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def plan_download(row_paths):
    """
    Reparte las rutas de la tabla entre lo que va a --download y lo que va
    a --download-file, igual que Download Clip en Hiero: una secuencia
    (`nombre.####.exr[1001-1129]`) se pide por su CARPETA, y un archivo
    suelto por su ruta. Lo que no tiene raiz VFX- se deja afuera, porque
    FileManager S3 lo rechazaria, y se devuelve en `skipped` con el motivo.
    """
    folders = []
    files = []
    skipped = []
    for raw in row_paths:
        ruta = str(raw or "").strip()
        if not ruta:
            continue
        ruta = os.path.normpath(ruta)
        if not path_has_vfx_root(ruta):
            skipped.append((ruta, "no VFX- project root"))
            continue
        # La tabla escribe las secuencias con '#', pero un Read offline con
        # `%d` pelado -sin padding- llega con el token tal cual: tambien es
        # secuencia, y pedirlo como archivo daria una ruta que no existe.
        if _SEQ_TOKEN_RE.search(os.path.basename(ruta)):
            folders.append(os.path.dirname(ruta))
        else:
            files.append(ruta)
    return DownloadPlan(
        _dedupe_preserve_order(folders), _dedupe_preserve_order(files), skipped
    )


def _app_command(app, cli_args):
    """El comando para lanzar una app LGA con argumentos, sin shell."""
    if app.system == "macos":
        return ["open", "-na", app.executable, "--args"] + list(cli_args)
    return [app.executable] + list(cli_args)


def build_download_command(app, folders, files):
    """
    El comando de descarga, o None si no hay nada que pedir. Sirve para
    FileManager S3 y para PipeSync, que aceptan los mismos flags. Todo va en
    una sola invocacion; sin --context, para que mande la edicion instalada.
    """
    cli_args = []
    if folders:
        cli_args.append("--download")
        cli_args.extend(folders)
    if files:
        cli_args.append("--download-file")
        cli_args.extend(files)
    if not cli_args:
        return None
    return _app_command(app, cli_args)


def launch(command, popen=subprocess.Popen):
    """Lanza el comando sin shell y sin esperar. Devuelve el proceso."""
    debug_print("Ejecutando: %s" % " ".join(command))
    return popen(command, shell=False)


__all__ = [
    "AppSpec",
    "DownloadPlan",
    "DownloadTarget",
    "FILEMANAGERS3",
    "LgaApp",
    "PIPESYNC_STUDIO",
    "build_download_command",
    "launch",
    "path_has_vfx_root",
    "plan_download",
    "read_windows_uninstall_entry",
    "registry_directory",
    "reset_cache",
    "resolve_download_target",
    "resolve_lga_app",
]
