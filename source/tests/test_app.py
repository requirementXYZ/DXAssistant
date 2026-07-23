import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dxassistant.app import default_config_path, ensure_config_file, main


class AppPackagingTests(unittest.TestCase):
    def test_frozen_build_uses_editable_config_beside_executable(self):
        executable = Path(r"C:\Portable\DXAssistant\DXAssistant.exe")
        with patch("dxassistant.app.sys.frozen", True, create=True):
            with patch("dxassistant.app.sys.executable", str(executable)):
                self.assertEqual(
                    default_config_path(),
                    Path(r"C:\Portable\DXAssistant\config.json"),
                )

    def test_source_build_uses_project_config(self):
        self.assertEqual(default_config_path().name, "config.json")
        self.assertEqual(default_config_path().parent.name, "source")

    def test_first_run_copies_template_to_untracked_live_config(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            template = directory / "config.template.json"
            config = directory / "config.json"
            template.write_text('{"target_call": "T22TT"}\n', encoding="utf-8")
            ensure_config_file(config)
            self.assertEqual(config.read_bytes(), template.read_bytes())
            config.write_text('{"target_call": "VK9WX"}\n', encoding="utf-8")
            ensure_config_file(config)
            self.assertIn("VK9WX", config.read_text(encoding="utf-8"))

    def test_smoke_test_loads_config_and_checks_bridge_without_gui(self):
        source_config = default_config_path().with_name("config.template.json")
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "config.json"
            config.write_bytes(source_config.read_bytes())
            self.assertEqual(main(["--config", str(config), "--smoke-test"]), 0)


if __name__ == "__main__":
    unittest.main()
