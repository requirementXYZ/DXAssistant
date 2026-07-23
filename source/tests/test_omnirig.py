import json
import subprocess
import unittest
from unittest.mock import patch

from dxassistant.omnirig import OmniRigClient, OmniRigError


PAYLOAD = {
    "ok": True,
    "rig_type": "FTDX101D",
    "status": "On-line",
    "frequency_a_hz": 18100000,
    "frequency_b_hz": 18100000,
    "receive_frequency_hz": 18100000,
    "split": "On",
    "routing": "RX-A/TX-B",
    "tx_state": "RX",
    "capabilities": {
        "compatible": True,
        "missing": [],
        "parameters": {
            "read_freq_a": True,
            "write_freq_a": True,
            "read_freq_b": True,
            "write_freq_b": True,
            "read_vfo_ab": True,
            "read_split": True,
            "read_rx": True,
        },
    },
}


class OmniRigTests(unittest.TestCase):
    @patch("dxassistant.omnirig.subprocess.run")
    def test_align_returns_verified_snapshot(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, json.dumps(PAYLOAD), "")
        result = OmniRigClient().align(18_100_000)
        self.assertEqual(result.frequency_a_hz, 18_100_000)
        self.assertEqual(result.frequency_b_hz, 18_100_000)
        self.assertTrue(result.compatible)
        self.assertEqual(result.missing_capabilities, ())
        command = run.call_args.args[0]
        self.assertIn("align", command)
        self.assertIn("18100000", command)

    @patch("dxassistant.omnirig.subprocess.run")
    def test_bridge_interlock_error_is_raised(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 1, json.dumps({"ok": False, "message": "Radio is not in receive"}), ""
        )
        with self.assertRaisesRegex(OmniRigError, "not in receive"):
            OmniRigClient().align(14_074_000)

    def test_frequency_outside_supported_range_is_rejected_without_bridge(self):
        with self.assertRaises(OmniRigError):
            OmniRigClient().align(1000)

    @patch("dxassistant.omnirig.subprocess.run")
    def test_incomplete_profile_capabilities_are_reported(self, run):
        payload = dict(PAYLOAD)
        payload["rig_type"] = "Example Rig"
        payload["capabilities"] = {
            "compatible": False,
            "missing": ["read_freq_b", "write_freq_b"],
            "parameters": {"read_freq_a": True},
        }
        run.return_value = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
        result = OmniRigClient().status()
        self.assertFalse(result.compatible)
        self.assertEqual(result.missing_capabilities, ("read_freq_b", "write_freq_b"))

    @patch("dxassistant.omnirig.subprocess.run")
    def test_success_payload_with_missing_fields_is_rejected(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, json.dumps({"ok": True, "rig_type": "Broken"}), ""
        )
        with self.assertRaisesRegex(OmniRigError, "incomplete or invalid"):
            OmniRigClient().status()


if __name__ == "__main__":
    unittest.main()
