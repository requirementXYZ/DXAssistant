import json
import queue
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from dxassistant.config import AppConfig, BandConfig
from dxassistant.dashboard import (
    BUTTON_AMBER,
    BUTTON_DISABLED,
    BUTTON_GREEN,
    Dashboard,
    MAX_RECENT_DECODES,
)
from dxassistant.hopping import SearchState
from dxassistant.omnirig import OmniRigResult
from dxassistant.protocol import Decode, Heartbeat, Status
from dxassistant.pskreporter import BandPriority
from dxassistant.state import AppState


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        self.config_path = Path(self.temp.name) / "config.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "target_call": "T22TT",
                    "udp_host": "127.0.0.1",
                    "udp_port": 2237,
                    "alarm_enabled": True,
                    "heartbeat_timeout_seconds": 15,
                    "log_directory": "logs",
                    "bands": {
                        "20m": {"enabled": True, "frequency_mhz": 14.074},
                        "17m": {"enabled": True, "frequency_mhz": 18.100},
                    },
                }
            ),
            encoding="utf-8",
        )
        config = AppConfig(
            target_call="T22TT",
            udp_host="127.0.0.1",
            udp_port=2237,
            alarm_enabled=True,
            heartbeat_timeout_seconds=15,
            log_directory=Path(self.temp.name),
            bands={
                "20m": BandConfig(True, 14.074),
                "17m": BandConfig(True, 18.100),
            },
            source_path=self.config_path,
        )
        self.dashboard = Dashboard(self.root, config)

    def tearDown(self):
        self.dashboard.receiver.stop()
        self.root.destroy()
        self.temp.cleanup()

    def pump(self):
        for _ in range(5):
            self.root.update()

    def test_dashboard_constructs_with_band_and_stopped_state(self):
        self.assertEqual(self.dashboard.machine.current, AppState.STOPPED)
        self.assertEqual(self.dashboard.bands.item("20m")["values"][0], "20m")

    def test_dashboard_start_is_written_to_append_only_event_log(self):
        self.dashboard.start()
        event_files = list(Path(self.temp.name).glob("events-*.jsonl"))
        records = [
            json.loads(line)
            for line in event_files[0].read_text(encoding="utf-8").splitlines()
        ]
        self.assertIn("application_started", [item["event"] for item in records])
        self.assertIn("monitoring_start_requested", [item["event"] for item in records])

    def test_muted_alarm_keeps_visual_alert_without_bell(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        self.dashboard.mute_alarm()
        packet = Decode(
            "TEST", 3, True, "12:00:00", -14, 0.1, 1300, "FT8", "CQ T22TT RI49"
        )
        with patch.object(self.dashboard.root, "state", return_value="normal"):
            with patch.object(self.dashboard.root, "bell") as bell:
                self.dashboard._handle_packet(packet)
        bell.assert_not_called()
        self.assertTrue(self.dashboard.alarm_active)
        self.assertEqual(self.dashboard.machine.current, AppState.TARGET_DECODED)

    def test_capable_omnirig_profile_is_reported_without_tuning(self):
        result = OmniRigResult(
            "Elecraft K3", "On-line", 14_074_000, 14_074_000,
            14_074_000, "On", "RX-A/TX-B", "RX", True, (),
            {"read_freq_a": True, "write_freq_a": True},
        )
        with patch.object(self.dashboard.omnirig, "align") as align:
            self.dashboard._handle_rig_check_result((result, None))
        align.assert_not_called()
        self.assertIn("Elecraft K3: compatible capability set", self.dashboard.status_text.get())

    def test_incomplete_omnirig_profile_lists_missing_capabilities(self):
        result = OmniRigResult(
            "Example Rig", "On-line", 14_074_000, 0, 14_074_000,
            "Other", "Other", "RX", False, ("read_freq_b", "write_freq_b"),
        )
        self.dashboard._handle_rig_check_result((result, None))
        self.assertIn("missing read_freq_b, write_freq_b", self.dashboard.status_text.get())

    def test_compact_left_controls_fit_in_default_window(self):
        self.root.deiconify()
        self.root.update_idletasks()
        control_bottom = (
            self.dashboard.reset_frequencies_button.winfo_rooty()
            + self.dashboard.reset_frequencies_button.winfo_height()
        )
        window_bottom = self.root.winfo_rooty() + self.root.winfo_height()
        self.assertLess(control_bottom, window_bottom)
        self.root.withdraw()

    def test_target_decode_raises_acknowledgeable_alarm(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.events.put(("receiver_started", None))
        self.dashboard._poll_events()
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        packet = Decode("TEST", 3, True, "12:00:00", -14, 0.1, 1300, "FT8", "CQ T22TT RI49")
        self.dashboard.events.put(("packet", packet))
        self.dashboard._poll_events()
        self.assertEqual(self.dashboard.machine.current, AppState.TARGET_DECODED)
        self.assertTrue(self.dashboard.alarm_active)
        self.assertEqual(len(self.dashboard.target_decodes.get_children()), 1)
        target_item = self.dashboard.target_decodes.get_children()[0]
        self.assertEqual(self.dashboard.target_decodes.item(target_item)["values"][1], "20m")
        self.dashboard.acknowledge()
        self.assertEqual(self.dashboard.machine.current, AppState.MONITORING)

    def test_operator_can_change_target_while_stopped(self):
        with patch("dxassistant.dashboard.simpledialog.askstring", return_value=" om3kfo "):
            self.dashboard.change_target()
        self.assertEqual(self.dashboard.engine.state.target_call, "OM3KFO")
        self.assertEqual(self.dashboard.values["target"].get(), "OM3KFO")
        self.assertTrue(self.dashboard.target_prepare_pending)
        self.assertIn("prepare it in WSJT-X", self.dashboard.status_text.get())
        saved = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["target_call"], "OM3KFO")

    def test_recent_activity_rolls_but_target_panel_is_separate(self):
        for number in range(MAX_RECENT_DECODES + 7):
            packet = Decode("TEST", 3, True, "12:00:00", -10, 0.1, number, "FT8", f"CQ G{number}ABC IO91")
            self.dashboard._handle_packet(packet)
        self.assertEqual(len(self.dashboard.recent_decodes.get_children()), MAX_RECENT_DECODES)
        self.assertEqual(len(self.dashboard.target_decodes.get_children()), 0)
        items = self.dashboard.recent_decodes.get_children()
        self.assertIn("G7ABC", self.dashboard.recent_decodes.item(items[0])["values"][4])
        self.assertIn("G18ABC", self.dashboard.recent_decodes.item(items[-1])["values"][4])

    def test_clear_displays_preserves_counters(self):
        packet = Decode("TEST", 3, True, "12:00:00", -14, 0.1, 1300, "FT8", "CQ T22TT RI49")
        self.dashboard._handle_packet(packet)
        self.dashboard.clear_decodes()
        self.assertEqual(len(self.dashboard.recent_decodes.get_children()), 0)
        self.assertEqual(len(self.dashboard.target_decodes.get_children()), 0)
        self.assertEqual(self.dashboard.engine.state.decode_count, 1)

    def test_all_target_decodes_are_retained_for_session(self):
        for number in range(15):
            packet = Decode("TEST", 3, True, "12:00:00", -14, 0.1, 1300 + number, "FT8", "CQ T22TT RI49")
            self.dashboard._handle_packet(packet)
        self.assertEqual(len(self.dashboard.target_decodes.get_children()), 15)
        self.assertEqual(len(self.dashboard.recent_decodes.get_children()), MAX_RECENT_DECODES)

    def test_operator_can_persist_nonstandard_band_frequency(self):
        self.dashboard.bands.selection_set("20m")
        with patch("dxassistant.dashboard.simpledialog.askstring", return_value="14.095"):
            self.dashboard.edit_band_frequency()
        self.assertEqual(self.dashboard.session_band_frequencies["20m"], 14.095)
        self.assertEqual(self.dashboard.bands.item("20m")["values"][2], "14.095")
        self.assertIn("nonstandard", self.dashboard.bands.item("20m")["tags"])
        saved = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["bands"]["20m"]["frequency_mhz"], 14.095)

    def test_operator_can_restore_default_band_frequencies(self):
        self.dashboard.session_band_frequencies["20m"] = 14.095
        self.dashboard.session_band_enabled["20m"] = False
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        raw["bands"]["20m"]["frequency_mhz"] = 14.095
        raw["bands"]["20m"]["enabled"] = False
        self.config_path.write_text(json.dumps(raw), encoding="utf-8")
        self.dashboard._render_band_row("20m")
        self.dashboard.restore_default_frequencies()
        self.assertEqual(self.dashboard.session_band_frequencies["20m"], 14.074)
        self.assertFalse(self.dashboard.session_band_enabled["20m"])
        self.assertEqual(self.dashboard.bands.item("20m")["values"][2], "14.074")
        saved = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertFalse(saved["bands"]["20m"]["enabled"])
        self.assertEqual(saved["bands"]["20m"]["frequency_mhz"], 14.074)

    def test_out_of_band_session_frequency_is_rejected(self):
        self.dashboard.bands.selection_set("20m")
        with patch("dxassistant.dashboard.simpledialog.askstring", return_value="18.100"):
            with patch("dxassistant.dashboard.messagebox.showerror") as error:
                self.dashboard.edit_band_frequency()
        error.assert_called_once()
        self.assertEqual(self.dashboard.session_band_frequencies["20m"], 14.074)

    def test_session_frequency_is_rounded_to_one_khz(self):
        self.dashboard.bands.selection_set("20m")
        with patch("dxassistant.dashboard.simpledialog.askstring", return_value="14.0956"):
            self.dashboard.edit_band_frequency()
        self.assertEqual(self.dashboard.session_band_frequencies["20m"], 14.096)
        self.assertEqual(self.dashboard.bands.item("20m")["values"][2], "14.096")

    def test_band_plan_has_no_misleading_power_column_or_control(self):
        self.assertEqual(tuple(self.dashboard.bands.cget("columns")), ("band", "enabled", "frequency"))
        self.assertFalse(hasattr(self.dashboard, "edit_power_button"))
        self.assertFalse(hasattr(self.dashboard, "band_power_watts"))

    def test_top_status_frequency_uses_three_decimal_places(self):
        packet = Status("TEST", 3, 14_074_000, "FT8", "", False, False, True)
        self.dashboard._handle_packet(packet)
        self.assertEqual(self.dashboard.values["frequency"].get(), "14.074 MHz")

    def test_status_displays_wsjtx_tx_audio_offset(self):
        packet = Status(
            "TEST", 3, 14_074_000, "FT8", "", False, False, True, 1300, 1800
        )
        self.dashboard._handle_packet(packet)
        self.assertEqual(
            self.dashboard.tx_offset_text.get(), "WSJT-X Tx offset: 1800 Hz"
        )

    def test_status_highlights_current_band(self):
        packet = Status("TEST", 3, 14_074_000, "FT8", "", False, False, True)
        self.dashboard._handle_packet(packet)
        self.assertEqual(self.dashboard.current_band, "20m")
        self.assertEqual(self.dashboard.current_band_text.get(), "20m")
        self.assertIn("current", self.dashboard.bands.item("20m")["tags"])

    def test_current_band_warns_when_disabled_in_plan(self):
        self.dashboard.session_band_enabled["20m"] = False
        packet = Status("TEST", 3, 14_074_000, "FT8", "", False, False, True)
        self.dashboard._handle_packet(packet)
        self.assertEqual(self.dashboard.current_band_text.get(), "20m - disabled in plan")
        self.assertIn("current_disabled", self.dashboard.bands.item("20m")["tags"])

    def test_target_decode_pauses_active_band_search(self):
        self.dashboard.search.begin()
        self.dashboard.search.tuned("20m", 0.0)
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        packet = Decode("TEST", 3, True, "12:00:00", -14, 0.1, 1300, "FT8", "CQ T22TT RI49")
        self.dashboard._handle_packet(packet)
        self.assertEqual(self.dashboard.search.state, SearchState.TARGET_HOLD)

    def test_enable_tx_hands_vfo_control_to_operator(self):
        self.dashboard.search.begin()
        self.dashboard.search.tuned("20m", 0.0)
        packet = Status("TEST", 3, 14_074_000, "FT8", "T22TT", True, False, False)
        self.dashboard._handle_packet(packet)
        self.dashboard._update_controls()
        self.assertEqual(self.dashboard.search.state, SearchState.OPERATOR_CONTROL)
        self.assertEqual(self.dashboard.search_button.cget("text"), "Resume search")

    def test_acknowledged_target_repeats_are_retained_without_rearming_alert(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.search.begin()
        self.dashboard.search.tuned("20m", 0.0)
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        packet = Decode("TEST", 3, True, "12:00:00", -14, 0.1, 1300, "FT8", "CQ T22TT RI49")
        self.dashboard._handle_packet(packet)
        self.dashboard.acknowledge()
        self.dashboard._handle_packet(packet)
        self.assertFalse(self.dashboard.alarm_active)
        self.assertEqual(self.dashboard.machine.current, AppState.MONITORING)
        self.assertEqual(len(self.dashboard.target_decodes.get_children()), 2)

    def test_resume_after_target_hold_moves_to_next_enabled_band(self):
        self.dashboard.search.begin()
        self.dashboard.search.tuned("20m", 0.0)
        self.dashboard.search.pause(target_found=True)
        with patch.object(self.dashboard, "_start_tune") as tune:
            self.dashboard._resume_search()
        tune.assert_called_once_with("17m")
        self.assertEqual(self.dashboard.search.state, SearchState.STARTING)

    def test_operator_can_disable_band_for_attached_antenna(self):
        self.dashboard.bands.selection_set("20m")
        self.dashboard.toggle_selected_band()
        self.assertFalse(self.dashboard.session_band_enabled["20m"])
        self.assertEqual(self.dashboard.bands.item("20m")["values"][1], "No")
        self.assertIn("disabled", self.dashboard.bands.item("20m")["tags"])
        self.assertEqual(self.dashboard.bands.selection(), ())
        saved = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertFalse(saved["bands"]["20m"]["enabled"])
        self.dashboard.bands.selection_set("20m")
        self.dashboard.toggle_selected_band()
        self.assertTrue(self.dashboard.session_band_enabled["20m"])
        self.assertEqual(self.dashboard.bands.item("20m")["values"][1], "Yes")

    def test_primary_action_colours_follow_available_state(self):
        self.dashboard._update_controls()
        self.assertEqual(self.dashboard.start_button.cget("background"), BUTTON_GREEN)
        self.assertEqual(self.dashboard.target_button.cget("background"), BUTTON_GREEN)
        self.assertEqual(self.dashboard.stop_button.cget("background"), BUTTON_DISABLED)
        self.assertEqual(
            self.dashboard.edit_frequency_button.cget("background"), BUTTON_AMBER
        )
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        self.dashboard._update_controls()
        self.assertEqual(self.dashboard.start_button.cget("background"), BUTTON_DISABLED)
        self.assertEqual(self.dashboard.target_button.cget("background"), BUTTON_DISABLED)
        self.assertEqual(self.dashboard.stop_button.cget("background"), BUTTON_AMBER)
        self.assertEqual(self.dashboard.search_button.cget("background"), BUTTON_GREEN)

    def test_search_error_detail_survives_wsjtx_heartbeat(self):
        self.dashboard._handle_tune_result(("20m", None, "Split is not on"))
        self.dashboard._handle_packet(Heartbeat("TEST", 3, 3, "3.0.1", ""))
        self.assertEqual(
            self.dashboard.search_status.get(), "Search blocked: Split is not on"
        )

    def test_repeated_target_decode_does_not_restore_or_raise_visible_window_again(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        packet = Decode(
            "TEST", 3, True, "12:00:00", -14, 0.1, 1300, "FT8", "CQ T22TT RI49"
        )
        with patch.object(self.dashboard.root, "state", return_value="normal"):
            with patch.object(self.dashboard.root, "deiconify") as deiconify:
                with patch.object(self.dashboard.root, "lift") as lift:
                    with patch.object(self.dashboard.root, "bell") as bell:
                        self.dashboard._handle_packet(packet)
                        self.dashboard._handle_packet(packet)
        deiconify.assert_not_called()
        lift.assert_called_once()
        bell.assert_called_once()

    def test_operator_can_monitor_selected_enabled_band_immediately(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        self.dashboard.bands.selection_set("17m")
        self.dashboard.bands.focus("17m")
        with patch.object(self.dashboard, "_start_tune") as tune:
            self.dashboard.monitor_selected_band()
        tune.assert_called_once_with("17m")
        self.assertEqual(self.dashboard.search.state, SearchState.STARTING)
        self.assertEqual(self.dashboard.bands.selection(), ())
        self.assertEqual(self.dashboard.bands.focus(), "")

    def test_disabled_band_cannot_be_monitored_immediately(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        self.dashboard.session_band_enabled["17m"] = False
        self.dashboard.bands.selection_set("17m")
        with patch("dxassistant.dashboard.messagebox.showwarning") as warning:
            with patch.object(self.dashboard, "_start_tune") as tune:
                self.dashboard.monitor_selected_band()
        warning.assert_called_once()
        tune.assert_not_called()

    def test_psk_reporter_focus_restricts_search_band_order(self):
        self.dashboard.pskr_priority_bands = ["17m"]
        self.assertEqual(self.dashboard._search_band_names(), ["17m"])

    def test_psk_reporter_result_updates_focus_and_receiver_counts(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        priorities = [BandPriority("17m", 3, 120, 2, 18.0)]
        self.dashboard._handle_pskr_result(
            ("T22TT", "JO03", 2500, priorities, 8, None)
        )
        self.assertEqual(self.dashboard.pskr_priority_bands, ["17m"])
        self.assertIn("17m: 3 receivers", self.dashboard.pskr_status_text.get())

    def test_psk_reporter_error_returns_search_to_full_sweep(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.pskr_priority_bands = ["17m"]
        self.dashboard._handle_pskr_result(
            ("T22TT", "JO03", 2500, [], 0, "offline")
        )
        self.assertEqual(self.dashboard.pskr_priority_bands, [])
        self.assertEqual(self.dashboard._search_band_names(), ["20m", "17m"])

    def test_operator_can_save_travel_psk_search_area(self):
        self.dashboard.locator_value.set("io91wm")
        self.dashboard.distance_value.set("1000")
        with patch("dxassistant.dashboard.save_psk_search_area") as save:
            self.dashboard.apply_psk_search_area()
        save.assert_called_once_with(self.dashboard.config, "IO91WM", 1000)
        self.assertEqual(self.dashboard.station_locator, "IO91WM")
        self.assertEqual(self.dashboard.pskr_distance_km, 1000)
        self.assertEqual(self.dashboard.pskr_next_poll, 0.0)

    def test_prepare_dx_uses_detected_target_and_latest_grid_only(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        self.dashboard.engine.state.dial_frequency_hz = 14_074_000
        packet = Decode(
            "TEST", 3, True, "12:00:00", -10, 0.1, 1300, "FT8",
            "CQ T22TT RI49",
        )
        self.dashboard._handle_packet(packet)
        with patch.object(self.dashboard.receiver, "prepare_dx") as prepare:
            self.dashboard.prepare_dx()
        prepare.assert_called_once_with("T22TT", "RI49")

    def test_first_live_status_prepares_selected_target_before_decode(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        packet = Status(
            "TEST", 3, 14_074_000, "FT8", "OLD1", False, False, True,
            1300, 1800,
        )
        with patch.object(self.dashboard.receiver, "prepare_dx") as prepare:
            self.dashboard._handle_packet(packet)
        prepare.assert_called_once_with("T22TT", "")
        self.assertFalse(self.dashboard.target_prepare_pending)
        self.assertEqual(self.dashboard.engine.state.target_decode_count, 0)
        self.dashboard._update_controls()
        self.assertEqual(str(self.dashboard.prepare_dx_button.cget("state")), "normal")

    def test_pending_target_waits_until_wsjtx_is_not_tx_enabled(self):
        self.dashboard.machine.transition(AppState.STARTING, "test")
        self.dashboard.machine.transition(AppState.MONITORING, "test")
        tx_enabled = Status(
            "TEST", 3, 14_074_000, "FT8", "OLD1", True, False, False,
            1300, 1800,
        )
        receive_only = Status(
            "TEST", 3, 14_074_000, "FT8", "OLD1", False, False, True,
            1300, 1800,
        )
        with patch.object(self.dashboard.receiver, "prepare_dx") as prepare:
            self.dashboard._handle_packet(tx_enabled)
            prepare.assert_not_called()
            self.assertTrue(self.dashboard.target_prepare_pending)
            self.dashboard._handle_packet(receive_only)
        prepare.assert_called_once_with("T22TT", "")
        self.assertFalse(self.dashboard.target_prepare_pending)


if __name__ == "__main__":
    unittest.main()
