"""
____________________________________________________________________________________

  LGA_Write_Focus v1.60 | Lega
  Script para buscar, enfocar, centrar y hacer zoom a un nodo con nombre definido
  en el archivo de configuracion. Por defecto es Write_Pub.
____________________________________________________________________________________
"""

import nuke
import time
import os
import configparser
import platform

# Variable global para activar o desactivar los prints de depuracion
DEBUG = False  # Cambiar a True para ver los mensajes detallados


# Funcion para imprimir mensajes de depuracion
def debug_print(*message):
    if DEBUG:
        print(*message)


def normalize_name(name):
    """
    Normaliza un nombre reemplazando espacios por guiones bajos.
    """
    return name.replace(" ", "_") if name else ""


def find_write_node_flexible(target_name):
    """
    Busca un nodo Write de forma flexible:
    1. Busqueda exacta con nombre normalizado
    2. Busqueda parcial si no hay match exacto
    Excluye nodos Write que esten actualmente seleccionados.
    Devuelve el primer nodo encontrado o None.
    """
    if not target_name:
        return None

    normalized_target = normalize_name(target_name)
    debug_print(f"Buscando nodo: '{target_name}' (normalizado: '{normalized_target}')")

    # Obtener nodos Write actualmente seleccionados para excluirlos
    selected_writes = [n for n in nuke.selectedNodes() if n.Class() == "Write"]
    debug_print(
        f"Nodos Write seleccionados a excluir: {[n.name() for n in selected_writes]}"
    )

    # Obtener todos los nodos Write del script (excluyendo los seleccionados)
    all_writes = [
        n for n in nuke.allNodes() if n.Class() == "Write" and n not in selected_writes
    ]
    debug_print(
        f"Total nodos Write encontrados (excluyendo seleccionados): {len(all_writes)}"
    )

    # 1. Busqueda exacta con nombres normalizados
    for node in all_writes:
        normalized_node_name = normalize_name(node.name())
        if normalized_node_name == normalized_target:
            debug_print(
                f"Match exacto encontrado: '{node.name()}' -> '{normalized_node_name}'"
            )
            return node

    # 2. Busqueda parcial: el nombre del nodo contiene el target normalizado
    partial_matches = []
    for node in all_writes:
        normalized_node_name = normalize_name(node.name())
        if normalized_target in normalized_node_name:
            partial_matches.append(node)
            debug_print(
                f"Match parcial encontrado: '{node.name()}' -> '{normalized_node_name}'"
            )

    # Devolver el primer match parcial si existe
    if partial_matches:
        debug_print(f"Usando match parcial: '{partial_matches[0].name()}'")
        return partial_matches[0]

    debug_print(
        f"No se encontro ningun nodo Write que coincida con '{target_name}' (excluyendo seleccionados)"
    )
    return None


def get_user_config_dir():
    """
    Obtiene el directorio de configuracion del usuario segun el sistema operativo.
    Windows: %APPDATA%
    Mac: ~/Library/Application Support
    """
    system = platform.system()
    if system == "Windows":
        config_path = os.getenv("APPDATA")
        if not config_path:
            debug_print("Error: No se pudo encontrar la variable de entorno APPDATA.")
            return None
    elif system == "Darwin":  # macOS
        config_path = os.path.expanduser("~/Library/Application Support")
    else:
        # Para otros sistemas, usar el directorio home como fallback
        config_path = os.path.expanduser("~/.config")
        debug_print(
            f"Sistema no reconocido ({system}), usando ~/.config como fallback."
        )

    return config_path


# Constante para el nombre del archivo de configuracion
CONFIG_FILE_NAME = "Write_Focus.ini"
# Constante para el nombre de la seccion en el archivo .ini
CONFIG_SECTION = "Settings"
# Constante para la clave del nombre del nodo principal en el archivo .ini
CONFIG_NODE_NAME_KEY = "node_name"
# Constante para la clave del nombre del nodo secundario en el archivo .ini
CONFIG_SECONDARY_NODE_NAME_KEY = "secondary_node_name"
# Valor por defecto para el nombre del nodo principal
DEFAULT_NODE_NAME = "Write_Pub"
# Valor por defecto para el nombre del nodo secundario
DEFAULT_SECONDARY_NODE_NAME = "Write_EXR_Publish_DWAA"


def get_config_path():
    """Devuelve la ruta completa al archivo de configuracion."""
    try:
        user_config_dir = get_user_config_dir()
        if not user_config_dir:
            return None
        config_dir = os.path.join(user_config_dir, "LGA", "ToolPack")
        return os.path.join(config_dir, CONFIG_FILE_NAME)
    except Exception as e:
        debug_print(f"Error al obtener la ruta de configuracion: {e}")
        return None


def ensure_config_exists():
    """
    Asegura que el directorio de configuracion y el archivo .ini existan.
    Si no existen, los crea con los valores predeterminados.
    """
    config_file_path = get_config_path()
    if not config_file_path:
        return  # Salir si no se pudo obtener la ruta

    config_dir = os.path.dirname(config_file_path)

    try:
        # Crear el directorio si no existe
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            debug_print(f"Directorio creado: {config_dir}")

        # Crear el archivo .ini si no existe
        if not os.path.exists(config_file_path):
            config = configparser.ConfigParser()
            config[CONFIG_SECTION] = {
                CONFIG_NODE_NAME_KEY: DEFAULT_NODE_NAME,
                CONFIG_SECONDARY_NODE_NAME_KEY: DEFAULT_SECONDARY_NODE_NAME,
            }
            with open(config_file_path, "w") as configfile:
                config.write(configfile)
            debug_print(
                f"Archivo de configuración creado: {config_file_path} con valores predeterminados '{DEFAULT_NODE_NAME}' y '{DEFAULT_SECONDARY_NODE_NAME}'"
            )
        # else:
        #     debug_print(f"Archivo de configuración ya existe: {config_file_path}")
    except Exception as e:
        debug_print(f"Error al asegurar la configuración: {e}")


def get_node_names_from_config():
    """
    Lee los nombres de los nodos desde el archivo de configuracion .ini.
    Devuelve una tupla (primario, secundario) con los valores leidos o los valores por defecto si hay errores.
    Los nombres se normalizan al leerlos.
    """
    config_file_path = get_config_path()
    if not config_file_path or not os.path.exists(config_file_path):
        debug_print(
            "Archivo de configuración no encontrado, usando valores por defecto."
        )
        return (
            normalize_name(DEFAULT_NODE_NAME),
            normalize_name(DEFAULT_SECONDARY_NODE_NAME),
        )
    try:
        config = configparser.ConfigParser()
        config.read(config_file_path)
        if config.has_section(CONFIG_SECTION):
            node_name = config.get(
                CONFIG_SECTION, CONFIG_NODE_NAME_KEY, fallback=DEFAULT_NODE_NAME
            )
            secondary_node_name = config.get(
                CONFIG_SECTION,
                CONFIG_SECONDARY_NODE_NAME_KEY,
                fallback=DEFAULT_SECONDARY_NODE_NAME,
            )
            return (
                (
                    normalize_name(node_name.strip())
                    if node_name
                    else normalize_name(DEFAULT_NODE_NAME)
                ),
                (
                    normalize_name(secondary_node_name.strip())
                    if secondary_node_name
                    else normalize_name(DEFAULT_SECONDARY_NODE_NAME)
                ),
            )
        else:
            debug_print(
                f"Sección [{CONFIG_SECTION}] no encontrada en {config_file_path}. Usando valores por defecto."
            )
            return (
                normalize_name(DEFAULT_NODE_NAME),
                normalize_name(DEFAULT_SECONDARY_NODE_NAME),
            )
    except configparser.Error as e:
        debug_print(
            f"Error al leer el archivo de configuración {config_file_path}: {e}. Usando valores por defecto."
        )
        return (
            normalize_name(DEFAULT_NODE_NAME),
            normalize_name(DEFAULT_SECONDARY_NODE_NAME),
        )
    except Exception as e:
        debug_print(
            f"Error inesperado al leer la configuración: {e}. Usando valores por defecto."
        )
        return (
            normalize_name(DEFAULT_NODE_NAME),
            normalize_name(DEFAULT_SECONDARY_NODE_NAME),
        )


# Asegurarse de que el archivo de configuracion existe al iniciar
ensure_config_exists()


def main():
    """
    Busca un nodo Write con el nombre especificado en la configuracion (primario y secundario),
    lo centra en el DAG, aplica un zoom fijo y abre su panel de propiedades.
    Si no encuentra ninguno, muestra un mensaje de error.
    Incluye medicion de tiempo para cada proceso.
    """
    tiempo_inicio_total = time.time()
    debug_print("Inicio script - Tiempo: 0.00 ms")
    ZOOM_LEVEL = 1.5
    # --- Leer nombres de los nodos desde config ---
    tiempo_inicio_config = time.time()
    node_to_find, secondary_node_to_find = get_node_names_from_config()
    tiempo_fin_config = time.time()
    debug_print(
        f"Configuración leída ('{node_to_find}', '{secondary_node_to_find}') - Tiempo: {(tiempo_fin_config - tiempo_inicio_total) * 1000:.2f} ms"
    )
    # --- Buscar nodo principal por nombre usando busqueda flexible ---
    tiempo_inicio_busqueda = time.time()
    write_node = find_write_node_flexible(node_to_find)
    # Si no encuentra el principal, busca el secundario
    if not write_node:
        debug_print(
            f"No se encontró el nodo principal '{node_to_find}', buscando secundario '{secondary_node_to_find}'"
        )
        write_node = find_write_node_flexible(secondary_node_to_find)
    tiempo_fin_busqueda = time.time()
    debug_print(
        f"Búsqueda de nodo finalizada - Tiempo: {(tiempo_fin_busqueda - tiempo_inicio_total) * 1000:.2f} ms"
    )
    debug_print(
        f"  Tiempo específico de búsqueda (find_write_node_flexible): {(tiempo_fin_busqueda - tiempo_inicio_busqueda) * 1000:.2f} ms"
    )
    if write_node:
        if write_node.Class() != "Write":
            nuke.message(
                f"Se encontró un nodo llamado '{write_node.name()}' pero no es del tipo Write."
            )
            tiempo_fin_total = time.time()
            debug_print(
                f"Error: Tipo de nodo incorrecto. Tiempo total: {(tiempo_fin_total - tiempo_inicio_total) * 1000:.2f} ms"
            )
            return
        tiempo_inicio_deseleccion = time.time()
        for n in nuke.selectedNodes():
            n["selected"].setValue(False)
        tiempo_fin_deseleccion = time.time()
        debug_print(
            f"  Tiempo de deselección: {(tiempo_fin_deseleccion - tiempo_inicio_deseleccion) * 1000:.2f} ms"
        )
        tiempo_inicio_seleccion = time.time()
        write_node["selected"].setValue(True)
        tiempo_fin_seleccion = time.time()
        debug_print(
            f"  Tiempo de selección: {(tiempo_fin_seleccion - tiempo_inicio_seleccion) * 1000:.2f} ms"
        )
        tiempo_inicio_calculo = time.time()
        xCenter = write_node.xpos() + write_node.screenWidth() / 2
        yCenter = write_node.ypos() + write_node.screenHeight() / 2
        tiempo_fin_calculo = time.time()
        debug_print(
            f"  Tiempo de cálculo de centro: {(tiempo_fin_calculo - tiempo_inicio_calculo) * 1000:.2f} ms"
        )
        tiempo_inicio_zoom = time.time()
        nuke.zoom(ZOOM_LEVEL, [xCenter, yCenter])
        tiempo_fin_zoom = time.time()
        debug_print(
            f"  Tiempo de zoom: {(tiempo_fin_zoom - tiempo_inicio_zoom) * 1000:.2f} ms"
        )
        tiempo_inicio_panel = time.time()
        write_node.showControlPanel()
        tiempo_fin_panel = time.time()
        debug_print(
            f"  Tiempo de mostrar panel: {(tiempo_fin_panel - tiempo_inicio_panel) * 1000:.2f} ms"
        )
        tiempo_fin_total = time.time()
        debug_print(
            f"Nodo '{write_node.name()}' encontrado y enfocado. Tiempo total: {(tiempo_fin_total - tiempo_inicio_total) * 1000:.2f} ms"
        )
    else:
        tiempo_fin_total = time.time()
        debug_print(
            f"Error: Nodo no encontrado. Tiempo total: {(tiempo_fin_total - tiempo_inicio_total) * 1000:.2f} ms"
        )
        nuke.message(
            f"No se encontró ningún nodo Write que coincida con '{node_to_find}' ni '{secondary_node_to_find}' en el script actual."
        )


# Ejecutar la funcion cuando se importe este script
# main()
