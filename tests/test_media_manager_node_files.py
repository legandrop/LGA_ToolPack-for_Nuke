"""
Pruebas de como el Media Manager elige el knob de cada fila (sin Nuke ni Qt).

Lo que se prueba vive en LGA_MediaManager_paths, que no importa ninguno de los
dos. El FileScanner solo le pasa self.read_node_info y su normalizador.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import LGA_MediaManager_paths as mm_paths
import LGA_NodeFiles as nf


def _normalizar(ruta):
    """El mismo normalize_path_for_comparison del FileScanner."""
    return (ruta or "").replace("\\", "/").lower()


def _info(knob, path, node_class="Read", role=nf.ROLE_INPUT, is_folder=False):
    return {
        "knob": knob,
        "path": path,
        "role": role,
        "is_folder": is_folder,
        "node_class": node_class,
    }


# El caso real que motivo el cambio: un CopyCat con sus dos knobs y un
# Inference apuntando a OTRO checkpoint de la misma carpeta.
CARPETA = "N:/VFX-ERSO/000/ERSO_5076_0400_SUP/Comp/2_prerenders/CopyCat/"
READ_NODE_INFO = {
    "Read1": [_info("file", "T:/proj/shot/comp/plate.%04d.exr")],
    "CopyCat2": [
        _info("dataDirectory", CARPETA, "CopyCat", nf.ROLE_WORKDIR, is_folder=True),
        _info("checkpointFile", CARPETA + "Training_260909_112302.3331.cat", "CopyCat"),
    ],
    "Inference1": [
        _info("modelFile", CARPETA + "Training_260909_112302.4723.cat", "Inference")
    ],
}


class TestKnobPorFila(unittest.TestCase):
    def test_nodo_con_un_solo_knob(self):
        info = mm_paths.knob_for_path(READ_NODE_INFO, "Inference1", "", _normalizar)
        self.assertEqual(info["knob"], "modelFile")
        self.assertEqual(info["node_class"], "Inference")

    def test_nodo_con_dos_knobs_se_elige_por_carpeta(self):
        # La fila del .cat tiene que resolver a checkpointFile, no al
        # dataDirectory, que es el primero de la lista.
        info = mm_paths.knob_for_path(
            READ_NODE_INFO,
            "CopyCat2",
            CARPETA + "Training_260909_112302.3331.cat",
            _normalizar,
        )
        self.assertEqual(info["knob"], "checkpointFile")

    def test_read_con_file_y_proxy_en_carpetas_distintas(self):
        info_read = {
            "Read1": [
                _info("file", "T:/proj/full/plate.%04d.exr"),
                _info("proxy", "T:/proj/proxy/plate.%04d.exr"),
            ]
        }
        elegido = mm_paths.knob_for_path(
            info_read, "Read1", "T:/proj/proxy/plate.####.exr", _normalizar
        )
        self.assertEqual(elegido["knob"], "proxy")

    def test_el_rango_de_frames_de_la_celda_no_rompe_la_eleccion(self):
        # La celda de una fila de secuencia dice "nombre.####.exr[1001-1100]",
        # y la ruta del knob nunca trae ese sufijo. Sin sacarlo, la comparacion
        # exacta fallaba SIEMPRE en secuencias y el desempate por carpeta
        # devolvia `file` cuando la fila era la del `proxy`: relinkear el proxy
        # reescribia el knob equivocado, sin aviso.
        info_read = {
            "Read1": [
                _info("file", "T:/proj/shot/comp/plate.%04d.exr"),
                _info("proxy", "T:/proj/shot/comp/plate_proxy.%04d.exr"),
            ]
        }
        elegido = mm_paths.knob_for_path(
            info_read,
            "Read1",
            "T:/proj/shot/comp/plate_proxy.####.exr[1001-1100]",
            _normalizar,
        )
        self.assertEqual(elegido["knob"], "proxy")

        elegido = mm_paths.knob_for_path(
            info_read,
            "Read1",
            "T:/proj/shot/comp/plate.####.exr[1001-1100]",
            _normalizar,
        )
        self.assertEqual(elegido["knob"], "file")

    def test_rango_negativo_y_corchete_en_el_nombre(self):
        info_read = {
            "Read1": [
                _info("file", "T:/proj/take[1]_a.%04d.exr"),
                _info("proxy", "T:/proj/take[1]_b.%04d.exr"),
            ]
        }
        elegido = mm_paths.knob_for_path(
            info_read, "Read1", "T:/proj/take[1]_b.####.exr[-10--1]", _normalizar
        )
        self.assertEqual(elegido["knob"], "proxy")

    def test_padding_distinto_no_rompe_la_eleccion(self):
        # El knob guarda "%05d" y la tabla muestra "#####": comparar por
        # carpeta es lo unico que sobrevive a esa diferencia.
        info_read = {"Read1": [_info("file", "T:/proj/full/plate.%05d.exr")]}
        elegido = mm_paths.knob_for_path(
            info_read, "Read1", "T:/proj/full/plate.#####.exr", _normalizar
        )
        self.assertEqual(elegido["knob"], "file")

    def test_nunca_devuelve_un_knob_de_carpeta(self):
        # Una fila de la tabla es un archivo. El dataDirectory tiene como ruta
        # la carpeta misma, asi que su dirname coincide con el de todo lo que
        # vive adentro y ganaba por carpeta al checkpointFile del mismo nodo.
        solo_carpeta = {
            "CopyCat2": [
                _info(
                    "dataDirectory", CARPETA, "CopyCat", nf.ROLE_WORKDIR, is_folder=True
                )
            ]
        }
        self.assertIsNone(
            mm_paths.knob_for_path(solo_carpeta, "CopyCat2", CARPETA + "x.cat", _normalizar)
        )
        # Y con los dos knobs, gana el archivo aunque el otro este primero.
        elegido = mm_paths.knob_for_path(
            READ_NODE_INFO, "CopyCat2", CARPETA + "otro.cat", _normalizar
        )
        self.assertEqual(elegido["knob"], "checkpointFile")

    def test_nodo_desconocido_da_none(self):
        self.assertIsNone(
            mm_paths.knob_for_path(READ_NODE_INFO, "NoExiste", "", _normalizar)
        )
        self.assertIsNone(mm_paths.knob_for_path({}, "Read1", "", _normalizar))
        self.assertIsNone(mm_paths.knob_for_path(None, "Read1", "", _normalizar))

    def test_barras_invertidas_en_la_fila(self):
        info = mm_paths.knob_for_path(
            READ_NODE_INFO,
            "CopyCat2",
            CARPETA.replace("/", "\\") + "Training_260909_112302.3331.cat",
            _normalizar,
        )
        self.assertEqual(info["knob"], "checkpointFile")


class TestCarpetasDeNodo(unittest.TestCase):
    def test_solo_los_knobs_de_carpeta(self):
        rutas = mm_paths.folder_paths(READ_NODE_INFO)
        self.assertEqual(rutas, {os.path.normpath(CARPETA)})

    def test_mapa_por_nodo_para_el_matching(self):
        carpetas = mm_paths.folder_paths_by_node(READ_NODE_INFO, _normalizar)
        # Una sola entrada, sin barra final, y con el nodo que la aporta.
        self.assertEqual(len(carpetas), 1)
        clave = list(carpetas)[0]
        self.assertFalse(clave.endswith("/"))
        self.assertEqual(carpetas[clave], ["CopyCat2"])

    def test_sin_carpetas_devuelve_vacio(self):
        solo_archivos = {"Read1": [_info("file", "T:/a.exr")]}
        self.assertEqual(mm_paths.folder_paths(solo_archivos), set())
        self.assertEqual(
            mm_paths.folder_paths_by_node(solo_archivos, _normalizar), {}
        )
        self.assertEqual(mm_paths.folder_paths_by_node(None, _normalizar), {})

    def test_el_matching_por_carpeta_agarra_lo_de_adentro(self):
        # Es la regla que aplica add_file_to_table con este mapa.
        carpetas = mm_paths.folder_paths_by_node(READ_NODE_INFO, _normalizar)
        clave = list(carpetas)[0]

        adentro = _normalizar(CARPETA + "Training_260909_112302.1.png").rsplit("/", 1)[0]
        self.assertTrue(adentro == clave or adentro.startswith(clave + "/"))

        afuera = _normalizar("N:/VFX-ERSO/000/ERSO_5076_0400_SUP/_input/plate.mov")
        afuera = afuera.rsplit("/", 1)[0]
        self.assertFalse(afuera == clave or afuera.startswith(clave + "/"))


class TestCierreDeTanda(unittest.TestCase):
    """
    Todo callback de _run_batch tiene que soltar la tanda en su primera linea.

    Quien pone _batch_worker en None es el CALLBACK, no _run_batch. Un callback
    que no lo hace deja operacion_en_curso() devolviendo "batch" para siempre:
    la barra entera apagada, y Copy to, Delete y Relink muertos en silencio por
    el resto de la sesion. Pasó con _on_collect_finished, que nació sin la
    linea, y el sintoma fue justo ese: apretar Copy to y que no pasara nada.

    Es una prueba sobre el FUENTE porque los tres metodos necesitan Qt y una
    ventana viva; lo que se cuida es la invariante, no la implementacion.
    """

    CALLBACKS = ("_on_copy_finished", "_on_delete_finished", "_on_collect_finished")

    def setUp(self):
        ruta = os.path.join(
            os.path.dirname(__file__), "..", "py", "LGA_MediaManager_FileScanner.py"
        )
        with open(ruta, encoding="utf-8") as handle:
            self.lineas = handle.read().splitlines()

    def _cuerpo(self, nombre):
        for indice, linea in enumerate(self.lineas):
            if linea.strip().startswith("def %s(" % nombre):
                return self.lineas[indice : indice + 16]
        self.fail("no se encontro %s" % nombre)

    def test_los_tres_sueltan_la_tanda(self):
        for nombre in self.CALLBACKS:
            cuerpo = self._cuerpo(nombre)
            self.assertTrue(
                any("self._batch_worker = None" in linea for linea in cuerpo),
                "%s no suelta _batch_worker en sus primeras lineas" % nombre,
            )

    def test_lo_sueltan_antes_de_cualquier_return(self):
        for nombre in self.CALLBACKS:
            cuerpo = self._cuerpo(nombre)
            suelta = next(
                i for i, l in enumerate(cuerpo) if "self._batch_worker = None" in l
            )
            returns = [i for i, l in enumerate(cuerpo) if l.strip().startswith("return")]
            if returns:
                self.assertLess(
                    suelta,
                    min(returns),
                    "%s puede volver sin haber soltado la tanda" % nombre,
                )


class TestExtensionDelCat(unittest.TestCase):
    """El .cat tiene que estar en las extensiones que escanea la tool."""

    def test_cat_en_sequence_extensions(self):
        ruta = os.path.join(
            os.path.dirname(__file__), "..", "py", "LGA_MediaManager_FileScanner.py"
        )
        with open(ruta, encoding="utf-8") as handle:
            fuente = handle.read()
        self.assertIn(
            'self.sequence_extensions = [".exr", ".tif", ".png", ".jpg", ".cat"]',
            fuente,
        )

    def test_el_parser_de_training_acepta_cat(self):
        # La otra mitad del arreglo: el parser ya lo aceptaba, la compuerta de
        # extensiones era la que no lo dejaba llegar.
        ruta = os.path.join(
            os.path.dirname(__file__), "..", "py", "LGA_MediaManager_utils.py"
        )
        with open(ruta, encoding="utf-8") as handle:
            fuente = handle.read()
        self.assertIn(r"(png|cat)$", fuente)


if __name__ == "__main__":
    unittest.main()
