import struct
import unittest

from dxassistant.engine import DXEngine, transmitting_call
from dxassistant.protocol import (
    Decode,
    Heartbeat,
    PacketReader,
    Status,
    WSJTX_CONFIGURE,
    WSJTX_MAGIC,
    build_prepare_dx,
    parse_packet,
)


def text(value):
    encoded = value.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


def header(packet_type):
    return struct.pack(">III", WSJTX_MAGIC, 3, packet_type) + text("WSJT-X")


class CoreTests(unittest.TestCase):
    def test_heartbeat(self):
        packet = parse_packet(header(0) + struct.pack(">I", 3) + text("2.7.0") + text("r1"))
        self.assertIsInstance(packet, Heartbeat)

    def test_status(self):
        data = (
            header(1)
            + struct.pack(">Q", 14_074_000)
            + text("FT8")
            + text("")
            + text("")
            + text("FT8")
            + struct.pack(">???II", False, False, True, 1200, 1800)
        )
        packet = parse_packet(data)
        self.assertIsInstance(packet, Status)
        self.assertEqual(packet.dial_frequency_hz, 14_074_000)
        self.assertFalse(packet.transmitting)
        self.assertEqual(packet.rx_df_hz, 1200)
        self.assertEqual(packet.tx_df_hz, 1800)

    def test_short_status_without_df_fields_remains_compatible(self):
        data = header(1) + struct.pack(">Q", 14_074_000) + text("FT8") + text("") + text("") + text("FT8") + struct.pack(">???", False, False, True)
        packet = parse_packet(data)
        self.assertIsInstance(packet, Status)
        self.assertIsNone(packet.rx_df_hz)
        self.assertIsNone(packet.tx_df_hz)

    def test_prepare_dx_builds_configure_only_and_mirrors_status(self):
        status = Status(
            "WSJT-X", 3, 14_074_000, "FT8", "", False, False, False,
            1200, 1800, "G8AJM", "JO03", "", False, "", False, 0,
            50, 15, "Default", "",
        )
        reader = PacketReader(build_prepare_dx(status, "cr7brv", "im58"))
        self.assertEqual(reader.read_uint32(), WSJTX_MAGIC)
        self.assertEqual(reader.read_uint32(), 3)
        self.assertEqual(reader.read_uint32(), WSJTX_CONFIGURE)
        self.assertEqual(reader.read_text(), "WSJT-X")
        self.assertEqual(reader.read_text(), "FT8")
        self.assertEqual(reader.read_uint32(), 50)
        self.assertEqual(reader.read_text(), "")
        self.assertFalse(reader.read_bool())
        self.assertEqual(reader.read_uint32(), 15)
        self.assertEqual(reader.read_uint32(), 1200)
        self.assertEqual(reader.read_text(), "CR7BRV")
        self.assertEqual(reader.read_text(), "IM58")
        self.assertTrue(reader.read_bool())
        self.assertEqual(reader.remaining(), 0)

    def test_exact_target_decode(self):
        packet = Decode("WSJT-X", 3, True, "12:00:00", -10, 0.1, 1200, "FT8", "CQ T22TT RI49")
        result = DXEngine("t22tt").handle(packet)
        self.assertTrue(result.target_found)
        self.assertEqual(result.transmitting_grid, "RI49")

    def test_engine_retains_wsjt_x_transmit_handover_state(self):
        engine = DXEngine("T22TT")
        engine.handle(Status("WSJT-X", 3, 14_074_000, "FT8", "T22TT", True, False, False))
        self.assertTrue(engine.state.tx_enabled)
        self.assertFalse(engine.state.transmitting)
        self.assertEqual(engine.state.dx_call, "T22TT")

    def test_partial_target_is_not_match(self):
        packet = Decode("WSJT-X", 3, True, "12:00:00", -10, 0.1, 1200, "FT8", "CQ T22TT/P RI49")
        self.assertFalse(DXEngine("T22TT").handle(packet).target_found)

    def test_target_being_called_is_not_reported_as_heard(self):
        packet = Decode("WSJT-X", 3, True, "12:00:00", 4, 0.1, 1405, "FT8", "T22TT OM3KFO 73")
        result = DXEngine("T22TT").handle(packet)
        self.assertEqual(result.transmitting_call, "OM3KFO")
        self.assertFalse(result.target_found)

    def test_target_as_directed_message_sender_is_found(self):
        packet = Decode("WSJT-X", 3, True, "12:00:00", -8, 0.1, 1405, "FT8", "OM3KFO T22TT -10")
        result = DXEngine("T22TT").handle(packet)
        self.assertEqual(result.transmitting_call, "T22TT")
        self.assertTrue(result.target_found)

    def test_cq_modifier_identifies_sender(self):
        self.assertEqual(transmitting_call("CQ DX T22TT RI49"), "T22TT")


if __name__ == "__main__":
    unittest.main()
