"""Pruebas aisladas del Download del Media Manager (sin Nuke, Qt ni apps)."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import LGA_MediaManager_download as dl


def _write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle)


class _Sandbox(unittest.TestCase):
    """Un %APPDATA% y una $HOME de mentira, con su registro LGA vacio."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        self.appdata = os.path.join(self.tmp.name, "appdata")
        self.registry = os.path.join(self.appdata, "LGA")
        os.makedirs(self.registry)
        os.makedirs(self.home)
        self.env = {"APPDATA": self.appdata}
        dl.reset_cache()

    def tearDown(self):
        dl.reset_cache()
        self.tmp.cleanup()

    def _windows_install(self, name, exe="FileManagerS3.exe"):
        folder = os.path.join(self.tmp.name, name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, exe), "wb") as handle:
            handle.write(b"MZ")
        return folder

    def _resolve(
        self, spec, system="win32", read_uninstall=lambda key: None, default_paths=()
    ):
        # default_paths vacio: en la maquina de desarrollo la app SI esta en
        # su carpeta de siempre, y sin esto el fallback la encontraria.
        return dl.resolve_lga_app(
            spec,
            system=system,
            env=self.env,
            home=self.home,
            read_uninstall=read_uninstall,
            default_paths=default_paths,
        )


class RegistryDirectoryTests(unittest.TestCase):
    def test_windows_uses_appdata(self):
        self.assertEqual(
            dl.registry_directory("win32", env={"APPDATA": r"C:\Users\x\AppData\Roaming"}),
            os.path.join(r"C:\Users\x\AppData\Roaming", "LGA"),
        )

    def test_macos_uses_application_support(self):
        self.assertTrue(
            dl.registry_directory("darwin", home="/Users/x").endswith(
                os.path.join("Library", "Application Support", "LGA")
            )
        )


class ResolveWindowsTests(_Sandbox):
    def test_registry_wins(self):
        folder = self._windows_install("fm")
        _write_json(
            os.path.join(self.registry, "FileManagerS3.json"),
            {"installPath": folder, "executable": os.path.join(folder, "FileManagerS3.exe"),
             "version": "0.912"},
        )
        app = self._resolve(dl.FILEMANAGERS3)
        self.assertIsNotNone(app)
        self.assertEqual(app.source, "registry")
        self.assertEqual(app.version, "0.912")
        self.assertEqual(app.executable, os.path.join(folder, "FileManagerS3.exe"))

    def test_registry_pointing_to_empty_folder_is_ignored(self):
        folder = os.path.join(self.tmp.name, "vacia")
        os.makedirs(folder)
        _write_json(
            os.path.join(self.registry, "FileManagerS3.json"), {"installPath": folder}
        )
        self.assertIsNone(self._resolve(dl.FILEMANAGERS3))

    def test_registry_pointing_to_build_tree_is_ignored(self):
        folder = self._windows_install("build")
        _write_json(
            os.path.join(self.registry, "FileManagerS3.json"), {"installPath": folder}
        )
        self.assertIsNone(self._resolve(dl.FILEMANAGERS3))

    def test_uninstall_key_is_second(self):
        folder = self._windows_install("instalada")
        app = self._resolve(
            dl.FILEMANAGERS3, read_uninstall=lambda key: ("0.910", folder)
        )
        self.assertIsNotNone(app)
        self.assertEqual(app.source, "uninstall")
        self.assertEqual(app.version, "0.910")
        self.assertEqual(app.install_path, folder)

    def test_orphan_uninstall_key_is_ignored(self):
        folder = os.path.join(self.tmp.name, "huerfana")
        os.makedirs(folder)
        app = self._resolve(
            dl.FILEMANAGERS3, read_uninstall=lambda key: ("0.910", folder)
        )
        self.assertIsNone(app)

    def test_uninstall_reader_error_does_not_break(self):
        def explota(key):
            raise RuntimeError("sin registro")

        self.assertIsNone(self._resolve(dl.FILEMANAGERS3, read_uninstall=explota))

    def test_nothing_installed(self):
        self.assertIsNone(self._resolve(dl.FILEMANAGERS3))
        self.assertIsNone(self._resolve(dl.PIPESYNC_STUDIO))


class ResolveMacTests(_Sandbox):
    def _bundle(self, relative):
        bundle = os.path.normpath(os.path.join(self.home, relative))
        os.makedirs(os.path.join(bundle, "Contents", "MacOS"))
        return bundle

    def test_registry_bundle(self):
        registry = os.path.join(self.home, "Library", "Application Support", "LGA")
        os.makedirs(registry)
        bundle = self._bundle("Apps/LGA FileManager S3.app")
        _write_json(
            os.path.join(registry, "FileManagerS3.json"),
            {"installPath": os.path.join(bundle, "Contents", "MacOS"), "version": "0.9"},
        )
        app = self._resolve(dl.FILEMANAGERS3, system="darwin")
        self.assertIsNotNone(app)
        self.assertEqual(app.executable, bundle)

    def test_default_bundle_under_home(self):
        bundle = self._bundle("Applications/LGA FileManager S3.app")
        app = self._resolve(
            dl.FILEMANAGERS3,
            system="darwin",
            default_paths=dl.FILEMANAGERS3.mac_defaults,
        )
        self.assertIsNotNone(app)
        self.assertEqual(app.source, "default")
        self.assertEqual(app.executable, bundle)


class DownloadTargetTests(_Sandbox):
    def _kwargs(self, **extra):
        base = dict(system="win32", env=self.env, home=self.home,
                    read_uninstall=lambda key: None, default_paths=())
        base.update(extra)
        return base

    def test_filemanagers3_first(self):
        fm = self._windows_install("fm")
        ps = self._windows_install("ps", exe="PipeSync.exe")
        _write_json(os.path.join(self.registry, "FileManagerS3.json"), {"installPath": fm})
        _write_json(os.path.join(self.registry, "PipeSync.json"), {"installPath": ps})
        target = dl.resolve_download_target(**self._kwargs())
        self.assertEqual(target.kind, "filemanagers3")

    def test_pipesync_studio_fallback(self):
        ps = self._windows_install("ps", exe="PipeSync.exe")
        _write_json(os.path.join(self.registry, "PipeSync.json"), {"installPath": ps})
        target = dl.resolve_download_target(**self._kwargs())
        self.assertEqual(target.kind, "pipesync")
        # PipeSync entiende los mismos flags: el comando es identico salvo el exe.
        self.assertEqual(
            dl.build_download_command(target.app, [], [r"T:\VFX-A\ref.mov"]),
            [os.path.join(ps, "PipeSync.exe"), "--download-file", r"T:\VFX-A\ref.mov"],
        )

    def test_only_a_filemanagers3_hit_is_cached(self):
        # Sin nada instalado: None y NO se cachea, para que instalar y reabrir
        # alcance. Con FileManager S3: se cachea.
        dl.reset_cache()
        self.assertIsNone(dl.resolve_download_target(**self._kwargs()))
        self.assertFalse(
            dl._cache_resolved and dl._cached_target is not None
        )
        fm = self._windows_install("fm")
        _write_json(os.path.join(self.registry, "FileManagerS3.json"), {"installPath": fm})
        self.assertEqual(dl.resolve_download_target(**self._kwargs()).kind, "filemanagers3")

    def test_pipesync_client_does_not_count(self):
        ps = self._windows_install("psc", exe="PipeSync.exe")
        _write_json(os.path.join(self.registry, "PipeSyncClient.json"), {"installPath": ps})
        self.assertIsNone(dl.resolve_download_target(**self._kwargs()))


class PlanTests(unittest.TestCase):
    def test_sequences_go_by_folder_and_files_by_path(self):
        plan = dl.plan_download([
            r"T:\VFX-PROJA\PROJA_1013_0800\_input\plate\plate.####.exr[1001-1010]",
            r"T:\VFX-PROJA\PROJA_1013_0800\_input\plate\plate.####.exr[1001-1010]",
            r"T:\VFX-PROJA\PROJA_1013_0800\_input\ref.mov",
            "",
        ])
        self.assertEqual(
            plan.folders,
            [os.path.normpath(r"T:\VFX-PROJA\PROJA_1013_0800\_input\plate")],
        )
        self.assertEqual(
            plan.files, [os.path.normpath(r"T:\VFX-PROJA\PROJA_1013_0800\_input\ref.mov")]
        )
        self.assertEqual(plan.skipped, [])

    def test_paths_without_vfx_root_are_skipped(self):
        plan = dl.plan_download([r"D:\otra\cosa.mov"])
        self.assertEqual(plan.files, [])
        self.assertEqual(len(plan.skipped), 1)

    def test_printf_token_is_a_sequence_too(self):
        plan = dl.plan_download([
            r"T:\VFX-PROJA\shot\plate.%d.exr",
            r"T:\VFX-PROJA\shot\comp.%04d.exr",
        ])
        self.assertEqual(plan.folders, [os.path.normpath(r"T:\VFX-PROJA\shot")])
        self.assertEqual(plan.files, [])

    def test_version_hashes_in_name_do_not_confuse(self):
        plan = dl.plan_download([r"T:\VFX-PROJA\shot\comp_v###.####.exr[1-2]"])
        self.assertEqual(plan.folders, [os.path.normpath(r"T:\VFX-PROJA\shot")])


class CommandTests(unittest.TestCase):
    def test_windows_command(self):
        app = dl.LgaApp("windows", "FileManager S3", r"C:\fm", r"C:\fm\FileManagerS3.exe", "", "registry")
        self.assertEqual(
            dl.build_download_command(app, [r"T:\VFX-A\seq"], [r"T:\VFX-A\ref.mov"]),
            [r"C:\fm\FileManagerS3.exe", "--download", r"T:\VFX-A\seq",
             "--download-file", r"T:\VFX-A\ref.mov"],
        )

    def test_macos_command_uses_open(self):
        app = dl.LgaApp("macos", "FileManager S3", "/Applications/X.app", "/Applications/X.app", "", "default")
        self.assertEqual(
            dl.build_download_command(app, [], ["/Volumes/T/VFX-A/ref.mov"]),
            ["open", "-na", "/Applications/X.app", "--args",
             "--download-file", "/Volumes/T/VFX-A/ref.mov"],
        )

    def test_empty_plan_has_no_command(self):
        app = dl.LgaApp("windows", "x", "", "x.exe", "", "")
        self.assertIsNone(dl.build_download_command(app, [], []))

    def test_launch_does_not_use_shell(self):
        llamadas = []

        def popen(cmd, shell):
            llamadas.append((cmd, shell))
            return "proc"

        self.assertEqual(dl.launch(["x.exe", "--download", "a"], popen=popen), "proc")
        self.assertEqual(llamadas, [(["x.exe", "--download", "a"], False)])


if __name__ == "__main__":
    unittest.main()
