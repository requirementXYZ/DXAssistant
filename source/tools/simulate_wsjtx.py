"""Send a short sequence of synthetic WSJT-X packets to localhost."""

import socket
import struct
import time


MAGIC = 0xADBCCBDA
SCHEMA = 3
DESTINATION = ("127.0.0.1", 2237)


def text(value):
    encoded = value.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


def header(packet_type):
    return struct.pack(">III", MAGIC, SCHEMA, packet_type) + text("WSJT-X-SIM")


def heartbeat():
    return header(0) + struct.pack(">I", SCHEMA) + text("2.7.0-simulator") + text("test")


def status():
    return (
        header(1) + struct.pack(">Q", 14_074_000) + text("FT8") + text("")
        + text("") + text("FT8")
        + struct.pack(">???II", False, False, True, 1250, 1800)
        + text("G8AJM") + text("JO03") + text("")
        + struct.pack(">??BII", False, False, 0, 50, 15)
        + text("Default") + text("")
    )


def decode(message, snr=-12, audio_frequency=1250):
    milliseconds = 12 * 3600 * 1000 + 34 * 60 * 1000 + 56 * 1000
    return (
        header(2) + struct.pack(">?Ii", True, milliseconds, snr)
        + struct.pack(">dI", 0.2, audio_frequency) + text("FT8") + text(message)
    )


def main():
    packets = (
        heartbeat(), status(), decode("CQ G8AJM IO91", -8, 950),
        decode("T22TT OM3KFO 73", 4, 1405),
        decode("CQ T22TT RI49", -16, 1420), heartbeat(),
    )
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for packet in packets:
            sock.sendto(packet, DESTINATION)
            time.sleep(0.7)
        print("Synthetic heartbeat, status, ordinary decode, and target decode sent.")
        print("Waiting up to 12 seconds for DX Assistant's Configure-only request.")
        sock.settimeout(12)
        try:
            response, _ = sock.recvfrom(4096)
        except TimeoutError:
            print("No Configure request received; the receive-path test is still complete.")
        else:
            packet_type = struct.unpack_from(">I", response, 8)[0]
            if packet_type == 15:
                print("Configure-only DX preparation request received successfully.")
            else:
                print(f"Unexpected outbound packet type received: {packet_type}")


if __name__ == "__main__":
    main()
