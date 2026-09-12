"""
Pruebas de las carpetas recordadas de los browsers (sin Nuke ni Qt).

Dos piezas: el helper que sube hasta la primera carpeta que existe, y el
archivito donde se guarda lo ultimo que eligio el usuario.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import LGA_MediaManager_config as mm_config
import LGA_MediaManager_paths as mm_paths


class TestPrimeraCarpetaExistente(unittest.TestCase):
    """
    La ruta guardada puede ser de hace meses: el proyecto se archivo, la
    unidad no esta montada, la carpeta se borro. Sin esto el browser abre en
    cualquier lado.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="recientes_")
        self.hondo = os.path.join(self.tmp, "proyecto", "shot", "comp")
        os.makedirs(self.hondo)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_si_existe_la_devuelve_tal_cual(self):
        self.assertEqual(
            mm_paths.primera_carpeta_existente(self.hondo),
            self.hondo.replace("\\", "/"),
        )

    def test_sube_hasta_la_primera_que_existe(self):
        borrada = os.path.join(self.hondo, "ya_no_esta", "ni_esta")
        self.assertEqual(
            mm_paths.primera_carpeta_existente(borrada),
            self.hondo.replace("\\", "/"),
        )

    def test_sube_varios_niveles(self):
        shutil.rmtree(os.path.join(self.tmp, "proyecto", "shot"))
        esperado = os.path.join(self.tmp, "proyecto").replace("\\", "/")
        self.assertEqual(mm_paths.primera_carpeta_existente(self.hondo), esperado)

    def test_barras_invertidas_y_barra_final(self):
        self.assertEqual(
            mm_paths.primera_carpeta_existente(self.hondo.replace("/", "\\") + "\\"),
            self.hondo.replace("\\", "/"),
        )

    def test_vacio_o_none(self):
        self.assertEqual(mm_paths.primera_carpeta_existente(""), "")
        self.assertEqual(mm_paths.primera_carpeta_existente(None), "")

    def test_una_unidad_que_no_existe_no_cuelga(self):
        # os.path.dirname de una raiz devuelve la raiz misma: sin el tope, el
        # bucle no termina nunca.
        self.assertEqual(
            mm_paths.primera_carpeta_existente("Z:/no/existe/nada"), ""
        )

    def test_un_archivo_no_cuenta_como_carpeta(self):
        archivo = os.path.join(self.hondo, "algo.nk")
        with open(archivo, "w", encoding="utf-8") as handle:
            handle.write("x")
        self.assertEqual(
            mm_paths.primera_carpeta_existente(archivo),
            self.hondo.replace("\\", "/"),
        )


class TestArchivoDeRecientes(unittest.TestCase):
    """El archivito propio, con la carpeta de config redirigida al scratch."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="recientes_ini_")
        self.original = mm_config.get_user_ini_path
        destino = os.path.join(self.tmp, mm_config.USER_INI_NAME)
        mm_config.get_user_ini_path = lambda create_dir=False: destino

    def tearDown(self):
        mm_config.get_user_ini_path = self.original
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sin_archivo_devuelve_vacio(self):
        self.assertEqual(mm_config.load_recientes(), {})

    def test_ida_y_vuelta(self):
        self.assertTrue(
            mm_config.save_reciente(mm_config.RECIENTE_RELINK, "T:/proj/shot")
        )
        self.assertEqual(
            mm_config.load_recientes()[mm_config.RECIENTE_RELINK], "T:/proj/shot"
        )

    def test_una_clave_no_pisa_la_otra(self):
        mm_config.save_reciente(mm_config.RECIENTE_RELINK, "T:/uno")
        mm_config.save_reciente(mm_config.RECIENTE_COLLECT, "T:/dos")
        guardadas = mm_config.load_recientes()
        self.assertEqual(guardadas[mm_config.RECIENTE_RELINK], "T:/uno")
        self.assertEqual(guardadas[mm_config.RECIENTE_COLLECT], "T:/dos")

    def test_se_reescribe_la_misma_clave(self):
        mm_config.save_reciente(mm_config.RECIENTE_RELINK, "T:/viejo")
        mm_config.save_reciente(mm_config.RECIENTE_RELINK, "T:/nuevo")
        self.assertEqual(
            mm_config.load_recientes()[mm_config.RECIENTE_RELINK], "T:/nuevo"
        )

    def test_las_barras_se_guardan_normalizadas(self):
        mm_config.save_reciente(mm_config.RECIENTE_COLLECT, "T:\\proj\\entregas")
        self.assertEqual(
            mm_config.load_recientes()[mm_config.RECIENTE_COLLECT],
            "T:/proj/entregas",
        )

    def test_una_ruta_vacia_no_se_guarda(self):
        self.assertFalse(mm_config.save_reciente(mm_config.RECIENTE_RELINK, ""))
        self.assertFalse(mm_config.save_reciente(mm_config.RECIENTE_RELINK, "   "))
        self.assertEqual(mm_config.load_recientes(), {})

    def test_una_ruta_con_porcentaje_no_envenena_el_archivo(self):
        # Para configparser un "%" suelto empieza una sustitucion, y en una
        # RUTA no es raro: una carpeta "100%_final", o el "%04d" de una
        # secuencia de Nuke. Sin interpolation=None, guardar UNA sola ruta asi
        # rompia load_recientes Y save_reciente -que relee para mergear- y con
        # eso se caian Relink y Collect enteros, no solo la memoria.
        self.assertTrue(
            mm_config.save_reciente(mm_config.RECIENTE_COLLECT, "T:/proj/100%_final")
        )
        self.assertEqual(
            mm_config.load_recientes()[mm_config.RECIENTE_COLLECT],
            "T:/proj/100%_final",
        )
        # Y la otra clave se sigue pudiendo guardar encima.
        self.assertTrue(
            mm_config.save_reciente(mm_config.RECIENTE_RELINK, "T:/proj/sh_%04d/comp")
        )
        guardadas = mm_config.load_recientes()
        self.assertEqual(guardadas[mm_config.RECIENTE_RELINK], "T:/proj/sh_%04d/comp")
        self.assertEqual(guardadas[mm_config.RECIENTE_COLLECT], "T:/proj/100%_final")

    def test_un_archivo_con_basura_no_revienta(self):
        ruta = mm_config.get_recientes_path(create_dir=True)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as handle:
            handle.write("esto no es un ini\n[[[\n")
        self.assertEqual(mm_config.load_recientes(), {})

    def test_no_toca_el_ini_de_configuracion(self):
        # Es la razon de que viva aparte: la ventana de ajustes arma el dict
        # que guarda desde cero, asi que una clave nueva en el .ini se perderia
        # el dia que el usuario toque Save.
        mm_config.save_reciente(mm_config.RECIENTE_RELINK, "T:/proj")
        self.assertNotEqual(
            os.path.basename(mm_config.get_recientes_path()), mm_config.USER_INI_NAME
        )
        self.assertFalse(os.path.exists(mm_config.get_user_ini_path()))


class TestVolumenYTamano(unittest.TestCase):
    """El disco del proyecto y su espacio libre, como se muestran en la barra."""

    def test_letra_de_unidad_en_windows(self):
        self.assertEqual(mm_paths.nombre_de_volumen("N:/VFX/shot/comp.nk"), "N:")
        self.assertEqual(mm_paths.nombre_de_volumen(r"T:\VFX\shot"), "T:")

    def test_share_unc(self):
        # En UNC el "disco" es el share, no el servidor.
        self.assertEqual(
            mm_paths.nombre_de_volumen("//servidor/proyectos/shot/x.nk"),
            "//servidor/proyectos",
        )

    def test_vacio(self):
        self.assertEqual(mm_paths.nombre_de_volumen(""), "")
        self.assertEqual(mm_paths.nombre_de_volumen(None), "")

    def test_escalas_de_tamano(self):
        self.assertEqual(mm_paths.formatear_tamano(1.4 * 1024 ** 4), "1.4 TB")
        self.assertEqual(mm_paths.formatear_tamano(847 * 1024 ** 3), "847 GB")
        self.assertEqual(mm_paths.formatear_tamano(9.6 * 1024 ** 3), "9.6 GB")
        self.assertEqual(mm_paths.formatear_tamano(512 * 1024 ** 2), "512 MB")

    def test_un_decimal_solo_cuando_el_numero_es_chico(self):
        # "1.4 TB" dice algo; "847.3 GB" es ruido.
        self.assertNotIn(".", mm_paths.formatear_tamano(847 * 1024 ** 3))
        self.assertIn(".", mm_paths.formatear_tamano(1.4 * 1024 ** 4))

    def test_valores_que_no_sirven(self):
        self.assertEqual(mm_paths.formatear_tamano(None), "")
        self.assertEqual(mm_paths.formatear_tamano("no es un numero"), "")
        self.assertEqual(mm_paths.formatear_tamano(-1), "")

    def test_un_disco_lleno_no_dice_vacio(self):
        # 0 libres es un dato, no un fallo: tiene que mostrarse.
        self.assertTrue(mm_paths.formatear_tamano(0))

if __name__ == "__main__":
    unittest.main()
