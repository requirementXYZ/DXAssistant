import unittest

from dxassistant.bands import (
    STANDARD_FT8_FREQUENCIES_MHZ,
    band_for_frequency,
    band_limits_mhz,
)


class BandTests(unittest.TestCase):
    def test_supported_hf_bands(self):
        examples = {
            1_840_000: "160m",
            3_573_000: "80m",
            7_074_000: "40m",
            10_136_000: "30m",
            14_074_000: "20m",
            18_100_000: "17m",
            21_074_000: "15m",
            24_915_000: "12m",
            28_074_000: "10m",
            50_313_000: "6m",
        }
        for frequency, expected in examples.items():
            with self.subTest(frequency=frequency):
                self.assertEqual(band_for_frequency(frequency), expected)

    def test_standard_ft8_plan_includes_requested_low_and_vhf_bands(self):
        self.assertEqual(STANDARD_FT8_FREQUENCIES_MHZ["160m"], 1.840)
        self.assertEqual(STANDARD_FT8_FREQUENCIES_MHZ["80m"], 3.573)
        self.assertEqual(STANDARD_FT8_FREQUENCIES_MHZ["6m"], 50.313)

    def test_nonstandard_frequency_within_band_is_labelled(self):
        self.assertEqual(band_for_frequency(14_095_000), "20m")

    def test_unknown_frequency_is_unlabelled(self):
        self.assertEqual(band_for_frequency(0), "-")

    def test_band_limits_are_available_for_session_validation(self):
        self.assertEqual(band_limits_mhz("20m"), (14.0, 14.35))
        self.assertIsNone(band_limits_mhz("unknown"))


if __name__ == "__main__":
    unittest.main()
