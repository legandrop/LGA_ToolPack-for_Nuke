import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import LGA_FrameRev_Front_ToolPack as front  # noqa: E402


def _window(hwnd, area=1000, visible=True, owned=False, tool=False, cloaked=False):
    return {"hwnd": hwnd, "visible": visible, "owned": owned, "tool": tool,
            "cloaked": cloaked, "area": area}


class FrameRevFrontTests(unittest.TestCase):
    """Traer FrameRev al frente: eleccion de ventana y decision de cada vuelta."""

    def test_pick_main_window(self):
        self.assertIsNone(front.pick_main_window([]))
        # El toast (tool), un dialogo (owned), una oculta y la encapada no cuentan.
        windows = [
            _window(1, area=50, tool=True),
            _window(2, area=900000, owned=True),
            _window(3, area=800000, visible=False),
            _window(4, area=700000, cloaked=True),
            _window(5, area=0),
        ]
        self.assertIsNone(front.pick_main_window(windows))
        windows.append(_window(6, area=400000))
        windows.append(_window(7, area=600000))
        self.assertEqual(front.pick_main_window(windows), 7)

    def test_front_step(self):
        own, child, other = 100, 200, 300
        step = front.front_step
        self.assertEqual(step(child, own, child, True, None), "done")
        self.assertEqual(step(own, own, child, False, None), "exited")
        self.assertEqual(step(other, own, child, True, 7), "user_left")
        self.assertEqual(step(own, own, child, True, None), "wait")
        self.assertEqual(step(own, own, child, True, 7), "raise")
        # Sin ventana de frente (transicion) no se fuerza nada.
        self.assertEqual(step(0, own, child, True, 7), "wait")

    @unittest.skipUnless(sys.platform.startswith("win"), "solo Windows")
    def test_win32_enumeration(self):
        """Solo lectura: enumera ventanas reales para validar los tipos de ctypes."""
        api = front._win32()
        self.assertIsNotNone(api)
        user32 = api[2]
        foreground_pid = front._window_pid(api, user32.GetForegroundWindow())
        self.assertIsInstance(foreground_pid, int)
        if foreground_pid:
            for window in front._windows_of(api, foreground_pid):
                self.assertEqual(set(window),
                                 {"hwnd", "visible", "owned", "tool", "cloaked", "area"})
        self.assertEqual(front._windows_of(api, os.getpid()), [])

    def test_gallery_hands_process_to_front(self):
        # La galeria importa nuke: se verifica sobre el fuente que pase el Popen.
        source = (Path(__file__).resolve().parents[1] / "py"
                  / "LGA_viewer_SnapShot_Gallery.py").read_text(encoding="utf-8")
        self.assertIn("proceso = subprocess.Popen(comando, **kwargs)", source)
        self.assertIn("bring_to_front_when_ready(proceso, debug_print)", source)


if __name__ == "__main__":
    unittest.main()
