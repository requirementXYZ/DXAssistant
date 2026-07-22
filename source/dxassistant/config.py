from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .bands import STANDARD_FT8_FREQUENCIES_MHZ


PSK_REPORTER_DISTANCES_KM = (500, 1000, 1500, 2500, 5000)


@dataclass(frozen=True)
class BandConfig:
    enabled: bool
    frequency_mhz: float
    power_watts: int | None = None


@dataclass(frozen=True)
class AppConfig:
    target_call: str
    udp_host: str
    udp_port: int
    alarm_enabled: bool
    heartbeat_timeout_seconds: int
    log_directory: Path
    bands: dict[str, BandConfig]
    station_locator: str = "JO03"
    psk_reporter_enabled: bool = True
    psk_reporter_lookback_minutes: int = 30
    psk_reporter_distance_km: int = 2500
    source_path: Path | None = None


def _require(mapping: dict[str, Any], name: str, expected: type) -> Any:
    value = mapping.get(name)
    if not isinstance(value, expected):
        raise ValueError(f"Configuration item '{name}' must be {expected.__name__}")
    return value


def load_config(path: Path) -> AppConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Configuration file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error

    target = _require(raw, "target_call", str).strip().upper()
    if not target or any(character.isspace() for character in target):
        raise ValueError("target_call must be one callsign without spaces")
    port = _require(raw, "udp_port", int)
    if not 1 <= port <= 65535:
        raise ValueError("udp_port must be between 1 and 65535")
    timeout = int(raw.get("heartbeat_timeout_seconds", 15))
    if not 5 <= timeout <= 300:
        raise ValueError("heartbeat_timeout_seconds must be between 5 and 300")
    station_locator = str(raw.get("station_locator", "JO03")).strip().upper()
    if not re.fullmatch(r"[A-R]{2}[0-9]{2}(?:[A-X]{2})?(?:[0-9]{2})?", station_locator):
        raise ValueError("station_locator must be a 4, 6, or 8 character Maidenhead locator")
    psk_lookback = int(raw.get("psk_reporter_lookback_minutes", 30))
    if not 10 <= psk_lookback <= 120:
        raise ValueError("psk_reporter_lookback_minutes must be between 10 and 120")
    psk_distance = int(raw.get("psk_reporter_distance_km", 2500))
    if psk_distance not in PSK_REPORTER_DISTANCES_KM:
        raise ValueError(
            "psk_reporter_distance_km must be 500, 1000, 1500, 2500, or 5000"
        )

    configured_bands = _require(raw, "bands", dict)
    band_names = list(STANDARD_FT8_FREQUENCIES_MHZ)
    band_names.extend(name for name in configured_bands if name not in band_names)
    bands: dict[str, BandConfig] = {}
    for name in band_names:
        settings = configured_bands.get(name)
        if settings is None:
            bands[name] = BandConfig(
                False, STANDARD_FT8_FREQUENCIES_MHZ[name], None
            )
            continue
        if not isinstance(settings, dict):
            raise ValueError(f"Band '{name}' must contain settings")
        frequency = settings.get("frequency_mhz")
        if not isinstance(frequency, (int, float)) or frequency <= 0:
            raise ValueError(f"Band '{name}' has an invalid frequency_mhz")
        power = settings.get("power_watts")
        if power is not None and (
            isinstance(power, bool) or not isinstance(power, int) or not 5 <= power <= 100
        ):
            raise ValueError(f"Band '{name}' power_watts must be blank or between 5 and 100")
        bands[name] = BandConfig(
            bool(settings.get("enabled", False)), float(frequency), power
        )

    log_directory = Path(_require(raw, "log_directory", str))
    if not log_directory.is_absolute():
        log_directory = path.parent / log_directory
    return AppConfig(
        target_call=target,
        udp_host=_require(raw, "udp_host", str),
        udp_port=port,
        alarm_enabled=bool(raw.get("alarm_enabled", True)),
        heartbeat_timeout_seconds=timeout,
        log_directory=log_directory,
        bands=bands,
        station_locator=station_locator,
        psk_reporter_enabled=bool(raw.get("psk_reporter_enabled", True)),
        psk_reporter_lookback_minutes=psk_lookback,
        psk_reporter_distance_km=psk_distance,
        source_path=path,
    )


def _band_settings_for_update(raw: dict[str, Any], band: str) -> dict[str, Any]:
    bands = raw.get("bands")
    if not isinstance(bands, dict):
        raise ValueError("Configuration item 'bands' must be dict")
    if band not in bands:
        standard = STANDARD_FT8_FREQUENCIES_MHZ.get(band)
        if standard is None:
            raise ValueError(f"Unknown band: {band}")
        bands[band] = {
            "enabled": False,
            "frequency_mhz": standard,
            "power_watts": None,
        }
    settings = bands[band]
    if not isinstance(settings, dict):
        raise ValueError(f"Band '{band}' must contain settings")
    return settings


def save_band_power(config: AppConfig, band: str, power_watts: int) -> None:
    """Persist an operator safety-profile value; this never controls a radio."""

    if not 5 <= power_watts <= 100:
        raise ValueError("Maximum-drive reference must be between 5 and 100 watts")
    if config.source_path is None:
        raise ValueError("Configuration location is unavailable")
    path = config.source_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    _band_settings_for_update(raw, band)["power_watts"] = power_watts
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def save_target_call(config: AppConfig, target_call: str) -> None:
    """Persist the selected target so the next launch resumes with it."""

    target = target_call.strip().upper()
    compact = target.replace("/", "")
    valid = (
        bool(re.fullmatch(r"[A-Z0-9/]{3,15}", target))
        and any(character.isalpha() for character in compact)
        and any(character.isdigit() for character in compact)
    )
    if not valid:
        raise ValueError("Enter one callsign, for example T22TT or G8AJM")
    if config.source_path is None:
        raise ValueError("Configuration location is unavailable")
    path = config.source_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["target_call"] = target
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def save_band_enabled(config: AppConfig, band: str, enabled: bool) -> None:
    """Persist the antenna-compatible enabled state for one band."""

    if config.source_path is None:
        raise ValueError("Configuration location is unavailable")
    path = config.source_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    _band_settings_for_update(raw, band)["enabled"] = bool(enabled)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def save_band_frequency(config: AppConfig, band: str, frequency_mhz: float) -> None:
    """Persist an already validated band frequency rounded to one kHz."""

    if config.source_path is None:
        raise ValueError("Configuration location is unavailable")
    path = config.source_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    _band_settings_for_update(raw, band)["frequency_mhz"] = round(
        float(frequency_mhz), 3
    )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def save_band_frequencies(config: AppConfig, frequencies_mhz: dict[str, float]) -> None:
    """Persist a validated frequency set atomically without changing band enablement."""

    if config.source_path is None:
        raise ValueError("Configuration location is unavailable")
    path = config.source_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    for band, frequency_mhz in frequencies_mhz.items():
        _band_settings_for_update(raw, band)["frequency_mhz"] = round(
            float(frequency_mhz), 3
        )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def save_psk_search_area(config: AppConfig, locator: str, distance_km: int) -> None:
    locator = locator.strip().upper()
    if not re.fullmatch(r"[A-R]{2}[0-9]{2}(?:[A-X]{2})?(?:[0-9]{2})?", locator):
        raise ValueError("Enter a 4, 6, or 8 character Maidenhead locator")
    if distance_km not in PSK_REPORTER_DISTANCES_KM:
        raise ValueError("Select a supported PSK Reporter distance")
    if config.source_path is None:
        raise ValueError("Configuration location is unavailable")
    path = config.source_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["station_locator"] = locator
    raw["psk_reporter_distance_km"] = distance_km
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
