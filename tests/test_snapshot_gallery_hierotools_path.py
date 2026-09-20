import unittest
from pathlib import Path


GALLERY_PATH = (
    Path(__file__).resolve().parents[1] / "py" / "LGA_viewer_SnapShot_Gallery.py"
)


class SnapshotGalleryHieroToolsPathTests(unittest.TestCase):
    def test_sharex_editor_uses_flow_rev_private_directory(self):
        source = GALLERY_PATH.read_text(encoding="utf-8")

        self.assertIn('"LGA_NKS_Flow_Rev_Panel_py"', source)
        self.assertNotIn('"LGA_NKS_Flow_Panel_py"', source)


if __name__ == "__main__":
    unittest.main()
