from __future__ import annotations

import re
from dataclasses import dataclass

_YEAR_PATTERN = re.compile(r"\d{4}")


@dataclass(frozen=True)
class Season:
    competition: str
    label: str

    @property
    def start_year(self) -> int | None:
        match = _YEAR_PATTERN.search(self.label)
        return int(match.group()) if match else None
