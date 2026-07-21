from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .protocol import Decode, Heartbeat, Packet, Status


MESSAGE_TOKEN = re.compile(r"<([A-Z0-9/]+)>|([A-Z0-9/]+)")
GRID_TOKEN = re.compile(r"\b([A-R]{2}[0-9]{2}(?:[A-X]{2})?)\b", re.IGNORECASE)
CQ_MODIFIERS = {"DX", "TEST", "POTA", "SOTA", "WW", "NA", "EU", "AS", "AF", "SA", "OC", "QRP", "FD"}


def _tokens(message: str) -> list[str]:
    return [(first or second).upper() for first, second in MESSAGE_TOKEN.findall(message.upper())]


def _looks_like_call(value: str) -> bool:
    compact = value.replace("/", "")
    return 3 <= len(compact) <= 11 and any(c.isalpha() for c in compact) and any(c.isdigit() for c in compact)


def transmitting_call(message: str) -> str | None:
    """Return the station that sent a conventional FT8 message.

    Standard directed messages are ``TO FROM REPORT``. CQ/QRZ/DE messages
    place the sender after the prefix. Free text that does not identify a
    sender is deliberately left unmatched.
    """

    tokens = _tokens(message)
    if len(tokens) < 2:
        return None
    if tokens[0] in {"CQ", "QRZ", "DE"}:
        index = 1
        if tokens[0] == "CQ" and len(tokens) > 2:
            if tokens[1] in CQ_MODIFIERS or tokens[1].isdigit():
                index = 2
        candidate = tokens[index]
    else:
        candidate = tokens[1]
    return candidate if _looks_like_call(candidate) else None


def transmitting_grid(message: str) -> str | None:
    matches = GRID_TOKEN.findall(message.upper())
    return matches[-1].upper() if matches else None


@dataclass
class AssistantState:
    target_call: str
    wsjtx_id: str = ""
    wsjtx_version: str = ""
    dial_frequency_hz: int = 0
    mode: str = ""
    decoding: bool = False
    dx_call: str = ""
    tx_enabled: bool = False
    transmitting: bool = False
    last_heartbeat_utc: datetime | None = None
    decode_count: int = 0
    target_decode_count: int = 0


@dataclass(frozen=True)
class EngineResult:
    decode: Decode | None = None
    target_found: bool = False
    status_changed: bool = False
    transmitting_call: str | None = None
    transmitting_grid: str | None = None


class DXEngine:
    def __init__(self, target_call: str):
        self.state = AssistantState(target_call.upper())

    def handle(self, packet: Packet) -> EngineResult:
        if isinstance(packet, Heartbeat):
            self.state.wsjtx_id = packet.wsjtx_id
            self.state.wsjtx_version = packet.version
            self.state.last_heartbeat_utc = datetime.now(timezone.utc)
            return EngineResult(status_changed=True)
        if isinstance(packet, Status):
            changed = (
                self.state.dial_frequency_hz != packet.dial_frequency_hz
                or self.state.mode != packet.mode
                or self.state.decoding != packet.decoding
                or self.state.dx_call != packet.dx_call
                or self.state.tx_enabled != packet.tx_enabled
                or self.state.transmitting != packet.transmitting
            )
            self.state.wsjtx_id = packet.wsjtx_id
            self.state.dial_frequency_hz = packet.dial_frequency_hz
            self.state.mode = packet.mode
            self.state.decoding = packet.decoding
            self.state.dx_call = packet.dx_call
            self.state.tx_enabled = packet.tx_enabled
            self.state.transmitting = packet.transmitting
            return EngineResult(status_changed=changed)
        if isinstance(packet, Decode):
            if not packet.is_new:
                return EngineResult()
            self.state.decode_count += 1
            sender = transmitting_call(packet.message)
            target_found = sender == self.state.target_call
            if target_found:
                self.state.target_decode_count += 1
            return EngineResult(
                packet,
                target_found,
                transmitting_call=sender,
                transmitting_grid=transmitting_grid(packet.message) if target_found else None,
            )
        return EngineResult()
