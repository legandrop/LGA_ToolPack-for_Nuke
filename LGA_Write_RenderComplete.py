"""
_______________________________________________________________________________________________________________

  LGA_Write_RenderComplete v1.34 | Lega
  Calcula la duracion al finalizar el render y la agrega en un knob en el tab User del nodo write
  Reproduce un sonido y envia un correo con los detalles del render si la opcion 'Send Mail' esta activada
_______________________________________________________________________________________________________________

"""

import nuke
import os
import datetime
from PySide2.QtMultimedia import QSound
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
import binascii
import platform

# Variable global para controlar el debug
DEBUG = False  # Poner en False para desactivar los mensajes de debug


# Funcion debug_print
def debug_print(*message):
    if DEBUG:
        print(*message)


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


# --- Configuración de archivo DAT para settings de mail ---
CONFIG_FILE_NAME = "RenderComplete.dat"
CONFIG_FROM_KEY = "from_email"
CONFIG_PASS_KEY = "from_password"
CONFIG_TO_KEY = "to_email"
CONFIG_WAV_KEY = "sound_wav_path"  # Nueva clave para referencia
CONFIG_SOUND_ENABLED_KEY = "sound_enabled"  # Nuevo setting para ON/OFF
CONFIG_RENDER_TIME_ENABLED_KEY = "render_time_enabled"  # Nuevo setting para ON/OFF
# Exportar constantes para uso externo
__all__ = [
    "get_config_path",
    "ensure_config_exists",
    "get_mail_settings_from_config",
    "save_mail_settings_to_config",
    "get_wav_path_from_config",
    "save_wav_path_to_config",
    "get_sound_enabled_from_config",
    "save_sound_enabled_to_config",
    "get_render_time_enabled_from_config",
    "save_render_time_enabled_to_config",
    "CONFIG_FROM_KEY",
    "CONFIG_PASS_KEY",
    "CONFIG_TO_KEY",
    "CONFIG_WAV_KEY",
    "CONFIG_SOUND_ENABLED_KEY",
    "CONFIG_RENDER_TIME_ENABLED_KEY",
]


def get_config_path():
    """Devuelve la ruta completa al archivo de configuración de mail (.dat)."""
    try:
        user_config_dir = get_user_config_dir()
        if not user_config_dir:
            return None
        config_dir = os.path.join(user_config_dir, "LGA", "ToolPack")
        return os.path.join(config_dir, CONFIG_FILE_NAME)
    except Exception as e:
        debug_print(f"Error al obtener la ruta de configuración: {e}")
        return None


def ensure_config_exists():
    """
    Asegura que el directorio de configuración y el archivo .dat existan.
    Si no existen, los crea con valores vacíos codificados.
    """
    config_file_path = get_config_path()
    if not config_file_path:
        return
    config_dir = os.path.dirname(config_file_path)
    try:
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            debug_print(f"Directorio de configuración creado: {config_dir}")
        if not os.path.exists(config_file_path):
            # Crear archivo .dat con lineas vacias codificadas
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            with open(config_file_path, "w", encoding="utf-8") as configfile:
                configfile.write(f"{empty_encoded}\\n")  # From Email
                configfile.write(f"{empty_encoded}\\n")  # Password
                configfile.write(f"{empty_encoded}\\n")  # To Email
            debug_print(
                f"Archivo de configuración de mail creado: {config_file_path}. Complételo usando LGA_ToolPack_settings."
            )
    except Exception as e:
        debug_print(f"Error al asegurar la configuración de mail: {e}")


def get_mail_settings_from_config():
    """
    Lee los datos de mail desde el archivo .dat codificado.
    Devuelve (from_email, from_password, to_email) decodificados o (None, None, None).
    """
    config_file_path = get_config_path()
    if not config_file_path or not os.path.exists(config_file_path):
        debug_print(
            f"Archivo de configuración de mail (.dat) no encontrado: {config_file_path}"
        )
        return None, None, None
    try:
        with open(config_file_path, "r", encoding="utf-8") as configfile:
            lines = configfile.readlines()

        if len(lines) < 3:
            debug_print(
                f"Archivo de configuración de mail {config_file_path} está incompleto o corrupto."
            )
            return None, None, None

        # Decodificar cada linea
        from_email_encoded = lines[0].strip()
        from_password_encoded = lines[1].strip()
        to_email_encoded = lines[2].strip()

        from_email = base64.b64decode(from_email_encoded).decode("utf-8")
        from_password = base64.b64decode(from_password_encoded).decode("utf-8")
        to_email = base64.b64decode(to_email_encoded).decode("utf-8")

        if from_email and from_password and to_email:
            return from_email, from_password, to_email
        else:
            debug_print(
                f"Uno o más datos de mail en {config_file_path} están vacíos (después de decodificar)."
            )
            return None, None, None

    except (binascii.Error, UnicodeDecodeError) as e:  # Usar binascii.Error
        debug_print(
            f"Error al decodificar el archivo de configuración de mail {config_file_path}: {e}"
        )
        return None, None, None
    except Exception as e:
        debug_print(
            f"Error inesperado al leer la configuración de mail codificada: {e}"
        )
        return None, None, None


def save_mail_settings_to_config(from_email, from_password, to_email):
    """
    Guarda los datos de mail codificados en base64 en el archivo .dat.
    """
    config_file_path = get_config_path()
    if not config_file_path:
        debug_print("No se pudo obtener la ruta del archivo de configuración de mail.")
        return False
    try:
        # Codificar los valores
        from_email_encoded = base64.b64encode(from_email.encode("utf-8")).decode(
            "utf-8"
        )
        password_encoded = base64.b64encode(from_password.encode("utf-8")).decode(
            "utf-8"
        )
        to_email_encoded = base64.b64encode(to_email.encode("utf-8")).decode("utf-8")

        # Escribir las lineas codificadas usando writelines
        lines_to_write = [
            f"{from_email_encoded}\n",
            f"{password_encoded}\n",
            f"{to_email_encoded}\n",
        ]
        with open(config_file_path, "w", encoding="utf-8") as configfile:
            configfile.writelines(lines_to_write)

        debug_print("Configuración de mail guardada de forma segura (writelines).")
        return True
    except Exception as e:
        debug_print(f"Error al guardar la configuración de mail codificada: {e}")
        return False


def get_wav_path_from_config():
    """
    Lee la ruta del wav desde el archivo .dat codificado. Si no existe, devuelve la ruta por defecto (en la carpeta del script).
    """
    config_file_path = get_config_path()
    default_wav_path = os.path.join(
        os.path.dirname(__file__), "LGA_Write_RenderComplete.wav"
    )
    if not config_file_path or not os.path.exists(config_file_path):
        return default_wav_path
    try:
        with open(config_file_path, "r", encoding="utf-8") as configfile:
            lines = configfile.readlines()
        if len(lines) < 4:
            # No hay setting guardado, usar default
            return default_wav_path
        wav_path_encoded = lines[3].strip()
        wav_path = base64.b64decode(wav_path_encoded).decode("utf-8")
        if wav_path:
            return wav_path
        return default_wav_path
    except Exception as e:
        debug_print(f"Error al leer la ruta del wav: {e}")
        return default_wav_path


def save_wav_path_to_config(wav_path):
    """
    Guarda la ruta del wav codificada en base64 en el archivo .dat (cuarta línea).
    Si el archivo no existe, lo crea con los otros campos vacíos.
    """
    config_file_path = get_config_path()
    if not config_file_path:
        debug_print(
            "No se pudo obtener la ruta del archivo de configuración de mail para guardar wav."
        )
        return False
    try:
        # Leer las líneas existentes (o crear vacías si no existen)
        if os.path.exists(config_file_path):
            with open(config_file_path, "r", encoding="utf-8") as configfile:
                lines = configfile.readlines()
        else:
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            lines = [f"{empty_encoded}\n" for _ in range(3)]
        # Asegurar que hay al menos 3 líneas para mail
        while len(lines) < 3:
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            lines.append(f"{empty_encoded}\n")
        # Codificar la ruta del wav
        wav_path_encoded = base64.b64encode(wav_path.encode("utf-8")).decode("utf-8")
        if len(lines) >= 4:
            lines[3] = f"{wav_path_encoded}\n"
        else:
            lines.append(f"{wav_path_encoded}\n")
        with open(config_file_path, "w", encoding="utf-8") as configfile:
            configfile.writelines(lines)
        debug_print(f"Ruta del wav guardada en config: {wav_path}")
        return True
    except Exception as e:
        debug_print(f"Error al guardar la ruta del wav: {e}")
        return False


def get_sound_enabled_from_config():
    """
    Lee el setting de sonido habilitado desde el archivo .dat (quinta línea, ON/OFF, base64). Por defecto ON si no existe.
    """
    config_file_path = get_config_path()
    if not config_file_path or not os.path.exists(config_file_path):
        return True  # Por defecto ON
    try:
        with open(config_file_path, "r", encoding="utf-8") as configfile:
            lines = configfile.readlines()
        if len(lines) < 5:
            return True  # Por defecto ON
        enabled_encoded = lines[4].strip()
        enabled_str = base64.b64decode(enabled_encoded).decode("utf-8")
        return enabled_str.upper() == "ON"
    except Exception as e:
        debug_print(f"Error al leer el setting de sonido: {e}")
        return True


def save_sound_enabled_to_config(enabled):
    """
    Guarda el setting de sonido habilitado (ON/OFF, base64) en la quinta línea del .dat.
    """
    config_file_path = get_config_path()
    if not config_file_path:
        debug_print(
            "No se pudo obtener la ruta del archivo de configuración para guardar sound_enabled."
        )
        return False
    try:
        # Leer las líneas existentes (o crear vacías si no existen)
        if os.path.exists(config_file_path):
            with open(config_file_path, "r", encoding="utf-8") as configfile:
                lines = configfile.readlines()
        else:
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            lines = [f"{empty_encoded}\n" for _ in range(4)]
        # Asegurar que hay al menos 4 líneas para los otros settings
        while len(lines) < 4:
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            lines.append(f"{empty_encoded}\n")
        # Codificar el valor ON/OFF
        value = "ON" if enabled else "OFF"
        value_encoded = base64.b64encode(value.encode("utf-8")).decode("utf-8")
        if len(lines) >= 5:
            lines[4] = f"{value_encoded}\n"
        else:
            lines.append(f"{value_encoded}\n")
        with open(config_file_path, "w", encoding="utf-8") as configfile:
            configfile.writelines(lines)
        debug_print(f"Sound enabled guardado en config: {value}")
        return True
    except Exception as e:
        debug_print(f"Error al guardar el setting de sonido: {e}")
        return False


def get_render_time_enabled_from_config():
    """
    Lee el setting de render time habilitado desde el archivo .dat (sexta línea, ON/OFF, base64). Por defecto ON si no existe.
    """
    config_file_path = get_config_path()
    if not config_file_path or not os.path.exists(config_file_path):
        return True  # Por defecto ON
    try:
        with open(config_file_path, "r", encoding="utf-8") as configfile:
            lines = configfile.readlines()
        if len(lines) < 6:
            return True  # Por defecto ON
        enabled_encoded = lines[5].strip()
        enabled_str = base64.b64decode(enabled_encoded).decode("utf-8")
        return enabled_str.upper() == "ON"
    except Exception as e:
        debug_print(f"Error al leer el setting de render time: {e}")
        return True


def save_render_time_enabled_to_config(enabled):
    """
    Guarda el setting de render time habilitado (ON/OFF, base64) en la sexta línea del .dat.
    """
    config_file_path = get_config_path()
    if not config_file_path:
        debug_print(
            "No se pudo obtener la ruta del archivo de configuración para guardar render_time_enabled."
        )
        return False
    try:
        # Leer las líneas existentes (o crear vacías si no existen)
        if os.path.exists(config_file_path):
            with open(config_file_path, "r", encoding="utf-8") as configfile:
                lines = configfile.readlines()
        else:
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            lines = [f"{empty_encoded}\n" for _ in range(5)]
        # Asegurar que hay al menos 5 líneas para los otros settings
        while len(lines) < 5:
            empty_encoded = base64.b64encode("".encode("utf-8")).decode("utf-8")
            lines.append(f"{empty_encoded}\n")
        # Codificar el valor ON/OFF
        value = "ON" if enabled else "OFF"
        value_encoded = base64.b64encode(value.encode("utf-8")).decode("utf-8")
        if len(lines) >= 6:
            lines[5] = f"{value_encoded}\n"
        else:
            lines.append(f"{value_encoded}\n")
        with open(config_file_path, "w", encoding="utf-8") as configfile:
            configfile.writelines(lines)
        debug_print(f"Render time enabled guardado en config: {value}")
        return True
    except Exception as e:
        debug_print(f"Error al guardar el setting de render time: {e}")
        return False


# Asegurarse de que el archivo de configuración existe al iniciar
ensure_config_exists()


def start_time():
    knob = nuke.root().knob("Km_Render_Start_Time")
    if not knob:
        nuke.root().addKnob(nuke.EvalString_Knob("Km_Render_Start_Time"))
        knob = nuke.root().knob("Km_Render_Start_Time")
    if knob:
        knob.setVisible(False)
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        knob.setValue(current_time_str)


def total_time():
    knob = nuke.root().knob("Km_Render_Start_Time")
    if not knob:
        return "00:00:00"
    time1_str = knob.getValue()
    time1 = datetime.datetime.strptime(time1_str, "%Y-%m-%d %H:%M:%S")
    time2 = datetime.datetime.now()
    duration = time2 - time1
    duration_in_s = duration.total_seconds()
    hours, remainder = divmod(duration_in_s, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def send_email(subject, body, to_email=None):
    from_email, password, default_to_email = get_mail_settings_from_config()
    if not from_email or not password or not default_to_email:
        config_path = get_config_path() or "LGA/ToolPack/RenderComplete.dat"
        debug_print(
            f"No se pudieron leer los datos de mail desde: {config_path}\nRevise la consola para detalles y asegúrese de que el archivo esté completo."
        )
        return
    if to_email is None:
        to_email = default_to_email
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.close()
        debug_print("Correo enviado exitosamente.")
    except Exception as e:
        debug_print(f"Error al enviar correo: {e}")


def add_render_time_knob(write_node, render_time):
    if not write_node.knobs().get("render_time"):
        render_time_knob = nuke.String_Knob("render_time", "Render Time")
        write_node.addKnob(render_time_knob)
    write_node["render_time"].setValue(render_time)


def Render_Complete():
    render_time = total_time()

    # Reproducir el sonido solo si el setting está en ON
    if get_sound_enabled_from_config():
        sound_file_path = get_wav_path_from_config()
        QSound.play(sound_file_path)

    # Verificar si el knob "send_mail" existe y esta activado
    write_node = nuke.thisNode()
    send_mail_state = False
    if "send_mail" in write_node.knobs():
        send_mail_state = write_node["send_mail"].value()

    # Agregar o actualizar el knob con el tiempo de render solo si el setting está en ON
    if get_render_time_enabled_from_config():
        add_render_time_knob(write_node, render_time)

    if send_mail_state:
        # Obtener el destinatario del correo electronico de las variables de entorno
        to_email = os.getenv("Nuke_Write_Mail_To", "default_to_email@example.com")

        # Formatear el cuerpo del correo
        script_name = os.path.basename(nuke.root().name())
        file_knob = write_node.knob("file")
        render_directory = os.path.dirname(file_knob.value()) if file_knob else ""
        # Usar nuke.filename(write_node) si es posible, sino fallback a file_knob.value()
        try:
            render_file = nuke.filename(write_node) if file_knob else ""
        except Exception:
            render_file = file_knob.value() if file_knob else ""
        body = (
            f"Script Name: {script_name}\n"
            f"Render Directory: {render_directory}\n"
            f"Render File: {render_file}\n"
            f"Render Time: {render_time}\n"
            "El render ha finalizado exitosamente."
        )

        # Enviar correo electronico
        send_email(subject="Render Finished", body=body, to_email=to_email)


# Agregar callbacks de Nuke
nuke.addBeforeRender(start_time)
nuke.addAfterRender(Render_Complete)
