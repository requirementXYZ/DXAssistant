import ast
import unittest
from pathlib import Path


class SafetyTests(unittest.TestCase):
    def test_production_package_has_no_outbound_socket_calls(self):
        package = Path(__file__).resolve().parents[1] / "dxassistant"
        prohibited = {"send", "sendall", "sendto", "connect", "connect_ex"}
        found = []
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in prohibited
                    and not (path.name == "receiver.py" and node.func.attr == "sendto")
                ):
                    found.append(f"{path.name}:{node.lineno}:{node.func.attr}")
        self.assertEqual(found, [])

    def test_only_configure_message_is_available_for_wsjtx_requests(self):
        package = Path(__file__).resolve().parents[1] / "dxassistant"
        protocol = (package / "protocol.py").read_text(encoding="utf-8")
        receiver = (package / "receiver.py").read_text(encoding="utf-8")
        self.assertIn("WSJTX_CONFIGURE = 15", protocol)
        self.assertIn("build_prepare_dx", receiver)
        self.assertNotIn("WSJTX_REPLY", protocol)
        self.assertNotIn("WSJTX_HALT", protocol)
        self.assertNotIn("EnableTx", protocol)

    def test_http_access_is_confined_to_approved_receive_side_services(self):
        package = Path(__file__).resolve().parents[1] / "dxassistant"
        network_modules = []
        for path in package.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            if "urllib.request" in source:
                network_modules.append(path.name)
        self.assertEqual(network_modules, ["pskreporter.py", "pushover.py"])

    def test_omnirig_bridge_cannot_key_or_configure_transmit(self):
        bridge = Path(__file__).resolve().parents[1] / "dxassistant" / "omnirig_bridge.ps1"
        source = bridge.read_text(encoding="utf-8").lower().replace(" ", "")
        self.assertNotIn("$rig.tx=", source)
        self.assertNotIn("tx1;", source)
        self.assertNotIn("$rig.mode=", source)
        self.assertNotIn("$rig.split=", source)
        self.assertNotIn("setmode", source)

    def test_omnirig_bridge_only_writes_vfo_frequencies(self):
        bridge = Path(__file__).resolve().parents[1] / "dxassistant" / "omnirig_bridge.ps1"
        source = bridge.read_text(encoding="utf-8").lower().replace(" ", "")
        self.assertIn("$rig.freqa=", source)
        self.assertIn("$rig.freqb=", source)

    def test_omnirig_bridge_uses_capabilities_not_model_identity(self):
        bridge = Path(__file__).resolve().parents[1] / "dxassistant" / "omnirig_bridge.ps1"
        source = bridge.read_text(encoding="utf-8").lower()
        self.assertIn("isparamreadable", source)
        self.assertIn("isparamwriteable", source)
        self.assertNotIn("-ne \"ftdx101d\"", source)


if __name__ == "__main__":
    unittest.main()
