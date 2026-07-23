import io
import json
import unittest
import urllib.error
import urllib.parse

from dxassistant import __version__
from dxassistant.pushover import PushoverClient, PushoverError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.read_size = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, maximum_bytes=-1):
        self.read_size = maximum_bytes
        return json.dumps(self.payload).encode("utf-8")


class PushoverTests(unittest.TestCase):
    def test_message_uses_https_post_and_normal_priority(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            captured["response"] = FakeResponse({"status": 1, "request": "request-id"})
            return captured["response"]

        client = PushoverClient(opener=opener)
        request_id = client.push(
            "U" * 30,
            "A" * 30,
            "DX Assistant: T22TT heard",
            "Target T22TT decoded on 20m.",
        )
        request = captured["request"]
        parameters = urllib.parse.parse_qs(request.data.decode("ascii"))
        self.assertEqual(request.full_url, "https://api.pushover.net/1/messages.json")
        self.assertEqual(request.method, "POST")
        self.assertEqual(parameters["priority"], ["0"])
        self.assertEqual(parameters["user"], ["U" * 30])
        self.assertEqual(parameters["token"], ["A" * 30])
        self.assertEqual(request_id, "request-id")
        self.assertIn(f"DXAssistant/{__version__}", request.headers["User-agent"])
        self.assertEqual(captured["response"].read_size, 65536)

    def test_rejected_message_raises_sanitised_error(self):
        client = PushoverClient(
            opener=lambda request, timeout: FakeResponse(
                {"status": 0, "errors": ["user identifier is invalid"]}
            )
        )
        with self.assertRaisesRegex(
            PushoverError, "user identifier is invalid"
        ) as raised:
            client.push("U" * 30, "A" * 30, "title", "message")
        self.assertNotIn("U" * 30, str(raised.exception))
        self.assertNotIn("A" * 30, str(raised.exception))

    def test_http_error_json_is_sanitised(self):
        body = io.BytesIO(json.dumps({"errors": ["application token is invalid"]}).encode())

        def opener(request, timeout):
            raise urllib.error.HTTPError(
                "https://api.pushover.net", 400, "Bad Request", {}, body
            )

        with self.assertRaisesRegex(PushoverError, "application token is invalid"):
            PushoverClient(opener=opener).push(
                "U" * 30, "A" * 30, "title", "message"
            )

    def test_timeout_is_reported_as_pushover_error(self):
        def opener(request, timeout):
            raise TimeoutError("timed out")

        with self.assertRaisesRegex(PushoverError, "timed out"):
            PushoverClient(opener=opener).push(
                "U" * 30, "A" * 30, "title", "message"
            )


if __name__ == "__main__":
    unittest.main()
