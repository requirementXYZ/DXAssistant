from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import timedelta
from typing import Union


WSJTX_MAGIC = 0xADBCCBDA
WSJTX_CONFIGURE = 15


class PacketReader:
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0

    def read_bytes(self, length: int) -> bytes:
        if length < 0 or self.position + length > len(self.data):
            raise ValueError("Packet ended unexpectedly")
        value = self.data[self.position : self.position + length]
        self.position += length
        return value

    def read_uint32(self):
        return struct.unpack(">I", self.read_bytes(4))[0]

    def read_uint8(self):
        return struct.unpack(">B", self.read_bytes(1))[0]

    def read_uint64(self):
        return struct.unpack(">Q", self.read_bytes(8))[0]

    def read_int32(self):
        return struct.unpack(">i", self.read_bytes(4))[0]

    def read_double(self):
        return struct.unpack(">d", self.read_bytes(8))[0]

    def read_bool(self):
        return struct.unpack(">?", self.read_bytes(1))[0]

    def read_text(self):
        length = self.read_uint32()
        if length == 0xFFFFFFFF:
            return ""
        return self.read_bytes(length).decode("utf-8", errors="replace")

    def remaining(self) -> int:
        return len(self.data) - self.position


@dataclass(frozen=True)
class Heartbeat:
    wsjtx_id: str
    schema: int
    max_schema: int
    version: str
    revision: str


@dataclass(frozen=True)
class Status:
    wsjtx_id: str
    schema: int
    dial_frequency_hz: int
    mode: str
    dx_call: str
    tx_enabled: bool
    transmitting: bool
    decoding: bool
    rx_df_hz: int | None = None
    tx_df_hz: int | None = None
    de_call: str = ""
    de_grid: str = ""
    dx_grid: str = ""
    tx_watchdog: bool = False
    sub_mode: str = ""
    fast_mode: bool = False
    special_operation_mode: int = 0
    frequency_tolerance_hz: int | None = None
    tr_period_seconds: int | None = None
    configuration_name: str = ""
    tx_message: str = ""


@dataclass(frozen=True)
class Decode:
    wsjtx_id: str
    schema: int
    is_new: bool
    time: str
    snr: int
    delta_time: float
    audio_frequency_hz: int
    mode: str
    message: str


Packet = Union[Heartbeat, Status, Decode]


def encode_text(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


def build_prepare_dx(status: Status, dx_call: str, dx_grid: str = "") -> bytes:
    """Build only WSJT-X Configure(15); this cannot enable or halt transmit."""

    call = dx_call.strip().upper()
    grid = dx_grid.strip().upper()
    compact = call.replace("/", "")
    if not (
        3 <= len(compact) <= 15
        and all(character.isalnum() or character == "/" for character in call)
        and any(character.isalpha() for character in compact)
        and any(character.isdigit() for character in compact)
    ):
        raise ValueError("Invalid DX callsign")
    if grid and not (
        len(grid) in {4, 6, 8}
        and grid[:2].isalpha()
        and grid[2:4].isdigit()
    ):
        raise ValueError("Invalid DX locator")
    maximum = 0xFFFFFFFF
    return b"".join(
        (
            struct.pack(">III", WSJTX_MAGIC, status.schema, WSJTX_CONFIGURE),
            encode_text(status.wsjtx_id),
            encode_text(status.mode or "FT8"),
            struct.pack(">I", status.frequency_tolerance_hz if status.frequency_tolerance_hz is not None else maximum),
            encode_text(status.sub_mode),
            struct.pack(">?", status.fast_mode),
            struct.pack(">I", status.tr_period_seconds if status.tr_period_seconds is not None else 15),
            struct.pack(">I", status.rx_df_hz if status.rx_df_hz is not None else maximum),
            encode_text(call),
            encode_text(grid),
            struct.pack(">?", True),
        )
    )


def format_time(milliseconds: int) -> str:
    total_seconds = milliseconds // 1000
    time_value = timedelta(seconds=total_seconds)
    return f"{time_value.seconds // 3600:02}:{(time_value.seconds % 3600) // 60:02}:{time_value.seconds % 60:02}"


def parse_packet(data: bytes) -> Packet | None:
    reader = PacketReader(data)
    magic = reader.read_uint32()
    schema = reader.read_uint32()
    packet_type = reader.read_uint32()
    if magic != WSJTX_MAGIC:
        return None
    wsjtx_id = reader.read_text()
    if packet_type == 0:
        return Heartbeat(wsjtx_id, schema, reader.read_uint32(), reader.read_text(), reader.read_text())
    if packet_type == 1:
        dial = reader.read_uint64()
        mode = reader.read_text()
        dx_call = reader.read_text()
        reader.read_text()
        reader.read_text()
        tx_enabled = reader.read_bool()
        transmitting = reader.read_bool()
        decoding = reader.read_bool()
        # Rx DF and Tx DF were appended to the Status message. Older or
        # deliberately minimal test senders may omit them, so retain backward
        # compatibility with the original shorter packet.
        rx_df_hz = reader.read_uint32() if reader.remaining() >= 4 else None
        tx_df_hz = reader.read_uint32() if reader.remaining() >= 4 else None
        de_call = reader.read_text() if reader.remaining() >= 4 else ""
        de_grid = reader.read_text() if reader.remaining() >= 4 else ""
        dx_grid = reader.read_text() if reader.remaining() >= 4 else ""
        tx_watchdog = reader.read_bool() if reader.remaining() >= 1 else False
        sub_mode = reader.read_text() if reader.remaining() >= 4 else ""
        fast_mode = reader.read_bool() if reader.remaining() >= 1 else False
        special_operation_mode = reader.read_uint8() if reader.remaining() >= 1 else 0
        frequency_tolerance_hz = reader.read_uint32() if reader.remaining() >= 4 else None
        tr_period_seconds = reader.read_uint32() if reader.remaining() >= 4 else None
        configuration_name = reader.read_text() if reader.remaining() >= 4 else ""
        tx_message = reader.read_text() if reader.remaining() >= 4 else ""
        return Status(
            wsjtx_id,
            schema,
            dial,
            mode,
            dx_call,
            tx_enabled,
            transmitting,
            decoding,
            rx_df_hz,
            tx_df_hz,
            de_call,
            de_grid,
            dx_grid,
            tx_watchdog,
            sub_mode,
            fast_mode,
            special_operation_mode,
            frequency_tolerance_hz,
            tr_period_seconds,
            configuration_name,
            tx_message,
        )
    if packet_type == 2:
        return Decode(
            wsjtx_id, schema, reader.read_bool(), format_time(reader.read_uint32()),
            reader.read_int32(), reader.read_double(), reader.read_uint32(),
            reader.read_text(), reader.read_text(),
        )
    return None
