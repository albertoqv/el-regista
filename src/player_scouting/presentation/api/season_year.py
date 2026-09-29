from __future__ import annotations

import re

YEAR_PATTERN = re.compile(r"\d{4}")


def extract_season_year(label: str) -> int | None:
    match = YEAR_PATTERN.search(label)
    if match is None:
        return None
    return int(match.group())
