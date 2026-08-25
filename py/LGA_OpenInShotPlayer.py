"""
____________________________________________________________________

  LGA_OpenInShotPlayer v1.01 | Lega

  Abre la media del Read seleccionado en LGA Shot Player.

  v1.01: Suma shortcut multiplataforma desde el menu: Ctrl+Alt+Shift+P
         en Windows y Command+Alt+Shift+P en macOS.
  v1.00: Version inicial: resuelve el registro compartido de LGA, evalua
         la media del frame actual —o el primer frame del Read si aquel no
         existe— y abre el player con semantica de archivo asociado en macOS
         y Windows. Deja trazas de diagnostico en el Script Editor.
____________________________________________________________________
"""

# Los imports de Nuke y Qt son deliberadamente lazy. Los helpers puros sirven
# para pruebas y para diagnosticar una instalacion fuera de Nuke; el codigo de
# UI importa los adapters del pack solo cuando tiene que mostrar un aviso.

import json
import os
import re
import subprocess
import sys
from collections import namedtuple


TOOL_TITLE = "Open in Shot Player"
DEBUG = True
REGISTRY_PROFILES = ("LGA Shot Player", "LGA Player")
MAC_DEFAULT_BUNDLES = (
    "/Applications/LGA Shot Player.app",
    "~/Applications/LGA Shot Player.app",
)
WINDOWS_DEFAULT_INSTALL = r"C:\Portable\LGA\ShotPlayer"
WINDOWS_DEFAULT_EXECUTABLE = "LGA_Player.exe"
MAC_EXECUTABLE = os.path.join("Contents", "MacOS", "LGA Shot Player")

ShotPlayerInstall = namedtuple(
    "ShotPlayerInstall", "system install_path executable bundle_path profile version"
)


def debug_print(*message):
    """Traza acotada al Script Editor, igual que las tools simples del pack."""
    if DEBUG:
        print("[LGA_OpenInShotPlayer]", *message)


def _platform_name(system=None):
    """Normaliza nombres de plataforma para que los helpers sean testeables."""
    value = (system or sys.platform).lower()
    if value.startswith("win"):
        return "windows"
    if value == "darwin" or value.startswith("mac"):
        return "macos"
    return "linux"


def registry_directory(system=None, env=None, home=None):
    """Devuelve la carpeta del registro comun de LGA sin crearla."""
    platform = _platform_name(system)
    environment = os.environ if env is None else env
    user_home = os.path.expanduser("~" if home is None else home)
    if platform == "macos":
        return os.path.join(
            user_home, "Library", "Application Support", "LGA"
        )
    if platform == "windows":
        appdata = environment.get("APPDATA", "").strip()
        return os.path.join(appdata, "LGA") if appdata else ""
    # Linux no es una plataforma publicada del player, pero un registro LGA
    # valido permite que la deteccion sea util en entornos de desarrollo.
    config_home = environment.get("XDG_CONFIG_HOME", "").strip()
    if not config_home:
        config_home = os.path.join(user_home, ".config")
    return os.path.join(config_home, "LGA")


def _read_json(path, read_file=None):
    """Lee un objeto JSON y devuelve {} ante cualquier registro inutilizable."""
    reader = read_file or _read_text_file
    try:
        data = json.loads(reader(path))
    except (OSError, IOError, TypeError, ValueError, UnicodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_text_file(path):
    with open(path, "r", encoding="utf-8") as stream:
        return stream.read()


def _is_dev_tree(path, system=None):
    """Replica el guard del registro: no usar salidas build/deploy como instalacion."""
    if not path:
        return True
    normalized = os.path.normpath(os.path.expanduser(path))
    if _platform_name(system) == "macos" and normalized.lower().endswith(".app"):
        container = os.path.basename(os.path.dirname(normalized))
    else:
        container = os.path.basename(normalized)
    lowered = container.lower()
    return "build" in lowered or "deploy" in lowered


def _default_entry(system, path, exists=os.path.exists, access=os.access):
    platform = _platform_name(system)
    expanded = os.path.abspath(os.path.expanduser(path))
    if not exists(expanded) or _is_dev_tree(expanded, platform):
        return None
    if platform == "macos":
        if not os.path.isdir(expanded):
            return None
        executable = os.path.join(expanded, MAC_EXECUTABLE)
        if not os.path.isfile(executable) or not access(executable, os.X_OK):
            return None
        return ShotPlayerInstall(platform, expanded, executable, expanded, "", "")
    if platform == "windows":
        executable = os.path.join(expanded, WINDOWS_DEFAULT_EXECUTABLE)
        if not os.path.isfile(executable):
            return None
        return ShotPlayerInstall(platform, expanded, executable, "", "", "")
    return None


def _registry_entry(
    data,
    system=None,
    profile="",
    exists=os.path.exists,
    access=os.access,
):
    """Convierte un JSON en una instalacion solo si el binario es usable."""
    platform = _platform_name(system)
    install_path = str(data.get("installPath", "") or "").strip()
    executable_value = str(data.get("executable", "") or "").strip()
    version = str(data.get("version", "") or "").strip()
    if not install_path:
        return None
    install_path = os.path.abspath(os.path.expanduser(install_path))
    if not exists(install_path):
        return None

    if platform == "macos":
        # El contrato actual escribe el bundle `.app`, pero algunos registros
        # históricos dejaron `Contents/MacOS` o el ejecutable como installPath.
        # Normalizar esas formas evita concatenar `Contents/MacOS` dos veces y
        # permite validar siempre el bundle que se le pasa a `open -a`.
        bundle_path = _mac_bundle_path(install_path, executable_value)
        if not bundle_path or _is_dev_tree(bundle_path, platform):
            return None
        if not os.path.isdir(bundle_path):
            return None
        bundle_executable = os.path.join(bundle_path, MAC_EXECUTABLE)
        # `executable` se conserva en el JSON como dato informativo, pero no
        # se sigue a ciegas si quedo apuntando afuera del bundle. La ubicacion
        # instalada y el nombre de binario conocido son la fuente confiable.
        executable = bundle_executable
        if not os.path.isfile(executable) or not access(executable, os.X_OK):
            return None
        return ShotPlayerInstall(platform, bundle_path, executable, bundle_path, profile, version)

    if platform == "windows":
        if os.path.isfile(install_path):
            if os.path.basename(install_path).lower() != WINDOWS_DEFAULT_EXECUTABLE.lower():
                return None
            executable = install_path
            install_dir = os.path.dirname(install_path)
        else:
            if not os.path.isdir(install_path):
                return None
            # Igual que en macOS, el campo puede quedar stale tras mover la app.
            # El instalador define el ejecutable dentro de installPath.
            install_dir = install_path
            executable = os.path.join(install_dir, WINDOWS_DEFAULT_EXECUTABLE)
        if _is_dev_tree(install_dir, platform) or not os.path.isfile(executable):
            return None
        return ShotPlayerInstall(platform, install_dir, executable, "", profile, version)

    # Linux no tiene fallback estandar, pero un ejecutable registrado y vivo
    # es seguro de usar y mantiene util al resolver en pruebas.
    executable = os.path.expandvars(os.path.expanduser(executable_value))
    if not executable:
        return None
    if not os.path.isabs(executable):
        executable = os.path.join(install_path, executable)
    if not exists(executable) or not access(executable, os.X_OK):
        return None
    return ShotPlayerInstall(platform, install_path, executable, "", profile, version)


def resolve_shot_player(
    system=None,
    env=None,
    home=None,
    exists=os.path.exists,
    access=os.access,
    read_file=None,
):
    """Encuentra una instalacion viva del player, primero por registro y luego por fallback."""
    platform = _platform_name(system)
    registry = registry_directory(platform, env=env, home=home)
    for profile in REGISTRY_PROFILES:
        if not registry:
            break
        manifest = os.path.join(registry, profile + ".json")
        entry = _registry_entry(
            _read_json(manifest, read_file),
            platform,
            profile,
            exists=exists,
            access=access,
        )
        if entry:
            return entry

    if platform == "macos":
        for bundle in MAC_DEFAULT_BUNDLES:
            candidate = bundle
            if home is not None and candidate.startswith("~/"):
                candidate = os.path.join(os.path.abspath(os.path.expanduser(home)), candidate[2:])
            entry = _default_entry(platform, candidate, exists=exists, access=access)
            if entry:
                return entry
    elif platform == "windows":
        entry = _default_entry(
            platform,
            WINDOWS_DEFAULT_INSTALL,
            exists=exists,
            access=access,
        )
        if entry:
            return entry
    return None


def _mac_bundle_path(install_path, executable_value=""):
    """Obtiene el `.app` desde las formas de ruta que dejaron los registros."""
    candidates = [install_path, executable_value]
    for candidate in candidates:
        if not candidate:
            continue
        path = os.path.normpath(os.path.expanduser(candidate))
        if path.endswith(".app"):
            return path
        if os.path.basename(path).lower() == "macos":
            contents = os.path.dirname(path)
            bundle = os.path.dirname(contents)
            if bundle.lower().endswith(".app"):
                return bundle
        if os.path.basename(path).lower() == "lga shot player":
            macos_dir = os.path.dirname(path)
            contents = os.path.dirname(macos_dir)
            bundle = os.path.dirname(contents)
            if bundle.lower().endswith(".app"):
                return bundle
    return ""


def _frame_number(nuke_module):
    try:
        return int(nuke_module.frame())
    except (AttributeError, TypeError, ValueError):
        return None


def _expand_frame_tokens(path, frame):
    """Reemplaza tokens de secuencia con el numero del frame actual."""
    if frame is None:
        return path

    def percent(match):
        width = match.group(1)
        return ("%0" + width + "d") % frame if width else str(frame)

    expanded = re.sub(r"%0(\d+)d", percent, path)
    expanded = re.sub(r"%(\d*)d", lambda match: str(frame).zfill(int(match.group(1)) if match.group(1) else 0), expanded)
    expanded = re.sub(r"(#+)", lambda match: str(frame).zfill(len(match.group(1))), expanded)
    return expanded


def _knob_frame_value(knob, frame=None):
    """Evalua un File_Knob en un frame sin mover el timeline de Nuke."""
    if frame is not None:
        try:
            return (knob.evaluate(frame) or "").strip()
        except (TypeError, AttributeError):
            pass
        except Exception as error:
            debug_print("No se pudo evaluar el file knob en frame %s: %s" % (frame, error))
    try:
        return (knob.evaluate() or "").strip()
    except Exception:
        try:
            return (knob.value() or "").strip()
        except Exception:
            return ""


def _read_frame_value(node, knob_name):
    """Lee first/origfirst sin dejar que un knob raro rompa la tool."""
    try:
        knob = node[knob_name]
        return int(knob.value())
    except (KeyError, TypeError, AttributeError, ValueError):
        return None


def media_path_for_read(nuke_module, node, frame=None):
    """Devuelve la media concreta del Read para el frame pedido o el actual."""
    try:
        knob = node["file"]
    except (KeyError, TypeError, AttributeError):
        knob = getattr(node, "knob", lambda _name: None)("file")
    if knob is None:
        return ""

    requested_frame = _frame_number(nuke_module) if frame is None else frame
    raw = _knob_frame_value(knob, requested_frame)
    if not raw:
        return ""

    # filename() aplica los filtros de nombre de Nuke y resuelve expresiones
    # que knob.evaluate() puede dejar atras. evaluate() sigue siendo la primera
    # fuente porque es el valor del frame actual por contrato.
    filtered = raw
    # nuke.filename() describe el estado del frame ACTUAL. Para un fallback a
    # otro frame se usa evaluate(frame), asi no se termina reutilizando por
    # accidente el path que justamente acabamos de comprobar que falta.
    if frame is None:
        try:
            candidate = nuke_module.filename(node)
            if candidate:
                filtered = str(candidate).strip()
        except Exception:
            pass

    filtered = _expand_frame_tokens(filtered, requested_frame)
    filtered = os.path.expandvars(os.path.expanduser(filtered)).strip()
    return os.path.normpath(filtered) if filtered else ""


def existing_media_path_for_read(nuke_module, node, is_file=os.path.isfile):
    """Elige el frame actual si existe; si no, el primero declarado por el Read."""
    current_frame = _frame_number(nuke_module)
    current_path = media_path_for_read(nuke_module, node)
    debug_print("Frame actual:", current_frame, "| path:", current_path or "<vacio>")
    if current_path and is_file(current_path):
        return current_path

    tried_frames = set([current_frame])
    for knob_name in ("first", "origfirst"):
        first_frame = _read_frame_value(node, knob_name)
        if first_frame is None or first_frame in tried_frames:
            continue
        tried_frames.add(first_frame)
        first_path = media_path_for_read(nuke_module, node, frame=first_frame)
        debug_print("Fallback %s=%s | path: %s" % (
            knob_name, first_frame, first_path or "<vacio>"))
        if first_path and is_file(first_path):
            return first_path
    return ""


def launch_shot_player(installation, media_path, popen=subprocess.Popen):
    """Lanza el player sin shell y con la media como archivo asociado."""
    if not installation or not media_path:
        raise ValueError("Missing Shot Player installation or media path")
    if installation.system == "macos":
        command = ["/usr/bin/open", "-a", installation.bundle_path, media_path]
    elif installation.system in ("windows", "linux"):
        command = [installation.executable, media_path]
    else:
        raise OSError("Unsupported platform")
    return popen(command, shell=False)


def _show_warning(title, text):
    """Muestra un QMessageBox con la hoja del tema del pack."""
    try:
        from LGA_QtAdapter_ToolPack import QtWidgets
        import LGA_UI_Style_ToolPack as ui_style

        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow() if app is not None else None
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            title,
            text,
            QtWidgets.QMessageBox.Ok,
            parent,
        )
        box.setStyleSheet(ui_style.theme(None).Style.FORM)
        ui_style.apply_ui_font(box)
        box.exec_()
    except Exception:
        # Nuke es el ultimo recurso si Qt no pudo construir el cartel. No se
        # oculta el aviso ante un host parcialmente inicializado.
        try:
            import nuke

            nuke.message(text)
        except Exception:
            pass


def _selected_read(nuke_module):
    try:
        # Importa la cantidad de Reads, no que el Read sea el unico objeto
        # seleccionado: un Backdrop u otro nodo seleccionado junto al Read no
        # vuelve ambiguo que media hay que abrir.
        selected = list(nuke_module.selectedNodes("Read"))
    except TypeError:
        # Harnesses o APIs antiguas sin el filtro posicional: conservar el
        # mismo contrato filtrando la seleccion completa.
        try:
            selected = [node for node in nuke_module.selectedNodes()
                        if node.Class() == "Read"]
        except Exception:
            selected = []
    except Exception:
        selected = []
    if len(selected) != 1:
        return None
    node = selected[0]
    try:
        return node if node.Class() == "Read" else None
    except Exception:
        return None


def main(nuke_module=None, popen=subprocess.Popen, installer_resolver=None):
    """Entry point del menu TP."""
    if nuke_module is None:
        import nuke as nuke_module

    node = _selected_read(nuke_module)
    if node is None:
        _show_warning(
            TOOL_TITLE,
            "Select exactly one Read node before using Open in Shot Player.",
        )
        return False

    media_path = existing_media_path_for_read(nuke_module, node)
    if not media_path:
        _show_warning(
            TOOL_TITLE,
            "The selected Read does not have media on disk at the current or first frame.",
        )
        return False

    resolver = installer_resolver or resolve_shot_player
    installation = resolver()
    if installation is None:
        _show_warning(
            TOOL_TITLE,
            "LGA Shot Player is not installed. Install it from the LGA Updates card in PipeSync.",
        )
        return False

    debug_print(
        "Shot Player resuelto:", installation.executable,
        "| perfil:", installation.profile or "fallback",
    )
    debug_print("Abriendo media:", media_path)

    try:
        launch_shot_player(installation, media_path, popen=popen)
    except (OSError, IOError, ValueError, subprocess.SubprocessError) as error:
        # El detalle tecnico queda en el log del proceso/host; la UI conserva
        # un mensaje accionable y no expone rutas internas del usuario.
        try:
            print("[OpenInShotPlayer] No se pudo lanzar LGA Shot Player: %s" % error)
        except Exception:
            pass
        _show_warning(
            TOOL_TITLE,
            "LGA Shot Player could not be opened. Verify the installation and try again.",
        )
        return False
    return True


__all__ = [
    "MAC_DEFAULT_BUNDLES",
    "REGISTRY_PROFILES",
    "ShotPlayerInstall",
    "_expand_frame_tokens",
    "existing_media_path_for_read",
    "launch_shot_player",
    "main",
    "media_path_for_read",
    "registry_directory",
    "resolve_shot_player",
]
