import unittest

from dxassistant.hopping import SearchSession, SearchState


class HoppingTests(unittest.TestCase):
    def test_default_dwell_and_round_robin(self):
        search = SearchSession()
        search.begin()
        search.tuned("20m", 100.0)
        self.assertEqual(search.state, SearchState.SEARCHING)
        self.assertFalse(search.is_due(219.9))
        self.assertTrue(search.is_due(220.0))
        self.assertEqual(search.next_band(["40m", "30m", "20m", "17m"]), "17m")

    def test_target_decode_requires_explicit_resume(self):
        search = SearchSession(120)
        search.begin()
        search.tuned("20m", 0.0)
        search.pause(target_found=True)
        self.assertEqual(search.state, SearchState.TARGET_HOLD)
        self.assertTrue(search.can_resume(False, False))
        self.assertFalse(search.can_resume(True, False))
        self.assertIsNone(search.deadline)

    def test_enable_tx_hands_control_to_operator(self):
        search = SearchSession(120)
        search.begin()
        search.tuned("17m", 0.0)
        search.hand_to_operator()
        self.assertEqual(search.state, SearchState.OPERATOR_CONTROL)
        self.assertFalse(search.can_resume(True, False))
        self.assertTrue(search.can_resume(False, False))

    def test_dwell_must_be_supported_gui_value(self):
        with self.assertRaises(ValueError):
            SearchSession(15)


if __name__ == "__main__":
    unittest.main()
