from __future__ import annotations

import queue
import socket
import struct
import threading

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

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="WSJTXReceiver", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join(timeout=2)
        with self._lock:
            self._wsjtx_address = None
            self._last_status = None

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

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket = sock
        sock.settimeout(0.5)
        try:
            sock.bind((self.host, self.port))
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
                    self.events.put(("warning", f"Malformed WSJT-X packet: {error}"))
        except OSError as error:
            self.events.put(("receiver_error", str(error)))
        finally:
            sock.close()
            self._socket = None
