from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MarketValuePoint:
    as_of: date
    amount_eur: int
    club: str
