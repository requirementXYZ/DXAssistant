import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from dxassistant.config import (
    load_config,
    save_band_enabled,
    save_band_frequency,
    save_band_frequencies,
    save_psk_search_area,
    save_target_call,
)
from dxassistant.logging import DecodeLogger, EventLogger
from dxassistant.protocol import Decode


class ConfigAndLoggingTests(unittest.TestCase):
    def test_loads_and_normalises_config(self):
        raw = {
            "target_call": " t22tt ", "udp_host": "127.0.0.1", "udp_port": 2237,
            "alarm_enabled": True, "heartbeat_timeout_seconds": 15,
            "log_directory": "logs", "bands": {"20m": {"enabled": True, "frequency_mhz": 14.074}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            self.assertEqual(config.target_call, "T22TT")
            self.assertEqual(config.log_directory, path.parent / "logs")
            self.assertEqual(config.station_locator, "JO03")
            self.assertEqual(config.psk_reporter_distance_km, 2500)
            self.assertFalse(config.bands["160m"].enabled)
            self.assertEqual(config.bands["160m"].frequency_mhz, 1.840)
            self.assertFalse(config.bands["80m"].enabled)
            self.assertEqual(config.bands["80m"].frequency_mhz, 3.573)
            self.assertFalse(config.bands["6m"].enabled)
            self.assertEqual(config.bands["6m"].frequency_mhz, 50.313)

    def test_new_standard_band_can_be_saved_into_an_older_band_plan(self):
        raw = {
            "target_call": "T22TT", "udp_host": "127.0.0.1", "udp_port": 2237,
            "alarm_enabled": True, "heartbeat_timeout_seconds": 15,
            "log_directory": "logs",
            "bands": {"20m": {"enabled": True, "frequency_mhz": 14.074}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            save_band_enabled(config, "80m", True)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(saved["bands"]["80m"]["enabled"])
            self.assertEqual(saved["bands"]["80m"]["frequency_mhz"], 3.573)
            self.assertNotIn("power_watts", saved["bands"]["80m"])

    def test_logs_decode(self):
        packet = Decode("WSJT-X", 3, True, "12:00:00", -8, 0.1, 1000, "FT8", "CQ T22TT")
        with tempfile.TemporaryDirectory() as directory:
            path = DecodeLogger(Path(directory)).write(packet, 14_074_000, True, datetime(2026, 7, 14, tzinfo=timezone.utc))
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]["target_found"], "True")
            self.assertEqual(rows[0]["band"], "20m")

    def test_event_log_is_append_only_json_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = EventLogger(Path(directory))
            path = logger.write("monitoring_started", "UDP listener started", target="T22TT")
            logger.write("monitoring_stopped", "Operator selected Stop")
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([item["event"] for item in records], ["monitoring_started", "monitoring_stopped"])
            self.assertEqual(records[0]["target"], "T22TT")

    def test_event_log_buffers_and_flushes_after_write_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = EventLogger(Path(directory))
            with unittest.mock.patch("pathlib.Path.open", side_effect=OSError("disk unavailable")):
                self.assertIsNone(logger.write("tune_failed", "offline"))
            self.assertEqual(len(logger.pending), 1)
            path = logger.write("monitoring_started", "recovered")
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([item["event"] for item in records], ["tune_failed", "monitoring_started"])
            self.assertEqual(logger.pending, [])

    def test_legacy_band_power_value_is_ignored(self):
        raw = {
            "target_call": "T22TT", "udp_host": "127.0.0.1", "udp_port": 2237,
            "alarm_enabled": True, "heartbeat_timeout_seconds": 15,
            "log_directory": "logs",
            "bands": {"20m": {"enabled": True, "frequency_mhz": 14.074, "power_watts": 101}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            self.assertTrue(config.bands["20m"].enabled)
            self.assertEqual(config.bands["20m"].frequency_mhz, 14.074)
            self.assertFalse(hasattr(config.bands["20m"], "power_watts"))

    def test_psk_search_area_is_validated_and_persisted(self):
        raw = {
            "target_call": "T22TT", "udp_host": "127.0.0.1", "udp_port": 2237,
            "alarm_enabled": True, "heartbeat_timeout_seconds": 15,
            "log_directory": "logs",
            "bands": {"20m": {"enabled": True, "frequency_mhz": 14.074}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            save_psk_search_area(config, "io91wm", 1000)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["station_locator"], "IO91WM")
            self.assertEqual(saved["psk_reporter_distance_km"], 1000)

    def test_band_enablement_and_frequency_plan_are_persisted(self):
        raw = {
            "target_call": "T22TT", "udp_host": "127.0.0.1", "udp_port": 2237,
            "alarm_enabled": True, "heartbeat_timeout_seconds": 15,
            "log_directory": "logs",
            "bands": {
                "20m": {"enabled": True, "frequency_mhz": 14.074},
                "17m": {"enabled": True, "frequency_mhz": 18.100},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            save_band_enabled(config, "20m", False)
            save_band_frequency(config, "17m", 18.0956)
            save_band_frequencies(config, {"17m": 18.100})
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(saved["bands"]["20m"]["enabled"])
            self.assertEqual(saved["bands"]["17m"]["frequency_mhz"], 18.1)

    def test_target_call_is_normalised_and_persisted(self):
        raw = {
            "target_call": "T22TT", "udp_host": "127.0.0.1", "udp_port": 2237,
            "alarm_enabled": True, "heartbeat_timeout_seconds": 15,
            "log_directory": "logs",
            "bands": {"20m": {"enabled": True, "frequency_mhz": 14.074}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            save_target_call(config, " vk9wx ")
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["target_call"], "VK9WX")


if __name__ == "__main__":
    unittest.main()
