"""
Shared logging helpers for LGA_mediaManager.
"""

import atexit
import logging
import os
import queue
import threading
import time
from logging.handlers import QueueHandler, QueueListener


DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True
TOOL_NAME = "LGA_mediaManager"

script_start_time = None
debug_log_listener = None
_logging_lock = threading.Lock()


class RelativeTimeFormatter(logging.Formatter):
    """Formatter that adds relative time from the first log record."""

    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created

        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def get_toolpack_root():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_log_file_path(tool_name=TOOL_NAME):
    return os.path.join(get_toolpack_root(), "logs", f"{tool_name}.log")


def get_log_prefix(caller_class=None, caller_method=None):
    """Compatibility helper for old timestamp-prefixed debug messages."""
    global script_start_time

    if script_start_time is None:
        script_start_time = time.time()

    elapsed = time.time() - script_start_time
    timestamp = f"[{elapsed:.3f}s]"

    if caller_class and caller_method:
        return f"{timestamp} [{caller_class}::{caller_method}]"
    return timestamp


def setup_debug_logging(tool_name=TOOL_NAME):
    """Configure a file-only async logger for the given tool."""
    global debug_log_listener

    with _logging_lock:
        log_file_path = get_log_file_path(tool_name)
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)

        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, "w", encoding="utf-8") as log_file:
                    log_file.write("")
            except Exception:
                pass

        logger_name = f"{tool_name.lower()}_logger"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if logger.handlers:
            logger.handlers.clear()

        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            RelativeTimeFormatter("[%(relative_time)s] [%(module)s::%(funcName)s] %(message)s")
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
        debug_log_listener.daemon = True
        debug_log_listener.start()

        return logger


def configure_logger(reset=False):
    if reset and hasattr(configure_logger, "logger"):
        cleanup_logging()
        try:
            configure_logger.logger.handlers.clear()
        except Exception:
            pass
        delattr(configure_logger, "logger")

    if hasattr(configure_logger, "logger"):
        return configure_logger.logger

    configure_logger.logger = setup_debug_logging()
    return configure_logger.logger


def debug_print(*message, level="info"):
    """Route debug messages to file and optionally console."""
    global script_start_time

    if not DEBUG:
        return

    msg = " ".join(str(arg) for arg in message)

    if DEBUG_LOG:
        logger = configure_logger()
        if script_start_time is None:
            script_start_time = time.time()

        log_method = getattr(logger, level, logger.info)
        try:
            log_method(msg, stacklevel=2)
        except TypeError:
            log_method(msg)

    if DEBUG_CONSOLE:
        if script_start_time is None:
            script_start_time = time.time()
        relative_time = time.time() - script_start_time
        print(f"[{relative_time:.3f}s] {msg}")


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
