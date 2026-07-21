from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppState(Enum):
    STOPPED = "Stopped"
    STARTING = "Starting"
    MONITORING = "Monitoring"
    TARGET_DECODED = "Target decoded"
    DEGRADED = "Degraded"
    ERROR = "Error"


ALLOWED_TRANSITIONS = {
    AppState.STOPPED: {AppState.STARTING},
    AppState.STARTING: {AppState.MONITORING, AppState.ERROR, AppState.STOPPED},
    AppState.MONITORING: {AppState.TARGET_DECODED, AppState.DEGRADED, AppState.ERROR, AppState.STOPPED},
    AppState.TARGET_DECODED: {AppState.MONITORING, AppState.DEGRADED, AppState.ERROR, AppState.STOPPED},
    AppState.DEGRADED: {AppState.MONITORING, AppState.TARGET_DECODED, AppState.ERROR, AppState.STOPPED},
    AppState.ERROR: {AppState.STARTING, AppState.STOPPED},
}


@dataclass(frozen=True)
class StateChange:
    previous: AppState
    current: AppState
    reason: str


class StateMachine:
    def __init__(self):
        self.current = AppState.STOPPED

    def transition(self, new_state: AppState, reason: str) -> StateChange:
        if new_state == self.current:
            return StateChange(self.current, self.current, reason)
        if new_state not in ALLOWED_TRANSITIONS[self.current]:
            raise ValueError(f"Invalid transition: {self.current.value} -> {new_state.value}")
        previous = self.current
        self.current = new_state
        return StateChange(previous, new_state, reason)

