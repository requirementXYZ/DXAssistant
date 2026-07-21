from __future__ import annotations


# Broad amateur-band edges are used rather than only the standard FT8 calling
# frequencies so non-standard DXpedition frequencies still receive a band.
BAND_RANGES_HZ = (
    (1_800_000, 2_000_000, "160m"),
    (3_500_000, 4_000_000, "80m"),
    (5_000_000, 5_500_000, "60m"),
    (7_000_000, 7_300_000, "40m"),
    (10_100_000, 10_150_000, "30m"),
    (14_000_000, 14_350_000, "20m"),
    (18_068_000, 18_168_000, "17m"),
    (21_000_000, 21_450_000, "15m"),
    (24_890_000, 24_990_000, "12m"),
    (28_000_000, 29_700_000, "10m"),
    (50_000_000, 54_000_000, "6m"),
)

STANDARD_FT8_FREQUENCIES_MHZ = {
    "40m": 7.074,
    "30m": 10.136,
    "20m": 14.074,
    "17m": 18.100,
    "15m": 21.074,
    "12m": 24.915,
    "10m": 28.074,
}


def band_for_frequency(frequency_hz: int) -> str:
    for lower, upper, name in BAND_RANGES_HZ:
        if lower <= frequency_hz <= upper:
            return name
    return "-"


def band_limits_mhz(name: str) -> tuple[float, float] | None:
    for lower, upper, band_name in BAND_RANGES_HZ:
        if band_name == name:
            return lower / 1_000_000, upper / 1_000_000
    return None


def is_standard_ft8_frequency(name: str, frequency_mhz: float) -> bool:
    standard = STANDARD_FT8_FREQUENCIES_MHZ.get(name)
    return standard is not None and abs(frequency_mhz - standard) < 0.0005
