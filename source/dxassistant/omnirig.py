from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class OmniRigResult:
    rig_type: str
    status: str
    frequency_a_hz: int
    frequency_b_hz: int
    receive_frequency_hz: int
    split: str
    routing: str
    tx_state: str
    compatible: bool = False
    missing_capabilities: tuple[str, ...] = ()
    capabilities: dict[str, bool] = field(default_factory=dict)


class OmniRigError(RuntimeError):
    pass


class OmniRigClient:
    """Frequency-only adapter for the bundled, interlocked OmniRig bridge."""

    def __init__(self, bridge_path: Path | None = None):
        self.bridge_path = bridge_path or Path(__file__).with_name("omnirig_bridge.ps1")

    def status(self) -> OmniRigResult:
        return self._run("status")

    def align(self, frequency_hz: int) -> OmniRigResult:
        if not 1_800_000 <= frequency_hz <= 54_000_000:
            raise OmniRigError("Requested frequency is outside the supported HF/6m range")
        return self._run("align", frequency_hz)

    def _run(self, action: str, frequency_hz: int | None = None) -> OmniRigResult:
        powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        command = [
            str(powershell),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.bridge_path),
            "-Action",
            action,
        ]
        if frequency_hz is not None:
            command.extend(["-FrequencyHz", str(frequency_hz)])
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=creationflags,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise OmniRigError(f"Could not run the OmniRig bridge: {error}") from error
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip().startswith("{")]
        if not lines:
            detail = completed.stderr.strip() or completed.stdout.strip() or "No response"
            raise OmniRigError(f"OmniRig bridge failed: {detail}")
        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError as error:
            raise OmniRigError("OmniRig bridge returned invalid data") from error
        if not payload.get("ok"):
            raise OmniRigError(payload.get("message", "Unknown OmniRig error"))
        try:
            capability_data = payload.get("capabilities") or {}
            return OmniRigResult(
                rig_type=payload["rig_type"],
                status=payload["status"],
                frequency_a_hz=int(payload["frequency_a_hz"]),
                frequency_b_hz=int(payload["frequency_b_hz"]),
                receive_frequency_hz=int(payload["receive_frequency_hz"]),
                split=payload["split"],
                routing=payload["routing"],
                tx_state=payload["tx_state"],
                compatible=bool(capability_data.get("compatible", False)),
                missing_capabilities=tuple(capability_data.get("missing") or ()),
                capabilities=dict(capability_data.get("parameters") or {}),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise OmniRigError("OmniRig bridge returned incomplete or invalid data") from error
