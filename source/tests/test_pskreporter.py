import gzip
import time
import unittest
import urllib.parse

from dxassistant.pskreporter import (
    PSKReporterClient,
    ReceptionReport,
    distance_km,
    locator_to_latlon,
    rank_bands,
)


class FakeResponse:
    def __init__(self, payload, encoding=""):
        self.payload = payload
        self.headers = {"Content-Encoding": encoding}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class PSKReporterTests(unittest.TestCase):
    def test_maidenhead_locator_and_distance(self):
        latitude, longitude = locator_to_latlon("JO03")
        self.assertAlmostEqual(latitude, 53.5)
        self.assertAlmostEqual(longitude, 1.0)
        self.assertLess(distance_km("JO03", "JO02"), 150)

    def test_band_ranking_uses_unique_nearby_receivers_and_ignores_exact_offset(self):
        now = 1_700_000_000
        reports = [
            ReceptionReport("G1AAA", "JO02", 14_076_400, now - 60, "FT8"),
            ReceptionReport("G1AAA", "JO02", 14_074_000, now - 30, "FT8"),
            ReceptionReport("G2BBB", "IO93", 14_075_800, now - 120, "FT8"),
            ReceptionReport("G3CCC", "JO01", 21_076_000, now - 90, "FT8"),
            ReceptionReport("W1FAR", "FN42", 7_074_000, now - 30, "FT8"),
            ReceptionReport("G4OLD", "JO03", 18_100_000, now - 3600, "FT8"),
        ]
        priorities = rank_bands(
            reports,
            "JO03",
            ["40m", "20m", "17m", "15m"],
            now_seconds=now,
            lookback_minutes=30,
        )
        self.assertEqual([item.band for item in priorities], ["20m", "15m"])
        self.assertEqual(priorities[0].receiver_count, 2)

    def test_client_posts_supported_query_and_parses_gzip_xml(self):
        now = int(time.time())
        xml = (
            '<receptionReports><receptionReport receiverCallsign="G1AAA" '
            'receiverLocator="JO02" senderCallsign="D2UY" frequency="14076000" '
            f'flowStartSeconds="{now}" mode="FT8" /></receptionReports>'
        ).encode("utf-8")
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(gzip.compress(xml), "gzip")

        reports = PSKReporterClient(opener=opener).fetch("d2uy", 30)
        parameters = urllib.parse.parse_qs(captured["request"].data.decode("ascii"))
        self.assertEqual(parameters["senderCallsign"], ["D2UY"])
        self.assertEqual(parameters["flowStartSeconds"], ["-1800"])
        self.assertEqual(parameters["mode"], ["FT8"])
        self.assertEqual(reports[0].receiver_locator, "JO02")
        self.assertEqual(reports[0].frequency_hz, 14_076_000)


if __name__ == "__main__":
    unittest.main()
