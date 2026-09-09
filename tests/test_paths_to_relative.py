"""
Pruebas de armado de filas de Paths to Relative, sin Nuke ni Qt.

El modulo importa nuke y el adapter de Qt en el tope, asi que los dos se
stubbean como en la receta de docs/Docu_UI_Style.md. Lo que se prueba es
build_rows, que es lo que cambio al pasar el barrido a LGA_NodeFiles.
"""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))


# ---------------------------------------------------------------------------
#                            Stubs de nuke y Qt
# ---------------------------------------------------------------------------
def _install_stubs():
    """Deja nuke y el adapter de Qt en sys.modules antes del import real."""

    class _AnyModule(types.ModuleType):
        """Devuelve una clase vacia para cualquier atributo que le pidan."""

        def __getattr__(self, name):
            clase = type(str(name), (object,), {})
            setattr(self, name, clase)
            return clase

    if "nuke" not in sys.modules:
        nuke = _AnyModule("nuke")
        sys.modules["nuke"] = nuke

    if "LGA_QtAdapter_ToolPack" not in sys.modules:
        adapter = types.ModuleType("LGA_QtAdapter_ToolPack")
        adapter.QtWidgets = _AnyModule("QtWidgets")
        adapter.QtGui = _AnyModule("QtGui")
        adapter.QtCore = _AnyModule("QtCore")
        sys.modules["LGA_QtAdapter_ToolPack"] = adapter


_install_stubs()

import LGA_NodeFiles as nf  # noqa: E402
import LGA_RnW_PathsToRelative as ptr  # noqa: E402


# ---------------------------------------------------------------------------
#                                  Helpers
# ---------------------------------------------------------------------------
ANCHOR = "T:/proj/shot/comp"


def entry(node_class, node_name, knob, raw, location="Root"):
    """Una entrada del inventario, armada a mano como la devuelve el modulo."""
    return {
        "node": object(),
        "node_name": node_name,
        "node_class": node_class,
        "knob": knob,
        "raw": raw,
        "role": nf.role_for(node_class, knob),
        "is_folder": nf.is_folder_knob(node_class, knob),
        "is_expression": nf.is_expression_value(raw),
        "location": location,
    }


def _one(entries):
    rows, _ = ptr.build_rows(entries, ANCHOR)
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
class TestFilasQueYaFuncionaban(unittest.TestCase):
    """Lo que la tool hacia antes del cambio tiene que seguir igual."""

    def test_read_absoluto_se_convierte(self):
        fila = _one([entry("Read", "Read1", "file", "T:/proj/input/plate.%04d.exr")])
        self.assertEqual(fila["relative"], "../../input/plate.%04d.exr")
        self.assertEqual(fila["up_levels"], 2)
        self.assertEqual(fila["status"], ptr.STATUS_CONVERT)

    def test_muchos_niveles_se_marcan_deep(self):
        fila = _one([entry("Read", "Read1", "file", "T:/otro/lado/plate.exr")])
        self.assertEqual(fila["status"], ptr.STATUS_DEEP)
        self.assertGreaterEqual(fila["up_levels"], ptr.DEEP_LEVEL_WARNING)

    def test_expresion_vacio_y_relativo_no_hacen_fila(self):
        entradas = [
            entry("Write", "Write1", "file", "[python {nuke.script_directory()}]/o.exr"),
            entry("Read", "Read2", "file", ""),
            entry("Read", "Read3", "file", "../input/plate.exr"),
        ]
        filas, skipped = ptr.build_rows(entradas, ANCHOR)
        self.assertEqual(filas, [])
        self.assertEqual(skipped[ptr.SKIP_EXPRESSION], 1)
        self.assertEqual(skipped[ptr.SKIP_EMPTY], 1)
        self.assertEqual(skipped[ptr.SKIP_RELATIVE], 1)

    @unittest.skipUnless(os.name == "nt", "relpath solo falla entre unidades en Windows")
    def test_otra_unidad_queda_bloqueada(self):
        # El caso del shot real: Reads en T: y CopyCat en N:.
        fila = _one([entry("Read", "Read1", "file", "N:/otro/plate.exr")])
        self.assertEqual(fila["status"], ptr.STATUS_BLOCKED)
        self.assertIsNone(fila["relative"])


class TestLoQueEntraAhora(unittest.TestCase):
    """CopyCat e Inference: la lista de clases los dejaba afuera."""

    def test_inference_model_file(self):
        fila = _one(
            [
                entry(
                    "Inference",
                    "Inference1",
                    "modelFile",
                    "T:/proj/shot/comp/2_prerenders/CopyCat/Training.4723.cat",
                )
            ]
        )
        self.assertIsNotNone(fila)
        self.assertEqual(fila["relative"], "2_prerenders/CopyCat/Training.4723.cat")
        self.assertEqual(fila["role"], nf.ROLE_INPUT)
        self.assertEqual(fila["node_class"], "Inference")

    def test_copycat_checkpoint(self):
        fila = _one(
            [
                entry(
                    "CopyCat",
                    "CopyCat2",
                    "checkpointFile",
                    "T:/proj/shot/comp/2_prerenders/CopyCat/Training.3331.cat",
                )
            ]
        )
        self.assertEqual(fila["relative"], "2_prerenders/CopyCat/Training.3331.cat")
        self.assertFalse(fila["is_folder"])

    def test_data_directory_conserva_la_barra_final(self):
        # relpath se come la barra; el valor escrito tiene que ser el mismo que
        # habia, solo que relativo.
        fila = _one(
            [
                entry(
                    "CopyCat",
                    "CopyCat2",
                    "dataDirectory",
                    "T:/proj/shot/comp/2_prerenders/CopyCat/",
                )
            ]
        )
        self.assertEqual(fila["relative"], "2_prerenders/CopyCat/")
        self.assertTrue(fila["is_folder"])
        self.assertEqual(fila["role"], nf.ROLE_WORKDIR)

    def test_sin_barra_final_no_se_le_agrega_una(self):
        fila = _one(
            [
                entry(
                    "CopyCat",
                    "CopyCat2",
                    "dataDirectory",
                    "T:/proj/shot/comp/2_prerenders/CopyCat",
                )
            ]
        )
        self.assertEqual(fila["relative"], "2_prerenders/CopyCat")

    def test_el_rol_viaja_a_la_fila(self):
        filas, _ = ptr.build_rows(
            [
                entry("Read", "Read1", "file", "T:/proj/shot/comp/a.exr"),
                entry("Write", "Write1", "file", "T:/proj/shot/comp/b.exr"),
                entry("CopyCat", "CopyCat1", "dataDirectory", "T:/proj/shot/comp/cc/"),
            ],
            ANCHOR,
        )
        self.assertEqual(
            [f["role"] for f in filas],
            [nf.ROLE_INPUT, nf.ROLE_OUTPUT, nf.ROLE_WORKDIR],
        )
        # Y hay tooltip para los tres, que es lo que muestra la columna Knob.
        for fila in filas:
            self.assertIn(fila["role"], ptr.KNOB_ROLE_TOOLTIP)


if __name__ == "__main__":
    unittest.main()
