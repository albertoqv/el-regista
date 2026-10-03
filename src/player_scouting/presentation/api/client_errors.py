from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

# Distinct errors kept; the oldest leave first. In memory: it is a since-the-last-
# deploy view, like the API metrics, and costs no database.
MAX_ERRORS = 100
MAX_MESSAGE = 300


@dataclass
class ClientError:
    message: str
    path: str
    count: int
    last_seen: str


class ClientErrorLog:
    """JavaScript errors seen in visitors' browsers, grouped by message and page."""

    def __init__(self) -> None:
        self._errors: OrderedDict[tuple[str, str], ClientError] = OrderedDict()

    def record(self, message: str, path: str) -> None:
        message, path = message.strip()[:MAX_MESSAGE], path.split("?")[0][:200] or "/"
        if not message:
            return
        now = datetime.now(UTC).isoformat(timespec="seconds")
        key = (message, path)
        if key in self._errors:
            error = self._errors.pop(key)
            error.count += 1
            error.last_seen = now
        else:
            error = ClientError(message, path, 1, now)
        self._errors[key] = error
        while len(self._errors) > MAX_ERRORS:
            self._errors.popitem(last=False)

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(error) for error in reversed(self._errors.values())]
