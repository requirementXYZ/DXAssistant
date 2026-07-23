from __future__ import annotations

import gzip
import math
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable, Iterable

from . import __version__
from .bands import band_for_frequency


PSK_REPORTER_ENDPOINT = "https://retrieve.pskreporter.info/query"
LOCATOR_PATTERN = re.compile(r"^[A-R]{2}[0-9]{2}(?:[A-X]{2})?(?:[0-9]{2})?$", re.IGNORECASE)


class PSKReporterError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReceptionReport:
    receiver_call: str
    receiver_locator: str
    frequency_hz: int
    flow_start_seconds: int
    mode: str


@dataclass(frozen=True)
class BandPriority:
    band: str
    receiver_count: int
    nearest_km: int
    latest_age_minutes: int
    score: float


def locator_to_latlon(locator: str) -> tuple[float, float]:
    """Return the centre of a 4, 6, or 8 character Maidenhead locator."""

    value = locator.strip().upper()
    if not LOCATOR_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid Maidenhead locator: {locator}")

    longitude = -180.0 + (ord(value[0]) - ord("A")) * 20.0
    latitude = -90.0 + (ord(value[1]) - ord("A")) * 10.0
    longitude += int(value[2]) * 2.0
    latitude += int(value[3])
    lon_width = 2.0
    lat_height = 1.0

    if len(value) >= 6:
        lon_width /= 24.0
        lat_height /= 24.0
        longitude += (ord(value[4]) - ord("A")) * lon_width
        latitude += (ord(value[5]) - ord("A")) * lat_height
    if len(value) == 8:
        lon_width /= 10.0
        lat_height /= 10.0
        longitude += int(value[6]) * lon_width
        latitude += int(value[7]) * lat_height

    return latitude + lat_height / 2.0, longitude + lon_width / 2.0


def distance_km(first_locator: str, second_locator: str) -> float:
    lat1, lon1 = locator_to_latlon(first_locator)
    lat2, lon2 = locator_to_latlon(second_locator)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    haversine = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return 6371.0 * 2.0 * math.atan2(math.sqrt(haversine), math.sqrt(1.0 - haversine))


def _proximity_weight(distance: float) -> float:
    if distance <= 500:
        return 4.0
    if distance <= 1000:
        return 3.0
    if distance <= 1500:
        return 2.0
    return 1.0


def _recency_weight(age_seconds: int) -> float:
    if age_seconds <= 10 * 60:
        return 2.0
    if age_seconds <= 20 * 60:
        return 1.5
    return 1.0


def rank_bands(
    reports: Iterable[ReceptionReport],
    station_locator: str,
    enabled_bands: Iterable[str],
    *,
    now_seconds: int | None = None,
    lookback_minutes: int = 30,
    maximum_distance_km: int = 2500,
) -> list[BandPriority]:
    """Rank recently reported bands without relying on exact reported frequency."""

    now = int(time.time()) if now_seconds is None else now_seconds
    enabled = set(enabled_bands)
    cutoff = now - lookback_minutes * 60
    # Repeated transmissions decoded by the same receiver must not overwhelm
    # the majority signal. Retain only its newest report on each band.
    newest_by_receiver: dict[tuple[str, str], tuple[ReceptionReport, float]] = {}
    for report in reports:
        if report.mode and report.mode.upper() != "FT8":
            continue
        if report.flow_start_seconds < cutoff or report.flow_start_seconds > now + 300:
            continue
        band = band_for_frequency(report.frequency_hz)
        if band not in enabled:
            continue
        receiver_key = report.receiver_call.strip().upper() or report.receiver_locator.strip().upper()
        if not receiver_key:
            continue
        try:
            distance = distance_km(station_locator, report.receiver_locator)
        except ValueError:
            continue
        if distance > maximum_distance_km:
            continue
        key = (band, receiver_key)
        previous = newest_by_receiver.get(key)
        if previous is None or report.flow_start_seconds > previous[0].flow_start_seconds:
            newest_by_receiver[key] = (report, distance)

    grouped: dict[str, list[tuple[ReceptionReport, float]]] = {}
    for (band, _receiver), value in newest_by_receiver.items():
        grouped.setdefault(band, []).append(value)

    priorities = []
    for band, values in grouped.items():
        nearest = min(distance for _report, distance in values)
        newest = max(report.flow_start_seconds for report, _distance in values)
        score = sum(
            _proximity_weight(distance)
            * _recency_weight(max(0, now - report.flow_start_seconds))
            for report, distance in values
        )
        priorities.append(
            BandPriority(
                band=band,
                receiver_count=len(values),
                nearest_km=round(nearest),
                latest_age_minutes=max(0, (now - newest) // 60),
                score=score,
            )
        )
    return sorted(
        priorities,
        key=lambda item: (-item.score, -item.receiver_count, item.latest_age_minutes, item.nearest_km),
    )


class PSKReporterClient:
    def __init__(
        self,
        endpoint: str = PSK_REPORTER_ENDPOINT,
        opener: Callable | None = None,
        timeout_seconds: int = 12,
    ):
        self.endpoint = endpoint
        self.opener = opener or urllib.request.urlopen
        self.timeout_seconds = timeout_seconds

    def fetch(self, target_call: str, lookback_minutes: int = 30) -> list[ReceptionReport]:
        parameters = urllib.parse.urlencode(
            {
                "senderCallsign": target_call.strip().upper(),
                "flowStartSeconds": -(lookback_minutes * 60),
                "mode": "FT8",
                "rptlimit": 500,
                "rronly": 1,
                "noactive": 1,
            }
        ).encode("ascii")
        request = urllib.request.Request(
            self.endpoint,
            data=parameters,
            method="POST",
            headers={
                "Accept": "application/xml,text/xml",
                "Accept-Encoding": "gzip",
                "User-Agent": f"DXAssistant/{__version__} (PSK Reporter band prioritisation)",
            },
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                payload = response.read()
                encoding = response.headers.get("Content-Encoding", "")
        except Exception as error:
            raise PSKReporterError(f"PSK Reporter request failed: {error}") from error
        if encoding.lower() == "gzip":
            try:
                payload = gzip.decompress(payload)
            except OSError as error:
                raise PSKReporterError("PSK Reporter returned invalid compressed data") from error
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as error:
            raise PSKReporterError("PSK Reporter returned invalid XML") from error

        reports = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "receptionReport":
                continue
            try:
                frequency_hz = int(element.attrib["frequency"])
                flow_start_seconds = int(element.attrib["flowStartSeconds"])
            except (KeyError, ValueError):
                continue
            reports.append(
                ReceptionReport(
                    receiver_call=element.attrib.get("receiverCallsign", ""),
                    receiver_locator=element.attrib.get("receiverLocator", ""),
                    frequency_hz=frequency_hz,
                    flow_start_seconds=flow_start_seconds,
                    mode=element.attrib.get("mode", ""),
                )
            )
        return reports
