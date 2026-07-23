from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable


PUSHOVER_MESSAGES_ENDPOINT = "https://api.pushover.net/1/messages.json"


class PushoverError(RuntimeError):
    pass


class PushoverClient:
    """Minimal HTTPS client for notification-only Pushover messages."""

    def __init__(
        self,
        endpoint: str = PUSHOVER_MESSAGES_ENDPOINT,
        opener: Callable | None = None,
        timeout_seconds: int = 12,
    ):
        self.endpoint = endpoint
        self.opener = opener or urllib.request.urlopen
        self.timeout_seconds = timeout_seconds

    def push(
        self,
        user_key: str,
        api_token: str,
        title: str,
        message: str,
    ) -> str:
        payload = urllib.parse.urlencode(
            {
                "token": api_token,
                "user": user_key,
                "title": title,
                "message": message,
                "priority": 0,
            }
        ).encode("ascii")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "DXAssistant/0.14",
            },
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8"))
                message_text = "; ".join(detail.get("errors", []))
            except (json.JSONDecodeError, UnicodeDecodeError):
                message_text = ""
            raise PushoverError(
                f"Pushover rejected the notification"
                f"{': ' + message_text if message_text else ''}"
            ) from error
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise PushoverError(f"Pushover notification failed: {error}") from error
        if result.get("status") != 1:
            errors = "; ".join(result.get("errors", []))
            raise PushoverError(
                f"Pushover rejected the notification"
                f"{': ' + errors if errors else ''}"
            )
        return str(result.get("request", ""))
