from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkippedPlayer:
    player_id: int
    name: str
    reason: str


@dataclass
class IngestionResult:
    ingested: int
    skipped: list[SkippedPlayer] = field(default_factory=list)
