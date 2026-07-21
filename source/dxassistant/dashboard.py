from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import tkinter as tk
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from tkinter import messagebox, simpledialog, ttk

from . import __version__
from .bands import (
    STANDARD_FT8_FREQUENCIES_MHZ,
    band_for_frequency,
    band_limits_mhz,
    is_standard_ft8_frequency,
)
from .config import (
    PSK_REPORTER_DISTANCES_KM,
    save_band_enabled,
    save_band_frequencies,
    save_band_frequency,
    save_band_power,
    save_psk_search_area,
    save_target_call,
)
from .engine import DXEngine
from .hopping import SearchSession, SearchState
from .logging import DecodeLogger, EventLogger
from .omnirig import OmniRigClient, OmniRigError
from .protocol import Decode, Heartbeat, Status
from .pskreporter import PSKReporterClient, PSKReporterError, rank_bands
from .receiver import UDPReceiver, WSJTXRequestError
from .state import AppState, StateMachine


STATE_COLOURS = {
    AppState.STOPPED: "#5f6368",
    AppState.STARTING: "#b06000",
    AppState.MONITORING: "#137333",
    AppState.TARGET_DECODED: "#b31412",
    AppState.DEGRADED: "#b06000",
    AppState.ERROR: "#b31412",
}
MAX_RECENT_DECODES = 12
PSK_REPORTER_POLL_SECONDS = 300
BUTTON_GREEN = "#c6efce"
BUTTON_AMBER = "#ffeb9c"
BUTTON_NEUTRAL = "#f0f0f0"
BUTTON_DISABLED = "#e1e1e1"


class Dashboard:
    def __init__(self, root: tk.Tk, config):
        self.root = root
        self.config = config
        self.events = queue.Queue()
        self.engine = DXEngine(config.target_call)
        self.machine = StateMachine()
        self.logger = DecodeLogger(config.log_directory)
        self.event_logger = EventLogger(config.log_directory)
        self.receiver = UDPReceiver(config.udp_host, config.udp_port, self.events)
        self.omnirig = OmniRigClient()
        self.pskr_client = PSKReporterClient()
        self.search = SearchSession(120)
        self.tune_in_progress = False
        self.session_band_frequencies = {
            name: band.frequency_mhz for name, band in config.bands.items()
        }
        self.session_band_enabled = {
            name: band.enabled for name, band in config.bands.items()
        }
        self.band_power_watts = {
            name: band.power_watts for name, band in config.bands.items()
        }
        self.last_packet_utc = None
        self.alarm_active = False
        self.current_band = "-"
        self.suppressed_target_band = None
        self.latest_target_grid = ""
        self.wsjtx_status_available = False
        self.target_prepare_pending = True
        self.station_locator = config.station_locator
        self.pskr_distance_km = config.psk_reporter_distance_km
        self.pskr_poll_in_progress = False
        self.pskr_next_poll = 0.0
        self.pskr_priority_bands = []
        self.last_search_error = ""
        self.alarm_muted_until = 0.0
        self.rig_compatibility_text = "Not checked"
        self.rig_check_in_progress = False

        root.title(f"DX Assistant {__version__}")
        root.geometry("1040x760")
        root.minsize(880, 600)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._build()
        self._audit("application_started", "Dashboard opened", version=__version__)
        self._show_state("Ready")
        self._update_controls()
        root.after(100, self._poll_events)
        root.after(1000, self._check_timeout)
        root.after(250, self._search_tick)
        root.after(1000, self._pskr_tick)

    def _build(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Metric.TLabel", font=("Segoe UI", 14, "bold"))

        header = ttk.Frame(self.root, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="DX Assistant", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="RX ONLY - NO TRANSMIT CONTROL", foreground="#137333").pack(side="right")

        summary = ttk.LabelFrame(self.root, text="Monitoring status", padding=12)
        summary.pack(fill="x", padx=16, pady=(0, 10))
        for column in range(6):
            summary.columnconfigure(column, weight=1)
        self.values = {name: tk.StringVar(value=value) for name, value in {
            "state": "Stopped", "target": self.config.target_call, "connection": "Not listening",
            "frequency": "-", "mode": "-", "counts": "0 / 0",
        }.items()}
        metrics = (("State", "state"), ("Target", "target"), ("WSJT-X", "connection"),
                   ("Frequency", "frequency"), ("Mode", "mode"), ("Decodes / target", "counts"))
        for column, (label, key) in enumerate(metrics):
            ttk.Label(summary, text=label).grid(row=0, column=column, sticky="w")
            metric = ttk.Label(summary, textvariable=self.values[key], style="Metric.TLabel")
            metric.grid(row=1, column=column, sticky="w", padx=(0, 10))
            if key == "state":
                self.state_label = metric

        controls = ttk.Frame(self.root, padding=(16, 0, 16, 10))
        controls.pack(fill="x")
        self.start_button = self._action_button(
            controls, "Start monitoring", self.start
        )
        self.stop_button = self._action_button(controls, "Stop", self.stop)
        self.target_button = ttk.Button(controls, text="Change target", command=self.change_target)
        self.ack_button = self._action_button(
            controls, "Acknowledge target alert", self.acknowledge
        )
        self.clear_button = ttk.Button(controls, text="Clear displays", command=self.clear_decodes)
        self.mute_button = ttk.Button(controls, text="Mute 15 min", command=self.mute_alarm)
        self.diagnostics_button = ttk.Button(
            controls, text="Diagnostics", command=self.show_diagnostics
        )
        self.prepare_dx_button = self._action_button(
            controls, "Re-send target to WSJT-X", self.prepare_dx
        )
        for button in (
            self.start_button,
            self.stop_button,
            self.target_button,
            self.ack_button,
            self.prepare_dx_button,
            self.clear_button,
            self.mute_button,
            self.diagnostics_button,
        ):
            button.pack(side="left", padx=(0, 8))

        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        bands_frame = ttk.LabelFrame(panes, text="Session band plan", padding=8)
        activity_panes = ttk.PanedWindow(panes, orient="vertical")
        panes.add(bands_frame, weight=1)
        panes.add(activity_panes, weight=4)

        self.bands = ttk.Treeview(
            bands_frame,
            columns=("band", "enabled", "frequency", "power"),
            show="headings",
            height=9,
        )
        self.bands.heading("band", text="Band")
        self.bands.heading("enabled", text="On")
        self.bands.heading("frequency", text="FT8 MHz")
        self.bands.heading("power", text="Max W")
        self.bands.column("band", width=45, anchor="center")
        self.bands.column("enabled", width=35, anchor="center")
        self.bands.column("frequency", width=75, anchor="e")
        self.bands.column("power", width=55, anchor="e")
        self.bands.tag_configure("disabled", foreground="#777777")
        self.bands.tag_configure(
            "nonstandard", foreground="#b31412", font=("Segoe UI", 9, "bold")
        )
        self.bands.tag_configure(
            "disabled_nonstandard", foreground="#b31412"
        )
        self.bands.tag_configure(
            "current", background="#d9ead3", foreground="#137333", font=("Segoe UI", 9, "bold")
        )
        self.bands.tag_configure(
            "current_nonstandard",
            background="#d9ead3",
            foreground="#b31412",
            font=("Segoe UI", 9, "bold"),
        )
        self.bands.tag_configure(
            "current_disabled", background="#fce8cc", foreground="#b06000", font=("Segoe UI", 9, "bold")
        )
        for name, band in self.config.bands.items():
            self.bands.insert("", "end", iid=name)
            self._render_band_row(name)
        self.bands.pack(fill="x", pady=(0, 6))
        current_band_frame = ttk.LabelFrame(bands_frame, text="Current band", padding=(8, 5))
        current_band_frame.pack(fill="x", pady=(0, 6))
        self.current_band_text = tk.StringVar(value="Waiting for status")
        self.current_band_label = ttk.Label(
            current_band_frame,
            textvariable=self.current_band_text,
            style="Metric.TLabel",
        )
        self.current_band_label.pack(anchor="center")
        self.tx_offset_text = tk.StringVar(value="WSJT-X Tx offset: waiting")
        self.tx_offset_label = ttk.Label(
            current_band_frame,
            textvariable=self.tx_offset_text,
        )
        self.tx_offset_label.pack(anchor="center", pady=(3, 0))

        search_frame = ttk.LabelFrame(bands_frame, text="Band search", padding=8)
        search_frame.pack(fill="x", pady=(0, 6))
        dwell_row = ttk.Frame(search_frame)
        dwell_row.pack(fill="x", pady=(0, 5))
        ttk.Label(dwell_row, text="Dwell").pack(side="left")
        self.dwell_value = tk.StringVar(value="120")
        self.dwell_selector = ttk.Combobox(
            dwell_row,
            textvariable=self.dwell_value,
            values=("60", "90", "120", "180", "240", "300"),
            state="readonly",
            width=5,
        )
        self.dwell_selector.pack(side="left", padx=(6, 3))
        ttk.Label(dwell_row, text="seconds").pack(side="left")
        self.search_status = tk.StringVar(value="Not started")
        ttk.Label(
            search_frame,
            textvariable=self.search_status,
            anchor="center",
            justify="center",
            wraplength=215,
        ).pack(fill="x", pady=(0, 5))
        self.search_button = self._action_button(
            search_frame, "Start band search", self.search_action
        )
        self.search_button.pack(fill="x")

        self.monitor_selected_button = ttk.Button(
            search_frame,
            text="Monitor selected band now",
            command=self.monitor_selected_band,
        )
        self.monitor_selected_button.pack(fill="x", pady=(4, 0))
        self.compatibility_button = ttk.Button(
            search_frame,
            text="Check OmniRig compatibility",
            command=self.check_rig_compatibility,
        )
        self.compatibility_button.pack(fill="x", pady=(4, 0))

        pskr_frame = ttk.LabelFrame(bands_frame, text="PSK Reporter", padding=(8, 5))
        pskr_frame.pack(fill="x", pady=(0, 6))
        area_row = ttk.Frame(pskr_frame)
        area_row.pack(fill="x", pady=(0, 4))
        ttk.Label(area_row, text="Area").pack(side="left")
        self.locator_value = tk.StringVar(value=self.station_locator)
        self.locator_entry = ttk.Entry(area_row, textvariable=self.locator_value, width=7)
        self.locator_entry.pack(side="left", padx=(5, 5))
        self.distance_value = tk.StringVar(value=str(self.pskr_distance_km))
        self.distance_selector = ttk.Combobox(
            area_row,
            textvariable=self.distance_value,
            values=tuple(str(value) for value in PSK_REPORTER_DISTANCES_KM),
            state="readonly",
            width=5,
        )
        self.distance_selector.pack(side="left")
        ttk.Label(area_row, text="km").pack(side="left", padx=(3, 5))
        self.apply_area_button = ttk.Button(
            area_row, text="Apply", width=6, command=self.apply_psk_search_area
        )
        self.apply_area_button.pack(side="right")
        initial_pskr_status = (
            f"Waiting for {self.config.target_call} near {self.station_locator} - full sweep"
            if self.config.psk_reporter_enabled
            else "Disabled - full sweep"
        )
        self.pskr_status_text = tk.StringVar(value=initial_pskr_status)
        ttk.Label(
            pskr_frame,
            textvariable=self.pskr_status_text,
            anchor="center",
            justify="center",
            wraplength=225,
        ).pack(fill="x")

        band_controls = ttk.Frame(bands_frame)
        band_controls.pack(fill="x")
        self.edit_frequency_button = self._action_button(
            band_controls, "Edit frequency", self.edit_band_frequency
        )
        self.toggle_band_button = self._action_button(
            band_controls, "Enable / disable", self.toggle_selected_band
        )
        self.edit_power_button = self._action_button(
            band_controls, "Edit max drive", self.edit_band_power
        )
        self.reset_frequencies_button = self._action_button(
            band_controls, "Restore frequencies", self.restore_default_frequencies
        )
        band_controls.columnconfigure(0, weight=1)
        band_controls.columnconfigure(1, weight=1)
        self.edit_frequency_button.grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=(0, 4))
        self.toggle_band_button.grid(row=0, column=1, sticky="ew", padx=(2, 0), pady=(0, 4))
        self.edit_power_button.grid(row=1, column=0, sticky="ew", padx=(0, 2))
        self.reset_frequencies_button.grid(row=1, column=1, sticky="ew", padx=(2, 0))

        recent_frame = ttk.LabelFrame(activity_panes, text=f"Recent WSJT-X activity (latest {MAX_RECENT_DECODES})", padding=8)
        target_frame = ttk.LabelFrame(activity_panes, text="Target decodes - retained for this session", padding=8)
        activity_panes.add(recent_frame, weight=1)
        activity_panes.add(target_frame, weight=3)
        self.recent_decodes = self._create_decode_table(recent_frame, height=5)
        self.target_decodes = self._create_decode_table(target_frame, height=11)

        self.status_text = tk.StringVar(value="Ready")
        status = ttk.Label(self.root, textvariable=self.status_text, relief="sunken", anchor="w", padding=(8, 4))
        status.pack(fill="x", side="bottom")

    @staticmethod
    def _action_button(parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9),
            relief="raised",
            borderwidth=1,
            padx=8,
            pady=2,
        )

    @staticmethod
    def _set_action_state(button, enabled: bool, colour: str) -> None:
        button.configure(
            state="normal" if enabled else "disabled",
            background=colour if enabled else BUTTON_DISABLED,
            activebackground=colour,
            foreground="#202124" if enabled else "#777777",
            disabledforeground="#777777",
        )

    def _create_decode_table(self, parent, height):
        columns = ("time", "band", "snr", "offset", "message")
        table = ttk.Treeview(parent, columns=columns, show="headings", height=height)
        widths = (75, 55, 55, 65, 475)
        headings = ("Time", "Band", "SNR", "Offset", "Message")
        for name, heading, width in zip(columns, headings, widths):
            table.heading(name, text=heading)
            table.column(name, width=width, anchor="e" if name in {"snr", "offset"} else "center" if name == "band" else "w")
        table.tag_configure("target", background="#fce8e6", foreground="#b31412")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return table

    def start(self):
        if self.machine.current not in {AppState.STOPPED, AppState.ERROR}:
            return
        self.machine.transition(AppState.STARTING, "Operator selected Start")
        self._audit("monitoring_start_requested", "Operator selected Start")
        self.target_prepare_pending = True
        self._show_state(
            f"Opening WSJT-X listener; {self.engine.state.target_call} will be prepared when connected"
        )
        self.receiver.start()
        self._update_controls()

    def stop(self):
        self._audit("monitoring_stopped", "Operator selected Stop")
        self.receiver.stop()
        self.wsjtx_status_available = False
        self.search.stop()
        self.search_status.set("Not started")
        self.suppressed_target_band = None
        self.pskr_priority_bands = []
        self.last_search_error = ""
        self.pskr_next_poll = 0.0
        self.pskr_status_text.set(
            f"Waiting for {self.engine.state.target_call} near {self.station_locator} - full sweep"
            if self.config.psk_reporter_enabled
            else "Disabled - full sweep"
        )
        if self.machine.current != AppState.STOPPED:
            self.machine.transition(AppState.STOPPED, "Operator selected Stop")
        self.alarm_active = False
        self.values["connection"].set("Not listening")
        self._show_state("Monitoring stopped")
        self._update_controls()

    def acknowledge(self):
        if not self.alarm_active:
            return
        self.alarm_active = False
        self._audit("target_alarm_acknowledged", "Operator acknowledged target alert")
        if self.search.state == SearchState.TARGET_HOLD:
            self.suppressed_target_band = self.search.current_band
        elif self.current_band != "-":
            self.suppressed_target_band = self.current_band
        if self.machine.current == AppState.TARGET_DECODED:
            self.machine.transition(AppState.MONITORING, "Target alarm acknowledged")
        self._show_state("Alarm acknowledged; monitoring continues")
        self._update_controls()

    def _enabled_band_names(self):
        return [name for name in self.config.bands if self.session_band_enabled[name]]

    def _search_band_names(self):
        enabled = self._enabled_band_names()
        focused = [band for band in self.pskr_priority_bands if band in enabled]
        return focused or enabled

    def search_action(self):
        if self.search.state in {SearchState.SEARCHING, SearchState.STARTING}:
            self.search.pause()
            self._audit("search_paused", "Operator selected Pause search")
            self.search_status.set("Paused - select Resume search when ready")
            self._update_controls()
            return
        if self.search.state == SearchState.STOPPED:
            self._begin_search()
            return
        self._resume_search()

    def _begin_search(self):
        if self.machine.current not in {AppState.MONITORING, AppState.DEGRADED}:
            messagebox.showinfo(
                "Start monitoring first",
                "Start WSJT-X monitoring and wait for its status before starting the band search.",
                parent=self.root,
            )
            return
        if not self.engine.state.dial_frequency_hz:
            messagebox.showinfo(
                "Waiting for WSJT-X",
                "No WSJT-X frequency status has been received yet.",
                parent=self.root,
            )
            return
        if self.engine.state.tx_enabled or self.engine.state.transmitting:
            messagebox.showwarning(
                "Transmit control active",
                "Disable Enable Tx in WSJT-X before starting the band search.",
                parent=self.root,
            )
            return
        enabled = self._search_band_names()
        if not enabled:
            messagebox.showerror("No enabled bands", "Enable at least one band before starting the search.", parent=self.root)
            return
        self.search = SearchSession(int(self.dwell_value.get()))
        self.last_search_error = ""
        current = band_for_frequency(self.engine.state.dial_frequency_hz)
        band = current if current in enabled else enabled[0]
        self.search.begin()
        self._start_tune(band)

    def _resume_search(self):
        if not self.search.can_resume(
            self.engine.state.tx_enabled, self.engine.state.transmitting
        ):
            return
        enabled = self._search_band_names()
        if not enabled:
            messagebox.showerror("No enabled bands", "Enable at least one band before resuming the search.", parent=self.root)
            return
        self.search.dwell_seconds = int(self.dwell_value.get())
        self.last_search_error = ""
        if self.search.state == SearchState.ERROR:
            current = band_for_frequency(self.engine.state.dial_frequency_hz)
            band = current if current in enabled else enabled[0]
        else:
            band = self.search.next_band(enabled)
        self.search.begin()
        self._start_tune(band)

    def monitor_selected_band(self):
        selection = self.bands.selection()
        if not selection:
            messagebox.showinfo(
                "Select a band",
                "Select an enabled band in the Session band plan first.",
                parent=self.root,
            )
            return
        band = selection[0]
        if not self.session_band_enabled[band]:
            messagebox.showwarning(
                "Band disabled",
                f"Enable {band} for the attached antenna before monitoring it.",
                parent=self.root,
            )
            return
        if self.machine.current not in {AppState.MONITORING, AppState.DEGRADED}:
            messagebox.showinfo(
                "Start monitoring first",
                "Start WSJT-X monitoring and wait for its status before selecting a band.",
                parent=self.root,
            )
            return
        if not self.engine.state.dial_frequency_hz:
            messagebox.showinfo(
                "Waiting for WSJT-X",
                "No WSJT-X frequency status has been received yet.",
                parent=self.root,
            )
            return
        if self.engine.state.tx_enabled or self.engine.state.transmitting:
            messagebox.showwarning(
                "Transmit control active",
                "Disable Enable Tx in WSJT-X before changing bands.",
                parent=self.root,
            )
            return
        if self.alarm_active or self.tune_in_progress:
            return
        self.search = SearchSession(int(self.dwell_value.get()))
        self.search.begin()
        self.bands.selection_remove(*selection)
        self._start_tune(band)

    def _start_tune(self, band):
        if self.tune_in_progress:
            return
        if self.engine.state.tx_enabled or self.engine.state.transmitting:
            self.search.hand_to_operator()
            self.search_status.set("Operator control - Enable Tx is active")
            self._update_controls()
            return
        self.tune_in_progress = True
        frequency_hz = int(round(self.session_band_frequencies[band] * 1_000_000))
        self._audit("tune_requested", f"Align VFO A and B to {band}", band=band, frequency_hz=frequency_hz)
        self.search_status.set(f"Aligning A and B to {band}...")
        self._update_controls()

        def worker():
            try:
                result = self.omnirig.align(frequency_hz)
                self.events.put(("tune_result", (band, result, None)))
            except OmniRigError as error:
                self.events.put(("tune_result", (band, None, str(error))))

        threading.Thread(target=worker, name="OmniRigTune", daemon=True).start()

    def _handle_tune_result(self, payload):
        band, result, error = payload
        self.tune_in_progress = False
        if error:
            self.search.fail()
            self.last_search_error = error
            self.search_status.set(f"Search blocked: {error}")
            self._show_state(f"OmniRig tuning blocked: {error}")
            self._audit("tune_failed", error, band=band)
            self._update_controls()
            return
        self.search.current_band = band
        self._audit(
            "tune_verified",
            f"VFO A and B verified on {band}",
            band=band,
            receive_frequency_hz=result.receive_frequency_hz,
        )
        self.last_search_error = ""
        if self.suppressed_target_band and band != self.suppressed_target_band:
            self.suppressed_target_band = None
        if self.search.state in {SearchState.STARTING, SearchState.SEARCHING}:
            self.search.tuned(band, time.monotonic())
            self.search_status.set(f"{band} - {self.search.dwell_seconds}s remaining")
            self.status_text.set(
                f"Band search on {band}: A and B verified at {result.receive_frequency_hz / 1_000_000:.3f} MHz"
            )
        else:
            self.search_status.set(f"{self.search.state.value} on {band}")
        self._update_controls()

    def _search_tick(self):
        now = time.monotonic()
        if self.search.state in {SearchState.SEARCHING, SearchState.STARTING} and (
            self.engine.state.tx_enabled or self.engine.state.transmitting
        ):
            self.search.hand_to_operator()
            self.search_status.set("Operator control - search remains paused")
        elif self.search.state == SearchState.SEARCHING:
            remaining = self.search.remaining(now)
            if remaining is not None:
                minutes, seconds = divmod(remaining, 60)
                self.search_status.set(
                    f"{self.search.current_band} - {minutes}:{seconds:02} remaining"
                )
            if (
                self.search.is_due(now)
                and not self.tune_in_progress
                and not self.engine.state.decoding
            ):
                enabled = self._search_band_names()
                if not enabled:
                    self.search.pause()
                    self.search_status.set("Paused - no bands enabled")
                else:
                    next_band = self.search.next_band(enabled)
                    if next_band == self.search.current_band:
                        self.search.tuned(next_band, now)
                    else:
                        self._start_tune(next_band)
        self._update_controls()
        self.root.after(250, self._search_tick)

    def change_target(self):
        if self.machine.current != AppState.STOPPED:
            return
        value = simpledialog.askstring(
            "Change target",
            "Enter the callsign to identify as the transmitting station:",
            initialvalue=self.engine.state.target_call,
            parent=self.root,
        )
        if value is None:
            return
        target = value.strip().upper()
        compact = target.replace("/", "")
        valid = (
            bool(re.fullmatch(r"[A-Z0-9/]{3,15}", target))
            and any(character.isalpha() for character in compact)
            and any(character.isdigit() for character in compact)
        )
        if not valid:
            messagebox.showerror("Invalid callsign", "Enter one callsign, for example T22TT or G8AJM.", parent=self.root)
            return
        try:
            save_target_call(self.config, target)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Could not save target",
                f"The target was not changed because it could not be saved:\n\n{error}",
                parent=self.root,
            )
            return
        self.engine = DXEngine(target)
        self._audit("target_changed", f"Target changed to {target}", target=target)
        self.values["target"].set(target)
        self.values["counts"].set("0 / 0")
        self.alarm_active = False
        self.suppressed_target_band = None
        self.latest_target_grid = ""
        self.target_prepare_pending = True
        self.pskr_priority_bands = []
        self.pskr_next_poll = 0.0
        self.pskr_status_text.set(
            f"Waiting for {target} near {self.station_locator} - full sweep"
        )
        self._show_state(
            f"Target changed to {target} and saved; select Start monitoring to prepare it in WSJT-X"
        )
        self._update_controls()

    def apply_psk_search_area(self):
        locator = self.locator_value.get().strip().upper()
        try:
            distance_km = int(self.distance_value.get())
            save_psk_search_area(self.config, locator, distance_km)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Invalid PSK search area",
                f"The search area was not changed:\n{error}",
                parent=self.root,
            )
            return
        self.station_locator = locator
        self._audit("psk_area_changed", "PSK Reporter search area saved", locator=locator, distance_km=distance_km)
        self.pskr_distance_km = distance_km
        self.locator_value.set(locator)
        self.pskr_priority_bands = []
        self.pskr_next_poll = 0.0
        self.pskr_status_text.set(
            f"Area {locator}, {distance_km} km saved - refreshing"
        )

    def prepare_dx(self):
        if self.engine.state.tx_enabled or self.engine.state.transmitting:
            return
        self._send_prepare_dx(show_error=True)

    def _send_prepare_dx(self, show_error: bool) -> bool:
        """Prepare the selected target without enabling or initiating transmit."""

        try:
            self.receiver.prepare_dx(
                self.engine.state.target_call, self.latest_target_grid
            )
        except WSJTXRequestError as error:
            if show_error:
                messagebox.showerror(
                    "Could not prepare DX",
                    f"{error}\n\nIn WSJT-X, enable Settings > Reporting > Accept UDP requests.",
                    parent=self.root,
                )
            return False
        self.target_prepare_pending = False
        self._audit(
            "wsjtx_target_prepared",
            "Configure-only request sent",
            target=self.engine.state.target_call,
            grid=self.latest_target_grid,
        )
        grid_note = f" and locator {self.latest_target_grid}" if self.latest_target_grid else ""
        self.status_text.set(
            f"Prepare request sent for {self.engine.state.target_call}{grid_note}; "
            "check WSJT-X, confirm the period, then select Enable Tx"
        )
        return True

    def edit_band_frequency(self):
        if self.machine.current != AppState.STOPPED:
            return
        selection = self.bands.selection()
        if not selection:
            messagebox.showinfo(
                "Select a band",
                "Select a band in the Enabled bands list first.",
                parent=self.root,
            )
            return
        band = selection[0]
        current = self.session_band_frequencies[band]
        value = simpledialog.askstring(
            f"{band} session frequency",
            f"Enter the receive frequency in MHz for {band}:\n"
            "This change applies only to the current DX Assistant session.",
            initialvalue=f"{current:.3f}",
            parent=self.root,
        )
        if value is None:
            return
        try:
            frequency_mhz = float(
                Decimal(value.strip()).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            )
        except (InvalidOperation, ValueError):
            messagebox.showerror("Invalid frequency", "Enter a frequency in MHz, for example 14.095000.", parent=self.root)
            return
        limits = band_limits_mhz(band)
        if limits is None or not limits[0] <= frequency_mhz <= limits[1]:
            if limits is None:
                permitted = "the selected amateur band"
            else:
                permitted = f"{limits[0]:.3f} to {limits[1]:.3f} MHz"
            messagebox.showerror(
                "Frequency outside band",
                f"The {band} session frequency must be within {permitted}.",
                parent=self.root,
            )
            return
        try:
            save_band_frequency(self.config, band, frequency_mhz)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Could not save frequency",
                f"The frequency was not changed:\n{error}",
                parent=self.root,
            )
            return
        self.session_band_frequencies[band] = frequency_mhz
        self._render_band_row(band)
        self.status_text.set(
            f"{band} frequency saved as {frequency_mhz:.3f} MHz"
        )

    def toggle_selected_band(self):
        if self.machine.current != AppState.STOPPED:
            return
        selection = self.bands.selection()
        if not selection:
            messagebox.showinfo(
                "Select a band",
                "Select a band in the Session band plan first.",
                parent=self.root,
            )
            return
        band = selection[0]
        enabled = not self.session_band_enabled[band]
        try:
            save_band_enabled(self.config, band, enabled)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Could not save antenna plan",
                f"The band selection was not changed:\n{error}",
                parent=self.root,
            )
            return
        self.session_band_enabled[band] = enabled
        self._render_band_row(band)
        if band == self.current_band:
            self._set_current_band(self.engine.state.dial_frequency_hz)
        state = "enabled" if self.session_band_enabled[band] else "disabled"
        self.status_text.set(f"{band} {state} and saved for the antenna plan")
        self.bands.selection_remove(*selection)

    def edit_band_power(self):
        if self.machine.current != AppState.STOPPED:
            return
        selection = self.bands.selection()
        if not selection:
            messagebox.showinfo(
                "Select a band",
                "Select a band in the Session band plan first.",
                parent=self.root,
            )
            return
        band = selection[0]
        current = self.band_power_watts[band]
        value = simpledialog.askstring(
            f"{band} maximum drive",
            "Enter the maximum-drive reference in watts (5-100).\n\n"
            "This stores a persistent safety profile only. It is not yet sent to the radio.",
            initialvalue="" if current is None else str(current),
            parent=self.root,
        )
        if value is None:
            return
        try:
            power_watts = int(value.strip())
        except ValueError:
            messagebox.showerror("Invalid power", "Enter a whole number from 5 to 100 watts.", parent=self.root)
            return
        if not 5 <= power_watts <= 100:
            messagebox.showerror("Power outside range", "Maximum-drive reference must be between 5 and 100 watts.", parent=self.root)
            return
        previous = self.band_power_watts[band]
        self.band_power_watts[band] = power_watts
        try:
            save_band_power(self.config, band, power_watts)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.band_power_watts[band] = previous
            messagebox.showerror(
                "Could not save power profile",
                f"The radio was not changed. The profile could not be saved:\n{error}",
                parent=self.root,
            )
            return
        self._render_band_row(band)
        self.status_text.set(
            f"{band} maximum drive saved as {power_watts} W; no command was sent to the radio"
        )

    def _render_band_row(self, name):
        enabled = self.session_band_enabled[name]
        frequency = self.session_band_frequencies[name]
        power = self.band_power_watts[name]
        nonstandard = not is_standard_ft8_frequency(name, frequency)
        if name == self.current_band:
            if enabled:
                tags = ("current_nonstandard",) if nonstandard else ("current",)
            else:
                tags = ("current_disabled",)
        else:
            if enabled:
                tags = ("nonstandard",) if nonstandard else ()
            else:
                tags = ("disabled_nonstandard",) if nonstandard else ("disabled",)
        self.bands.item(
            name,
            values=(
                name,
                "Yes" if enabled else "No",
                f"{frequency:.3f}",
                "--" if power is None else str(power),
            ),
            tags=tags,
        )

    def _set_current_band(self, frequency_hz):
        previous = self.current_band
        self.current_band = band_for_frequency(frequency_hz)
        if (
            self.suppressed_target_band
            and self.current_band != self.suppressed_target_band
        ):
            self.suppressed_target_band = None
        if previous in self.session_band_enabled:
            self._render_band_row(previous)
        if self.current_band in self.session_band_enabled:
            self._render_band_row(self.current_band)
            enabled = self.session_band_enabled[self.current_band]
            self.current_band_text.set(
                self.current_band if enabled else f"{self.current_band} - disabled in plan"
            )
            self.current_band_label.configure(
                foreground="#137333" if enabled else "#b06000"
            )
        elif self.current_band == "-":
            self.current_band_text.set("Outside known amateur bands")
            self.current_band_label.configure(foreground="#b06000")
        else:
            self.current_band_text.set(f"{self.current_band} - not in session plan")
            self.current_band_label.configure(foreground="#b06000")

    def restore_default_frequencies(self):
        if self.machine.current != AppState.STOPPED:
            return
        standards = {
            name: STANDARD_FT8_FREQUENCIES_MHZ[name]
            for name in self.config.bands
            if name in STANDARD_FT8_FREQUENCIES_MHZ
        }
        try:
            save_band_frequencies(self.config, standards)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Could not restore frequencies",
                f"The frequencies were not changed:\n{error}",
                parent=self.root,
            )
            return
        for name, frequency_mhz in standards.items():
            self.session_band_frequencies[name] = frequency_mhz
            self._render_band_row(name)
        if self.current_band in self.session_band_enabled:
            self._set_current_band(self.engine.state.dial_frequency_hz)
        self.status_text.set(
            "Standard FT8 frequencies restored and saved; antenna band selection unchanged"
        )

    def clear_decodes(self):
        for table in (self.recent_decodes, self.target_decodes):
            for item in table.get_children():
                table.delete(item)
        self.status_text.set("Decode displays cleared; the full CSV log is unchanged")
        self._audit("displays_cleared", "Operator cleared decode displays")

    def mute_alarm(self):
        self.alarm_muted_until = time.monotonic() + 15 * 60
        self._audit("alarm_muted", "Audible alarm muted for 15 minutes")
        self.status_text.set("Audible target alarm muted for 15 minutes; visual alerts remain active")

    def test_alarm(self):
        if self.config.alarm_enabled and time.monotonic() >= self.alarm_muted_until:
            self.root.bell()
            self._audit("alarm_tested", "Operator tested audible alarm")
            self.status_text.set("Alarm test sounded")
        else:
            self.status_text.set("Alarm sound is disabled or temporarily muted")

    def show_diagnostics(self):
        window = tk.Toplevel(self.root)
        window.title("DX Assistant diagnostics")
        window.geometry("660x390")
        text = tk.Text(window, wrap="word", padx=10, pady=10)
        text.pack(fill="both", expand=True)
        details = (
            f"DX Assistant: {__version__}\n"
            f"State: {self.machine.current.value}\n"
            f"Target: {self.engine.state.target_call}\n"
            f"WSJT-X: {self.values['connection'].get()}\n"
            f"Current band: {self.current_band}\n"
            f"Search: {self.search_status.get()}\n"
            f"PSK Reporter: {self.pskr_status_text.get()}\n"
            f"Last search error: {self.last_search_error or 'None'}\n"
            f"OmniRig compatibility: {self.rig_compatibility_text}\n"
            f"Configuration: {self.config.source_path}\n"
            f"Logs: {self.config.log_directory}\n"
            f"Buffered audit records: {len(self.event_logger.pending)}\n"
            f"Last log error: {self.event_logger.last_error or 'None'}\n"
        )
        text.insert("1.0", details)
        text.configure(state="disabled")
        buttons = ttk.Frame(window, padding=8)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Test alarm", command=self.test_alarm).pack(side="left")
        ttk.Button(buttons, text="Open log folder", command=self.open_log_folder).pack(side="left", padx=8)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
        self._audit("diagnostics_opened", "Operator opened diagnostics")

    def check_rig_compatibility(self):
        """Read OmniRig capabilities only; this performs no radio writes."""

        if self.rig_check_in_progress:
            return
        self.rig_check_in_progress = True
        self.compatibility_button.configure(state="disabled")
        self.status_text.set("Reading OmniRig Rig 1 capabilities; no tuning will occur...")

        def worker():
            try:
                self.events.put(("rig_check_result", (self.omnirig.status(), None)))
            except OmniRigError as error:
                self.events.put(("rig_check_result", (None, str(error))))

        threading.Thread(target=worker, name="OmniRigCompatibility", daemon=True).start()

    def _handle_rig_check_result(self, payload):
        result, error = payload
        self.rig_check_in_progress = False
        self.compatibility_button.configure(state="normal")
        if error:
            self.rig_compatibility_text = f"Check failed: {error}"
            self._audit("rig_compatibility_failed", error)
            self.status_text.set(self.rig_compatibility_text)
            return
        if result.compatible:
            self.rig_compatibility_text = (
                f"{result.rig_type}: compatible capability set; live validation required"
            )
        else:
            missing = ", ".join(result.missing_capabilities) or "unknown capability report"
            self.rig_compatibility_text = f"{result.rig_type}: incompatible - missing {missing}"
        self._audit(
            "rig_compatibility_checked",
            self.rig_compatibility_text,
            rig_type=result.rig_type,
            compatible=result.compatible,
            missing=list(result.missing_capabilities),
        )
        self.status_text.set(self.rig_compatibility_text)

    def open_log_folder(self):
        self.config.log_directory.mkdir(parents=True, exist_ok=True)
        os.startfile(self.config.log_directory)
        self._audit("log_folder_opened", "Operator opened log folder")

    def _audit(self, event: str, detail: str = "", **data):
        path = self.event_logger.write(event, detail, **data)
        if path is None and hasattr(self, "status_text"):
            self.status_text.set(
                f"Log warning: {self.event_logger.last_error}; events buffered in memory"
            )

    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "receiver_started":
                    self.machine.transition(AppState.MONITORING, "UDP listener started")
                    self._audit("monitoring_started", "UDP listener started")
                    self.values["connection"].set("Listening")
                    self._show_state(f"Listening on {self.config.udp_host}:{self.config.udp_port}")
                elif kind == "receiver_error":
                    if self.machine.current != AppState.ERROR:
                        self.machine.transition(AppState.ERROR, payload)
                    if self.search.state != SearchState.STOPPED:
                        self.search.fail()
                        self.search_status.set("Search error - WSJT-X listener failed")
                    self.values["connection"].set("Error")
                    self._show_state(f"Listener error: {payload}")
                    self._audit("receiver_error", str(payload))
                elif kind == "warning":
                    self.status_text.set(payload)
                elif kind == "packet":
                    self._handle_packet(payload)
                elif kind == "tune_result":
                    self._handle_tune_result(payload)
                elif kind == "pskr_result":
                    self._handle_pskr_result(payload)
                elif kind == "rig_check_result":
                    self._handle_rig_check_result(payload)
                self._update_controls()
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _pskr_tick(self):
        now = time.monotonic()
        if (
            self.config.psk_reporter_enabled
            and self.machine.current
            in {AppState.MONITORING, AppState.TARGET_DECODED, AppState.DEGRADED}
            and not self.pskr_poll_in_progress
            and now >= self.pskr_next_poll
        ):
            target = self.engine.state.target_call
            locator = self.station_locator
            distance_km = self.pskr_distance_km
            enabled_bands = self._enabled_band_names()
            lookback = self.config.psk_reporter_lookback_minutes
            self.pskr_poll_in_progress = True
            # Set the next permitted time before starting the request so even
            # failures cannot cause rapid retries against the public service.
            self.pskr_next_poll = now + PSK_REPORTER_POLL_SECONDS
            self.pskr_status_text.set(f"Checking {target} near {locator}...")

            def worker():
                try:
                    reports = self.pskr_client.fetch(target, lookback)
                    priorities = rank_bands(
                        reports,
                        locator,
                        enabled_bands,
                        lookback_minutes=lookback,
                        maximum_distance_km=distance_km,
                    )
                    self.events.put(
                        (
                            "pskr_result",
                            (target, locator, distance_km, priorities, len(reports), None),
                        )
                    )
                except (PSKReporterError, ValueError) as error:
                    self.events.put(
                        (
                            "pskr_result",
                            (target, locator, distance_km, [], 0, str(error)),
                        )
                    )

            threading.Thread(target=worker, name="PSKReporter", daemon=True).start()
        self.root.after(1000, self._pskr_tick)

    def _handle_pskr_result(self, payload):
        target, locator, distance_km, priorities, total_reports, error = payload
        self.pskr_poll_in_progress = False
        if (
            target != self.engine.state.target_call
            or locator != self.station_locator
            or distance_km != self.pskr_distance_km
            or self.machine.current == AppState.STOPPED
        ):
            return
        if error:
            self.pskr_priority_bands = []
            self.pskr_status_text.set("Unavailable - full enabled-band sweep")
            self._audit("psk_reporter_unavailable", error)
            return
        self.pskr_priority_bands = [priority.band for priority in priorities]
        if not priorities:
            self.pskr_status_text.set(
                f"No nearby recent {target} reports - full sweep"
            )
            return
        summary = "; ".join(
            f"{priority.band}: {priority.receiver_count} "
            f"{'receiver' if priority.receiver_count == 1 else 'receivers'}"
            for priority in priorities
        )
        self.pskr_status_text.set(
            f"Focus {summary} - {total_reports} reports checked"
        )

    def _handle_packet(self, packet):
        self.last_packet_utc = datetime.now(timezone.utc)
        result = self.engine.handle(packet)
        if self.machine.current == AppState.DEGRADED:
            self.machine.transition(AppState.MONITORING, "WSJT-X data resumed")
        if isinstance(packet, Heartbeat):
            self.values["connection"].set(f"{packet.wsjtx_id} {packet.version}")
            self.status_text.set("WSJT-X heartbeat received")
        elif isinstance(packet, Status):
            self.wsjtx_status_available = True
            self.values["frequency"].set(f"{packet.dial_frequency_hz / 1_000_000:.3f}")
            self.values["mode"].set(packet.mode or "-")
            if packet.tx_df_hz is None:
                self.tx_offset_text.set("WSJT-X Tx offset: unavailable")
                self.tx_offset_label.configure(foreground="#5f6368")
            else:
                self.tx_offset_text.set(f"WSJT-X Tx offset: {packet.tx_df_hz} Hz")
                self.tx_offset_label.configure(
                    foreground="#137333" if 0 <= packet.tx_df_hz <= 3000 else "#b06000"
                )
            self._set_current_band(packet.dial_frequency_hz)
            if (
                (packet.tx_enabled or packet.transmitting)
                and self.search.state != SearchState.STOPPED
            ):
                self.search.hand_to_operator()
                self.search_status.set("Operator control - search remains paused")
            if (
                self.target_prepare_pending
                and not packet.tx_enabled
                and not packet.transmitting
            ):
                self._send_prepare_dx(show_error=False)
        elif isinstance(packet, Decode) and result.decode is not None:
            tag = ("target",) if result.target_found else ()
            band = band_for_frequency(self.engine.state.dial_frequency_hz)
            values = (packet.time, band, packet.snr, packet.audio_frequency_hz, packet.message)
            self.recent_decodes.insert("", 0, values=values, tags=tag)
            recent_items = self.recent_decodes.get_children()
            while len(recent_items) > MAX_RECENT_DECODES:
                self.recent_decodes.delete(recent_items[-1])
                recent_items = self.recent_decodes.get_children()
            self.logger.write(packet, self.engine.state.dial_frequency_hz, result.target_found)
            if result.target_found:
                if result.transmitting_grid:
                    self.latest_target_grid = result.transmitting_grid
                self.target_decodes.insert("", 0, values=values, tags=("target",))
                if band != self.suppressed_target_band:
                    if self.search.state in {SearchState.SEARCHING, SearchState.STARTING}:
                        self.search.pause(target_found=True)
                        self.search_status.set(f"Target hold on {band} - search paused")
                    if self.machine.current in {AppState.MONITORING, AppState.DEGRADED}:
                        self.machine.transition(AppState.TARGET_DECODED, f"Decoded {self.config.target_call}")
                        self._audit("target_decoded", packet.message, band=band, snr=packet.snr)
                    if not self.alarm_active:
                        self.alarm_active = True
                        if self.config.alarm_enabled and time.monotonic() >= self.alarm_muted_until:
                            self.root.bell()
                        # Calling deiconify on an already visible snapped window
                        # can restore its old free-floating geometry on Windows.
                        # Restore only a genuinely minimized window; otherwise
                        # raise it without altering size or position.
                        if self.root.state() == "iconic":
                            self.root.deiconify()
                        self.root.lift()
                    self.status_text.set(f"TARGET FOUND: {packet.message}")
        self.values["counts"].set(f"{self.engine.state.decode_count} / {self.engine.state.target_decode_count}")
        self._show_state(self.status_text.get())

    def _check_timeout(self):
        if self.machine.current in {AppState.MONITORING, AppState.TARGET_DECODED} and self.last_packet_utc:
            elapsed = (datetime.now(timezone.utc) - self.last_packet_utc).total_seconds()
            if elapsed > self.config.heartbeat_timeout_seconds and self.machine.current != AppState.DEGRADED:
                self.machine.transition(AppState.DEGRADED, "WSJT-X data timeout")
                self._audit("wsjtx_timeout", "WSJT-X data timeout")
                self.values["connection"].set("No recent data")
                self._show_state("WSJT-X data timeout; waiting for recovery")
        self.root.after(1000, self._check_timeout)

    def _show_state(self, message):
        self.values["state"].set(self.machine.current.value)
        self.state_label.configure(foreground=STATE_COLOURS[self.machine.current])
        self.status_text.set(message)

    def _update_controls(self):
        stopped = self.machine.current in {AppState.STOPPED, AppState.ERROR}
        self._set_action_state(self.start_button, stopped, BUTTON_GREEN)
        self._set_action_state(
            self.stop_button,
            self.machine.current != AppState.STOPPED and not self.tune_in_progress,
            BUTTON_AMBER,
        )
        self.target_button.configure(state="normal" if self.machine.current == AppState.STOPPED else "disabled")
        for button in (
            self.edit_frequency_button,
            self.toggle_band_button,
            self.edit_power_button,
            self.reset_frequencies_button,
        ):
            self._set_action_state(
                button, self.machine.current == AppState.STOPPED, BUTTON_AMBER
            )
        self.monitor_selected_button.configure(
            state=(
                "normal"
                if self.machine.current in {AppState.MONITORING, AppState.DEGRADED}
                and self.engine.state.dial_frequency_hz
                and not self.engine.state.tx_enabled
                and not self.engine.state.transmitting
                and not self.alarm_active
                and not self.tune_in_progress
                else "disabled"
            )
        )
        self._set_action_state(self.ack_button, self.alarm_active, BUTTON_AMBER)
        self._set_action_state(
            self.prepare_dx_button,
            self.wsjtx_status_available
                and self.machine.current
                in {AppState.MONITORING, AppState.TARGET_DECODED, AppState.DEGRADED}
                and not self.engine.state.tx_enabled
                and not self.engine.state.transmitting,
            BUTTON_NEUTRAL,
        )
        if self.search.state == SearchState.STOPPED:
            self.search_button.configure(text="Start band search")
            self._set_action_state(
                self.search_button,
                self.machine.current in {AppState.MONITORING, AppState.DEGRADED}
                    and self.engine.state.dial_frequency_hz
                    and not self.engine.state.tx_enabled
                    and not self.engine.state.transmitting,
                BUTTON_GREEN,
            )
        elif self.search.state in {SearchState.SEARCHING, SearchState.STARTING}:
            self.search_button.configure(text="Pause search")
            self._set_action_state(
                self.search_button, not self.tune_in_progress, BUTTON_AMBER
            )
        else:
            self.search_button.configure(text="Resume search")
            self._set_action_state(
                self.search_button,
                self.search.can_resume(
                        self.engine.state.tx_enabled, self.engine.state.transmitting
                    )
                    and self.machine.current not in {AppState.STOPPED, AppState.ERROR}
                    and not self.alarm_active
                    and not self.tune_in_progress,
                BUTTON_GREEN,
            )
        self.dwell_selector.configure(
            state="disabled"
            if self.search.state in {SearchState.SEARCHING, SearchState.STARTING}
            else "readonly"
        )

    def close(self):
        if self.tune_in_progress:
            messagebox.showinfo(
                "Frequency alignment in progress",
                "Wait for the current OmniRig alignment to finish before closing.",
                parent=self.root,
            )
            return
        if self.machine.current != AppState.STOPPED:
            if not messagebox.askyesno("Close DX Assistant", "Stop monitoring and close DX Assistant?"):
                return
        self.receiver.stop()
        self.search.stop()
        self._audit("application_closed", "Dashboard closed")
        self.root.destroy()
