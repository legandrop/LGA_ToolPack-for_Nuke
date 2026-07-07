"""
____________________________________________________________________

  SecureConfig_Reader v1.02 | Lega

  Lee config.secure de PipeSync para credenciales/roles de Flow.

  v1.01: Copia local para LGA_ToolPack, usada por Show Flow Notes sin depender
         de HieroTools instalado/cargado.
  v1.02: Agrega trazas no sensibles para diagnosticar lectura de config.secure.
____________________________________________________________________

Usado por runtime activo:
- LGA_NKS_ViewerTL_Panel.py
- LGA_NKS_Projects_Panel_py/LGA_Projects_Panel_ScanProjects.py
- LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py
- LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assignee.py
- LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assign_Assignee.py
- LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Clear_Assignees.py
- LGA_NKS_Assignee_Panel_py/LGA_NKS_Wasabi_PolicyAssign.py
- LGA_NKS_Assignee_Panel_py/LGA_NKS_Wasabi_PolicyUnassign.py
- LGA_NKS_Assignee_Panel_py/LGA_NKS_Wasabi_PolicyUnassign_CompletedShots.py
- LGA_NKS_Assignee_Panel_py/wasabi_policy_utils.py
- LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ShowInFlow.py
- LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_CreateShot.py
- LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ShotPriority.py
"""

import sys
import os
import json
import base64
from pathlib import Path
import hashlib


# Variable global para activar o desactivar los prints de debug
DEBUG = False


def _trace(*parts):
    try:
        log_path = Path(__file__).resolve().parents[1] / "logs" / "LGA_showFlowNotes.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(log_path), "a", encoding="utf-8") as handle:
            handle.write(
                "[SecureConfig_Reader] {}\n".format(" ".join(str(part) for part in parts))
            )
    except Exception:
        pass


_trace("module import started", "file=", __file__)


def debug_print(message):
    """Función de debug simple que imprime directamente si DEBUG está activado"""
    if DEBUG:
        print(f"[SecureConfig_Reader] {message}")


def get_config_path():
    """Obtiene la ruta del archivo de configuración segura."""
    # En Windows: %APPDATA%\LGA\PipeSync\config.secure
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")  # APPDATA ya apunta a Roaming
        if not app_data:
            raise RuntimeError("Variable de entorno APPDATA no encontrada")
        return Path(app_data) / "LGA" / "PipeSync" / "config.secure"
    # En macOS: ~/Library/Application Support/LGA/PipeSync/config.secure
    elif sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "LGA"
            / "PipeSync"
            / "config.secure"
        )
    # En Linux: ~/.config/LGA/PipeSync/config.secure
    else:
        return Path.home() / ".config" / "LGA" / "PipeSync" / "config.secure"


def get_key_path():
    """Obtiene la ruta del archivo de clave."""
    # En Windows: %APPDATA%\LGA\PipeSync\.key
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")  # APPDATA ya apunta a Roaming
        if not app_data:
            raise RuntimeError("Variable de entorno APPDATA no encontrada")
        return Path(app_data) / "LGA" / "PipeSync" / ".key"
    # En macOS: ~/Library/Application Support/LGA/PipeSync/.key
    elif sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "LGA"
            / "PipeSync"
            / ".key"
        )
    # En Linux: ~/.config/LGA/PipeSync/.key
    else:
        return Path.home() / ".config" / "LGA" / "PipeSync" / ".key"


def get_system_identifier():
    """Obtiene un identificador único del sistema para generar la clave."""
    # Obtener información del sistema
    import platform

    system_info = platform.uname()

    # Crear un identificador único
    identifier = f"{system_info.node}{system_info.system}{system_info.machine}"

    # Añadir MAC address si es posible
    try:
        import uuid

        mac = ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 8 * 6, 8)
            ][::-1]
        )
        identifier += mac
    except:
        pass

    return identifier


def generate_key():
    """Genera una clave de encriptación basada en el sistema."""
    system_id = get_system_identifier()
    return hashlib.sha256(system_id.encode()).digest()


def get_encryption_key():
    """Obtiene la clave de encriptación."""
    key_path = get_key_path()

    if key_path.exists():
        # Eliminado log detallado
        with open(key_path, "rb") as f:
            key = f.read()
            return key
    else:
        # Si no existe el archivo de clave, generar una nueva
        key = generate_key()
        return key


def decrypt(encrypted_text, key):
    """Desencripta un texto usando XOR con la clave proporcionada."""
    if not encrypted_text:
        return ""

    try:
        # Decodificar de base64
        encrypted_data = base64.b64decode(encrypted_text)

        # Desencriptar usando XOR
        decrypted_data = bytearray()
        for i in range(len(encrypted_data)):
            decrypted_data.append(encrypted_data[i] ^ key[i % len(key)])

        result = decrypted_data.decode("utf-8")
        return result
    except Exception as e:
        debug_print(f"[SecureConfig_Reader::decrypt] Error al desencriptar: {str(e)}")
        return ""


def read_secure_config():
    """Lee la configuración segura y devuelve un diccionario con los valores."""
    try:
        _trace("read_secure_config started")
        config_path = get_config_path()
        _trace("config_path=", config_path, "exists=", config_path.exists())
        debug_print(
            f"[SecureConfig_Reader::read_secure_config] Ruta de configuración segura: {config_path}"
        )

        if not config_path.exists():
            debug_print(
                f"[SecureConfig_Reader::read_secure_config] Archivo de configuración segura no encontrado en: {config_path}"
            )
            return None

        # Obtener la clave de encriptación
        _trace("getting encryption key")
        key = get_encryption_key()
        _trace("encryption key length=", len(key) if key else 0)

        # Leer el archivo encriptado
        _trace("reading encrypted config")
        with open(config_path, "r") as f:
            encrypted_data = f.read()
        _trace("encrypted config chars=", len(encrypted_data))

        # Desencriptar el contenido
        _trace("decrypting config")
        json_data = decrypt(encrypted_data, key)

        if not json_data:
            _trace("decrypt failed or returned empty")
            debug_print(
                f"[SecureConfig_Reader::read_secure_config] No se pudo desencriptar la configuración"
            )
            return None

        # Parsear el JSON
        config = json.loads(json_data)
        _trace("config parsed", "sections=", list(config.keys()) if isinstance(config, dict) else type(config))
        # Comentado temporalmente este log. NO BORRAR!
        # debug_print(f"Contenido de la configuración: {json.dumps(config, indent=2)}")
        return config

    except Exception as e:
        _trace("read_secure_config exception", repr(e))
        debug_print(
            f"[SecureConfig_Reader::read_secure_config] Error al leer la configuración segura: {str(e)}"
        )
        import traceback

        debug_print(traceback.format_exc())
        return None


def get_flow_credentials():
    """Obtiene las credenciales de Flow desde la configuración segura."""
    _trace("get_flow_credentials started")
    config = read_secure_config()

    if not config:
        _trace("get_flow_credentials no config")
        debug_print(
            f"[SecureConfig_Reader::get_flow_credentials] No se pudo leer la configuración segura"
        )
        return None, None, None

    if "Flow" not in config:
        _trace("get_flow_credentials Flow section missing")
        debug_print(
            f"[SecureConfig_Reader::get_flow_credentials] No se encontró la sección 'Flow' en la configuración segura"
        )
        return None, None, None

    flow_config = config["Flow"]

    url = flow_config.get("Url", "")
    login = flow_config.get("Login", "")
    password = flow_config.get("Password", "")
    _trace(
        "get_flow_credentials done",
        "has_url=", bool(url),
        "has_login=", bool(login),
        "has_password=", bool(password),
    )

    return url, login, password


def get_s3_credentials():
    """Obtiene las credenciales de Wasabi S3 desde la configuración segura."""
    config = read_secure_config()

    if not config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_credentials] No se pudo leer la configuración segura"
        )
        return None, None, None, None

    if "Wasabi" not in config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_credentials] No se encontró la sección 'Wasabi' en la configuración segura"
        )
        return None, None, None, None

    wasabi_config = config["Wasabi"]

    access_key = wasabi_config.get("AccessKey", "")
    secret_key = wasabi_config.get("SecretKey", "")
    endpoint = wasabi_config.get("Endpoint", "")
    region = wasabi_config.get("Region", "")

    return access_key, secret_key, endpoint, region


def get_s3_connection_limits():
    """
    Obtiene el número máximo de conexiones S3 permitidas desde la configuración segura.

    Returns:
        int: Número máximo de conexiones. Por defecto 30 si no está configurado.
    """
    config = read_secure_config()

    if not config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_connection_limits] No se pudo leer la configuración segura para los límites de conexión"
        )
        return 30

    if "Wasabi" not in config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_connection_limits] No se encontró la sección 'Wasabi' en la configuración para los límites de conexión"
        )
        return 30

    wasabi_config = config["Wasabi"]

    # Leer el número de conexiones, por defecto 30
    connections = wasabi_config.get("Connections", 30)

    # Asegurar que es un número válido
    try:
        connections = int(connections)
        if connections <= 0:
            debug_print(
                f"[SecureConfig_Reader::get_s3_connection_limits] Número de conexiones inválido: {connections}, usando el valor por defecto (30)"
            )
            return 30
        debug_print(
            f"[SecureConfig_Reader::get_s3_connection_limits] Límite de conexiones S3 configurado: {connections}"
        )
        return connections
    except (ValueError, TypeError):
        debug_print(
            f"[SecureConfig_Reader::get_s3_connection_limits] Error al leer el número de conexiones: {wasabi_config.get('Connections')}, usando el valor por defecto (30)"
        )
        return 30


def get_s3_download_connection_limit():
    """
    Obtiene el número máximo de conexiones de descarga S3 permitidas desde la configuración segura.

    Returns:
        int: Número máximo de conexiones de descarga. Por defecto 30 si no está configurado o es inválido.
    """
    config = read_secure_config()
    default_limit = 30  # Coincide con el default en C++

    if not config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_download_connection_limit] No se pudo leer la configuración segura. Usando default: {default_limit}"
        )
        return default_limit

    if "Wasabi" not in config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_download_connection_limit] No se encontró la sección 'Wasabi'. Usando default: {default_limit}"
        )
        return default_limit

    wasabi_config = config["Wasabi"]

    # Leer el número de conexiones de descarga, por defecto el valor default_limit
    connections = wasabi_config.get("DownloadConnections", default_limit)

    # Asegurar que es un número válido
    try:
        connections = int(connections)
        if connections <= 0:
            debug_print(
                f"[SecureConfig_Reader::get_s3_download_connection_limit] Número de conexiones de descarga inválido: {connections}. Usando default: {default_limit}"
            )
            return default_limit
        debug_print(
            f"[SecureConfig_Reader::get_s3_download_connection_limit] Límite de conexiones de descarga S3 leído: {connections}"
        )
        return connections
    except (ValueError, TypeError):
        debug_print(
            f"[SecureConfig_Reader::get_s3_download_connection_limit] Error al leer el número de conexiones de descarga: '{wasabi_config.get('DownloadConnections')}. Usando default: {default_limit}"
        )
        return default_limit


def get_s3_upload_connection_limit():
    """
    Obtiene el número máximo de conexiones de subida S3 permitidas desde la configuración segura.

    Returns:
        int: Número máximo de conexiones de subida. Por defecto 10 si no está configurado o es inválido.
    """
    config = read_secure_config()
    default_limit = 10  # Cambio: Nuevo máximo permitido

    if not config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_upload_connection_limit] No se pudo leer la configuración segura. Usando default: {default_limit}"
        )
        return default_limit

    if "Wasabi" not in config:
        debug_print(
            f"[SecureConfig_Reader::get_s3_upload_connection_limit] No se encontró la sección 'Wasabi'. Usando default: {default_limit}"
        )
        return default_limit

    wasabi_config = config["Wasabi"]

    # Leer el número de conexiones de subida, por defecto el valor default_limit
    connections = wasabi_config.get("UploadConnections", default_limit)

    # Asegurar que es un número válido
    try:
        connections = int(connections)
        if connections <= 0:
            debug_print(
                f"[SecureConfig_Reader::get_s3_upload_connection_limit] Número de conexiones de subida inválido: {connections}. Usando default: {default_limit}"
            )
            return default_limit
        # Ajustar automáticamente valores mayores al máximo permitido
        if connections > 10:
            debug_print(
                f"[SecureConfig_Reader::get_s3_upload_connection_limit] Valor de conexiones de subida mayor al máximo permitido ({connections} > 10). Ajustando a 10."
            )
            connections = 10
        debug_print(
            f"[SecureConfig_Reader::get_s3_upload_connection_limit] Límite de conexiones de subida S3 leído: {connections}"
        )
        return connections
    except (ValueError, TypeError):
        debug_print(
            f"[SecureConfig_Reader::get_s3_upload_connection_limit] Error al leer el número de conexiones de subida: '{wasabi_config.get('UploadConnections')}'. Usando default: {default_limit}"
        )
        return default_limit


def save_flow_permission_group(permission_group):
    """Guarda el grupo de permisos del usuario de Flow en la configuración segura."""
    try:
        # Leer la configuración actual
        config = read_secure_config()

        if not config:
            debug_print(
                f"[SecureConfig_Reader::save_flow_permission_group] Error: No se pudo leer la configuración segura para guardar el grupo de permisos"
            )
            return False

        # Asegurar que existe la sección 'Flow'
        if "Flow" not in config:
            config["Flow"] = {}

        # Guardar el grupo de permisos
        config["Flow"]["PermissionGroup"] = permission_group

        # Convertir a JSON
        json_data = json.dumps(config)

        # Encriptar
        key = get_encryption_key()
        encrypted_data = encrypt(json_data, key)

        # Guardar en el archivo
        config_path = get_config_path()
        with open(config_path, "w") as f:
            f.write(encrypted_data)

        debug_print(
            f"[SecureConfig_Reader::save_flow_permission_group] Grupo de permisos '{permission_group}' guardado en la configuración"
        )
        return True

    except Exception as e:
        debug_print(
            f"[SecureConfig_Reader::save_flow_permission_group] Error al guardar el grupo de permisos: {str(e)}"
        )
        import traceback

        debug_print(traceback.format_exc())
        return False


def encrypt(text, key):
    """Encripta un texto usando XOR con la clave proporcionada."""
    if not text:
        return ""

    try:
        # Encriptar usando XOR
        encrypted_data = bytearray()
        text_bytes = text.encode("utf-8")
        for i in range(len(text_bytes)):
            encrypted_data.append(text_bytes[i] ^ key[i % len(key)])

        # Codificar en base64
        result = base64.b64encode(encrypted_data).decode("utf-8")
        return result
    except Exception as e:
        debug_print(f"[SecureConfig_Reader::encrypt] Error al encriptar: {str(e)}")
        return ""


# Función principal para pruebas
if __name__ == "__main__":
    debug_print("[SecureConfig_Reader::main] Iniciando lectura de configuración segura")

    url, login, password = get_flow_credentials()

    if url and login and password:
        debug_print(
            f"[SecureConfig_Reader::main] Credenciales obtenidas. URL: {url}, Usuario: {login}"
        )
        debug_print(
            f"[SecureConfig_Reader::main] URL: {url}, Usuario: {login}, Contraseña: {'*' * len(password)}"
        )
    else:
        debug_print(
            "[SecureConfig_Reader::main] No se pudieron obtener las credenciales de Flow"
        )
        debug_print(
            "[SecureConfig_Reader::main] ERROR: No se pudieron obtener las credenciales de Flow"
        )
