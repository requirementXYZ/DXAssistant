import json
import unittest
import urllib.parse

from dxassistant.pushover import PushoverClient, PushoverError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class PushoverTests(unittest.TestCase):
    def test_message_uses_https_post_and_normal_priority(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse({"status": 1, "request": "request-id"})

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


if __name__ == "__main__":
    unittest.main()
