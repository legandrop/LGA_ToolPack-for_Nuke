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


NK_DIR = SHOT + "/Comp/1_projects"
NK = NK_DIR + "/comp_v008.nk"


def _estructura(shot=SHOT, nk_dir=NK_DIR, locations=None):
    return collect.analizar_estructura(
        shot, nk_dir, LOCATIONS if locations is None else locations
    )


class TestEstructura(unittest.TestCase):
    """
    Collect reproduce la estructura REAL del shot, no buckets por nombre.

    Es lo unico que hace que el script colectado resuelva adentro del collect:
    el shot folder y las locations se escriben relativas al .nk, asi que si el
    .nk no queda en su misma posicion relativa, resuelven al shot VIEJO. Con la
    estructura de buckets, un rescan del script colectado volvia a escanear el
    shot original (medido en la corrida del 2026-09-11).
    """

    def test_la_estructura_del_shot_de_ejemplo(self):
        e = _estructura()
        self.assertTrue(e.reproducible)
        self.assertEqual(e.nombre_shot, "ERSO_5076_0400_SUP")
        self.assertEqual(e.rel_nk, "Comp/1_projects")
        self.assertEqual(e.rel_externos, "_input")
        self.assertEqual(e.nombre_externos, "Input")

    def test_las_locations_quedan_con_su_ruta_real(self):
        e = _estructura()
        rutas = {nombre: rel for nombre, _abs, rel in e.internas}
        self.assertEqual(rutas["Input"], "_input")
        self.assertEqual(rutas["Assets"], "Comp/0_assets")
        self.assertEqual(rutas["Prerenders"], "Comp/2_prerenders")

    def test_la_mas_especifica_primero(self):
        e = _estructura(locations=LOCATIONS + [("Comp", SHOT + "/Comp")])
        self.assertEqual(e.internas[0][2], "Comp/2_prerenders")

    def test_shot_apagado_no_es_reproducible(self):
        e = _estructura(shot="")
        self.assertFalse(e.reproducible)
        self.assertIn("turned off", e.motivo)

    def test_shot_sin_nombre_no_es_reproducible(self):
        # La raiz de una unidad o de un UNC: sin nombre no hay carpeta de shot
        # que crear y todo caeria suelto en la carpeta elegida.
        for raiz in ("N:/", "N:", "//server/share"):
            self.assertFalse(_estructura(shot=raiz, nk_dir=raiz + "/Comp").reproducible)

    def test_nk_fuera_del_shot_no_es_reproducible(self):
        e = _estructura(nk_dir="D:/otro/lado")
        self.assertFalse(e.reproducible)
        self.assertIn("not inside", e.motivo)

    def test_location_fuera_del_shot_se_descarta_sin_reventar(self):
        # Una location puede ser una ruta absoluta a otra unidad: os.path.relpath
        # ahi lanza ValueError, y con la misma unidad devuelve una ruta con ".."
        # que se escapa del destino.
        locations = LOCATIONS + [
            ("Libreria", "T:/pipeline/shared"),
            ("Otra", "C:/fuera/del/shot"),
        ]
        e = _estructura(locations=locations)
        self.assertTrue(e.reproducible)
        self.assertNotIn("Libreria", [n for n, _a, _r in e.internas])
        self.assertNotIn("Otra", [n for n, _a, _r in e.internas])
        for _n, _a, rel in e.internas:
            self.assertNotIn("..", rel)

    def test_sin_location_input_cae_a_la_primera(self):
        locations = [("Plates", SHOT + "/_input"), ("Assets", SHOT + "/Comp/0_assets")]
        e = _estructura(locations=locations)
        self.assertEqual(e.nombre_externos, "Plates")

    def test_sin_ninguna_location_interna_usa_carpeta_propia(self):
        e = _estructura(locations=[("Libreria", "T:/pipeline/shared")])
        self.assertEqual(e.rel_externos, collect.CARPETA_EXTERNOS)
        self.assertEqual(e.nombre_externos, "")


class TestRaizYScript(unittest.TestCase):
    def test_se_le_cuelga_la_carpeta_del_shot(self):
        self.assertEqual(
            collect.raiz_de_collect("D:/entregas", "ERSO_5076_0400_SUP"),
            "D:/entregas/ERSO_5076_0400_SUP",
        )

    def test_si_ya_se_llama_como_el_shot_no_anida(self):
        self.assertEqual(
            collect.raiz_de_collect("D:/entregas/ERSO_5076_0400_SUP", "ERSO_5076_0400_SUP"),
            "D:/entregas/ERSO_5076_0400_SUP",
        )
        self.assertEqual(
            collect.raiz_de_collect("D:/entregas/erso_5076_0400_sup", "ERSO_5076_0400_SUP"),
            "D:/entregas/erso_5076_0400_sup",
        )

    def test_el_script_va_a_su_posicion_del_shot(self):
        e = _estructura()
        raiz = collect.raiz_de_collect("D:/entregas", e.nombre_shot)
        self.assertEqual(
            collect.destino_del_script(raiz, e, "comp_v008.nk"),
            "D:/entregas/ERSO_5076_0400_SUP/Comp/1_projects/comp_v008.nk",
        )

    def test_sin_estructura_el_script_va_a_la_raiz(self):
        e = _estructura(shot="")
        self.assertEqual(
            collect.destino_del_script("D:/entregas", e, "comp_v008.nk"),
            "D:/entregas/comp_v008.nk",
        )


class TestDestino(unittest.TestCase):
    """
    Que destinos sirven. Collect COPIA, no mueve.

    Un guard viejo prohibia el shot ENTERO y rechazaba un "Comp/collect" que no
    tiene ningun riesgo. Y desde que el destino reproduce la estructura, elegir
    la carpeta del .nk tampoco es peligroso: el script colectado aterriza dos
    niveles mas abajo. Lo unico que destruye algo es que el .nk colectado caiga
    exactamente sobre el original.
    """

    def _revisar(self, elegida):
        e = _estructura()
        raiz = collect.raiz_de_collect(elegida, e.nombre_shot)
        destino_nk = collect.destino_del_script(raiz, e, "comp_v008.nk")
        return collect.revisar_destino(raiz, destino_nk, NK, SHOT)

    def test_afuera_del_shot_sirve(self):
        self.assertEqual(self._revisar("D:/entregas"), (collect.DESTINO_OK, None))

    def test_la_carpeta_del_nk_ya_no_se_bloquea(self):
        # Es el caso que el usuario planteo: el script colectado cae en
        # <nk_dir>/<shot>/Comp/1_projects/, dos niveles mas abajo.
        self.assertEqual(self._revisar(NK_DIR)[0], collect.DESTINO_EN_EL_SHOT)

    def test_la_raiz_del_shot_actual_se_bloquea(self):
        # Se llama como el shot, asi que no anida y la estructura se reproduce
        # encima: el Save As pisaria el script original.
        self.assertEqual(self._revisar(SHOT)[0], collect.DESTINO_PISA_SCRIPT)

    def test_adentro_del_shot_avisa_pero_deja_seguir(self):
        self.assertEqual(
            self._revisar(SHOT + "/Comp/collect")[0], collect.DESTINO_EN_EL_SHOT
        )
        self.assertEqual(self._revisar(SHOT + "/Comp")[0], collect.DESTINO_EN_EL_SHOT)

    def test_un_alias_del_shot_tampoco_pasa_desapercibido(self):
        # Una letra de unidad mapeada al shot -un subst, una unidad de red- es
        # el mismo lugar con otro nombre, y la comparacion de texto no lo ve:
        # el collect se metia adentro del shot sin ni siquiera el aviso.
        import tempfile

        real = tempfile.mkdtemp(prefix="shot_alias_")
        try:
            adentro = os.path.join(real, "sub")
            os.makedirs(adentro, exist_ok=True)
            # Sin alias de por medio, el texto ya alcanza.
            self.assertTrue(collect._dentro_de_real(adentro, real))
            # Y con rutas que no se tocan, sigue diciendo que no.
            self.assertFalse(collect._dentro_de_real(tempfile.gettempdir(), adentro))
        finally:
            import shutil

            shutil.rmtree(real, ignore_errors=True)

    def test_sin_shot_ni_script_no_molesta(self):
        self.assertEqual(
            collect.revisar_destino("D:/x", "D:/x/a.nk", "", ""),
            (collect.DESTINO_OK, None),
        )


class TestRutaDelKnob(unittest.TestCase):
    """La ruta que queda escrita es relativa a la CARPETA DEL .nk."""

    def test_relativa_entre(self):
        self.assertEqual(
            collect.relativa_entre("Comp/1_projects", "_input/plate.mov"),
            "../../_input/plate.mov",
        )
        # Se cancela el prefijo comun: la ruta queda como la escribiria alguien.
        self.assertEqual(
            collect.relativa_entre("Comp/1_projects", "Comp/2_prerenders/x.exr"),
            "../2_prerenders/x.exr",
        )
        # Sin estructura el .nk esta en la raiz y la relativa es la sub-ruta.
        self.assertEqual(collect.relativa_entre("", "input/plate.mov"), "input/plate.mov")

    def test_el_plan_escribe_la_relativa_al_nk(self):
        e = _estructura()
        raiz = collect.raiz_de_collect("D:/entregas", e.nombre_shot)
        entradas = [
            entrada("file", SHOT + "/_input/plate.mov"),
            entrada("file", SHOT + "/Comp/2_prerenders/pre.%04d.exr", node="Read2"),
            entrada("file", SHOT + "/Comp/3_review/nota.mov", node="Read3"),
            entrada("file", "T:/afuera/gt/env.%04d.png", node="Read4"),
        ]
        plan, _ = collect.armar_plan(entradas, raiz, LOCATIONS, SHOT, estructura=e)
        self.assertEqual(
            [i["relativa"] for i in plan],
            [
                "../../_input/plate.mov",
                "../2_prerenders/pre.%04d.exr",
                "../3_review/nota.mov",
                "../../_input/gt/env.%04d.png",
            ],
        )

    def test_los_homonimos_de_afuera_siguen_sin_pisarse(self):
        # El borrador de esta propuesta usaba una formula fija de un segmento
        # para el bucket de externos, y eso reintroducia la perdida silenciosa
        # que _sin_colision existe para evitar.
        e = _estructura()
        raiz = collect.raiz_de_collect("D:/entregas", e.nombre_shot)
        entradas = [
            entrada("file", "T:/renders/take%03d/out/output/plate.exr" % i, node="R%d" % i)
            for i in range(150)
        ]
        plan, _ = collect.armar_plan(entradas, raiz, LOCATIONS, SHOT, estructura=e)
        self.assertEqual(len({i["destino"] for i in plan}), 150)


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

    def test_se_crea_el_esqueleto_del_shot_aunque_una_location_este_vacia(self):
        # Medido de punta a punta: sin esto, una location sin archivos no existe
        # en el destino y desde el script colectado resuelve a CERO carpetas, o
        # sea que el collect deja de ser un shot valido apenas alguna location
        # no tenga contenido, que es el caso normal.
        e = _estructura()
        raiz = collect.raiz_de_collect("D:/entregas", e.nombre_shot)
        plan, _ = collect.armar_plan(
            [entrada("file", SHOT + "/_input/plate.mov")], raiz, LOCATIONS, SHOT,
            estructura=e,
        )
        carpetas = collect.carpetas_a_crear(plan, raiz, e)
        # Las cuatro locations, salgan de donde salgan, mas la del .nk.
        esperadas = [raiz + "/" + rel for _n, _a, rel in e.internas]
        esperadas.append(raiz + "/" + e.rel_nk)
        for esperada in esperadas:
            self.assertIn(esperada, carpetas)
        self.assertEqual(len(esperadas), len(LOCATIONS) + 1)

    def test_sin_estructura_no_se_inventa_esqueleto(self):
        e = _estructura(shot="")
        plan, _ = collect.armar_plan(
            [entrada("file", "T:/x/plate.mov")], DESTINO, LOCATIONS, "", estructura=e
        )
        carpetas = collect.carpetas_a_crear(plan, DESTINO, e)
        self.assertTrue(all(c.startswith(DESTINO) for c in carpetas))
        self.assertNotIn(DESTINO + "/Comp/1_projects", carpetas)

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
