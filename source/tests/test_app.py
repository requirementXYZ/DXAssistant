import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dxassistant.app import default_config_path, main


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

    def test_smoke_test_loads_config_and_checks_bridge_without_gui(self):
        source_config = default_config_path()
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "config.json"
            config.write_bytes(source_config.read_bytes())
            self.assertEqual(main(["--config", str(config), "--smoke-test"]), 0)


if __name__ == "__main__":
    unittest.main()
