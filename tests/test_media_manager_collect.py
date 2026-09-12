"""Pruebas del plan de Collect (sin Nuke, Qt ni disco)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import LGA_MediaManager_collect as collect


# El shot de la auditoria, con las locations de fabrica ya resueltas.
SHOT = "N:/VFX-ERSO/000/ERSO_5076_0400_SUP"
LOCATIONS = [
    ("Input", SHOT + "/_input"),
    ("Assets", SHOT + "/Comp/0_assets"),
    ("Prerenders", SHOT + "/Comp/2_prerenders"),
    ("Publish", SHOT + "/Comp/3_publish"),
]
DESTINO = "D:/entregas/ERSO_5076_0400"


def entrada(knob, path, role="input", node="Read1", clase="Read", carpeta=False,
            expresion=False):
    return {
        "node_name": node,
        "node_class": clase,
        "knob": knob,
        "role": role,
        "is_folder": carpeta,
        "is_expression": expresion,
        "path": path,
    }


def _uno(entradas, **kwargs):
    plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT, **kwargs)
    return plan[0] if plan else None


# ---------------------------------------------------------------------------
class TestClasificacion(unittest.TestCase):
    def test_cada_location_es_su_bucket(self):
        casos = [
            (SHOT + "/_input/plate.mov", "input", "plate.mov"),
            (SHOT + "/Comp/0_assets/logo.png", "assets", "logo.png"),
            (SHOT + "/Comp/2_prerenders/pre.exr", "prerenders", "pre.exr"),
            (SHOT + "/Comp/3_publish/final.exr", "publish", "final.exr"),
        ]
        for ruta, bucket, sub in casos:
            self.assertEqual(collect.clasificar(ruta, LOCATIONS, SHOT), (bucket, sub))

    def test_conserva_la_estructura_de_adentro(self):
        bucket, sub = collect.clasificar(
            SHOT + "/_input/ERSO_aPlate_v001/ERSO_aPlate_v001.%04d.exr",
            LOCATIONS,
            SHOT,
        )
        self.assertEqual(bucket, "input")
        self.assertEqual(sub, "ERSO_aPlate_v001/ERSO_aPlate_v001.%04d.exr")

    def test_gana_la_location_mas_especifica(self):
        # Prerenders vive adentro del shot; si ganara el shot, todo caeria ahi.
        locations = LOCATIONS + [("Comp", SHOT + "/Comp")]
        bucket, _ = collect.clasificar(
            SHOT + "/Comp/2_prerenders/x.exr", locations, SHOT
        )
        self.assertEqual(bucket, "prerenders")

    def test_dentro_del_shot_pero_fuera_de_toda_location(self):
        bucket, sub = collect.clasificar(
            SHOT + "/Comp/1_projects/comp_v01.psd", LOCATIONS, SHOT
        )
        self.assertEqual(bucket, "shot")
        self.assertEqual(sub, "Comp/1_projects/comp_v01.psd")

    def test_afuera_del_shot_conserva_la_carpeta_padre(self):
        # El caso real: los Reads del CopyCat viven en T:, otro disco.
        bucket, sub = collect.clasificar(
            "T:/VFX-ERSO/000/ERSO_5076_0400_SUP/Comp/2_prerenders/lga_faceLock/"
            "groundtruth/ERSO_envejecido.%04d.png",
            LOCATIONS,
            SHOT,
        )
        self.assertEqual(bucket, "outside")
        self.assertEqual(sub, "groundtruth/ERSO_envejecido.%04d.png")

    def test_comparacion_insensible_a_mayusculas_y_barras(self):
        bucket, _ = collect.clasificar(
            SHOT.lower().replace("/", "\\") + "\\_INPUT\\plate.mov", LOCATIONS, SHOT
        )
        self.assertEqual(bucket, "input")

    def test_nombre_de_bucket(self):
        self.assertEqual(collect.nombre_de_bucket("Prerenders"), "prerenders")
        self.assertEqual(collect.nombre_de_bucket("Mi Carpeta"), "mi_carpeta")
        self.assertEqual(collect.nombre_de_bucket("  "), "location")


class TestDestino(unittest.TestCase):
    """
    Que destinos sirven. Collect COPIA, no mueve.

    Hubo un guard que prohibia el shot ENTERO, y rechazaba un "Comp/collect"
    recien creado que no tiene ningun riesgo detras: el lugar natural para
    dejar una entrega. Lo unico que puede destruir algo es la carpeta del .nk.
    """

    NK_DIR = SHOT + "/Comp/1_projects"

    def _revisar(self, destino):
        return collect.revisar_destino(destino, self.NK_DIR, LOCATIONS)

    def test_una_carpeta_nueva_adentro_del_shot_sirve(self):
        self.assertEqual(self._revisar(SHOT + "/Comp/collect"), (collect.DESTINO_OK, None))

    def test_afuera_del_shot_sirve(self):
        self.assertEqual(self._revisar("D:/entregas/ERSO"), (collect.DESTINO_OK, None))

    def test_la_carpeta_del_nk_se_bloquea(self):
        # El paso final es un scriptSaveAs con el mismo nombre: pisaria el
        # script original y sus rutas absolutas.
        self.assertEqual(self._revisar(self.NK_DIR), (collect.DESTINO_ES_NK_DIR, None))

    def test_la_carpeta_del_nk_con_barra_o_backslash_tambien(self):
        self.assertEqual(
            self._revisar(self.NK_DIR + "/")[0], collect.DESTINO_ES_NK_DIR
        )
        self.assertEqual(
            self._revisar(self.NK_DIR.replace("/", "\\"))[0], collect.DESTINO_ES_NK_DIR
        )

    def test_adentro_de_una_scan_location_solo_avisa(self):
        veredicto, nombre = self._revisar(SHOT + "/Comp/2_prerenders/collect")
        self.assertEqual(veredicto, collect.DESTINO_EN_LOCATION)
        self.assertEqual(nombre, "Prerenders")

    def test_sin_locations_ni_nk_dir_no_molesta(self):
        self.assertEqual(
            collect.revisar_destino("D:/x", "", []), (collect.DESTINO_OK, None)
        )


class TestAcciones(unittest.TestCase):
    def test_input_se_copia(self):
        item = _uno([entrada("file", SHOT + "/_input/plate.mov")])
        self.assertEqual(item["accion"], collect.ACTION_COPY)

    def test_write_se_reapunta_pero_no_se_copia(self):
        item = _uno(
            [
                entrada(
                    "file",
                    SHOT + "/Comp/3_publish/comp_v01.%04d.exr",
                    role="output",
                    node="Write1",
                    clase="Write",
                )
            ]
        )
        self.assertEqual(item["accion"], collect.ACTION_REPOINT)
        self.assertEqual(item["relativa"], "publish/comp_v01.%04d.exr")
        self.assertEqual(collect.a_copiar([item]), [])
        self.assertEqual(len(collect.a_reapuntar([item])), 1)

    def test_datadirectory_se_crea_vacio_por_default(self):
        item = _uno(
            [
                entrada(
                    "dataDirectory",
                    SHOT + "/Comp/2_prerenders/CopyCat/",
                    role="workdir",
                    node="CopyCat2",
                    clase="CopyCat",
                    carpeta=True,
                )
            ]
        )
        self.assertEqual(item["accion"], collect.ACTION_MKDIR)
        # La barra final se conserva: el knob tiene que quedar como estaba.
        self.assertEqual(item["relativa"], "prerenders/CopyCat/")

    def test_datadirectory_se_copia_si_lo_piden(self):
        item = _uno(
            [
                entrada(
                    "dataDirectory",
                    SHOT + "/Comp/2_prerenders/CopyCat/",
                    role="workdir",
                    carpeta=True,
                )
            ],
            incluir_workdir=True,
        )
        self.assertEqual(item["accion"], collect.ACTION_COPY)

    def test_el_kernel_de_blinkscript_se_copia(self):
        # Paths to Relative lo deja destildado, pero un collect sin el kernel
        # deja un BlinkScript que no compila.
        item = _uno(
            [
                entrada(
                    "kernelSourceFile",
                    "T:/pipeline/blink_kernels/Sharpen.cpp",
                    role="tooling",
                    node="BlinkScript1",
                    clase="BlinkScript",
                )
            ]
        )
        self.assertEqual(item["accion"], collect.ACTION_COPY)
        self.assertEqual(item["bucket"], "outside")
        self.assertEqual(item["relativa"], "outside/blink_kernels/Sharpen.cpp")

    def test_expresiones_y_vacios_se_saltean(self):
        entradas = [
            entrada("file", "[python {nuke.script_directory()}]/o.exr", role="output"),
            entrada("proxy", ""),
        ]
        entradas[0]["is_expression"] = True
        plan, salteadas = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        self.assertEqual(plan, [])
        motivos = sorted(motivo for _, motivo in salteadas)
        self.assertEqual(motivos, [collect.SKIP_EMPTY, collect.SKIP_EXPRESSION])


class TestCasosDegenerados(unittest.TestCase):
    def test_knob_que_apunta_a_la_raiz_de_una_location(self):
        # Sin nombre de archivo la sub-ruta salia vacia y el knob quedaba
        # escrito como "input" a secas, apuntando a una carpeta.
        item = _uno([entrada("file", SHOT + "/_input")])
        self.assertEqual(item["relativa"], "input/_input")
        self.assertTrue(item["destino"].endswith("/input/_input"))

    def test_shot_apagado(self):
        # El shot folder se puede apagar en los ajustes: ahi shot_dir viene
        # vacio y todo lo que no cae en una location es outside.
        plan, _ = collect.armar_plan(
            [entrada("file", SHOT + "/Comp/1_projects/x.psd")],
            DESTINO,
            LOCATIONS,
            "",
        )
        self.assertEqual(plan[0]["bucket"], "outside")

    def test_sin_locations_ni_shot(self):
        plan, _ = collect.armar_plan(
            [entrada("file", SHOT + "/_input/plate.mov")], DESTINO, [], ""
        )
        self.assertEqual(plan[0]["bucket"], "outside")
        self.assertEqual(plan[0]["relativa"], "outside/_input/plate.mov")

    def test_location_vacia_o_sin_resolver_no_rompe(self):
        locations = [("Input", ""), ("Assets", None), ("Prerenders", SHOT + "/Comp/2_prerenders")]
        plan, _ = collect.armar_plan(
            [entrada("file", SHOT + "/Comp/2_prerenders/x.exr")], DESTINO, locations, SHOT
        )
        self.assertEqual(plan[0]["bucket"], "prerenders")

    def test_juntar_con_tramos_vacios_y_unc(self):
        self.assertEqual(collect._juntar("D:/a", "", "b"), "D:/a/b")
        self.assertEqual(collect._juntar("//nas/share", "input", "p.mov"),
                         "//nas/share/input/p.mov")
        self.assertEqual(collect._juntar("//nas/share/", "", ""), "//nas/share")


class TestRutasRelativas(unittest.TestCase):
    def test_la_relativa_se_calcula_contra_la_raiz_del_collect(self):
        # Es el punto del modulo: la relativa NO se calcula contra la carpeta
        # vieja, porque el .nk se va a guardar en la raiz del collect.
        item = _uno([entrada("file", SHOT + "/_input/plate.mov")])
        self.assertEqual(item["relativa"], "input/plate.mov")
        self.assertEqual(item["destino"], DESTINO + "/input/plate.mov")

    def test_la_secuencia_conserva_el_token_de_frame(self):
        item = _uno([entrada("file", SHOT + "/_input/pl/pl.%04d.exr")])
        self.assertEqual(item["relativa"], "input/pl/pl.%04d.exr")
        self.assertTrue(item["is_sequence"])

    def test_el_inference_apuntando_afuera(self):
        # El caso que motivo todo: un .cat que vive fuera del shot.
        item = _uno(
            [
                entrada(
                    "modelFile",
                    "T:/modelos/faceLock/Training_260909_112302.4723.cat",
                    node="Inference1",
                    clase="Inference",
                )
            ]
        )
        self.assertEqual(item["bucket"], "outside")
        self.assertEqual(
            item["relativa"], "outside/faceLock/Training_260909_112302.4723.cat"
        )
        self.assertEqual(item["accion"], collect.ACTION_COPY)


class TestColisiones(unittest.TestCase):
    def test_dos_archivos_distintos_con_el_mismo_nombre_no_se_pisan(self):
        entradas = [
            entrada("file", "T:/a/pares/plate.exr", node="Read1"),
            entrada("file", "T:/b/pares/plate.exr", node="Read2"),
        ]
        plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        destinos = [item["destino"] for item in plan]
        self.assertEqual(len(set(destinos)), 2, destinos)

    def test_el_mismo_archivo_desde_dos_nodos_va_a_un_solo_destino(self):
        # Dos Reads sobre la misma media no tienen que duplicar el archivo.
        entradas = [
            entrada("file", SHOT + "/_input/plate.mov", node="Read1"),
            entrada("file", SHOT + "/_input/plate.mov", node="Read2"),
        ]
        plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        self.assertEqual(len({item["destino"] for item in plan}), 1)
        self.assertEqual(len(plan), 2)

    def test_ciento_cincuenta_homonimos_profundos(self):
        # El desempate numeraba la carpeta con un range acotado y, agotado,
        # devolvia la sub-ruta original SIN registrarla: dos origenes distintos
        # caian en el mismo destino, uno solo se copiaba y el otro no aparecia
        # ni entre los errores. Un archivo que se perdia con un resumen que
        # decia que salio todo bien.
        entradas = [
            entrada("file", "T:/renders/take%03d/out/output/plate.exr" % i, node="R%d" % i)
            for i in range(150)
        ]
        plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        destinos = [item["destino"] for item in plan]
        self.assertEqual(len(set(destinos)), 150, "hay destinos repetidos")

    def test_tres_homonimos(self):
        entradas = [
            entrada("file", "T:/a/pares/plate.exr", node="Read1"),
            entrada("file", "T:/b/pares/plate.exr", node="Read2"),
            entrada("file", "T:/c/pares/plate.exr", node="Read3"),
        ]
        plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        destinos = [item["destino"] for item in plan]
        self.assertEqual(len(set(destinos)), 3, destinos)


class TestArchivosReales(unittest.TestCase):
    """De la ruta del knob a los archivos que hay en disco."""

    def setUp(self):
        self.disco = {
            SHOT + "/_input/pl": [
                "pl.1001.exr",
                "pl.1002.exr",
                "pl.1003.exr",
                "notas.txt",
                "pl_v01.exr",
            ]
        }
        self.listar = lambda carpeta: self.disco.get(
            collect.con_barras(carpeta).rstrip("/"), []
        )

    def _plan(self, path, **kwargs):
        return _uno([entrada("file", path, **kwargs)])

    def test_secuencia_con_porcentaje(self):
        item = self._plan(SHOT + "/_input/pl/pl.%04d.exr")
        pares = collect.archivos_de(item, listar=self.listar)
        self.assertEqual(len(pares), 3)
        self.assertEqual(pares[0][0], SHOT + "/_input/pl/pl.1001.exr")
        self.assertEqual(pares[0][1], DESTINO + "/input/pl/pl.1001.exr")

    def test_secuencia_con_almohadillas(self):
        item = self._plan(SHOT + "/_input/pl/pl.####.exr")
        pares = collect.archivos_de(item, listar=self.listar)
        self.assertEqual(len(pares), 3)

    def test_no_se_lleva_lo_que_no_es_de_la_secuencia(self):
        item = self._plan(SHOT + "/_input/pl/pl.%04d.exr")
        nombres = [os.path.basename(o) for o, _ in collect.archivos_de(item, listar=self.listar)]
        self.assertNotIn("notas.txt", nombres)
        self.assertNotIn("pl_v01.exr", nombres)

    def test_padding_mayor_al_declarado(self):
        # Nuke escribe "%04d" y en disco puede haber cinco digitos.
        self.disco[SHOT + "/_input/pl"] = ["pl.10001.exr", "pl.10002.exr"]
        item = self._plan(SHOT + "/_input/pl/pl.%04d.exr")
        self.assertEqual(len(collect.archivos_de(item, listar=self.listar)), 2)

    def test_version_en_el_nombre_no_se_confunde_con_el_frame(self):
        # El grupo de almohadillas del frame es el ULTIMO.
        expresion = collect._regex_de_secuencia("sh010_v###_####.exr")
        self.assertTrue(expresion.match("sh010_v###_1001.exr"))

    def test_dos_grupos_del_MISMO_largo(self):
        # Solo el ULTIMO grupo es el frame; los anteriores son texto literal
        # del nombre en disco, que es la misma regla que expand_sequence.
        # Con str.replace el sustituido era el de la IZQUIERDA y el del frame
        # quedaba literal en el regex, asi que con dos grupos de igual largo
        # la secuencia entera no matcheaba ni un archivo: el collect la daba
        # por inexistente en disco y el cartel decia que no habia nada que
        # copiar. Con largos distintos el bug no se veia, y por eso el test
        # que ya existia no lo agarraba.
        self.disco[SHOT + "/_input/pl"] = [
            "sh010_v####_1001.exr",
            "sh010_v####_1002.exr",
            "sh010_v####_1003.exr",
        ]
        item = self._plan(SHOT + "/_input/pl/sh010_v####_####.exr")
        self.assertEqual(len(collect.archivos_de(item, listar=self.listar)), 3)

    def test_dos_tokens_de_porcentaje_del_mismo_largo(self):
        self.disco[SHOT + "/_input/pl"] = [
            "sh010_v%04d_1001.exr",
            "sh010_v%04d_1002.exr",
        ]
        item = self._plan(SHOT + "/_input/pl/sh010_v%04d_%04d.exr")
        self.assertEqual(len(collect.archivos_de(item, listar=self.listar)), 2)

    def test_caracteres_especiales_de_regex_en_el_nombre(self):
        self.disco[SHOT + "/_input/pl"] = ["take(1)+a.1001.exr", "take(1)+a.1002.exr"]
        item = self._plan(SHOT + "/_input/pl/take(1)+a.%04d.exr")
        self.assertEqual(len(collect.archivos_de(item, listar=self.listar)), 2)

    def test_archivo_suelto(self):
        item = self._plan(SHOT + "/_input/plate.mov")
        self.assertEqual(
            collect.archivos_de(item, listar=self.listar),
            [(SHOT + "/_input/plate.mov", DESTINO + "/input/plate.mov")],
        )

    def test_carpeta_que_no_se_copia_no_da_archivos(self):
        item = _uno(
            [
                entrada(
                    "dataDirectory",
                    SHOT + "/Comp/2_prerenders/CopyCat/",
                    role="workdir",
                    carpeta=True,
                )
            ]
        )
        self.assertEqual(collect.archivos_de(item), [])

    def test_carpeta_que_si_se_copia_se_camina_entera(self):
        item = _uno(
            [
                entrada(
                    "dataDirectory",
                    SHOT + "/Comp/2_prerenders/CopyCat/",
                    role="workdir",
                    carpeta=True,
                )
            ],
            incluir_workdir=True,
        )
        base = SHOT + "/Comp/2_prerenders/CopyCat"
        caminar = lambda raiz: [
            (base, ["sub"], ["Training.3331.cat"]),
            (base + "/sub", [], ["extra.png"]),
        ]
        pares = collect.archivos_de(item, caminar=caminar)
        self.assertEqual(
            pares,
            [
                (base + "/Training.3331.cat", DESTINO + "/prerenders/CopyCat/Training.3331.cat"),
                (base + "/sub/extra.png", DESTINO + "/prerenders/CopyCat/sub/extra.png"),
            ],
        )

    def test_carpeta_ilegible_no_revienta(self):
        def explota(_carpeta):
            raise OSError("sin permiso")

        item = self._plan(SHOT + "/_input/pl/pl.%04d.exr")
        self.assertEqual(collect.archivos_de(item, listar=explota), [])


class TestResumen(unittest.TestCase):
    def test_cuenta_por_bucket_y_sin_buckets_vacios(self):
        entradas = [
            entrada("file", SHOT + "/_input/plate.mov"),
            entrada("file", SHOT + "/_input/otra.mov", node="Read2"),
            entrada("file", "T:/afuera/x.exr", node="Read3"),
        ]
        plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        self.assertEqual(collect.buckets_del_plan(plan), {"input": 2, "outside": 1})
        self.assertNotIn("assets", collect.buckets_del_plan(plan))

    def test_carpetas_a_crear_incluye_el_workdir_vacio(self):
        entradas = [
            entrada("file", SHOT + "/_input/pl/pl.%04d.exr"),
            entrada(
                "dataDirectory",
                SHOT + "/Comp/2_prerenders/CopyCat/",
                role="workdir",
                carpeta=True,
            ),
        ]
        plan, _ = collect.armar_plan(entradas, DESTINO, LOCATIONS, SHOT)
        carpetas = collect.carpetas_a_crear(plan)
        self.assertIn(DESTINO + "/input/pl", carpetas)
        self.assertIn(DESTINO + "/prerenders/CopyCat", carpetas)


if __name__ == "__main__":
    unittest.main()
