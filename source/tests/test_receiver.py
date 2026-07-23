import queue
import socket
import struct
import time
import unittest

from dxassistant.protocol import Heartbeat, WSJTX_CONFIGURE, WSJTX_MAGIC, parse_packet
from dxassistant.receiver import UDPReceiver


def text(value):
    encoded = value.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


class ReceiverTests(unittest.TestCase):
    def test_non_wsjtx_and_truncated_datagrams_are_ignored(self):
        self.assertIsNone(parse_packet(b""))
        self.assertIsNone(parse_packet(b"short"))
        self.assertIsNone(parse_packet(struct.pack(">III", 123, 3, 0)))
        truncated_text = (
            struct.pack(">III", WSJTX_MAGIC, 3, 0)
            + struct.pack(">I", 500)
        )
        with self.assertRaises(ValueError):
            parse_packet(truncated_text)

    def test_bind_failure_surfaces_receiver_error(self):
        occupied = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        occupied.bind(("127.0.0.1", 0))
        events = queue.Queue()
        receiver = UDPReceiver("127.0.0.1", occupied.getsockname()[1], events)
        receiver.start()
        kind, detail = events.get(timeout=2)
        occupied.close()
        self.assertEqual(kind, "receiver_error")
        self.assertTrue(detail)

    def test_malformed_packet_warning_is_rate_limited(self):
        events = queue.Queue()
        receiver = UDPReceiver("127.0.0.1", 2237, events)
        with unittest.mock.patch(
            "dxassistant.receiver.time.monotonic", side_effect=[100.0, 101.0, 161.0]
        ):
            receiver._report_malformed(ValueError("first"))
            receiver._report_malformed(ValueError("second"))
            receiver._report_malformed(ValueError("third"))
        self.assertEqual(events.qsize(), 2)
        self.assertIn("first", events.get_nowait()[1])
        self.assertIn("third", events.get_nowait()[1])

    def test_receiver_can_stop_and_restart_quickly(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        events = queue.Queue()
        receiver = UDPReceiver("127.0.0.1", port, events)
        receiver.start()
        self.assertEqual(events.get(timeout=2)[0], "receiver_started")
        receiver.stop()
        receiver.start()
        self.assertEqual(events.get(timeout=2)[0], "receiver_started")
        receiver.stop()

    def test_receives_local_heartbeat(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        events = queue.Queue()
        receiver = UDPReceiver("127.0.0.1", port, events)
        receiver.start()
        kind, _ = events.get(timeout=2)
        self.assertEqual(kind, "receiver_started")
        packet = struct.pack(">III", WSJTX_MAGIC, 3, 0) + text("TEST") + struct.pack(">I", 3) + text("2.7") + text("r1")
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender.sendto(packet, ("127.0.0.1", port))
        sender.close()
        kind, payload = events.get(timeout=2)
        receiver.stop()
        self.assertEqual(kind, "packet")
        self.assertIsInstance(payload, Heartbeat)

    def test_prepare_dx_returns_configure_to_live_wsjtx_endpoint(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        events = queue.Queue()
        receiver = UDPReceiver("127.0.0.1", port, events)
        receiver.start()
        self.assertEqual(events.get(timeout=2)[0], "receiver_started")
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender.bind(("127.0.0.1", 0))
        sender.settimeout(2)
        status = (
            struct.pack(">III", WSJTX_MAGIC, 3, 1)
            + text("TEST")
            + struct.pack(">Q", 14_074_000)
            + text("FT8") + text("") + text("") + text("FT8")
            + struct.pack(">???II", False, False, False, 1200, 1800)
        )
        sender.sendto(status, ("127.0.0.1", port))
        self.assertEqual(events.get(timeout=2)[0], "packet")
        receiver.prepare_dx("CR7BRV", "IM58")
        response, _address = sender.recvfrom(65535)
        receiver.stop()
        sender.close()
        _magic, _schema, packet_type = struct.unpack(">III", response[:12])
        self.assertEqual(packet_type, WSJTX_CONFIGURE)


if __name__ == "__main__":
    unittest.main()
