"""
______________________________________________________________________________

  LGA_viewer_SnapShot_logging v1.07 | Lega

  Logger compartido de la tool Take/Show Snapshot.

  Sigue el esquema de docs/Docu_Logging_System.md: escribe a archivo, no a la
  consola de Nuke, y es seguro entre hilos con QueueHandler + QueueListener.

  Tres cosas se apartan del logger del Media Manager, a proposito:

  1. NO trunca el log al arrancar, appendea. El caso que motivo todo esto fue
     un boton que desaparecio y se diagnostico al dia siguiente: si el log se
     vaciara en cada arranque, reiniciar Nuke —lo primero que uno hace cuando
     algo se rompe— borraria la evidencia.
  2. Un archivo POR PROCESO, con el pid en el nombre. Con dos Nukes abiertos
     sobre el mismo archivo, al cruzar el tamano de rotacion los dos rotan a la
     vez y uno falla; ese traceback sale por stderr, o sea al Script Editor,
     que es justo lo que este sistema existe para evitar. Al arrancar se borran
     los logs de sesiones viejas y se dejan los MAX_SESIONES mas recientes.
  3. Rota por tamano (1 MB x 2 backups) en vez de crecer sin limite, que es la
     contracara de no truncar nunca.

  El motivo de que este modulo exista: un boton del viewer desaparecio y no
  quedo ni una linea en ningun lado para saber por que. La tool usaba
  debug_print contra la consola con DEBUG = False.

  Los cuatro modulos de esta tool escriben aca (todos van con la misma version):
    LGA_viewer_SnapShot.py          <- el principal
    LGA_viewer_SnapShot_Buttons.py
    LGA_viewer_SnapShot_Gallery.py
    LGA_viewer_SnapShot_logging.py  <- este

  v1.06: Version inicial.
______________________________________________________________________________

"""

import atexit
import logging
import os
import queue
import threading
import time
from logging.handlers import QueueHandler, RotatingFileHandler, QueueListener


# DEBUG apaga todo. DEBUG_LOG escribe al archivo; DEBUG_CONSOLE, ademas, al
# Script Editor. El archivo va prendido por default: es barato —la escritura es
# asincrona— y es la unica forma de saber que paso cuando algo falla una vez.
DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True

TOOL_NAME = "LGA_viewer_SnapShot"
MAX_BYTES = 1024 * 1024
BACKUP_COUNT = 2
# Cuantas sesiones de Nuke se conservan. Cada una es un archivo con su pid.
MAX_SESIONES = 5

script_start_time = None
debug_log_listener = None
_logging_lock = threading.Lock()


class RelativeTimeFormatter(logging.Formatter):
    """Agrega el tiempo transcurrido desde el primer registro."""

    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created
        record.relative_time = "%.3fs" % (record.created - script_start_time)
        return super().format(record)


def get_toolpack_root():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_log_dir():
    return os.path.join(get_toolpack_root(), "logs")


def get_log_file_path(tool_name=TOOL_NAME):
    """Un archivo por proceso: dos Nukes no pueden pelear por el mismo."""
    return os.path.join(get_log_dir(), "%s_%d.log" % (tool_name, os.getpid()))


def limpiar_sesiones_viejas(tool_name=TOOL_NAME, dejar=MAX_SESIONES):
    """
    Borra los logs de sesiones anteriores y deja los mas recientes.

    Sin esto, un archivo por proceso se acumula sin fin. Los backups de
    rotacion (.log.1, .log.2) se cuentan como parte de su sesion.
    """
    import glob
    import re

    try:
        patron = os.path.join(get_log_dir(), "%s_*.log*" % tool_name)
        por_sesion = {}
        for ruta in glob.glob(patron):
            m = re.match(
                r"%s_(\d+)\.log" % re.escape(tool_name), os.path.basename(ruta)
            )
            if not m:
                continue
            por_sesion.setdefault(m.group(1), []).append(ruta)

        if len(por_sesion) <= dejar:
            return

        def mas_nuevo(archivos):
            return max(os.path.getmtime(a) for a in archivos)

        ordenadas = sorted(por_sesion.items(), key=lambda kv: mas_nuevo(kv[1]))
        for _pid, archivos in ordenadas[: len(ordenadas) - dejar]:
            for ruta in archivos:
                try:
                    os.remove(ruta)
                except Exception:
                    # Puede ser de un Nuke todavia abierto: se deja y listo.
                    pass
    except Exception:
        pass


def setup_debug_logging(tool_name=TOOL_NAME):
    """Arma el logger a archivo. Devuelve None si no se pudo."""
    global debug_log_listener

    with _logging_lock:
        try:
            log_file_path = get_log_file_path(tool_name)
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            limpiar_sesiones_viejas(tool_name)

            logger = logging.getLogger("%s_logger" % tool_name.lower())
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            if logger.handlers:
                logger.handlers.clear()

            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                RelativeTimeFormatter(
                    "%(asctime)s [%(relative_time)8s] %(levelname)-5s "
                    "[%(module)s::%(funcName)s] %(message)s"
                )
            )

            log_queue = queue.Queue()
            queue_handler = QueueHandler(log_queue)
            queue_handler.setLevel(logging.DEBUG)
            logger.addHandler(queue_handler)

            if debug_log_listener:
                try:
                    debug_log_listener.stop()
                except Exception:
                    pass

            debug_log_listener = QueueListener(
                log_queue, file_handler, respect_handler_level=True
            )
            debug_log_listener.start()

            return logger
        except Exception as e:
            # El logging nunca puede tumbar la tool.
            print("LGA_viewer_SnapShot: no se pudo iniciar el log: %s" % e)
            return None


def configure_logger(reset=False):
    """Devuelve el logger, armandolo la primera vez."""
    if reset and hasattr(configure_logger, "logger"):
        cleanup_logging()
        try:
            if configure_logger.logger:
                configure_logger.logger.handlers.clear()
        except Exception:
            pass
        delattr(configure_logger, "logger")

    if hasattr(configure_logger, "logger"):
        return configure_logger.logger

    configure_logger.logger = setup_debug_logging()
    if configure_logger.logger is not None:
        # Marca de arranque, para separar sesiones adentro del mismo archivo.
        try:
            configure_logger.logger.info(
                "=== sesion nueva | pid %d | %s ==="
                % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S"))
            )
        except Exception:
            pass
    return configure_logger.logger


def debug_print(*message, **kwargs):
    """
    Reemplazo de los debug_print sueltos que tenia cada modulo.

    Misma firma de siempre, asi que las llamadas existentes no cambian; lo que
    cambia es que ahora quedan escritas en el archivo.

    _nivel_pila: cuantos frames saltar para que el log diga quien llamo y no
    esta funcion. 2 es el llamador directo; log_error usa 3 porque agrega uno.
    """
    if not DEBUG:
        return

    nivel = kwargs.get("level", "info")
    nivel_pila = kwargs.get("_nivel_pila", 2)
    msg = " ".join(str(a) for a in message)

    if DEBUG_LOG:
        try:
            logger = configure_logger()
            if logger is not None:
                metodo = getattr(logger, nivel, logger.info)
                try:
                    metodo(msg, stacklevel=nivel_pila)
                except TypeError:
                    metodo(msg)
        except Exception:
            # El logging nunca puede tumbar a quien lo llama.
            pass

    if DEBUG_CONSOLE:
        global script_start_time
        if script_start_time is None:
            script_start_time = time.time()
        print("[%.3fs] %s" % (time.time() - script_start_time, msg))


def log_error(*message):
    """Atajo para lo que ademas se le muestra al usuario."""
    debug_print(*message, level="error", _nivel_pila=3)


def cleanup_logging():
    global debug_log_listener
    if not debug_log_listener:
        return
    try:
        debug_log_listener.stop()
    except Exception:
        pass
    finally:
        debug_log_listener = None


atexit.register(cleanup_logging)
