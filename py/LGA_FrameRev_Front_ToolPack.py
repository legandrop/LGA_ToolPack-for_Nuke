"""
___________________________________________________________________________________

  LGA_FrameRev_Front_ToolPack v1.00 | Lega

  Trae al frente la ventana de FrameRev que se acaba de lanzar (solo Windows).

  La ventana de FrameRev la abre un proceso NUEVO, y Windows no le deja tomar
  el foco solo: su activateWindow() apenas hace titilar el boton de la barra de
  tareas y la ventana queda detras de Nuke. Quien SI puede ceder el frente es
  Nuke, que es la app del frente cuando el usuario hace click. Por eso, despues
  de lanzar, un QTimer en el hilo de la UI espera la ventana de FrameRev y la
  trae con SetForegroundWindow. Si mientras tanto el usuario se fue a otra app,
  no se le roba el foco.

  Es una copia de la logica de LGA_NKS_FrameRev v1.01 de HieroTools: los packs
  no importan codigo entre si. Un arreglo en una se aplica en las dos.

  v1.00: Version inicial.
___________________________________________________________________________________

"""

import os
import sys
import time

# Cada cuanto se busca la ventana de FrameRev y cuanto se la espera. Arranca en
# ~1 s; 15 s cubre una maquina lenta o el primer arranque tras instalar.
FRONT_POLL_MS = 100
FRONT_TIMEOUT_MS = 15000

# Los QTimer vivos: sin una referencia, Python los recolecta y dejan de sonar.
_FRONT_WATCHERS = []


def pick_main_window(windows):
    """Elige la ventana principal de FrameRev entre sus ventanas de nivel superior.

    `windows` es una lista de dicts con hwnd, visible, owned, tool, cloaked y
    area. Se descartan las invisibles, las que tienen dueño (dialogos), las
    tool windows (toasts, popovers) y las encapadas: FrameRev encapa la ventana
    mientras ajusta el zoom, y Windows no trae al frente una ventana encapada.
    De las que quedan, la mas grande. Devuelve el hwnd o None.
    """
    candidates = [
        w for w in windows
        if w["visible"] and not w["owned"] and not w["tool"] and not w["cloaked"] and w["area"] > 0
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda w: w["area"])["hwnd"]


def front_step(foreground_pid, own_pid, child_pid, child_alive, main_window):
    """Decide que hacer en cada vuelta del QTimer. Pura, para poder probarla.

    Devuelve "done" (FrameRev ya esta al frente), "user_left" (el usuario se
    fue a otra app: no se le roba el foco), "exited" (FrameRev se cerro),
    "raise" (Nuke esta al frente y la ventana ya existe) o "wait".
    """
    if foreground_pid == child_pid:
        return "done"
    if not child_alive:
        return "exited"
    # 0 = sin ventana de frente (transicion): no dice nada, se sigue esperando.
    if foreground_pid and foreground_pid != own_pid:
        return "user_left"
    if main_window is None:
        return "wait"
    # Solo Nuke, siendo el proceso del frente, puede ceder el foco.
    return "raise" if foreground_pid == own_pid else "wait"


def _win32():
    """Funciones de user32/dwmapi con sus tipos. None si no se pueden cargar."""
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        dwmapi.DwmGetWindowAttribute.argtypes = [
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
        ]
    except OSError:
        dwmapi = None
    return ctypes, wintypes, user32, dwmapi, enum_proc


def _window_pid(api, hwnd):
    ctypes, wintypes, user32 = api[0], api[1], api[2]
    if not hwnd:
        return 0
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _windows_of(api, pid):
    """Ventanas de nivel superior del proceso `pid`, en el formato de pick_main_window."""
    ctypes, wintypes, user32, dwmapi, enum_proc = api
    gw_owner, gwl_exstyle, ws_ex_toolwindow, dwmwa_cloaked = 4, -20, 0x00000080, 14
    found = []

    def collect(hwnd, _lparam):
        if _window_pid(api, hwnd) != pid:
            return True
        cloaked = ctypes.c_int(0)
        if dwmapi is not None:
            dwmapi.DwmGetWindowAttribute(hwnd, dwmwa_cloaked, ctypes.byref(cloaked),
                                         ctypes.sizeof(cloaked))
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        found.append({
            "hwnd": hwnd,
            "visible": bool(user32.IsWindowVisible(hwnd)),
            "owned": bool(user32.GetWindow(hwnd, gw_owner)),
            "tool": bool(user32.GetWindowLongW(hwnd, gwl_exstyle) & ws_ex_toolwindow),
            "cloaked": bool(cloaked.value),
            "area": max(0, rect.right - rect.left) * max(0, rect.bottom - rect.top),
        })
        return True

    user32.EnumWindows(enum_proc(collect), 0)
    return found


def bring_to_front_when_ready(process, log=None):
    """Espera la ventana de FrameRev sin bloquear Nuke y la trae al frente.

    `process` es el Popen de FrameRev; `log` recibe una linea de texto (el
    debug_print de quien llama). Fuera de Windows no hace nada.
    """
    log = log or (lambda _message: None)
    if not sys.platform.startswith("win"):
        return
    api = _win32()
    if api is None:
        log("Sin ctypes: FrameRev queda donde Windows lo ponga.")
        return
    user32 = api[2]
    # Primero el permiso: si Windows se lo respeta, FrameRev se activa solo.
    user32.AllowSetForegroundWindow(process.pid)
    try:
        from LGA_QtAdapter_ToolPack import QtCore
    except ImportError:
        log("Sin Qt: no se espera la ventana de FrameRev.")
        return

    own_pid = os.getpid()
    timer = QtCore.QTimer()
    timer.setInterval(FRONT_POLL_MS)
    started = time.time()
    state = {"raises": 0}

    def finish(reason):
        timer.stop()
        if timer in _FRONT_WATCHERS:
            _FRONT_WATCHERS.remove(timer)
        log("FrameRev al frente: {0} a los {1:.1f} s ({2} SetForegroundWindow)".format(
            reason, time.time() - started, state["raises"]))

    def tick():
        try:
            foreground_pid = _window_pid(api, user32.GetForegroundWindow())
            alive = process.poll() is None
            main_window = None
            if alive and foreground_pid != process.pid:
                main_window = pick_main_window(_windows_of(api, process.pid))
            action = front_step(foreground_pid, own_pid, process.pid, alive, main_window)
            if action not in ("raise", "wait"):
                finish(action)
            elif (time.time() - started) * 1000 > FRONT_TIMEOUT_MS:
                finish("timeout")
            elif action == "raise":
                state["raises"] += 1
                user32.SetForegroundWindow(main_window)
        except Exception as error:
            finish("error {0}".format(error))

    timer.timeout.connect(tick)
    _FRONT_WATCHERS.append(timer)
    timer.start()
