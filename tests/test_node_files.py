"""Pruebas del inventario de knobs de archivo (sin Nuke ni Qt)."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import LGA_NodeFiles as nf


# ---------------------------------------------------------------------------
#                          Nodos y knobs de mentira
# ---------------------------------------------------------------------------
class FakeFileKnob(object):
    """Un File_Knob de mentira. El check de tipo lo inyecta el test."""

    def __init__(self, value):
        self._value = value

    def getValue(self):
        return self._value


class FakeOtherKnob(object):
    """Un knob cualquiera que NO es de archivo."""

    def __init__(self, value=""):
        self._value = value

    def getValue(self):
        return self._value


class FakeNode(object):
    def __init__(self, node_class, name, knobs, children=None, parent=None):
        self._class = node_class
        self._name = name
        self._knobs = knobs
        self._children = children or []
        self._parent = parent
        for child in self._children:
            child._parent = self

    def Class(self):
        return self._class

    def name(self):
        return self._name

    def fullName(self):
        # Como en Nuke: el Root no prefija. Un Read suelto es "Read1" y uno
        # adentro de un Group es "Group1.Read1".
        if self._parent is None or self._parent.Class() == "Root":
            return self._name
        return "%s.%s" % (self._parent.fullName(), self._name)

    def knobs(self):
        return self._knobs

    def nodes(self):
        return self._children


def _is_file_knob(knob):
    return isinstance(knob, FakeFileKnob)


def _entries(nodes):
    return nf.entries_from_nodes(nodes, is_file_knob=_is_file_knob)


def _by_knob(entries, node_name, knob_name):
    for entry in entries:
        if entry["node_name"] == node_name and entry["knob"] == knob_name:
            return entry
    return None


# ---------------------------------------------------------------------------
#                                  Politica
# ---------------------------------------------------------------------------
class TestRoles(unittest.TestCase):
    def test_default_es_input(self):
        self.assertEqual(nf.role_for("Read", "file"), nf.ROLE_INPUT)
        self.assertEqual(nf.role_for("Read", "proxy"), nf.ROLE_INPUT)
        self.assertEqual(nf.role_for("OCIOFileTransform", "file"), nf.ROLE_INPUT)

    def test_los_que_escriben_son_output(self):
        self.assertEqual(nf.role_for("Write", "file"), nf.ROLE_OUTPUT)
        self.assertEqual(nf.role_for("Write", "proxy"), nf.ROLE_OUTPUT)
        self.assertEqual(nf.role_for("DeepWrite", "file"), nf.ROLE_OUTPUT)
        self.assertEqual(nf.role_for("WriteGeo", "file"), nf.ROLE_OUTPUT)

    def test_precomp_lee_su_nk_y_escribe_su_render(self):
        self.assertEqual(nf.role_for("Precomp", "file"), nf.ROLE_INPUT)
        self.assertEqual(nf.role_for("Precomp", "output"), nf.ROLE_OUTPUT)

    def test_copycat_e_inference(self):
        # El caso que motivo todo el modulo.
        self.assertEqual(nf.role_for("CopyCat", "dataDirectory"), nf.ROLE_WORKDIR)
        self.assertEqual(nf.role_for("CopyCat", "checkpointFile"), nf.ROLE_INPUT)
        self.assertEqual(nf.role_for("Inference", "modelFile"), nf.ROLE_INPUT)

    def test_el_kernel_de_blinkscript_es_tooling(self):
        # No es media del shot: vive en una carpeta de herramientas compartida.
        self.assertEqual(
            nf.role_for("BlinkScript", "kernelSourceFile"), nf.ROLE_TOOLING
        )

    def test_solo_dataDirectory_es_carpeta(self):
        self.assertTrue(nf.is_folder_knob("CopyCat", "dataDirectory"))
        self.assertFalse(nf.is_folder_knob("CopyCat", "checkpointFile"))
        self.assertFalse(nf.is_folder_knob("Inference", "modelFile"))
        self.assertFalse(nf.is_folder_knob("Read", "file"))


class TestExpresiones(unittest.TestCase):
    def test_detecta_tcl_y_python(self):
        self.assertTrue(nf.is_expression_value("[python {nuke.script_directory()}]"))
        self.assertTrue(nf.is_expression_value("[value root.name]/render.exr"))
        self.assertFalse(nf.is_expression_value("T:/shot/plate.%04d.exr"))
        self.assertFalse(nf.is_expression_value(""))


class TestRutas(unittest.TestCase):
    def test_absolutas_de_las_dos_plataformas(self):
        self.assertTrue(nf.is_absolute_path("T:/shot/plate.exr"))
        self.assertTrue(nf.is_absolute_path("T:\\shot\\plate.exr"))
        self.assertTrue(nf.is_absolute_path("//server/share/plate.exr"))
        self.assertTrue(nf.is_absolute_path("\\\\server\\share\\plate.exr"))
        self.assertTrue(nf.is_absolute_path("/Volumes/shot/plate.exr"))
        self.assertFalse(nf.is_absolute_path("../input/plate.exr"))
        self.assertFalse(nf.is_absolute_path(""))

    def test_relativo_cuenta_los_niveles(self):
        relativo, niveles = nf.to_relative(
            "T:/proj/shot/comp/plate.exr", "T:/proj/shot/comp"
        )
        self.assertEqual(relativo, "plate.exr")
        self.assertEqual(niveles, 0)

        relativo, niveles = nf.to_relative("T:/proj/input/plate.exr", "T:/proj/shot/comp")
        self.assertEqual(relativo, "../../input/plate.exr")
        self.assertEqual(niveles, 2)

    def test_otra_unidad_no_tiene_relativo(self):
        # Es el caso real del shot: los Reads en T: y el CopyCat en N:, que son
        # dos discos distintos.
        if os.name != "nt":
            self.skipTest("os.path.relpath solo falla entre unidades en Windows")
        relativo, niveles = nf.to_relative("N:/proj/plate.exr", "T:/proj/shot/comp")
        self.assertIsNone(relativo)
        self.assertEqual(niveles, 0)

    def test_resolve_against(self):
        self.assertEqual(
            nf.resolve_against("../input/plate.exr", "T:/proj/shot/comp"),
            "T:/proj/shot/input/plate.exr",
        )
        # Una absoluta vuelve igual, sin pegarle el ancla adelante.
        self.assertEqual(
            nf.resolve_against("N:/otro/plate.exr", "T:/proj/shot/comp"),
            "N:/otro/plate.exr",
        )
        self.assertEqual(nf.resolve_against("", "T:/proj"), "")


# ---------------------------------------------------------------------------
#                                 Inventario
# ---------------------------------------------------------------------------
class TestInventario(unittest.TestCase):
    def test_toma_todos_los_file_knob_y_ninguno_mas(self):
        nodo = FakeNode(
            "Read",
            "Read1",
            {
                "file": FakeFileKnob("T:/shot/plate.%04d.exr"),
                "proxy": FakeFileKnob("T:/shot/proxy.%04d.exr"),
                "first": FakeOtherKnob("1001"),
                "colorspace": FakeOtherKnob("sRGB"),
            },
        )
        entries = _entries([nodo])
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            sorted(entry["knob"] for entry in entries), ["file", "proxy"]
        )

    def test_copycat_e_inference_entran_sin_nombrar_la_clase(self):
        # El punto del modulo: no hay lista de clases que los habilite.
        copycat = FakeNode(
            "CopyCat",
            "CopyCat2",
            {
                "dataDirectory": FakeFileKnob("N:/shot/comp/2_prerenders/CopyCat/"),
                "checkpointFile": FakeFileKnob(
                    "N:/shot/comp/2_prerenders/CopyCat/Training_260909_112302.3331.cat"
                ),
                "epochs": FakeOtherKnob("80000"),
            },
        )
        inference = FakeNode(
            "Inference",
            "Inference1",
            {
                "modelFile": FakeFileKnob(
                    "N:/shot/comp/2_prerenders/CopyCat/Training_260909_112302.4723.cat"
                ),
            },
        )
        entries = _entries([copycat, inference])
        self.assertEqual(len(entries), 3)

        data_dir = _by_knob(entries, "CopyCat2", "dataDirectory")
        self.assertEqual(data_dir["role"], nf.ROLE_WORKDIR)
        self.assertTrue(data_dir["is_folder"])

        checkpoint = _by_knob(entries, "CopyCat2", "checkpointFile")
        self.assertEqual(checkpoint["role"], nf.ROLE_INPUT)
        self.assertFalse(checkpoint["is_folder"])

        modelo = _by_knob(entries, "Inference1", "modelFile")
        self.assertEqual(modelo["role"], nf.ROLE_INPUT)
        self.assertTrue(modelo["raw"].endswith(".4723.cat"))

    def test_vacios_y_expresiones_vienen_marcados_no_filtrados(self):
        nodo = FakeNode(
            "Write",
            "Write1",
            {
                "file": FakeFileKnob("[python {nuke.script_directory()}]/render.exr"),
                "proxy": FakeFileKnob(""),
            },
        )
        entries = _entries([nodo])
        self.assertEqual(len(entries), 2)
        self.assertTrue(_by_knob(entries, "Write1", "file")["is_expression"])
        self.assertEqual(_by_knob(entries, "Write1", "proxy")["raw"], "")
        # usable_entries es el que los saca.
        self.assertEqual(nf.usable_entries(entries), [])

    def test_root_nunca_entra(self):
        # project_directory es un File_Knob y convertirlo rompe el script.
        root = FakeNode(
            "Root",
            "root",
            {"project_directory": FakeFileKnob("[python {nuke.script_directory()}]")},
        )
        self.assertEqual(_entries([root]), [])

    def test_barras_invertidas_normalizadas(self):
        nodo = FakeNode("Read", "Read1", {"file": FakeFileKnob("T:\\shot\\plate.exr")})
        self.assertEqual(_entries([nodo])[0]["raw"], "T:/shot/plate.exr")

    def test_filtro_por_rol(self):
        nodos = [
            FakeNode("Read", "Read1", {"file": FakeFileKnob("T:/a.exr")}),
            FakeNode("Write", "Write1", {"file": FakeFileKnob("T:/b.exr")}),
            FakeNode(
                "CopyCat", "CopyCat1", {"dataDirectory": FakeFileKnob("T:/cc/")}
            ),
        ]
        entries = _entries(nodos)
        entradas = [e for e in entries if e["role"] == nf.ROLE_INPUT]
        salidas = [e for e in entries if e["role"] == nf.ROLE_OUTPUT]
        trabajo = [e for e in entries if e["role"] == nf.ROLE_WORKDIR]
        self.assertEqual([e["node_name"] for e in entradas], ["Read1"])
        self.assertEqual([e["node_name"] for e in salidas], ["Write1"])
        self.assertEqual([e["node_name"] for e in trabajo], ["CopyCat1"])


class TestBarrido(unittest.TestCase):
    def test_baja_a_los_group_y_anota_donde_vive_el_nodo(self):
        interno = FakeNode("Read", "Read1", {"file": FakeFileKnob("T:/a.exr")})
        grupo = FakeNode("Group", "Group1", {}, children=[interno])
        raiz = FakeNode("Root", "root", {}, children=[grupo])

        collected = []
        nf.walk_group(raiz, collected)
        self.assertIn(interno, collected)

        entries = _entries(collected)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["location"], "Group1")

    def test_un_ciclo_no_cuelga_ni_devuelve_una_lista_a_medias(self):
        # Nuke no puede producir ciclos, pero sin la guarda el RecursionError
        # se lo comia el except y el barrido devolvia una lista incompleta sin
        # avisar. Con la guarda, cada nodo aparece una sola vez.
        grupo1 = FakeNode("Group", "Group1", {})
        grupo2 = FakeNode("Group", "Group2", {}, children=[grupo1])
        grupo1._children = [grupo2, FakeNode("Read", "Read1", {"file": FakeFileKnob("T:/a.exr")})]
        raiz = FakeNode("Root", "root", {}, children=[grupo1])

        collected = []
        nf.walk_group(raiz, collected)
        nombres = [n.name() for n in collected]
        self.assertEqual(sorted(nombres), ["Group1", "Group2", "Read1"])

    def test_no_baja_a_precomp_ni_a_livegroup(self):
        # Sus nodos internos vienen de otro .nk: tocarlos aca no hace nada.
        interno = FakeNode("Read", "ReadInterno", {"file": FakeFileKnob("T:/a.exr")})
        precomp = FakeNode(
            "Precomp",
            "Precomp1",
            {"file": FakeFileKnob("T:/otro.nk")},
            children=[interno],
        )
        live = FakeNode(
            "LiveGroup",
            "LiveGroup1",
            {"file": FakeFileKnob("T:/live.nk")},
            children=[FakeNode("Read", "ReadLive", {"file": FakeFileKnob("T:/b.exr")})],
        )
        raiz = FakeNode("Root", "root", {}, children=[precomp, live])

        collected = []
        nf.walk_group(raiz, collected)
        nombres = [n.name() for n in collected]
        self.assertIn("Precomp1", nombres)
        self.assertIn("LiveGroup1", nombres)
        self.assertNotIn("ReadInterno", nombres)
        self.assertNotIn("ReadLive", nombres)


class TestAlcanceDeLaSeleccion(unittest.TestCase):
    """
    collect_entries con un nuke de mentira.

    Lo que se prueba es la regla de alcance: con seleccion se trabaja sobre
    ella, pero si lo seleccionado no aporta ningun knob de archivo -un Dot, un
    Backdrop- se cae al script entero, como hacia la lista de clases.
    """

    def setUp(self):
        self.read = FakeNode("Read", "Read1", {"file": FakeFileKnob("T:/a.exr")})
        self.grupo = FakeNode(
            "Group",
            "Group1",
            {},
            children=[FakeNode("Write", "Write1", {"file": FakeFileKnob("T:/b.exr")})],
        )
        self.dot = FakeNode("Dot", "Dot1", {})
        self.raiz = FakeNode(
            "Root", "root", {}, children=[self.read, self.grupo, self.dot]
        )

        self.nuke_falso = types.ModuleType("nuke")
        self.nuke_falso.File_Knob = FakeFileKnob
        self.nuke_falso.root = lambda: self.raiz
        self.nuke_falso.selectedNodes = lambda: self.seleccion
        self.seleccion = []
        self.anterior = sys.modules.get("nuke")
        sys.modules["nuke"] = self.nuke_falso
        # La clase File_Knob se cachea al primer uso: si queda la de mentira,
        # se la lleva puesta el test siguiente.
        nf.reset_cache()

    def tearDown(self):
        nf.reset_cache()
        if self.anterior is None:
            sys.modules.pop("nuke", None)
        else:
            sys.modules["nuke"] = self.anterior

    def test_sin_seleccion_recorre_todo(self):
        self.seleccion = []
        entries, from_selection = nf.collect_entries()
        self.assertFalse(from_selection)
        self.assertEqual(
            sorted(e["node_name"] for e in entries), ["Read1", "Write1"]
        )

    def test_con_seleccion_util_trabaja_solo_sobre_ella(self):
        self.seleccion = [self.read]
        entries, from_selection = nf.collect_entries()
        self.assertTrue(from_selection)
        self.assertEqual([e["node_name"] for e in entries], ["Read1"])

    def test_seleccionar_el_group_baja_a_sus_nodos(self):
        # Antes el Group no estaba en la lista de clases, asi que seleccionarlo
        # equivalia a no seleccionar nada y se procesaba el script entero.
        self.seleccion = [self.grupo]
        entries, from_selection = nf.collect_entries()
        self.assertTrue(from_selection)
        self.assertEqual([e["node_name"] for e in entries], ["Write1"])

    def test_seleccion_sin_knobs_de_archivo_cae_al_script_entero(self):
        self.seleccion = [self.dot]
        entries, from_selection = nf.collect_entries()
        self.assertFalse(from_selection)
        self.assertEqual(
            sorted(e["node_name"] for e in entries), ["Read1", "Write1"]
        )


if __name__ == "__main__":
    unittest.main()
