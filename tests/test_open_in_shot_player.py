"""Pruebas aisladas para Open in Shot Player (sin Nuke, Qt ni apps reales)."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import LGA_OpenInShotPlayer as shot_player


class _Knob:
    def __init__(self, value):
        self.value_text = value
        self.evaluated = False

    def evaluate(self, _frame=None):
        self.evaluated = True
        return self.value_text

    def value(self):
        return self.value_text


class _Node:
    def __init__(
        self,
        class_name="Read",
        path="/tmp/shot.%04d.exr",
        first=1001,
        origfirst=None,
    ):
        self.knob = _Knob(path)
        self.class_name = class_name
        self.knobs = {
            "file": self.knob,
            "first": _Knob(first),
            "origfirst": _Knob(first if origfirst is None else origfirst),
        }

    def __getitem__(self, name):
        if name not in self.knobs:
            raise KeyError(name)
        return self.knobs[name]

    def Class(self):
        return self.class_name


class _Nuke:
    def __init__(self, nodes, frame_number=1001, filename=None):
        self.nodes = nodes
        self.frame_number = frame_number
        self.filename_value = filename

    def selectedNodes(self, class_name=None):
        if class_name is None:
            return self.nodes
        return [node for node in self.nodes if node.Class() == class_name]

    def frame(self):
        return self.frame_number

    def filename(self, _node):
        return self.filename_value


class ShotPlayerTests(unittest.TestCase):
    def test_media_path_evaluates_current_frame_token(self):
        node = _Node(path="/tmp/shot.%04d.exr")
        nuke = _Nuke([node], frame_number=1001, filename="/tmp/shot.%04d.exr")
        self.assertEqual(
            shot_player.media_path_for_read(nuke, node),
            os.path.normpath("/tmp/shot.1001.exr"),
        )
        self.assertTrue(node.knob.evaluated)

    def test_missing_current_frame_falls_back_to_read_first(self):
        node = _Node(path="/tmp/shot.%04d.exr", first=975)
        nuke = _Nuke([node], frame_number=1, filename="/tmp/shot.%04d.exr")
        checked = []

        def is_file(path):
            checked.append(path)
            return path.endswith("shot.0975.exr")

        self.assertEqual(
            shot_player.existing_media_path_for_read(nuke, node, is_file=is_file),
            os.path.normpath("/tmp/shot.0975.exr"),
        )
        self.assertEqual(
            checked,
            [
                os.path.normpath("/tmp/shot.0001.exr"),
                os.path.normpath("/tmp/shot.0975.exr"),
            ],
        )

    def test_registry_accepts_new_mac_profile_and_rejects_dev_path(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = os.path.join(temp, "LGA Shot Player.app")
            executable = os.path.join(bundle, "Contents", "MacOS", "LGA Shot Player")
            os.makedirs(os.path.dirname(executable))
            open(executable, "w").close()
            os.chmod(executable, 0o755)
            manifest = {
                "name": "LGA Shot Player",
                "version": "1.23.0",
                "installPath": bundle,
                "executable": executable,
            }
            read_file = lambda path: json.dumps(manifest) if path.endswith("LGA Shot Player.json") else "{}"
            found = shot_player.resolve_shot_player(
                system="darwin",
                home=temp,
                read_file=read_file,
            )
            self.assertEqual(found.profile, "LGA Shot Player")
            self.assertEqual(found.bundle_path, os.path.abspath(bundle))

            dev_bundle = bundle.replace("LGA Shot Player.app", "build/LGA Shot Player.app")
            self.assertTrue(shot_player._is_dev_tree(dev_bundle, "darwin"))

    def test_registry_normalizes_mac_contents_macos_install_path(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = os.path.join(temp, "LGA Shot Player.app")
            executable = os.path.join(bundle, "Contents", "MacOS", "LGA Shot Player")
            os.makedirs(os.path.dirname(executable))
            open(executable, "w").close()
            os.chmod(executable, 0o755)
            manifest = {
                "installPath": os.path.dirname(executable),
                "executable": executable,
                "version": "1.24",
            }
            found = shot_player.resolve_shot_player(
                system="darwin",
                home=temp,
                read_file=lambda path: json.dumps(manifest),
            )
            self.assertEqual(found.bundle_path, os.path.abspath(bundle))
            self.assertEqual(found.executable, os.path.abspath(executable))

    def test_registry_accepts_windows_executable_install_path(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = os.path.join(temp, "LGA_Player.exe")
            open(executable, "w").close()
            manifest = {"installPath": executable, "version": "2.01"}
            found = shot_player.resolve_shot_player(
                system="win32",
                env={"APPDATA": temp},
                read_file=lambda path: json.dumps(manifest),
            )
            self.assertEqual(found.install_path, os.path.abspath(temp))
            self.assertEqual(found.executable, os.path.abspath(executable))

    def test_registry_accepts_legacy_windows_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            install = os.path.join(temp, "ShotPlayer")
            os.makedirs(install)
            executable = os.path.join(install, "LGA_Player.exe")
            open(executable, "w").close()
            manifest = {"installPath": install, "executable": executable, "version": "2.00"}
            read_file = lambda path: json.dumps(manifest) if path.endswith("LGA Player.json") else "{}"
            found = shot_player.resolve_shot_player(
                system="win32",
                env={"APPDATA": temp},
                read_file=read_file,
            )
            self.assertEqual(found.profile, "LGA Player")
            self.assertEqual(os.path.basename(found.executable), "LGA_Player.exe")

    def test_stale_new_profile_falls_back_to_legacy_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            install = os.path.join(temp, "ShotPlayer")
            os.makedirs(install)
            executable = os.path.join(install, "LGA_Player.exe")
            open(executable, "w").close()
            legacy = {"installPath": install, "version": "2.02"}

            def read_file(path):
                if path.endswith("LGA Shot Player.json"):
                    return json.dumps({"installPath": os.path.join(temp, "missing")})
                return json.dumps(legacy)

            found = shot_player.resolve_shot_player(
                system="win32",
                env={"APPDATA": temp},
                read_file=read_file,
            )
            self.assertEqual(found.profile, "LGA Player")

    def test_mac_fallback_uses_home_override(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = os.path.join(temp, "Applications", "LGA Shot Player.app")
            executable = os.path.join(bundle, "Contents", "MacOS", "LGA Shot Player")
            os.makedirs(os.path.dirname(executable))
            open(executable, "w").close()
            os.chmod(executable, 0o755)
            original = shot_player.MAC_DEFAULT_BUNDLES
            try:
                shot_player.MAC_DEFAULT_BUNDLES = ("~/Applications/LGA Shot Player.app",)
                found = shot_player.resolve_shot_player(system="darwin", home=temp)
            finally:
                shot_player.MAC_DEFAULT_BUNDLES = original
            self.assertEqual(found.bundle_path, os.path.abspath(bundle))

    def test_launch_uses_associated_file_semantics(self):
        install = shot_player.ShotPlayerInstall(
            "macos", "/Applications/LGA Shot Player.app", "/fake/player", "/Applications/LGA Shot Player.app", "", ""
        )
        calls = []
        shot_player.launch_shot_player(install, "/tmp/shot.1001.exr", popen=lambda *args, **kwargs: calls.append((args, kwargs)))
        self.assertEqual(calls[0][0][0], ["/usr/bin/open", "-a", "/Applications/LGA Shot Player.app", "/tmp/shot.1001.exr"])
        self.assertFalse(calls[0][1]["shell"])

    def test_main_reports_invalid_selection_without_launching(self):
        warnings = []
        original = shot_player._show_warning
        try:
            shot_player._show_warning = lambda title, text: warnings.append((title, text))
            self.assertFalse(shot_player.main(_Nuke([_Node("Write")]), popen=lambda *_args, **_kwargs: self.fail("launched")))
        finally:
            shot_player._show_warning = original
        self.assertIn("exactly one Read", warnings[0][1])

    def test_read_remains_unambiguous_with_another_node_selected(self):
        read = _Node("Read")
        write = _Node("Write")
        self.assertIs(shot_player._selected_read(_Nuke([read, write])), read)

    def test_main_rejects_missing_current_frame_without_launching(self):
        warnings = []
        installation = shot_player.ShotPlayerInstall(
            "windows", "/tmp/player", "/tmp/player/LGA_Player.exe", "", "", ""
        )
        original = shot_player._show_warning
        try:
            shot_player._show_warning = lambda title, text: warnings.append((title, text))
            self.assertFalse(
                shot_player.main(
                    _Nuke([_Node(path="/tmp/no-such-frame.%04d.exr")]),
                    popen=lambda *_args, **_kwargs: self.fail("launched"),
                    installer_resolver=lambda: installation,
                )
            )
        finally:
            shot_player._show_warning = original
        self.assertIn("does not have media on disk", warnings[0][1])


if __name__ == "__main__":
    unittest.main()
