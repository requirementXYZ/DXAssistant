from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SearchState(Enum):
    STOPPED = "Stopped"
    STARTING = "Starting"
    SEARCHING = "Searching"
    PAUSED = "Paused"
    TARGET_HOLD = "Target hold"
    OPERATOR_CONTROL = "Operator control"
    ERROR = "Error"


@dataclass
class SearchSession:
    dwell_seconds: int = 120
    state: SearchState = SearchState.STOPPED
    current_band: str | None = None
    deadline: float | None = None

    def __post_init__(self):
        if self.dwell_seconds not in {60, 90, 120, 180, 240, 300}:
            raise ValueError("Dwell time must be 60, 90, 120, 180, 240, or 300 seconds")

    def begin(self) -> None:
        self.state = SearchState.STARTING
        self.deadline = None

    def tuned(self, band: str, now: float) -> None:
        self.current_band = band
        self.deadline = now + self.dwell_seconds
        self.state = SearchState.SEARCHING

    def is_due(self, now: float) -> bool:
        return (
            self.state == SearchState.SEARCHING
            and self.deadline is not None
            and now >= self.deadline
        )

    def next_band(self, enabled_bands: list[str]) -> str:
        if not enabled_bands:
            raise ValueError("At least one band must be enabled")
        if self.current_band not in enabled_bands:
            return enabled_bands[0]
        index = enabled_bands.index(self.current_band)
        return enabled_bands[(index + 1) % len(enabled_bands)]

    def pause(self, target_found: bool = False) -> None:
        self.deadline = None
        self.state = SearchState.TARGET_HOLD if target_found else SearchState.PAUSED

    def hand_to_operator(self) -> None:
        self.deadline = None
        self.state = SearchState.OPERATOR_CONTROL

    def can_resume(self, tx_enabled: bool, transmitting: bool) -> bool:
        return (
            self.state
            in {SearchState.PAUSED, SearchState.TARGET_HOLD, SearchState.OPERATOR_CONTROL, SearchState.ERROR}
            and not tx_enabled
            and not transmitting
        )

    def stop(self) -> None:
        self.state = SearchState.STOPPED
        self.deadline = None

    def fail(self) -> None:
        self.state = SearchState.ERROR
        self.deadline = None

    def remaining(self, now: float) -> int | None:
        if self.deadline is None:
            return None
        return max(0, int(self.deadline - now + 0.999))
