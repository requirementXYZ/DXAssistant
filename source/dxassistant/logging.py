from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bands import band_for_frequency
from .protocol import Decode


class DecodeLogger:
    FIELDS = ("received_utc", "decode_time", "band", "dial_frequency_hz", "audio_frequency_hz", "snr_db", "delta_time_s", "mode", "message", "target_found", "wsjtx_id")

    def __init__(self, directory: Path):
        self.directory = directory

    def write(self, decode: Decode, dial_frequency_hz: int, target_found: bool, now=None):
        now = now or datetime.now(timezone.utc)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"decodes-{now:%Y-%m-%d}.csv"
        new_file = not path.exists()
        with path.open("a", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=self.FIELDS)
            if new_file:
                writer.writeheader()
            writer.writerow({
                "received_utc": now.isoformat(), "decode_time": decode.time,
                "band": band_for_frequency(dial_frequency_hz),
                "dial_frequency_hz": dial_frequency_hz, "audio_frequency_hz": decode.audio_frequency_hz,
                "snr_db": decode.snr, "delta_time_s": f"{decode.delta_time:.3f}",
                "mode": decode.mode, "message": decode.message,
                "target_found": target_found, "wsjtx_id": decode.wsjtx_id,
            })
        return path


class EventLogger:
    """Append-only UTC audit log with a bounded in-memory failure buffer."""

    def __init__(self, directory: Path, maximum_buffered: int = 250):
        self.directory = directory
        self.maximum_buffered = maximum_buffered
        self.pending: list[dict[str, Any]] = []
        self.last_error = ""

    def write(self, event: str, detail: str = "", **data: Any) -> Path | None:
        record = {
            "utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "detail": detail,
            **data,
        }
        records = [*self.pending, record]
        path = self.directory / f"events-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as stream:
                for item in records:
                    stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as error:
            self.pending = records[-self.maximum_buffered :]
            self.last_error = str(error)
            return None
        self.pending.clear()
        self.last_error = ""
        return path
