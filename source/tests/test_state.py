import unittest

from dxassistant.state import AppState, StateMachine


class StateMachineTests(unittest.TestCase):
    def test_normal_monitoring_and_alarm_path(self):
        machine = StateMachine()
        machine.transition(AppState.STARTING, "start")
        machine.transition(AppState.MONITORING, "listener ready")
        machine.transition(AppState.TARGET_DECODED, "target")
        machine.transition(AppState.MONITORING, "acknowledged")
        machine.transition(AppState.STOPPED, "stop")
        self.assertEqual(machine.current, AppState.STOPPED)

    def test_rejects_unsafe_skip(self):
        with self.assertRaises(ValueError):
            StateMachine().transition(AppState.TARGET_DECODED, "invalid")

    def test_degraded_state_recovers(self):
        machine = StateMachine()
        machine.transition(AppState.STARTING, "start")
        machine.transition(AppState.MONITORING, "ready")
        machine.transition(AppState.DEGRADED, "timeout")
        machine.transition(AppState.MONITORING, "recovered")
        self.assertEqual(machine.current, AppState.MONITORING)


if __name__ == "__main__":
    unittest.main()

