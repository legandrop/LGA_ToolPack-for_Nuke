import unittest
from pathlib import Path


GALLERY_PATH = (
    Path(__file__).resolve().parents[1] / "py" / "LGA_viewer_SnapShot_Gallery.py"
)


class SnapshotGalleryFrameRevTests(unittest.TestCase):
    """El Shift+click de la galeria abre FrameRev y ya no depende de HieroTools.

    El modulo importa nuke, asi que se verifica sobre el fuente.
    """

    def setUp(self):
        self.source = GALLERY_PATH.read_text(encoding="utf-8")

    def test_uses_framerev_edit_image(self):
        # --edit-image abre una ventana aparte y no borra el archivo; lanzar el
        # exe a secas con FrameRev abierto arrancaria una segunda copia.
        self.assertIn('"--edit-image"', self.source)
        self.assertIn('"FrameRev.json"', self.source)
        self.assertIn("FRAMEREV_MIN_VERSION = (0, 265)", self.source)

    def test_no_longer_depends_on_hierotools_sharex(self):
        # El header guarda el historial con los nombres viejos: se mira solo el codigo.
        code = self.source.split('"""', 2)[2]
        self.assertNotIn("ShareX_ImageEditor_LGA", code)
        self.assertNotIn("LGA_NKS_Flow_Rev_Panel_py", code)


if __name__ == "__main__":
    unittest.main()
