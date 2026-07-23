from __future__ import annotations

import queue
import socket
import struct
import threading
import time

from .protocol import Status, build_prepare_dx, parse_packet


class WSJTXRequestError(RuntimeError):
    pass


class UDPReceiver:
    """WSJT-X listener with one Configure-only Prepare DX response path."""

    def __init__(self, host: str, port: int, events: queue.Queue):
        self.host = host
        self.port = port
        self.events = events
        self._stop = threading.Event()
        self._thread = None
        self._socket = None
        self._lock = threading.Lock()
        self._wsjtx_address = None
        self._last_status = None
        self._last_malformed_warning = 0.0

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        try:
            sock.bind((self.host, self.port))
        except OSError as error:
            sock.close()
            self.events.put(("receiver_error", str(error)))
            return
        with self._lock:
            self._socket = sock
        self._thread = threading.Thread(
            target=self._run,
            args=(sock,),
            name="WSJTXReceiver",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        with self._lock:
            sock = self._socket
            thread = self._thread
        if sock:
            sock.close()
        if thread:
            thread.join(timeout=2)
            if thread.is_alive():
                self.events.put(("receiver_error", "WSJT-X listener did not stop within 2 seconds"))
        with self._lock:
            self._wsjtx_address = None
            self._last_status = None
            if self._thread is thread and (thread is None or not thread.is_alive()):
                self._thread = None

    def prepare_dx(self, dx_call: str, dx_grid: str = "") -> None:
        """Populate WSJT-X DX fields/messages without any transmit command."""

        with self._lock:
            sock = self._socket
            address = self._wsjtx_address
            status = self._last_status
        if sock is None or address is None or status is None:
            raise WSJTXRequestError("No WSJT-X status endpoint is available")
        try:
            payload = build_prepare_dx(status, dx_call, dx_grid)
            sock.sendto(payload, address)
        except (OSError, ValueError) as error:
            raise WSJTXRequestError(f"Could not prepare DX in WSJT-X: {error}") from error

    def _run(self, sock):
        try:
            self.events.put(("receiver_started", None))
            while not self._stop.is_set():
                try:
                    data, address = sock.recvfrom(65535)
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop.is_set():
                        break
                    raise
                try:
                    packet = parse_packet(data)
                    if packet is not None:
                        with self._lock:
                            self._wsjtx_address = address
                            if isinstance(packet, Status):
                                self._last_status = packet
                        self.events.put(("packet", packet))
                except (ValueError, struct.error) as error:
                    self._report_malformed(error)
        except OSError as error:
            self.events.put(("receiver_error", str(error)))
        finally:
            sock.close()
            with self._lock:
                if self._socket is sock:
                    self._socket = None

    def _report_malformed(self, error: Exception) -> None:
        """Rate-limit operator-visible warnings from unrelated local UDP traffic."""

        now = time.monotonic()
        if now - self._last_malformed_warning < 60:
            return
        self._last_malformed_warning = now
        self.events.put(("warning", f"Malformed WSJT-X packet ignored: {error}"))
